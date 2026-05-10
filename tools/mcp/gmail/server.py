"""Gmail MCP Server: Enviar y leer correos via Gmail API"""
import os, asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cowork-gmail")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="gmail_send", description="Envía un email via Gmail", inputSchema={"type":"object","properties":{"to":{"type":"string"},"subject":{"type":"string"},"body":{"type":"string"}},"required":["to","subject","body"]}),
        Tool(name="gmail_read", description="Lee los últimos emails del inbox", inputSchema={"type":"object","properties":{"max_results":{"type":"integer","default":5}},"required":[]}),
        Tool(name="gmail_setup", description="Instrucciones para configurar Gmail bot", inputSchema={"type":"object","properties":{},"required":[]}),
    ]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "gmail_setup":
        return [TextContent(type="text", text="📧 Configuración Gmail:\n1. Creá cowork.bot@gmail.com\n2. Activá 2FA en myaccount.google.com\n3. Generá App Password en https://myaccount.google.com/apppasswords\n4. Agregá al .env:\n   GMAIL_USER=cowork.bot@gmail.com\n   GMAIL_APP_PASSWORD=xxxx")]
    
    elif name == "gmail_send":
        user = os.getenv("GMAIL_USER","")
        password = os.getenv("GMAIL_APP_PASSWORD","")
        if not user or not password:
            return [TextContent(type="text", text="⚠️ Configurá GMAIL_USER y GMAIL_APP_PASSWORD en .env")]
        try:
            import yagmail
            yag = yagmail.SMTP(user, password)
            yag.send(to=args.get("to"), subject=args.get("subject"), contents=args.get("body"))
            return [TextContent(type="text", text=f"✅ Email enviado a {args.get('to')}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error: {e}")]
    
    elif name == "gmail_read":
        user = os.getenv("GMAIL_USER","")
        password = os.getenv("GMAIL_APP_PASSWORD","")
        if not user or not password:
            return [TextContent(type="text", text="⚠️ Configurá GMAIL_USER y GMAIL_APP_PASSWORD en .env")]
        try:
            import imaplib, email
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, password)
            mail.select("inbox")
            _, data = mail.search(None, "ALL")
            ids = data[0].split()[-args.get("max_results",5):]
            results = []
            for id in reversed(ids):
                _, msg_data = mail.fetch(id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                results.append(f"📧 {msg['subject']} | De: {msg['from']}")
            mail.close()
            mail.logout()
            return [TextContent(type="text", text="\n".join(results) if results else "Sin emails")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error: {e}")]
    
    return [TextContent(type="text", text=f"?: {name}")]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
