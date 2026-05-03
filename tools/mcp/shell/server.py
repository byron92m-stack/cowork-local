"""MCP Server: Shell - v1.27.0 compatible."""
import subprocess, os, asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

ALLOWED = ["ls","cat","grep","find","wc","tree","head","tail","diff","stat","file","du","sort","echo","pwd","which","python","python3","git","docker"]
BLOCKED = ["rm","mv","dd","mkfs","shutdown","reboot","sudo","su"]
server = Server("cowork-shell")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="execute_command", description="Ejecuta un comando shell controlado", inputSchema={"type":"object","properties":{"command":{"type":"string"},"cwd":{"type":"string"}},"required":["command"]})]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "execute_command":
        cmd = args.get("command","")
        cwd = args.get("cwd","/media/SSD1T/cowork-local")
        if not cmd.strip(): return [TextContent(type="text", text="Error: vacío")]
        base = cmd.strip().split()[0]
        if base in BLOCKED: return [TextContent(type="text", text=f"Bloqueado: {base}")]
        if base not in ALLOWED: return [TextContent(type="text", text=f"No permitido: {base}")]
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=cwd)
            return [TextContent(type="text", text=(r.stdout or r.stderr)[:8000])]
        except subprocess.TimeoutExpired: return [TextContent(type="text", text="Timeout 30s")]
        except Exception as e: return [TextContent(type="text", text=str(e))]
    return [TextContent(type="text", text=f"?: {name}")]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
