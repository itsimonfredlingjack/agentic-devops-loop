"""Email notification service for booking confirmations and cancellations."""

import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from src.bookit.config import settings

logger = logging.getLogger(__name__)


async def _send_email(to: str, subject: str, html_body: str) -> None:
    """Send an HTML email via SMTP.

    This is a low-level helper.  Callers should use the public functions
    which handle fire-and-forget semantics.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        html_body: HTML body content.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_from_email
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=True,
    )


def _confirmation_html(
    customer_name: str,
    service_name: str,
    slot_start: str,
    slot_end: str,
) -> str:
    """Build HTML body for a booking confirmation email."""
    return f"""\
<html>
<body style="font-family: sans-serif; color: #333;">
<h2>Bokningsbekräftelse</h2>
<p>Hej {customer_name},</p>
<p>Din bokning är bekräftad!</p>
<table style="border-collapse:collapse;">
<tr><td style="padding:4px 12px 4px 0;font-weight:bold;">Tjänst:</td><td>{service_name}</td></tr>
<tr><td style="padding:4px 12px 4px 0;font-weight:bold;">Tid:</td>
<td>{slot_start} – {slot_end}</td></tr>
</table>
<p style="margin-top:16px;">Välkommen!</p>
<p style="color:#888;font-size:12px;">— BookIt</p>
</body>
</html>"""


def _cancellation_html(customer_name: str, service_name: str, slot_start: str) -> str:
    """Build HTML body for a cancellation notification email."""
    return f"""\
<html>
<body style="font-family: sans-serif; color: #333;">
<h2>Avbokning bekräftad</h2>
<p>Hej {customer_name},</p>
<p>Din bokning har avbokats.</p>
<table style="border-collapse:collapse;">
<tr><td style="padding:4px 12px 4px 0;font-weight:bold;">Tjänst:</td><td>{service_name}</td></tr>
<tr><td style="padding:4px 12px 4px 0;font-weight:bold;">Tid:</td><td>{slot_start}</td></tr>
</table>
<p style="color:#888;font-size:12px;">— BookIt</p>
</body>
</html>"""


async def send_booking_confirmation(
    customer_name: str,
    customer_email: str,
    service_name: str,
    slot_start: str,
    slot_end: str,
) -> None:
    """Fire-and-forget booking confirmation email.

    Email errors are logged but never propagated — a failed email must
    never block a booking.
    """
    if not settings.email_enabled:
        logger.debug("Email disabled, skipping confirmation to %s", customer_email)
        return

    try:
        html = _confirmation_html(customer_name, service_name, slot_start, slot_end)
        await asyncio.wait_for(
            _send_email(customer_email, "Bokningsbekräftelse — BookIt", html),
            timeout=10.0,
        )
        logger.info("Confirmation email sent to %s", customer_email)
    except Exception:
        logger.exception("Failed to send confirmation email to %s", customer_email)


async def send_cancellation_notification(
    customer_name: str,
    customer_email: str,
    service_name: str,
    slot_start: str,
) -> None:
    """Fire-and-forget cancellation notification email.

    Email errors are logged but never propagated.
    """
    if not settings.email_enabled:
        logger.debug("Email disabled, skipping cancellation to %s", customer_email)
        return

    try:
        html = _cancellation_html(customer_name, service_name, slot_start)
        await asyncio.wait_for(
            _send_email(customer_email, "Avbokning bekräftad — BookIt", html),
            timeout=10.0,
        )
        logger.info("Cancellation email sent to %s", customer_email)
    except Exception:
        logger.exception("Failed to send cancellation email to %s", customer_email)
