"""Tests for web_app business logic functions.

Tests the pure functions in web_app.py that don't require the FastAPI app
or external services (LLM, GCS, etc.).
"""

import sys
import types
import pytest

# Stub out heavy GCP dependencies before importing web_app
from unittest.mock import MagicMock

_STUB_MODULES = [
    "vertexai", "vertexai.generative_models", "vertexai.preview",
    "vertexai.preview.generative_models",
    "google.cloud.videointelligence", "google.cloud.videointelligence_v1",
    "google.cloud.bigquery", "google.cloud.storage",
    "google.cloud.aiplatform",
    "google.api_core", "google.api_core.exceptions",
    "google.auth", "google.auth.transport", "google.auth.transport.requests",
    "google.oauth2", "google.oauth2.id_token",
    "google.genai", "google.genai.types",
    "google.api_python_client",
    "moviepy", "moviepy.editor",
    "yt_dlp",
    "stripe",
]
for _mod_name in _STUB_MODULES:
  if _mod_name not in sys.modules:
    sys.modules[_mod_name] = MagicMock()

from web_app import (
    compute_comparison,
    _compute_emotional_coherence,
    _compute_accessibility,
    _build_action_plan,
    _build_feature_timeline,
    _parse_ts_seconds,
)


# ---- Timestamp parsing ----

class TestParseTimestampSeconds:
  def test_mm_ss(self):
    assert _parse_ts_seconds("0:30") == 30.0

  def test_m_ss(self):
    assert _parse_ts_seconds("1:05") == 65.0

  def test_hh_mm_ss(self):
    assert _parse_ts_seconds("1:02:30") == 3750.0

  def test_zero(self):
    assert _parse_ts_seconds("0:00") == 0.0

  def test_invalid(self):
    assert _parse_ts_seconds("abc") == 0.0

  def test_empty(self):
    assert _parse_ts_seconds("") == 0.0


# ---- Emotional coherence ----

class TestComputeEmotionalCoherence:
  def test_single_scene(self):
    result = _compute_emotional_coherence([{"sentiment_score": 0.5}])
    assert result["score"] == 100
    assert result["flagged_shifts"] == []

  def test_smooth_arc(self):
    scenes = [
        {"sentiment_score": 0.0, "scene_number": 1, "emotion": "calm"},
        {"sentiment_score": 0.1, "scene_number": 2, "emotion": "calm"},
        {"sentiment_score": 0.2, "scene_number": 3, "emotion": "trust"},
        {"sentiment_score": 0.3, "scene_number": 4, "emotion": "trust"},
    ]
    result = _compute_emotional_coherence(scenes)
    assert result["score"] >= 85
    assert len(result["flagged_shifts"]) == 0

  def test_abrupt_shift_flagged(self):
    scenes = [
        {"sentiment_score": 0.8, "scene_number": 1, "emotion": "excitement"},
        {"sentiment_score": -0.5, "scene_number": 2, "emotion": "sadness"},
    ]
    result = _compute_emotional_coherence(scenes)
    assert result["score"] < 50
    assert len(result["flagged_shifts"]) == 1
    assert result["flagged_shifts"][0]["delta"] > 0.5

  def test_empty_scenes(self):
    result = _compute_emotional_coherence([])
    assert result["score"] == 100

  def test_mixed_shifts(self, sample_scenes):
    result = _compute_emotional_coherence(sample_scenes)
    assert 0 <= result["score"] <= 100
    assert isinstance(result["flagged_shifts"], list)


# ---- Accessibility ----

class TestComputeAccessibility:
  def test_basic_score(self, accessibility_features, sample_scenes):
    result = _compute_accessibility(accessibility_features, sample_scenes)
    assert "score" in result
    assert "passed" in result
    assert "total" in result
    assert "features" in result
    assert "speech_rate_wpm" in result
    assert "speech_rate_flag" in result
    assert 0 <= result["score"] <= 100

  def test_speech_rate_computed(self, accessibility_features, sample_scenes):
    result = _compute_accessibility(accessibility_features, sample_scenes)
    # With the sample scenes having transcripts & speech ratios, WPM should be > 0
    assert result["speech_rate_wpm"] > 0
    assert result["speech_rate_flag"] in ("ok", "too_fast", "too_slow")

  def test_no_speech_scenes(self, accessibility_features):
    scenes = [{"scene_number": 1, "start_time": "0:00", "end_time": "0:10"}]
    result = _compute_accessibility(accessibility_features, scenes)
    assert result["speech_rate_wpm"] == 0
    assert result["speech_rate_flag"] == "no_speech"

  def test_enriched_features_have_remediation(self, accessibility_features, sample_scenes):
    result = _compute_accessibility(accessibility_features, sample_scenes)
    for f in result["features"]:
      # All accessibility features should have remediation text
      assert "remediation" in f

  def test_empty_features(self, sample_scenes):
    result = _compute_accessibility([], sample_scenes)
    assert result["score"] == 100  # No features = perfect
    assert result["total"] == 0


