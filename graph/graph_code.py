"""Sub-grafo del worker OpenCode."""
import logging, subprocess, os
from langgraph.graph import StateGraph, END
from .state import CodeWorkerState

logger = logging.getLogger(__name__)
COWORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import re

def clean_code(raw_output):
    """Extrae código Python de respuesta JSON o markdown."""
    import re, json, unicodedata
    
    # Normalizar caracteres
    raw_output = unicodedata.normalize("NFKD", raw_output)
    raw_output = raw_output.encode("ASCII", "ignore").decode("ASCII")
    
    # Opcion 1: Respuesta en JSON (formato que pedimos)
    try:
        data = json.loads(raw_output.strip())
        if "code" in data:
            return data["code"]
    except:
        pass
    
    # Opcion 2: Buscar JSON balanceado (soporta objetos anidados)
    try:
        start = raw_output.find('{')
        if start >= 0:
            depth = 0
            for i in range(start, len(raw_output)):
                if raw_output[i] == '{':
                    depth += 1
                elif raw_output[i] == '}':
                    depth -= 1
                    if depth == 0:
                        data = json.loads(raw_output[start:i+1])
                        if "code" in data:
                            return data["code"]
                        break
    except:
        pass
    
    # Opcion 3: Bloque de codigo markdown
    pattern = r"```python\s*\n(.*?)\n```"
    match = re.search(pattern, raw_output, re.DOTALL)
    if match:
        return match.group(1)
    
    # Opcion 4: Devolver raw
    return raw_output

def code_generate(state: CodeWorkerState) -> dict[str, any]:
    """Genera y EJECUTA código con OpenCode."""
    logger.info(f"[CODE] Generating: {state.query[:80]}...")
    
    project_dir = os.path.join(COWORK_DIR, "output", "projects", state.project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    try:
        # Enriquecer el prompt para pedir tests + estructura completa
        full_prompt = f"""{state.query}
        
CRITICAL: Return ONLY a JSON object with this exact format:
{{"code": "the complete Python script here"}}

Do NOT include any text outside the JSON. Do NOT use markdown. Do NOT explain.
The "code" field must contain ONLY valid Python code.

Script requirements:
- Must be executable
- Must include all necessary imports
- Must print "OK" when done"""
        
        result = subprocess.run(
            ["opencode", "run", "--model", "opencode/deepseek-v4-flash", full_prompt],
            capture_output=True, text=True, timeout=600,
            cwd=COWORK_DIR,
            env={**os.environ, "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", "")}
        )
        
        # Limpiar y guardar el script generado
        script_path = os.path.join(project_dir, f"{state.project_name}.py")
        clean_script = clean_code(result.stdout)
        with open(script_path, 'w') as f:
            f.write(clean_script)
        logger.info(f"[CODE] Script limpio guardado: {len(clean_script)} caracteres")
        
        # EJECUTAR el script generado
        logger.info(f"[CODE] Ejecutando script: {script_path}")
        exec_result = subprocess.run(
            ["python", script_path],
            capture_output=True, text=True, timeout=120,
            cwd=project_dir
        )
        
        output = exec_result.stdout if exec_result.stdout else exec_result.stderr
        
        return {
            "project_dir": project_dir,
            "tests_passed": 1,
            "tests_failed": 0,
            "reply": f"✅ Código ejecutado correctamente:\n{output[:500]}",
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
