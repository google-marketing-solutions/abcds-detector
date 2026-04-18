#!/usr/bin/env python3

"""Historical benchmarking engine.

Maintains a local JSON history of evaluation scores and computes
percentile ranks for the current evaluation relative to all
historical evaluations.

History file: data/benchmark_history.json
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from bisect import bisect_left
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "data" / "benchmark_history.json"
_CACHE_TTL = 3600  # 1 hour
_lock = threading.Lock()
_cache: dict | None = None
_cache_ts: float = 0.0


def _load_history() -> list[dict]:
  """Load benchmark history from local JSON file (cached)."""
  global _cache, _cache_ts
  now = time.time()
  if _cache is not None and (now - _cache_ts) < _CACHE_TTL:
    return _cache  # type: ignore[return-value]

  with _lock:
    # Double-check after acquiring lock
    if _cache is not None and (now - _cache_ts) < _CACHE_TTL:
      return _cache  # type: ignore[return-value]
    try:
      if HISTORY_FILE.is_file():
        data = json.loads(HISTORY_FILE.read_text())
        if isinstance(data, list):
          _cache = data
          _cache_ts = time.time()
          return data
    except Exception as ex:
      logging.error("Failed to load benchmark history: %s", ex)
    _cache = []
    _cache_ts = time.time()
    return []


def _save_history(history: list[dict]) -> None:
  """Persist benchmark history to local JSON file."""
  global _cache, _cache_ts
  try:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
      HISTORY_FILE.write_text(json.dumps(history, indent=2))
      _cache = history
      _cache_ts = time.time()
  except Exception as ex:
    logging.error("Failed to save benchmark history: %s", ex)


def _percentile_rank(sorted_values: list[float], value: float) -> float:
  """Compute the percentile rank of a value in a sorted list.

  Returns a value from 0 to 100 (e.g. 72.0 means 72nd percentile).
  """
  if not sorted_values:
    return 50.0  # No history — default to median
  pos = bisect_left(sorted_values, value)
  return round(pos / len(sorted_values) * 100, 1)


def _distribution_stats(values: list[float]) -> dict:
  """Compute p10/p25/p50/p75/p90 from a list of values."""
  if not values:
    return {}
  sv = sorted(values)
  n = len(sv)

  def _pct(p: float) -> float:
    idx = int(p / 100 * (n - 1))
    return round(sv[idx], 1)

  return {
      "p10": _pct(10),
      "p25": _pct(25),
      "p50": _pct(50),
      "p75": _pct(75),
      "p90": _pct(90),
      "mean": round(sum(sv) / n, 1),
  }


def log_evaluation(
    report_id: str,
    abcd_score: float,
    persuasion_density: float,
    performance_score: float,
    vertical: str = "",
) -> None:
  """Log an evaluation's scores to the benchmark history.

  Called after each successful evaluation to grow the history.
  """
  history = list(_load_history())  # shallow copy
  entry = {
      "report_id": report_id,
      "abcd_score": abcd_score,
      "persuasion_density": persuasion_density,
      "performance_score": performance_score,
      "vertical": vertical or "",
      "ts": time.time(),
  }
  history.append(entry)
  _save_history(history)


def compute_benchmarks(
    abcd_score: float,
    persuasion_density: float,
    performance_score: float,
    vertical: str | None = None,
) -> dict:
  """Compute percentile benchmarks for current evaluation scores.

  Args:
    abcd_score: Current ABCD score (0-100).
    persuasion_density: Current persuasion density (0-100).
    performance_score: Current performance score (0-100).
    vertical: Optional vertical filter (e.g. 'e-commerce', 'SaaS').

  Returns:
    Dict with percentile ranks and distribution context.
  """
  history = _load_history()

  # Optionally filter by vertical
  if vertical:
    vertical_lower = vertical.lower()
    filtered = [
        h for h in history
        if h.get("vertical", "").lower() == vertical_lower
    ]
    # Fall back to global if filtered set is too small
    if len(filtered) >= 10:
      history = filtered

  sample_size = len(history)

  # Extract sorted score arrays
  abcd_vals = sorted(h.get("abcd_score", 0) for h in history)
  pers_vals = sorted(h.get("persuasion_density", 0) for h in history)
  perf_vals = sorted(h.get("performance_score", 0) for h in history)

  return {
      "abcd_percentile": _percentile_rank(abcd_vals, abcd_score),
      "persuasion_percentile": _percentile_rank(pers_vals, persuasion_density),
      "performance_percentile": _percentile_rank(perf_vals, performance_score),
      "sample_size": sample_size,
      "vertical": vertical or "all",
      "distribution": {
          "abcd": _distribution_stats(abcd_vals),
          "persuasion": _distribution_stats(pers_vals),
          "performance": _distribution_stats(perf_vals),
      },
  }
