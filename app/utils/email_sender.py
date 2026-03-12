"""SMTP email delivery helpers."""

from email.message import EmailMessage
from email.utils import formataddr
import smtplib
import ssl

from app.core.config import settings
from app.core.exceptions import ValidationException


def send_email_with_attachment(
    *,
    to_email: str,
    subject: str,
    body_text: str,
    attachment_bytes: bytes,
    attachment_filename: str,
    mime_type: str = "application/pdf",
) -> None:
    """Send an email with a single attachment using configured SMTP settings."""

    if not settings.smtp_password:
        raise ValidationException("SMTP password is not configured. Add the Gmail app password before sending email.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.smtp_sender_name, settings.smtp_sender_email))
    message["To"] = to_email
    message.set_content(body_text)

    main_type, sub_type = mime_type.split("/", 1)
    message.add_attachment(
        attachment_bytes,
        maintype=main_type,
        subtype=sub_type,
        filename=attachment_filename,
    )

    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise ValidationException(
            "Salary slip email could not be sent. Check the sender mailbox, app password, and SMTP settings."
        ) from exc
