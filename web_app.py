#!/usr/bin/env python3

"""FastAPI web application for AI Creative Review"""

import hashlib
import json
import os
import queue
import re
import threading
import urllib.request
import uuid
import asyncio
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# Load .env file if present (no dependency on python-dotenv)
_env_path = Path(__file__).parent / ".env"
if _env_path.is_file():
  for _line in _env_path.read_text().splitlines():
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
      _k, _v = _line.split("=", 1)
      os.environ.setdefault(_k.strip(), _v.strip())

import benchmarking
import models
import performance_predictor
import platform_optimizer
import reference_library
import report_service
import scene_detector
import notification_service
from configuration import Configuration
from evaluation_services import video_evaluation_service
from evaluation_services import confidence_calibration_service
from helpers import generic_helpers
from sqlalchemy import text
from db import init_db, get_db, Render, User
from auth import router as auth_router, get_current_user
from billing import router as billing_router
from admin import router as admin_router
import credits as credits_mod
from sqlalchemy.orm import Session
import calibration as calibration_mod

# ---------------------------------------------------------------------------
# Environment mode
# ---------------------------------------------------------------------------
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
_is_production = ENVIRONMENT == "production"

# Enforce SESSION_SECRET in production
if _is_production:
  _sess = os.environ.get("SESSION_SECRET", "")
  if not _sess or _sess == "change-me-in-production":
    raise RuntimeError(
        "SESSION_SECRET must be set to a secure random value in production. "
        "Generate one: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    )

# ---------------------------------------------------------------------------
# Structured logging (JSON for Cloud Run → Cloud Logging)
# ---------------------------------------------------------------------------
if _is_production:
  import logging as _logging_mod

  class _CloudJsonFormatter(_logging_mod.Formatter):
    """Emit JSON lines compatible with Cloud Logging structured logs."""
    def format(self, record):
      log_entry = {
          "severity": record.levelname,
          "message": record.getMessage(),
          "module": record.module,
          "function": record.funcName,
          "line": record.lineno,
      }
      if record.exc_info and record.exc_info[0]:
        log_entry["exception"] = self.formatException(record.exc_info)
      return json.dumps(log_entry)

  _handler = _logging_mod.StreamHandler()
  _handler.setFormatter(_CloudJsonFormatter())
  _logging_mod.root.handlers = [_handler]
  _logging_mod.root.setLevel(_logging_mod.INFO)
else:
  logging.basicConfig(level=logging.INFO)

# Attach Slack error handler — sends ERROR/CRITICAL logs to Slack.
import error_logging
_slack_err = error_logging.install()
if _slack_err:
  logging.info("Slack error logging enabled")
else:
  logging.warning("SLACK_ERROR_WEBHOOK_URL not set — Slack error alerts disabled")

app = FastAPI(
    title="AI Creative Review",
    version="2.1",
    # Trust proxy headers from Cloud Run load balancer
    root_path_in_servers=False,
    # Hide docs in production
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
_ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:8080,http://localhost:3000" if not _is_production else "",
).split(",")
_ALLOWED_ORIGINS = [o.strip() for o in _ALLOWED_ORIGINS if o.strip()]

if _ALLOWED_ORIGINS:
  app.add_middleware(
      CORSMiddleware,
      allow_origins=_ALLOWED_ORIGINS,
      allow_credentials=True,
      allow_methods=["GET", "POST", "DELETE"],
      allow_headers=["*"],
  )


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if _is_production:
      response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# Rate limiting (slowapi)
# ---------------------------------------------------------------------------
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
  return JSONResponse(
      {"error": "rate_limited", "message": "Too many requests. Please slow down."},
      status_code=429,
  )


app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(admin_router)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
  """Health check for uptime monitoring and load balancer probes."""
  db_ok = True
  try:
    db = next(get_db())
    db.execute(text("SELECT 1"))
    db.close()
  except Exception:
    db_ok = False

  status = "healthy" if db_ok else "degraded"
  code = 200 if db_ok else 503
  return JSONResponse(
      {
          "status": status,
          "version": app.version,
          "database": "ok" if db_ok else "unreachable",
      },
      status_code=code,
  )

# Config defaults
PROJECT_ID = "abcds-detector-488021"
BUCKET_NAME = "abcds-detector-488021-videos"
KG_API_KEY = os.environ.get("ABCD_KG_API_KEY", "")
BQ_DATASET = "abcd_detector_ds"
BQ_TABLE = "abcd_assessments"

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")


def _send_slack_notification(results: dict, report_url: str) -> None:
  """Send Slack notification in a background daemon thread.

  No-op if SLACK_WEBHOOK_URL is not configured.
  Errors are logged but never raised.
  """
  if not SLACK_WEBHOOK_URL:
    return
  def _send():
    try:
      report_service.send_slack_notification(results, report_url, SLACK_WEBHOOK_URL)
    except Exception as ex:
      logging.error("Slack notification failed: %s", ex)
  threading.Thread(target=_send, daemon=True).start()


def _send_upload_slack_notification(
    user_email: str, filename: str, size_mb: float, gcs_uri: str,
) -> None:
  """Send Slack notification when a video is uploaded (fire-and-forget).

  No-op if SLACK_WEBHOOK_URL is not configured.
  """
  if not SLACK_WEBHOOK_URL:
    return
  def _send():
    try:
      payload = {
          "text": f"\U0001f4e4 Video uploaded by {user_email}: {filename} ({size_mb} MB)",
          "blocks": [
              {
                  "type": "section",
                  "text": {
                      "type": "mrkdwn",
                      "text": (
                          f":inbox_tray: *New Video Upload*\n"
                          f"*User:* {user_email}\n"
                          f"*File:* {filename}\n"
                          f"*Size:* {size_mb} MB\n"
                          f"*GCS:* `{gcs_uri}`"
                      ),
                  },
              },
          ],
          "unfurl_links": False,
      }
      body = json.dumps(payload).encode("utf-8")
      req = urllib.request.Request(
          SLACK_WEBHOOK_URL,
          data=body,
          headers={"Content-Type": "application/json"},
          method="POST",
      )
      with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
          logging.warning("Upload Slack webhook returned status %d", resp.status)
    except Exception as ex:
      logging.error("Upload Slack notification failed: %s", ex)
  threading.Thread(target=_send, daemon=True).start()

PRO_MODEL = "gemini-2.5-pro"
FLASH_MODEL = "gemini-2.5-flash"

# In-memory results store (keyed by report_id)
results_store: dict = {}

# Evaluation cache: video_uri + config hash → results
_eval_cache: dict = {}

# GCS prefix for persistent report storage
_REPORTS_GCS_PREFIX = "reports/"


def _save_results_to_gcs(report_id: str, data: dict) -> None:
  """Persist evaluation results as JSON to GCS (fire-and-forget)."""
  def _upload():
    try:
      client = storage.Client(project=PROJECT_ID)
      bucket = client.bucket(BUCKET_NAME)
      blob = bucket.blob(f"{_REPORTS_GCS_PREFIX}{report_id}.json")
      blob.upload_from_string(
          json.dumps(data, default=str),
          content_type="application/json",
      )
      logging.info("Report %s persisted to GCS", report_id)
    except Exception as ex:
      logging.error("Failed to persist report %s to GCS: %s", report_id, ex)
  threading.Thread(target=_upload, daemon=True).start()


def _load_results_from_gcs(report_id: str) -> Optional[dict]:
  """Load evaluation results from GCS if not in memory."""
  try:
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"{_REPORTS_GCS_PREFIX}{report_id}.json")
    if not blob.exists():
      return None
    data = json.loads(blob.download_as_text())
    # Cache in memory for subsequent requests
    results_store[report_id] = data
    return data
  except Exception as ex:
    logging.error("Failed to load report %s from GCS: %s", report_id, ex)
    return None


def _get_results(report_id: str) -> Optional[dict]:
  """Get results from memory or GCS."""
  if report_id in results_store:
    return results_store[report_id]
  return _load_results_from_gcs(report_id)


