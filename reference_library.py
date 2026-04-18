#!/usr/bin/env python3

from __future__ import annotations

"""Reference library of high-scoring ads with similarity matching.

Loads a curated library of reference ads and finds the most similar
ones to a given evaluation based on cosine similarity of normalized
performance section scores.
"""

import json
import logging
import math
import os

_LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "data", "reference_library.json")

_library_cache: list[dict] | None = None


def load_library() -> list[dict]:
  """Load and cache the reference ad library from JSON.

  Returns:
    List of reference ad dicts.
  """
  global _library_cache
  if _library_cache is not None:
    return _library_cache

  try:
    with open(_LIBRARY_PATH, "r") as f:
      _library_cache = json.load(f)
    logging.info("Reference library loaded: %d ads", len(_library_cache))
  except Exception as ex:
    logging.warning("Failed to load reference library: %s", ex)
    _library_cache = []
  return _library_cache


def _cosine_similarity(a: list[float], b: list[float]) -> float:
  """Compute cosine similarity between two vectors."""
  if len(a) != len(b) or not a:
    return 0.0
  dot = sum(x * y for x, y in zip(a, b))
  mag_a = math.sqrt(sum(x * x for x in a))
  mag_b = math.sqrt(sum(x * x for x in b))
  if mag_a == 0 or mag_b == 0:
    return 0.0
  return dot / (mag_a * mag_b)


def _build_feature_vector(predictions: dict) -> list[float]:
  """Build a 9-element normalized feature vector from predictions.

  Maps the 9 section scores from performance_predictor to a [0-1] vector.
  """
  norm = predictions.get("normalized", {})
  keys = [
      "hook_attention", "brand_visibility", "social_proof_trust",
      "product_clarity_benefits", "funnel_alignment", "cta",
      "creative_diversity_readiness", "measurement_compatibility",
      "data_audience_leverage",
  ]
  return [norm.get(k, 0.0) for k in keys]


def find_similar_ads(
    predictions: dict,
    vertical: str | None = None,
    top_k: int = 3,
) -> list[dict]:
  """Find the top_k most similar high-scoring reference ads.

  Args:
    predictions: The predictions dict from performance_predictor.compute_predictions().
    vertical: Optional vertical filter (e.g. "e-commerce", "SaaS", "CPG").
    top_k: Number of results to return.
  Returns:
    List of reference ad dicts with added "similarity" score.
  """
  library = load_library()
  if not library:
    return []

  current_vec = _build_feature_vector(predictions)
  if not any(v > 0 for v in current_vec):
    return []

  candidates = library
  if vertical:
    v_lower = vertical.lower()
    filtered = [ad for ad in library if ad.get("vertical", "").lower() == v_lower]
    if filtered:
      candidates = filtered

  scored = []
  for ad in candidates:
    ref_vec = ad.get("feature_vector", [])
    if not ref_vec or len(ref_vec) != len(current_vec):
      continue
    sim = _cosine_similarity(current_vec, ref_vec)
    scored.append({**ad, "similarity": round(sim, 3)})

  scored.sort(key=lambda x: x["similarity"], reverse=True)
  return scored[:top_k]
