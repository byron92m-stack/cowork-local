#!/usr/bin/env python3
"""
Cowork-Local CLI: Interfaz de línea de comandos.

Uso:
    python -m apps.cli.main run --project /ruta/proyecto --query "Tu consulta"
    python -m apps.cli.main check   # Verificar que todo está configurado
    python -m apps.cli.main status  # Estado de los servicios
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Agregar el proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_logging(level: str = "INFO"):
    """Configura logging para la CLI."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_check(args):
    """Verifica que todos los servicios estén funcionando."""
    print("🔍 Verificando servicios de Cowork-Local...\n")
    
    checks = []
    
    # 1. Ollama
    try:
        import httpx
        response = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        checks.append(("✅ Ollama", f"Conectado. Modelos: {', '.join(model_names) if model_names else 'ninguno'}"))
    except Exception as e:
        checks.append(("❌ Ollama", f"Error: {e}"))
    
    # 2. PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="cowork",
            password="coworkpass",
            database="coworkdb",
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
        table_count = cur.fetchone()[0]
        conn.close()
        checks.append(("✅ PostgreSQL", f"Conectado. {table_count} tablas en la DB."))
    except Exception as e:
        checks.append(("❌ PostgreSQL", f"Error: {e}"))
    
    # 3. DeepSeek API Key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key and api_key != "tu_api_key_aqui":
        checks.append(("✅ DeepSeek", "API key configurada."))
    else:
        checks.append(("⚠️  DeepSeek", "API key no configurada. Edita .env o exporta DEEPSEEK_API_KEY."))
    
    # 4. Directorios
    paths_to_check = [
        ("/media/SSD1T/cowork-local", "Proyecto"),
        ("/media/SSD1T/ollama-models", "Modelos Ollama"),
        ("/media/SSD1T/docker-data", "Datos Docker"),
        ("/media/SSD1T/projects", "Proyectos a analizar"),
    ]
    for path, name in paths_to_check:
        if os.path.exists(path):
            checks.append((f"✅ {name}", f"Existe: {path}"))
        else:
            checks.append((f"❌ {name}", f"No existe: {path}"))
    
    # 5. Python packages
    try:
        import langgraph
        checks.append(("✅ LangGraph", f"Versión {"instalado (ver paquete)"}"))
    except ImportError:
        checks.append(("❌ LangGraph", "No instalado"))
    
    try:
        import pydantic
        checks.append(("✅ Pydantic", f"Versión {pydantic.__version__}"))
    except ImportError:
        checks.append(("❌ Pydantic", "No instalado"))
    
    # Mostrar resultados
    for status, message in checks:
        print(f"  {status}: {message}")
    
    print("\n✨ Verificación completada.")


def cmd_status(args):
    """Muestra el estado de los servicios en tiempo real."""
    print("📊 Estado de Cowork-Local\n")
    
    # Docker
    import subprocess
    try:
        result = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
                              capture_output=True, text=True, timeout=10)
        print("🐳 Contenedores Docker:")
        print(result.stdout)
    except Exception as e:
        print(f"🐳 Docker: Error - {e}")
    
    # Ollama
    try:
        import httpx
        response = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5)
        models = response.json().get("models", [])
        print(f"🦙 Ollama: {len(models)} modelo(s) cargado(s)")
        for m in models:
            size_gb = m.get("size", 0) / (1024**3)
            print(f"   - {m['name']}: {size_gb:.1f} GB")
    except Exception as e:
        print(f"🦙 Ollama: Error - {e}")


def cmd_run(args):
    """Ejecuta el grafo agentic con una consulta."""
    from graph.graph import run_graph
    
    query = args.query
    project = args.project or str(PROJECT_ROOT)
    max_iter = args.max_iterations or 10
    
    print(f"🚀 Ejecutando Cowork-Local...")
    print(f"   Consulta: {query}")
    print(f"   Proyecto: {project}")
    print(f"   Máx. iteraciones: {max_iter}")
    print()
    
    try:
        final_state = run_graph(
            user_query=query,
            project_path=project,
            max_iterations=max_iter,
        )
        
        print("\n" + "="*60)
        print("📋 RESULTADO FINAL")
        print("="*60)
        print(f"Session: {final_state.session_id}")
        print(f"Pasos completados: {len([s for s in final_state.plan if s.status == 'done'])}/{len(final_state.plan)}")
        print(f"Artefactos generados: {len(final_state.artifacts)}")
        print(f"Errores: {len(final_state.errors)}")
        
        if final_state.artifacts:
            print("\n📦 Artefactos:")
            for i, artifact in enumerate(final_state.artifacts):
                print(f"  {i+1}. [{artifact.type}] {artifact.content[:200]}...")
        
        if final_state.errors:
            print("\n⚠️  Errores:")
            for error in final_state.errors:
                print(f"  - {error[:200]}")
        
    except Exception as e:
        print(f"\n❌ Error ejecutando el grafo: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="🐄 Cowork-Local: Tu asistente agentic de desarrollo local",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  cowork check                           # Verificar que todo funciona
  cowork status                          # Ver estado de servicios
  cowork run --query "Analiza este proyecto"
  cowork run --project /ruta/repo --query "Genera tests para el módulo X"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Comando: check
    parser_check = subparsers.add_parser("check", help="Verificar configuración y servicios")
    parser_check.set_defaults(func=cmd_check)
    
    # Comando: status
    parser_status = subparsers.add_parser("status", help="Mostrar estado de servicios")
    parser_status.set_defaults(func=cmd_status)
    
    # Comando: run
    parser_run = subparsers.add_parser("run", help="Ejecutar el asistente agentic")
    parser_run.add_argument("--query", "-q", required=True, help="Consulta o tarea a realizar")
    parser_run.add_argument("--project", "-p", help="Ruta del proyecto a analizar")
    parser_run.add_argument("--max-iterations", "-n", type=int, default=10, help="Máximo de iteraciones")
    parser_run.set_defaults(func=cmd_run)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    setup_logging("INFO")
    args.func(args)


if __name__ == "__main__":
    main()
