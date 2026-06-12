"""Accounting Worker: Extrae datos de facturas electrónicas (XML SRI / PDF)."""
import os, json, logging, re, xml.etree.ElementTree as ET
from datetime import date, datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from .state import AccountingState
from .accounting_db import get_pool, save_invoice, invoice_exists, init_invoices_table

load_dotenv()
logger = logging.getLogger(__name__)

# ─── Namespaces SRI ──────────────────────────────────────────
SRI_NS = {
    'factura': 'http://ec.gob.sri/comprobantes/1.0.0',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
}

def extract_from_xml(filepath: str) -> dict:
    """Extrae datos de una factura electrónica XML (SRI Ecuador).
    Soporta XML con namespace (estándar SRI) y sin namespace."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Detectar namespace del SRI
        ns = ''
        for prefix, uri in {'factura': 'http://ec.gob.sri/comprobantes/1.0.0'}.items():
            if f'{{{uri}}}' in root.tag:
                ns = uri
                break
        if not ns:
            # Buscar en el árbol
            for elem in root.iter():
                if 'infoTributaria' in elem.tag:
                    # Extraer namespace de la etiqueta
                    if elem.tag.startswith('{'):
                        ns = elem.tag.split('}')[0].replace('{', '')
                    break
        
        # Helper con sintaxis de Clark
        def _find(parent, tag):
            if ns:
                return parent.find(f'.//{{{ns}}}{tag}')
            return parent.find(f'.//{tag}')
        
        def _text(parent, tag, default=''):
            el = _find(parent, tag)
            return el.text if el is not None and el.text else default
        
        # infoTributaria
        info_trib = _find(root, 'infoTributaria')
        if info_trib is None:
            return {}
        
        ruc = _text(info_trib, 'ruc')
        razon = _text(info_trib, 'razonSocial')
        estab = _text(info_trib, 'estab')
        pto = _text(info_trib, 'ptoEmi')
        sec = _text(info_trib, 'secuencial')
        num = f"{estab}-{pto}-{sec}"
        
        # infoFactura
        info_fact = _find(root, 'infoFactura')
        fecha_str = ''
        subtotal = 0.0
        iva = 0.0
        total = 0.0
        
        if info_fact is not None:
            fecha_str = _text(info_fact, 'fechaEmision')
            subtotal = float(_text(info_fact, 'subtotal', '0') or _text(info_fact, 'subtotal12', '0') or 0)
            total = float(_text(info_fact, 'total', '0') or _text(info_fact, 'importeTotal', '0') or 0)
            
            # IVA
            iva_elem = _find(info_fact, 'iva') or _find(info_fact, 'totalImpuesto')
            if iva_elem is not None:
                iva = float(_text(iva_elem, 'valor', '0') or 0)
        
        fecha = None
        if fecha_str:
            try:
                fecha = date.fromisoformat(fecha_str[:10])
            except:
                pass
        
        return {
            'ruc_emisor': ruc,
            'razon_social': razon,
            'numero_factura': num,
            'fecha_emision': fecha,
            'subtotal': subtotal,
            'iva': iva,
            'total': total,
        }
    except Exception as e:
        logger.error(f"Error parseando XML: {e}")
        return {}

def extract_from_pdf(filepath: str) -> dict:
    """Extrae datos de un PDF de factura (texto plano)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        text = "\n".join([p.extract_text() or '' for p in reader.pages])
        
        # Patrones comunes en facturas ecuatorianas
        ruc_match = re.search(r'RUC[:\s]*(\d{13})', text)
        num_match = re.search(r'(?:No?\.?|Nro\.?|Factura)\s*(?:#|No?\.?)?\s*(\d{3}-\d{3}-\d+)', text)
        total_match = re.search(r'(?:TOTAL|Total)\s*\$?\s*([\d,.]+)', text)
        fecha_match = re.search(r'Fecha[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
        
        data = {}
        if ruc_match:
            data['ruc_emisor'] = ruc_match.group(1)
        if num_match:
            data['numero_factura'] = num_match.group(1)
        if total_match:
            try:
                data['total'] = float(total_match.group(1).replace(',', ''))
            except:
                pass
        if fecha_match:
            from dateparser import parse
            dt = parse(fecha_match.group(1), settings={'DATE_ORDER': 'DMY'})
            if dt:
                data['fecha_emision'] = dt.date()
        
        return data
    except Exception as e:
        logger.error(f"Error parseando PDF: {e}")
        return {}

async def accounting_extract(state: AccountingState) -> dict:
    """Nodo principal: extrae datos de la factura y guarda en DB."""
    await init_invoices_table()
    
    filepath = state.attachment_path
    if not filepath or not os.path.exists(filepath):
        return {"complete": True, "error": "No attachment found", "reply": "Sin adjunto"}
    
    # Extraer según tipo
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.xml':
        data = extract_from_xml(filepath)
    elif ext == '.pdf':
        data = extract_from_pdf(filepath)
    else:
        return {"complete": True, "reply": f"Formato no soportado: {ext}"}
    
    if not data or not data.get('ruc_emisor'):
        return {"complete": True, "error": "No se pudo extraer datos", "reply": "Extracción fallida"}
    
    # Verificar duplicado
    if data.get('numero_factura') and data.get('ruc_emisor'):
        exists = await invoice_exists(data['numero_factura'], data['ruc_emisor'])
        if exists:
            logger.info(f"Factura duplicada: {data['numero_factura']}")
            return {"complete": True, "reply": "Factura ya existe"}
    
    data['source_email'] = state.user_id
    data['attachment_path'] = filepath
    data['raw_data'] = json.dumps(data.copy(), default=str)
    
    saved = await save_invoice(data)
    if saved:
        logger.info(f"Factura guardada: {data.get('numero_factura')} - ${data.get('total')}")
        return {"invoice_data": data, "complete": True, "reply": f"Factura {data.get('numero_factura')} guardada"}
    else:
        return {"complete": True, "error": "No se pudo guardar", "reply": "Error al guardar"}

def build_accounting_graph():
    """Grafo simple: un solo nodo de extracción."""
    workflow = StateGraph(AccountingState)
    workflow.add_node("extract", accounting_extract)
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", END)
    return workflow.compile()

async def run_accounting(channel: str, user_id: str, attachment_path: str, attachment_type: str = "") -> AccountingState:
    """API pública: procesa un adjunto y extrae datos de factura."""
    state = AccountingState(
        channel=channel,
        user_id=user_id,
        attachment_path=attachment_path,
        attachment_type=attachment_type
    )
    graph = build_accounting_graph()
    result = await graph.ainvoke(state)
    final = AccountingState(**result)
    return final
