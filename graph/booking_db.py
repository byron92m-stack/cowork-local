"""Funciones de base de datos para el Booking Worker."""
import os
import asyncpg
from typing import Optional, List, Dict
from datetime import datetime, date, time

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_USER = os.getenv('POSTGRES_USER', 'cowork')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'coworkpass')
DB_NAME = os.getenv('POSTGRES_DB', 'coworkdb')

async def get_pool():
    return await asyncpg.create_pool(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME,
        min_size=1, max_size=5
    )

# ─── Pacientes ──────────────────────────────────────────────
async def get_or_create_patient(pool, channel: str, user_id: str, full_name: str = None, email: str = None, patient_id: str = None, doc_id: str = None) -> dict:
    """Busca paciente por doc_id (cedula) > patient_id (UUID) > telegram_chat_id > email+channel.
    Crea uno nuevo solo si no existe ninguna coincidencia."""
    async with pool.acquire() as conn:
        row = None
        
        # 1. Buscar por doc_id (cedula/ruc/pasaporte) - llave universal
        if doc_id:
            row = await conn.fetchrow("SELECT * FROM patients WHERE doc_id = $1", doc_id)
            if row:
                # Actualizar canal si es necesario
                if channel == "telegram" and not row['telegram_chat_id']:
                    try:
                        row = await conn.fetchrow(
                            "UPDATE patients SET telegram_chat_id=$1 WHERE id=$2 RETURNING *",
                            user_id, row['id']
                        )
                    except UniqueViolationError:
                        # Otro paciente ya tiene ese chat_id, liberarlo primero
                        await conn.execute(
                            "UPDATE patients SET telegram_chat_id=NULL WHERE telegram_chat_id=$1 AND id != $2",
                            user_id, row['id']
                        )
                        row = await conn.fetchrow(
                            "UPDATE patients SET telegram_chat_id=$1 WHERE id=$2 RETURNING *",
                            user_id, row['id']
                        )
                return dict(row)
        
        # 2. Buscar por UUID
        if patient_id:
            try:
                from uuid import UUID
                uuid_obj = UUID(patient_id)
                row = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", uuid_obj)
                if row:
                    return dict(row)
            except (ValueError, TypeError):
                pass
        
        # 3. Buscar por telegram_chat_id
        if channel == "telegram":
            row = await conn.fetchrow("SELECT * FROM patients WHERE telegram_chat_id = $1", user_id)
            if row:
                return dict(row)
        
        # 4. Buscar por email
        if email:
            row = await conn.fetchrow("SELECT * FROM patients WHERE email = $1", email)
            if row:
                return dict(row)
        
        # 5. Crear nuevo paciente
        if channel == "telegram":
            row = await conn.fetchrow(
                "INSERT INTO patients (telegram_chat_id, full_name, email) VALUES ($1, $2, $3) RETURNING *",
                user_id, full_name, email
            )
        else:
            row = await conn.fetchrow(
                "INSERT INTO patients (full_name, email) VALUES ($1, $2) RETURNING *",
                full_name or '', email or user_id
            )
        return dict(row)

# ─── Disponibilidad ─────────────────────────────────────────
async def get_availability(pool, weekday: int) -> dict:
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM availability WHERE weekday = $1 AND is_active = TRUE", weekday
        )

async def get_available_slots(pool, date_str) -> List[str]:
    """Devuelve slots disponibles para una fecha (formato 'YYYY-MM-DD')."""
    from datetime import date, timedelta
    if isinstance(date_str, str):
        d = date.fromisoformat(date_str)
    else:
        d = date_str
    weekday = d.weekday()  # 0=Lunes
    
    avail = await get_availability(pool, weekday)
    if not avail:
        return []
    
    start = avail['start_time']
    end = avail['end_time']
    duration = avail['slot_duration_minutes']
    
    # Generar todos los slots posibles
    slots = []
    current = datetime.combine(d, start)
    end_dt = datetime.combine(d, end)
    while current + timedelta(minutes=duration) <= end_dt:
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=duration)
    
    # Filtrar slots ocupados
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT start_time FROM appointments WHERE start_time::date = $1::date AND status NOT IN ('cancelled', 'no_show')",
            date_str
        )
        occupied = {r['start_time'].strftime('%H:%M') for r in rows}
    
    return [s for s in slots if s not in occupied]