def build_config(
    use_abcd: bool = True,
    use_shorts: bool = False,
    use_ci: bool = True,
    provider_type: str = "GCS",
) -> Configuration:
  """Build a Configuration object for evaluation."""
  config = Configuration()
  config.set_parameters(
      project_id=PROJECT_ID,
      project_zone="us-central1",
      bucket_name=BUCKET_NAME,
      knowledge_graph_api_key=KG_API_KEY,
      bigquery_dataset=BQ_DATASET,
      bigquery_table=BQ_TABLE,
      assessment_file="",
      extract_brand_metadata=True,
      use_annotations=False,
      use_llms=True,
      run_long_form_abcd=use_abcd,
      run_shorts=use_shorts,
      run_creative_intelligence=use_ci,
      features_to_evaluate=[],
      creative_provider_type=provider_type,
      verbose=True,
  )
  config.set_llm_params(
      llm_name=PRO_MODEL,
      location="us-central1",
      max_output_tokens=65535,
      temperature=1,
      top_p=0.95,
  )
  return config


def upload_to_gcs(file_path: str, destination_name: str) -> str:
  """Upload a local file to GCS and return the gs:// URI."""
  client = storage.Client(project=PROJECT_ID)
  bucket = client.bucket(BUCKET_NAME)
  blob = bucket.blob(destination_name)
  blob.upload_from_filename(file_path)
  return f"gs://{BUCKET_NAME}/{destination_name}"


def _cache_key(video_uri: str, use_abcd: bool, use_shorts: bool, use_ci: bool) -> str:
  """Build a deterministic cache key for evaluation results."""
  raw = f"{video_uri}|{use_abcd}|{use_shorts}|{use_ci}"
  return hashlib.md5(raw.encode()).hexdigest()


def _bq_log_background(config, long_form, shorts, creative_intel, video_uri):
  """Fire-and-forget BQ logging in a daemon thread."""
  def _log():
    try:
      if config.bq_dataset_name:
        all_evals = long_form + shorts + creative_intel
        confidence_calibration_service.log_evaluation_confidence(
            config.project_id, config.bq_dataset_name, video_uri, all_evals,
        )
      if config.bq_table_name:
        assessment = models.VideoAssessment(
            brand_name=config.brand_name,
            video_uri=video_uri,
            long_form_abcd_evaluated_features=long_form,
            shorts_evaluated_features=shorts,
            creative_intelligence_evaluated_features=creative_intel,
            config=config,
        )
        generic_helpers.store_in_bq(config, assessment)
    except Exception as ex:
      logging.error("BQ background logging failed: %s", ex)
  t = threading.Thread(target=_log, daemon=True)
  t.start()


def run_evaluation(
    video_uri: str,
    config: Configuration,
    on_progress=None,
) -> dict:
  """Run the evaluation pipeline and return structured results.

  Optimised pipeline:
    1. Check cache
    2. Combined metadata + scene detection (single flash LLM call)
    3. ABCD + CI + video download in parallel
    4. Keyframes + volume + brand intelligence in parallel
    5. Fire-and-forget BQ logging
  """
  def progress(step, message, pct=0, partial=None):
    if on_progress:
      msg = {"step": step, "message": message, "pct": pct}
      if partial:
        msg["partial"] = partial
      on_progress(step, message, pct, partial)

  # 0) Cache check
  cache_k = _cache_key(
      video_uri, config.run_long_form_abcd, config.run_shorts,
      config.run_creative_intelligence,
  )
  if cache_k in _eval_cache:
    progress("cache", "Using cached results", 100)
    return _eval_cache[cache_k]

  # 1) Trim video for first-5-seconds features (GCS only)
  progress("trim", "Preparing video...", 5)
  if (
      config.run_long_form_abcd
      and config.creative_provider_type == models.CreativeProviderType.GCS
  ):
    generic_helpers.trim_video(config, video_uri)

  # 2) Combined metadata + scene detection (single flash LLM call)
  #    + start video download in parallel
  progress("metadata", "Extracting brand metadata & detecting scenes...", 8)
  scenes = []
  tmp_dir = ""
  video_path = ""

  with ThreadPoolExecutor(max_workers=2) as pool:
    combo_future = pool.submit(
        scene_detector.extract_metadata_and_scenes, config, video_uri,
    )
    dl_future = pool.submit(
        scene_detector.download_video_locally, config, video_uri,
    )

    try:
      metadata, scenes = combo_future.result()
      config.brand_name = metadata.get("brand_name") or config.brand_name
      config.brand_variations = metadata.get("brand_variations", [])
      config.branded_products = metadata.get("branded_products", [])
      config.branded_products_categories = metadata.get("branded_products_categories", [])
      config.branded_call_to_actions = metadata.get("branded_call_to_actions", [])
      config.extract_brand_metadata = False
      progress("metadata_done", f"Brand: {config.brand_name} | {len(scenes)} scenes", 18,
              partial={"brand_name": config.brand_name, "scene_count": len(scenes)})
    except Exception as ex:
      logging.error("Combined metadata+scenes failed: %s", ex)
      config.extract_brand_metadata = False

    try:
      tmp_dir, video_path = dl_future.result()
    except Exception as ex:
      logging.error("Video download failed: %s", ex)

  # 3) ABCD + CI evaluations in parallel (Pro model)
  progress("evaluating", "Evaluating creative features...", 20)
  long_form = []
  shorts = []
  creative_intel = []

  with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {}

    if config.run_long_form_abcd:
      futures["abcd"] = pool.submit(
          video_evaluation_service.video_evaluation_service.evaluate_features,
          config=config,
          video_uri=video_uri,
          features_category=models.VideoFeatureCategory.LONG_FORM_ABCD,
      )

    if config.run_shorts:
      futures["shorts"] = pool.submit(
          video_evaluation_service.video_evaluation_service.evaluate_features,
          config=config,
          video_uri=video_uri,
          features_category=models.VideoFeatureCategory.SHORTS,
      )

    if config.run_creative_intelligence:
      futures["ci"] = pool.submit(
          video_evaluation_service.video_evaluation_service.evaluate_features,
          config=config,
          video_uri=video_uri,
          features_category=models.VideoFeatureCategory.CREATIVE_INTELLIGENCE,
      )

    for key, future in futures.items():
      try:
        result = future.result()
        if key == "abcd":
          long_form = result
          abcd_passed = sum(1 for f in result if f.detected)
          abcd_score = round(abcd_passed / len(result) * 100) if result else 0
          progress("abcd_done", "ABCD features complete", 50,
                   partial={"abcd": {"score": abcd_score, "passed": abcd_passed, "total": len(result)}})
        elif key == "shorts":
          shorts = result
        elif key == "ci":
          creative_intel = result
          ci_detected = sum(1 for f in result if f.detected)
          ci_density = round(ci_detected / len(result) * 100) if result else 0
          progress("ci_done", "Creative intelligence complete", 60,
                   partial={"persuasion": {"density": ci_density, "detected": ci_detected, "total": len(result)}})
      except Exception as ex:
        logging.error("Evaluation task '%s' failed: %s", key, ex)

  # 4) Fire-and-forget BQ logging
  _bq_log_background(config, long_form, shorts, creative_intel, video_uri)

  # 5) Keyframes + volume + brand intelligence + video metadata in parallel
  progress("post", "Extracting keyframes & building brand profile...", 65)
  keyframes = []
  volumes = []
  brand_intel = {}
  video_metadata = {}

  creative_brief = {}
  audio_analysis = {}

  with ThreadPoolExecutor(max_workers=6) as pool:
    kf_future = pool.submit(
        scene_detector.extract_keyframes, scenes, video_path,
    )
    vol_future = pool.submit(
        scene_detector.analyze_volume_levels, scenes, video_path,
    )
    bi_future = pool.submit(
        scene_detector.generate_brand_intelligence,
        config, video_uri, config.brand_name,
    )
    vm_future = pool.submit(
        scene_detector.extract_video_metadata, video_path,
    )
    cb_future = pool.submit(
        scene_detector.generate_creative_brief,
        config, video_uri, config.brand_name,
    )
    ar_future = pool.submit(
        scene_detector.analyze_audio_richness, scenes, video_path,
    )

    try:
      keyframes = kf_future.result()
      progress("keyframes_done", "Keyframes extracted", 75)
    except Exception as ex:
      logging.error("Keyframe extraction failed: %s", ex)

    try:
      volumes = vol_future.result()
      progress("volume_done", "Volume analysis complete", 82)
    except Exception as ex:
      logging.error("Volume analysis failed: %s", ex)

    try:
      brand_intel = bi_future.result()
      progress("brand_done", "Brand intelligence complete", 90)
    except Exception as ex:
      logging.error("Brand intelligence failed: %s", ex)

    try:
      video_metadata = vm_future.result()
    except Exception as ex:
      logging.error("Video metadata extraction failed: %s", ex)

    try:
      creative_brief = cb_future.result()
      progress("brief_done", "Creative brief generated", 92)
    except Exception as ex:
      logging.error("Creative brief generation failed: %s", ex)

    try:
      audio_analysis = ar_future.result()
      progress("audio_done", "Audio richness analysis complete", 93)
    except Exception as ex:
      logging.error("Audio richness analysis failed: %s", ex)

  scene_detector.cleanup_temp_dir(tmp_dir)
  generic_helpers.remove_local_video_files()

  progress("formatting", "Generating report...", 95)
  result = format_results(config.brand_name, video_uri, long_form, shorts, creative_intel, scenes, keyframes, volumes, brand_intel, video_metadata, creative_brief, audio_analysis)

  # Store in cache
  _eval_cache[cache_k] = result
  return result


