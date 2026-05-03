"""Scheduled Tasks for Cowork-Local."""
import os
import logging
from datetime import datetime
from typing import Optional
import psycopg2

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "cowork"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "coworkdb"),
}

def schedule_task(query: str, project_path: str, cron_expression: str, description: str = "") -> Optional[str]:
    """Schedule a recurring task with CRON expression."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query TEXT NOT NULL,
                project_path TEXT NOT NULL,
                cron_expression TEXT NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT true,
                last_run TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        
        cur.execute("""
            INSERT INTO scheduled_tasks (query, project_path, cron_expression, description)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (query, project_path, cron_expression, description))
        
        task_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        
        logger.info(f"Scheduled task created: {task_id}")
        return str(task_id)
    except Exception as e:
        logger.error(f"Error scheduling task: {e}")
        return None

def get_scheduled_tasks() -> list:
    """Get all scheduled tasks."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT * FROM scheduled_tasks ORDER BY created_at DESC")
        columns = [desc[0] for desc in cur.description]
        tasks = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        return tasks
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return []
