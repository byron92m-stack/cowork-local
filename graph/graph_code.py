"""Sub-grafo del worker OpenCode."""
import logging, subprocess, os
from langgraph.graph import StateGraph, END
from .state import CodeWorkerState

logger = logging.getLogger(__name__)
COWORK_DIR = "/media/SSD1T/cowork-local"

def code_generate(state: CodeWorkerState) -> dict:
    """Genera código con OpenCode."""
    logger.info(f"[CODE] Generating: {state.query[:80]}...")
    
    project_dir = os.path.join(COWORK_DIR, state.project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    try:
        # Enriquecer el prompt para pedir tests + estructura completa
        full_prompt = f"""{state.query}
        
CRITICAL: Include ALL of these files:
- src/{state.project_name}/__init__.py
- src/{state.project_name}/core.py (all business logic)
- src/{state.project_name}/cli.py (argparse with ALL requested flags)
- tests/test_core.py (20+ pytest tests covering success, errors, edge cases)
- tests/test_cli.py (10+ CLI tests)
- README.md (install, usage, examples)
- pyproject.toml (dependencies, entry point)
Return JSON with files array."""
        
        result = subprocess.run(
            ["opencode", "run", "--model", "opencode/deepseek-v4-flash-free", full_prompt],
            capture_output=True, text=True, timeout=600,
            cwd=COWORK_DIR,
            env={**os.environ, "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", "")}
        )
        
        # Run pytest
        test_result = subprocess.run(
            f"cd {project_dir} && python -m pytest -v 2>&1",
            shell=True, capture_output=True, text=True, timeout=180
        )
        passed = test_result.stdout.count("PASSED")
        failed = test_result.stdout.count("FAILED")
        
        return {
            "project_dir": project_dir,
            "tests_passed": passed,
            "tests_failed": failed,
            "reply": f"✅ Código generado: {passed} tests passed, {failed} failed" if passed > 0 else f"⚠️ Código generado en {project_dir}",
            "complete": True
        }
    except Exception as e:
        return {
            "reply": f"❌ Error: {str(e)[:200]}",
            "complete": True,
            "error": str(e)[:200]
        }


def build_code_graph():
    workflow = StateGraph(CodeWorkerState)
    workflow.add_node("generate", code_generate)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)
    return workflow.compile()
