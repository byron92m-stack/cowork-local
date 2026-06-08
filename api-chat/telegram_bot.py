"""Telegram Bot - Booking Agency Worker."""
import time, requests, os, sys, json, re, asyncio
from collections import defaultdict
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "telegram_state.txt")
AUTHORIZED_CHAT_ID = "8047752200"

# Rate limiting: 15 msg/min por usuario
_ratelimit = defaultdict(list)

def check_rate(chat_id, max_per_minute=15):
    now = time.time()
    _ratelimit[chat_id] = [t for t in _ratelimit[chat_id] if now - t < 60]
    if len(_ratelimit[chat_id]) >= max_per_minute:
        return False
    _ratelimit[chat_id].append(now)
    return True

def sanitize(text):
    text = text[:500]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()

# Cargar último update_id
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        last_update_id = int(f.read().strip())
else:
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates")
    updates = r.json().get("result", [])
    last_update_id = updates[-1]["update_id"] if updates else 0
    with open(STATE_FILE, "w") as f:
        f.write(str(last_update_id))

def save_state(uid):
    with open(STATE_FILE, "w") as f:
        f.write(str(uid))

def send_message(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  json={"chat_id": chat_id, "text": text[:4000]})

# ─── Comandos ────────────────────────────────────────────
def handle_command(chat_id, text):
    cmd = text.strip().lower()
    
    if cmd in ("/start", "/ayuda", "/help"):
        return """👋 ¡Hola! Soy el asistente del consultorio.

🩺 *Consulta médica general*
• 30 minutos • $30
• Lunes a viernes, 8:00 a 17:00

*Comandos:*
/citas - Ver tus citas agendadas
/cancelar - Cancelar tu última cita
/ayuda - Ver este mensaje

Escribime para agendar una cita o hacerme cualquier consulta. 😊"""
    
    elif cmd == "/citas":
        return handle_citas(chat_id)
    
    elif cmd == "/cancelar":
        return handle_cancel(chat_id)
    
    return None

