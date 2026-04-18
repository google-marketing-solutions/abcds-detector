"""Tests for platform_optimizer module."""

import pytest
from platform_optimizer import (
    _parse_aspect_ratio,
    _parse_duration_seconds,
    _has_feature_keyword,
    _score_youtube,
    _score_meta_feed,
    _score_meta_reels,
    _score_tiktok,
    _score_ctv,
    compute_platform_fit,
)


# ---- Parse helpers ----

class TestParseAspectRatio:
  def test_colon_format(self):
    assert _parse_aspect_ratio("16:9") == pytest.approx(16 / 9, rel=1e-3)

  def test_colon_4_5(self):
    assert _parse_aspect_ratio("4:5") == pytest.approx(0.8, rel=1e-3)

  def test_float_string(self):
    assert _parse_aspect_ratio("1.78") == pytest.approx(1.78, rel=1e-3)

  def test_empty(self):
    assert _parse_aspect_ratio("") is None

  def test_none(self):
    assert _parse_aspect_ratio(None) is None

  def test_invalid(self):
    assert _parse_aspect_ratio("abc") is None

  def test_zero_denominator(self):
    assert _parse_aspect_ratio("16:0") is None


class TestParseDurationSeconds:
  def test_mm_ss(self):
    assert _parse_duration_seconds("0:30") == 30.0

  def test_mm_ss_with_minutes(self):
    assert _parse_duration_seconds("1:05") == 65.0

  def test_hh_mm_ss(self):
    assert _parse_duration_seconds("1:02:30") == 3750.0

  def test_seconds_suffix(self):
    assert _parse_duration_seconds("30s") == 30.0

  def test_plain_number(self):
    assert _parse_duration_seconds("45") == 45.0

  def test_empty(self):
    assert _parse_duration_seconds("") == 0.0

  def test_none(self):
    assert _parse_duration_seconds(None) == 0.0

  def test_invalid(self):
    assert _parse_duration_seconds("abc") == 0.0


class TestHasFeatureKeyword:
  def test_detected_match(self):
    features = [{"name": "Dynamic Start Hook", "detected": True}]
    assert _has_feature_keyword(features, ["dynamic start"]) is True

  def test_not_detected_skipped(self):
    features = [{"name": "Dynamic Start Hook", "detected": False}]
    assert _has_feature_keyword(features, ["dynamic start"], detected_only=True) is False

  def test_not_detected_included(self):
    features = [{"name": "Dynamic Start Hook", "detected": False}]
    assert _has_feature_keyword(features, ["dynamic start"], detected_only=False) is True

  def test_no_match(self):
    features = [{"name": "Brand Logo", "detected": True}]
    assert _has_feature_keyword(features, ["dynamic start"]) is False

  def test_empty(self):
    assert _has_feature_keyword([], ["anything"]) is False


# ---- Platform scoring ----

class TestScoreYouTube:
  def test_ideal_video(self):
    result = _score_youtube(
        duration_s=30, ar=16/9, scene_count=6,
        hook_fast=True, has_cta=True, has_brand_early=True, has_captions=True,
    )
    assert result["score"] >= 90
    assert isinstance(result["tips"], list)

  def test_short_video_penalized(self):
    result = _score_youtube(
        duration_s=3, ar=16/9, scene_count=1,
        hook_fast=False, has_cta=False, has_brand_early=False, has_captions=False,
    )
    assert result["score"] < 70

  def test_vertical_penalized(self):
    result = _score_youtube(
        duration_s=30, ar=9/16, scene_count=6,
        hook_fast=True, has_cta=True, has_brand_early=True, has_captions=True,
    )
    # Vertical should lose points vs landscape
    ideal = _score_youtube(
        duration_s=30, ar=16/9, scene_count=6,
        hook_fast=True, has_cta=True, has_brand_early=True, has_captions=True,
    )
    assert result["score"] < ideal["score"]

  def test_score_clamped_0_100(self):
    result = _score_youtube(
        duration_s=30, ar=16/9, scene_count=6,
        hook_fast=True, has_cta=True, has_brand_early=True, has_captions=True,
    )
    assert 0 <= result["score"] <= 100


class TestScoreMetaFeed:
  def test_ideal_feed_video(self):
    result = _score_meta_feed(
        duration_s=20, ar=1.0, hook_fast=True,
        has_cta=True, has_captions=True, audio_independent=True,
    )
    assert result["score"] >= 85

  def test_landscape_penalized(self):
    result = _score_meta_feed(
        duration_s=20, ar=16/9, hook_fast=True,
        has_cta=True, has_captions=True, audio_independent=True,
    )
    assert any("square" in t.lower() or "landscape" in t.lower() for t in result["tips"])

  def test_no_captions_no_audio_independence(self):
    result = _score_meta_feed(
        duration_s=20, ar=1.0, hook_fast=True,
        has_cta=True, has_captions=False, audio_independent=False,
    )
    assert result["score"] <= 70


class TestScoreMetaReels:
  def test_ideal_reel(self):
    result = _score_meta_reels(
        duration_s=20, ar=9/16, hook_fast=True,
        has_captions=True, audio_independent=True,
        pacing_fast=True, structure_archetype="UGC",
    )
    assert result["score"] >= 85

  def test_landscape_heavily_penalized(self):
    result = _score_meta_reels(
        duration_s=20, ar=16/9, hook_fast=True,
        has_captions=True, audio_independent=True,
        pacing_fast=True, structure_archetype="",
    )
    assert result["score"] <= 65


class TestScoreTikTok:
  def test_ideal_tiktok(self):
    result = _score_tiktok(
        duration_s=12, ar=9/16, hook_fast=True,
        has_captions=True, pacing_fast=True, structure_archetype="UGC",
    )
    assert result["score"] >= 85

  def test_long_landscape(self):
    result = _score_tiktok(
        duration_s=90, ar=16/9, hook_fast=False,
        has_captions=False, pacing_fast=False, structure_archetype="",
    )
    assert result["score"] < 45


class TestScoreCTV:
  def test_ideal_ctv(self):
    result = _score_ctv(
        duration_s=30, ar=16/9, has_brand_early=True,
        has_cta=True, pacing_fast=False, text_readable=True,
    )
    assert result["score"] >= 90

  def test_vertical_penalized(self):
    result = _score_ctv(
        duration_s=30, ar=9/16, has_brand_early=True,
        has_cta=True, pacing_fast=False, text_readable=True,
    )
    assert result["score"] <= 80


# ---- Integration: compute_platform_fit ----

class TestComputePlatformFit:
  def test_returns_all_platforms(
      self, abcd_features, persuasion_features, structure_features,
      accessibility_features, video_metadata, sample_scenes,
  ):
    result = compute_platform_fit(
        abcd_features, persuasion_features, structure_features,
        accessibility_features, video_metadata, sample_scenes,
    )
    for key in ("youtube", "meta_feed", "meta_reels", "tiktok", "ctv"):
      assert key in result
      assert "score" in result[key]
      assert "tips" in result[key]
      assert 0 <= result[key]["score"] <= 100

  def test_empty_inputs(self):
    result = compute_platform_fit([], [], [], [], {}, [])
    assert "youtube" in result
    for key in result:
      assert 0 <= result[key]["score"] <= 100
