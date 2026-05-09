"""Memoria entre sesiones para Claude Code."""
import sys, os, json
sys.path.insert(0, "/media/SSD1T/cowork-local")
from tools.python_tools.db_tools import (
    create_session, get_session, get_artifacts_by_session, save_artifact
)
import uuid

COWORK = "/media/SSD1T/cowork-local"

def save_session(user_query, artifacts=None):
    """Guarda la sesión actual en PostgreSQL."""
    session_id = str(uuid.uuid4())
    create_session(session_id, user_query, COWORK)
    if artifacts:
        for art in artifacts:
            save_artifact(session_id, art)
    return session_id

def load_history(limit=5):
    """Carga el historial de sesiones recientes."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    conn = psycopg2.connect(
        host="localhost", port=5432, user="cowork",
        password="coworkpass", database="coworkdb"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, user_query, status, created_at 
        FROM sessions ORDER BY created_at DESC LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r["id"][:8], "query": r["user_query"][:80], 
             "status": r["status"], "date": str(r["created_at"])[:19]} for r in rows]

def load_last_artifacts(session_id=None):
    """Carga artefactos de la última sesión."""
    import psycopg2
    conn = psycopg2.connect(
        host="localhost", port=5432, user="cowork",
        password="coworkpass", database="coworkdb"
    )
    cur = conn.cursor()
    if session_id:
        cur.execute("SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            session_id = row[0]
    
    artifacts = get_artifacts_by_session(session_id) if session_id else []
    conn.close()
    return [{"type": a["type"], "preview": a["content"][:200] if a.get("content") else ""} 
            for a in artifacts[:5]]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: session_memory.py <save|load|artifacts> [args]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "save":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        sid = save_session(query)
        print(f"✅ Sesión guardada: {sid[:8]}")
    
    elif action == "load":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        history = load_history(limit)
        for h in history:
            print(f"[{h['status']}] {h['date']} - {h['query']}")
    
    elif action == "artifacts":
        sid = sys.argv[2] if len(sys.argv) > 2 else None
        arts = load_last_artifacts(sid)
        for a in arts:
            print(f"[{a['type']}] {a['preview']}")
    
    else:
        print(f"Acción desconocida: {action}")
