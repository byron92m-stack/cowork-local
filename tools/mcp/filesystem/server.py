"""MCP Server: Filesystem - v1.27.0 compatible."""
import os, glob, asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

ALLOWED_PATHS = ["/media/SSD1T/cowork-local", "/media/SSD1T/projects", "/tmp", "/media/SSD1T"]
server = Server("cowork-filesystem")

def _allowed(path: str) -> bool:
    real = os.path.realpath(os.path.expanduser(path))
    return any(real.startswith(os.path.realpath(a)) for a in ALLOWED_PATHS)

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="read_file", description="Lee un archivo", inputSchema={"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}),
        Tool(name="write_file", description="Escribe un archivo", inputSchema={"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}),
        Tool(name="list_directory", description="Lista un directorio", inputSchema={"type":"object","properties":{"path":{"type":"string"},"recursive":{"type":"boolean"}},"required":[]}),
        Tool(name="search_files", description="Busca archivos por patrón glob", inputSchema={"type":"object","properties":{"pattern":{"type":"string"},"path":{"type":"string"}},"required":["pattern"]}),
    ]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "read_file":
        path = args.get("path", "")
        if not _allowed(path): return [TextContent(type="text", text=f"Error: Ruta no permitida")]
        try:
            with open(path) as f: content = f.read()
            return [TextContent(type="text", text=content[:10000])]
        except Exception as e: return [TextContent(type="text", text=str(e))]
    
    elif name == "write_file":
        path, content = args.get("path",""), args.get("content","")
        if not _allowed(path): return [TextContent(type="text", text="Error: Ruta no permitida")]
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path,"w") as f: f.write(content)
            return [TextContent(type="text", text=f"OK: {path} ({len(content)} bytes)")]
        except Exception as e: return [TextContent(type="text", text=str(e))]
    
    elif name == "list_directory":
        path = args.get("path", "/media/SSD1T/cowork-local")
        recursive = args.get("recursive", False)
        if not _allowed(path): return [TextContent(type="text", text="Error: Ruta no permitida")]
        try:
            if recursive:
                result = []
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in ('venv','__pycache__','.git')]
                    for f in files: result.append(os.path.relpath(os.path.join(root,f), path))
                return [TextContent(type="text", text="\n".join(result[:200]))]
            return [TextContent(type="text", text="\n".join(sorted(os.listdir(path))[:50]))]
        except Exception as e: return [TextContent(type="text", text=str(e))]
    
    elif name == "search_files":
        pattern, path = args.get("pattern","*.py"), args.get("path","/media/SSD1T/cowork-local")
        try:
            matches = glob.glob(os.path.join(path,"**",pattern), recursive=True)
            matches = [m for m in matches if 'venv' not in m and '__pycache__' not in m]
            return [TextContent(type="text", text="\n".join(matches[:50]))]
        except Exception as e: return [TextContent(type="text", text=str(e))]
    
    return [TextContent(type="text", text=f"?: {name}")]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
