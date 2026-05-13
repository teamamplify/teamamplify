"""Email delivery — SendGrid primary, SMTP fallback, file fallback."""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def send(
    subject: str,
    html_body: str,
    text_body: str,
    from_email: str,
    to_email: str,
) -> bool:
    """
    Send the report email.

    Tries SendGrid first, then SMTP, then saves to file as last resort.
    Returns True if the email was delivered (or saved to file).
    """
    if _try_sendgrid(subject, html_body, text_body, from_email, to_email):
        return True

    if _try_smtp(subject, html_body, text_body, from_email, to_email):
        return True

    return _save_to_file(subject, html_body, text_body)


# ── SendGrid ──────────────────────────────────────────────────────────────────

def _try_sendgrid(
    subject: str,
    html_body: str,
    text_body: str,
    from_email: str,
    to_email: str,
) -> bool:
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        logger.info("SendGrid: SENDGRID_API_KEY not set — skipping")
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import Content, Email, Mail, To

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        mail = Mail(
            from_email=Email(from_email, "ARIA — Amplify Impact"),
            to_emails=To(to_email),
            subject=subject,
        )
        mail.add_content(Content("text/plain", text_body))
        mail.add_content(Content("text/html", html_body))

        resp = sg.client.mail.send.post(request_body=mail.get())
        if resp.status_code in (200, 202):
            logger.info("SendGrid: email delivered (status %d)", resp.status_code)
            return True
        else:
            logger.warning("SendGrid: unexpected status %d", resp.status_code)
            return False
    except ImportError:
        logger.warning("SendGrid: sendgrid package not installed — skipping")
        return False
    except Exception as exc:
        logger.warning("SendGrid delivery failed: %s", exc)
        return False


# ── SMTP ──────────────────────────────────────────────────────────────────────

def _try_smtp(
    subject: str,
    html_body: str,
    text_body: str,
    from_email: str,
    to_email: str,
) -> bool:
    host = os.getenv("SMTP_HOST")
    port_str = os.getenv("SMTP_PORT", "587")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not all([host, user, password]):
        logger.info("SMTP: credentials not configured — skipping")
        return False

    try:
        port = int(port_str)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ARIA — Amplify Impact <{from_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(user, password)
            server.sendmail(from_email, to_email, msg.as_string())

        logger.info("SMTP: email delivered via %s:%d", host, port)
        return True
    except Exception as exc:
        logger.warning("SMTP delivery failed: %s", exc)
        return False


# ── File fallback ─────────────────────────────────────────────────────────────

def _save_to_file(subject: str, html_body: str, text_body: str) -> bool:
    """Save report to local files when no email transport is available."""
    try:
        output_dir = Path(__file__).parent / "data" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        html_path = output_dir / f"aria_report_{timestamp}.html"
        txt_path = output_dir / f"aria_report_{timestamp}.txt"

        html_path.write_text(html_body, encoding="utf-8")
        txt_path.write_text(f"Subject: {subject}\n\n{text_body}", encoding="utf-8")

        logger.warning(
            "No email transport configured. Report saved locally:\n  %s\n  %s",
            html_path,
            txt_path,
        )
        return True
    except Exception as exc:
        logger.error("Failed to save report to file: %s", exc)
        return False
