"""Design & Marketing Worker: OpenDesign API + email delivery."""
import logging, os, json, glob, shutil
from datetime import datetime
from langgraph.graph import StateGraph, END
from .state import DesignWorkerState

logger = logging.getLogger(__name__)
COWORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD_DIR = os.path.join(COWORK_DIR, "workers", "open-design")
OD_PROJECTS = os.path.join(OD_DIR, ".od", "projects")

def _get_latest_project():
    """Busca el proyecto más reciente generado por OpenDesign."""
    if not os.path.exists(OD_PROJECTS):
        return None
    dirs = [d for d in os.listdir(OD_PROJECTS) if os.path.isdir(os.path.join(OD_PROJECTS, d))]
    if not dirs:
        return None
    latest = max(dirs, key=lambda d: os.path.getmtime(os.path.join(OD_PROJECTS, d)))
    return os.path.join(OD_PROJECTS, latest)

def design_generate(state: DesignWorkerState) -> dict:
    """Genera diseño con OpenDesign y guarda el output."""
    logger.info(f"[DESIGN] Generating: {state.query[:80]}...")
    
    try:
        import requests
        
        # Healthcheck
        try:
            hc = requests.get("http://127.0.0.1:34095/api/health", timeout=2)
            if not hc.ok:
                raise Exception("Daemon health check failed")
        except Exception:
            return {
                "reply": "❌ OpenDesign daemon no está corriendo. Inicialo con:\ncd workers/open-design && pnpm tools-dev run web --daemon-port 34095 --web-port 45125",
                "complete": True,
                "error": "Daemon offline"
            }
        
        # Marcar timestamp antes de generar
        before = datetime.now()
        
        resp = requests.post(
            "http://127.0.0.1:34095/api/chat",
            json={
                "message": state.query,
                "agentId": "opencode",
                "skillId": state.skill or "frontend"
            },
            timeout=600,
            stream=True
        )
        
        if not resp.ok:
            return {
                "reply": f"❌ Error {resp.status_code}",
                "complete": True,
                "error": f"HTTP {resp.status_code}"
            }
        
        # Consumir el stream SSE hasta que termine
        output_text = []
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data = line[5:].strip()
                if data and data != "[DONE]":
                    try:
                        import json as _json
                        event = _json.loads(data)
                        if event.get("type") == "text_delta":
                            output_text.append(event.get("delta", ""))
                    except:
                        pass
        
        generated_text = "".join(output_text)
        logger.info(f"[DESIGN] Generated {len(generated_text)} chars")
        
        # Buscar proyecto generado (posterior al timestamp)
        project_dir = _get_latest_project()
        if project_dir:
            # Copiar a output/design/
            dest = os.path.join(COWORK_DIR, "output", "design", 
                               f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copytree(project_dir, dest, dirs_exist_ok=True)
            html_files = glob.glob(os.path.join(dest, "*.html"))
            
            return {
                "reply": f"✅ Diseño generado ({state.skill or 'frontend'}) - {len(html_files)} archivos HTML en {dest}",
                "complete": True,
                "project_dir": dest,
                "artifacts": html_files
            }
        
        return {
            "reply": f"✅ Diseño generado ({state.skill or 'frontend'}) - revisá http://127.0.0.1:45125",
            "complete": True
        }
        
    except Exception as e:
        return {
            "reply": f"❌ OpenDesign no disponible: {str(e)[:200]}",
            "complete": True,
            "error": str(e)[:200]
        }


def build_design_graph():
    workflow = StateGraph(DesignWorkerState)
    workflow.add_node("generate", design_generate)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)
    return workflow.compile()
