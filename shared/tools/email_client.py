"""
Gmail SMTP Email Client

Provides send_email() for the onboarding pipeline.
All configuration is read from environment variables (EMAIL_FROM, GMAIL_APP_PASSWORD).
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from shared.logger import logger


class EmailClientError(Exception):
    """Raised when an email fails to send."""


class EmailBounceError(EmailClientError):
    """Raised specifically when the email bounces (4xx recipient error)."""


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    *,
    from_email: str | None = None,
) -> dict:
    """
    Send an email via Gmail SMTP.

    Parameters
    ----------
    to_email : str
        Recipient address.
    subject  : str
        Email subject line.
    body_html : str
        HTML body content.
    from_email : str | None
        Sender address. Defaults to EMAIL_FROM env var.

    Returns
    -------
    dict
        ``{"status_code": int, "message_id": str}``

    Raises
    ------
    EmailBounceError
        If the SMTP server refuses the recipient.
    EmailClientError
        For any other send failure.
    """
    sender = from_email or os.environ["EMAIL_FROM"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    
    # Set the content directly as HTML
    msg.set_content(body_html, subtype='html')

    try:
        # Use SSL on port 465 for Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.send_message(msg)

        logger.info(
            "Email sent → %s  (status 200, subject: %s)",
            to_email,
            subject,
        )

        return {"status_code": 200, "message_id": "smtp-sent"}

    except smtplib.SMTPRecipientsRefused as exc:
        raise EmailBounceError(f"Email to {to_email} refused: {exc}")
    except smtplib.SMTPException as exc:
        raise EmailClientError(f"SMTP error {exc} for {to_email}.")
    except Exception as exc:
        logger.error("Email send failed → %s: %s", to_email, exc)
        raise EmailClientError(str(exc)) from exc
