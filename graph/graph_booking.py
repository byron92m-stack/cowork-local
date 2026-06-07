"""Booking Worker: Vendedor IA para agendamiento medico - vFinal."""
import os, json, logging, re, httpx
import redis as redis_lib
import dateparser
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from datetime import datetime, date
from .state import BookingState
from .booking_prompts import VENDEDOR_SYSTEM, BOOKING_ROUTER_PROMPT
from .booking_db import (
    get_pool, get_or_create_patient, get_available_slots,
    create_appointment, update_appointment_status,
    get_patient_appointments, get_faqs, enqueue_email,
    detectar_y_validar_id, link_doc_to_patient
)

load_dotenv()
logger = logging.getLogger(__name__)

redis_client = redis_lib.Redis(host='localhost', port=6379, decode_responses=True)

# ─── Prompts ──────────────────────────────────────────────
EXTRACT_PROMPT = (
    'Extrae nombre y email del mensaje. Responde SOLO JSON:\n'
    '{"name": "Nombre Completo", "email": "correo@ejemplo.com"}\n'
    'Si algo falta, dejalo vacio: {"name": "", "email": ""}'
)

EXTRACT_ALL_PROMPT = (
    'Extrae cedula, nombre y email del mensaje. Responde SOLO JSON:\n'
    '{"cedula": "1712345678", "name": "Juan Perez", "email": "juan@gmail.com"}\n'
    'Si algo falta, dejalo vacio.'
)

HELP_TEXT = (
    "En que te ayudo?\\n\\n"
    "1. Agendar una cita\\n"
    "2. Ver mis citas\\n"
    "3. Cancelar una cita\\n"
    "4. Cambiar de identidad (/reset)\\n\\n"
    "Responde con el numero o la opcion."
)

WELCOME_TEXT = (
    "Hola! Necesito tu numero de cedula, RUC o pasaporte.\\n\\n"
    "Ejemplos:\\n- Cedula: 1712345678\\n- RUC: 1712345678001\\n- Pasaporte: A1234567"
)

ASK_DATA_TEXT = "Ahora necesito tu nombre completo y email.\\n\\nEjemplo: Juan Perez, juan@gmail.com"

_pool = None

# ─── Redis Helpers (doc_id como key principal) ────────────
def _state_key(state_dict):
    """Key de Redis basada en doc_id (identificador único)."""
    doc = state_dict.get('doc_id', '') or ''
    if not doc:
        doc = state_dict.get('patient_id', '') or ''
    if doc:
        return f"booking:doc:{doc}"
    channel = state_dict.get('channel', 'telegram')
    user_id = state_dict.get('user_id', 'unknown')
    return f"booking:tmp:{channel}:{user_id}"

def save_booking_state(state_dict):
    channel = state_dict.get('channel', 'telegram')
    user_id = state_dict.get('user_id', 'unknown')
    # Siempre guardar sesion temporal por canal
    key_tmp = f"booking:tmp:{channel}:{user_id}"
    redis_client.setex(key_tmp, 7200, json.dumps(state_dict, default=str))
    # Si hay doc_id, guardar tambien copia por documento
    doc = state_dict.get('doc_id', '') or ''
    if not doc:
        doc = state_dict.get('patient_id', '') or ''
    if doc and not doc.startswith('tmp:'):
        key_doc = f"booking:doc:{doc}"
        redis_client.setex(key_doc, 7200, json.dumps(state_dict, default=str))

def load_booking_state(doc_id=None, channel=None, user_id=None):
    if doc_id:
        data = redis_client.get(f"booking:doc:{doc_id}")
        if data:
            return json.loads(data)
    if channel and user_id:
        data = redis_client.get(f"booking:tmp:{channel}:{user_id}")
        if data:
            return json.loads(data)
    return {}

# ─── Helpers ──────────────────────────────────────────────
async def get_db_pool():
    global _pool
    if _pool is None:
        _pool = await get_pool()
    return _pool

