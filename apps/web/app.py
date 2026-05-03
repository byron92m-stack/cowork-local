"""
Cowork-Local Web UI - Panel de control con Streamlit.
Ejecutar: streamlit run apps/web/app.py
"""

import sys
import os
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Configuración de la página
st.set_page_config(
    page_title="Cowork-Local",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🐄 Cowork-Local")
    st.markdown("---")
    
    page = st.radio(
        "Navegación",
        ["🏠 Dashboard", "💬 Chat Agentic", "📋 Historial", "🔧 Herramientas MCP", "⚙️ Sistema"],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    st.caption(f"Fedora 43 | DeepSeek + Qwen 14B GPU")


# ─── Dashboard ─────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Obtener estadísticas
    from tools.python_tools.db_tools import get_stats, get_project_memory
    
    stats = get_stats()
    memory = get_project_memory(os.getenv("COWORK_ROOT", str(PROJECT_ROOT)))
    
    with col1:
        st.metric("Sesiones Totales", stats.get("total_sessions", 0))
    with col2:
        st.metric("Artefactos", stats.get("total_artifacts", 0))
    with col3:
        st.metric("Proyectos", stats.get("projects_tracked", 0))
    with col4:
        st.metric("Sesiones Activas", stats.get("active_sessions", 0))
    
    st.markdown("---")
    
    # Memoria del proyecto
    if memory:
        st.subheader("📝 Memoria del Proyecto")
        st.info(memory.get("summary", "Sin resumen"))
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Arquitectura")
            st.text(memory.get("architecture_notes", "Sin notas"))
        with col2:
            st.caption("Decisiones Clave")
            decisions = memory.get("key_decisions", [])
            if isinstance(decisions, str):
                decisions = json.loads(decisions)
            for d in decisions:
                st.checkbox(d, value=True, disabled=True)
    
    # Últimas sesiones
    st.markdown("---")
    st.subheader("📋 Últimas Sesiones")
    
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "cowork")
    db_pass = os.getenv("POSTGRES_PASSWORD", "coworkpass")
    db_name = os.getenv("POSTGRES_DB", "coworkdb")
    
    conn = psycopg2.connect(
        host=db_host, port=db_port, user=db_user,
        password=db_pass, database=db_name
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, user_query, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 10")
    sessions = cur.fetchall()
    conn.close()
    
    if sessions:
        df = pd.DataFrame([{
            "ID": s["id"][:8],
            "Consulta": s["user_query"][:80],
            "Estado": s["status"],
            "Fecha": str(s["created_at"])[:19],
        } for s in sessions])
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No hay sesiones aún. ¡Ejecutá tu primera tarea!")


# ─── Chat Agentic ─────────────────────────────────────────────
elif page == "💬 Chat Agentic":
    st.title("💬 Chat Agentic")
    st.caption("Chateá con tu asistente de desarrollo local")
    
    # Inicializar historial
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar mensajes anteriores
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input del usuario
    if query := st.chat_input("¿Qué querés hacer? Ej: Analiza el proyecto"):
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        # Ejecutar el grafo
        with st.chat_message("assistant"):
            with st.spinner("🧠 Pensando..."):
                from graph.graph import run_graph
                
                try:
                    final_state = run_graph(
                        user_query=query,
                        project_path=os.getenv("COWORK_ROOT", str(PROJECT_ROOT)),
                        max_iterations=15,
                    )
                    
                    # Construir respuesta
                    steps_done = len([s for s in final_state.plan if s.status == "done"])
                    response = f"### ✅ Tarea completada: {steps_done}/{len(final_state.plan)} pasos\n\n"
                    
                    if final_state.artifacts:
                        for i, art in enumerate(final_state.artifacts[-3:]):  # Últimos 3
                            if art.content:
                                response += f"**{art.type}**: {art.content[:300]}...\n\n"
                    
                    if final_state.errors:
                        response += f"\n⚠️ Errores: {len(final_state.errors)}"
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


# ─── Historial ─────────────────────────────────────────────────
elif page == "📋 Historial":
    st.title("📋 Historial de Sesiones")
    
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from tools.python_tools.db_tools import get_artifacts_by_session
    
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "cowork")
    db_pass = os.getenv("POSTGRES_PASSWORD", "coworkpass")
    db_name = os.getenv("POSTGRES_DB", "coworkdb")
    
    conn = psycopg2.connect(
        host=db_host, port=db_port, user=db_user,
        password=db_pass, database=db_name
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, user_query, project_path, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 20")
    sessions = cur.fetchall()
    conn.close()
    
    if sessions:
        for s in sessions:
            with st.expander(f"[{s['status']}] {s['user_query'][:100]} ({str(s['created_at'])[:19]})"):
                st.caption(f"ID: `{s['id']}`")
                st.caption(f"Proyecto: `{s['project_path']}`")
                
                # Artefactos
                artifacts = get_artifacts_by_session(s["id"])
                if artifacts:
                    st.write(f"**{len(artifacts)} artefactos:**")
                    for a in artifacts[:5]:
                        st.text(f"[{a['type']}] {a['content'][:200] if a.get('content') else ''}")
    else:
        st.info("No hay sesiones guardadas")


# ─── Herramientas MCP ─────────────────────────────────────────
elif page == "🔧 Herramientas MCP":
    st.title("🔧 Herramientas MCP")
    st.caption("Probar los MCP Servers manualmente")
    
    default_path = os.getenv("COWORK_ROOT", str(PROJECT_ROOT))
    
    tool_tab = st.selectbox("Servidor", ["📁 Filesystem", "🐚 Shell", "🔀 Git", "🐳 Docker"])
    
    if tool_tab == "📁 Filesystem":
        op = st.selectbox("Operación", ["list_directory", "read_file", "search_files"])
        path = st.text_input("Ruta", default_path)
        
        if st.button("Ejecutar"):
            from tools.mcp_client import get_mcp_client
            client = get_mcp_client()
            
            if op == "list_directory":
                result = client.call_sync("filesystem", "list_directory", {"path": path})
            elif op == "read_file":
                result = client.call_sync("filesystem", "read_file", {"path": path})
            elif op == "search_files":
                pattern = st.text_input("Patrón", "*.py")
                result = client.call_sync("filesystem", "search_files", {"pattern": pattern, "path": path})
            
            st.code(result, language="text")
    
    elif tool_tab == "🐚 Shell":
        cmd = st.text_input("Comando", "ls -la")
        cwd = st.text_input("Directorio", default_path)
        
        if st.button("Ejecutar"):
            from tools.mcp_client import get_mcp_client
            client = get_mcp_client()
            result = client.call_sync("shell", "execute_command", {"command": cmd, "cwd": cwd})
            st.code(result, language="bash")
    
    elif tool_tab == "🔀 Git":
        op = st.selectbox("Operación", ["status", "diff", "log", "branch", "show"])
        
        if st.button("Ejecutar"):
            from tools.mcp_client import get_mcp_client
            client = get_mcp_client()
            result = client.call_sync("git", "git_operation", {"operation": op})
            st.code(result, language="diff")
    
    elif tool_tab == "🐳 Docker":
        op = st.selectbox("Operación", ["ps", "logs", "inspect", "stats", "version"])
        container = st.text_input("Contenedor (opcional)", "cowork-postgres")
        
        if st.button("Ejecutar"):
            from tools.mcp_client import get_mcp_client
            client = get_mcp_client()
            result = client.call_sync("docker", "docker_operation", {
                "operation": op, 
                "container_name": container if container else ""
            })
            st.code(result, language="text")


# ─── Sistema ───────────────────────────────────────────────────
elif page == "⚙️ Sistema":
    st.title("⚙️ Estado del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🦙 Ollama")
        try:
            import httpx
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
            r = httpx.get(f"{ollama_url}/api/tags", timeout=5)
            models = r.json().get("models", [])
            if models:
                st.success(f"Conectado - {len(models)} modelo(s)")
                for m in models:
                    size_gb = m.get("size", 0) / (1024**3)
                    st.text(f"• {m['name']}: {size_gb:.1f} GB")
            else:
                st.warning("Sin modelos")
        except:
            st.error("No conectado")
    
    with col2:
        st.subheader("🐘 PostgreSQL")
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                user=os.getenv("POSTGRES_USER", "cowork"),
                password=os.getenv("POSTGRES_PASSWORD", "coworkpass"),
                database=os.getenv("POSTGRES_DB", "coworkdb"),
                connect_timeout=3
            )
            conn.close()
            st.success("Conectado")
        except:
            st.error("No conectado")
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🧠 DeepSeek")
        if os.getenv("DEEPSEEK_API_KEY"):
            st.success("API Key configurada")
        else:
            st.warning("API Key no configurada")
    
    with col4:
        st.subheader("🐳 Docker")
        import subprocess
        try:
            r = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
            containers = r.stdout.strip().split("\n")
            st.success(f"{len(containers)} contenedor(es)")
            for c in containers:
                if c: st.text(f"• {c}")
        except:
            st.error("No disponible")
    
    st.markdown("---")
    st.subheader("📁 Directorios")
    dirs = [
        os.getenv("COWORK_ROOT", str(PROJECT_ROOT)),
        os.getenv("OLLAMA_MODELS", "/media/SSD1T/ollama-models"),
        os.getenv("DOCKER_DATA", "/media/SSD1T/docker-data"),
        os.getenv("COWORK_PROJECTS", "/media/SSD1T/projects"),
    ]
    for d in dirs:
        exists = os.path.exists(d)
        icon = "✅" if exists else "❌"
        st.text(f"{icon} {d}")
