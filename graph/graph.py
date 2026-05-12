"""Cowork Multi-Agent: Planner(Pro) + OpenCode Workers + Validation + Review + Loop"""
import logging, json, subprocess, os, httpx
from langgraph.graph import StateGraph, END
from .state import CoworkState

logger = logging.getLogger(__name__)
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
COWORK_DIR = "/media/SSD1T/cowork-local"

PLANNER_SYSTEM = """You are a senior architect. Create a JSON plan for a Python CLI project.
Output ONLY:
{
  "project_name": "name",
  "project_description": "what to build",
  "flags": ["--flag1", "--flag2"],
  "steps": [
    {"id":1, "agent":"opencode", "task":"Write pyproject.toml and src/{name}/__init__.py"},
    {"id":2, "agent":"opencode", "task":"Write src/{name}/core.py with ALL business logic"},
    {"id":3, "agent":"opencode", "task":"Write src/{name}/cli.py with argparse using ALL flags: --flags"},
    {"id":4, "agent":"opencode", "task":"Write tests/test_core.py with 20+ pytest tests"},
    {"id":5, "agent":"opencode", "task":"Write tests/test_cli.py with 10+ CLI tests"},
    {"id":6, "agent":"opencode", "task":"Write README.md with install, all flags, examples"}
  ]
}"""

def call_deepseek(system, prompt, json_mode=True):
    try:
        payload = {"model":"deepseek-chat","messages":[{"role":"system","content":system},{"role":"user","content":prompt}],"max_tokens":4096,"temperature":0.1}
        if json_mode: payload["response_format"] = {"type":"json_object"}
        r = httpx.post(DEEPSEEK_URL, json=payload, headers={"Authorization":f"Bearer {DEEPSEEK_KEY}"}, timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return '{"error":"%s"}' % str(e)

def call_opencode(task, project_dir):
    """Llama a OpenCode CLI para generar código."""
    try:
        prompt = f"Create {task}. Write files in {project_dir}. Return JSON with files array."
        result = subprocess.run(
            ["opencode", "run", "--model", "opencode/deepseek-v4-flash-free", prompt],
            capture_output=True, text=True, timeout=120,
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
        subprocess.run(f"cd {project_dir} && pip install -e . 2>&1 | tail -2", shell=True, capture_output=True, text=True, timeout=60)
        r = subprocess.run(f"cd {project_dir} && python -m pytest tests/ -v 2>&1", shell=True, capture_output=True, text=True, timeout=60)
        return r.stdout + r.stderr
    except:
        return "ERROR"

def task_intake(state): return state.model_dump()

def planner(state):
    logger.info(f"[PLANNER] iter {state.iteration_count+1}/{state.max_iterations}")
    feedback = ""
    if state.errors:
        feedback = "Fix these errors:\n" + "\n".join([str(e) for e in state.errors[-3:]])
        query = feedback + "\n\nOriginal: " + state.user_query
    else:
        query = state.user_query
    
    response = call_deepseek(PLANNER_SYSTEM, query)
    try:
        plan = json.loads(response)
        state.plan = []
        state.metadata["project_name"] = plan.get("project_name","project")
        state.metadata["flags"] = str(plan.get("flags",[]))
        state.metadata["project_description"] = plan.get("project_description","")
        for s in plan.get("steps",[]):
            state.add_step(description=s.get("task",""), assigned_to="executor", step_type="code_generation")
        state.add_artifact("plan", json.dumps(plan, indent=2))
        logger.info(f"[PLANNER] {len(state.plan)} steps, project={state.metadata['project_name']}")
    except:
        state.add_step(description=state.user_query, assigned_to="executor", step_type="code_generation")
    state.iteration_count += 1
    return state.model_dump()

def worker_opencode(state):
    global COWORK_DIR
    logger.info("[WORKER] OpenCode generating...")
    project_name = state.metadata.get("project_name","project")
    project_dir = os.path.join(COWORK_DIR, project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    # Construir prompt completo para OpenCode
    flags = state.metadata.get("flags","[]")
    description = state.metadata.get("project_description", state.user_query)
    
    full_prompt = f"""Create a Python CLI project called '{project_name}'. {description}
It MUST have these EXACT flags: {flags}
Include: src/{project_name}/cli.py with argparse using ALL flags, src/{project_name}/core.py with all business logic, tests/test_core.py with 20+ pytest tests, tests/test_cli.py with 10+ CLI tests, README.md with all flag examples, pyproject.toml. Return JSON with files array."""
    
    output = call_opencode(full_prompt, project_dir)
    state.add_artifact("log", output[:1000])
    
    # Correr tests
    test_output = run_pytest(project_dir)
    passed = test_output.count("PASSED")
    failed = test_output.count("FAILED")
    state.metadata["tests_passed"] = passed
    state.metadata["tests_failed"] = failed
    state.metadata["last_project_dir"] = project_dir
    state.add_artifact("log", test_output[:1000])
    
    for step in state.plan: step.status = "done"
    if failed > 0:
        state.add_error(f"{failed} tests failed, {passed} passed")
        state.metadata["complete"] = False
    else:
        state.metadata["complete"] = True
    
    logger.info(f"[WORKER] {passed} passed, {failed} failed -> {project_dir}")
    return state.model_dump()

def validation(state): return state.model_dump()

def review(state):
    logger.info("[REVIEW]")
    if state.metadata.get("tests_failed", 0) == 0 and state.metadata.get("tests_passed", 0) > 0:
        state.metadata["complete"] = True
    return state.model_dump()

def decision(state):
    if state.metadata.get("complete"):
        logger.info("[DECISION] DONE")
        return END
    if state.iteration_count >= state.max_iterations:
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

def run_graph(user_query, project_path=COWORK_DIR, max_iterations=4):
    state = CoworkState(user_query=user_query, project_path=project_path, max_iterations=max_iterations)
    graph = build_graph()
    result = graph.invoke(state, {"recursion_limit": max_iterations * 10})
    final_state = CoworkState(**result)
    logger.info(f"DONE: {final_state.metadata.get('tests_passed',0)} passed, {final_state.metadata.get('tests_failed',0)} failed")
    return final_state
