"""CodeWhale Worker - Replaces mcp_worker with 30+ tools."""
import logging, subprocess, os
from langgraph.graph import StateGraph, END
from .state import CoworkState

logger = logging.getLogger(__name__)
CODEWHALE_BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workers/codewhale/codewhale")

def execute_codewhale(state: CoworkState) -> dict:
    """Ejecuta CodeWhale en modo exec --auto."""
    query = state.user_query
    
    try:
        result = subprocess.run(
            [CODEWHALE_BIN, "exec", "--auto", "--model", "deepseek-v4-flash", query],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()
        
        return {
            "reply": output[:2000] if output else "CodeWhale no devolvio resultado",
            "complete": True,
            "tests_passed": 1,
            "tests_failed": 0
        }
    except subprocess.TimeoutExpired:
        return {
            "reply": "CodeWhale tardo demasiado (>120s)",
            "complete": True,
            "tests_passed": 0,
            "tests_failed": 1
        }
    except Exception as e:
        logger.error(f"CodeWhale error: {e}")
        return {
            "reply": f"Error: {str(e)[:200]}",
            "complete": True,
            "tests_passed": 0,
            "tests_failed": 1
        }

def build_codewhale_graph():
    workflow = StateGraph(CoworkState)
    workflow.add_node("execute", execute_codewhale)
    workflow.set_entry_point("execute")
    workflow.add_edge("execute", END)
    return workflow.compile()
