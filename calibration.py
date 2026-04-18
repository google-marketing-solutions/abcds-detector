#!/usr/bin/env python3

from __future__ import annotations

"""Confidence calibration and feature reliability scoring.

Computes reliability levels for each feature based on historical
feedback data, and provides calibrated confidence scores.
"""

import datetime
import logging
from collections import defaultdict

from sqlalchemy.orm import Session

_calibration_cache: dict = {}
_cache_ts: datetime.datetime | None = None
_CACHE_TTL_HOURS = 24


def compute_feature_reliability(
    db: Session,
    feature_id: str,
) -> dict:
  """Compute reliability stats for a single feature.

  Returns:
    Dict with accuracy, sample_size, reliability_level (high/medium/low).
  """
  from db import FeatureFeedback
  try:
    rows = db.query(FeatureFeedback).filter(
        FeatureFeedback.feature_id == feature_id
    ).all()
  except Exception:
    return {"accuracy": None, "sample_size": 0, "reliability_level": "unknown"}

  if not rows:
    return {"accuracy": None, "sample_size": 0, "reliability_level": "unknown"}

  correct = sum(1 for r in rows if r.verdict == "correct")
  total = len(rows)
  accuracy = round(correct / total, 3)

  if total >= 20 and accuracy >= 0.85:
    level = "high"
  elif total >= 10 and accuracy >= 0.70:
    level = "medium"
  else:
    level = "low"

  return {
      "accuracy": accuracy,
      "sample_size": total,
      "reliability_level": level,
  }


def compute_all_reliability(db: Session) -> dict[str, dict]:
  """Compute reliability stats for all features with feedback.

  Uses a 24-hour cache to avoid repeated queries.

  Returns:
    Dict mapping feature_id -> reliability stats.
  """
  global _calibration_cache, _cache_ts

  now = datetime.datetime.utcnow()
  if _cache_ts and (now - _cache_ts).total_seconds() < _CACHE_TTL_HOURS * 3600:
    return _calibration_cache

  from db import FeatureFeedback
  try:
    rows = db.query(FeatureFeedback).all()
  except Exception as ex:
    logging.warning("Failed to load calibration data: %s", ex)
    return _calibration_cache

  by_feature: dict[str, list] = defaultdict(list)
  for r in rows:
    by_feature[r.feature_id].append(r.verdict)

  result = {}
  for fid, verdicts in by_feature.items():
    total = len(verdicts)
    correct = sum(1 for v in verdicts if v == "correct")
    accuracy = round(correct / total, 3)
    if total >= 20 and accuracy >= 0.85:
      level = "high"
    elif total >= 10 and accuracy >= 0.70:
      level = "medium"
    else:
      level = "low"
    result[fid] = {
        "accuracy": accuracy,
        "sample_size": total,
        "reliability_level": level,
    }

  _calibration_cache = result
  _cache_ts = now
  return result


def calibrate_confidence(
    raw_confidence: float,
    feature_id: str,
    calibration_data: dict[str, dict] | None = None,
) -> float:
  """Apply Platt-style scaling to raw LLM confidence.

  If calibration data is available, adjusts confidence toward the
  feature's historical accuracy. Otherwise returns raw confidence.
  """
  if not calibration_data or feature_id not in calibration_data:
    return raw_confidence

  stats = calibration_data[feature_id]
  accuracy = stats.get("accuracy")
  if accuracy is None:
    return raw_confidence

  # Simple linear blend: 70% raw + 30% historical accuracy
  calibrated = 0.7 * raw_confidence + 0.3 * accuracy
  return round(min(1.0, max(0.0, calibrated)), 3)
