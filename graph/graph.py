"""Cowork Multi-Agent: Planner(Pro) + OpenCode Workers + Validation + Review + Loop + Redis Memory"""
import logging, json, os
from typing import Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from .state import CoworkState, CodeWorkerState, DesignWorkerState
from .graph_code import build_code_graph
from .graph_design import build_design_graph
from .graph_mcp import build_mcp_graph
from .redis_client import get_redis

logger = logging.getLogger(__name__)
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
COWORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Redis memoria rápida (shared)
redis_client = get_redis()

PLANNER_SYSTEM = open(os.path.join(os.path.dirname(__file__), "prompts/planner_system.txt")).read()

def _get_llm():
    from models.deepseek_client import DeepSeekClient
    return DeepSeekClient()

def call_deepseek(system, prompt, json_mode=True):
    try:
        client = _get_llm()
        return client.chat(system=system, prompt=prompt, json_mode=json_mode)
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
    # Si hay contenido extraído (ej. de PDF), añadirlo al query
    augmented_query = state.user_query
    if state.reply and len(state.reply) > 100:
        augmented_query = f"{state.user_query}\n\nCONTENIDO DEL PDF:\n{state.reply}"
    
    # Ejecutar sub-grafo
    code_state = CodeWorkerState(
        query=augmented_query,
        project_name=state.metadata.get("project_name", "project")
    )
    result = build_code_graph().invoke(code_state)
    
    return {
        "reply": result["reply"],
        "metadata": {
            **state.metadata,
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
        "reply": result["reply"],
        "metadata": {
            **state.metadata,
            "complete": result.get("complete", False)
        },
        "artifacts": [{"type": "log", "content": result["reply"]}]
    }


def task_intake(state: CoworkState) -> dict: return state.model_dump()

def planner(state: CoworkState) -> dict:
    logger.info(f"[PLANNER] iter {state.iteration_count+1}/{state.max_iterations}")
    
    # Redis: cachear plan si ya se consultó este prompt
    import hashlib
    cache_key = f"plan:{hashlib.sha256(state.user_query.encode()).hexdigest()[:16]}"
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
    history = redis_client.lrange(f"chat:{session_id}", -6, -1)  # Solo últimos 6 mensajes
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
    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.warning(f"Plan parse error: {e}")
        state.add_step(description=state.user_query, assigned_to="executor", step_type="code_generation")
    state.iteration_count += 1
    return state.model_dump()


def review(state: CoworkState) -> dict:
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

def decision(state: CoworkState) -> str:
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
            n8n_token = os.getenv("N8N_WEBHOOK_TOKEN", "")
            headers = {"Authorization": f"Bearer {n8n_token}"} if n8n_token else {}
            requests.post("http://localhost:5678/webhook/cowork-telegram", json={
                "project": state.metadata.get("project_name", "proyecto"),
                "tests": f"{state.metadata.get('tests_passed',0)}/{state.metadata.get('tests_passed',0)+state.metadata.get('tests_failed',0)}",
                "path": state.metadata.get("last_project_dir", "")
            }, headers=headers, timeout=5)
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
    except Exception as e:
        logger.warning(f"Redis get_last_state error: {e}")
        return None

def save_last_state(state_dict: dict) -> None:
    """Guarda el último estado en Redis (TTL 1 hora)."""
    try:
        redis_client.setex("cowork:last_state", 86400, json.dumps(state_dict, default=str))
    except Exception as e:
        logger.warning(f"Redis save_last_state error: {e}")


