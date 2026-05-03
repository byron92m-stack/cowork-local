"""
Chat Agentic en Tiempo Real - Muestra el progreso paso a paso.
"""

import sys
import os
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import time
import json
from datetime import datetime
from typing import Optional

# ─── Inicialización ───────────────────────────────────────────
st.set_page_config(page_title="Chat Cowork-Local", page_icon="🐄", layout="wide")

# CSS personalizado para los estados
st.markdown("""
<style>
.step-pending { color: #888; }
.step-progress { color: #1a73e8; font-weight: bold; }
.step-done { color: #0d904f; }
.step-error { color: #d93025; }
.artifact-box { 
    border: 1px solid #e0e0e0; 
    border-radius: 8px; 
    padding: 12px; 
    margin: 8px 0;
    background-color: #f8f9fa;
}
.thinking-box {
    border-left: 4px solid #1a73e8;
    padding: 8px 16px;
    margin: 8px 0;
    background-color: #f0f6ff;
    border-radius: 0 8px 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🐄 Cowork Chat")
    st.markdown("---")
    
    max_iter = st.slider("Máx. iteraciones", 5, 30, 15)
    default_project = os.getenv("COWORK_ROOT", str(PROJECT_ROOT))
    project = st.text_input("Proyecto", default_project)
    
    st.markdown("---")
    
    if st.button("🗑️ Limpiar chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.caption("🧠 DeepSeek Cloud + 🦙 Qwen 14B GPU")

# ─── Título ───────────────────────────────────────────────────
st.title("💬 Chat Agentic en Tiempo Real")
st.caption("Cada paso del agente se muestra en vivo mientras se ejecuta")

# ─── Inicializar historial ────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── Mostrar mensajes anteriores ──────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── Función para ejecutar el grafo con callbacks ─────────────
def run_with_progress(query: str, project_path: str, max_iterations: int, status_container):
    """
    Ejecuta el grafo y muestra el progreso en tiempo real.
    """
    from graph.state import CoworkState
    from graph.graph import build_graph
    
    # Estado inicial
    initial_state = CoworkState(
        user_query=query,
        project_path=project_path,
        max_iterations=max_iterations,
    )
    
    # Construir grafo
    graph = build_graph()
    config = {"recursion_limit": max_iterations * 5 + 20}
    
    # Para tracking de progreso
    progress_data = {
        "steps": [],
        "current_step": None,
        "artifacts_count": 0,
        "errors_count": 0,
    }
    
    # Ejecutar paso a paso con streaming
    final_state = None
    for event in graph.stream(initial_state, config):
        for node_name, node_output in event.items():
            # node_output es un dict con el estado
            state_dict = node_output if isinstance(node_output, dict) else {}
            
            # Actualizar progreso
            if node_name == "supervisor":
                plan = state_dict.get("plan", [])
                if plan and not progress_data["steps"]:
                    progress_data["steps"] = [
                        {"description": s.get("description", ""), 
                         "status": s.get("status", "pending"),
                         "assigned_to": s.get("assigned_to", "")}
                        for s in plan
                    ]
                    with status_container:
                        st.markdown("### 🧠 Plan generado")
                        for i, step in enumerate(progress_data["steps"]):
                            assigned = step.get("assigned_to", "")
                            icon = "🔧" if assigned == "tools" else "🦙" if assigned == "executor" else "🧠"
                            st.markdown(f"{icon} **Paso {i+1}**: {step['description'][:100]}")
                
                # Actualizar paso actual
                current_id = state_dict.get("current_step_id")
                if current_id and progress_data["steps"]:
                    for i, s in enumerate(progress_data["steps"]):
                        if s.get("status") == "in_progress":
                            progress_data["current_step"] = i
                            with status_container:
                                assigned = s.get("assigned_to", "")
                                icon = "🔧" if assigned == "tools" else "🦙" if assigned == "executor" else "🧠"
                                st.markdown(f"""<div class="thinking-box">
                                {icon} <strong>Ejecutando paso {i+1}:</strong> {s['description'][:80]}...
                                </div>""", unsafe_allow_html=True)
            
            elif node_name == "executor":
                current = progress_data.get("current_step")
                if current is not None and current < len(progress_data["steps"]):
                    progress_data["steps"][current]["status"] = "done"
                    with status_container:
                        st.markdown(f"✅ **Paso {current+1} completado** (Qwen GPT)")
            
            elif node_name == "tools":
                current = progress_data.get("current_step")
                if current is not None and current < len(progress_data["steps"]):
                    progress_data["steps"][current]["status"] = "done"
                    with status_container:
                        st.markdown(f"✅ **Paso {current+1} completado** (Tools)")
            
            elif node_name == "reviewer":
                with status_container:
                    st.markdown(f"🔍 **Revisando resultado...**")
            
            elif node_name == "memory":
                if state_dict.get("metadata", {}).get("session_saved"):
                    with status_container:
                        st.markdown(f"💾 **Sesión guardada en PostgreSQL**")
            
            # Guardar estado final
            final_state = state_dict
    
    # Convertir a CoworkState
    if final_state:
        final_state = CoworkState(**final_state)
    
    return final_state, progress_data


# ─── Input del usuario ────────────────────────────────────────
if query := st.chat_input("¿Qué querés hacer? Ej: Analiza los archivos Python del proyecto"):
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    # Ejecutar con progreso en tiempo real
    with st.chat_message("assistant"):
        # Contenedor para el progreso en tiempo real
        progress_placeholder = st.empty()
        
        with st.spinner("🧠 Pensando..."):
            try:
                final_state, progress = run_with_progress(
                    query, project, max_iter, progress_placeholder
                )
                
                # Limpiar el placeholder de progreso
                progress_placeholder.empty()
                
                if final_state:
                    # Construir respuesta final
                    steps_done = len([s for s in final_state.plan if s.status == "done"])
                    total = len(final_state.plan)
                    
                    response = f"### ✅ Tarea completada\n\n"
                    response += f"**{steps_done}/{total} pasos** | "
                    response += f"**{len(final_state.artifacts)} artefactos** | "
                    response += f"**{len(final_state.errors)} errores**\n\n"
                    
                    # Mostrar artefactos
                    if final_state.artifacts:
                        response += "---\n\n### 📦 Resultados\n\n"
                        for i, art in enumerate(final_state.artifacts[-5:]):
                            if art.content and len(art.content) > 5:
                                response += f"<div class='artifact-box'>"
                                response += f"**{art.type.upper()}**: "
                                response += f"{art.content[:500]}"
                                if len(art.content) > 500:
                                    response += f"\n\n*... ({len(art.content)} caracteres totales)*"
                                response += f"</div>\n\n"
                    
                    if final_state.errors:
                        response += "\n⚠️ **Errores:**\n"
                        for e in final_state.errors[:3]:
                            response += f"- {e[:200]}\n"
                    
                    st.markdown(response, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Guardar en PostgreSQL automáticamente
                    from tools.python_tools.db_tools import (
                        create_session, save_all_steps, save_artifact, update_session_status
                    )
                    create_session(
                        session_id=final_state.session_id,
                        user_query=query,
                        project_path=project,
                    )
                    steps_data = [{"id": s.id, "description": s.description, 
                                   "status": s.status, "assigned_to": s.assigned_to,
                                   "metadata": s.metadata} for s in final_state.plan]
                    save_all_steps(final_state.session_id, steps_data)
                    for art in final_state.artifacts:
                        save_artifact(final_state.session_id, {
                            "id": art.id, "type": art.type, 
                            "content": art.content, "metadata": art.metadata
                        })
                    update_session_status(final_state.session_id, 
                        "completed" if final_state.is_complete() else "in_progress")
                    
                    st.success(f"💾 Sesión `{final_state.session_id[:8]}...` guardada en PostgreSQL")
                
            except Exception as e:
                progress_placeholder.empty()
                error_msg = f"❌ **Error:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                import traceback
                st.code(traceback.format_exc())
