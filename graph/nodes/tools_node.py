"""Nodo de herramientas - Ejecuta operaciones del sistema via MCP."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def tools_node(state) -> Dict[str, Any]:
    """Ejecuta el paso actual usando las herramientas MCP."""
    from ..state import Artifact
    
    current = state.get_current_step()
    if not current:
        return {"errors": ["No step to execute"]}
    
    logger.info(f"Tools: executing step {current.id[:8]}...")
    
    from tools.mcp_client import get_mcp_client
    client = get_mcp_client()
    
    results = []
    errors = []
    desc = current.description.lower()
    
    try:
        if any(w in desc for w in ["code", "script", "python"]):
            code = current.metadata.get("code", "")
            if code:
                result = client.call_sync("docker_sandbox", "execute_python", {"code": code, "timeout": 30})
                results.append(f"Sandbox: {result}")
            else:
                errors.append("No code found")
        elif any(w in desc for w in ["shell", "command"]):
            command = current.metadata.get("command", desc)
            result = client.call_sync("docker_sandbox", "execute_shell", {"command": command, "timeout": 30})
            results.append(f"Shell: {result}")
        elif any(w in desc for w in ["list", "files", "directory"]):
            result = client.call_sync("filesystem", "list_directory", {"path": state.project_path})
            results.append(result)
        elif any(w in desc for w in ["read"]):
            filepath = current.metadata.get("filepath", f"{state.project_path}/README.md")
            result = client.call_sync("filesystem", "read_file", {"path": filepath})
            results.append(result)
        elif any(w in desc for w in ["search", "web"]):
            query = current.metadata.get("query", desc)
            result = client.call_sync("websearch", "search", {"query": query})
            results.append(result)
        elif "git" in desc:
            result = client.call_sync("git", "git_operation", {"operation": "status"})
            results.append(result)
        elif "docker" in desc:
            result = client.call_sync("docker", "docker_operation", {"operation": "ps"})
            results.append(result)
        elif "sandbox" in desc:
            result = client.call_sync("docker_sandbox", "status", {})
            results.append(result)
        else:
            result = client.call_sync("docker_sandbox", "execute_shell", {
                "command": f"echo 'Step: {current.description}'", "timeout": 10
            })
            results.append(result)
        
        current.status = "done"
    except Exception as e:
        logger.error(f"Error: {e}")
        errors.append(str(e))
        current.status = "failed"
    
    for result in results:
        state.artifacts.append(Artifact(
            type="tool_call",
            content=result[:1000] if result else "",
            metadata={"step_id": current.id}
        ))
    
    return {
        "plan": state.plan,
        "artifacts": state.artifacts,
        "errors": state.errors + errors,
        "current_step_id": current.id,
        "metadata": state.metadata
    }
