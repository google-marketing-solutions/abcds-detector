#!/usr/bin/env python3

"""Deterministic platform fit scoring engine.

Computes fit scores (0-100) and optimization tips for:
  YouTube (pre-roll), Meta Feed, Meta Reels, TikTok, Connected TV.

Same inputs → same outputs. No LLM required.
"""

from __future__ import annotations


# --- Aspect ratio helpers ---

def _parse_aspect_ratio(ar_str: str) -> float | None:
  """Parse an aspect ratio string like '16:9' or '1.78' to a float."""
  if not ar_str:
    return None
  if ":" in ar_str:
    try:
      w, h = ar_str.split(":")
      return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
      return None
  try:
    return float(ar_str)
  except ValueError:
    return None


def _parse_duration_seconds(dur_str: str) -> float:
  """Parse a duration string like '0:30', '1:05', or '30s' to seconds."""
  if not dur_str:
    return 0.0
  dur_str = dur_str.strip().lower().rstrip("s")
  try:
    if ":" in dur_str:
      parts = dur_str.split(":")
      if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
      if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(dur_str)
  except (ValueError, IndexError):
    return 0.0


def _has_feature_keyword(
    features: list[dict],
    keywords: list[str],
    field: str = "name",
    detected_only: bool = True,
) -> bool:
  """True if any feature's field contains one of the keywords."""
  for f in features:
    if detected_only and not f.get("detected"):
      continue
    text = (f.get(field, "") or "").lower()
    if any(k in text for k in keywords):
      return True
  return False


# --- Platform scoring rules ---

def _score_youtube(
    duration_s: float,
    ar: float | None,
    scene_count: int,
    hook_fast: bool,
    has_cta: bool,
    has_brand_early: bool,
    has_captions: bool,
    **_kwargs,
) -> dict:
  """YouTube pre-roll / in-stream scoring."""
  score = 70  # baseline
  tips = []

  # Duration: ideal 15-60s for pre-roll
  if duration_s < 6:
    score -= 15
    tips.append("Video is very short for YouTube pre-roll. Aim for 15-60 seconds.")
  elif duration_s < 15:
    score -= 5
    tips.append("Consider extending to at least 15 seconds for full pre-roll impact.")
  elif duration_s > 180:
    score -= 10
    tips.append("Long-form (>3 min) may lose viewers. Consider a :30-:60 cutdown.")

  # Aspect ratio: 16:9 ideal
  if ar is not None:
    if 1.6 <= ar <= 1.9:
      score += 10
    elif 0.9 <= ar <= 1.1:
      score += 0
      tips.append("Square (1:1) works but 16:9 is optimal for YouTube.")
    elif ar < 0.7:
      score -= 5
      tips.append("Vertical video loses impact on YouTube. Use 16:9 landscape.")

  # Hook within 5 seconds
  if hook_fast:
    score += 5
  else:
    tips.append("Add a strong hook in the first 5 seconds — viewers can skip after 5s.")

  # CTA
  if has_cta:
    score += 5
  else:
    tips.append("Include a clear CTA (end card, overlay, or verbal) to drive action.")

  # Brand visibility early
  if has_brand_early:
    score += 5
  else:
    tips.append("Show your brand/logo in the first 5 seconds for skippable ads.")

  # Captions (nice to have)
  if has_captions:
    score += 5

  return {
      "score": max(0, min(100, score)),
      "tips": tips[:3],
  }


def _score_meta_feed(
    duration_s: float,
    ar: float | None,
    hook_fast: bool,
    has_cta: bool,
    has_captions: bool,
    audio_independent: bool,
    **_kwargs,
) -> dict:
  """Meta (Facebook/Instagram) Feed scoring."""
  score = 65
  tips = []

  # Duration: ideal 15-30s for Feed
  if duration_s > 60:
    score -= 10
    tips.append("Trim to 15-30 seconds for Feed. Shorter videos get higher completion rates.")
  elif duration_s > 30:
    score -= 5
    tips.append("Consider a :15-:30 edit for better Feed performance.")

  # Aspect ratio: 1:1 or 4:5 preferred
  if ar is not None:
    if 0.75 <= ar <= 1.1:
      score += 10  # Square or 4:5
    elif ar < 0.65:
      score += 5  # 9:16 acceptable
    elif ar > 1.5:
      score -= 10
      tips.append("Use square (1:1) or 4:5 vertical for Feed. Landscape loses real estate.")

  # Sound-off: critical for Feed
  if audio_independent:
    score += 10
  else:
    score -= 10
    tips.append("Most Feed viewers watch with sound off. Add text overlays and ensure the message works visually.")

  # Captions
  if has_captions:
    score += 10
  else:
    score -= 5
    tips.append("Add captions — Feed autoplay is muted. Captions increase watch time by 12%.")

  # Hook
  if hook_fast:
    score += 5
  else:
    tips.append("Hook viewers in the first 3 seconds — Feed scrolling is fast.")

  # CTA
  if has_cta:
    score += 5

  return {
      "score": max(0, min(100, score)),
      "tips": tips[:3],
  }


