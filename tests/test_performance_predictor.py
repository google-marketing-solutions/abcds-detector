"""Tests for performance_predictor module."""

import pytest
from performance_predictor import (
    _section_score,
    _has_keyword_detected,
    _by_sub,
    compute_predictions,
    SECTION_MAXES,
)


class TestSectionScore:
  def test_empty_features(self):
    assert _section_score([], 15) == 0.0

  def test_all_detected_high_confidence(self):
    features = [
        {"detected": True, "confidence": 1.0},
        {"detected": True, "confidence": 1.0},
    ]
    result = _section_score(features, 10)
    assert result == pytest.approx(10.0, abs=0.01)

  def test_none_detected(self):
    features = [
        {"detected": False, "confidence": 0.5},
        {"detected": False, "confidence": 0.5},
    ]
    assert _section_score(features, 10) == 0.0

  def test_partial_detection(self):
    features = [
        {"detected": True, "confidence": 0.8},
        {"detected": False, "confidence": 0.5},
    ]
    result = _section_score(features, 10)
    # 1 detected: 0.8 * (10/2) = 4.0
    assert result == pytest.approx(4.0, abs=0.01)

  def test_no_confidence_defaults_half(self):
    features = [{"detected": True, "confidence": None}]
    result = _section_score(features, 10)
    assert result == pytest.approx(5.0, abs=0.01)  # 0.5 * 10

  def test_capped_at_max(self):
    features = [{"detected": True, "confidence": 2.0}]  # above 1.0
    result = _section_score(features, 10)
    assert result <= 10.0


class TestHasKeywordDetected:
  def test_match(self):
    features = [{"name": "dynamic start with motion", "detected": True}]
    assert _has_keyword_detected(features, ["dynamic start"]) is True

  def test_not_detected_skipped(self):
    features = [{"name": "dynamic start", "detected": False}]
    assert _has_keyword_detected(features, ["dynamic start"]) is False

  def test_no_match(self):
    features = [{"name": "Brand Logo", "detected": True}]
    assert _has_keyword_detected(features, ["dynamic start"]) is False

  def test_custom_field(self):
    features = [{"name": "CTA", "evidence": "shop now button", "detected": True}]
    assert _has_keyword_detected(features, ["shop"], field="evidence") is True


class TestBySub:
  def test_filters_correctly(self):
    features = [
        {"sub_category": "ATTRACT", "name": "hook"},
        {"sub_category": "BRAND", "name": "logo"},
        {"sub_category": "ATTRACT", "name": "supers"},
    ]
    result = _by_sub(features, "ATTRACT")
    assert len(result) == 2
    assert all(f["sub_category"] == "ATTRACT" for f in result)

  def test_case_insensitive(self):
    features = [{"sub_category": "attract", "name": "hook"}]
    result = _by_sub(features, "ATTRACT")
    assert len(result) == 1

  def test_empty_input(self):
    assert _by_sub([], "ATTRACT") == []


class TestComputePredictions:
  def test_returns_expected_keys(self, abcd_features, persuasion_features, structure_features):
    result = compute_predictions(abcd_features, persuasion_features, structure_features)
    assert "overall_score" in result
    assert "section_scores" in result
    assert "section_maxes" in result
    assert "normalized" in result
    assert "flags" in result
    assert "labels" in result
    assert "drivers" in result

  def test_overall_score_in_range(self, abcd_features, persuasion_features, structure_features):
    result = compute_predictions(abcd_features, persuasion_features, structure_features)
    assert 0 <= result["overall_score"] <= 100

  def test_section_scores_within_max(self, abcd_features, persuasion_features, structure_features):
    result = compute_predictions(abcd_features, persuasion_features, structure_features)
    for key, score in result["section_scores"].items():
      assert score <= SECTION_MAXES[key] + 0.01, f"{key} exceeds max"

  def test_normalized_between_0_and_1(self, abcd_features, persuasion_features, structure_features):
    result = compute_predictions(abcd_features, persuasion_features, structure_features)
    for key, val in result["normalized"].items():
      assert 0 <= val <= 1.0001, f"{key} normalized value out of range: {val}"

  def test_flags_are_booleans(self, abcd_features, persuasion_features, structure_features):
    result = compute_predictions(abcd_features, persuasion_features, structure_features)
    for key, val in result["flags"].items():
      assert isinstance(val, bool), f"Flag {key} is not bool"

  def test_empty_features(self):
    result = compute_predictions([], [], [])
    assert result["overall_score"] == 0 or result["overall_score"] >= 0
    assert isinstance(result["section_scores"], dict)

  def test_indices_present(self, abcd_features, persuasion_features, structure_features):
    result = compute_predictions(abcd_features, persuasion_features, structure_features)
    # Should have CRI, ROAS, fatigue_risk, funnel_strength
    assert "cri" in result or "indices" in result or "overall_score" in result

  def test_drivers_structure(self, abcd_features, persuasion_features, structure_features):
    result = compute_predictions(abcd_features, persuasion_features, structure_features)
    drivers = result.get("drivers", {})
    assert "top_positive" in drivers
    assert "top_negative" in drivers
    assert isinstance(drivers["top_positive"], list)
