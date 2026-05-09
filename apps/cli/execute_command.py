"""Ejecuta acciones de Claude Code via MCP Tools. Soporta stdin para contenido multilinea."""
import sys, json, asyncio, os

sys.path.insert(0, "/media/SSD1T/cowork-local")
from tools.mcp_client import get_mcp_client

async def execute(action, *args):
    client = get_mcp_client()
    
    if action == "write-file":
        # El path es el primer argumento. El contenido viene por stdin.
        path = args[0].strip().strip("'\"") if args else ""
        content = sys.stdin.read()
        if path and content:
            result = await client.call("filesystem", "write_file", {"path": path, "content": content})
            return f"OK {path}: {result}"
        return "Error: path o content vacios"
    
    elif action == "run-command":
        cmd = " ".join(args).strip().strip("'\"")
        return await client.call("shell", "execute_command", {"command": cmd})
    
    elif action == "list-files":
        path = " ".join(args).strip().strip("'\"") or "/media/SSD1T/cowork-local"
        return await client.call("filesystem", "list_directory", {"path": path})
    
    elif action == "git-status":
        return await client.call("git", "git_operation", {"operation": "status"})
    
    elif action == "run-tests":
        path = " ".join(args).strip().strip("'\"") or "/media/SSD1T/cowork-local"
        result = await client.call("shell", "execute_command", {
            "command": f"cd {path} && python -m pytest -v 2>&1 | tail -20"
        })
        return result
    
    return f"OK: {action}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: cowork execute <accion> <args...>")
        sys.exit(1)
    action = sys.argv[1]
    args = sys.argv[2:]
    result = asyncio.run(execute(action, *args))
    print(result)
