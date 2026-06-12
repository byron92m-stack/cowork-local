"""Cowork: Ejecuta el grafo LangGraph completo."""
import sys, os, json, logging, redis

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

from graph.graph import run_graph

if __name__ == "__main__":
    # Modo diseño directo (sin planner)
    if "--design" in sys.argv:
        from graph.graph_design import build_design_graph
        from graph.state import DesignWorkerState
        
        action = sys.argv[-1] if len(sys.argv) > 2 else "generate"
        skill_map = {"generate": "campaign_generate", "view": "campaign_view", 
                     "approve": "campaign_approve", "list": "campaign_list"}
        skill = skill_map.get(action, action)
        
        state = DesignWorkerState(query="", skill=skill)
        graph = build_design_graph()
        result = graph.invoke(state)
        print(result.get("reply", "Sin respuesta"))
        sys.exit(0)
    
    args = sys.argv[1:]
    
    # Detectar --session
    session_name = "pc-terminal"
    query_parts = []
    for i, arg in enumerate(args):
        if arg == "--session" and i + 1 < len(args):
            session_name = args[i + 1]
        elif not (i > 0 and args[i-1] == "--session"):
            query_parts.append(arg)
    
    query = " ".join(query_parts) if query_parts else "Hola"
    max_iter = int(os.getenv("COWORK_MAX_ITER", "5"))
    
    # Guardar sesión en Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.setex(f"cowork:session:{session_name}", 3600, json.dumps({"active": True, "device": "pc"}))
    
    print(f"> build · cowork (Planner Pro + Worker Flash FREE) [sesión: {session_name}]")
    print(f"> Query: {query[:100]}...\n")
    
    result = run_graph(user_query=query, max_iterations=max_iter)
    
    passed = result.metadata.get("tests_passed", 0)
    failed = result.metadata.get("tests_failed", 0)
    total = passed + failed
    complete = result.metadata.get("complete", False)
    project = result.metadata.get("project_name", "desconocido")
    
    print(f"\n{'='*50}")
    print(f"✅ {project}")
    print(f"   Tests: {passed}/{total} passed" if total > 0 else f"   Tests: {passed} passed")
    print(f"   Completo: {complete}")
    print(f"   Iteraciones: {result.iteration_count}/{max_iter}")
    print(f"   Sesión: {session_name}")
    print(f"{'='*50}")
