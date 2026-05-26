"""Cowork Multi-Agent: Planner(Pro) + OpenCode Workers + Validation + Review + Loop + Redis Memory"""
import logging, json, subprocess, os, httpx
from typing import Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from .state import CoworkState, CodeWorkerState, DesignWorkerState
from .graph_code import build_code_graph
from .graph_design import build_design_graph
from .graph_mcp import build_mcp_graph
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
- "tool_design": Design frontend, landing pages, dashboards, presentations, UI/UX
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
  "project_type": "code_generation|tool_filesystem|tool_document|tool_web|tool_design|tool_shell|chat",
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



def mcp_wrapper(state: CoworkState) -> dict:
    """Wrapper que ejecuta el sub-grafo MCP y mapea resultados."""
    result = build_mcp_graph().invoke(state)
    return {
        "reply": result.get("reply", "Tarea completada"),
        "metadata": {
            **state.metadata,
            "tests_passed": result.get("tests_passed", 1),
            "tests_failed": result.get("tests_failed", 0),
            "complete": result.get("complete", True)
        },
        "artifacts": [{"type": "log", "content": result.get("reply", "")}]
    }


def code_wrapper(state: CoworkState) -> dict:
    """Wrapper que ejecuta el sub-grafo y mapea resultados."""
    # Ejecutar sub-grafo
    code_state = CodeWorkerState(
        query=state.user_query,
        project_name=state.metadata.get("project_name", "project")
    )
    result = build_code_graph().invoke(code_state)
    
    return {
        "metadata": {
            **state.metadata,
            "reply": result["reply"],
            "tests_passed": result.get("tests_passed", 0),
            "tests_failed": result.get("tests_failed", 0),
            "complete": result.get("complete", False)
        },
        "artifacts": [{"type": "log", "content": result["reply"]}]
    }


def design_wrapper(state: CoworkState) -> dict:
    """Wrapper que ejecuta el sub-grafo de diseño y mapea resultados."""
    design_state = DesignWorkerState(
        query=state.user_query
    )
    result = build_design_graph().invoke(design_state)
    
    return {
        "metadata": {
            **state.metadata,
            "reply": result["reply"],
            "complete": result.get("complete", False)
        },
        "artifacts": [{"type": "log", "content": result["reply"]}]
    }


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
        redis_client.expire(f"chat:{session_id}", 86400)
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
    """Grafo principal con sub-grafos para cada worker."""
    workflow = StateGraph(CoworkState)
    
    workflow.add_node("intake", task_intake)
    workflow.add_node("planner", planner)
    workflow.add_node("code_worker", code_wrapper)
    workflow.add_node("design_worker", design_wrapper)
    workflow.add_node("mcp_worker", mcp_wrapper)
    workflow.add_node("review", review)
    
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "planner")
    
    def route_to_worker(state: CoworkState) -> str:
        pt = state.metadata.get("project_type", "code_generation")
        if pt == "tool_design":
            return "design_worker"
        elif pt.startswith("tool_") or pt == "chat":
            return "mcp_worker"
        else:
            return "code_worker"
    
    workflow.add_conditional_edges(
        "planner", route_to_worker,
        {"code_worker": "code_worker", "design_worker": "design_worker", "mcp_worker": "mcp_worker"}
    )
    
    workflow.add_edge("code_worker", "review")
    workflow.add_edge("design_worker", "review")
    workflow.add_edge("mcp_worker", "review")
    workflow.add_conditional_edges("review", decision, {"planner": "planner", END: END})
    
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
        redis_client.setex("cowork:last_state", 86400, json.dumps(state_dict, default=str))
    except:
        pass


