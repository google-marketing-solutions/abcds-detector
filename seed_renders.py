#!/usr/bin/env python3
"""Seed the database with sample Render rows for development/demo."""

import datetime
import json
import random
import uuid

from db import Render, User, init_db, SessionLocal

STATUSES = ["queued", "rendering", "succeeded", "failed", "canceled"]
SOURCE_TYPES = ["upload", "url", "api"]
PIPELINES = [
    "Gemini → FFmpeg → Encode v3",
    "Gemini → FFmpeg → Encode v2",
    "Flash → Transcode → Deliver",
    "Pro → Compose → Encode v3",
]
MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
FILENAMES = [
    "brand_hero_30s.mp4",
    "product_launch_15s.mp4",
    "testimonial_cutdown.mp4",
    "holiday_promo_60s.mp4",
    "awareness_bumper_6s.mp4",
    "retarget_demo_20s.mp4",
    "social_story_9x16.mp4",
    "explainer_45s.mp4",
    "brand_anthem_30s.mp4",
    "sale_event_15s.mp4",
]
ERROR_CODES = [None, None, None, None, "TIMEOUT", "ENCODE_FAIL", "OOM", "PIPELINE_CRASH"]
BRANDS = ["Nike", "Coca-Cola", "Apple", "Google", "Samsung", "Adidas", "Pepsi", "Tesla"]


def _rand_dt(days_back: int = 30) -> datetime.datetime:
  """Return a random datetime within the last N days."""
  now = datetime.datetime.utcnow()
  offset = random.randint(0, days_back * 86400)
  return now - datetime.timedelta(seconds=offset)


def seed(count: int = 20):
  """Insert sample renders into the database."""
  init_db()
  db = SessionLocal()

  # Ensure at least one demo user exists
  demo_users = []
  for i, email in enumerate([
      "alice@example.com",
      "bob@acme.co",
      "carol@brand.io",
  ]):
    user = db.query(User).filter(User.email == email).first()
    if not user:
      user = User(
          id=str(uuid.uuid4()),
          google_sub=f"demo_sub_{i}",
          email=email,
          is_admin=(i == 0),  # first user is admin
          credits_balance=random.randint(200, 5000),
      )
      db.add(user)
      db.flush()
    demo_users.append(user)

  for n in range(count):
    user = random.choice(demo_users)
    status = random.choices(
        STATUSES, weights=[5, 5, 60, 20, 10], k=1,
    )[0]
    created = _rand_dt()
    started = created + datetime.timedelta(seconds=random.randint(0, 5))
    duration = round(random.uniform(6, 60), 1)
    finished = None
    error_code = None
    error_message = None

    if status in ("succeeded", "failed", "canceled"):
      finished = started + datetime.timedelta(
          seconds=random.randint(10, 120),
      )
    if status == "failed":
      error_code = random.choice([c for c in ERROR_CODES if c])
      error_message = f"Pipeline error: {error_code}"

    filename = random.choice(FILENAMES)
    source_type = random.choice(SOURCE_TYPES)
    source_ref = filename if source_type == "upload" else f"https://storage.example.com/{filename}"

    tokens_est = int(duration * 10)
    tokens_used = tokens_est if status == "succeeded" else 0

    render = Render(
        render_id=str(uuid.uuid4())[:8],
        status=status,
        progress_pct=100 if status == "succeeded" else (
            random.randint(10, 90) if status == "rendering" else 0
        ),
        created_at=created,
        started_at=started,
        finished_at=finished,
        user_id=user.id,
        user_email=user.email,
        user_name=user.email.split("@")[0].title(),
        source_type=source_type,
        source_ref=source_ref,
        input_assets=json.dumps([{
            "type": "video",
            "size": round(random.uniform(2, 48), 1),
            "url": f"gs://demo-bucket/{filename}",
        }]),
        prompt_text=f"Create a {random.choice(BRANDS)} ad with {random.choice(['upbeat', 'cinematic', 'minimal', 'bold'])} style",
        brand_guide=random.choice(BRANDS),
        config_json=json.dumps({
            "aspect_ratio": random.choice(["16:9", "9:16", "1:1"]),
            "fps": random.choice([24, 30, 60]),
            "bitrate": random.choice(["8M", "12M", "20M"]),
            "output_format": "mp4",
        }),
        output_url=f"gs://demo-bucket/output/{filename}" if status == "succeeded" else None,
        thumbnail_url=f"/api/keyframe/demo/{n}" if status == "succeeded" else None,
        duration_seconds=duration,
        file_size_mb=round(random.uniform(2, 48), 1),
        pipeline_version=random.choice(PIPELINES),
        model=random.choice(MODELS),
        tokens_estimated=tokens_est,
        tokens_used=tokens_used,
        error_code=error_code,
        error_message=error_message,
        logs_url=f"/admin/api/renders/{n}/logs",
        webhook_failures_count=random.choice([0, 0, 0, 0, 1, 2, 3]),
    )
    db.add(render)

  db.commit()
  db.close()
  print(f"Seeded {count} renders with {len(demo_users)} demo users.")


if __name__ == "__main__":
  seed()
