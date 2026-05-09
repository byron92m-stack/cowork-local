"""
LangGraph con 7 nodos según blueprint:
intake → planner → worker → validation → review → decision → loop
"""
import logging, json, subprocess, os, httpx
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from .state import CoworkState

logger = logging.getLogger(__name__)

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-122139651350414899e1617d190c94f3")
OLLAMA_URL = "http://localhost:11434/api/generate"
COWORK_DIR = "/media/SSD1T/cowork-local"

# ─── Helpers ──────────────────────────────────────────────
def call_deepseek(system: str, prompt: str, json_mode=False) -> str:
    try:
        payload = {"model": "deepseek-chat", "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ], "max_tokens": 4096, "temperature": 0.1}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        r = httpx.post(DEEPSEEK_URL, json=payload, headers={
            "Authorization": f"Bearer {DEEPSEEK_KEY}"
        }, timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'

def call_qwen(prompt: str) -> str:
    try:
        r = httpx.post(OLLAMA_URL, json={
            "model": "qwen3:14b",
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 1024, "temperature": 0.2}
        }, timeout=60)
        return r.json().get("response", "")[:2000]
    except Exception as e:
        return f"ERROR Qwen: {e}"

def execute_command(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, 
                                text=True, cwd=COWORK_DIR, timeout=30)
        return result.stdout.strip() or result.stderr.strip() or "(ok)"
    except Exception as e:
        return f"ERROR: {e}"

# ─── Nodos ────────────────────────────────────────────────
def task_intake(state: CoworkState) -> Dict[str, Any]:
    logger.info("[INTAKE] Tarea recibida")
    state.metadata["started"] = True
    return state.model_dump()

def deepseek_planner(state: CoworkState) -> Dict[str, Any]:
    logger.info("[PLANNER] DeepSeek generando plan")
    prompt = f"""Tarea: {state.user_query}
Contexto: {state.project_context}
Iteración: {state.iteration_count}

Genera un plan JSON con pasos concretos. Formato EXACTO:
{{"steps":[
  {{"id":1,"goal":"descripción","files":["archivo.py"],"type":"code"}}
]}}"""
    
    response = call_deepseek("Eres arquitecto de software. Solo respondes JSON válido.", prompt, json_mode=True)
    logger.info(f"[PLANNER] Respuesta: {response[:200]}")
    
    try:
        plan = json.loads(response)
        for s in plan.get("steps", []):
            raw_type = s.get("type", "code_generation")
            # Mapear tipos de DeepSeek a step_type válidos
            if raw_type in ("code", "generate", "script", "function"):
                step_type = "code_generation"
            elif raw_type in ("test", "tests", "testing"):
                step_type = "code_generation"
            elif raw_type in ("review", "check", "validate"):
                step_type = "review"
            elif raw_type in ("analyze", "analysis", "investigate"):
                step_type = "analysis"
            elif raw_type in ("tool", "command", "execute", "bash"):
                step_type = "tool_call"
            else:
                step_type = "code_generation"
            
            state.add_step(
                description=s.get("goal", s.get("description", "")),
                assigned_to="executor",
                step_type=step_type
            )
        if state.plan and not state.current_step_id:
            state.current_step_id = state.plan[0].id
            state.plan[0].status = "in_progress"
        state.add_artifact("plan", response)
    except Exception as e:
        logger.error(f"[PLANNER] Error parseando JSON: {e}")
        state.add_step(description=state.user_query, assigned_to="executor", step_type="code_generation")
        if not state.current_step_id and state.plan:
            state.current_step_id = state.plan[0].id
            state.plan[0].status = "in_progress"
    
    state.iteration_count += 1
    return state.model_dump()

def qwen_worker(state: CoworkState) -> Dict[str, Any]:
    logger.info("[WORKER] Qwen3 generando código")
    step = state.get_current_step()
    if step and step.assigned_to == "executor":
        prompt = f"Genera SOLO código Python para: {step.description}. Sin explicaciones ni markdown. Solo el código."
        code = call_qwen(prompt)
        filename = f"output/gen_{state.session_id[:8]}_{step.id[:8]}.py"
        filepath = f"{COWORK_DIR}/{filename}"
        with open(filepath, "w") as f:
            f.write(code)
        state.add_artifact("code", code, filepath)
        step.status = "done"
        logger.info(f"[WORKER] Código generado: {filepath} ({len(code)} chars)")
    return state.model_dump()

def validation(state: CoworkState) -> Dict[str, Any]:
    logger.info("[VALIDATION] Ejecutando tests")
    result = execute_command(f"cd {COWORK_DIR}/output && python -m pytest --tb=short 2>&1 | tail -10")
    state.add_artifact("log", result)
    if "FAILED" in result or "ERROR" in result:
        state.errors.append(result[:200])
    return state.model_dump()

def supervisor_review(state: CoworkState) -> Dict[str, Any]:
    logger.info("[REVIEW] DeepSeek revisando")
    artifacts_summary = "\n".join([a.content[:200] for a in state.artifacts[-3:] if a.content])
    prompt = f"""Tarea original: {state.user_query}
Resultados: {artifacts_summary}
Errores: {state.errors[-2:] if state.errors else 'Ninguno'}
Iteraciones: {state.iteration_count}

¿Está la tarea completada? Responde SOLO JSON:
{{"complete": true/false, "comments": "breve explicación"}}"""
    
    response = call_deepseek("Eres supervisor de calidad. Solo respondes JSON.", prompt, json_mode=True)
    try:
        review = json.loads(response)
        state.metadata["complete"] = review.get("complete", False)
        state.add_artifact("review", review.get("comments", ""))
    except:
        state.metadata["complete"] = state.is_complete()
    return state.model_dump()

def loop_decision(state: CoworkState) -> Literal["planner", END]:
    if state.metadata.get("complete") or state.is_complete() or state.iteration_count >= state.max_iterations:
        logger.info(f"[DECISION] FIN. Iteraciones: {state.iteration_count}/{state.max_iterations}")
        return END
    logger.info(f"[DECISION] Loop {state.iteration_count}/{state.max_iterations}")
    return "planner"

# ─── Construir grafo ──────────────────────────────────────
def build_graph() -> StateGraph:
    workflow = StateGraph(CoworkState)
    workflow.add_node("intake", task_intake)
    workflow.add_node("planner", deepseek_planner)
    workflow.add_node("worker", qwen_worker)
    workflow.add_node("validation", validation)
    workflow.add_node("review", supervisor_review)
    
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "planner")
    workflow.add_edge("planner", "worker")
    workflow.add_edge("worker", "validation")
    workflow.add_edge("validation", "review")
    workflow.add_conditional_edges("review", loop_decision, {"planner": "planner", END: END})
    
    return workflow.compile()

def run_graph(user_query: str, project_path: str = COWORK_DIR, max_iterations: int = 3) -> CoworkState:
    state = CoworkState(user_query=user_query, project_path=project_path, max_iterations=max_iterations)
    graph = build_graph()
    config = {"recursion_limit": max_iterations * 10}
    result = graph.invoke(state, config)
    return CoworkState(**result)
