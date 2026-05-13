"""Telegram MCP Server: Enviar y leer mensajes via Telegram Bot API"""
import os, asyncio, httpx
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cowork-telegram")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="telegram_send", description="Envía un mensaje via Telegram Bot", inputSchema={"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}),
        Tool(name="telegram_read", description="Lee los últimos mensajes enviados al bot", inputSchema={"type":"object","properties":{"limit":{"type":"integer","default":5}},"required":[]}),
        Tool(name="telegram_setup", description="Instrucciones para configurar Telegram Bot", inputSchema={"type":"object","properties":{},"required":[]}),
    ]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "telegram_setup":
        return [TextContent(type="text", text="📱 Bot: @byron92m_bot | Chat ID: ${TELEGRAM_CHAT_ID}")]
    
    elif name == "telegram_send":
        token = os.getenv("TELEGRAM_BOT_TOKEN","")
        chat_id = os.getenv("TELEGRAM_CHAT_ID","")
        if not token or not chat_id:
            return [TextContent(type="text", text="⚠️ Configurá TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env")]
        try:
            r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat_id,"text":f"🤖 {args.get('text')}"}, timeout=10)
            return [TextContent(type="text", text="✅ Enviado" if r.json().get("ok") else f"❌ {r.json().get('description')}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ {e}")]
    
    elif name == "telegram_read":
        token = os.getenv("TELEGRAM_BOT_TOKEN","")
        if not token:
            return [TextContent(type="text", text="⚠️ Configurá TELEGRAM_BOT_TOKEN en .env")]
        try:
            r = httpx.post(f"https://api.telegram.org/bot{token}/getUpdates", json={"limit": args.get("limit",5)}, timeout=10)
            data = r.json()
            msgs = data.get("result",[])
            out = []
            for m in msgs:
                msg = m.get("message",{})
                out.append(f"💬 {msg.get('from',{}).get('first_name','?')}: {msg.get('text','')[:200]}")
            return [TextContent(type="text", text="\n".join(out) if out else "Sin mensajes")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ {e}")]
    
    return [TextContent(type="text", text=f"?: {name}")]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
