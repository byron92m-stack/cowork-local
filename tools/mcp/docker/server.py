"""MCP Server: Docker - v1.27.0 compatible."""
import subprocess, asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

ALLOWED = ["ps","logs","inspect","stats","version"]
server = Server("cowork-docker")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="docker_operation", description="Operación docker: ps, logs, inspect, stats, version", inputSchema={"type":"object","properties":{"operation":{"type":"string"},"container_name":{"type":"string"},"args":{"type":"array","items":{"type":"string"}}},"required":["operation"]})]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "docker_operation":
        op = args.get("operation","")
        container = args.get("container_name","")
        extra = args.get("args",[])
        if op not in ALLOWED: return [TextContent(type="text", text=f"No permitido: {op}")]
        try:
            cmd = ["docker", op]
            if container: cmd.append(container)
            cmd.extend(extra)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return [TextContent(type="text", text=(r.stdout or r.stderr)[:8000])]
        except Exception as e: return [TextContent(type="text", text=str(e))]
    return [TextContent(type="text", text=f"?: {name}")]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
