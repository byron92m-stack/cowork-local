"""Background worker: Envía emails de la cola. 1 por ciclo, ejecutar cada 60s con APScheduler."""
import os, sys, asyncio, logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, "/media/SSD1T/cowork-local")

logger = logging.getLogger(__name__)

MAIL_USER = os.getenv("MAIL_USER", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_SMTP_HOST = os.getenv("MAIL_SMTP_HOST", "smtp.mail.ru")
MAIL_SMTP_PORT = int(os.getenv("MAIL_SMTP_PORT", "465"))

_last_sent_time = None  # Track último envío global

async def process_email_queue():
    """Toma 1 email de la cola y lo envía. Respeta límite 1/min."""
    global _last_sent_time
    
    if not MAIL_USER or not MAIL_PASSWORD:
        return
    
    # Verificar que pasó al menos 1 minuto desde el último envío
    now = datetime.now()
    if _last_sent_time and (now - _last_sent_time).total_seconds() < 60:
        return  # Saltar este ciclo
    
    from graph.booking_db import get_pool, get_pending_emails, mark_email_sent, mark_email_failed
    
    pool = await get_pool()
    pending = await get_pending_emails(pool, limit=1)
    
    if not pending:
        await pool.close()
        return
    
    email_item = pending[0]
    try:
        import yagmail
        yag = yagmail.SMTP(
            user=MAIL_USER,
            password=MAIL_PASSWORD,
            host=MAIL_SMTP_HOST,
            port=MAIL_SMTP_PORT
        )
        
        if email_item.get('ics_path') and os.path.exists(email_item['ics_path']):
            yag.send(
                to=email_item['to_email'],
                subject=email_item['subject'],
                contents=email_item['body'],
                attachments=email_item['ics_path']
            )
        else:
            yag.send(
                to=email_item['to_email'],
                subject=email_item['subject'],
                contents=email_item['body']
            )
        
        await mark_email_sent(pool, str(email_item['id']))
        _last_sent_time = now
        logger.info(f"📧 Enviado a {email_item['to_email']}: {email_item['subject']}")
    
    except Exception as e:
        await mark_email_failed(pool, str(email_item['id']), str(e)[:200])
        logger.error(f"❌ Error email {email_item['id']}: {e}")
    
    await pool.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("📧 Email Sender iniciado (1/min)")
    asyncio.run(process_email_queue())
