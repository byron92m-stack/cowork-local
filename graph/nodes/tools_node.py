"""Nodo de herramientas - Ejecuta operaciones del sistema via MCP."""
import logging
from typing import Dict, Any
from . import CoworkState

logger = logging.getLogger(__name__)

def tools_node(state: CoworkState) -> Dict[str, Any]:
    """Ejecuta el paso actual usando las herramientas MCP.
    
    Si el paso requiere ejecución de código, usa el Docker Sandbox
    para aislamiento seguro.
    """
    current = state.get_current_step()
    if not current:
        return {"errors": ["No hay paso actual para ejecutar"]}
    
    logger.info(f"Tools: ejecutando paso {current.id[:8]}... - {current.description}")
    
    from tools.mcp_client import get_mcp_client
    client = get_mcp_client()
    
    results = []
    errors = []
    
    # Determinar qué herramienta usar según la descripción del paso
    description_lower = current.description.lower()
    
    try:
        # Ejecución de código Python en sandbox seguro
        if any(word in description_lower for word in ["código", "code", "script", "python", "ejecutar código", "run code"]):
            code = current.metadata.get("code", "")
            if code:
                result = client.call_sync("docker_sandbox", "execute_python", {
                    "code": code,
                    "timeout": 30
                })
                results.append(f"Sandbox Python: {result}")
                logger.info(f"Código ejecutado en sandbox: {len(code)} caracteres")
            else:
                errors.append("No se encontró código para ejecutar")
        
        # Operaciones de shell en sandbox
        elif any(word in description_lower for word in ["shell", "comando", "command", "bash"]):
            command = current.metadata.get("command", description_lower)
            result = client.call_sync("docker_sandbox", "execute_shell", {
                "command": command,
                "timeout": 30
            })
            results.append(f"Sandbox Shell: {result}")
        
        # Listar archivos del proyecto
        elif any(word in description_lower for word in ["listar", "list", "archivos", "files", "directorio", "directory"]):
            result = client.call_sync("filesystem", "list_directory", {
                "path": state.project_path
            })
            results.append(result)
        
        # Leer un archivo específico
        elif any(word in description_lower for word in ["leer", "read", "contenido", "content"]):
            filepath = current.metadata.get("filepath", f"{state.project_path}/README.md")
            result = client.call_sync("filesystem", "read_file", {
                "path": filepath
            })
            results.append(f"Archivo leído:\n{result}")
        
        # Búsqueda web
        elif any(word in description_lower for word in ["buscar", "search", "web", "internet"]):
            query = current.metadata.get("query", description_lower)
            result = client.call_sync("websearch", "search", {
                "query": query
            })
            results.append(result)
        
        # Git status
        elif any(word in description_lower for word in ["git", "commit", "branch", "diff"]):
            result = client.call_sync("git", "git_operation", {
                "operation": "status"
            })
            results.append(result)
        
        # Docker status
        elif any(word in description_lower for word in ["docker", "container", "contenedor"]):
            result = client.call_sync("docker", "docker_operation", {
                "operation": "ps"
            })
            results.append(result)
        
        # Sandbox status
        elif "sandbox" in description_lower:
            result = client.call_sync("docker_sandbox", "status", {})
            results.append(result)
        
        # Fallback: ejecutar como comando shell en sandbox
        else:
            result = client.call_sync("docker_sandbox", "execute_shell", {
                "command": f"echo 'Paso: {current.description}'",
                "timeout": 10
            })
            results.append(result)
        
        # Marcar paso como completado
        current.status = "done"
        
    except Exception as e:
        logger.error(f"Error ejecutando herramienta: {e}")
        errors.append(str(e))
        current.status = "failed"
    
    # Agregar artefactos con los resultados
    for i, result in enumerate(results):
        from ..state import Artifact
        state.artifacts.append(Artifact(
            type="tool_call",
            content=result[:1000] if result else "",
            metadata={"step_id": current.id, "index": i}
        ))
    
    return {
        "plan": state.plan,
        "artifacts": state.artifacts,
        "errors": state.errors + errors,
        "current_step_id": current.id,
        "metadata": state.metadata
    }
