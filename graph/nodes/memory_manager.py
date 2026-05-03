"""
Nodo Memory Manager: Persistencia en PostgreSQL.
Ejecuta PRE-RUN (carga memoria) o POST-RUN (guarda sesión) según metadata.
"""

import logging
from typing import Dict, Any
from ..state import CoworkState

logger = logging.getLogger(__name__)


def memory_manager_node(state: CoworkState) -> Dict[str, Any]:
    """
    Nodo de gestión de memoria.
    - pre_run (si no hay pasos): Carga memoria del proyecto
    - post_run (si hay pasos completados y no se ha guardado aún): Guarda sesión
    """
    from tools.python_tools.db_tools import (
        create_session, save_all_steps, save_artifact, 
        get_project_memory, update_session_status
    )
    
    # ─── PRE-RUN: Cargar memoria ──────────────────────────────
    if not state.plan or len(state.plan) == 0:
        logger.info(f"[Memory] PRE-RUN: Cargando memoria de {state.project_path}")
        project_memory = get_project_memory(state.project_path)
        if project_memory:
            state.memory_context = {
                "summary": project_memory.get("summary", ""),
                "architecture_notes": project_memory.get("architecture_notes", ""),
                "key_decisions": project_memory.get("key_decisions", []),
                "last_analyzed": project_memory.get("last_analyzed", "Nunca"),
            }
            logger.info(f"[Memory] Memoria cargada")
        state.metadata["memory_loaded"] = True
        return state.model_dump()
    
    # ─── POST-RUN: Guardar sesión (solo una vez) ──────────────
    if state.metadata.get("session_saved"):
        logger.debug("[Memory] Sesión ya guardada, saltando")
        return state.model_dump()
    
    logger.info(f"[Memory] POST-RUN: Guardando sesión {state.session_id[:8]}...")
    
    # 1. Crear sesión
    create_session(
        session_id=state.session_id,
        user_query=state.user_query,
        project_path=state.project_path,
        metadata={
            "total_steps": len(state.plan),
            "completed_steps": len([s for s in state.plan if s.status == "done"]),
            "total_artifacts": len(state.artifacts),
            "total_errors": len(state.errors),
        }
    )
    
    # 2. Guardar pasos
    steps_data = []
    for step in state.plan:
        steps_data.append({
            "id": step.id,
            "description": step.description,
            "status": step.status,
            "assigned_to": step.assigned_to,
            "metadata": step.metadata,
        })
    save_all_steps(state.session_id, steps_data)
    
    # 3. Guardar artefactos
    for artifact in state.artifacts:
        save_artifact(
            session_id=state.session_id,
            artifact_data={
                "id": artifact.id,
                "type": artifact.type,
                "path": artifact.path,
                "content": artifact.content,
                "metadata": artifact.metadata,
            },
        )
    
    # 4. Estado final
    if state.is_complete():
        update_session_status(state.session_id, "completed")
    elif state.errors:
        update_session_status(state.session_id, "failed")
    else:
        update_session_status(state.session_id, "in_progress")
    
    # Marcar como guardado para no repetir
    state.metadata["session_saved"] = True
    
    logger.info(f"[Memory] Sesión guardada: {len(steps_data)} pasos, {len(state.artifacts)} artefactos")
    
    return state.model_dump()