async def call_llm(system, user, history=None, json_mode=False):
    import httpx
    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user})
    payload = {"model": "deepseek-chat", "messages": messages, "max_tokens": 300, "temperature": 0.7}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY', '')}"},
                json=payload
            )
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return "Lo siento, hubo un error."

def fecha_legible(date_str):
    try:
        d = date.fromisoformat(date_str)
        dias = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']
        return f"{dias[d.weekday()]} {d.day}/{d.month}"
    except Exception:
        return date_str

# ═══════════════ ROUTER ═══════════════
async def booking_router(state: BookingState) -> dict:
    pool = await get_db_pool()
    patient = await get_or_create_patient(pool, state.channel, state.user_id)
    msg = state.user_message.strip()
    hist_add = [{"role": "user", "content": state.user_message}]

    # /reset → cambiar de identidad
    if msg.lower() in ("/reset", "/reiniciar"):
        old_doc = patient.get('doc_id', '')
        async with pool.acquire() as conn:
            await conn.execute("UPDATE patients SET telegram_chat_id=NULL WHERE id=$1", str(patient['id']))
        if old_doc:
            redis_client.delete(f"booking:doc:{old_doc}")
        redis_client.delete(f"booking:tmp:{state.channel}:{state.user_id}")
        new_patient = await get_or_create_patient(pool, state.channel, state.user_id)
        return {"patient_id": str(new_patient['id']), "step": "ask_doc", "intent": "chat",
                "reply": "Identidad cambiada. " + WELCOME_TEXT, "history": []}

    # Paciente completo + sin flujo activo → Flash clasifica
    if patient.get('doc_id') and patient.get('full_name') and patient.get('email'):
        step = state.step
        if step in ("ask_date", "confirm_date", "ask_slot", "confirm"):
            return {"patient_id": str(patient['id']), "intent": "booking", "step": step,
                    "history": state.history + hist_add}
        if step == "confirm_cancel":
            return {"patient_id": str(patient['id']), "intent": "cancel", "step": step,
                    "history": state.history + hist_add}
        intent_raw = await call_llm(BOOKING_ROUTER_PROMPT, msg, json_mode=True)
        try:
            intent_data = json.loads(intent_raw)
            intent = intent_data.get('intent', 'chat').strip().lower()
        except:
            intent = intent_raw.strip().lower()
        if intent not in ("booking", "cancel", "info", "chat"):
            intent = "chat"
        logger.info(f"[BOOKING] Flash: {intent}")
        return {"patient_id": str(patient['id']), "intent": intent, "step": "router",
                "history": state.history + hist_add}

    # Sin cedula → extraer todo con Flash
    if not patient.get('doc_id'):
        info = await call_llm(EXTRACT_ALL_PROMPT, msg, json_mode=True)
        try:
            data = json.loads(info)
            cedula_raw = data.get('cedula', '').strip()
            name_raw = data.get('name', '').strip()
            email_raw = data.get('email', '').strip()
        except Exception:
            cedula_raw = name_raw = email_raw = ''

        tipo, valor = None, None
        if cedula_raw:
            tipo, val = detectar_y_validar_id(cedula_raw)
            if tipo: valor = val
        if tipo is None:
            tipo, val = detectar_y_validar_id(msg)
            if tipo: valor = val

        if tipo is None:
            return {"patient_id": str(patient['id']), "step": "ask_doc", "intent": "chat",
                    "reply": WELCOME_TEXT, "history": state.history + hist_add}

        await link_doc_to_patient(pool, str(patient['id']), tipo, valor)
        async with pool.acquire() as conn:
            if name_raw:
                await conn.execute("UPDATE patients SET full_name=$1 WHERE id=$2", name_raw[:100], str(patient['id']))
            if email_raw:
                await conn.execute("UPDATE patients SET email=$1 WHERE id=$2", email_raw[:100], str(patient['id']))
        patient = await get_or_create_patient(pool, state.channel, state.user_id)

        if patient.get('full_name') and patient.get('email'):
            return {"patient_id": str(patient['id']), "step": "show_help", "intent": "chat",
                    "reply": "Gracias! Ya tenes todos tus datos. " + HELP_TEXT,
                    "history": state.history + hist_add}

    # Faltan nombre/email
    if state.step == "ask_data":
        info = await call_llm(EXTRACT_PROMPT, msg, json_mode=True)
        try:
            data = json.loads(info)
            name = data.get('name', '').strip()
            email_addr = data.get('email', '').strip()
        except Exception:
            name = email_addr = ''
        async with pool.acquire() as conn:
            if name:
                await conn.execute("UPDATE patients SET full_name=$1 WHERE id=$2", name[:100], str(patient['id']))
            if email_addr:
                await conn.execute("UPDATE patients SET email=$1 WHERE id=$2", email_addr[:100], str(patient['id']))
        patient = await get_or_create_patient(pool, state.channel, state.user_id)
        if not patient.get('full_name') or not patient.get('email'):
            faltante = []
            if not patient.get('full_name'): faltante.append("nombre completo")
            if not patient.get('email'): faltante.append("email")
            return {"patient_id": str(patient['id']), "step": "ask_data", "intent": "chat",
                    "reply": f"Me falta tu {', '.join(faltante)}. Ej: Juan Perez, juan@gmail.com",
                    "history": state.history + hist_add}
        return {"patient_id": str(patient['id']), "step": "show_help", "intent": "chat",
                "reply": "Gracias! Ya tenes todos tus datos. " + HELP_TEXT,
                "history": state.history + hist_add}

    return {"patient_id": str(patient['id']), "step": "ask_data", "intent": "chat",
            "reply": ASK_DATA_TEXT, "history": state.history + hist_add}