def format_feature(f: models.FeatureEvaluation) -> dict:
  """Format a single feature evaluation to JSON-serializable dict."""
  return {
      "id": f.feature.id,
      "name": f.feature.name,
      "category": f.feature.category.value if hasattr(f.feature.category, "value") else str(f.feature.category),
      "sub_category": f.feature.sub_category.value if hasattr(f.feature.sub_category, "value") else str(f.feature.sub_category),
      "detected": f.detected,
      "confidence": f.confidence_score,
      "rationale": f.rationale or "",
      "evidence": f.evidence or "",
      "strengths": f.strengths or "",
      "weaknesses": f.weaknesses or "",
      "timestamps": f.timestamps or [],
      "recommendation": f.recommendation or "",
      "recommendation_priority": f.recommendation_priority or "",
  }


def format_results(
    brand_name: str,
    video_uri: str,
    long_form: list,
    shorts: list,
    creative_intel: list,
    scenes: Optional[list] = None,
    keyframes: Optional[list] = None,
    volumes: Optional[list] = None,
    brand_intel: Optional[dict] = None,
    video_metadata: Optional[dict] = None,
    creative_brief: Optional[dict] = None,
    audio_analysis: Optional[dict] = None,
) -> dict:
  """Format all results into a JSON-serializable structure."""
  # ABCD score
  abcd_features = [format_feature(f) for f in long_form]
  abcd_total = len(long_form)
  abcd_passed = len([f for f in long_form if f.detected])
  abcd_score = round((abcd_passed / abcd_total * 100), 1) if abcd_total > 0 else 0

  if abcd_score >= 80:
    abcd_result = "Excellent"
  elif abcd_score >= 65:
    abcd_result = "Might Improve"
  else:
    abcd_result = "Needs Review"

  # Persuasion
  persuasion_features = [
      format_feature(f) for f in creative_intel
      if f.feature.sub_category == models.VideoFeatureSubCategory.PERSUASION
  ]
  persuasion_total = len(persuasion_features)
  persuasion_detected = len([f for f in persuasion_features if f["detected"]])
  persuasion_density = round((persuasion_detected / persuasion_total * 100), 1) if persuasion_total > 0 else 0

  # Structure
  structure_features = [
      format_feature(f) for f in creative_intel
      if f.feature.sub_category == models.VideoFeatureSubCategory.STRUCTURE
  ]

  # Accessibility
  accessibility_features = [
      format_feature(f) for f in creative_intel
      if f.feature.sub_category == models.VideoFeatureSubCategory.ACCESSIBILITY
  ]

  # Concept: use LLM creative brief if available, else fallback to naive synthesis
  scene_list = _format_scenes(scenes or [], keyframes or [], volumes or [])
  brief = creative_brief or {}
  if brief.get("one_line_pitch"):
    concept_data = brief
  else:
    # Fallback: naive synthesis from scenes + structure
    concept_name = ""
    concept_desc = ""
    if structure_features:
      sf = structure_features[0]
      concept_name = sf.get("evidence", "").split(",")[0].strip()
    scene_descs = [s.get("description", "") for s in scene_list if s.get("description")]
    if scene_descs:
      concept_desc = " ".join(scene_descs)
      if not concept_name:
        first = scene_descs[0]
        concept_name = (first[:80] + "...") if len(first) > 80 else first
    concept_data = {"name": concept_name, "description": concept_desc}

  # Compute accessibility score + speech rate enrichment
  accessibility_data = _compute_accessibility(accessibility_features, scene_list)

  # Compute emotional coherence from scene sentiment scores
  emotional_coherence = _compute_emotional_coherence(scene_list)

  _predictions = performance_predictor.compute_predictions(
      abcd_features, persuasion_features, structure_features,
  )
  _bi_vertical = (brand_intel or {}).get("product_service", None)

  return {
      "brand_name": brand_name,
      "video_uri": video_uri,
      "video_name": video_uri.split("/")[-1],
      "abcd": {
          "score": abcd_score,
          "result": abcd_result,
          "passed": abcd_passed,
          "total": abcd_total,
          "features": abcd_features,
      },
      "persuasion": {
          "density": persuasion_density,
          "detected": persuasion_detected,
          "total": persuasion_total,
          "features": persuasion_features,
      },
      "structure": {
          "features": structure_features,
      },
      "shorts": {
          "features": [format_feature(f) for f in shorts],
      },
      "scenes": scene_list,
      "concept": concept_data,
      "predictions": _predictions,
      "reference_ads": reference_library.find_similar_ads(
          _predictions,
          vertical=_bi_vertical,
      ),
      "brand_intelligence": brand_intel or {},
      "video_metadata": video_metadata or {},
      "emotional_coherence": emotional_coherence,
      "audio_analysis": audio_analysis or {},
      "action_plan": _build_action_plan(
          abcd_features + persuasion_features + structure_features + accessibility_features
      ),
      "feature_timeline": _build_feature_timeline(
          abcd_features + persuasion_features + structure_features + accessibility_features, scene_list
      ),
      "accessibility": accessibility_data,
      "platform_fit": platform_optimizer.compute_platform_fit(
          abcd_features, persuasion_features, structure_features,
          accessibility_features, video_metadata or {}, scene_list,
      ),
      "benchmarks": benchmarking.compute_benchmarks(
          abcd_score,
          persuasion_density,
          _predictions.get("overall_score", 0),
          vertical=_bi_vertical,
      ),
  }


def _build_action_plan(features: list[dict]) -> list[dict]:
  """Build prioritised action plan from feature recommendations.

  Returns a list of dicts sorted by priority (high > medium > low),
  each with: feature_name, detected, recommendation, priority.
  """
  prio_order = {"high": 0, "medium": 1, "low": 2, "": 3}
  items = []
  for f in features:
    rec = f.get("recommendation", "")
    if not rec:
      continue
    items.append({
        "feature_name": f.get("name", ""),
        "detected": f.get("detected", False),
        "recommendation": rec,
        "priority": f.get("recommendation_priority", "medium"),
    })
  items.sort(key=lambda x: prio_order.get(x["priority"], 3))
  return items


def _compute_emotional_coherence(scenes: list[dict]) -> dict:
  """Compute emotional coherence metrics from scene sentiment scores.

  Returns a dict with:
    score: 0-100 coherence score (100 = perfectly smooth emotional flow)
    flagged_shifts: list of scene pairs with abrupt emotional shifts (>0.5 delta)
  """
  sentiments = [s.get("sentiment_score", 0.0) for s in scenes]
  if len(sentiments) < 2:
    return {"score": 100, "flagged_shifts": []}

  deltas = []
  flagged = []
  for i in range(1, len(sentiments)):
    delta = abs(sentiments[i] - sentiments[i - 1])
    deltas.append(delta)
    if delta > 0.5:
      flagged.append({
          "from_scene": scenes[i - 1].get("scene_number", i),
          "to_scene": scenes[i].get("scene_number", i + 1),
          "delta": round(delta, 2),
          "from_emotion": scenes[i - 1].get("emotion", ""),
          "to_emotion": scenes[i].get("emotion", ""),
      })

  avg_delta = sum(deltas) / len(deltas)
  # Score: 100 when avg_delta=0, 0 when avg_delta>=1.0
  score = round(max(0, min(100, (1.0 - avg_delta) * 100)), 1)

  return {"score": score, "flagged_shifts": flagged}


