"""
Cowork-Local: Definición del estado global de LangGraph.

Este archivo define los modelos de datos que viajan entre los nodos
del grafo agentic. Es el contrato central que todos los nodos deben respetar.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime


# ─── Paso individual del plan ───────────────────────────────────────
class Step(BaseModel):
    """Representa un paso en el plan de ejecución."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str = Field(..., description="Descripción de la tarea a realizar")
    status: Literal["pending", "in_progress", "done", "failed"] = "pending"
    assigned_to: Optional[Literal["supervisor", "executor", "tools"]] = Field(
        default=None,
        description="Quién debe ejecutar este paso"
    )
    step_type: Optional[Literal["analysis", "code_generation", "review", "tool_call"]] = Field(
        default=None,
        description="Tipo de tarea"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


# ─── Artefacto generado ─────────────────────────────────────────────
class Artifact(BaseModel):
    """Resultado de un paso de ejecución."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["file_diff", "analysis", "plan", "log", "code", "error", "review", "code_generation", "tool_call"] = Field(
        ...,
        description="Tipo de artefacto"
    )
    path: Optional[str] = Field(
        default=None,
        description="Ruta al archivo (si aplica)"
    )
    content: Optional[str] = Field(
        default=None,
        description="Contenido del artefacto (código, diff, texto)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ─── Estado global del grafo ────────────────────────────────────────
class CoworkState(BaseModel):
    """
    Estado global que fluye entre todos los nodos del grafo LangGraph.
    
    Este objeto se serializa/deserializa en cada transición del grafo
    y puede persistirse en PostgreSQL vía checkpoint.
    """
    # Identificación de sesión
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_query: str = Field(default="", description="La consulta original del usuario")
    project_path: str = Field(default="", description="Ruta del proyecto a analizar")
    
    # Plan y ejecución
    plan: List[Step] = Field(default_factory=list)
    current_step_id: Optional[str] = Field(default=None)
    iteration_count: int = Field(default=0)
    max_iterations: int = Field(default=10)
    
    # Artefactos generados
    artifacts: List[Artifact] = Field(default_factory=list)
    
    # Trazabilidad
    tools_used: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    # Contexto enriquecido
    memory_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto recuperado de la memoria persistente (Postgres)"
    )
    project_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Información del proyecto actual (archivos, estructura)"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

    # ─── Helpers ─────────────────────────────────────────────────
    def add_step(self, description: str, assigned_to: str, step_type: str) -> Step:
        """Agrega un paso al plan y lo devuelve."""
        step = Step(
            description=description,
            assigned_to=assigned_to,
            step_type=step_type
        )
        self.plan.append(step)
        return step

    def get_pending_steps(self) -> List[Step]:
        """Devuelve los pasos pendientes."""
        return [s for s in self.plan if s.status == "pending"]

    def get_current_step(self) -> Optional[Step]:
        """Devuelve el paso actual si existe."""
        if self.current_step_id:
            for step in self.plan:
                if step.id == self.current_step_id:
                    return step
        return None

    def add_artifact(self, artifact_type: str, content: str, path: str = None) -> Artifact:
        """Agrega un artefacto y lo devuelve."""
        artifact = Artifact(
            type=artifact_type,
            content=content,
            path=path
        )
        self.artifacts.append(artifact)
        return artifact

    def add_error(self, error: str) -> None:
        """Registra un error."""
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")

    def continue_session(self, new_query: str) -> None:
        """Prepara el estado para continuar una sesión existente con una nueva query."""
        self.user_query = new_query
        # No reiniciar iteration_count, plan, artifacts, errors
        # El planner usará el contexto acumulado
    
    def is_complete(self) -> bool:
        """Verifica si todos los pasos están terminados (done o failed)."""
        if len(self.plan) == 0:
            return False
        # Verificar que no haya pasos pending o in_progress
        active_steps = [s for s in self.plan if s.status in ("pending", "in_progress")]
        return len(active_steps) == 0

    def summary(self) -> str:
        """Devuelve un resumen del estado actual."""
        return (
            f"Session: {self.session_id[:8]}... | "
            f"Steps: {len([s for s in self.plan if s.status == 'done'])}/{len(self.plan)} done | "
            f"Artifacts: {len(self.artifacts)} | "
            f"Errors: {len(self.errors)} | "
            f"Iteration: {self.iteration_count}/{self.max_iterations}"
        )
