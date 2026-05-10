"""Comando para ejecutar el grafo desde el CLI de Claude Code."""
import sys, os, json, logging
sys.path.insert(0, "/media/SSD1T/cowork-local")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

from graph.graph import run_graph

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Crea un proyecto Python"
    max_iter = int(os.getenv("COWORK_MAX_ITER", "3"))
    
    print(f"🚀 Ejecutando grafo: {query}")
    print(f"   Máx iteraciones: {max_iter}")
    print()
    
    result = run_graph(user_query=query, max_iterations=max_iter)
    
    # Output limpio para Claude Code
    output = {
        "pasos": len(result.plan),
        "artefactos": len(result.artifacts),
        "errores": len(result.errors),
        "iteraciones": result.iteration_count,
        "completado": result.metadata.get("complete", False),
        "archivos": [a.path for a in result.artifacts if a.path and a.type == "code"]
    }
    
    print("\n📊 RESULTADO:")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    # Mostrar código generado
    for a in result.artifacts:
        if a.type == "code" and a.path and os.path.exists(a.path):
            print(f"\n📁 {a.path}:")
            with open(a.path) as f:
                print(f.read()[:500])
# test watcher