def _compute_accessibility(
    features: list[dict],
    scenes: list[dict],
) -> dict:
  """Compute accessibility score and enrich with speech rate metrics.

  Returns a dict with:
    score: 0-100 accessibility score (passed / total * 100)
    passed: number of features passed
    total: number of features evaluated
    features: list of feature dicts (enriched with remediation)
    speech_rate_wpm: computed words-per-minute across all scenes
    speech_rate_flag: 'too_fast' | 'too_slow' | 'ok' | 'no_speech'
  """
  # Compute speech rate from scene transcripts + timestamps
  total_words = 0
  total_speech_duration_s = 0.0
  for sc in scenes:
    transcript = sc.get("transcript", "")
    speech_ratio = sc.get("speech_ratio", 0.0)
    if not transcript or speech_ratio <= 0:
      continue
    words = len(transcript.split())
    total_words += words
    start_s = _parse_ts_seconds(sc.get("start_time", "0:00"))
    end_s = _parse_ts_seconds(sc.get("end_time", "0:00"))
    scene_dur = max(end_s - start_s, 0.1)
    total_speech_duration_s += scene_dur * speech_ratio

  speech_rate_wpm = 0.0
  speech_rate_flag = "no_speech"
  if total_speech_duration_s > 0:
    speech_rate_wpm = round(total_words / (total_speech_duration_s / 60), 1)
    if speech_rate_wpm > 180:
      speech_rate_flag = "too_fast"
    elif speech_rate_wpm < 100:
      speech_rate_flag = "too_slow"
    else:
      speech_rate_flag = "ok"

  # Enrich speech rate feature with computed data
  remediation_map = {
      "acc_captions_present": "Add burned-in captions/subtitles to all spoken segments. Use a legible font (≥24px) with a semi-transparent background for readability.",
      "acc_text_contrast": "Increase text contrast by adding drop shadows, dark overlays behind text, or switching to white text on dark backgrounds. Ensure text stays on screen ≥2 seconds.",
      "acc_speech_rate": (
          f"Speech rate is {speech_rate_wpm:.0f} WPM. "
          + ("Slow down narration to ≤180 WPM or add pauses between key points." if speech_rate_flag == "too_fast"
             else "Consider a more natural pacing (120-170 WPM) to maintain engagement." if speech_rate_flag == "too_slow"
             else "Speech rate is within the comfortable range (100-180 WPM).")
      ),
      "acc_audio_dependence": "Add text overlays for key messages, product benefits, and CTA so the ad works with sound off. Ensure the visual narrative tells the story independently.",
  }

  enriched = []
  for f in features:
    fe = dict(f)
    fid = fe.get("id", "")
    # Override speech rate detection with computed value
    if fid == "acc_speech_rate" and speech_rate_flag != "no_speech":
      fe["detected"] = speech_rate_flag == "ok"
      fe["evidence"] = f"Computed speech rate: {speech_rate_wpm:.0f} WPM ({speech_rate_flag})"
    fe["remediation"] = remediation_map.get(fid, "")
    enriched.append(fe)

  total = len(enriched)
  passed = sum(1 for f in enriched if f.get("detected"))
  score = round(passed / total * 100, 1) if total > 0 else 100

  return {
      "score": score,
      "passed": passed,
      "total": total,
      "features": enriched,
      "speech_rate_wpm": speech_rate_wpm,
      "speech_rate_flag": speech_rate_flag,
  }


def _parse_ts_seconds(ts: str) -> float:
  """Parse a M:SS or MM:SS timestamp string to total seconds."""
  try:
    parts = ts.strip().split(":")
    if len(parts) == 2:
      return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
      return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
  except (ValueError, IndexError):
    pass
  return 0.0


def _build_feature_timeline(
    features: list[dict],
    scenes: list[dict],
) -> dict:
  """Build a feature timeline mapping features to their active time ranges.

  Returns a dict with:
    video_duration_s: estimated total duration in seconds
    scene_boundaries: list of {start_s, end_s, scene_number}
    features: list of {id, name, sub_category, detected, timestamps: [{start_s, end_s, label}]}
  """
  # Estimate total video duration from scene end times
  scene_boundaries = []
  max_end = 0.0
  for sc in scenes:
    start_s = _parse_ts_seconds(sc.get("start_time", "0:00"))
    end_s = _parse_ts_seconds(sc.get("end_time", "0:00"))
    scene_boundaries.append({
        "start_s": start_s,
        "end_s": end_s,
        "scene_number": sc.get("scene_number", 0),
    })
    if end_s > max_end:
      max_end = end_s

  timeline_features = []
  for f in features:
    ts_entries = []
    for ts in f.get("timestamps", []):
      s = _parse_ts_seconds(ts.get("start", "0:00"))
      e = _parse_ts_seconds(ts.get("end", "0:00"))
      if e > max_end:
        max_end = e
      ts_entries.append({
          "start_s": s,
          "end_s": e,
          "label": ts.get("label", ""),
      })
    timeline_features.append({
        "id": f.get("id", ""),
        "name": f.get("name", ""),
        "sub_category": f.get("sub_category", ""),
        "detected": f.get("detected", False),
        "timestamps": ts_entries,
    })

  return {
      "video_duration_s": max_end,
      "scene_boundaries": scene_boundaries,
      "features": timeline_features,
  }


def _format_scenes(
    scenes: list[dict],
    keyframes: list[str],
    volumes: Optional[list] = None,
) -> list:
  """Format scenes with keyframe and volume data for JSON response."""
  volumes = volumes or []
  formatted = []
  for i, scene in enumerate(scenes):
    entry = {
        "scene_number": scene.get("scene_number", i + 1),
        "start_time": scene.get("start_time", ""),
        "end_time": scene.get("end_time", ""),
        "description": scene.get("description", ""),
        "transcript": scene.get("transcript", ""),
        "keyframe": keyframes[i] if i < len(keyframes) else "",
        "emotion": scene.get("emotion", ""),
        "sentiment_score": scene.get("sentiment_score", 0.0),
        "music_mood": scene.get("music_mood", "none"),
        "has_music": scene.get("has_music", False),
        "speech_ratio": scene.get("speech_ratio", 0.0),
    }
    if i < len(volumes):
      entry.update(volumes[i])
    formatted.append(entry)
  return formatted


# ===== API ENDPOINTS =====

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
  """Serve the main HTML page."""
  html_path = Path(__file__).parent / "static" / "index.html"
  return HTMLResponse(content=html_path.read_text())


@app.get("/reset-password", response_class=HTMLResponse)
async def serve_reset_password():
  """Serve the password reset page."""
  html_path = Path(__file__).parent / "static" / "reset-password.html"
  return HTMLResponse(content=html_path.read_text())


@app.get("/terms", response_class=HTMLResponse)
async def serve_terms():
  """Serve the Terms of Service page."""
  html_path = Path(__file__).parent / "static" / "terms.html"
  if html_path.is_file():
    return HTMLResponse(content=html_path.read_text())
  return HTMLResponse("<h1>Terms of Service — Coming Soon</h1>", status_code=200)


@app.get("/privacy", response_class=HTMLResponse)
async def serve_privacy():
  """Serve the Privacy Policy page."""
  html_path = Path(__file__).parent / "static" / "privacy.html"
  if html_path.is_file():
    return HTMLResponse(content=html_path.read_text())
  return HTMLResponse("<h1>Privacy Policy — Coming Soon</h1>", status_code=200)


@app.get("/api/examples")
async def get_examples():
  """Serve example videos gallery data (public, no auth required)."""
  examples_path = Path(__file__).parent / "static" / "examples.json"
  if examples_path.is_file():
    data = json.loads(examples_path.read_text())
    return JSONResponse(
        data,
        headers={"Cache-Control": "public, max-age=3600"},
    )
  return JSONResponse({"examples": [], "count": 0})


@app.get("/billing", response_class=HTMLResponse)
async def serve_billing():
  """Serve the billing page (auth handled client-side)."""
  html_path = Path(__file__).parent / "static" / "billing.html"
  return HTMLResponse(content=html_path.read_text())


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin(
    current_user: User = Depends(get_current_user),
):
  """Serve the admin dashboard page (admin-only)."""
  from admin import ADMIN_EMAILS
  if current_user.email not in ADMIN_EMAILS:
    return HTMLResponse("<h1>403 — Admin access required</h1>", status_code=403)
  html_path = Path(__file__).parent / "static" / "admin.html"
  return HTMLResponse(content=html_path.read_text())