# ═══════════════ CHAT ═══════════════
async def chat_flow(state: BookingState) -> dict:
    pool = await get_db_pool()
    faqs = await get_faqs(pool)
    faqs_text = "\n".join([f"- {f['question']}: {f['answer']}" for f in faqs])
    system = VENDEDOR_SYSTEM + f"\n\nINFO DEL CONSULTORIO:\n{faqs_text}"
    reply = await call_llm(system, state.user_message, state.history[:-1] if state.history else None)
    return {"reply": reply, "step": "router", "complete": False,
            "history": state.history + [{"role": "assistant", "content": reply}]}

# ═══════════════ BOOKING ═══════════════
async def booking_flow(state: BookingState) -> dict:
    pool = await get_db_pool()
    step = state.step

    if step == "router":
        return {"step": "ask_date", "reply": "Genial! Para que dia queres la cita?"}

    elif step == "ask_date":
        date_obj = dateparser.parse(state.user_message, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()})
        if date_obj:
            date_str = date_obj.strftime('%Y-%m-%d')
            prompt = (
                f"El paciente quiere agendar. dateparser entendio: {fecha_legible(date_str)} ({date_str}). "
                f"Mensaje original: '{state.user_message}'. "
                "Respondele al paciente confirmando la fecha de forma amable y pregunta si es correcta (si/no). "
                "Si la fecha no coincide, pedi que la aclare."
            )
            reply = await call_llm(VENDEDOR_SYSTEM, prompt)
            return {"selected_date": date_str, "step": "confirm_date", "reply": reply}
        else:
            return {"reply": "No entendi la fecha. Que dia te queda mejor?", "step": "ask_date"}

    elif step == "confirm_date":
        msg_lower = state.user_message.lower().strip()
        if any(w in msg_lower for w in ("si", "ok", "dale", "correcto", "bien", "confirmo")):
            try:
                date_obj = date.fromisoformat(state.selected_date)
                slots = await get_available_slots(pool, date_obj)
            except ValueError:
                return {"reply": "Error con la fecha. Probemos de nuevo. Que dia?", "step": "ask_date"}
            if not slots:
                return {"reply": f"No tengo horarios para {fecha_legible(state.selected_date)}. Otro dia?", "step": "ask_date"}
            return {"available_slots": slots, "step": "ask_slot",
                    "reply": f"Para {fecha_legible(state.selected_date)} tengo: {', '.join(slots[:6])}. Que horario preferis?"}
        else:
            return {"reply": "Entendido. Para que dia queres la cita?", "step": "ask_date"}

    elif step == "ask_slot":
        slot = None
        msg_clean = state.user_message.strip().replace(' ', '').replace('.', ':')
        if ':' in msg_clean and len(msg_clean) <= 5:
            slot = msg_clean
        if not slot:
            match = re.search(r'(\d{1,2}):?(\d{2})?', state.user_message)
            if match:
                slot = f"{match.group(1).zfill(2)}:{match.group(2) or '00'}"
        if slot and slot in state.available_slots:
            return {"selected_slot": slot, "step": "confirm",
                    "reply": f"Confirma: Consulta 30min, {fecha_legible(state.selected_date)} a las {slot}. $30. Si/no?"}
        elif slot:
            return {"reply": f"{slot} no disponible. Opciones: {', '.join(state.available_slots[:6])}"}
        else:
            return {"reply": f"Que horario? Tengo: {', '.join(state.available_slots[:6])}"}

    elif step == "confirm":
        if not state.selected_date or not state.selected_slot:
            return {"step": "router", "reply": "Faltan datos. Empecemos de nuevo. Para que dia?"}
        msg_lower = state.user_message.lower().strip()
        affirmative = any(w == msg_lower or msg_lower.startswith(w) for w in ("si", "ok", "dale", "confirmo", "acepto", "yes"))
        if affirmative:
            start_time = datetime.fromisoformat(f"{state.selected_date}T{state.selected_slot}:00-05:00")
            appt = await create_appointment(pool, state.patient_id, start_time, source_channel=state.channel)
            patient = await get_or_create_patient(pool, state.channel, state.user_id)
            if patient.get('email'):
                from tools.mcp.calendar.server import _create_ics
                ics_content = _create_ics(
                    summary="Consulta medica",
                    start=f"{state.selected_date}T{state.selected_slot}:00",
                    end=f"{state.selected_date}T{state.selected_slot}:30",
                    desc="Consulta medica general - 30 minutos")
                ics_file = f"/tmp/cita_{str(appt['id'])[:8]}.ics"
                with open(ics_file, "w") as f:
                    f.write(ics_content)
                await enqueue_email(pool, patient['email'],
                    "Confirmacion de cita medica",
                    f"Hola {patient.get('full_name', '')},\\n\\n"
                    f"Tu cita es el {state.selected_date} a las {state.selected_slot}.\\n"
                    f"Duracion: 30 minutos. Costo: $30.\\n\\n"
                    "Adjunto esta la invitacion para tu calendario.\\n\\nTe esperamos!",
                    ics_path=ics_file)
                logger.info(f"[BOOKING] ICS encolado para {patient['email']}")
            return {"appointment_id": str(appt['id']), "step": "done", "complete": True,
                    "reply": f"Listo! Cita {fecha_legible(state.selected_date)} a las {state.selected_slot}. Te envie un email con los detalles."}
        else:
            return {"step": "router", "reply": "Ok, empecemos de nuevo. Para que dia?"}
    return {"step": "done", "complete": True}

