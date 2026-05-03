"""Cowork-Local: Grafo con ejecución paralela de sub-agentes y memoria PostgreSQL."""
import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.constants import Send
from .state import CoworkState
from .nodes import supervisor_node, executor_node, reviewer_node, tools_node, memory_manager_node

logger = logging.getLogger(__name__)

def route_to_workers(state: CoworkState) -> List[Send]:
    """Distribuye pasos pendientes a múltiples workers en paralelo.
    
    El Supervisor ya marcó los pasos como in_progress y asignó cada uno
    a executor o tools. Esta función los distribuye para ejecución simultánea.
    """
    pending = state.get_pending_steps()
    if not pending:
        return [Send("supervisor", {})]
    
    # Marcar hasta 3 pasos para ejecución paralela
    parallel_steps = pending[:3]
    sends = []
    
    for step in parallel_steps:
        step.status = "in_progress"
        state.current_step_id = step.id
        
        if step.assigned_to == "tools":
            sends.append(Send("tools", {"current_step_id": step.id}))
        else:
            sends.append(Send("executor", {"current_step_id": step.id}))
    
    logger.info(f"Distribuyendo {len(sends)} pasos en paralelo: {[s.node for s in sends]}")
    return sends

def after_memory(state: CoworkState) -> str:
    """Después memory: si es pre-run, ir a supervisor. Si post-run, END."""
    if state.metadata.get("session_saved"):
        return END
    return "supervisor"

def after_supervisor(state: CoworkState) -> str:
    """Después del supervisor: distribuir en paralelo o finalizar."""
    if state.is_complete():
        return "memory"
    pending = state.get_pending_steps()
    if not pending:
        return "memory"
    return "workers"

def after_worker(state: CoworkState) -> str:
    """Después de un worker: siempre va a reviewer."""
    return "reviewer"

def after_reviewer(state: CoworkState) -> str:
    """Después del reviewer: más pasos o finalizar."""
    if state.is_complete():
        return "memory"
    pending = state.get_pending_steps()
    return "supervisor" if pending else "memory"

def build_graph() -> StateGraph:
    """Construye el grafo con soporte para ejecución paralela."""
    workflow = StateGraph(CoworkState)
    
    # Nodos principales
    workflow.add_node("memory", memory_manager_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("reviewer", reviewer_node)
    
    # Entry point
    workflow.set_entry_point("memory")
    
    # Memory → Supervisor o END
    workflow.add_conditional_edges(
        "memory", after_memory, 
        {"supervisor": "supervisor", END: END}
    )
    
    # Supervisor → Workers (paralelo) o Memory
    workflow.add_conditional_edges(
        "supervisor", after_supervisor, {
            "workers": route_to_workers,
            "memory": "memory"
        }
    )
    
    # Workers → Reviewer
    workflow.add_conditional_edges(
        "executor", after_worker,
        {"reviewer": "reviewer"}
    )
    workflow.add_conditional_edges(
        "tools", after_worker,
        {"reviewer": "reviewer"}
    )
    
    # Reviewer → Supervisor o Memory
    workflow.add_conditional_edges(
        "reviewer", after_reviewer, {
            "supervisor": "supervisor",
            "memory": "memory"
        }
    )
    
    return workflow.compile()

def run_graph(
    user_query: str,
    project_path: str,
    max_iterations: int = 10,
    project_context: Dict[str, Any] = None
) -> CoworkState:
    """Ejecuta el grafo agentic con soporte paralelo.
    
    Args:
        user_query: Consulta del usuario.
        project_path: Ruta del proyecto.
        max_iterations: Máximo de iteraciones del grafo.
        project_context: Contexto adicional del proyecto.
        
    Returns:
        CoworkState con los resultados de la ejecución.
    """
    initial_state = CoworkState(
        user_query=user_query,
        project_path=project_path,
        max_iterations=max_iterations,
        project_context=project_context or {},
    )
    
    graph = build_graph()
    config = {"recursion_limit": max_iterations * 10 + 20}
    
    # Usar stream para obtener el estado final
    final_state = None
    for event in graph.stream(initial_state, config):
        for node_name, node_output in event.items():
            logger.info(f"Nodo completado: {node_name}")
            if isinstance(node_output, dict):
                final_state = node_output
    
    if final_state:
        return CoworkState(**final_state)
    return initial_state
