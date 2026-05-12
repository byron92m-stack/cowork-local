"""LangGraph 6 nodos con DeepSeek multi-archivo + auto-instalacion + tests"""
import logging, json, subprocess, os, httpx
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from .state import CoworkState

logger = logging.getLogger(__name__)
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
COWORK_DIR = "/media/SSD1T/cowork-local"

def _load_prompt():
    with open(os.path.join(COWORK_DIR, "apps", "cli", "worker_prompt.txt")) as f:
        return f.read().strip()

def call_deepseek(system, prompt, json_mode=False):
    try:
        payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.1}
        if json_mode: payload["response_format"] = {"type": "json_object"}
        r = httpx.post(DEEPSEEK_URL, json=payload, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return '{"error": "%s"}' % str(e)

def call_worker(prompt):
    try:
        sp = _load_prompt()
        r = httpx.post(DEEPSEEK_URL, json={"model": "deepseek-chat", "messages": [{"role": "system", "content": sp}, {"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.1, "response_format": {"type": "json_object"}}, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=120)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return '{"error": "%s"}' % str(e)

def save_files(json_response):
    try:
        data = json.loads(json_response)
        created = []
        
        # Formato 1: {"files": [{"name":..., "content":...}]}
        files = data.get("files", [])
        if files:
            for f in files:
                path = f.get("path", "") or f.get("name", "")
                fc = f.get("content", "")
                if path and fc:
                    if not path.startswith("/"): path = os.path.join(COWORK_DIR, "output", path)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as fh: fh.write(fc)
                    created.append(path)
            return created
        
        # Formato 2: {"name": "project", "content": {"file.py": "code", ...}}
        content_dict = data.get("content", {})
        if isinstance(content_dict, dict):
            for path, fc in content_dict.items():
                if path and fc and isinstance(fc, str):
                    if not path.startswith("/"): path = os.path.join(COWORK_DIR, "output", path)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as fh: fh.write(fc)
                    created.append(path)
            return created
        
        return []
    except: return []

def execute_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=COWORK_DIR, timeout=30)
        return result.stdout.strip() or result.stderr.strip() or "(ok)"
    except: return "ERROR"

def task_intake(state):
    logger.info("[INTAKE]")
    return state.model_dump()

def deepseek_planner(state):
    logger.info("[PLANNER]")
    response = call_deepseek("Eres arquitecto. Solo respondes JSON.", 'Tarea: %s\nGenera plan JSON: {"steps":[{"id":1,"goal":"...","type":"code"}]}' % state.user_query, json_mode=True)
    try:
        plan = json.loads(response)
        for s in plan.get("steps", []):
            state.add_step(description=s.get("goal",""), assigned_to="executor", step_type="code_generation")
        if state.plan and not state.current_step_id:
            state.current_step_id = state.plan[0].id
            state.plan[0].status = "in_progress"
        state.add_artifact("plan", response)
    except:
        state.add_step(description=state.user_query, assigned_to="executor", step_type="code_generation")
    state.iteration_count += 1
    return state.model_dump()

def qwen_worker(state):
    logger.info("[WORKER]")
    step = state.get_current_step()
    if step and step.assigned_to == "executor":
        prompt = "Create a complete project: %s. Generate ALL files. Return JSON with files array." % step.description
        json_response = call_worker(prompt)
        created = save_files(json_response)
        logger.info("[WORKER] %d archivos: %s" % (len(created), created))
        state.add_artifact("code", json_response[:500], created[0] if created else None)
        step.status = "done"
        if created:
            project_dir = os.path.dirname(created[0])
            execute_command("cd %s && pip install -e . 2>&1 | tail -3" % project_dir)
            test_result = execute_command("cd %s && python -m pytest -v 2>&1 | tail -15" % project_dir)
            state.add_artifact("log", test_result)
    return state.model_dump()

def validation(state):
    logger.info("[VALIDATION]")
    return state.model_dump()

def supervisor_review(state):
    logger.info("[REVIEW]")
    artifacts_summary = "\n".join([a.content[:200] for a in state.artifacts[-3:] if a.content])
    response = call_deepseek("Supervisor. Solo JSON.", 'Tarea: %s\nResultados: %s\nCompletado? JSON: {"complete":true/false,"comments":"..."}' % (state.user_query, artifacts_summary), json_mode=True)
    try:
        review = json.loads(response)
        state.metadata["complete"] = review.get("complete", False)
        state.add_artifact("review", review.get("comments",""))
    except:
        state.metadata["complete"] = state.is_complete()
    return state.model_dump()

def loop_decision(state):
    if state.metadata.get("complete") or state.is_complete() or state.iteration_count >= state.max_iterations:
        logger.info("[DECISION] FIN %d/%d" % (state.iteration_count, state.max_iterations))
        return END
    logger.info("[DECISION] Loop %d/%d" % (state.iteration_count, state.max_iterations))
    return "planner"

def build_graph():
    workflow = StateGraph(CoworkState)
    for name, fn in [("intake", task_intake), ("planner", deepseek_planner), ("worker", qwen_worker), ("validation", validation), ("review", supervisor_review)]:
        workflow.add_node(name, fn)
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "planner")
    workflow.add_edge("planner", "worker")
    workflow.add_edge("worker", "validation")
    workflow.add_edge("validation", "review")
    workflow.add_conditional_edges("review", loop_decision, {"planner":"planner", END:END})
    return workflow.compile()

def run_graph(user_query, project_path=COWORK_DIR, max_iterations=3):
    state = CoworkState(user_query=user_query, project_path=project_path, max_iterations=max_iterations)
    graph = build_graph()
    result = graph.invoke(state, {"recursion_limit": max_iterations * 10})
    return CoworkState(**result)