# ═══════════════ CANCEL ═══════════════
async def cancel_flow(state: BookingState) -> dict:
    pool = await get_db_pool()
    appts = await get_patient_appointments(pool, state.patient_id)
    active = [a for a in appts if a['status'] in ('pending', 'confirmed')]
    if not active:
        return {"reply": "No tenes citas activas.", "step": "router", "complete": False}
    if len(active) == 1:
        a = active[0]
        if state.step == "confirm_cancel":
            await update_appointment_status(pool, str(a['id']), 'cancelled')
            ts = a['start_time'].strftime('%d/%m %H:%M') if a['start_time'] else '?'
            return {"reply": f"Cancelada: {ts}.", "step": "done", "complete": True}
        ts = a['start_time'].strftime('%d/%m %H:%M') if a['start_time'] else '?'
        return {"appointment_id": str(a['id']), "step": "confirm_cancel",
                "reply": f"Cancelar cita del {ts}? (si/no)"}
    lista = "\n".join([f"- {x['start_time'].strftime('%d/%m %H:%M')}" for x in active])
    return {"reply": f"Tus citas:\n{lista}\nCual cancelar?", "step": "done", "complete": True}

# ═══════════════ INFO ═══════════════
async def info_flow(state: BookingState) -> dict:
    pool = await get_db_pool()
    appts = await get_patient_appointments(pool, state.patient_id)
    if not appts:
        return {"reply": "No tenes citas.", "step": "router", "complete": False}
    lista = "\n".join([f"📅 {a['start_time'].strftime('%d/%m %H:%M')} - {a['status']}" for a in appts[:5]])
    return {"reply": f"Tus citas:\n{lista}", "step": "done", "complete": True}

