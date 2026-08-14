import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("ferry")


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email.

    If email is disabled, SMTP is not configured, or the recipient
    address ends with ``.local``, the message is logged and suppressed.
    Errors are logged but never propagated.
    """
    if to.endswith(".local"):
        logger.info(
            "Email suppressed [to=%s] [subject=%s] [reason=%s]",
            to,
            subject,
            "development address",
        )
        return

    if not settings.email_enabled:
        logger.info(
            "Email suppressed [to=%s] [subject=%s] [reason=%s]",
            to,
            subject,
            "email disabled",
        )
        return

    if not settings.smtp_host:
        logger.info(
            "Email suppressed [to=%s] [subject=%s] [reason=%s]",
            to,
            subject,
            "SMTP not configured",
        )
        return

    msg = EmailMessage()
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        logger.info("Email sent [to=%s] [subject=%s]", to, subject)
    except Exception:
        logger.exception(
            "Failed to send email [to=%s] [subject=%s]",
            to,
            subject,
        )
