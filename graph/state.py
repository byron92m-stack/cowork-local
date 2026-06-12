"""
Cowork-Local: Definición del estado global de LangGraph.

Este archivo define los modelos de datos que viajan entre los nodos
del grafo agentic. Es el contrato central que todos los nodos deben respetar.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime


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
    
    # Ejecución
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
    
    # Resultados
    reply: str = Field(default="", description="Respuesta del worker")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Resultados de sub-workers
    code_result: Dict[str, Any] = Field(default_factory=dict)
    design_result: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    # ─── Helpers ─────────────────────────────────────────────────
    # add_step() removed - dead code (Phase 35 cleanup)

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
        self.iteration_count = 0  # Reiniciar para nueva query
        self.errors = []  # Limpiar errores de sesión anterior
    
    # is_complete() removed - dead code (Phase 35 cleanup)



# ─── Estado del Worker de Código (OpenCode) ────────────────────────
class CodeWorkerState(BaseModel):
    """Estado aislado para el worker de generación de código."""
    query: str = ""
    project_name: str = "project"
    project_dir: str = ""
    tests_passed: int = 0
    tests_failed: int = 0
    reply: str = ""
    complete: bool = False
    error: str = ""
    
    class Config:
        arbitrary_types_allowed = True


# ─── Estado del Worker de Diseño (OpenDesign) ──────────────────────
class DesignWorkerState(BaseModel):
    """Estado aislado para el worker de diseño."""
    query: str = ""
    skill: str = "web-prototype"
    design_system: str = "vercel"
    reply: str = ""
    complete: bool = False
    error: str = ""
    
    class Config:
        arbitrary_types_allowed = True

# ─── Estado del Worker de Booking (Agencia de Citas) ────────────────
class BookingState(BaseModel):
    """Estado aislado para el worker de booking (vendedor IA)."""
    # Canal y usuario
    channel: str = "telegram"  # telegram | email
    user_id: str = ""  # chat_id o email
    patient_id: str = ""  # UUID del paciente en PostgreSQL
    
    # Flujo de conversación
    intent: str = "chat"  # chat | booking | cancel | reschedule | info
    step: str = "router"  # router | chat | booking | cancel | confirm | done
    
    # Datos recolectados
    service: str = "consulta_30min"
    selected_date: str = ""  # "2026-06-10"
    selected_slot: str = ""  # "09:00"
    available_slots: list = []
    
    # Cita
    appointment_id: str = ""  # UUID
    
    # Mensajes
    user_message: str = ""  # último mensaje del usuario
    reply: str = ""  # respuesta para el usuario
    
    # Historial de conversación (últimos N mensajes)
    history: list = []
    
    # Identificación única
    doc_id: str = ""  # cédula/ruc/pasaporte
    
    # Metadata
    complete: bool = False
    error: str = ""
    
    class Config:
        arbitrary_types_allowed = True


# ─── Estado del Worker de Accounting (Facturación) ──────────────────
class AccountingState(BaseModel):
    """Estado aislado para el worker de contabilidad (facturas electrónicas)."""
    # Canal y usuario
    channel: str = "email"
    user_id: str = ""  # email del remitente
    
    # Archivo adjunto
    attachment_path: str = ""  # ruta al archivo descargado (PDF/XML)
    attachment_type: str = ""  # "xml" | "pdf" | None
    
    # Datos extraídos de la factura
    invoice_data: dict = {}  # {ruc, razon_social, numero, fecha, subtotal, iva, total}
    
    # Metadata
    reply: str = ""
    complete: bool = False
    error: str = ""
    
    class Config:
        arbitrary_types_allowed = True