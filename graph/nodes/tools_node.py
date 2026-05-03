"""
Nodo Tools: Ejecución de herramientas vía MCP.

Este nodo ejecuta herramientas del sistema:
- filesystem: leer/escribir archivos
- shell: comandos controlados
- git: operaciones de control de versiones
- docker: operaciones con contenedores

Por ahora es un placeholder que delega en el executor.
La integración MCP completa se hará en la FASE 10.
"""

import logging
import subprocess
import asyncio
from typing import Dict, Any
from ..state import CoworkState
from tools.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


# ─── Configuración de comandos permitidos ─────────────────────────
ALLOWED_SHELL_COMMANDS = [
    "ls", "cat", "grep", "find", "wc", "tree",
    "head", "tail", "diff", "stat", "file",
    # Comandos adicionales para análisis de proyectos
    "du", "sort", "xargs",
]

ALLOWED_GIT_OPERATIONS = [
    "status", "diff", "log", "branch", "show",
]


def tools_node(state: CoworkState) -> Dict[str, Any]:
    """
    Nodo Tools.
    
    Ejecuta herramientas del sistema de forma controlada.
    
    Args:
        state: Estado global del grafo.
        
    Returns:
        Diccionario con los campos actualizados del estado.
    """
    logger.info(f"[Tools] Iniciando. Session: {state.session_id[:8]}...")
    state.iteration_count += 1
    
    current_step = state.get_current_step()
    
    if current_step is None:
        logger.warning("[Tools] No hay paso actual")
        return state.model_dump()
    
    # Solo ejecutar pasos asignados a tools
    if current_step.assigned_to != "tools":
        return state.model_dump()
    
    logger.info(f"[Tools] Ejecutando herramienta: {current_step.description[:100]}")
    
    try:
        tool_name = current_step.metadata.get("tool_name", "")
        tool_input = current_step.metadata.get("tool_input", {})
        
        # Intentar usar MCP primero
        mcp = get_mcp_client()
        
        if tool_name == "shell" and tool_input.get("command"):
            # Usar MCP shell o fallback a subprocess
            try:
                result = mcp.call_sync("shell", "execute_command", tool_input)
                logger.info("[Tools] MCP shell ejecutado")
            except:
                result = _execute_shell(tool_input)
        elif tool_name == "git":
            try:
                result = mcp.call_sync("git", "git_operation", tool_input)
                logger.info("[Tools] MCP git ejecutado")
            except:
                result = _execute_git(tool_input)
        elif tool_name == "filesystem":
            # Detectar qué operación de filesystem
            operation = tool_input.get("operation", "list")
            if operation == "read":
                try:
                    result = mcp.call_sync("filesystem", "read_file", tool_input)
                except:
                    result = _execute_filesystem(tool_input)
            elif operation == "list":
                try:
                    result = mcp.call_sync("filesystem", "list_directory", tool_input)
                except:
                    result = _execute_filesystem(tool_input)
            else:
                result = _execute_filesystem(tool_input)
        else:
            # Detectar automáticamente según la descripción del paso
            desc = current_step.description.lower()
            # PRIMERO: verificar si es lectura de archivos (antes que listado)
            if any(word in desc for word in ["leer contenido", "leer el contenido", "leer archivo", "read file", "cat file"]):
                project_path = state.project_path or "/media/SSD1T/cowork-local"
                result = read_python_files(project_path)
                logger.info(f"[Tools] Leyendo archivos Python del proyecto")
            # SEGUNDO: verificar si pide recursión o listado completo
            elif any(cmd in desc for cmd in ["recursivo", "recursiva", "todos los archivos", "subcarpeta", "completa", "cada carpeta", "cada subcarpeta", "estructura completa"]):
                result = _execute_shell({
                    "command": "find /media/SSD1T/cowork-local -type f -name '*.py' -not -path '*/venv/*' -not -path '*/__pycache__/*' -not -path '*/.git/*'",
                    "cwd": "/media/SSD1T/cowork-local"
                })
            elif any(cmd in desc for cmd in ["tree"]):
                result = _execute_shell({
                    "command": "tree /media/SSD1T/cowork-local -I 'venv|__pycache__|*.pyc' -L 4",
                    "cwd": "/media/SSD1T/cowork-local"
                })
            elif any(cmd in desc for cmd in ["ls", "listar", "lista", "archivos", "directorio", "find", ".py", "python"]):
                result = _execute_shell({
                    "command": "find /media/SSD1T/cowork-local -type f -name '*.py' -not -path '*/venv/*' -not -path '*/__pycache__/*' -not -path '*/.git/*'",
                    "cwd": "/media/SSD1T/cowork-local"
                })
            elif "git" in desc:
                result = _execute_git({"operation": "status", "repo_path": "/media/SSD1T/cowork-local"})
            else:
                # Último recurso: si la descripción menciona "proyecto", "estructura", "analizar", etc.
                # ejecutar find para listar archivos
                if any(w in desc for w in ["proyecto", "estructura", "analizar", "directorio", "carpeta", "configuración", "dependencias"]):
                    result = _execute_shell({
                        "command": "find /media/SSD1T/cowork-local -type f -name '*.py' -not -path '*/venv/*' -not -path '*/__pycache__/*'",
                        "cwd": "/media/SSD1T/cowork-local"
                    })
                else:
                    result = f"Herramienta no reconocida: {tool_name}. Descripción: {desc[:100]}"
        
        # Guardar resultado
        state.add_artifact("log", result)
        state.tools_used.append({
            "step_id": current_step.id,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "result": result[:500],
        })
        
        current_step.status = "done"
        logger.info(f"[Tools] Herramienta ejecutada correctamente")
        
    except Exception as e:
        logger.error(f"[Tools] Error: {e}")
        current_step.status = "failed"
        state.add_error(f"Error de tools: {str(e)}")
    
    return state.model_dump()


