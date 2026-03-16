import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.celery_app import celery_app
from src.settings import settings

@celery_app.task
def send_verification_email(to_email: str, verification_link: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Подтверждение регистрации"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    text = f"Подтвердите регистрацию, перейдя по ссылке: {verification_link}"
    html = f"<p>Подтвердите регистрацию:</p><p><a href=\"{verification_link}\">{verification_link}</a></p>"
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, to_email, msg.as_string()) 