# ---- Action plan ----

class TestBuildActionPlan:
  def test_features_with_recommendations(self):
    features = [
        {"name": "CTA", "detected": False, "recommendation": "Add a CTA", "recommendation_priority": "high"},
        {"name": "Hook", "detected": True, "recommendation": "Improve hook timing", "recommendation_priority": "medium"},
        {"name": "Logo", "detected": True, "recommendation": "", "recommendation_priority": ""},
    ]
    plan = _build_action_plan(features)
    assert len(plan) == 2  # Only features with recommendations
    assert plan[0]["priority"] == "high"  # Sorted by priority
    assert plan[1]["priority"] == "medium"

  def test_empty_features(self):
    assert _build_action_plan([]) == []

  def test_no_recommendations(self):
    features = [{"name": "A", "detected": True, "recommendation": "", "recommendation_priority": ""}]
    assert _build_action_plan(features) == []


# ---- Feature timeline ----

class TestBuildFeatureTimeline:
  def test_basic_timeline(self, sample_scenes):
    features = [
        {
            "id": "f1", "name": "Hook", "sub_category": "ATTRACT",
            "detected": True,
            "timestamps": [{"start": "0:00", "end": "0:03", "label": "opening hook"}],
        },
        {
            "id": "f2", "name": "CTA", "sub_category": "DIRECT",
            "detected": True,
            "timestamps": [{"start": "0:25", "end": "0:30", "label": "end CTA"}],
        },
    ]
    result = _build_feature_timeline(features, sample_scenes)
    assert "video_duration_s" in result
    assert result["video_duration_s"] >= 30  # Last scene ends at 0:30
    assert len(result["scene_boundaries"]) == 4
    assert len(result["features"]) == 2
    assert result["features"][0]["timestamps"][0]["start_s"] == 0.0

  def test_empty_features(self, sample_scenes):
    result = _build_feature_timeline([], sample_scenes)
    assert result["features"] == []
    assert len(result["scene_boundaries"]) == len(sample_scenes)

  def test_empty_scenes(self):
    result = _build_feature_timeline([], [])
    assert result["video_duration_s"] == 0.0


# ---- Comparison ----

class TestComputeComparison:
  def _make_variant(self, name, abcd_score, perf_score, pers_density, acc_score=80):
    return {
        "video_name": name,
        "brand_name": "TestBrand",
        "abcd": {"score": abcd_score, "features": []},
        "persuasion": {"density": pers_density, "features": []},
        "predictions": {"overall_score": perf_score},
        "accessibility": {"score": acc_score, "features": []},
        "emotional_coherence": {"score": 75},
        "report_id": f"rpt-{name.lower().replace(' ', '-')}",
    }

  def test_two_variants(self):
    variants = [
        self._make_variant("Variant A", 80, 70, 60),
        self._make_variant("Variant B", 90, 85, 50),
    ]
    result = compute_comparison(variants)
    assert result["variant_count"] == 2
    assert len(result["variants"]) == 2
    assert len(result["deltas"]) == 1
    assert "recommended_winner" in result
    assert result["recommended_winner"]["video_name"] in ("Variant A", "Variant B")

  def test_deltas_computed_correctly(self):
    variants = [
        self._make_variant("A", 80, 70, 60),
        self._make_variant("B", 90, 85, 50),
    ]
    result = compute_comparison(variants)
    delta = result["deltas"][0]
    assert delta["abcd_delta"] == 10.0
    assert delta["performance_delta"] == 15.0
    assert delta["persuasion_delta"] == -10.0

  def test_winner_is_higher_composite(self):
    # B has much higher performance score → should win
    variants = [
        self._make_variant("A", 50, 30, 50, 50),
        self._make_variant("B", 90, 95, 90, 90),
    ]
    result = compute_comparison(variants)
    assert result["recommended_winner"]["video_name"] == "B"

  def test_feature_diffs_detected(self):
    va = self._make_variant("A", 80, 70, 60)
    va["abcd"]["features"] = [{"id": "f1", "name": "Hook", "detected": True}]
    vb = self._make_variant("B", 85, 75, 50)
    vb["abcd"]["features"] = [{"id": "f1", "name": "Hook", "detected": False}]
    result = compute_comparison([va, vb])
    assert len(result["feature_diffs"]) >= 1
    diff = result["feature_diffs"][0]
    assert diff["feature_id"] == "f1"
    assert diff["results"] == [True, False]

  def test_less_than_two_variants(self):
    assert compute_comparison([self._make_variant("A", 80, 70, 60)]) == {}

  def test_three_variants(self):
    variants = [
        self._make_variant("A", 70, 60, 50),
        self._make_variant("B", 80, 70, 60),
        self._make_variant("C", 90, 80, 70),
    ]
    result = compute_comparison(variants)
    assert result["variant_count"] == 3
    assert len(result["deltas"]) == 2  # B vs A, C vs A
    assert result["recommended_winner"]["video_name"] == "C"
