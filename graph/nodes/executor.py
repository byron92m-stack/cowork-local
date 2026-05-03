"""
Nodo Executor: Ejecución de tareas con Qwen local.

Este nodo usa Qwen 2.5 vía Ollama para:
1. Analizar código y arquitectura
2. Generar código y diffs
3. Refactorizar módulos
4. Ejecutar análisis técnicos
"""

import logging
from typing import Dict, Any
from ..state import CoworkState

logger = logging.getLogger(__name__)

_qwen_client = None


def _get_qwen_client():
    """Obtiene o crea el cliente Qwen."""
    global _qwen_client
    if _qwen_client is None:
        from models.qwen_ollama_client import QwenOllamaClient
        _qwen_client = QwenOllamaClient()
    return _qwen_client


def executor_node(state: CoworkState) -> Dict[str, Any]:
    """
    Nodo Executor.
    
    Ejecuta el paso actual si está asignado al executor.
    
    Args:
        state: Estado global del grafo.
        
    Returns:
        Diccionario con los campos actualizados del estado.
    """
    logger.info(f"[Executor] Iniciando. Session: {state.session_id[:8]}...")
    state.iteration_count += 1
    
    current_step = state.get_current_step()
    
    if current_step is None:
        logger.warning("[Executor] No hay paso actual para ejecutar")
        return state.model_dump()
    
    # Solo ejecutar pasos asignados al executor
    if current_step.assigned_to != "executor":
        logger.debug(f"[Executor] Paso asignado a {current_step.assigned_to}, no a executor. Saltando.")
        # Si el paso es de tools pero llegó aquí por error, marcarlo para que tools lo tome
        if current_step.assigned_to == "tools":
            current_step.status = "pending"
            logger.info(f"[Executor] Reasignando paso a tools")
        return state.model_dump()
    
    # También saltar si la descripción es claramente de lectura de archivos
    desc = current_step.description.lower()
    if any(w in desc for w in ["leer", "listar", "ls", "find", "cat"]) and not any(w in desc for w in ["analizar", "explicar", "propósito"]):
        logger.info(f"[Executor] Reasignando a tools: {current_step.description[:60]}")
        current_step.assigned_to = "tools"
        current_step.status = "pending"
        # El grafo (after_executor) detectará status=pending+assigned_to=tools y ruteará a tools
        return state.model_dump()
    
    logger.info(f"[Executor] Ejecutando: {current_step.description[:100]}")
    
    try:
        client = _get_qwen_client()
        
        # Elegir la acción según el tipo de paso
        if current_step.step_type == "analysis":
            result = _execute_analysis(state, current_step, client)
        elif current_step.step_type == "code_generation":
            result = _execute_code_generation(state, current_step, client)
        else:
            # Tarea genérica
            result = _execute_generic(state, current_step, client)
        
        # Guardar el resultado como artefacto
        state.add_artifact(
            artifact_type=current_step.step_type or "analysis",
            content=result,
            path=current_step.metadata.get("file_path"),
        )
        
        current_step.status = "done"
        current_step.metadata["result_summary"] = result[:200]
        
        logger.info(f"[Executor] Paso completado exitosamente")
        
    except Exception as e:
        logger.error(f"[Executor] Error: {e}")
        current_step.status = "failed"
        state.add_error(f"Error del executor: {str(e)}")
    
    return state.model_dump()


def _execute_analysis(state: CoworkState, step, client) -> str:
    """Ejecuta un análisis de código o proyecto."""
    # 1. Buscar contenido de archivos en artefactos previos (tipo 'log' del tools_node)
    file_contents = ""
    for artifact in state.artifacts:
        if artifact.type == "log" and artifact.content:
            # Buscar bloques de código Python en el artifact
            if "```python" in artifact.content or "### Archivo:" in artifact.content:
                file_contents += artifact.content + "\n\n"
    
    # 2. Si no hay contenido en artefactos, usar project_context
    if not file_contents:
        file_contents = state.project_context.get("code", "")
    
    # 3. Construir el prompt
    if file_contents:
        prompt = f"""
Analiza el siguiente código del proyecto:

Proyecto: {state.project_path}
Consulta original: {state.user_query}

CONTENIDO DE LOS ARCHIVOS:
{file_contents[:6000]}

Basado en el contenido real de los archivos mostrados arriba, proporciona un análisis detallado que responda a la consulta: "{state.user_query}"

Incluye:
1. Estructura general del proyecto
2. Propósito de cada archivo según su código real
3. Relaciones entre módulos
4. Observaciones y recomendaciones
"""
    else:
        prompt = f"""
Analiza el siguiente proyecto o consulta:

Proyecto: {state.project_path}
Consulta original: {state.user_query}
Contexto del proyecto: {state.project_context}

Proporciona un análisis detallado. Si necesitas ver el código, indícalo.
"""
    
    return client.generate(prompt=prompt, temperature=0.1)


def _execute_code_generation(state: CoworkState, step, client) -> str:
    """Genera código según especificaciones."""
    language = step.metadata.get("language", "python")
    context = step.metadata.get("context", "")
    
    return client.generate_code(
        task=step.description,
        language=language,
        context=context or state.project_context.get("code", ""),
    )


def _execute_generic(state: CoworkState, step, client) -> str:
    """Ejecuta una tarea genérica."""
    prompt = f"""
Tarea: {step.description}

Contexto del proyecto: {state.project_path}
Consulta original: {state.user_query}
Artefactos previos: {[a.content[:100] for a in state.artifacts[-3:]]}

Ejecuta la tarea solicitada.
"""
    return client.generate(prompt=prompt, temperature=0.1)