def handle_citas(chat_id):
    """Muestra citas del paciente desde DB directo (sin LLM)."""
    try:
        from graph.booking_db import get_pool, get_or_create_patient, get_patient_appointments
        import asyncio
        
        async def _get():
            pool = await get_pool()
            patient = await get_or_create_patient(pool, "telegram", str(chat_id))
            appts = await get_patient_appointments(pool, str(patient['id']))
            await pool.close()
            return appts
        
        appts = asyncio.run(_get())
        
        if not appts:
            return "No tenés citas agendadas. ¿Querés agendar una? Escribime."
        
        lines = ["📅 *Tus citas:*\n"]
        for a in appts[:5]:
            start = a['start_time'].strftime('%d/%m/%Y %H:%M') if a['start_time'] else '?'
            status_map = {
                'pending': '⏳ Pendiente',
                'confirmed': '✅ Confirmada',
                'cancelled': '❌ Cancelada',
                'completed': '✔️ Completada',
                'no_show': '🚫 No asistió'
            }
            st = status_map.get(a['status'], a['status'])
            lines.append(f"• {start} - {st}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error al consultar citas. Intentá de nuevo."

def handle_cancel(chat_id):
    """Cancela la última cita activa del paciente."""
    try:
        from graph.booking_db import get_pool, get_or_create_patient, get_patient_appointments, update_appointment_status
        import asyncio
        
        async def _cancel():
            pool = await get_pool()
            patient = await get_or_create_patient(pool, "telegram", str(chat_id))
            appts = await get_patient_appointments(pool, str(patient['id']))
            active = [a for a in appts if a['status'] in ('pending', 'confirmed')]
            
            if not active:
                await pool.close()
                return None, "No tenés citas activas para cancelar."
            
            # Cancelar la más próxima
            a = active[0]
            await update_appointment_status(pool, str(a['id']), 'cancelled', 'patient')
            start = a['start_time'].strftime('%d/%m/%Y %H:%M') if a['start_time'] else '?'
            await pool.close()
            return a, start
        
        appt, msg_or_start = asyncio.run(_cancel())
        
        if appt is None:
            return msg_or_start
        
        return f"✅ Cancelé tu cita del {msg_or_start}. Si querés reagendar, avisame."
    except Exception as e:
        return f"Error al cancelar. Intentá de nuevo."

# ─── Recordatorio ─────────────────────────────────────────
def check_reminders():
    """Busca citas en 24h y envía recordatorio por Telegram o email según source_channel."""
    import asyncio as asyncio_mod
    from graph.booking_db import get_pool, enqueue_email
    
    async def _check():
        from datetime import datetime, timedelta
        pool = await get_pool()
        async with pool.acquire() as conn:
            target = datetime.now() + timedelta(hours=24)
            start = target - timedelta(minutes=30)
            end = target + timedelta(minutes=30)
            rows = await conn.fetch(
                """SELECT a.source_channel, a.start_time, p.telegram_chat_id, p.email, p.full_name
                   FROM appointments a JOIN patients p ON a.patient_id = p.id
                   WHERE a.status = 'confirmed'
                   AND a.start_time BETWEEN $1 AND $2""",
                start, end)
            for row in rows:
                ts = row['start_time'].strftime('%d/%m a las %H:%M') if row['start_time'] else '?'
                msg = f"Recordatorio: Tenés una consulta médica mañana {ts}. Te esperamos."
                
                if row['source_channel'] == 'telegram' and row['telegram_chat_id']:
                    # Telegram → enviar por Telegram
                    try:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                            json={"chat_id": row['telegram_chat_id'], "text": f"🔔 {msg}"}, timeout=10)
                        print(f"📱 Recordatorio Telegram: {row['full_name']}")
                    except Exception as e:
                        print(f"❌ Telegram: {e}")
                elif row['source_channel'] == 'email' and row['email']:
                    # Email → encolar email de recordatorio
                    await enqueue_email(pool, row['email'],
                        "Recordatorio de cita médica",
                        f"Hola {row.get('full_name', '')},\n\n{msg}")
                    print(f"📧 Recordatorio Email encolado: {row['email']}")
        await pool.close()
    
    asyncio_mod.run(_check())

# ─── Main Loop ────────────────────────────────────────────
print("🩺 Bot del Consultorio iniciado")
print("   Comandos: /start /citas /cancelar /ayuda")

# Iniciar scheduler de recordatorios (cada 1 hora)
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', hours=1, id='reminders')
scheduler.start()
print("   Recordatorios: cada 1 hora")

while True:
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                        params={"offset": last_update_id + 1, "timeout": 10})
        updates = r.json().get("result", [])
        
        for upd in updates:
            last_update_id = upd["update_id"]
            save_state(last_update_id)
            
            msg = upd.get("message", {})
            text = msg.get("text", "")
            chat_id = msg.get("chat", {}).get("id")
            
            if not text or not chat_id:
                continue
            
            text = sanitize(text)
            chat_id_str = str(chat_id)
            
            print(f"📩 [{chat_id_str}] {text[:60]}...")
            
            # Rate limit
            if not check_rate(chat_id_str):
                send_message(chat_id, "Esperá un momento antes de enviar otro mensaje.")
                continue
            
            # Comandos
            cmd_response = handle_command(chat_id_str, text)
            if cmd_response:
                send_message(chat_id, cmd_response)
                print("✅ Comando")
                continue
            
            # Vendedor IA
            try:
                from graph.graph_booking import run_booking
                result = asyncio.run(run_booking(
                    channel="telegram",
                    user_id=chat_id_str,
                    message=text
                ))
                reply = result.reply or "¿En qué puedo ayudarte?"
                send_message(chat_id, reply)
                print("✅")
            except Exception as e:
                print(f"❌ Error: {e}")
                send_message(chat_id, "Perdón, tuve un error. ¿Probás de nuevo?")
    
    except KeyboardInterrupt:
        print(f"\n👋 Chau. Último ID: {last_update_id}")
        break
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(5)
