"""Design & Marketing Worker: OpenDesign API + Campaign Management."""
import logging, os, json, glob, shutil, subprocess
from datetime import datetime
from langgraph.graph import StateGraph, END
from .state import DesignWorkerState

logger = logging.getLogger(__name__)
COWORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD_DIR = os.path.join(COWORK_DIR, "workers", "open-design")
OD_PROJECTS = os.path.join(OD_DIR, ".od", "projects")
DESIGN_OUTPUT = os.path.join(COWORK_DIR, "output", "design")
APPROVED_DIR = os.path.join(COWORK_DIR, "output", "marketing", "approved")

# ─── Campaign Templates ────────────────────────────────────
WEEKLY_CAMPAIGNS = [
    {"theme": "Lunes de Salud", "prompt": "Medical campaign poster: 'Lunes de Salud - Check-up preventivo con 20% descuento'. Blue and white, medical cross, modern clean design. Include price: $24 instead of $30.", "skill": "poster"},
    {"theme": "Miércoles de Bienestar", "prompt": "Wellness campaign poster: 'Miércoles de Bienestar - Consulta nutricional gratuita'. Green and white, fresh design, fruits/vegetables icons.", "skill": "poster"},
    {"theme": "Viernes de Oferta", "prompt": "Special offer medical poster: 'Viernes de Oferta - 2x1 en consultas generales'. Red and gold, promotion badge, modern design.", "skill": "poster"},
]

def _get_weekly_campaign():
    return WEEKLY_CAMPAIGNS[datetime.now().weekday() % len(WEEKLY_CAMPAIGNS)]

def _get_latest_project():
    if not os.path.exists(OD_PROJECTS):
        return None
    dirs = [d for d in os.listdir(OD_PROJECTS) if os.path.isdir(os.path.join(OD_PROJECTS, d))]
    if not dirs:
        return None
    return os.path.join(OD_PROJECTS, max(dirs, key=lambda d: os.path.getmtime(os.path.join(OD_PROJECTS, d))))

