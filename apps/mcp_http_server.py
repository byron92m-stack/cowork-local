"""
Servidor HTTP que expone los MCP Tools de Cowork-Local como API REST.
Claude Code puede llamarlos con curl.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys, os, asyncio, json

sys.path.insert(0, "/media/SSD1T/cowork-local")
from tools.mcp_client import get_mcp_client

app = FastAPI(title="Cowork-Local MCP HTTP Server")

class ToolRequest(BaseModel):
    server: str
    tool: str
    args: dict = {}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "cowork-mcp-http"}

@app.post("/call")
async def call_tool(req: ToolRequest):
    try:
        client = get_mcp_client()
        result = await client.call(req.server, req.tool, req.args)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🔧 MCP HTTP Server iniciado en http://localhost:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765)
