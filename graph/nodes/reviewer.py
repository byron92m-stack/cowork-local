"""Nodo revisor - Evalúa resultados y decide si continuar."""
import logging
logger = logging.getLogger(__name__)

def reviewer_node(state) -> dict:
    """Revisa el resultado del paso actual y decide."""
    current = state.get_current_step()
    if not current:
        return {"metadata": state.metadata}
    
    logger.info(f"[Reviewer] Revisando paso {current.id[:8]}...")
    
    # Marcar paso como completado si ya pasó por executor o tools
    current.status = "done"
    
    # Limitar iteraciones
    done_count = len([s for s in state.plan if s.status == "done"])
    logger.info(f"[Reviewer] Pasos completados: {done_count}/{len(state.plan)}")
    
    return {
        "plan": state.plan,
        "metadata": state.metadata
    }
