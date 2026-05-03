"""
Cowork-Local: Herramientas de base de datos PostgreSQL.

Proporciona funciones para guardar y recuperar:
- Sesiones (session_id, user_query, project_path, status)
- Pasos del plan (step_id, description, status, assigned_to)
- Artefactos (type, content, path)
- Memoria de proyectos (project_path, summary, decisiones)
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Configuración desde settings.yaml o variables de entorno
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "cowork"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "coworkdb"),
}


def _get_connection():
    """Obtiene una conexión a PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)


# ─── Sesiones ────────────────────────────────────────────────────

def create_session(session_id: str, user_query: str, project_path: str, metadata: Dict = None) -> bool:
    """
    Crea una nueva sesión en la base de datos.
    
    Args:
        session_id: UUID de la sesión.
        user_query: Consulta original del usuario.
        project_path: Ruta del proyecto.
        metadata: Diccionario con metadata adicional.
        
    Returns:
        True si se creó correctamente, False en caso de error.
    """
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sessions (id, user_query, project_path, status, metadata)
            VALUES (%s, %s, %s, 'active', %s)
            ON CONFLICT (id) DO UPDATE SET
                user_query = EXCLUDED.user_query,
                project_path = EXCLUDED.project_path,
                updated_at = NOW()
        """, (session_id, user_query, project_path, json.dumps(metadata or {})))
        conn.commit()
        conn.close()
        logger.debug(f"Sesión guardada: {session_id[:8]}...")
        return True
    except Exception as e:
        logger.error(f"Error guardando sesión: {e}")
        return False


def update_session_status(session_id: str, status: str) -> bool:
    """Actualiza el estado de una sesión."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE sessions SET status = %s, updated_at = NOW() WHERE id = %s",
                   (status, session_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error actualizando sesión: {e}")
        return False


def get_session(session_id: str) -> Optional[Dict]:
    """Recupera una sesión por ID."""
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error recuperando sesión: {e}")
        return None


# ─── Pasos del plan ──────────────────────────────────────────────

def save_step(session_id: str, step_data: Dict[str, Any]) -> bool:
    """
    Guarda un paso del plan en la base de datos.
    
    Args:
        session_id: UUID de la sesión.
        step_data: Diccionario con: id, step_sequence, description, status, assigned_to, metadata.
    """
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO steps (id, session_id, step_sequence, description, status, assigned_to, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                assigned_to = EXCLUDED.assigned_to,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
        """, (
            step_data.get("id"),
            session_id,
            step_data.get("step_sequence", 0),
            step_data.get("description", ""),
            step_data.get("status", "pending"),
            step_data.get("assigned_to"),
            json.dumps(step_data.get("metadata", {})),
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error guardando paso: {e}")
        return False


def save_all_steps(session_id: str, steps: List[Dict[str, Any]]) -> bool:
    """Guarda todos los pasos de una sesión."""
    success = True
    for i, step in enumerate(steps):
        step["step_sequence"] = i
        if not save_step(session_id, step):
            success = False
    return success


# ─── Artefactos ──────────────────────────────────────────────────

def save_artifact(session_id: str, artifact_data: Dict[str, Any], step_id: str = None) -> bool:
    """
    Guarda un artefacto en la base de datos.
    
    Args:
        session_id: UUID de la sesión.
        artifact_data: Diccionario con: id, type, path, content, metadata.
        step_id: UUID del paso que generó este artefacto (opcional).
    """
    try:
        conn = _get_connection()
        cur = conn.cursor()
        # Truncar contenido muy largo para la DB (máximo 50KB)
        content = artifact_data.get("content", "")
        if content and len(content) > 50000:
            content = content[:50000] + "\n... [truncado para DB]"
        
        cur.execute("""
            INSERT INTO artifacts (id, session_id, step_id, type, path, content, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata
        """, (
            artifact_data.get("id"),
            session_id,
            step_id,
            artifact_data.get("type", "log"),
            artifact_data.get("path"),
            content,
            json.dumps(artifact_data.get("metadata", {})),
        ))
        conn.commit()
        conn.close()
        logger.debug(f"Artefacto guardado: {artifact_data.get('type')} ({len(content)} chars)")
        return True
    except Exception as e:
        logger.error(f"Error guardando artefacto: {e}")
        return False


def get_artifacts_by_session(session_id: str, limit: int = 20) -> List[Dict]:
    """Recupera los artefactos de una sesión."""
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM artifacts WHERE session_id = %s 
            ORDER BY created_at DESC LIMIT %s
        """, (session_id, limit))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error recuperando artefactos: {e}")
        return []


# ─── Memoria de proyectos ────────────────────────────────────────

def save_project_memory(project_path: str, summary: str = None, 
                        architecture_notes: str = None, 
                        key_decisions: List[str] = None) -> bool:
    """
    Guarda o actualiza la memoria de un proyecto.
    
    Args:
        project_path: Ruta del proyecto.
        summary: Resumen del proyecto.
        architecture_notes: Notas de arquitectura.
        key_decisions: Lista de decisiones clave tomadas.
    """
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO project_memory (project_path, summary, architecture_notes, key_decisions, last_analyzed)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (project_path) DO UPDATE SET
                summary = COALESCE(EXCLUDED.summary, project_memory.summary),
                architecture_notes = COALESCE(EXCLUDED.architecture_notes, project_memory.architecture_notes),
                key_decisions = COALESCE(EXCLUDED.key_decisions, project_memory.key_decisions),
                last_analyzed = NOW(),
                updated_at = NOW()
        """, (
            project_path,
            summary,
            architecture_notes,
            json.dumps(key_decisions or []),
        ))
        conn.commit()
        conn.close()
        logger.info(f"Memoria del proyecto guardada: {project_path}")
        return True
    except Exception as e:
        logger.error(f"Error guardando memoria del proyecto: {e}")
        return False


def get_project_memory(project_path: str) -> Optional[Dict]:
    """Recupera la memoria de un proyecto."""
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM project_memory WHERE project_path = %s", (project_path,))
        row = cur.fetchone()
        conn.close()
        if row:
            result = dict(row)
            # Parsear key_decisions de JSON
            if result.get("key_decisions") and isinstance(result["key_decisions"], str):
                result["key_decisions"] = json.loads(result["key_decisions"])
            # Convertir fechas a string
            for date_field in ["last_analyzed", "created_at", "updated_at"]:
                if result.get(date_field):
                    result[date_field] = str(result[date_field])
            return result
        return None
    except Exception as e:
        logger.error(f"Error recuperando memoria: {e}")
        return None


# ─── Estadísticas ────────────────────────────────────────────────

def get_stats() -> Dict[str, Any]:
    """Devuelve estadísticas de la base de datos."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        stats = {}
        
        cur.execute("SELECT count(*) FROM sessions")
        stats["total_sessions"] = cur.fetchone()[0]
        
        cur.execute("SELECT count(*) FROM artifacts")
        stats["total_artifacts"] = cur.fetchone()[0]
        
        cur.execute("SELECT count(*) FROM project_memory")
        stats["projects_tracked"] = cur.fetchone()[0]
        
        cur.execute("SELECT count(*) FROM sessions WHERE status = 'active'")
        stats["active_sessions"] = cur.fetchone()[0]
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {}
