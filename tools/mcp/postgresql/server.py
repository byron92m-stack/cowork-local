"""MCP PostgreSQL Server"""
import os, json, psycopg2
from psycopg2.extras import RealDictCursor

def _get_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "cowork"),
        password=os.getenv("POSTGRES_PASSWORD", "coworkpass"),
        database=os.getenv("POSTGRES_DB", "coworkdb")
    )

async def list_tools():
    return [
        {"name": "query", "description": "Execute SQL query (SELECT only)"},
        {"name": "execute", "description": "Execute SQL (INSERT/UPDATE/DELETE)"},
        {"name": "tables", "description": "List all tables and their columns"}
    ]

async def call_tool(name, args):
    conn = _get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if name == "query":
            cur.execute(args["sql"])
            rows = cur.fetchall()
            return [{"type": "text", "text": json.dumps([dict(r) for r in rows], default=str)}]
        elif name == "execute":
            cur.execute(args["sql"])
            conn.commit()
            return [{"type": "text", "text": f"OK. {cur.rowcount} rows affected"}]
        elif name == "tables":
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            return [{"type": "text", "text": json.dumps([r["table_name"] for r in cur.fetchall()])}]
    finally:
        cur.close()
        conn.close()