# ═══════════════ ROUTE ═══════════════
def route_by_intent(state: BookingState) -> str:
    if state.step in ("ask_doc", "ask_data", "show_help"):
        return state.step
    intent = state.intent
    if intent == "booking": return "booking"
    elif intent == "cancel": return "cancel"
    elif intent == "info": return "info"
    else: return "chat"

# ═══════════════ BUILD ═══════════════
def build_booking_graph():
    workflow = StateGraph(BookingState)
    nodes = [("router", booking_router), ("ask_doc", lambda s: s.model_dump()),
             ("ask_data", lambda s: s.model_dump()), ("show_help", lambda s: s.model_dump()),
             ("chat", chat_flow), ("booking", booking_flow),
             ("cancel", cancel_flow), ("info", info_flow)]
    for name, fn in nodes:
        workflow.add_node(name, fn)
    workflow.set_entry_point("router")
    workflow.add_conditional_edges("router", route_by_intent, {
        "chat": "chat", "booking": "booking", "cancel": "cancel",
        "info": "info", "ask_doc": "ask_doc", "ask_data": "ask_data", "show_help": "show_help"})
    for name, _ in nodes:
        workflow.add_edge(name, END)
    return workflow.compile()

# ═══════════════ PUBLIC API ═══════════════
async def run_booking(channel, user_id, message, history=None):
    saved = load_booking_state(channel=channel, user_id=user_id)
    # Si no hay sesión temporal, buscar por doc_id en DB
    if not saved:
        # Buscar paciente por canal para obtener doc_id (usar el pool global, no cerrar)
        pool = await get_db_pool()
        patient = await get_or_create_patient(pool, channel, user_id)
        if patient and patient.get('doc_id'):
            saved = load_booking_state(doc_id=patient['doc_id'])
    state = BookingState(
        channel=channel, user_id=user_id, user_message=message,
        patient_id=saved.get('patient_id', ''),
        step=saved.get('step', 'router'),
        intent=saved.get('intent', 'chat'),
        selected_date=saved.get('selected_date', ''),
        selected_slot=saved.get('selected_slot', ''),
        available_slots=saved.get('available_slots', []),
        appointment_id=saved.get('appointment_id', ''),
        history=saved.get('history', []) if history is None else history,
        doc_id=saved.get('doc_id', ''))
    graph = build_booking_graph()
    result = await graph.ainvoke(state)
    if result.get('step') == 'show_help':
        result['step'] = 'router'
    # Inyectar doc_id del paciente si no esta en el result
    if not result.get('doc_id'):
        pool = await get_db_pool()
        patient = await get_or_create_patient(pool, channel, user_id)
        if patient.get('doc_id'):
            result['doc_id'] = patient['doc_id']
    result['channel'] = channel
    result['user_id'] = user_id
    save_booking_state(result)
    final = BookingState(**result)
    return final
