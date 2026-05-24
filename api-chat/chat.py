from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from db import get_session, create_message, get_messages_by_user
from models import (
    ChatResponse,
    MessageCreate,
    MessageResponse,
    UserResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user_msg = await create_message(
        session, current_user.id, "user", message_data.content
    )
    reply_content = _generate_reply(message_data.content)
    bot_msg = await create_message(
        session, current_user.id, "assistant", reply_content
    )
    return ChatResponse(
        reply=reply_content,
        message=MessageResponse.model_validate(user_msg),
    )


@router.get("/history", response_model=list[MessageResponse])
async def get_history(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    messages = await get_messages_by_user(session, current_user.id, limit, offset)
    return [MessageResponse.model_validate(m) for m in messages]


def _generate_reply(user_message: str) -> str:
    user_lower = user_message.strip().lower()
    if "hello" in user_lower or "hi" in user_lower or "hola" in user_lower:
        return "¡Hola! Soy tu asistente con acceso a Cowork. Puedo buscar archivos, crear proyectos, analizar documentos, y más. ¿En qué te ayudo?"
    if "how are you" in user_lower:
        return "I'm doing great, thanks for asking!"
    if "bye" in user_lower or "goodbye" in user_lower:
        return "Goodbye! Have a great day!"
    if "?" in user_message:
        return "That's an interesting question. Let me think about it..."
    return f"You said: {user_message}"


# ─── DeepSeek Integration ────────────────────────────────
import httpx, os, sys, json, redis

# Cliente Redis para sesiones
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

import logging
logger = logging.getLogger(__name__)

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")

ASSISTANT_PROMPT = """Eres un asistente personal con acceso a Cowork-Local. Podés ejecutar acciones reales en la computadora del usuario.
CAPACIDADES: Buscar archivos, modificar documentos, navegar internet, ejecutar comandos, buscar información, generar proyectos de código.
Cuando el usuario te pida algo, ejecutá la acción. Si no podés, explicale por qué. Siempre respondé con un resumen claro."""


async def _call_deepseek(system_prompt: str, user_message: str) -> str:
    if not DEEPSEEK_KEY:
        return _generate_reply(user_message)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return _generate_reply(user_message)


@router.post("/assistant", response_model=ChatResponse)
async def send_assistant_message(
    message_data: MessageCreate,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Endpoint de asistente personal con acceso a Cowork."""
    user_msg = await create_message(
        session, current_user.id, "user", message_data.content
    )
    
    try:
        sys.path.insert(0, "/media/SSD1T/cowork-local")
        if not os.environ.get("DEEPSEEK_API_KEY"):
            os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_KEY or "sk-122139651350414899e1617d190c94f3"
        from graph.graph import run_graph, continue_graph
        from graph.state import CoworkState
        
        # Determinar session_id: extraer el ID real de la sesión
        raw_chat_id = message_data.chat_id if hasattr(message_data, 'chat_id') and message_data.chat_id else str(current_user.id)
        # Si viene con prefijo "cowork:session:", extraer el nombre
        if raw_chat_id.startswith("cowork:session:"):
            session_key = raw_chat_id
            session_id = raw_chat_id.replace("cowork:session:", "")
        else:
            session_id = str(raw_chat_id)
            session_key = f"cowork:session:{session_id}"
        
        # Intentar continuar sesión existente
        saved = redis_client.get(session_key)
        if saved:
            state_data = json.loads(saved)
            state = CoworkState(**state_data)
            result = continue_graph(state, message_data.content, max_iterations=2)
        else:
            result = run_graph(message_data.content, max_iterations=2)
        
        # Guardar estado para el próximo mensaje
        redis_client.setex(session_key, 3600, json.dumps(result.model_dump(), default=str))
        
        reply_content = result.metadata.get("reply", "")
        if not reply_content:
            passed = result.metadata.get("tests_passed", 0)
            failed = result.metadata.get("tests_failed", 0)
            reply_content = f"✅ Tarea ejecutada. Tests: {passed} passed, {failed} failed."
    except Exception as e:
        import traceback
        logger.error(f"Assistant error: {traceback.format_exc()}")
        reply_content = f"❌ Error: {str(e)[:200]}"
    
    bot_msg = await create_message(
        session, current_user.id, "assistant", reply_content
    )
    return ChatResponse(
        reply=reply_content,
        message=MessageResponse.model_validate(user_msg),
    )
