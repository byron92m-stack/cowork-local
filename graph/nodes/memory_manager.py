"""Nodo de memoria - Persiste sesiones y guarda archivos generados."""
import os
import re
import logging

logger = logging.getLogger(__name__)

def _detect_filename(content: str, step_desc: str) -> str:
    """Detecta nombre de archivo por contenido + descripción del paso."""
    desc = step_desc.lower()
    first_line = content.strip().split("\n")[0].lower() if content else ""
    first_50 = content.strip()[:50].lower()
    
    # 1. Detección por nombre explícito en la descripción del paso (más confiable)
    if "requirements.txt" in desc or "requirements" in desc:
        return "requirements.txt"
    if "database.py" in desc or "database" in desc:
        return "database.py"
    if "models.py" in desc or "models" in desc:
        return "models.py"
    if "main.py" in desc:
        return "main.py"
    if "readme" in desc:
        return "README.md"
    if "dockerfile" in desc:
        return "Dockerfile"
    if "docker-compose" in desc:
        return "docker-compose.yml"
    if "test" in desc and ".py" in desc:
        return "test_api.py"
    
    # 2. Detección por primeras líneas del contenido
    if "fastapi" in first_line and "uvicorn" in first_50:
        return "requirements.txt"
    if "from fastapi import" in first_50 or "app = fastapi" in first_50:
        return "main.py"
    if "from sqlalchemy" in first_50 or "create_engine" in first_50:
        return "database.py"
    if "from pydantic" in first_50 or "class" in first_line and "basemodel" in first_50:
        return "models.py"
    if content.strip().startswith("# ") and "api" in first_50:
        return "README.md"
    if "from fastapi" in first_50 and "import" in first_line:
        return "main.py"
    
    # 3. Detección por contenido completo
    content_lower = content.lower()[:500]
    if "pip install" in content_lower or "fastapi" in content_lower and "uvicorn" in content_lower:
        if "class" not in content_lower and "def " not in content_lower:
            return "requirements.txt"
    if "sessionlocal" in content_lower or "session = sessionmaker" in content_lower:
        return "database.py"
    
    return None

def memory_manager_node(state) -> dict:
    """PRE-RUN: Carga memoria. POST-RUN: Guarda sesión y archivos."""
    
    # PRE-RUN
    if not state.metadata.get("memory_loaded"):
        logger.info(f"[Memory] PRE-RUN: {state.project_path}")
        try:
            from tools.python_tools.db_tools import get_project_memory
            memory = get_project_memory(state.project_path)
            if memory:
                state.metadata["project_memory"] = memory
        except:
            pass
        state.metadata["memory_loaded"] = True
        return {"plan": state.plan, "metadata": state.metadata}
    
    # POST-RUN
    if not state.metadata.get("session_saved"):
        logger.info("[Memory] POST-RUN: Guardando...")
        
        saved_files = {}
        for artifact in state.artifacts:
            if artifact.content and artifact.type in ["code", "analysis"]:
                # Buscar descripción del paso asociado
                step_desc = ""
                for step in state.plan:
                    if step.id == artifact.metadata.get("step_id"):
                        step_desc = step.description
                        break
                
                filename = _detect_filename(artifact.content, step_desc)
                
                if filename:
                    clean = artifact.content
                    # Limpiar bloques markdown
                    if clean.startswith("```"):
                        lines = clean.split("\n")
                        lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        clean = "\n".join(lines)
                    # Limpiar prefijos de ruta
                    clean = re.sub(r'^#\s*/.*?\.py\n', '', clean)
                    clean = clean.strip() + "\n"
                    
                    filepath = os.path.join(state.project_path, filename)
                    os.makedirs(os.path.dirname(filepath) or state.project_path, exist_ok=True)
                    
                    try:
                        with open(filepath, "w") as f:
                            f.write(clean)
                        saved_files[filename] = len(clean)
                    except Exception as e:
                        logger.error(f"[Memory] ❌ {filename}: {e}")
        
        # PostgreSQL
        try:
            from tools.python_tools.db_tools import create_session, save_all_steps, save_artifact, update_session_status
            create_session(state.session_id, state.user_query, state.project_path)
            steps_data = [{"id": s.id, "description": s.description, "status": s.status, "assigned_to": s.assigned_to, "metadata": s.metadata} for s in state.plan]
            save_all_steps(state.session_id, steps_data)
            for art in state.artifacts:
                save_artifact(state.session_id, {"id": art.id, "type": art.type, "content": art.content[:5000] if art.content else "", "metadata": art.metadata})
            update_session_status(state.session_id, "completed")
        except Exception as e:
            logger.error(f"[Memory] DB: {e}")
        
        state.metadata["session_saved"] = True
        state.metadata["saved_files"] = list(saved_files.keys())
        logger.info(f"[Memory] {len(saved_files)} archivos: {list(saved_files.keys())}")
        
        return {"plan": state.plan, "artifacts": state.artifacts, "metadata": state.metadata}
    
    return {"metadata": state.metadata}