def _call_opendesign(query: str, skill: str) -> tuple[str | None, str | None]:
    """Llama a OpenDesign API. Retorna (project_dir, error)."""
    import requests
    try:
        hc = requests.get("http://127.0.0.1:34095/api/health", timeout=2)
        if not hc.ok:
            return None, "Daemon offline"
    except Exception:
        return None, "Daemon offline"
    
    resp = requests.post(
        "http://127.0.0.1:34095/api/chat",
        json={"message": query, "agentId": "opencode", "skillId": skill or "frontend",
             "model": "deepseek/deepseek-v4-flash"},
        timeout=600, stream=True
    )
    if not resp.ok:
        return None, f"HTTP {resp.status_code}"
    
    for line in resp.iter_lines(decode_unicode=True):
        pass  # Consumir stream
    
    project_dir = _get_latest_project()
    if project_dir:
        dest = os.path.join(DESIGN_OUTPUT, f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copytree(project_dir, dest, dirs_exist_ok=True)
        return dest, None
    return None, "No project found"

# ═══════════════ NODOS ═══════════════

def design_generate(state: DesignWorkerState) -> dict:
    """Genera diseño UI/UX con OpenDesign."""
    logger.info(f"[DESIGN] Generating: {state.query[:80]}...")
    project_dir, error = _call_opendesign(state.query, state.skill or "frontend")
    
    if error:
        return {"reply": f"❌ OpenDesign: {error}", "complete": True, "error": error}
    
    html_files = glob.glob(os.path.join(project_dir, "*.html")) if project_dir else []
    return {
        "reply": f"✅ Diseño generado ({state.skill or 'frontend'}) - {len(html_files)} archivos en {project_dir}",
        "complete": True, "project_dir": project_dir, "artifacts": html_files
    }

def campaign_generate(state: DesignWorkerState) -> dict:
    """Genera campaña semanal con OpenDesign."""
    campaign = _get_weekly_campaign()
    logger.info(f"[MARKETING] Generating: {campaign['theme']}")
    
    project_dir, error = _call_opendesign(campaign['prompt'], campaign['skill'])
    if error:
        return {"reply": f"❌ Campaña fallida: {error}", "complete": True, "error": error}
    
    html_files = glob.glob(os.path.join(project_dir, "*.html")) if project_dir else []
    
    # Guardar metadata
    meta = {'theme': campaign['theme'], 'prompt': campaign['prompt'],
            'generated_at': datetime.now().isoformat(), 'project_dir': project_dir,
            'files': html_files, 'status': 'pending'}
    with open(os.path.join(project_dir, 'campaign.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    
    return {
        "reply": f"🎨 Campaña {campaign['theme']} generada - {len(html_files)} archivos\nPara ver: python apps/cli/cowork_graph.py --design campaign_view\nPara aprobar: python apps/cli/cowork_graph.py --design campaign_approve",
        "complete": True, "project_dir": project_dir, "artifacts": html_files
    }

def campaign_view(state: DesignWorkerState) -> dict:
    """Abre la última campaña en Firefox."""
    projects = sorted([d for d in os.listdir(DESIGN_OUTPUT) if d.startswith('project_')], reverse=True)
    if not projects:
        return {"reply": "No hay campañas generadas.", "complete": True}
    
    index_path = os.path.join(DESIGN_OUTPUT, projects[0], 'index.html')
    if os.path.exists(index_path):
        subprocess.run(['firefox', index_path], capture_output=True)
        return {"reply": f"✅ Abriendo {index_path} en Firefox", "complete": True}
    return {"reply": "❌ No se encontró index.html", "complete": True}

def campaign_approve(state: DesignWorkerState) -> dict:
    """Aprueba la última campaña pendiente."""
    projects = sorted([d for d in os.listdir(DESIGN_OUTPUT) if d.startswith('project_')], reverse=True)
    
    for p in projects:
        meta_path = os.path.join(DESIGN_OUTPUT, p, 'campaign.json')
        if not os.path.exists(meta_path):
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        if meta.get('status') == 'approved':
            continue
        
        meta['status'] = 'approved'
        meta['approved_at'] = datetime.now().isoformat()
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        os.makedirs(APPROVED_DIR, exist_ok=True)
        dest = os.path.join(APPROVED_DIR, p)
        if not os.path.exists(dest):
            shutil.copytree(os.path.join(DESIGN_OUTPUT, p), dest)
        
        # Enviar email de notificación
        try:
            from tools.email_sender import send_email_simple
            index_file = os.path.join(dest, 'index.html')
            body = f"<h2>{meta['theme']} - APROBADA</h2><p>Carpeta: {dest}</p>"
            send_email_simple(os.getenv('ADMIN_EMAIL', 'byron92m@gmail.com'),
                            f"✅ APROBADA: {meta['theme']}", body,
                            attachments=[index_file] if os.path.exists(index_file) else [])
        except Exception as e:
            logger.warning(f"Email notification failed: {e}")
        
        return {"reply": f"✅ Campaña APROBADA: {meta['theme']}\n   Carpeta: {dest}\n   Archivos: {len(meta.get('files', []))}", "complete": True}
    
    return {"reply": "No hay campañas pendientes para aprobar.", "complete": True}

def campaign_list(state: DesignWorkerState) -> dict:
    """Lista todas las campañas."""
    if not os.path.exists(DESIGN_OUTPUT):
        return {"reply": "No hay campañas generadas.", "complete": True}
    
    projects = sorted([d for d in os.listdir(DESIGN_OUTPUT) if d.startswith('project_')], reverse=True)
    lines = []
    for p in projects:
        meta_path = os.path.join(DESIGN_OUTPUT, p, 'campaign.json')
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            lines.append(f"  [{meta.get('status', '?')}] {meta.get('theme', '?')} - {meta.get('generated_at', '')[:16]}")
    
    return {"reply": "Campañas:\n" + "\n".join(lines) if lines else "No hay campañas.", "complete": True}

# ═══════════════ ROUTING ═══════════════

def route_design(state: DesignWorkerState) -> str:
    """Rutea al nodo correcto según el skill."""
    skill = state.skill or "frontend"
    if skill in ("campaign_generate", "campaign_view", "campaign_approve", "campaign_list"):
        return skill
    return "generate"

# ═══════════════ BUILD ═══════════════

def build_design_graph():
    workflow = StateGraph(DesignWorkerState)
    
    workflow.add_node("generate", design_generate)
    workflow.add_node("campaign_generate", campaign_generate)
    workflow.add_node("campaign_view", campaign_view)
    workflow.add_node("campaign_approve", campaign_approve)
    workflow.add_node("campaign_list", campaign_list)
    
    workflow.set_entry_point("generate")
    workflow.add_conditional_edges("generate", route_design, {
        "generate": "generate",
        "campaign_generate": "campaign_generate",
        "campaign_view": "campaign_view",
        "campaign_approve": "campaign_approve",
        "campaign_list": "campaign_list",
    })
    
    for node in ["generate", "campaign_generate", "campaign_view", "campaign_approve", "campaign_list"]:
        workflow.add_edge(node, END)
    
    return workflow.compile()
