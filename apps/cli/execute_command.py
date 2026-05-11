"""Ejecuta acciones via MCP Tools. Soporta stdin y argumentos directos."""
import sys, json, asyncio, os

sys.path.insert(0, "/media/SSD1T/cowork-local")
from tools.mcp_client import get_mcp_client

async def execute(action, *args):
    client = get_mcp_client()
    
    if action == "write-file":
        path = args[0].strip().strip("'\"") if args else ""
        content = ""
        if not sys.stdin.isatty():
            try:
                content = sys.stdin.read()
            except:
                pass
        if not content and len(args) > 1:
            content = " ".join(args[1:]).strip()
            if content.startswith("'") and content.endswith("'"): content = content[1:-1]
            if content.startswith('"') and content.endswith('"'): content = content[1:-1]
            content = content.replace('\\n', '\n').replace('\\t', '\t')
        if path and content:
            result = await client.call("filesystem", "write_file", {"path": path, "content": content})
            return f"OK {path}: {result} ({len(content)} chars)"
        return f"Error: path='{path}' content={len(content)} chars"
    
    elif action == "write-json":
        path = args[0].strip().strip("'\"") if args else ""
        json_str = sys.stdin.read() if not sys.stdin.isatty() else " ".join(args[1:])
        try:
            data = json.loads(json_str)
            content = data.get("content", "")
            result = await client.call("filesystem", "write_file", {"path": path, "content": content})
            return f"OK {path}: {result} ({len(content)} chars)"
        except json.JSONDecodeError as e:
            return f"Error JSON: {e}"
    
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
        return await client.call("shell", "execute_command", {"command": f"cd {path} && python -m pytest -v 2>&1 | tail -20"})
    
    return f"OK: {action}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: cowork execute <accion> <args...>")
        sys.exit(1)
    action = sys.argv[1]
    args = sys.argv[2:]
    result = asyncio.run(execute(action, *args))
    print(result)
