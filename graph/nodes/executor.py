"""Nodo ejecutor - Genera código con Qwen 3 GPU."""
import logging
logger = logging.getLogger(__name__)

def executor_node(state) -> dict:
    """Ejecuta el paso actual usando Qwen 3 para generar código/análisis."""
    current = state.get_current_step()
    if not current:
        return {"metadata": state.metadata}
    
    logger.info(f"[Executor] Paso {current.id[:8]}: {current.description[:80]}...")
    
    # Si es paso de tools, delegar
    if current.assigned_to == "tools":
        logger.info("[Executor] Reasignando a tools")
        return {"plan": state.plan, "metadata": state.metadata}
    
    # Si ya tiene resultado, no regenerar
    if current.status == "done":
        return {"plan": state.plan, "metadata": state.metadata}
    
    # GENERAR CON QWEN 3
    try:
        from models.qwen_ollama_client import QwenOllamaClient
        
        # Construir prompt con contexto del proyecto
        context = ""
        for artifact in state.artifacts[-5:]:  # Últimos 5 artefactos como contexto
            if artifact.content:
                context += f"\n{artifact.content[:1000]}"
        
        prompt = f"""You are a software engineer working on a project at {state.project_path}.

User request: {state.user_query}

Current step: {current.description}

Context from previous steps:
{context if context else 'No previous context'}

Generate the code, analysis, or documentation for this step. Be specific and provide working code.
If this is a code generation step, output ONLY the code with a brief explanation.
If this is an analysis step, be thorough and structured.
If this is documentation, use Markdown format."""

        logger.info(f"[Executor] Calling Qwen 3... (prompt: {len(prompt)} chars)")
        
        client = QwenOllamaClient(model="qwen3:14b")
        response = client.generate(prompt)
        
        # Guardar resultado como artefacto
        from ..state import Artifact
        state.artifacts.append(Artifact(
            type="code" if "code" in current.description.lower() or "generate" in current.description.lower() else "analysis",
            content=response[:5000],
            metadata={
                "step_id": current.id,
                "model": "qwen3:14b",
                "prompt_length": len(prompt),
                "response_length": len(response)
            }
        ))
        
        current.status = "done"
        logger.info(f"[Executor] Qwen 3 generó {len(response)} caracteres")
        
    except Exception as e:
        logger.error(f"[Executor] Error con Qwen 3: {e}")
        current.status = "failed"
        state.errors.append(f"Executor error: {str(e)}")
    
    return {
        "plan": state.plan,
        "artifacts": state.artifacts,
        "errors": state.errors,
        "metadata": state.metadata
    }