def _score_meta_reels(
    duration_s: float,
    ar: float | None,
    hook_fast: bool,
    has_captions: bool,
    audio_independent: bool,
    pacing_fast: bool,
    structure_archetype: str,
    **_kwargs,
) -> dict:
  """Meta Reels / Instagram Reels scoring."""
  score = 60
  tips = []

  # Duration: ideal 15-30s
  if duration_s > 60:
    score -= 15
    tips.append("Reels perform best at 15-30 seconds. Trim aggressively.")
  elif duration_s > 30:
    score -= 5

  # Aspect ratio: 9:16 required
  if ar is not None:
    if ar < 0.65:
      score += 15  # 9:16
    elif 0.75 <= ar <= 1.1:
      score += 0
      tips.append("Reels are 9:16 vertical. Crop to vertical for maximum screen coverage.")
    elif ar > 1.3:
      score -= 15
      tips.append("Landscape video is heavily penalized on Reels. Re-crop to 9:16.")

  # Pacing
  if pacing_fast:
    score += 5
  else:
    tips.append("Increase pacing — Reels reward quick cuts and dynamic movement.")

  # UGC / authenticity
  if structure_archetype and "ugc" in structure_archetype.lower():
    score += 10
  elif structure_archetype and "demo" in structure_archetype.lower():
    score += 5

  # Captions
  if has_captions:
    score += 5

  # Hook
  if hook_fast:
    score += 5
  else:
    tips.append("Open with motion, text, or a face in the first 1-2 seconds.")

  # Sound-off resilience
  if audio_independent:
    score += 5

  return {
      "score": max(0, min(100, score)),
      "tips": tips[:3],
  }


def _score_tiktok(
    duration_s: float,
    ar: float | None,
    hook_fast: bool,
    has_captions: bool,
    pacing_fast: bool,
    structure_archetype: str,
    **_kwargs,
) -> dict:
  """TikTok scoring."""
  score = 55
  tips = []

  # Duration: ideal 9-15s (TikTok sweet spot), acceptable up to 30s
  if duration_s <= 15:
    score += 10
  elif duration_s <= 30:
    score += 5
  elif duration_s > 60:
    score -= 15
    tips.append("TikTok ads perform best at 9-15 seconds. Cut to a :15 version.")
  else:
    score -= 5
    tips.append("Trim to under 30 seconds for better TikTok completion rates.")

  # Aspect ratio: 9:16 required
  if ar is not None:
    if ar < 0.65:
      score += 15
    elif 0.75 <= ar <= 1.1:
      tips.append("Re-crop to 9:16 vertical. TikTok is a vertical-first platform.")
    elif ar > 1.3:
      score -= 15
      tips.append("Landscape format does not work on TikTok. Convert to 9:16.")

  # Hook: TikTok = 1 second to capture
  if hook_fast:
    score += 10
  else:
    score -= 5
    tips.append("Open with a hook in the first 1 second — text, question, or unexpected visual.")

  # Pacing
  if pacing_fast:
    score += 5

  # UGC authenticity
  if structure_archetype and "ugc" in structure_archetype.lower():
    score += 10
  elif structure_archetype:
    arch_lower = structure_archetype.lower()
    if any(k in arch_lower for k in ["demo", "problem-solution", "before-after"]):
      score += 5

  # Captions
  if has_captions:
    score += 5

  return {
      "score": max(0, min(100, score)),
      "tips": tips[:3],
  }


