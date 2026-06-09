"""Sub-grafo del worker OpenDesign."""
import logging
from langgraph.graph import StateGraph, END
from .state import DesignWorkerState

logger = logging.getLogger(__name__)

def design_generate(state: DesignWorkerState) -> dict:
    """Genera diseño con OpenDesign."""
    logger.info(f"[DESIGN] Generating: {state.query[:80]}...")
    
    try:
        import requests
        
        # Healthcheck: verificar que el daemon esté corriendo
        try:
            hc = requests.get("http://127.0.0.1:34095/api/health", timeout=2)
            if not hc.ok:
                raise Exception("Daemon health check failed")
        except Exception:
            return {
                "reply": "❌ OpenDesign daemon no está corriendo. Inicialo con:\ncd /media/SSD1T/cowork-local/workers/open-design && pnpm tools-dev run web --daemon-port 34095 --web-port 45125",
                "complete": True,
                "error": "Daemon offline"
            }
        
        resp = requests.post(
            "http://127.0.0.1:34095/api/chat",
            json={
                "message": state.query,
                "agentId": "opencode",
                "skillId": state.skill
            },
            timeout=600
        )
        if resp.ok:
            return {
                "reply": f"✅ Diseño generado ({state.skill}) - revisá http://127.0.0.1:45125",
                "complete": True
            }
        else:
            return {
                "reply": f"❌ Error {resp.status_code}",
                "complete": True,
                "error": f"HTTP {resp.status_code}"
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
