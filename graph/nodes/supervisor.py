"""
Nodo Supervisor: Planificación y revisión de alto nivel.

Este nodo usa DeepSeek Cloud para:
1. Interpretar la consulta del usuario
2. Generar un plan de pasos
3. Ajustar el plan según resultados

NO ejecuta herramientas ni genera código directamente.
"""

import json
import logging
from typing import Dict, Any
from ..state import CoworkState, Step

logger = logging.getLogger(__name__)

# Cliente DeepSeek se inicializa bajo demanda para no requerir API key en import
_deepseek_client = None


def _get_deepseek_client():
    """Obtiene o crea el cliente DeepSeek."""
    global _deepseek_client
    if _deepseek_client is None:
        from models.deepseek_client import DeepSeekClient
        _deepseek_client = DeepSeekClient()
    return _deepseek_client


def supervisor_node(state: CoworkState) -> Dict[str, Any]:
    """
    Nodo Supervisor.
    
    Responsabilidades:
    - Si no hay plan: genera un plan inicial basado en user_query + contexto.
    - Si hay plan en curso: revisa el paso completado y ajusta si es necesario.
    
    Args:
        state: Estado global del grafo.
        
    Returns:
        Diccionario con los campos actualizados del estado.
    """
    logger.info(f"[Supervisor] Iniciando. Session: {state.session_id[:8]}...")
    state.iteration_count += 1
    
    # Si no hay plan, lo generamos
    if not state.plan:
        return _generate_plan(state)
    
    # Si hay plan en curso, revisamos el último paso completado
    return _review_progress(state)


def _generate_plan(state: CoworkState) -> Dict[str, Any]:
    """
    Genera un plan inicial basado en la consulta del usuario.
    """
    logger.info(f"[Supervisor] Generando plan para: {state.user_query[:100]}...")
    
    try:
        client = _get_deepseek_client()
        
        # Construir contexto del proyecto
        project_context = {
            "path": state.project_path,
            "structure": state.project_context.get("structure", "No disponible"),
        }
        
        # Llamar a DeepSeek para generar el plan
        response = client.plan(
            user_query=state.user_query,
            project_context=project_context,
            memory_context=state.memory_context,
        )
        
        # Parsear la respuesta JSON
        plan_data = json.loads(response)
        reasoning = plan_data.get("reasoning", "Sin explicación")
        steps_data = plan_data.get("plan", [])
        
        logger.info(f"[Supervisor] Plan generado: {len(steps_data)} pasos. Razón: {reasoning[:100]}")
        
        # Convertir los pasos del JSON a objetos Step
        for i, step_data in enumerate(steps_data):
            state.add_step(
                description=step_data.get("description", f"Paso {i+1}"),
                assigned_to=step_data.get("assigned_to", "executor"),
                step_type=step_data.get("step_type", "analysis"),
            )
        
        # Agregar el razonamiento como artefacto
        state.add_artifact("plan", reasoning)
        
        # Si el plan no incluye un paso de "leer archivos" y hay pasos de análisis,
        # insertar automáticamente un paso de tools para leer el código
        has_read_step = any(
            any(w in s.description.lower() for w in ["leer", "read", "cat", "contenido de", "código de"])
            for s in state.plan
        )
        has_analysis_step = any(
            s.step_type == "analysis" and s.assigned_to == "executor"
            for s in state.plan
        )
        if has_analysis_step and not has_read_step:
            # Insertar paso de lectura antes del primer análisis
            read_step = Step(
                description="Leer el contenido de todos los archivos Python del proyecto",
                assigned_to="tools",
                step_type="tool_call",
                metadata={"tool_name": "filesystem"}
            )
            # Encontrar el primer paso de análisis e insertar antes
            for i, s in enumerate(state.plan):
                if s.step_type == "analysis" and s.assigned_to == "executor":
                    state.plan.insert(i, read_step)
                    logger.info("[Supervisor] Insertado paso automático de lectura de archivos")
                    break
        
        # Establecer el primer paso como actual
        if state.plan:
            state.current_step_id = state.plan[0].id
            state.plan[0].status = "in_progress"
        
        state.metadata["plan_reasoning"] = reasoning
        
    except Exception as e:
        logger.error(f"[Supervisor] Error generando plan: {e}")
        state.add_error(f"Error del supervisor: {str(e)}")
        
        # Plan fallback simple
        state.add_step(
            description=f"Analizar: {state.user_query}",
            assigned_to="executor",
            step_type="analysis",
        )
        if state.plan:
            state.current_step_id = state.plan[0].id
            state.plan[0].status = "in_progress"
    
    return state.model_dump()


def _review_progress(state: CoworkState) -> Dict[str, Any]:
    """
    Revisa el progreso del plan y AVANZA al siguiente paso automáticamente.
    """
    # Buscar el primer paso pendiente y activarlo
    for step in state.plan:
        if step.status == "pending":
            state.current_step_id = step.id
            step.status = "in_progress"
            logger.info(f"[Supervisor] Avanzando a: {step.description[:80]}")
            return state.model_dump()
    
    # Si no hay pendientes, el plan terminó
    if state.is_complete():
        logger.info("[Supervisor] Plan completado. Todos los pasos done.")
        return state.model_dump()
    
    # Si no hay más pasos, terminar
    logger.info("[Supervisor] No hay más pasos. Finalizando.")
    return state.model_dump()
    
    current_step = state.get_current_step()
    
    if current_step is None:
        logger.warning("[Supervisor] No hay paso actual, buscando pendientes...")
        pending = state.get_pending_steps()
        if pending:
            state.current_step_id = pending[0].id
            pending[0].status = "in_progress"
        return state.model_dump()
    
    # Si el paso actual está completado, mover al siguiente
    if current_step.status == "done":
        logger.info(f"[Supervisor] Paso completado: {current_step.description[:80]}")
        
        # Buscar el siguiente paso pendiente
        pending = state.get_pending_steps()
        if pending:
            state.current_step_id = pending[0].id
            pending[0].status = "in_progress"
            logger.info(f"[Supervisor] Siguiente paso: {pending[0].description[:80]}")
        else:
            logger.info("[Supervisor] ¡Todos los pasos completados!")
    
    # Si el paso actual falló, decidir si reintentar o seguir
    elif current_step.status == "failed":
        logger.warning(f"[Supervisor] Paso fallado: {current_step.description[:80]}")
        
        # Por ahora, marcamos como fallado y seguimos al siguiente
        pending = state.get_pending_steps()
        if pending:
            state.current_step_id = pending[0].id
            pending[0].status = "in_progress"
        else:
            state.add_error(f"Paso fallado sin más pasos: {current_step.description}")
    
    return state.model_dump()
