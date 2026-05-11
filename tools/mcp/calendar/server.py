"""Google Calendar via Email (simple, funcional, sin OAuth)"""
import os, asyncio
from datetime import datetime, timedelta
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cowork-calendar")

def _create_ics(summary: str, start: str, end: str, desc: str = "") -> str:
    """Crea un archivo .ics (invitación de calendario)"""
    now = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Cowork-Local//Calendar//ES
BEGIN:VEVENT
DTSTART:{start.replace('-','').replace(':','')}00
DTEND:{end.replace('-','').replace(':','')}00
SUMMARY:{summary}
DESCRIPTION:{desc}
DTSTAMP:{now}
END:VEVENT
END:VCALENDAR"""
    return ics

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="calendar_add", description="Agrega un evento enviando invitación por email", inputSchema={"type":"object","properties":{"summary":{"type":"string"},"start_time":{"type":"string"},"end_time":{"type":"string"},"description":{"type":"string"}},"required":["summary","start_time","end_time"]}),
        Tool(name="calendar_help", description="Instrucciones de uso del calendario", inputSchema={"type":"object","properties":{},"required":[]}),
    ]

@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "calendar_help":
        return [TextContent(type="text", text="📅 Calendar via Email:\nEl sistema envía invitaciones .ics a tu Gmail.\nGmail las agrega automáticamente a tu calendario.\nNo necesita OAuth ni permisos especiales.")]
    
    elif name == "calendar_add":
        summary = args.get("summary","")
        start = args.get("start_time","")
        end = args.get("end_time","")
        desc = args.get("description","Creado por Cowork-Local")
        
        # Crear archivo .ics
        ics_content = _create_ics(summary, start, end, desc)
        ics_file = f"/tmp/event_{datetime.now().strftime('%Y%m%d%H%M%S')}.ics"
        with open(ics_file, "w") as f:
            f.write(ics_content)
        
        # Enviar por Gmail
        user = os.getenv("GMAIL_USER","")
        pwd = os.getenv("GMAIL_APP_PASSWORD","")
        if not user or not pwd:
            return [TextContent(type="text", text="⚠️ Configurá GMAIL_USER y GMAIL_APP_PASSWORD en .env")]
        
        try:
            import yagmail
            yag = yagmail.SMTP(user, pwd)
            yag.send(
                to=user,
                subject=f"📅 {summary}",
                contents=f"Evento: {summary}\nInicio: {start}\nFin: {end}\n\n{desc}",
                attachments=ics_file
            )
            os.remove(ics_file)
            return [TextContent(type="text", text=f"✅ Evento enviado a tu calendario: {summary}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error: {e}")]
    
    return [TextContent(type="text", text=f"?: {name}")]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
