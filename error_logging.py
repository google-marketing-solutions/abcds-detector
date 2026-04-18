"""Slack error logging handler.

Attaches to Python's logging system and posts ERROR / CRITICAL messages
to a Slack channel via incoming webhook.

Features:
  - Rate limiting: at most 1 message per 60 seconds per unique error
  - Non-blocking: sends in a background daemon thread
  - Graceful no-op when webhook URL is not configured

Environment variables:
  SLACK_ERROR_WEBHOOK_URL  – Webhook for error alerts (falls back to SLACK_WEBHOOK_URL)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import traceback
import urllib.request
import urllib.error

# Use a dedicated webhook so errors can go to a separate channel.
# Falls back to the general webhook if not set.
SLACK_ERROR_WEBHOOK_URL = (
    os.environ.get("SLACK_ERROR_WEBHOOK_URL")
    or os.environ.get("SLACK_WEBHOOK_URL", "")
)

# Rate-limit window: suppress duplicate errors within this many seconds.
_RATE_LIMIT_SECONDS = 60


class SlackErrorHandler(logging.Handler):
  """logging.Handler that posts ERROR+ records to Slack."""

  def __init__(self, webhook_url: str = "", level: int = logging.ERROR):
    super().__init__(level)
    self.webhook_url = webhook_url or SLACK_ERROR_WEBHOOK_URL
    # Track (module, message_prefix) → last-sent timestamp for dedup.
    self._recent: dict[str, float] = {}
    self._lock = threading.Lock()

  # ------------------------------------------------------------------
  # logging.Handler interface
  # ------------------------------------------------------------------

  def emit(self, record: logging.LogRecord) -> None:
    if not self.webhook_url:
      return

    # Rate-limit: deduplicate by module + first 120 chars of message.
    dedup_key = f"{record.module}:{record.getMessage()[:120]}"
    now = time.time()

    with self._lock:
      last = self._recent.get(dedup_key, 0)
      if now - last < _RATE_LIMIT_SECONDS:
        return
      self._recent[dedup_key] = now

      # Prune stale entries to prevent unbounded growth.
      stale = [k for k, v in self._recent.items() if now - v > _RATE_LIMIT_SECONDS * 5]
      for k in stale:
        del self._recent[k]

    # Fire-and-forget in a daemon thread so logging never blocks.
    threading.Thread(
        target=self._post, args=(record,), daemon=True,
    ).start()

  # ------------------------------------------------------------------
  # Internal
  # ------------------------------------------------------------------

  def _post(self, record: logging.LogRecord) -> None:
    try:
      severity = record.levelname  # ERROR or CRITICAL
      emoji = ":rotating_light:" if severity == "CRITICAL" else ":warning:"
      module = f"{record.module}.{record.funcName}" if record.funcName else record.module
      message = record.getMessage()

      exc_text = ""
      if record.exc_info and record.exc_info[0]:
        exc_text = "\n".join(traceback.format_exception(*record.exc_info))

      blocks = [
          {
              "type": "header",
              "text": {
                  "type": "plain_text",
                  "text": f"{emoji} {severity}: {message[:150]}",
              },
          },
          {
              "type": "section",
              "text": {
                  "type": "mrkdwn",
                  "text": (
                      f"*Module:* `{module}` (line {record.lineno})\n"
                      f"*Message:* {message[:1000]}"
                  ),
              },
          },
      ]

      if exc_text:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Traceback:*\n```{exc_text[:2500]}```",
            },
        })

      payload = {
          "text": f"{severity} in {module}: {message[:200]}",
          "blocks": blocks,
          "unfurl_links": False,
      }

      body = json.dumps(payload).encode("utf-8")
      req = urllib.request.Request(
          self.webhook_url,
          data=body,
          headers={"Content-Type": "application/json"},
          method="POST",
      )
      with urllib.request.urlopen(req, timeout=10):
        pass
    except Exception:
      # Never let the handler itself raise — that would break logging.
      pass


def install(webhook_url: str = "") -> SlackErrorHandler | None:
  """Attach a SlackErrorHandler to the root logger.

  Returns the handler instance, or None if no webhook URL is available.
  """
  url = webhook_url or SLACK_ERROR_WEBHOOK_URL
  if not url:
    return None

  handler = SlackErrorHandler(webhook_url=url)
  logging.getLogger().addHandler(handler)
  return handler
