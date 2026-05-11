"""Cliente MCP unificado para todos los MCP Servers."""
import asyncio
from typing import Dict, Any

class MCPClient:
    def __init__(self):
        self._cache = {}
    
    async def call(self, server: str, tool: str, arguments: Dict[str, Any]) -> str:
        # Mapeo completo de servidores
        if server == "filesystem":
            from tools.mcp.filesystem.server import call_tool
        elif server == "shell":
            from tools.mcp.shell.server import call_tool
        elif server == "git":
            from tools.mcp.git.server import call_tool
        elif server == "docker":
            from tools.mcp.docker.server import call_tool
        elif server == "browser":
            from tools.mcp.browser.server import call_tool
        elif server == "websearch":
            from tools.mcp.websearch.server import call_tool
        elif server == "code_sandbox":
            from tools.mcp.code_sandbox.server import call_tool
        elif server == "filewatcher":
            from tools.mcp.filewatcher.server import call_tool
        elif server == "docker_sandbox":
            from tools.mcp.docker_sandbox.server import call_tool
        elif server == "gmail":
            from tools.mcp.gmail.server import call_tool
        elif server == "googledrive":
            from tools.mcp.googledrive.server import call_tool
        elif server == "notion":
            from tools.mcp.notion.server import call_tool
        elif server == "skills":
            from tools.mcp.skills.server import call_tool
        elif server == "telegram":
            from tools.mcp.telegram.server import call_tool
        elif server == "calendar":
            from tools.mcp.calendar.server import call_tool
        else:
            return f"Error: Servidor no encontrado: {server}. Disponibles: filesystem, shell, git, docker, browser, websearch, code_sandbox, docker_sandbox, gmail, googledrive, notion, skills"
        
        try:
            result = await call_tool(tool, arguments)
            if isinstance(result, list) and len(result) > 0:
                return result[0].text if hasattr(result[0], 'text') else str(result[0])
            return str(result)
        except Exception as e:
            return f"Error MCP {server}/{tool}: {e}"
    
    def call_sync(self, server: str, tool: str, arguments: Dict[str, Any]) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
            return asyncio.run(self.call(server, tool, arguments))
        except RuntimeError:
            return asyncio.run(self.call(server, tool, arguments))

_mcp = None
def get_mcp_client() -> MCPClient:
    global _mcp
    if _mcp is None: _mcp = MCPClient()
    return _mcp
