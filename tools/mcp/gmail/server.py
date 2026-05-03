"""Gmail MCP Server - Email sending and reading."""
import os
import logging

logger = logging.getLogger(__name__)

async def call_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute email operations via Gmail."""
    
    if tool_name == "send_email":
        to = arguments.get("to", "")
        subject = arguments.get("subject", "")
        body = arguments.get("body", "")
        
        try:
            import yagmail
            user = os.getenv("GMAIL_USER")
            password = os.getenv("GMAIL_APP_PASSWORD")
            
            if user and password:
                yag = yagmail.SMTP(user, password)
                yag.send(to=to, subject=subject, contents=body)
                return [type('obj', (object,), {'text': f"Email sent to {to}"})()]
            else:
                return [type('obj', (object,), {'text': "Gmail not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD"})()]
        except ImportError:
            return [type('obj', (object,), {'text': "Install yagmail: pip install yagmail"})()]
    
    elif tool_name == "read_emails":
        limit = arguments.get("limit", 5)
        try:
            import imaplib
            import email
            from email.header import decode_header
            
            user = os.getenv("GMAIL_USER")
            password = os.getenv("GMAIL_APP_PASSWORD")
            
            if not user or not password:
                return [type('obj', (object,), {'text': "Gmail not configured"})()]
            
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, password)
            mail.select("inbox")
            
            _, messages = mail.search(None, "ALL")
            ids = messages[0].split()[-limit:]
            
            emails = []
            for id in reversed(ids):
                _, msg = mail.fetch(id, "(RFC822)")
                email_body = msg[0][1]
                message = email.message_from_bytes(email_body)
                subject = decode_header(message["subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                emails.append(f"From: {message['from']}\nSubject: {subject}\n")
            
            mail.close()
            mail.logout()
            
            return [type('obj', (object,), {'text': '\n'.join(emails)})()]
        except ImportError:
            return [type('obj', (object,), {'text': "Email reading requires imaplib"})()]
    
    else:
        return [type('obj', (object,), {'text': f"Unknown email tool: {tool_name}"})()]
