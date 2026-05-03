"""Nodo ejecutor - Ejecuta pasos asignados."""
import logging
logger = logging.getLogger(__name__)

def executor_node(state) -> dict:
    """Ejecuta el paso actual o delega a tools."""
    current = state.get_current_step()
    if not current:
        return {"metadata": state.metadata}
    
    logger.info(f"[Executor] Paso {current.id[:8]}...")
    
    # Si es paso de tools, delegar (solo una vez)
    if current.assigned_to == "tools":
        logger.info("[Executor] Reasignando a tools")
        # No cambiar assigned_to, solo dejar que el router lo mande a tools
        return {"plan": state.plan, "metadata": state.metadata}
    
    # Si es paso de executor, marcarlo como done
    # (la generación de código real iría acá con Qwen)
    current.status = "done"
    logger.info(f"[Executor] Paso completado")
    
    return {"plan": state.plan, "metadata": state.metadata}