def _execute_shell(input_data: Dict[str, Any]) -> str:
    """Ejecuta un comando shell de forma controlada."""
    command = input_data.get("command", "")
    
    # Verificar que el comando está en la lista blanca
    cmd_parts = command.split()
    if not cmd_parts:
        return "Error: comando vacío"
    
    base_cmd = cmd_parts[0]
    if base_cmd not in ALLOWED_SHELL_COMMANDS:
        return f"Error: comando '{base_cmd}' no permitido. Permitidos: {ALLOWED_SHELL_COMMANDS}"
    
    try:
        # Usar shell=True para comandos complejos con pipes, comillas, etc.
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=input_data.get("cwd", "/media/SSD1T/cowork-local"),
        )
        output = result.stdout or result.stderr
        return output[:8000]  # Limitar salida (aumentado para análisis de proyectos)
    except subprocess.TimeoutExpired:
        return "Error: timeout del comando (30s)"
    except Exception as e:
        return f"Error ejecutando comando: {str(e)}"


def _execute_git(input_data: Dict[str, Any]) -> str:
    """Ejecuta una operación git controlada."""
    operation = input_data.get("operation", "")
    
    if operation not in ALLOWED_GIT_OPERATIONS:
        return f"Error: operación git '{operation}' no permitida. Permitidas: {ALLOWED_GIT_OPERATIONS}"
    
    repo_path = input_data.get("repo_path", "/media/SSD1T/cowork-local")
    
    try:
        result = subprocess.run(
            ["git", operation],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=repo_path,
        )
        output = result.stdout or result.stderr
        return output[:8000]
    except subprocess.TimeoutExpired:
        return "Error: timeout de git (30s)"
    except Exception as e:
        return f"Error en operación git: {str(e)}"


def _execute_filesystem(input_data: Dict[str, Any]) -> str:
    """Ejecuta operaciones de filesystem controladas."""
    operation = input_data.get("operation", "read")
    path = input_data.get("path", "")
    
    # Por ahora solo lectura
    if operation == "read":
        try:
            with open(path, "r") as f:
                content = f.read()
            return content[:8000]
        except FileNotFoundError:
            return f"Error: archivo no encontrado: {path}"
        except Exception as e:
            return f"Error leyendo archivo: {str(e)}"
    
    elif operation == "list":
        import os
        try:
            files = os.listdir(path or ".")
            return "\n".join(files[:100])
        except Exception as e:
            return f"Error listando directorio: {str(e)}"
    
    return f"Operación no soportada: {operation}"

# ─── Función auxiliar: leer archivos Python del proyecto ─────────
def read_python_files(project_path: str, max_files: int = 15) -> str:
    """
    Lee todos los archivos .py de un proyecto (excluyendo venv, __pycache__)
    y devuelve un string con el contenido de cada uno, formateado para Qwen.
    
    Args:
        project_path: Ruta raíz del proyecto.
        max_files: Máximo de archivos a leer (evita sobrecarga de contexto).
        
    Returns:
        String con formato: "Archivo: ruta\n```python\ncontenido\n```\n\n"
    """
    import os
    python_files = []
    
    # Buscar archivos .py
    for root, dirs, files in os.walk(project_path):
        # Excluir directorios que no son del proyecto
        dirs[:] = [d for d in dirs if d not in ('venv', '__pycache__', '.git', 'node_modules')]
        for f in files:
            if f.endswith('.py'):
                full_path = os.path.join(root, f)
                python_files.append(full_path)
    
    # Limitar cantidad
    python_files = python_files[:max_files]
    
    # Leer cada archivo
    result_parts = []
    for filepath in sorted(python_files):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            # Truncar archivos muy largos a 3000 caracteres
            if len(content) > 3000:
                content = content[:3000] + "\n# ... (truncado)"
            relative_path = os.path.relpath(filepath, project_path)
            result_parts.append(f"### Archivo: {relative_path}\n```python\n{content}\n```")
        except Exception as e:
            result_parts.append(f"### Archivo: {filepath}\nError al leer: {e}")
    
    return "\n\n".join(result_parts)