def _score_ctv(
    duration_s: float,
    ar: float | None,
    has_brand_early: bool,
    has_cta: bool,
    pacing_fast: bool,
    text_readable: bool,
    **_kwargs,
) -> dict:
  """Connected TV (CTV) / OTT scoring."""
  score = 70
  tips = []

  # Duration: :15 or :30 standard for CTV
  if 13 <= duration_s <= 32:
    score += 10
  elif duration_s < 10:
    score -= 10
    tips.append("CTV slots are typically :15 or :30. Extend your creative.")
  elif duration_s > 60:
    score -= 10
    tips.append("CTV ads should be :15 or :30. Create a broadcast-length cutdown.")

  # Aspect ratio: 16:9 mandatory
  if ar is not None:
    if 1.6 <= ar <= 1.9:
      score += 10
    else:
      score -= 15
      tips.append("CTV requires 16:9 landscape. Re-crop from vertical/square.")

  # Brand visibility
  if has_brand_early:
    score += 5
  else:
    tips.append("CTV viewers can't skip — but brand recall still requires early logo placement.")

  # CTA: on CTV, must be scannable (QR) or memorable (URL)
  if has_cta:
    score += 5

  # Pacing: CTV should not be too fast (lean-back viewing)
  if pacing_fast:
    score -= 5
    tips.append("Slow pacing slightly for CTV — viewers are in lean-back mode, not scrolling.")

  # Text readability: important on big screen
  if text_readable:
    score += 5
  else:
    tips.append("Ensure text is large and high-contrast for viewing from 10+ feet on TV screens.")

  return {
      "score": max(0, min(100, score)),
      "tips": tips[:3],
  }


# --- Public API ---

def compute_platform_fit(
    abcd_features: list[dict],
    persuasion_features: list[dict],
    structure_features: list[dict],
    accessibility_features: list[dict],
    video_metadata: dict,
    scenes: list[dict],
) -> dict:
  """Compute platform fit scores for all platforms.

  Args:
    abcd_features: Formatted ABCD feature dicts.
    persuasion_features: Formatted persuasion feature dicts.
    structure_features: Formatted structure feature dicts.
    accessibility_features: Formatted accessibility feature dicts.
    video_metadata: Video metadata dict (duration, resolution, aspect_ratio, etc.).
    scenes: Formatted scene list.

  Returns:
    Dict with per-platform {score, tips} entries.
  """
  # Extract signals from features and metadata
  duration_s = _parse_duration_seconds(video_metadata.get("duration", ""))
  ar = _parse_aspect_ratio(video_metadata.get("aspect_ratio", ""))
  scene_count = len(scenes) if scenes else 0

  all_features = abcd_features + persuasion_features + structure_features + accessibility_features

  # Pacing: more than 1 scene per 5 seconds = fast
  pacing_fast = (scene_count / max(duration_s, 1) * 5) > 1.0 if duration_s > 0 else False

  # Hook: any ATTRACT feature detected
  hook_fast = _has_feature_keyword(abcd_features, ["dynamic start", "hook", "supers"], detected_only=True)

  # CTA: any DIRECT feature detected
  has_cta = _has_feature_keyword(
      abcd_features,
      ["call to action", "offer", "text", "url"],
      detected_only=True,
  )

  # Brand early: any BRAND feature detected
  has_brand_early = _has_feature_keyword(
      abcd_features,
      ["brand", "logo"],
      detected_only=True,
  )

  # Captions: accessibility feature
  has_captions = _has_feature_keyword(
      accessibility_features,
      ["captions", "subtitles"],
      detected_only=True,
  )

  # Audio independence
  audio_independent = _has_feature_keyword(
      accessibility_features,
      ["audio independence"],
      detected_only=True,
  )

  # Text readability
  text_readable = _has_feature_keyword(
      accessibility_features,
      ["text contrast", "readability"],
      detected_only=True,
  )

  # Structure archetype
  structure_archetype = ""
  if structure_features:
    structure_archetype = structure_features[0].get("evidence", "")

  common = dict(
      duration_s=duration_s,
      ar=ar,
      scene_count=scene_count,
      hook_fast=hook_fast,
      has_cta=has_cta,
      has_brand_early=has_brand_early,
      has_captions=has_captions,
      audio_independent=audio_independent,
      text_readable=text_readable,
      pacing_fast=pacing_fast,
      structure_archetype=structure_archetype,
  )

  return {
      "youtube": _score_youtube(**common),
      "meta_feed": _score_meta_feed(**common),
      "meta_reels": _score_meta_reels(**common),
      "tiktok": _score_tiktok(**common),
      "ctv": _score_ctv(**common),
  }