# ─── Citas ──────────────────────────────────────────────────
async def create_appointment(pool, patient_id: str, start_time: str, duration: int = 30, 
                             source_channel: str = "telegram", notes: str = None) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO appointments (patient_id, start_time, duration_minutes, status, source_channel, notes)
               VALUES ($1, $2, $3, 'pending', $4, $5) RETURNING *""",
            patient_id, start_time, duration, source_channel, notes
        )
        # Registrar en historial
        await conn.execute(
            "INSERT INTO appointment_history (appointment_id, old_status, new_status, changed_by) VALUES ($1, NULL, 'pending', 'system')",
            row['id']
        )
        return dict(row)

async def update_appointment_status(pool, appointment_id: str, new_status: str, changed_by: str = "patient") -> dict:
    async with pool.acquire() as conn:
        old = await conn.fetchrow("SELECT status FROM appointments WHERE id = $1", appointment_id)
        row = await conn.fetchrow(
            "UPDATE appointments SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
            new_status, appointment_id
        )
        await conn.execute(
            "INSERT INTO appointment_history (appointment_id, old_status, new_status, changed_by) VALUES ($1, $2, $3, $4)",
            appointment_id, old['status'] if old else None, new_status, changed_by
        )
        return dict(row)

async def get_patient_appointments(pool, patient_id: str, status: str = None) -> List[dict]:
    async with pool.acquire() as conn:
        query = "SELECT * FROM appointments WHERE patient_id = $1"
        args = [patient_id]
        if status:
            query += " AND status = $2"
            args.append(status)
        query += " ORDER BY start_time DESC LIMIT 10"
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]

# ─── FAQs ───────────────────────────────────────────────────
async def get_faqs(pool, category: str = None) -> List[dict]:
    async with pool.acquire() as conn:
        if category:
            rows = await conn.fetch("SELECT * FROM faqs WHERE category = $1", category)
        else:
            rows = await conn.fetch("SELECT * FROM faqs")
        return [dict(r) for r in rows]

# ─── Email Queue ────────────────────────────────────────────
async def enqueue_email(pool, to_email: str, subject: str, body: str, ics_path: str = None) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO email_queue (to_email, subject, body, ics_path) VALUES ($1, $2, $3, $4) RETURNING *",
            to_email, subject, body, ics_path
        )
        return dict(row)

async def get_pending_emails(pool, limit: int = 1) -> List[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM email_queue WHERE status = 'pending' ORDER BY created_at LIMIT $1", limit
        )
        return [dict(r) for r in rows]

async def mark_email_sent(pool, email_id: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE email_queue SET status = 'sent', sent_at = NOW() WHERE id = $1", email_id
        )

async def mark_email_failed(pool, email_id: str, error: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE email_queue SET status = 'failed', error_msg = $1 WHERE id = $2", error, email_id
        )

# ─── Identificación (cédula/ruc/pasaporte) ─────────────────

def validar_cedula_ecuador(cedula: str) -> bool:
    """Valida cédula ecuatoriana (10 dígitos + algoritmo módulo 10)."""
    if not cedula or len(cedula) != 10 or not cedula.isdigit():
        return False
    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        return False
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for i in range(9):
        mult = int(cedula[i]) * coeficientes[i]
        suma += mult if mult < 10 else mult - 9
    resultado = 10 - (suma % 10)
    if resultado == 10:
        resultado = 0
    return resultado == int(cedula[9])

def validar_ruc_ecuador(ruc: str) -> bool:
    """RUC ecuatoriano: 13 dígitos, termina en 001, primeros 10 = cédula válida."""
    if not ruc or len(ruc) != 13 or not ruc.isdigit() or not ruc.endswith('001'):
        return False
    return validar_cedula_ecuador(ruc[:10])

def validar_pasaporte(pasaporte: str) -> bool:
    """Pasaporte: alfanumérico, 6-12 caracteres."""
    if not pasaporte or len(pasaporte) < 6 or len(pasaporte) > 12:
        return False
    return pasaporte.replace('-', '').isalnum()

def detectar_y_validar_id(valor: str) -> tuple:
    """Detecta tipo de documento y lo valida. Retorna (tipo, valor_limpio) o (None, error)."""
    valor = valor.strip().replace(' ', '').replace('-', '').replace('.', '')
    
    if len(valor) == 10 and valor.isdigit():
        if validar_cedula_ecuador(valor):
            return ('cedula', valor)
        return (None, 'Esa cédula no es válida. Revisala.')
    
    elif len(valor) == 13 and valor.isdigit() and valor.endswith('001'):
        if validar_ruc_ecuador(valor):
            return ('ruc', valor)
        return (None, 'Ese RUC no es válido. Revisalo.')
    
    elif 6 <= len(valor) <= 12 and valor.isalnum():
        return ('pasaporte', valor)
    
    return (None, 'No reconozco ese documento. Usá cédula (10 dígitos), RUC (13 dígitos) o pasaporte.')

async def get_patient_by_doc(pool, doc_id: str) -> dict:
    """Busca paciente por documento."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM patients WHERE doc_id = $1", doc_id)
        return dict(row) if row else None

async def link_doc_to_patient(pool, patient_id: str, id_type: str, doc_id: str) -> dict:
    """Vincula documento a paciente. Si ya existe en otro, lo mueve a este.
    Usa transacción para atomicidad."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Verificar si el doc_id ya pertenece a otro paciente
            existing = await conn.fetchrow(
                "SELECT id FROM patients WHERE doc_id = $1 AND id != $2 FOR UPDATE",
                doc_id, patient_id
            )
            if existing:
                # Quitar doc_id del paciente anterior
                await conn.execute(
                    "UPDATE patients SET doc_id = NULL, id_type = NULL WHERE id = $1",
                    existing['id']
                )
            
            row = await conn.fetchrow(
                "UPDATE patients SET id_type = $1, doc_id = $2, updated_at = NOW() WHERE id = $3 RETURNING *",
                id_type, doc_id, patient_id
            )
            return dict(row) if row else None

async def create_patient_with_doc(pool, id_type: str, doc_id: str, full_name: str = None,
                                   email: str = None, telegram_chat_id: str = None) -> dict:
    """Crea paciente nuevo con documento."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO patients (id_type, doc_id, full_name, email, telegram_chat_id)
               VALUES ($1, $2, $3, $4, $5) RETURNING *""",
            id_type, doc_id, full_name, email, telegram_chat_id
        )
        return dict(row) if row else None
