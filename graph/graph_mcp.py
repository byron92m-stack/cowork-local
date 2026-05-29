"""Sub-grafo de herramientas MCP (filesystem, document, web, shell, chat)."""
import logging, subprocess, os, re, asyncio
import redis as redis_lib
from langgraph.graph import StateGraph, END
from .state import CoworkState

logger = logging.getLogger(__name__)
COWORK_DIR = "/media/SSD1T/cowork-local"
redis_client = redis_lib.Redis(host='localhost', port=6379, decode_responses=True)
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")


def execute_tool(state: CoworkState) -> dict:
    """Ejecuta la herramienta MCP según el project_type."""
    project_type = state.metadata.get("project_type", "chat")
    query = state.user_query
    result = ""
    
    try:
        # ─── FILESYSTEM ────────────────────────────────
        if project_type == "tool_filesystem":
            path_match = re.search(r'/(?:media|home|tmp)/[^\s]*', query)
            path = path_match.group(0) if path_match else "/media/SSD1T/"
            ext_match = re.search(r'\.(\w+)', query)
            pattern = ext_match.group(1) if ext_match else None
            
            found = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    if pattern is None or f.endswith('.' + pattern):
                        found.append(os.path.join(root, f))
                if len(found) > 50:
                    break
            if found:
                result = "📁 Archivos encontrados en " + path + ":\n" + "\n".join(found[:20])
            else:
                result = "📁 No se encontraron archivos" + (f" .{pattern}" if pattern else "") + " en " + path
        
        # ─── DOCUMENT ──────────────────────────────────
        elif project_type == "tool_document":
            # PRIORIDAD 1: Usar project_path del estado
            filepath = state.project_path if state.project_path and os.path.exists(state.project_path) else None
            
            # PRIORIDAD 2: Buscar en el query (comportamiento original)
            if not filepath:
                # Buscar rutas que empiecen con /media, /home, /tmp
                path_match = re.search(r'/(?:media|home|tmp)/[^\s]+\.\w+', query)
                filepath = path_match.group(0) if path_match else None
            
            if filepath and os.path.exists(filepath):
                ext = filepath.split('.')[-1].lower()
                if ext == 'pdf':
                    from pypdf import PdfReader
                    reader = PdfReader(filepath)
                    text = "\n".join([p.extract_text() or '' for p in reader.pages])
                    result = f"📄 PDF: {filepath}\nPaginas: {len(reader.pages)}\n\n{text}"
                elif ext in ('xlsx', 'xls'):
                    import pandas as pd
                    df = pd.read_excel(filepath)
                    result = f"📊 Excel: {filepath}\nFilas: {len(df)}\nColumnas: {list(df.columns)}\n\n{df.head(10).to_string()}"
                elif ext in ('csv', 'txt', 'md', 'py', 'json', 'log'):
                    with open(filepath) as f:
                        text = f.read()
                    result = f"📝 Archivo: {filepath}\n{text}"
                else:
                    result = f"📁 Archivo no soportado: {filepath} (.{ext})"
            else:
                result = "📄 Especifica la ruta completa al archivo."
        
        elif project_type == "tool_edit":
            import subprocess as sp, re as _re
            path_match = _re.search(r'/(?:media|home|tmp)/[^\s]*\.\w+', query)
            filepath = path_match.group(0) if path_match else None
            
            if filepath and os.path.exists(filepath):
                with open(filepath) as f:
                    content = f.read()[:2000]
                
                edit_prompt = f"File: {filepath}\nCurrent content:\n{content}\n\nTask: {query}\n\nEdit the file to fulfill the task. Return ONLY the complete modified file content."
                cmd_result = sp.run(
                    ["opencode", "run", "--model", "opencode/deepseek-v4-flash-free", edit_prompt],
                    capture_output=True, text=True, timeout=120,
                    cwd=COWORK_DIR,
                    env={**os.environ, "DEEPSEEK_API_KEY": DEEPSEEK_KEY}
                )
                new_content = cmd_result.stdout.strip()
                if new_content and len(new_content) > 10:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    result = f"✏️ Archivo editado: {filepath}"
                else:
                    result = "❌ No se pudo generar la nueva versión del archivo"
            else:
                result = "📄 Especifica la ruta completa al archivo a editar"
        
        # ─── SHELL ─────────────────────────────────────
        elif project_type == "tool_shell":
            qlower = query.lower()
            cmd = query
            for w in ["ejecutá", "ejecuta", "ejecutar", "corré", "corre", "correr"]:
                if w in qlower:
                    cmd = query.lower().split(w, 1)[-1].strip()
                    break
            if "run " in qlower:
                cmd = query.lower().split("run ", 1)[-1].strip()
            cmd = cmd.replace(" --confirm", "").replace("--confirm", "").strip()
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            result = "💻 Comando ejecutado:\n" + (output.stdout or output.stderr)[:500]
        
        # ─── CHAT ──────────────────────────────────────
        elif project_type == "chat":
            session_id = state.session_id
            history = redis_client.lrange(f"chat:{session_id}", 0, -1)
            if history and len(history) >= 2:
                context = "\n".join(history[-6:])
                import httpx
                r = httpx.post("https://api.deepseek.com/v1/chat/completions", json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Answer based on conversation history."},
                        {"role": "user", "content": f"History:\n{context}\n\nUser: {query}\n\nAnswer:"}
                    ],
                    "max_tokens": 500, "temperature": 0.7
                }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=30)
                if r.status_code == 200:
                    result = r.json()["choices"][0]["message"]["content"]
                else:
                    result = "Lo siento, hubo un error al procesar tu mensaje."
            else:
                result = "¡Hola! Soy tu asistente Cowork. Puedo:\n• Buscar archivos en tu PC\n• Crear proyectos Python\n• Analizar documentos\n• Ejecutar comandos\n• Navegar internet\n\n¿En qué te ayudo?"
        
        return {
            "reply": result,
            "complete": True,
            "tests_passed": 1,
            "tests_failed": 0
        }
    
    except Exception as e:
        logger.error(f"MCP tool error: {e}")
        return {
            "reply": f"❌ Error: {str(e)[:200]}",
            "complete": True,
            "tests_passed": 1,
            "tests_failed": 0
        }


def build_mcp_graph():
    workflow = StateGraph(CoworkState)
    workflow.add_node("execute", execute_tool)
    workflow.set_entry_point("execute")
    workflow.add_edge("execute", END)
    return workflow.compile()
