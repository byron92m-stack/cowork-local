"""Cowork Multi-Agent: Planner(Pro) + OpenCode Workers + Validation + Review + Loop + Redis Memory"""
import logging, json, subprocess, os, httpx
from typing import Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from .state import CoworkState
import redis

logger = logging.getLogger(__name__)
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
COWORK_DIR = "/media/SSD1T/cowork-local"

# Redis memoria rápida
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

PLANNER_SYSTEM = """You are an AI assistant that executes tasks. Read the request and decide the BEST way.

CLASSIFY the intent first:
- "code_generation": Create a new Python project/CLI/API/library
- "tool_filesystem": Find, list, count, or search files (includes questions about files, directories, storage)
- "tool_document": Analyze, modify, or create documents (PDF, Excel)
- "tool_web": Browse the web, apply to jobs, search
- "tool_shell": Execute commands or scripts
- "chat": Answer a question, no action needed

EXAMPLES:
- "¿Cómo listo archivos?" → chat (asking HOW, not executing)
- "¿Cuántos archivos hay?" → tool_filesystem (asking about files)
- "¿Qué es Docker?" → chat (knowledge question)
- "Ejecuta ls -la" → tool_shell (direct command execution)
- "Corré backup.sh" → tool_shell (script execution)
- "Buscá PDFs" → tool_filesystem (file search)
- "Analiza documento.pdf" → tool_document (document analysis)
- "Leé archivo.txt" → tool_document (read file content)
- "Revisa el Excel" → tool_document (spreadsheet analysis)
- "¿Cómo creo un CLI?" → chat (asking for help)
- "Creá un CLI" → code_generation (building something)
- "Hola" → chat (greeting)
- "¿Qué podés hacer?" → chat (capability question)
- "De esos, ¿cuántos hay?" → chat (user refers to PREVIOUS results in history)
- "¿Cuál es el más grande?" → chat (user asks about PREVIOUS results)
- "Explicame eso" → chat (user wants explanation of PREVIOUS results)

RULES:
- The CURRENT USER MESSAGE determines the project_type. History is context only, not instructions.
- Classify based on what the user is asking NOW, not what they asked before.
- If CONVERSATION HISTORY is provided, USE IT. Do NOT search again if the answer is in the history.
- If user says "De esos", "De esos archivos", "Cuál de esos" → they refer to results in the history. Answer from history.
- If user asks HOW to do something → chat (they want explanation, not execution)
- If user asks WHAT is something → chat (knowledge question)
- If user asks to EXECUTE a specific command → tool_shell
- If user mentions NEW files/directories not in history → tool_filesystem
- If user wants to BUILD/CREATE code → code_generation
- Questions with "?" that ask for information → usually chat
- When history exists, prefer chat responses based on history over new searches

Output ONLY valid JSON:
{
  "project_name": "name",
  "project_description": "what to do",
  "project_type": "code_generation|tool_filesystem|tool_document|tool_web|tool_shell|chat",
  "steps": [{"id":1, "agent":"opencode", "task":"specific action"}]
}
CRITICAL: If project_type starts with "tool_" or is "chat", DO NOT create a Python project.
If the user just says hello, asks a question, or chats without requesting an action, use project_type "chat" and respond helpfully."""

def call_deepseek(system, prompt, json_mode=True):
    try:
        payload = {"model":"deepseek-chat","messages":[{"role":"system","content":system},{"role":"user","content":prompt}],"max_tokens":4096,"temperature":0.1}
        if json_mode: payload["response_format"] = {"type":"json_object"}
        r = httpx.post(DEEPSEEK_URL, json=payload, headers={"Authorization":f"Bearer {DEEPSEEK_KEY}"}, timeout=180)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return '{"error":"%s"}' % str(e)

