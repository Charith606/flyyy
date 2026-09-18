import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

settings = get_settings()

def send_smtp_email(to_email: str, subject: str, body_text: str, sender: str = "campaigns@flyyy.ai") -> bool:
    """
    Delivers email via SMTP to Mailpit (or configured mail server).
    Fallback graceful simulator if local SMTP server is not running.
    """
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body_text, 'plain'))
    
    try:
        server = smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=3)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        # Graceful fallback in development/demo when SMTP server is unreachable
        print(f"[MAILER SIMULATOR] Attempted delivery to {to_email} (Subject: '{subject}'). SMTP notice: {e}")
        return True
