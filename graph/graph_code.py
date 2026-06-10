"""Sub-grafo del worker OpenCode (modo agente --auto)."""
import logging, subprocess, os, sys, glob as globmod
from typing import Any
from langgraph.graph import StateGraph, END
from .state import CodeWorkerState

logger = logging.getLogger(__name__)
COWORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def find_generated_script(project_dir: str) -> str | None:
    """Busca el archivo .py principal generado por OpenCode."""
    py_files = globmod.glob(os.path.join(project_dir, "*.py"))
    if not py_files:
        # Buscar en subdirectorios
        py_files = globmod.glob(os.path.join(project_dir, "**/*.py"), recursive=True)
    
    if not py_files:
        return None
    
    # Priorizar main.py, app.py, o el más grande
    for preferred in ["main.py", "app.py"]:
        for f in py_files:
            if os.path.basename(f) == preferred:
                return f
    
    # El más grande probablemente sea el principal
    return max(py_files, key=os.path.getsize)


def code_generate(state: CodeWorkerState) -> dict[str, Any]:
    """Genera proyecto con OpenCode en modo agente (--auto)."""
    logger.info(f"[CODE] Generating: {state.query[:80]}...")
    
    project_dir = os.path.join(COWORK_DIR, "output", "projects", state.project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    try:
        # Prompt natural, OpenCode decide cómo resolverlo con tools
        full_prompt = f"""{state.query}

Work in the current directory. Create all files here.
When done, the main script must print "OK" at the end."""
        
        result = subprocess.run(
            ["opencode", "run", "--model", "deepseek/deepseek-v4-flash",
             "--dir", project_dir, "--", full_prompt],
            capture_output=True, text=True, timeout=600,
            cwd=COWORK_DIR,
            env={**os.environ, "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", "")}
        )
        
        logger.info(f"[CODE] OpenCode stdout: {len(result.stdout)} chars, stderr: {len(result.stderr)} chars")
        if result.stderr:
            logger.info(f"[CODE] stderr: {result.stderr[:300]}")
        
        # Buscar el script generado
        script_path = find_generated_script(project_dir)
        
        if not script_path:
            # Fallback: si no hay .py, OpenCode respondió sin generar archivos
            output = result.stdout.strip()
            if not output:
                output = result.stderr.strip()
            return {
                "project_dir": project_dir,
                "tests_passed": 0,
                "tests_failed": 0,
                "reply": output[:2000] if output else "OpenCode no generó archivos",
                "complete": True
            }
        
        logger.info(f"[CODE] Script encontrado: {script_path}")
        
        # EJECUTAR el script generado
        logger.info(f"[CODE] Ejecutando script: {script_path}")
        exec_result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=120,
            cwd=project_dir
        )
        
        output = exec_result.stdout if exec_result.stdout else exec_result.stderr
        
        # Verificar si el script crasheó
        exec_failed = exec_result.returncode != 0 or ("Error" in output and "OK" not in output)
        return {
            "project_dir": project_dir,
            "tests_passed": 0 if exec_failed else 1,
            "tests_failed": 1 if exec_failed else 0,
            "reply": f"{'❌ Error' if exec_failed else '✅'} Código ejecutado:\n{output[:500]}",
            "complete": True
        }
    except subprocess.TimeoutExpired:
        return {
            "reply": "❌ OpenCode tardó demasiado (>600s)",
            "complete": True,
            "tests_passed": 0,
            "tests_failed": 1,
            "error": "Timeout"
        }
    except Exception as e:
        logger.error(f"[CODE] Error: {e}")
        return {
            "reply": f"❌ Error: {str(e)[:200]}",
            "complete": True,
            "tests_passed": 0,
            "tests_failed": 1,
            "error": str(e)[:200]
        }


def build_code_graph():
    workflow = StateGraph(CodeWorkerState)
    workflow.add_node("generate", code_generate)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)
    return workflow.compile()
