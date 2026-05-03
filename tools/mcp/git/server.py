"""MCP Server: Git - v1.27.0 compatible."""
import subprocess, asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

ALLOWED = ["status","diff","log","branch","show","rev-parse"]
server = Server("cowork-git")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="git_operation", description="Operación git: status, diff, log, branch, show", inputSchema={"type":"object","properties":{"operation":{"type":"string"},"repo_path":{"type":"string"},"args":{"type":"array","items":{"type":"string"}}},"required":["operation"]})]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "git_operation":
        op = args.get("operation","")
        repo = args.get("repo_path","/media/SSD1T/cowork-local")
        extra = args.get("args",[])
        if op not in ALLOWED: return [TextContent(type="text", text=f"No permitido: {op}")]
        try:
            r = subprocess.run(["git",op]+extra, capture_output=True, text=True, timeout=30, cwd=repo)
            return [TextContent(type="text", text=(r.stdout or r.stderr)[:8000])]
        except Exception as e: return [TextContent(type="text", text=str(e))]
    return [TextContent(type="text", text=f"?: {name}")]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
