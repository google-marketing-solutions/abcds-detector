"""Notification service for new-signup alerts (Slack + email).

Sends a Slack message and an admin email whenever a new user signs up.
Both notifications include a link to the admin panel.
No-op when the corresponding env vars are not configured.
"""

import json
import logging
import os
import threading
import urllib.request
import urllib.error

import email_service

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
ADMIN_NOTIFICATION_EMAIL = os.environ.get("ADMIN_NOTIFICATION_EMAIL", "")

ADMIN_PANEL_PATH = "/admin.html"


def _admin_panel_url() -> str:
  """Return the full public URL to the admin panel."""
  return f"{PUBLIC_BASE_URL}{ADMIN_PANEL_PATH}" if PUBLIC_BASE_URL else ""


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------

def _send_signup_slack(email: str, method: str) -> bool:
  """Post a new-signup notification to the configured Slack webhook."""
  if not SLACK_WEBHOOK_URL:
    return False

  admin_url = _admin_panel_url()
  admin_link = f"  |  <{admin_url}|View Admin Panel>" if admin_url else ""

  blocks = [
      {
          "type": "header",
          "text": {"type": "plain_text", "text": ":tada: New Signup"},
      },
      {
          "type": "section",
          "text": {
              "type": "mrkdwn",
              "text": (
                  f"*Email:* {email}\n"
                  f"*Method:* {method}"
              ),
          },
      },
  ]

  if admin_url:
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":gear: <{admin_url}|*Open Admin Panel*>",
        },
    })

  payload = {
      "text": f"New signup: {email} ({method}){admin_link}",
      "blocks": blocks,
      "unfurl_links": False,
  }

  try:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
      if resp.status == 200:
        logging.info("Slack signup notification sent for %s", email)
        return True
      logging.warning("Slack webhook returned status %d", resp.status)
      return False
  except Exception as ex:
    logging.error("Slack signup notification failed: %s", ex)
    return False


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def _send_signup_email(new_user_email: str, method: str) -> bool:
  """Send a new-signup admin notification email."""
  if not ADMIN_NOTIFICATION_EMAIL:
    return False

  admin_url = _admin_panel_url()
  admin_button = ""
  if admin_url:
    admin_button = f"""\
    <a href="{admin_url}"
       style="display: inline-block; padding: 14px 32px; background: #818cf8; color: #000;
              font-weight: 600; border-radius: 8px; text-decoration: none; margin: 16px 0;">
      Open Admin Panel
    </a>"""

  subject = f"New signup: {new_user_email}"
  html = f"""\
<div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
  <h2 style="color: #e0e0e0; background: #1a1a2e; padding: 24px; border-radius: 12px 12px 0 0; margin: 0;">
    {email_service.APP_NAME}
  </h2>
  <div style="background: #16213e; padding: 24px; border-radius: 0 0 12px 12px; color: #ccc;">
    <p>A new user just signed up:</p>
    <p style="font-size: 16px; color: #fff;"><strong>{new_user_email}</strong></p>
    <p style="font-size: 13px; color: #aaa;">Sign-up method: {method}</p>
    {admin_button}
  </div>
</div>"""

  return email_service._send(ADMIN_NOTIFICATION_EMAIL, subject, html)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def notify_new_signup(email: str, method: str = "email") -> None:
  """Fire-and-forget Slack + email notifications for a new signup.

  Runs both sends in a background daemon thread so the auth response
  is never delayed.

  Args:
    email: The new user's email address.
    method: How they signed up ("google" or "email").
  """
  def _run():
    _send_signup_slack(email, method)
    _send_signup_email(email, method)

  threading.Thread(target=_run, daemon=True).start()


def notify_evaluation_started(render_id: str, user_email: str, filename: str) -> bool:
  """Send a Slack notification when a new asset upload evaluation starts.
  
  Args:
    render_id: The unique render/report ID.
    user_email: Email of the user who uploaded the asset.
    filename: Name of the uploaded file.
    
  Returns:
    True if notification was sent successfully, False otherwise.
  """
  if not SLACK_WEBHOOK_URL:
    return False

  admin_url = _admin_panel_url()

  blocks = [
      {
          "type": "header",
          "text": {"type": "plain_text", "text": ":rocket: Evaluation Started"},
      },
      {
          "type": "section",
          "text": {
              "type": "mrkdwn",
              "text": (
                  f"*User:* {user_email}\n"
                  f"*File:* {filename}\n"
                  f"*Render ID:* `{render_id}`"
              ),
          },
      },
  ]

  if admin_url:
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":gear: <{admin_url}|*Open Admin Panel*>",
        },
    })

  payload = {
      "text": f"Evaluation started for {filename} by {user_email}",
      "blocks": blocks,
      "unfurl_links": False,
  }

  try:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
      if resp.status == 200:
        logging.info("Slack evaluation notification sent for render %s", render_id)
        return True
      logging.warning("Slack webhook returned status %d", resp.status)
      return False
  except Exception as ex:
    logging.error("Slack evaluation notification failed: %s", ex)
    return False
