"""Cowork-Local: Grafo agentic con LangGraph."""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import CoworkState
from .nodes.supervisor import supervisor_node
from .nodes.executor import executor_node
from .nodes.reviewer import reviewer_node
from .nodes.memory_manager import memory_manager_node

logger = logging.getLogger(__name__)

def _get_tools_node():
    from .nodes.tools_node import tools_node
    return tools_node

def route_to_worker(state: CoworkState) -> str:
    current = state.get_current_step()
    if current and current.assigned_to == "tools":
        return "tools"
    return "executor"

def after_memory(state: CoworkState) -> str:
    if state.metadata.get("session_saved"):
        return END
    return "supervisor"

def after_supervisor(state: CoworkState) -> str:
    if state.is_complete():
        return "memory"
    pending = state.get_pending_steps()
    if not pending:
        return "memory"
    next_step = pending[0]
    state.current_step_id = next_step.id
    next_step.status = "in_progress"
    return route_to_worker(state)

def after_worker(state: CoworkState) -> str:
    return "reviewer"

def after_reviewer(state: CoworkState) -> str:
    if state.is_complete():
        return "memory"
    pending = state.get_pending_steps()
    return "supervisor" if pending else "memory"

def build_graph() -> StateGraph:
    workflow = StateGraph(CoworkState)
    
    workflow.add_node("memory", memory_manager_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("tools", _get_tools_node())
    workflow.add_node("reviewer", reviewer_node)
    
    workflow.set_entry_point("memory")
    
    workflow.add_conditional_edges("memory", after_memory, {"supervisor": "supervisor", END: END})
    workflow.add_conditional_edges("supervisor", after_supervisor, {
        "executor": "executor", "tools": "tools", "memory": "memory"
    })
    workflow.add_edge("executor", "reviewer")
    workflow.add_edge("tools", "reviewer")
    workflow.add_conditional_edges("reviewer", after_reviewer, {"supervisor": "supervisor", "memory": "memory"})
    
    return workflow.compile()

def run_graph(user_query: str, project_path: str, max_iterations: int = 10, project_context: Dict[str, Any] = None) -> CoworkState:
    initial_state = CoworkState(
        user_query=user_query, project_path=project_path,
        max_iterations=max_iterations, project_context=project_context or {},
    )
    graph = build_graph()
    # Límite generoso: 3 pasos × 3 iteraciones × 3 nodos = ~30
    config = {"recursion_limit": 50}
    result = graph.invoke(initial_state, config)
    return CoworkState(**result)
