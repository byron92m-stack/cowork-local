"""Background worker: IMAP polling para respuestas de email (APScheduler)."""
import os, sys, re, asyncio
import imaplib, email
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, "/media/SSD1T/cowork-local")

IMAP_HOST = os.getenv("MAIL_IMAP_HOST", "imap.mail.ru")
IMAP_PORT = int(os.getenv("MAIL_IMAP_PORT", "993"))
MAIL_USER = os.getenv("MAIL_USER", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")


from collections import defaultdict
_email_rate = defaultdict(list)  # {email: [timestamps]}

def check_email_rate(email_str, max_per_hour=3):
    from datetime import datetime, timedelta
    now = datetime.now()
    _email_rate[email_str] = [t for t in _email_rate[email_str] if now - t < timedelta(hours=1)]
    if len(_email_rate[email_str]) >= max_per_hour:
        return False
    _email_rate[email_str].append(now)
    return True

def is_valid_email(email_str):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email_str) is not None

def sanitize(text):
    text = text[:1000]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()

async def poll_inbox():
    """Revisa emails no leídos y los procesa con el booking worker."""
    if not MAIL_USER or not MAIL_PASSWORD:
        print("⚠️ MAIL_USER/MAIL_PASSWORD no configurados")
        return
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(MAIL_USER, MAIL_PASSWORD)
        mail.select("INBOX")
        
        # Buscar emails no leídos de los últimos 5 minutos
        since = (datetime.now() - timedelta(minutes=5)).strftime("%d-%b-%Y")
        result, message_ids = mail.search(None, f'(UNSEEN SINCE {since})')
        
        if not message_ids[0]:
            mail.close()
            mail.logout()
            return
        
        for num in message_ids[0].split()[-5:]:  # Máximo 5 por ciclo
            result, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Extraer cuerpo
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors='ignore')
                        break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors='ignore')
            
            body = sanitize(body)
            if not body or len(body) < 3:
                continue
            
            # Identificar paciente por email
            from_email = msg['From'] or ""
            # Extraer email del formato "Nombre <email@dominio.com>"
            match = re.search(r'<([^>]+)>', from_email)
            if match:
                from_email = match.group(1)
            
            # Validar email y rate limit
            if not is_valid_email(from_email):
                print(f"🚫 Email inválido: {from_email}")
                mail.store(num, '+FLAGS', '\Seen')
                continue
            
            if not check_email_rate(from_email):
                print(f"🚫 Rate limit: {from_email}")
                mail.store(num, '+FLAGS', '\Seen')
                continue
            
            print(f"📧 Email de {from_email}: {body[:60]}...")
            
            try:
                from graph.graph_booking import run_booking
                result = await run_booking(
                    channel="email",
                    user_id=from_email,
                    message=body
                )
                print(f"✅ Respuesta: {result.reply[:80]}...")
            except Exception as e:
                print(f"❌ Error procesando email: {e}")
            
            # Marcar como leído
            mail.store(num, '+FLAGS', '\\Seen')
        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"❌ Error IMAP: {e}")

if __name__ == "__main__":
    print("📧 Email Poller iniciado (IMAP cada 2 min)")
    import asyncio
    asyncio.run(poll_inbox())