# Allowed video file extensions
_ALLOWED_VIDEO_EXTENSIONS = {".mp4"}


@app.post("/api/upload", response_model=None)
@limiter.limit("10/minute")
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
  """Upload a video file to GCS with size and credit pre-checks."""
  # File type check
  filename = (file.filename or "").lower()
  ext = Path(filename).suffix
  if ext not in _ALLOWED_VIDEO_EXTENSIONS:
    hint = f"Unsupported file format ({ext or 'unknown'}). Only .mp4 files are supported."
    if ext == ".mov":
      hint = (
          ".mov files are not supported. Please convert to .mp4 first — "
          "you can use FFmpeg: ffmpeg -i video.mov -c:v libx264 -c:a aac output.mp4"
      )
    elif ext in (".avi", ".webm", ".mkv", ".flv", ".wmv"):
      hint = f"{ext} files are not supported. Please convert to .mp4 first using FFmpeg or a free online converter."
    return JSONResponse(
        {"error": "unsupported_format", "message": hint},
        status_code=415,
    )

  # Read file content
  content = await file.read()
  file_size_bytes = len(content)
  file_size_mb = file_size_bytes / (1024 * 1024)

  # File size check
  if file_size_mb > credits_mod.MAX_FILE_SIZE_MB:
    return JSONResponse(
        {"error": "file_too_large",
         "message": f"File size {file_size_mb:.1f}MB exceeds {credits_mod.MAX_FILE_SIZE_MB}MB limit"},
        status_code=413,
    )

  # Minimum credit balance check
  if current_user.credits_balance < credits_mod.MIN_TOKENS_TO_RENDER:
    return JSONResponse(
        {"error": "insufficient_credits",
         "message": f"You have {current_user.credits_balance} credits but need at least {credits_mod.MIN_TOKENS_TO_RENDER}",
         "credits_balance": current_user.credits_balance,
         "offers": [
             {"pack": k, "usd": v["usd"], "tokens": v["tokens"]}
             for k, v in credits_mod.TOKEN_PACKS.items()
         ]},
        status_code=402,
    )

  # Sanitize filename: strip path components, allow only safe characters
  raw_name = Path(file.filename or "upload.mp4").name  # strip directory components
  safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", raw_name)
  if not safe_name or safe_name.startswith("."):
    safe_name = f"upload_{uuid.uuid4().hex[:8]}.mp4"

  tmp_dir = Path("/tmp/cr_uploads")
  tmp_dir.mkdir(exist_ok=True)
  tmp_path = tmp_dir / safe_name

  with open(tmp_path, "wb") as f:
    f.write(content)

  # Upload to GCS
  gcs_uri = upload_to_gcs(str(tmp_path), safe_name)

  # Clean up local temp file
  tmp_path.unlink(missing_ok=True)

  _send_upload_slack_notification(
      user_email=current_user.email,
      filename=safe_name,
      size_mb=round(file_size_mb, 1),
      gcs_uri=gcs_uri,
  )

  return JSONResponse({
      "status": "uploaded",
      "filename": safe_name,
      "gcs_uri": gcs_uri,
      "size_mb": round(file_size_mb, 1),
  })


