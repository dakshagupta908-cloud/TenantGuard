from datetime import timedelta
from email.message import EmailMessage
import smtplib
import ssl

import httpx

from app.config import settings
from app.models import DemandLetter


class DeliveryError(Exception):
    pass


def send_letter_email(recipient_email: str, letter: DemandLetter) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise DeliveryError("Email delivery is not configured.")
    if bool(settings.SMTP_USERNAME) != bool(settings.SMTP_PASSWORD):
        raise DeliveryError("Email delivery credentials are incomplete.")

    message = EmailMessage()
    message["Subject"] = "TenantGuard repair notice"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient_email
    message.set_content(letter.content)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls(context=ssl.create_default_context())
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise DeliveryError("Email delivery failed. Check the SMTP configuration.") from exc


def send_letter_sms(recipient_phone: str, letter: DemandLetter) -> None:
    if not all(
        (
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_FROM_NUMBER,
        )
    ):
        raise DeliveryError("SMS delivery is not configured.")

    due_date = letter.created_at + timedelta(days=letter.response_deadline_days)
    deadline = due_date.strftime("%B %d, %Y")
    body = (
        f"Repair notice for {letter.property_address}: please complete "
        f"{letter.requested_remedy} by {deadline}. Please contact the tenant "
        "to confirm the completion schedule."
    )

    url = (
        "https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    )
    try:
        response = httpx.post(
            url,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            data={
                "From": settings.TWILIO_FROM_NUMBER,
                "To": recipient_phone,
                "Body": body,
            },
            timeout=15.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise DeliveryError("SMS delivery failed. Check the Twilio configuration.") from exc
