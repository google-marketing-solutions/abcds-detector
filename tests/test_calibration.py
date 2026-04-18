"""Tests for calibration module."""

import pytest
from calibration import calibrate_confidence


class TestCalibrateConfidence:
  def test_no_calibration_data_returns_raw(self):
    assert calibrate_confidence(0.8, "feat_1", None) == 0.8

  def test_missing_feature_returns_raw(self):
    cal = {"other_feat": {"accuracy": 0.9, "sample_size": 25, "reliability_level": "high"}}
    assert calibrate_confidence(0.8, "feat_1", cal) == 0.8

  def test_calibration_blends_with_accuracy(self):
    cal = {"feat_1": {"accuracy": 0.6, "sample_size": 30, "reliability_level": "medium"}}
    result = calibrate_confidence(0.8, "feat_1", cal)
    # 0.7 * 0.8 + 0.3 * 0.6 = 0.56 + 0.18 = 0.74
    assert result == pytest.approx(0.74, abs=0.01)

  def test_clamped_at_1(self):
    cal = {"feat_1": {"accuracy": 1.0, "sample_size": 50, "reliability_level": "high"}}
    result = calibrate_confidence(1.0, "feat_1", cal)
    assert result <= 1.0

  def test_clamped_at_0(self):
    cal = {"feat_1": {"accuracy": 0.0, "sample_size": 50, "reliability_level": "low"}}
    result = calibrate_confidence(0.0, "feat_1", cal)
    assert result >= 0.0

  def test_accuracy_none_returns_raw(self):
    cal = {"feat_1": {"accuracy": None, "sample_size": 0, "reliability_level": "unknown"}}
    assert calibrate_confidence(0.75, "feat_1", cal) == 0.75