@app.post("/api/evaluate")
@limiter.limit("5/minute")
async def evaluate_video(
    request: Request,
    gcs_uri: str = Form(...),
    use_abcd: bool = Form(True),
    use_shorts: bool = Form(False),
    use_ci: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Run ABCD evaluation with SSE progress streaming.

  Enforces credit balance and concurrent job limits.
  Credits are deducted AFTER a successful render, based on the
  actual video duration in seconds (10 tokens/sec).  Failed
  evaluations are not charged.
  """
  # Credit balance check — user needs at least MIN_TOKENS_TO_RENDER to start
  if current_user.credits_balance < credits_mod.MIN_TOKENS_TO_RENDER:
    return JSONResponse(
        {"error": "insufficient_credits",
         "message": f"Need at least {credits_mod.MIN_TOKENS_TO_RENDER} credits but only have {current_user.credits_balance}",
         "credits_balance": current_user.credits_balance,
         "required": credits_mod.MIN_TOKENS_TO_RENDER,
         "offers": [
             {"pack": k, "usd": v["usd"], "tokens": v["tokens"]}
             for k, v in credits_mod.TOKEN_PACKS.items()
         ]},
        status_code=402,
    )

  # Concurrent upload limit
  if not credits_mod.acquire_job_slot(current_user.id):
    return JSONResponse(
        {"error": "concurrent_limit",
         "message": "You already have a video being processed. Please wait."},
        status_code=429,
    )

  # Capture user fields now — the ORM object will be detached once the
  # DB session closes, before the SSE generator runs.
  user_id = current_user.id
  user_email = current_user.email

  # Credits are deducted AFTER the render succeeds, based on actual
  # video duration.  We only gate on MIN_TOKENS_TO_RENDER above.
  report_id = str(uuid.uuid4())[:8]

  provider_type = "YOUTUBE" if "youtube.com" in gcs_uri or "youtu.be" in gcs_uri else "GCS"
  source_type = "url" if provider_type == "YOUTUBE" else "upload"
  config = build_config(
      use_abcd=use_abcd,
      use_shorts=use_shorts,
      use_ci=use_ci,
      provider_type=provider_type,
  )

  # Persist render row (tokens_used filled in after success)
  render_row = Render(
      render_id=report_id,
      status="rendering",
      progress_pct=0,
      started_at=datetime.datetime.utcnow(),
      user_id=user_id,
      user_email=user_email,
      source_type=source_type,
      source_ref=gcs_uri.split("/")[-1] if source_type == "upload" else gcs_uri,
      prompt_text=gcs_uri,
      config_json=json.dumps({"use_abcd": use_abcd, "use_shorts": use_shorts, "use_ci": use_ci}),
      pipeline_version="Gemini → FFmpeg → Encode v3",
      model=PRO_MODEL,
      tokens_estimated=credits_mod.MAX_TOKENS_PER_VIDEO,
      tokens_used=0,
  )
  db.add(render_row)
  db.commit()

  progress_q: queue.Queue = queue.Queue()

  def on_progress(step, message, pct=0, partial=None):
    msg = {"step": step, "message": message, "pct": pct}
    if partial:
      msg["partial"] = partial
    progress_q.put(msg)

  def _run():
    return run_evaluation(gcs_uri, config, on_progress=on_progress)

  async def event_stream():
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, _run)
    results = None

    try:
      while True:
        # Drain progress messages
        try:
          while True:
            msg = progress_q.get_nowait()
            yield f"data: {json.dumps(msg)}\n\n"
        except queue.Empty:
          pass

        if task.done():
          # Drain any remaining
          while not progress_q.empty():
            msg = progress_q.get_nowait()
            yield f"data: {json.dumps(msg)}\n\n"
          try:
            results = task.result()
          except Exception as ex:
            yield f"data: {json.dumps({'step': 'error', 'message': str(ex)})}\n\n"
            return
          break

        await asyncio.sleep(0.3)

      # ---- Post-success: finalize results and send complete event ----
      try:
        actual_dur = credits_mod.get_actual_duration(results)
        if actual_dur is None:
          # Fallback: use max duration if we cannot determine actual
          actual_dur = float(credits_mod.MAX_VIDEO_SECONDS)
          logging.warning(
              "Could not determine actual duration for %s — charging max (%ds)",
              report_id, credits_mod.MAX_VIDEO_SECONDS,
          )
        tokens_used = 0
        credits_remaining = 0
        try:
          _db2 = next(get_db())
          _user = _db2.query(User).filter(User.id == user_id).first()
          if _user:
            tokens_used = credits_mod.deduct_credits(
                _db2, _user, actual_dur, job_id=report_id,
            )
            credits_remaining = _user.credits_balance
          _db2.close()
        except Exception as ex:
          logging.error("Post-success credit deduction failed: %s", ex)

        # Finalize: assign report ID, cache, notify
        results["report_id"] = report_id
        results["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
        results["tokens_used"] = tokens_used
        results["credits_remaining"] = credits_remaining
        results["duration_seconds"] = actual_dur
        results["user_email"] = user_email
        results_store[report_id] = results
        _save_results_to_gcs(report_id, results)

        # Log scores for benchmark history
        try:
          benchmarking.log_evaluation(
              report_id=report_id,
              abcd_score=results.get("abcd", {}).get("score", 0),
              persuasion_density=results.get("persuasion", {}).get("density", 0),
              performance_score=results.get("predictions", {}).get("overall_score", 0),
              vertical=results.get("brand_intelligence", {}).get("product_service", ""),
          )
        except Exception as ex:
          logging.error("Benchmark logging failed: %s", ex)

        # Build report URL before updating the render row
        base_url = PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
        report_url = f"{base_url}/report/{report_id}"
        results["report_url"] = report_url

        # Update render row → succeeded
        try:
          _db = next(get_db())
          _r = _db.query(Render).filter(Render.render_id == report_id).first()
          if _r:
            _r.status = "succeeded"
            _r.progress_pct = 100
            _r.finished_at = datetime.datetime.utcnow()
            _r.output_url = report_url
            _r.duration_seconds = actual_dur
            _r.file_size_mb = results.get("file_size_mb")
            _r.tokens_used = tokens_used
            _db.commit()
          _db.close()
        except Exception as ex:
          logging.error("Render row update failed: %s", ex)

        _send_slack_notification(results, report_url)
        slack_sent = bool(SLACK_WEBHOOK_URL)

        # Record Slack notification status
        try:
          _db = next(get_db())
          _r = _db.query(Render).filter(Render.render_id == report_id).first()
          if _r:
            _r.slack_notified = slack_sent
            _db.commit()
          _db.close()
        except Exception as ex:
          logging.error("Slack status update failed: %s", ex)

        yield f"data: {json.dumps({'step': 'complete', 'pct': 100, 'data': results}, default=str)}\n\n"
      except Exception as post_ex:
        logging.error(
            "Post-success processing failed for render %s: %s",
            report_id, post_ex, exc_info=True,
        )
        yield f"data: {json.dumps({'step': 'error', 'message': f'Evaluation succeeded but post-processing failed: {post_ex}'})}\n\n"
    finally:
      credits_mod.release_job_slot(user_id)
      # Mark render as failed if it's still in a non-terminal state
      # (e.g. client disconnect, unexpected error)
      try:
        _db_fin = next(get_db())
        _r_fin = _db_fin.query(Render).filter(Render.render_id == report_id).first()
        if _r_fin and _r_fin.status in ("queued", "rendering"):
          _r_fin.status = "failed"
          _r_fin.finished_at = datetime.datetime.utcnow()
          _r_fin.error_code = "STREAM_INTERRUPTED"
          _r_fin.error_message = "Render interrupted (client disconnect or unexpected error)"
          _db_fin.commit()
          logging.warning("Marked interrupted render %s as failed", report_id)
        _db_fin.close()
      except Exception as ex:
        logging.error("Failed to mark interrupted render %s as failed: %s", report_id, ex)

  return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/report/{report_id}", response_class=HTMLResponse)
async def serve_report(report_id: str):
  """Serve a shareable standalone HTML report."""
  data = _get_results(report_id)
  if not data:
    return HTMLResponse("<h1>Report not found</h1>", status_code=404)
  html = report_service.generate_report_html(data, report_url=f"/report/{report_id}")
  return HTMLResponse(content=html)


@app.get("/api/report/{report_id}/pdf")
async def download_pdf(report_id: str):
  """Generate and download a PDF of the evaluation report."""
  data = _get_results(report_id)
  if not data:
    return JSONResponse({"error": "Report not found"}, status_code=404)

  try:
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, report_service.generate_report_pdf, data
    )
  except Exception as ex:
    logging.error("PDF generation failed for %s: %s", report_id, ex, exc_info=True)
    return JSONResponse(
        {"error": f"PDF generation failed: {ex}"},
        status_code=500,
    )

  video_name = data.get("video_name", "report").replace(" ", "_")
  filename = f"abcd_report_{video_name}_{report_id}.pdf"
  return Response(
      content=pdf_bytes,
      media_type="application/pdf",
      headers={"Content-Disposition": f'attachment; filename="{filename}"'},
  )


@app.get("/api/keyframe/{report_id}/{scene_idx}")
async def serve_keyframe(report_id: str, scene_idx: int):
  """Serve a keyframe image for a specific scene."""
  data = _get_results(report_id)
  if not data:
    return JSONResponse({"error": "Report not found"}, status_code=404)
  scenes = data.get("scenes", [])
  if scene_idx < 0 or scene_idx >= len(scenes):
    return JSONResponse({"error": "Scene not found"}, status_code=404)
  b64 = scenes[scene_idx].get("keyframe", "")
  if not b64:
    return JSONResponse({"error": "No keyframe available"}, status_code=404)
  import base64
  return Response(
      content=base64.b64decode(b64),
      media_type="image/jpeg",
  )


@app.get("/api/video/{report_id}")
async def serve_video(report_id: str):
  """Stream the video file from GCS for embedding and download."""
  data = _get_results(report_id)
  if not data:
    return JSONResponse({"error": "Report not found"}, status_code=404)

  video_uri = data.get("video_uri", "")
  if not video_uri.startswith("gs://"):
    return JSONResponse({"error": "Video not available"}, status_code=404)

  parts = video_uri[len("gs://"):].split("/", 1)
  bucket_name = parts[0]
  blob_name = parts[1] if len(parts) > 1 else ""

  client = storage.Client(project=PROJECT_ID)
  bucket = client.bucket(bucket_name)
  blob = bucket.blob(blob_name)

  if not blob.exists():
    return JSONResponse({"error": "Video file not found"}, status_code=404)

  import io
  buffer = io.BytesIO()
  blob.download_to_file(buffer)
  buffer.seek(0)

  video_name = data.get("video_name", "video.mp4")
  return StreamingResponse(
      buffer,
      media_type="video/mp4",
      headers={
          "Content-Disposition": f'inline; filename="{video_name}"',
          "Cache-Control": "public, max-age=86400",
      },
  )


@app.get("/api/results/{report_id}")
async def get_results(report_id: str):
  """Get cached results for a report."""
  data = _get_results(report_id)
  if data:
    return JSONResponse(data)
  return JSONResponse({"error": "No results found"}, status_code=404)


@app.post("/api/report/{report_id}/feedback")
async def submit_feature_feedback(
    report_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
  """Submit human feedback on a feature detection (correct/incorrect)."""
  body = await request.json()
  feature_id = body.get("feature_id", "")
  verdict = body.get("verdict", "")
  if verdict not in ("correct", "incorrect"):
    return JSONResponse({"error": "verdict must be 'correct' or 'incorrect'"}, status_code=400)
  if not feature_id:
    return JSONResponse({"error": "feature_id required"}, status_code=400)
  from db import FeatureFeedback
  fb = FeatureFeedback(
      report_id=report_id,
      feature_id=feature_id,
      verdict=verdict,
  )
  db.add(fb)
  db.commit()
  return JSONResponse({"status": "ok"})


@app.get("/admin/api/calibration")
async def get_calibration_data(
    db: Session = Depends(get_db),
):
  """Return per-feature accuracy/reliability stats from feedback data."""
  data = calibration_mod.compute_all_reliability(db)
  return JSONResponse(data)


@app.post("/api/evaluate_file")
@limiter.limit("5/minute")
async def evaluate_file(
    request: Request,
    file: UploadFile = File(...),
    use_abcd: bool = Form(True),
    use_shorts: bool = Form(False),
    use_ci: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Upload a video file and return the complete evaluation report as JSON.

  Enforces:
  - 50MB file size limit
  - 60s video duration limit
  - Credit balance check (minimum tokens required)
  - 1 concurrent upload per user

  Credits are deducted AFTER a successful render, based on the
  actual video duration in seconds (10 tokens/sec).  Failed
  evaluations are not charged.
  """
  try:
    # Concurrent upload limit
    if not credits_mod.acquire_job_slot(current_user.id):
      return JSONResponse(
          {"error": "concurrent_limit", "message": "You already have a video being processed. Please wait."},
          status_code=429,
      )

    try:
      # Step 0: File type check
      _fname = (file.filename or "").lower()
      _ext = Path(_fname).suffix
      if _ext not in _ALLOWED_VIDEO_EXTENSIONS:
        hint = f"Unsupported file format ({_ext or 'unknown'}). Only .mp4 files are supported."
        if _ext == ".mov":
          hint = (
              ".mov files are not supported. Please convert to .mp4 first — "
              "you can use FFmpeg: ffmpeg -i video.mov -c:v libx264 -c:a aac output.mp4"
          )
        elif _ext in (".avi", ".webm", ".mkv", ".flv", ".wmv"):
          hint = f"{_ext} files are not supported. Please convert to .mp4 first using FFmpeg or a free online converter."
        return JSONResponse(
            {"error": "unsupported_format", "message": hint},
            status_code=415,
        )

      # Step 1: Save file locally
      logging.info(f"Received file: {file.filename} ({file.content_type})")
      raw_name = Path(file.filename or "upload.mp4").name
      safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", raw_name)
      if not safe_name or safe_name.startswith("."):
        safe_name = f"upload_{uuid.uuid4().hex[:8]}.mp4"

      tmp_dir = Path("/tmp/cr_uploads")
      tmp_dir.mkdir(exist_ok=True)
      tmp_path = tmp_dir / safe_name

      # Read and save file
      content = await file.read()
      file_size_bytes = len(content)
      file_size_mb = file_size_bytes / (1024 * 1024)
      logging.info(f"File size: {file_size_mb:.2f} MB")

      with open(tmp_path, "wb") as f:
        f.write(content)

      # Step 2: Validate upload constraints
      duration = credits_mod.get_video_duration(str(tmp_path))
      if duration < 0:
        tmp_path.unlink(missing_ok=True)
        return JSONResponse(
            {"error": "invalid_video", "message": "Could not determine video duration"},
            status_code=400,
        )

      validation_error = credits_mod.validate_upload(
          file_size_bytes, duration, current_user,
      )
      if validation_error:
        tmp_path.unlink(missing_ok=True)
        status_code = validation_error.pop("status_code", 400)
        return JSONResponse(validation_error, status_code=status_code)

      # Credits are deducted AFTER render success using actual duration.
      report_id = str(uuid.uuid4())[:8]

      # Persist render row (tokens_used filled in after success)
      render_row = Render(
          render_id=report_id,
          status="rendering",
          progress_pct=0,
          started_at=datetime.datetime.utcnow(),
          user_id=current_user.id,
          user_email=current_user.email,
          source_type="upload",
          source_ref=safe_name,
          config_json=json.dumps({"use_abcd": use_abcd, "use_shorts": use_shorts, "use_ci": use_ci}),
          duration_seconds=duration,
          file_size_mb=round(file_size_mb, 2),
          pipeline_version="Gemini → FFmpeg → Encode v3",
          model=PRO_MODEL,
          tokens_estimated=credits_mod.required_tokens(duration),
          tokens_used=0,
      )
      db.add(render_row)
      db.commit()

      # Step 4: Upload to GCS
      logging.info(f"Uploading {safe_name} to GCS...")
      gcs_uri = upload_to_gcs(str(tmp_path), safe_name)
      logging.info(f"Uploaded to: {gcs_uri}")

      # Clean up local file
      tmp_path.unlink(missing_ok=True)

      # Send Slack notification in background
      def _notify():
        try:
          if notification_service.notify_evaluation_started(
              report_id, current_user.email, safe_name
          ):
            render_row.slack_notified = True
            db.commit()
        except Exception as ex:
          logging.error("Failed to send evaluation started notification: %s", ex)
      threading.Thread(target=_notify, daemon=True).start()

      # Step 5: Run evaluation
      logging.info(f"Starting evaluation for {gcs_uri}...")
      config = build_config(
          use_abcd=use_abcd,
          use_shorts=use_shorts,
          use_ci=use_ci,
          provider_type="GCS",
      )

      # Run evaluation in thread pool to avoid blocking
      loop = asyncio.get_event_loop()
      results = await loop.run_in_executor(
          None,
          run_evaluation,
          gcs_uri,
          config,
          None,  # No progress callback for direct API
      )

      # Step 6: Deduct credits now that render succeeded
      actual_dur = credits_mod.get_actual_duration(results) or duration
      tokens_used = credits_mod.deduct_credits(
          db, current_user, actual_dur, job_id=report_id,
      )

      results["report_id"] = report_id
      results["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
      results["file_size_mb"] = round(file_size_mb, 2)
      results["tokens_used"] = tokens_used
      results["credits_remaining"] = current_user.credits_balance
      results["duration_seconds"] = actual_dur
      results["user_email"] = current_user.email

      # Store in cache for later retrieval
      results_store[report_id] = results
      _save_results_to_gcs(report_id, results)

      # Build report URL before updating the render row
      base_url = PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
      report_url = f"{base_url}/report/{report_id}"
      results["report_url"] = report_url

      # Update render row → succeeded
      try:
        render_row.status = "succeeded"
        render_row.progress_pct = 100
        render_row.finished_at = datetime.datetime.utcnow()
        render_row.output_url = report_url
        render_row.duration_seconds = actual_dur
        render_row.tokens_used = tokens_used
        db.commit()
      except Exception as ex:
        logging.error("Render row update failed: %s", ex)

      # Slack notification
      _send_slack_notification(results, report_url)
      try:
        render_row.slack_notified = bool(SLACK_WEBHOOK_URL)
        db.commit()
      except Exception as ex:
        logging.error("Slack status update failed: %s", ex)

      logging.info(f"Evaluation complete. Report ID: {report_id}")

      return JSONResponse(results)

    finally:
      credits_mod.release_job_slot(current_user.id)

  except Exception as ex:
    logging.error(f"Evaluation failed: {ex}", exc_info=True)
    # Mark render as failed so it doesn't stay stuck
    try:
      render_row.status = "failed"
      render_row.finished_at = datetime.datetime.utcnow()
      render_row.error_code = "EVALUATION_ERROR"
      render_row.error_message = str(ex)[:500]
      db.commit()
    except Exception as db_ex:
      logging.error("Failed to mark render as failed: %s", db_ex)
    return JSONResponse(
        {"error": f"Evaluation failed: {str(ex)}"},
        status_code=500,
    )


def compute_comparison(variants: list[dict]) -> dict:
  """Compute comparison deltas between 2+ evaluated variants.

  Returns:
    Dict with variants (summary), deltas, feature_diffs, and recommended_winner.
  """
  if len(variants) < 2:
    return {}

  summaries = []
  for i, v in enumerate(variants):
    summaries.append({
        "index": i,
        "video_name": v.get("video_name", f"Variant {i + 1}"),
        "brand_name": v.get("brand_name", ""),
        "abcd_score": v.get("abcd", {}).get("score", 0),
        "persuasion_density": v.get("persuasion", {}).get("density", 0),
        "performance_score": v.get("predictions", {}).get("overall_score", 0),
        "accessibility_score": v.get("accessibility", {}).get("score", 0),
        "emotional_coherence": v.get("emotional_coherence", {}).get("score", 0) if isinstance(v.get("emotional_coherence"), dict) else 0,
        "report_id": v.get("report_id", ""),
    })

  # Score deltas (variant[i] vs variant[0])
  base = summaries[0]
  deltas = []
  for s in summaries[1:]:
    deltas.append({
        "vs": f"{s['video_name']} vs {base['video_name']}",
        "abcd_delta": round(s["abcd_score"] - base["abcd_score"], 1),
        "persuasion_delta": round(s["persuasion_density"] - base["persuasion_density"], 1),
        "performance_delta": round(s["performance_score"] - base["performance_score"], 1),
    })

  # Feature-level diffs (features where variants disagree)
  all_feature_ids = set()
  variant_features = []
  for v in variants:
    features_map = {}
    for section_key in ("abcd", "persuasion"):
      for f in v.get(section_key, {}).get("features", []):
        fid = f.get("id", "")
        all_feature_ids.add(fid)
        features_map[fid] = {"name": f.get("name", ""), "detected": f.get("detected", False)}
    for f in v.get("accessibility", {}).get("features", []):
      fid = f.get("id", "")
      all_feature_ids.add(fid)
      features_map[fid] = {"name": f.get("name", ""), "detected": f.get("detected", False)}
    variant_features.append(features_map)

  feature_diffs = []
  for fid in sorted(all_feature_ids):
    results = [vf.get(fid, {}).get("detected", None) for vf in variant_features]
    # Only include if at least one variant has the feature and they disagree
    if any(r is not None for r in results) and len(set(r for r in results if r is not None)) > 1:
      name = ""
      for vf in variant_features:
        if fid in vf:
          name = vf[fid].get("name", fid)
          break
      feature_diffs.append({
          "feature_id": fid,
          "feature_name": name,
          "results": [r if r is not None else "N/A" for r in results],
      })

  # Recommended winner: highest weighted composite score
  def _composite(s):
    return s["performance_score"] * 0.4 + s["abcd_score"] * 0.3 + s["persuasion_density"] * 0.15 + s["accessibility_score"] * 0.15

  scored = [(i, _composite(s)) for i, s in enumerate(summaries)]
  scored.sort(key=lambda x: x[1], reverse=True)
  winner_idx = scored[0][0]
  winner = summaries[winner_idx]
  runner_up = summaries[scored[1][0]] if len(scored) > 1 else None

  justification = (
      f"{winner['video_name']} leads with a performance score of {winner['performance_score']}, "
      f"ABCD {winner['abcd_score']}%, and accessibility {winner['accessibility_score']}%."
  )
  if runner_up:
    perf_delta = winner["performance_score"] - runner_up["performance_score"]
    justification += f" Outperforms {runner_up['video_name']} by {perf_delta:+.0f} on performance."

  return {
      "variant_count": len(variants),
      "variants": summaries,
      "deltas": deltas,
      "feature_diffs": feature_diffs,
      "recommended_winner": {
          "index": winner_idx,
          "video_name": winner["video_name"],
          "justification": justification,
      },
  }


@app.post("/api/evaluate_compare")
async def evaluate_compare(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Evaluate 2+ videos in parallel and return a comparison report.

  Accepts JSON body: {"video_uris": ["gs://...", "https://youtube..."], "use_abcd": true, "use_ci": true}
  """
  body = await request.json()
  video_uris = body.get("video_uris", [])
  if not isinstance(video_uris, list) or len(video_uris) < 2:
    return JSONResponse({"error": "Provide at least 2 video_uris"}, status_code=400)
  if len(video_uris) > 5:
    return JSONResponse({"error": "Maximum 5 variants supported"}, status_code=400)

  use_abcd = body.get("use_abcd", True)
  use_shorts = body.get("use_shorts", False)
  use_ci = body.get("use_ci", True)

  # Credit check: need enough for all variants
  total_cost = credits_mod.MIN_TOKENS_TO_RENDER * len(video_uris)
  if current_user.credits_balance < total_cost:
    return JSONResponse(
        {"error": "insufficient_credits",
         "message": f"Comparing {len(video_uris)} videos requires ~{total_cost} credits"},
        status_code=402,
    )

  # Evaluate all variants in parallel
  loop = asyncio.get_event_loop()
  variant_results = []

  user_id = current_user.id

  async def _eval_one(uri: str) -> dict:
    provider_type = "YOUTUBE" if "youtube.com" in uri or "youtu.be" in uri else "GCS"
    config = build_config(
        use_abcd=use_abcd, use_shorts=use_shorts, use_ci=use_ci,
        provider_type=provider_type,
    )
    result = await loop.run_in_executor(None, run_evaluation, uri, config, None)
    rid = str(uuid.uuid4())[:8]
    result["report_id"] = rid
    result["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")

    # Deduct credits based on actual duration (only for successful renders)
    actual_dur = credits_mod.get_actual_duration(result)
    tokens_used = 0
    if actual_dur is not None and actual_dur > 0:
      try:
        _cdb = next(get_db())
        _cuser = _cdb.query(User).filter(User.id == user_id).first()
        if _cuser:
          tokens_used = credits_mod.deduct_credits(
              _cdb, _cuser, actual_dur, job_id=rid,
          )
          result["credits_remaining"] = _cuser.credits_balance
        _cdb.close()
      except Exception as ex:
        logging.error("Compare credit deduction failed for %s: %s", rid, ex)
    result["tokens_used"] = tokens_used
    result["duration_seconds"] = actual_dur

    results_store[rid] = result
    _save_results_to_gcs(rid, result)

    base_url = PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
    report_url = f"{base_url}/report/{rid}"
    result["report_url"] = report_url
    _send_slack_notification(result, report_url)
    return result

  import asyncio as _aio
  tasks = [_eval_one(uri) for uri in video_uris]
  variant_results = await _aio.gather(*tasks, return_exceptions=True)

  # Filter out failures — no credits deducted for failed evaluations
  successful = []
  errors = []
  for i, r in enumerate(variant_results):
    if isinstance(r, Exception):
      errors.append({"index": i, "uri": video_uris[i], "error": str(r)})
    else:
      successful.append(r)

  if len(successful) < 2:
    return JSONResponse(
        {"error": "comparison_failed", "message": "Need at least 2 successful evaluations", "errors": errors},
        status_code=500,
    )

  comparison = compute_comparison(successful)

  comparison_id = str(uuid.uuid4())[:8]
  comparison_result = {
      "comparison_id": comparison_id,
      "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
      "comparison": comparison,
      "variants": successful,
      "errors": errors,
  }
  results_store[f"cmp_{comparison_id}"] = comparison_result

  return JSONResponse(comparison_result)


@app.get("/report/compare/{comparison_id}", response_class=HTMLResponse)
async def serve_comparison_report(comparison_id: str):
  """Serve a comparison report for 2+ evaluated variants."""
  data = results_store.get(f"cmp_{comparison_id}")
  if not data:
    return HTMLResponse("<h1>Comparison report not found</h1>", status_code=404)
  html = report_service.generate_comparison_report_html(data)
  return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Stale render reaper — marks renders stuck in non-terminal states
# ---------------------------------------------------------------------------
STALE_RENDER_THRESHOLD_SECONDS = 600  # 10 minutes


async def _reap_stale_renders():
  """Periodically mark renders stuck in 'queued'/'rendering' as failed."""
  while True:
    await asyncio.sleep(120)  # check every 2 minutes
    try:
      cutoff = datetime.datetime.utcnow() - datetime.timedelta(
          seconds=STALE_RENDER_THRESHOLD_SECONDS,
      )
      db = next(get_db())
      stale = (
          db.query(Render)
          .filter(
              Render.status.in_(["queued", "rendering"]),
              Render.started_at < cutoff,
          )
          .all()
      )
      for r in stale:
        r.status = "failed"
        r.finished_at = datetime.datetime.utcnow()
        r.error_code = "STALE_TIMEOUT"
        r.error_message = (
            f"Render was stuck in '{r.status}' for over "
            f"{STALE_RENDER_THRESHOLD_SECONDS}s and was automatically failed"
        )
        logging.warning("Reaped stale render %s (started %s)", r.render_id, r.started_at)
      if stale:
        db.commit()
        logging.info("Reaped %d stale render(s)", len(stale))
      db.close()
    except Exception as ex:
      logging.error("Stale render reaper error: %s", ex)


@app.on_event("startup")
async def _prewarm():
  """Init DB, run auth migrations, and pre-warm Gemini connection on startup."""
  init_db()
  logging.info("Database initialized")

  # Start background reaper for stuck renders
  asyncio.create_task(_reap_stale_renders())

  # Ensure auth columns exist (idempotent)
  try:
    import migrate_auth
    migrate_auth.migrate()
    logging.info("Auth migration check complete")
  except Exception as ex:
    logging.warning("Auth migration failed (non-fatal): %s", ex)
  if SLACK_WEBHOOK_URL:
    logging.info("Slack notifications enabled (webhook configured)")
  else:
    logging.warning("SLACK_WEBHOOK_URL not set — Slack notifications disabled")

  def _warm():
    try:
      from google import genai
      client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
      # Tiny request to establish connection pool
      client.models.generate_content(
          model=FLASH_MODEL,
          contents="ping",
          config={"max_output_tokens": 1},
      )
      logging.info("Gemini connection pre-warmed")
    except Exception as ex:
      logging.warning("Pre-warm failed (non-fatal): %s", ex)
  threading.Thread(target=_warm, daemon=True).start()


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8080)
