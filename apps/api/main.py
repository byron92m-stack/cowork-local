"""
Cowork-Local API: Endpoints REST con FastAPI.

Endpoints:
- POST /run          → Ejecutar una tarea agentic
- GET /session/{id}  → Ver una sesión guardada
- GET /sessions      → Listar sesiones recientes
- GET /stats         → Estadísticas de la base de datos
- GET /health        → Health check
"""

import sys
import os
from pathlib import Path

# Agregar el proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor

from graph.graph import run_graph
from tools.python_tools.db_tools import (
    get_session, get_artifacts_by_session, get_stats, get_project_memory
)

# ─── Función helper para conexión a DB ───────────────────────
def _get_db_connection():
    """Crea una conexión a PostgreSQL usando variables de entorno."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "cowork"),
        password=os.getenv("POSTGRES_PASSWORD", "coworkpass"),
        database=os.getenv("POSTGRES_DB", "coworkdb"),
    )

def _get_default_project():
    """Devuelve el proyecto por defecto desde variable de entorno."""
    return os.getenv("COWORK_ROOT", str(PROJECT_ROOT))

# ─── Inicializar la app ───────────────────────────────────────
app = FastAPI(
    title="Cowork-Local API",
    description="API REST para el asistente agentic de desarrollo Cowork-Local",
    version="1.0.0",
)

# ─── Modelos de datos ─────────────────────────────────────────
class RunRequest(BaseModel):
    query: str
    project_path: Optional[str] = None
    max_iterations: int = 15
    
    def get_project_path(self) -> str:
        return self.project_path or _get_default_project()

class RunResponse(BaseModel):
    session_id: str
    status: str
    steps_completed: int
    total_steps: int
    artifacts_count: int
    errors_count: int
    message: str

# ─── Endpoints ────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check: verifica que la API está corriendo."""
    return {"status": "ok", "service": "cowork-local-api"}


@app.post("/run", response_model=RunResponse)
async def run_task(request: RunRequest):
    """Ejecuta una tarea agentic y devuelve el resultado."""
    try:
        if not os.getenv("DEEPSEEK_API_KEY"):
            raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY no configurada")
        
        final_state = run_graph(
            user_query=request.query,
            project_path=request.get_project_path(),
            max_iterations=request.max_iterations,
        )
        
        steps_done = len([s for s in final_state.plan if s.status == "done"])
        return RunResponse(
            session_id=final_state.session_id,
            status="completed" if final_state.is_complete() else "in_progress",
            steps_completed=steps_done,
            total_steps=len(final_state.plan),
            artifacts_count=len(final_state.artifacts),
            errors_count=len(final_state.errors),
            message=f"Tarea completada: {steps_done}/{len(final_state.plan)} pasos",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session_endpoint(session_id: str):
    """Recupera una sesión guardada con sus artefactos."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    for field in ["created_at", "updated_at"]:
        if session.get(field):
            session[field] = str(session[field])
    
    artifacts = get_artifacts_by_session(session_id)
    session["artifacts"] = [
        {
            "id": a["id"],
            "type": a["type"],
            "content_preview": a["content"][:200] if a.get("content") else "",
            "created_at": str(a["created_at"]) if a.get("created_at") else "",
        }
        for a in artifacts
    ]
    return session


@app.get("/sessions")
async def list_sessions(limit: int = 10):
    """Lista las sesiones recientes."""
    conn = _get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, user_query, project_path, status, created_at 
        FROM sessions ORDER BY created_at DESC LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    
    return [
        {
            "id": r["id"],
            "query": r["user_query"][:100],
            "project": r["project_path"],
            "status": r["status"],
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


@app.get("/stats")
async def get_stats_endpoint():
    """Devuelve estadísticas de uso del sistema."""
    stats = get_stats()
    memory = get_project_memory(_get_default_project())
    stats["project_summary"] = memory.get("summary", "") if memory else ""
    return stats


# ─── Iniciar el servidor ──────────────────────────────────────
if __name__ == "__main__":
    print("🖥️  Cowork-Local API en http://localhost:8000")
    print("📖 Swagger UI: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
