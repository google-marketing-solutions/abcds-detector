"""Lightweight SMTP email service for auth flows.

Supports any SMTP provider (SendGrid, Gmail relay, SES, Mailgun, etc.)
via environment variables. Falls back to console logging if SMTP is not
configured — useful for local development.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@aicreativereview.com")

APP_NAME = "AI Creative Review"


def is_configured() -> bool:
  """Return True if SMTP credentials are set."""
  return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _send(to: str, subject: str, html_body: str) -> bool:
  """Send an email. Returns True on success, False on failure."""
  if not is_configured():
    logging.warning(
        "SMTP not configured — email not sent. Subject: %s | To: %s",
        subject, to,
    )
    return False

  msg = MIMEMultipart("alternative")
  msg["From"] = f"{APP_NAME} <{SMTP_FROM}>"
  msg["To"] = to
  msg["Subject"] = subject
  msg.attach(MIMEText(html_body, "html"))

  try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
      server.ehlo()
      server.starttls()
      server.ehlo()
      server.login(SMTP_USER, SMTP_PASSWORD)
      server.sendmail(SMTP_FROM, to, msg.as_string())
    logging.info("Email sent to %s: %s", to, subject)
    return True
  except Exception as ex:
    logging.error("Failed to send email to %s: %s", to, ex)
    return False


def send_verification_email(to: str, verify_url: str) -> bool:
  """Send an email verification link."""
  subject = f"Verify your {APP_NAME} account"
  html = f"""\
<div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
  <h2 style="color: #e0e0e0; background: #1a1a2e; padding: 24px; border-radius: 12px 12px 0 0; margin: 0;">
    {APP_NAME}
  </h2>
  <div style="background: #16213e; padding: 24px; border-radius: 0 0 12px 12px; color: #ccc;">
    <p>Thanks for signing up! Click the button below to verify your email address.</p>
    <a href="{verify_url}"
       style="display: inline-block; padding: 14px 32px; background: #818cf8; color: #000;
              font-weight: 600; border-radius: 8px; text-decoration: none; margin: 16px 0;">
      Verify Email
    </a>
    <p style="font-size: 13px; color: #888; margin-top: 24px;">
      If you didn't create this account, you can safely ignore this email.
      This link expires in 24 hours.
    </p>
  </div>
</div>"""

  sent = _send(to, subject, html)
  if not sent:
    logging.info("VERIFY EMAIL LINK (dev fallback): %s", verify_url)
  return sent


def send_password_reset_email(to: str, reset_url: str) -> bool:
  """Send a password reset link."""
  subject = f"Reset your {APP_NAME} password"
  html = f"""\
<div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
  <h2 style="color: #e0e0e0; background: #1a1a2e; padding: 24px; border-radius: 12px 12px 0 0; margin: 0;">
    {APP_NAME}
  </h2>
  <div style="background: #16213e; padding: 24px; border-radius: 0 0 12px 12px; color: #ccc;">
    <p>We received a request to reset your password. Click the button below to choose a new one.</p>
    <a href="{reset_url}"
       style="display: inline-block; padding: 14px 32px; background: #818cf8; color: #000;
              font-weight: 600; border-radius: 8px; text-decoration: none; margin: 16px 0;">
      Reset Password
    </a>
    <p style="font-size: 13px; color: #888; margin-top: 24px;">
      If you didn't request this, you can safely ignore this email.
      This link expires in 1 hour.
    </p>
  </div>
</div>"""

  sent = _send(to, subject, html)
  if not sent:
    logging.info("PASSWORD RESET LINK (dev fallback): %s", reset_url)
  return sent
