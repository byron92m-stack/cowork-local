"""Background worker: Envía recordatorios de cita 24h antes."""
import os, sys, asyncio, logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, "/media/SSD1T/cowork-local")

logger = logging.getLogger(__name__)

async def send_reminders():
    """Busca citas en 24h y envía recordatorio por Telegram."""
    from graph.booking_db import get_pool
    import requests
    
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Buscar citas confirmed que empiezan en 24h (+/- 5 min)
        target = datetime.now() + timedelta(hours=24)
        start = target - timedelta(minutes=5)
        end = target + timedelta(minutes=5)
        
        rows = await conn.fetch(
            """SELECT a.id, a.start_time, p.telegram_chat_id, p.full_name
               FROM appointments a
               JOIN patients p ON a.patient_id = p.id
               WHERE a.status = 'confirmed'
               AND p.telegram_chat_id IS NOT NULL
               AND a.start_time BETWEEN $1 AND $2""",
            start, end
        )
        
        for row in rows:
            row = dict(row)
            start_str = row['start_time'].strftime('%d/%m a las %H:%M') if row['start_time'] else '?'
            msg = f"🔔 Recordatorio: Tenés una consulta médica mañana {start_str}. Te esperamos."
            
            try:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id": row['telegram_chat_id'], "text": msg},
                    timeout=10
                )
                logger.info(f"📱 Recordatorio Telegram: {row['full_name']}")
            except Exception as e:
                logger.error(f"❌ Telegram: {e}")
    
    await pool.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🔔 Reminder Job iniciado")
    asyncio.run(send_reminders())
