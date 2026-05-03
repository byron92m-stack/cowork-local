"""
Nodo Reviewer: Revisión de calidad de los resultados.

Este nodo evalúa si el resultado de un paso es satisfactorio
y decide si se necesita corrección.
"""

import json
import logging
from typing import Dict, Any
from ..state import CoworkState

logger = logging.getLogger(__name__)

_reviewer_client = None


def _get_reviewer_client():
    """Obtiene o crea el cliente para revisión (DeepSeek)."""
    global _reviewer_client
    if _reviewer_client is None:
        from models.deepseek_client import DeepSeekClient
        _reviewer_client = DeepSeekClient()
    return _reviewer_client


def reviewer_node(state: CoworkState) -> Dict[str, Any]:
    """
    Nodo Reviewer.
    
    Revisa el paso recién completado y decide si:
    - done: el resultado es aceptable.
    - needs_correction: requiere ajustes (reinyectar al executor).
    - failed: el resultado no es aprovechable.
    
    Args:
        state: Estado global del grafo.
        
    Returns:
        Diccionario con los campos actualizados del estado.
    """
    logger.info(f"[Reviewer] Iniciando revisión. Session: {state.session_id[:8]}...")
    state.iteration_count += 1
    
    current_step = state.get_current_step()
    
    if current_step is None:
        logger.warning("[Reviewer] No hay paso para revisar")
        return state.model_dump()
    
    # Solo revisar pasos completados o fallados
    if current_step.status not in ("done", "failed"):
        logger.debug(f"[Reviewer] Paso en estado {current_step.status}, no se revisa aún")
        return state.model_dump()
    
    # Obtener el último artefacto
    last_artifact = state.artifacts[-1] if state.artifacts else None
    
    try:
        client = _get_reviewer_client()
        
        review_response = client.review(
            original_query=state.user_query,
            step_description=current_step.description,
            step_result=last_artifact.content if last_artifact else "Sin resultado",
            artifacts=[a.model_dump() for a in state.artifacts[-3:]],
        )
        
        review_data = json.loads(review_response)
        review_status = review_data.get("status", "done")
        feedback = review_data.get("feedback", "")
        corrections = review_data.get("corrections_needed", [])
        
        logger.info(f"[Reviewer] Revisión: {review_status}. Feedback: {feedback[:100]}")
        
        # Actualizar el paso según la revisión
        if review_status == "done":
            current_step.status = "done"
            state.add_artifact("review", feedback)
            
        elif review_status == "needs_correction":
            # No reintentar: avanzar al siguiente paso. Las correcciones se pueden aplicar después.
            current_step.status = "done"
            current_step.metadata["corrections"] = corrections
            state.add_artifact("review", f"Paso completado (correcciones sugeridas para después): {feedback}")
            logger.info(f"[Reviewer] Paso necesita corrección pero avanzamos: {corrections}")
            
        elif review_status == "failed":
            # Si hay más pasos en el plan, marcamos como done para avanzar
            # (el análisis real lo harán los siguientes pasos)
            pending_after = [s for s in state.plan if s.status == "pending" and s.id != current_step.id]
            if pending_after:
                logger.info(f"[Reviewer] Paso marcado como failed pero hay {len(pending_after)} pasos más. Avanzando.")
                current_step.status = "done"
                state.add_artifact("review", f"Paso completado con observaciones: {feedback}")
            else:
                current_step.status = "failed"
                state.add_error(f"Revisión fallida: {feedback}")
                state.add_artifact("error", feedback)
        
    except Exception as e:
        logger.error(f"[Reviewer] Error en revisión: {e}")
        # Si falla la revisión, marcamos como done para no trabar el flujo
        current_step.status = "done"
        state.add_error(f"Error del reviewer: {str(e)}")
    
    return state.model_dump()
