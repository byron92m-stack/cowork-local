"""Marketing Scheduler: Campañas semanales con OpenDesign.
Modos:
  --generate : Genera arte y guarda en output/design/
  --approve  : Aprueba última campaña generada
  --list     : Lista campañas pendientes de aprobación
  --view     : Abre la última campaña en Firefox
"""

import os, sys, json, logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, "/media/SSD1T/cowork-local")

logger = logging.getLogger(__name__)
COWORK_DIR = "/media/SSD1T/cowork-local"
DESIGN_OUTPUT = os.path.join(COWORK_DIR, "output", "design")
APPROVED_DIR = os.path.join(COWORK_DIR, "output", "marketing", "approved")

# Templates de campañas semanales
WEEKLY_CAMPAIGNS = [
    {
        "theme": "Lunes de Salud",
        "prompt": "Medical campaign poster: 'Lunes de Salud - Check-up preventivo con 20% descuento'. Blue and white, medical cross, modern clean design. Include price: $24 instead of $30.",
        "skill": "poster"
    },
    {
        "theme": "Miércoles de Bienestar",
        "prompt": "Wellness campaign poster: 'Miércoles de Bienestar - Consulta nutricional gratuita'. Green and white, fresh design, fruits/vegetables icons.",
        "skill": "poster"
    },
    {
        "theme": "Viernes de Oferta",
        "prompt": "Special offer medical poster: 'Viernes de Oferta - 2x1 en consultas generales'. Red and gold, promotion badge, modern design.",
        "skill": "poster"
    },
]

def get_weekly_campaign():
    """Selecciona campaña según el día de la semana."""
    weekday = datetime.now().weekday()
    return WEEKLY_CAMPAIGNS[weekday % len(WEEKLY_CAMPAIGNS)]

def generate_campaign():
    """Genera arte con OpenDesign y guarda localmente."""
    campaign = get_weekly_campaign()
    print(f"🎨 Generando campaña: {campaign['theme']}")
    print(f"   Prompt: {campaign['prompt'][:80]}...")
    
    try:
        from graph.graph_design import design_generate
        from graph.state import DesignWorkerState
        
        state = DesignWorkerState(
            query=campaign['prompt'],
            skill=campaign['skill']
        )
        result = design_generate(state)
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
            return None
        
        project_dir = result.get('project_dir', '')
        html_files = result.get('artifacts', [])
        
        # Guardar metadata de la campaña
        meta = {
            'theme': campaign['theme'],
            'prompt': campaign['prompt'],
            'generated_at': datetime.now().isoformat(),
            'project_dir': project_dir,
            'files': html_files,
            'status': 'pending'
        }
        meta_path = os.path.join(project_dir, 'campaign.json')
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        print(f"✅ Campaña generada: {project_dir}")
        print(f"   Archivos: {len(html_files)}")
        print(f"   Para ver: python tools/marketing_scheduler.py --view")
        print(f"   Para aprobar: python tools/marketing_scheduler.py --approve")
        return project_dir
        
    except Exception as e:
        logger.error(f"Error generando campaña: {e}")
        return None

def list_campaigns():
    """Lista campañas pendientes de aprobación."""
    if not os.path.exists(DESIGN_OUTPUT):
        print("No hay campañas generadas.")
        return
    
    projects = sorted(
        [d for d in os.listdir(DESIGN_OUTPUT) if d.startswith('project_')],
        reverse=True
    )
    
    for p in projects:
        meta_path = os.path.join(DESIGN_OUTPUT, p, 'campaign.json')
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            status = meta.get('status', '?')
            theme = meta.get('theme', '?')
            date = meta.get('generated_at', '')[:16]
            print(f"  [{status}] {theme} - {date} - {p}")
        else:
            print(f"  [sin metadata] {p}")

def view_campaign():
    """Abre la última campaña en Firefox."""
    projects = sorted(
        [d for d in os.listdir(DESIGN_OUTPUT) if d.startswith('project_')],
        reverse=True
    )
    if not projects:
        print("No hay campañas generadas.")
        return
    
    latest = projects[0]
    index_path = os.path.join(DESIGN_OUTPUT, latest, 'index.html')
    
    if os.path.exists(index_path):
        import subprocess
        subprocess.run(['firefox', index_path], capture_output=True)
        print(f"✅ Abriendo {index_path} en Firefox")
    else:
        print(f"❌ No se encontró index.html en {latest}")

def approve_campaign():
    """Aprueba la última campaña pendiente."""
    projects = sorted(
        [d for d in os.listdir(DESIGN_OUTPUT) if d.startswith('project_')],
        reverse=True
    )
    
    for p in projects:
        meta_path = os.path.join(DESIGN_OUTPUT, p, 'campaign.json')
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            
            if meta.get('status') == 'approved':
                continue  # Ya aprobada
            
            # Aprobar
            meta['status'] = 'approved'
            meta['approved_at'] = datetime.now().isoformat()
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)
            
            # Copiar a aprobados
            os.makedirs(APPROVED_DIR, exist_ok=True)
            dest = os.path.join(APPROVED_DIR, p)
            if not os.path.exists(dest):
                import shutil
                shutil.copytree(os.path.join(DESIGN_OUTPUT, p), dest)
            
            print(f"✅ Campaña APROBADA: {meta['theme']}")
            print(f"   Carpeta: {dest}")
            print(f"   Archivos: {len(meta.get('files', []))}")
            
            # Enviar por email para que lo veas
            try:
                from tools.email_sender import send_email_simple
                index_file = os.path.join(dest, 'index.html')
                body = f"""<h2>{meta['theme']} - APROBADA</h2>
<p>La campaña fue aprobada y está lista para publicar.</p>
<p><b>Carpeta:</b> {dest}</p>
<p><b>Archivos:</b> {len(meta.get('files', []))}</p>
<p>Abrí index.html en Firefox para ver la galería.</p>"""
                send_email_simple(
                    to=os.getenv('ADMIN_EMAIL', 'byron92m@gmail.com'),
                    subject=f"✅ APROBADA: {meta['theme']}",
                    body=body,
                    attachments=[index_file] if os.path.exists(index_file) else []
                )
                print(f"   Email enviado a {os.getenv('ADMIN_EMAIL', 'byron92m@gmail.com')}")
            except Exception as e:
                print(f"   ⚠️ No se pudo enviar email: {e}")
            return
    
    print("No hay campañas pendientes para aprobar.")

if __name__ == "__main__":
    if "--generate" in sys.argv or len(sys.argv) == 1:
        generate_campaign()
    elif "--list" in sys.argv:
        list_campaigns()
    elif "--view" in sys.argv:
        view_campaign()
    elif "--approve" in sys.argv:
        approve_campaign()
    else:
        print("Uso: python tools/marketing_scheduler.py [--generate|--list|--view|--approve]")
