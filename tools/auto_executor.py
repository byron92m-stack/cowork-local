"""Auto-executor: Triggers Cowork agents on file changes."""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def on_file_changed(filepath: str, watch_dir: str):
    """Called when a file changes. Decides if an agent should run."""
    
    # Solo reaccionar a archivos relevantes
    relevant_extensions = [".py", ".yaml", ".json", ".md", ".txt", ".sql"]
    ext = Path(filepath).suffix
    
    if ext not in relevant_extensions:
        return
    
    # Evitar archivos temporales
    skip_patterns = ["__pycache__", ".pyc", ".log", ".git", "venv", "node_modules"]
    for pattern in skip_patterns:
        if pattern in filepath:
            return
    
    logger.info(f"File changed: {filepath}")
    
    # Decidir qué acción tomar según el archivo
    if ext == ".py":
        action = f"Review the changes in {filepath} and check for issues"
    elif ext == ".md":
        action = f"Check the documentation update in {filepath}"
    elif ext == ".yaml":
        action = f"Validate the configuration change in {filepath}"
    else:
        action = f"Review the change in {filepath}"
    
    # Ejecutar Cowork en background
    try:
        cowork_script = os.path.join(watch_dir, "cowork")
        if os.path.exists(cowork_script):
            cmd = [cowork_script, "run", "--query", action]
            subprocess.Popen(cmd, cwd=watch_dir)
            logger.info(f"Triggered agent: {action}")
    except Exception as e:
        logger.error(f"Error triggering agent: {e}")
