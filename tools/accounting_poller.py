"""Background worker: IMAP polling para facturas electrónicas (SRI)."""
import os, sys, re, asyncio, tempfile
import imaplib, email
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, "/media/SSD1T/cowork-local")

IMAP_HOST = os.getenv("MAIL_IMAP_HOST", "imap.mail.ru")
IMAP_PORT = int(os.getenv("MAIL_IMAP_PORT", "993"))
MAIL_USER = os.getenv("MAIL_USER", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

# ─── Descargar adjuntos ─────────────────────────────────────
def download_attachments(msg, save_dir: str) -> list:
    """Descarga adjuntos de un email. Retorna lista de rutas."""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            content_disp = part.get("Content-Disposition", "")
            if "attachment" in content_disp:
                filename = part.get_filename()
                if filename:
                    # Decodificar nombre
                    try:
                        from email.header import decode_header
                        decoded = decode_header(filename)
                        filename = decoded[0][0]
                        if isinstance(filename, bytes):
                            filename = filename.decode(decoded[0][1] or 'utf-8', errors='ignore')
                    except:
                        pass
                    
                    filepath = os.path.join(save_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    attachments.append(filepath)
    return attachments

def is_invoice_attachment(filename: str) -> bool:
    """Determina si un adjunto parece factura por nombre/extensión."""
    name_lower = filename.lower()
    if name_lower.endswith('.xml'):
        return True
    if name_lower.endswith('.pdf'):
        # Buscar palabras clave en el nombre
        keywords = ['factura', 'invoice', 'comprobante', 'sri', 'electronica']
        return any(kw in name_lower for kw in keywords)
    return False

# ─── Poller ──────────────────────────────────────────────────
async def poll_invoices():
    """Revisa emails no leídos con adjuntos de facturas y los procesa."""
    if not MAIL_USER or not MAIL_PASSWORD:
        print("⚠️ MAIL_USER/MAIL_PASSWORD no configurados")
        return
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(MAIL_USER, MAIL_PASSWORD)
        mail.select("INBOX")
        
        # Buscar emails no leídos de los últimos 2 días
        since = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
        result, message_ids = mail.search(None, f'(UNSEEN SINCE {since})')
        
        if not message_ids[0]:
            mail.close()
            mail.logout()
            return
        
        ids = message_ids[0].split()[-10:]  # Máximo 10 por ciclo
        print(f"📧 {len(ids)} emails UNSEEN para revisar")
        
        for num in ids:
            result, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            from_email = msg['From'] or ""
            match = re.search(r'<([^>]+)>', from_email)
            if match:
                from_email = match.group(1)
            
            subject = msg['Subject'] or ""
            print(f"📧 De: {from_email} | Asunto: {subject[:60]}")
            
            # Descargar adjuntos
            with tempfile.TemporaryDirectory() as tmpdir:
                attachments = download_attachments(msg, tmpdir)
                
                if not attachments:
                    mail.store(num, '+FLAGS', '\\Seen')
                    print("   Sin adjuntos → marcado como leído")
                    continue
                
                # Filtrar solo facturas
                invoice_files = [a for a in attachments if is_invoice_attachment(os.path.basename(a))]
                if not invoice_files:
                    mail.store(num, '+FLAGS', '\\Seen')
                    print(f"   {len(attachments)} adjuntos no parecen facturas → marcado como leído")
                    continue
                
                # Procesar cada factura
                for filepath in invoice_files:
                    ext = os.path.splitext(filepath)[1].lower()
                    print(f"   📎 {os.path.basename(filepath)} ({ext})")
                    
                    try:
                        from graph.graph_accounting import run_accounting
                        result = await run_accounting(
                            channel="email",
                            user_id=from_email,
                            attachment_path=filepath,
                            attachment_type=ext.replace('.', '')
                        )
                        if result.invoice_data:
                            inv = result.invoice_data
                            print(f"   ✅ Factura {inv.get('numero_factura')}: ${inv.get('total')} - {inv.get('razon_social')}")
                        elif "ya existe" in (result.reply or ""):
                            print(f"   ⏭️ Duplicada")
                        else:
                            print(f"   ❌ {result.error or result.reply}")
                    except Exception as e:
                        print(f"   ❌ Error procesando: {e}")
                
                # Marcar como leído
                mail.store(num, '+FLAGS', '\\Seen')
        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"❌ Error IMAP: {e}")

if __name__ == "__main__":
    print("🧾 Accounting Poller iniciado (IMAP cada 5 min)")
    import asyncio
    asyncio.run(poll_invoices())