def call_opencode(task, project_dir):
    """Llama a OpenCode CLI para generar código."""
    try:
        prompt = f"Create {task}. Write files in {project_dir}. Return JSON with files array."
        result = subprocess.run(
            ["opencode", "run", "--model", "opencode/deepseek-v4-flash-free", prompt],
            capture_output=True, text=True, timeout=1800,
            cwd=COWORK_DIR,
            env={**os.environ, "DEEPSEEK_API_KEY": DEEPSEEK_KEY}
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"

def run_pytest(project_dir):
    try:
        subprocess.run(f"cd {project_dir} && pip install -e . 2>&1 | tail -2", shell=True, capture_output=True, text=True, timeout=180)
        # Buscar tests en tests/ o en raíz
        has_tests_dir = os.path.isdir(os.path.join(project_dir, "tests"))
        has_pyproject = os.path.isfile(os.path.join(project_dir, "pyproject.toml"))
        if has_pyproject:
            r = subprocess.run(f"cd {project_dir} && python -m pytest -v 2>&1", shell=True, capture_output=True, text=True, timeout=180)
        elif has_tests_dir:
            r = subprocess.run(f"cd {project_dir} && python -m pytest tests/ -v 2>&1", shell=True, capture_output=True, text=True, timeout=180)
        else:
            r = subprocess.run(f"cd {project_dir} && python -m pytest -v 2>&1", shell=True, capture_output=True, text=True, timeout=180)
        return r.stdout + r.stderr
    except Exception as e:
        return f"ERROR: {e}"


def execute_mcp_tool(project_type: str, query: str, state) -> str:
    """Ejecuta la herramienta MCP correspondiente según el tipo de tarea."""
    result = ""
    
    try:
        if project_type == "tool_filesystem":
            import re, os
            # Extraer path del query
            path_match = re.search(r'/(?:media|home|tmp)/[^\s]*', query)
            path = path_match.group(0) if path_match else "/media/SSD1T/"
            ext_match = re.search(r'\.(\w+)', query)
            pattern = ext_match.group(1) if ext_match else None
            
            # Buscar archivos con os.walk (sin depender del MCP)
            found = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    if pattern is None or f.endswith('.' + pattern):
                        found.append(os.path.join(root, f))
                if len(found) > 50:
                    break
            result = "📁 Archivos encontrados en " + path + ":\n" + "\n".join(found[:20])
            if not found:
                result = "📁 No se encontraron archivos" + (f" .{pattern}" if pattern else "") + " en " + path
        
        elif project_type == "tool_document":
            import os
            import re
            path_match = re.search(r'/(?:media|home|tmp)/[^\s]*\.\w+', query)
            filepath = path_match.group(0) if path_match else None
            
            if filepath and os.path.exists(filepath):
                ext = filepath.split('.')[-1].lower()
                try:
                    if ext == 'pdf':
                        from pypdf import PdfReader
                        reader = PdfReader(filepath)
                        text = "\n".join([p.extract_text() or '' for p in reader.pages[:5]])
                        result = f"📄 PDF: {filepath}\nPaginas: {len(reader.pages)}\n\n{text[:1000]}"
                    elif ext in ('xlsx', 'xls'):
                        import pandas as pd
                        df = pd.read_excel(filepath)
                        result = f"📊 Excel: {filepath}\nFilas: {len(df)}\nColumnas: {list(df.columns)}\n\n{df.head(10).to_string()}"
                    elif ext in ('csv', 'txt', 'md', 'py', 'json', 'log'):
                        with open(filepath) as f:
                            text = f.read()
                        result = f"📝 Archivo: {filepath}\n{text[:1000]}"
                    else:
                        result = f"📁 Archivo no soportado: {filepath} (.{ext})"
                except Exception as e:
                    result = f"📄 Error al leer {filepath}: {str(e)[:200]}"
            else:
                result = "📄 Por favor especifica la ruta completa al archivo. Ej: 'Analiza /media/SSD1T/documento.pdf'"
        elif project_type == "tool_web":
            import os
            import re, asyncio
            os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', '/media/SSD1T/cowork-local/browsers')
            
            url_match = re.search(r'https?://[^\s]+', query)
            url = url_match.group(0) if url_match else "https://www.google.com"
            
            try:
                async def _browse():
                    from playwright.async_api import async_playwright
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        page = await browser.new_page()
                        await page.goto(url, timeout=15000)
                        title = await page.title()
                        text = await page.inner_text('body')
                        await browser.close()
                        return title, text[:1000]
                
                title, text = asyncio.run(_browse())
                result = f"🌐 {url}\nTitulo: {title}\n\n{text[:500]}"
            except Exception as e:
                result = f"🌐 Error al navegar: {str(e)[:200]}"
        elif project_type == "tool_shell":
            import subprocess
            # Extraer comando del query (case insensitive)
            qlower = query.lower()
            if "ejecutá" in qlower or "ejecuta" in qlower or "ejecutar" in qlower:
                for w in ["ejecutá", "ejecuta", "ejecutar"]:
                    if w in qlower:
                        cmd = query.lower().split(w, 1)[-1].strip()
                        break
            elif "corré" in qlower or "corre" in qlower or "correr" in qlower:
                for w in ["corré", "corre", "correr"]:
                    if w in qlower:
                        cmd = query.lower().split(w, 1)[-1].strip()
                        break
            elif "run " in qlower:
                cmd = query.lower().split("run ", 1)[-1].strip()
            else:
                cmd = query
            # Limpiar --confirm del comando
            cmd = cmd.replace(" --confirm", "").replace("--confirm", "").strip()
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            result = "💻 Comando ejecutado:\n" + (output.stdout or output.stderr)[:500]
        
        elif project_type == "chat":
            # Si hay historial, usar DeepSeek para respuesta contextual
            session_id = state.session_id
            history = redis_client.lrange(f"chat:{session_id}", 0, -1)
            if history and len(history) >= 2:
                # Usar DeepSeek para responder basándose en el historial
                context = "\n".join(history[-6:])
                response = call_deepseek(
                    "You are a helpful assistant. Answer the user based on the conversation history. Be concise and specific. If the history has file search results, reference them directly.",
                    f"History:\n{context}\n\nUser: {state.user_query}\n\nAnswer:",
                    json_mode=False
                )
                result = response
            else:
                result = "¡Hola! Soy tu asistente Cowork. Puedo:\n• Buscar archivos en tu PC\n• Crear proyectos Python\n• Analizar documentos\n• Ejecutar comandos\n• Navegar internet\n\n¿En qué te ayudo?"
        
        else:
            result = "Tarea ejecutada: " + query[:100] + "..."
        
        state.add_artifact("log", result)
        return result
    
    except Exception as e:
        logger.error(f"MCP tool error: {e}")
        return "❌ Error al ejecutar herramienta: " + str(e)[:200]

def task_intake(state): return state.model_dump()

def planner(state):
    logger.info(f"[PLANNER] iter {state.iteration_count+1}/{state.max_iterations}")
    
    # Redis: cachear plan si ya se consultó este prompt
    cache_key = f"plan:{hash(state.user_query) % 100000}"
    if state.iteration_count == 0:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info("[PLANNER] Usando plan cacheado en Redis")
            plan = json.loads(cached)
            state.metadata["project_name"] = plan.get("project_name","project")
            state.metadata["flags"] = str(plan.get("flags",[]))
            state.metadata["project_description"] = plan.get("project_description","")
            state.metadata["project_type"] = plan.get("project_type","code_generation")
            state.add_step(description=state.user_query, assigned_to="executor", step_type="code_generation")
            state.iteration_count += 1
            return state.model_dump()
    
    feedback = ""
    if state.errors:
        # Redis: qué falló antes?
        prev_failures = redis_client.lrange(f"failures:{state.metadata.get('project_name','')}", 0, -1)
        feedback = "Fix these errors:\n" + "\n".join(prev_failures[-5:] + [str(e) for e in state.errors[-3:]])
        query = feedback + "\n\nOriginal: " + state.user_query
    else:
        query = state.user_query
    
    # Cargar historial de conversación desde Redis
    session_id = state.session_id
    history = redis_client.lrange(f"chat:{session_id}", 0, -1)
    if history:
        context = "\n".join(history[-6:])  # Últimos 6 mensajes
        query = f"Conversation history (use this for context):\n{context}\n\nCurrent user message: {state.user_query}"
        logger.info(f"[PLANNER] Contexto cargado: {len(history)} mensajes en historial")
    
    response = call_deepseek(PLANNER_SYSTEM, query)
    try:
        plan = json.loads(response)
        state.plan = []
        state.metadata["project_name"] = plan.get("project_name","project")
        state.metadata["flags"] = str(plan.get("flags",[]))
        state.metadata["project_description"] = plan.get("project_description","")
        state.metadata["project_type"] = plan.get("project_type","code_generation")
        for s in plan.get("steps",[]):
            state.add_step(description=s.get("task",""), assigned_to="executor", step_type="code_generation")
        state.add_artifact("plan", json.dumps(plan, indent=2))
        # Redis: cachear plan por 1 hora
        redis_client.setex(cache_key, 3600, json.dumps(plan))
        logger.info(f"[PLANNER] {len(state.plan)} steps, project={state.metadata['project_name']}")
    except:
        state.add_step(description=state.user_query, assigned_to="executor", step_type="code_generation")
    state.iteration_count += 1
    return state.model_dump()

def worker_opencode(state):
    global COWORK_DIR
    logger.info("[WORKER] Executing...")
    project_name = state.metadata.get("project_name","project")
    project_type = state.metadata.get("project_type", "code_generation")
    description = state.metadata.get("project_description", state.user_query)
    
    # Si es tarea de herramienta o chat, usar MCPs directo
    if project_type.startswith("tool_") or project_type == "chat":
        # SEGURIDAD NIVEL 2: tool_shell y tool_web requieren --confirm
        dangerous = project_type in ("tool_shell", "tool_web")
        if dangerous and "--confirm" not in state.user_query.lower():
            result_text = "⚠️ Esta acción puede modificar tu sistema. Para confirmar, volvé a escribir el mensaje agregando '--confirm' al final.\n\nEjemplo: 'Ejecuta ls -la --confirm'"
            state.add_artifact("log", result_text[:1000])
            state.metadata["tests_passed"] = 1
            state.metadata["tests_failed"] = 0
            state.metadata["complete"] = True
            state.metadata["reply"] = result_text
            for step in state.plan: step.status = "done"
            return state.model_dump()
        
        logger.info(f"[WORKER] Using MCP tool for: {project_type}")
        result_text = execute_mcp_tool(project_type, state.user_query, state)
        state.add_artifact("log", result_text[:1000])
        state.metadata["tests_passed"] = 1
        state.metadata["tests_failed"] = 0
        state.metadata["complete"] = True
        state.metadata["reply"] = result_text  # Guardar respuesta real
        for step in state.plan: step.status = "done"
        return state.model_dump()
    
    # Si es generación de código, usar OpenCode
    project_dir = os.path.join(COWORK_DIR, project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    if project_type in ("json_file", "documentation", "other", "library"):
        full_prompt = f"{description}. Return JSON with files array. Do NOT create a Python project. Do NOT create cli.py or core.py. Do NOT add tests."
        state.metadata["complete"] = True
        state.metadata["tests_passed"] = 0
        state.metadata["tests_failed"] = 0
        logger.info(f"[WORKER] {project_type} mode - skipping pytest")
        output = call_opencode(full_prompt, project_dir)
        state.add_artifact("log", output[:1000])
        for step in state.plan: step.status = "done"
        return state.model_dump()
    else:
        files_list = state.metadata.get("files", [])
        files_str = ", ".join(files_list[:8]) if files_list else "appropriate files"
        flags = state.metadata.get("flags","[]")
        full_prompt = f"Create a Python {project_type} project called '{project_name}'. {description}. Project type: {project_type}. Required files: {files_str}. Flags: {flags}. Return JSON with files array."
    
    output = call_opencode(full_prompt, project_dir)
    state.add_artifact("log", output[:1000])
    
    test_output = run_pytest(project_dir)
    passed = test_output.count("PASSED")
    failed = test_output.count("FAILED")
    state.metadata["tests_passed"] = passed
    state.metadata["tests_failed"] = failed
    state.metadata["last_project_dir"] = project_dir
    state.add_artifact("log", test_output[:1000])
    
    if failed > 0:
        import re
        for match in re.finditer(r'FAILED (tests/\S+) - (.+)', test_output):
            redis_client.rpush(f"failures:{project_name}", f"{match.group(1)}: {match.group(2)[:150]}")
        redis_client.expire(f"failures:{project_name}", 600)
    
    for step in state.plan: step.status = "done"
    if failed > 0:
        state.add_error(f"{failed} tests failed, {passed} passed")
        state.metadata["complete"] = False
    else:
        state.metadata["complete"] = True
        redis_client.delete(f"failures:{project_name}")
    
    logger.info(f"[WORKER] {passed} passed, {failed} failed -> {project_dir}")
    return state.model_dump()
def validation(state): return state.model_dump()

def review(state):
    logger.info("[REVIEW]")
    passed = state.metadata.get("tests_passed", 0)
    failed = state.metadata.get("tests_failed", 0)
    total = passed + failed
    if total == 0:
        logger.warning("[REVIEW] No tests found - project may be incomplete")
        state.metadata["complete"] = False
        state.add_error("No tests were executed")
    elif failed == 0 and passed > 0:
        state.metadata["complete"] = True
    else:
        state.metadata["complete"] = False
    return state.model_dump()

def decision(state):
    if state.metadata.get("complete"):
        logger.info("[DECISION] DONE")
        # Guardar en historial de chat
        session_id = state.session_id
        redis_client.rpush(f"chat:{session_id}", f"Usuario: {state.user_query}")
        reply = state.metadata.get("reply", "Tarea completada")
        redis_client.rpush(f"chat:{session_id}", f"Asistente: {reply[:800]}")
        redis_client.expire(f"chat:{session_id}", 3600)
        logger.info("[DECISION] Historial guardado en Redis")
        # Notificar por n8n
        try:
            import requests
            requests.post("http://localhost:5678/webhook/cowork-telegram", json={
                "project": state.metadata.get("project_name", "proyecto"),
                "tests": f"{state.metadata.get('tests_passed',0)}/{state.metadata.get('tests_passed',0)+state.metadata.get('tests_failed',0)}",
                "path": state.metadata.get("last_project_dir", "")
            }, timeout=5)
            logger.info("[DECISION] Notificación enviada a Telegram via n8n")
        except Exception as e:
            logger.warning(f"[DECISION] No se pudo notificar: {e}")
        return END
    if state.iteration_count >= state.max_iterations:
        # Redis: guardar resumen final
        redis_client.setex(f"last_run:{state.metadata.get('project_name','')}", 3600, 
            f"{state.metadata.get('tests_passed',0)} passed, {state.metadata.get('tests_failed',0)} failed")
        logger.info("[DECISION] MAX")
        return END
    logger.info(f"[DECISION] Loop {state.iteration_count}/{state.max_iterations}")
    return "planner"

def build_graph():
    workflow = StateGraph(CoworkState)
    for name, fn in [("intake",task_intake),("planner",planner),("worker",worker_opencode),("validation",validation),("review",review)]:
        workflow.add_node(name, fn)
    workflow.set_entry_point("intake")
    workflow.add_edge("intake","planner")
    workflow.add_edge("planner","worker")
    workflow.add_edge("worker","validation")
    workflow.add_edge("validation","review")
    workflow.add_conditional_edges("review", decision, {"planner":"planner",END:END})
    return workflow.compile()

def run_graph(user_query, project_path=COWORK_DIR, max_iterations=5):
    state = CoworkState(user_query=user_query, project_path=project_path, max_iterations=max_iterations)
    graph = build_graph()
    result = graph.invoke(state, {"recursion_limit": max_iterations * 10})
    final_state = CoworkState(**result)
    logger.info(f"DONE: {final_state.metadata.get('tests_passed',0)} passed, {final_state.metadata.get('tests_failed',0)} failed")
    return final_state

def continue_graph(previous_state: CoworkState, new_query: str, max_iterations: int = 5):
    """Continúa una sesión existente con una nueva query, preservando el contexto."""
    logger.info(f"[CONTINUE] Session {previous_state.session_id[:8]}... nueva query: {new_query[:80]}...")
    previous_state.continue_session(new_query)
    previous_state.max_iterations = max_iterations
    # Mantener errores relevantes de la sesión anterior para feedback
    graph = build_graph()
    result = graph.invoke(previous_state, {"recursion_limit": max_iterations * 10})
    final_state = CoworkState(**result)
    logger.info(f"DONE: {final_state.metadata.get('tests_passed',0)} passed, {final_state.metadata.get('tests_failed',0)} failed")
    return final_state

# Cache de última sesión en Redis (persiste entre ejecuciones)
def get_last_state() -> Optional[dict]:
    """Recupera el último estado desde Redis."""
    try:
        data = redis_client.get("cowork:last_state")
        if data:
            return json.loads(data)
    except:
        pass
    return None

def save_last_state(state_dict: dict) -> None:
    """Guarda el último estado en Redis (TTL 1 hora)."""
    try:
        redis_client.setex("cowork:last_state", 3600, json.dumps(state_dict, default=str))
    except:
        pass


