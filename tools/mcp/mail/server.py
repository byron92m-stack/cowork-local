"""Mail MCP Server: Enviar y leer correos via Mail API"""
import os, asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cowork-mail")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="mail_send", description="Envía un email via Mail", inputSchema={"type":"object","properties":{"to":{"type":"string"},"subject":{"type":"string"},"body":{"type":"string"}},"required":["to","subject","body"]}),
        Tool(name="mail_read", description="Lee los últimos emails del inbox", inputSchema={"type":"object","properties":{"max_results":{"type":"integer","default":5}},"required":[]}),
        Tool(name="mail_setup", description="Instrucciones para configurar Mail bot", inputSchema={"type":"object","properties":{},"required":[]}),
    ]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "mail_setup":
        return [TextContent(type="text", text="📧 Configuración Mail:\n1. Creá tu cuenta en mail.ru\n2. Activá 2FA en https://account.mail.ru/user/2fa\n3. Generá App Password en https://account.mail.ru/apppasswords\n4. Agregá al .env:\n   MAIL_USER=cowork.bot@mail.ru\n   MAIL_PASSWORD=xxxx")]
    
    elif name == "mail_send":
        user = os.getenv("MAIL_USER","")
        password = os.getenv("MAIL_PASSWORD","")
        if not user or not password:
            return [TextContent(type="text", text="⚠️ Configurá MAIL_USER y MAIL_PASSWORD en .env")]
        try:
            import yagmail
            yag = yagmail.SMTP(user=user, password=password, host=os.getenv("MAIL_SMTP_HOST", "smtp.mail.ru"), port=int(os.getenv("MAIL_SMTP_PORT", "465")))
            yag.send(to=args.get("to"), subject=args.get("subject"), contents=args.get("body"))
            return [TextContent(type="text", text=f"✅ Email enviado a {args.get('to')}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error: {e}")]
    
    elif name == "mail_read":
        user = os.getenv("MAIL_USER","")
        password = os.getenv("MAIL_PASSWORD","")
        if not user or not password:
            return [TextContent(type="text", text="⚠️ Configurá MAIL_USER y MAIL_PASSWORD en .env")]
        try:
            import imaplib, email
            mail = imaplib.IMAP4_SSL("imap.mail.ru")
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
