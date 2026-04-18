"""Token system: pricing, duration detection, and credit management."""

from __future__ import annotations

import json
import logging
import math
import os
import subprocess
from typing import Optional

from sqlalchemy.orm import Session

from db import CreditTransaction, User

# Token pricing
TOKENS_PER_SECOND = 10
MAX_VIDEO_SECONDS = 60
MAX_FILE_SIZE_MB = 32
MAX_TOKENS_PER_VIDEO = TOKENS_PER_SECOND * MAX_VIDEO_SECONDS  # 600
MIN_TOKENS_TO_RENDER = 100

# Token packs (Phase 3)
TOKEN_PACKS = {
    "TOKENS_1000": {
        "usd": 10,
        "tokens": 1000,
        "stripe_price_id": os.environ.get("STRIPE_PRICE_1000", ""),
    },
    "TOKENS_3000": {
        "usd": 25,
        "tokens": 3000,
        "stripe_price_id": os.environ.get("STRIPE_PRICE_3000", ""),
    },
}

# In-progress jobs per user (for concurrent upload limit)
_active_jobs: dict[str, bool] = {}


def required_tokens(duration_seconds: float) -> int:
  """Calculate required tokens for a video of the given duration."""
  return math.ceil(duration_seconds) * TOKENS_PER_SECOND


def get_video_duration(file_path: str) -> float:
  """Extract video duration in seconds using ffprobe.

  Returns:
    Duration as a float, or -1.0 on failure.
  """
  try:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
      logging.error("ffprobe failed: %s", result.stderr)
      return -1.0

    info = json.loads(result.stdout)
    duration = float(info.get("format", {}).get("duration", -1))
    return duration
  except Exception as ex:
    logging.error("Duration detection failed: %s", ex)
    return -1.0


def validate_upload(
    file_size_bytes: int,
    duration_seconds: float,
    user: User,
) -> Optional[dict]:
  """Validate upload constraints. Returns error dict or None if valid."""
  # File size check
  file_size_mb = file_size_bytes / (1024 * 1024)
  if file_size_mb > MAX_FILE_SIZE_MB:
    return {
        "error": "file_too_large",
        "message": f"File size {file_size_mb:.1f}MB exceeds {MAX_FILE_SIZE_MB}MB limit",
        "status_code": 413,
    }

  # Duration check
  if duration_seconds > MAX_VIDEO_SECONDS:
    return {
        "error": "video_too_long",
        "message": (
            f"Video is {duration_seconds:.0f} seconds long, which exceeds the "
            f"{MAX_VIDEO_SECONDS}-second limit. Please trim your video to "
            f"{MAX_VIDEO_SECONDS} seconds or less before uploading."
        ),
        "status_code": 400,
    }

  # Credit check — user just needs MIN_TOKENS_TO_RENDER to start
  if user.credits_balance < MIN_TOKENS_TO_RENDER:
    return {
        "error": "insufficient_credits",
        "message": f"Need at least {MIN_TOKENS_TO_RENDER} credits but only have {user.credits_balance}",
        "credits_balance": user.credits_balance,
        "required": MIN_TOKENS_TO_RENDER,
        "offers": [
            {
                "pack": k,
                "usd": v["usd"],
                "tokens": v["tokens"],
            }
            for k, v in TOKEN_PACKS.items()
        ],
        "status_code": 402,
    }

  return None


def deduct_credits(
    db: Session,
    user: User,
    duration_seconds: float,
    job_id: Optional[str] = None,
) -> int:
  """Deduct credits from user and log the transaction.

  Returns the number of tokens deducted.
  """
  tokens = required_tokens(duration_seconds)

  user.credits_balance = max(0, user.credits_balance - tokens)
  tx = CreditTransaction(
      user_id=user.id,
      type="debit",
      amount=tokens,
      reason="video_evaluation",
      job_id=job_id,
  )
  db.add(tx)
  db.commit()
  db.refresh(user)

  logging.info(
      "Deducted %d credits from user %s (balance: %d)",
      tokens, user.email, user.credits_balance,
  )
  return tokens


def refund_credits(
    db: Session,
    user: User,
    tokens: int,
    job_id: Optional[str] = None,
    reason: str = "render_refund",
) -> int:
  """Refund credits to a user and log the transaction.

  Returns the number of tokens refunded.
  """
  if tokens <= 0:
    return 0

  user.credits_balance += tokens
  tx = CreditTransaction(
      user_id=user.id,
      type="grant",
      amount=tokens,
      reason=reason,
      job_id=job_id,
  )
  db.add(tx)
  db.commit()
  db.refresh(user)

  logging.info(
      "Refunded %d credits to user %s (balance: %d)",
      tokens, user.email, user.credits_balance,
  )
  return tokens


def get_actual_duration(results: dict) -> Optional[float]:
  """Extract the actual video duration in seconds from evaluation results.

  Checks video_metadata.duration_seconds first, then falls back to
  feature_timeline.video_duration_s.

  Returns:
    Duration as a float, or None if not available.
  """
  vm = results.get("video_metadata", {})
  dur = vm.get("duration_seconds")
  if dur is not None and dur > 0:
    return float(dur)

  ft = results.get("feature_timeline", {})
  dur = ft.get("video_duration_s")
  if dur is not None and dur > 0:
    return float(dur)

  return None


def acquire_job_slot(user_id: str) -> bool:
  """Try to acquire the single job slot for a user. Returns True on success."""
  if _active_jobs.get(user_id):
    return False
  _active_jobs[user_id] = True
  return True


def release_job_slot(user_id: str) -> None:
  """Release the job slot for a user."""
  _active_jobs.pop(user_id, None)


def token_model_info() -> dict:
  """Return static token model info for /auth/me response."""
  return {
      "tokens_per_second": TOKENS_PER_SECOND,
      "max_video_seconds": MAX_VIDEO_SECONDS,
      "max_tokens_per_video": MAX_TOKENS_PER_VIDEO,
  }
