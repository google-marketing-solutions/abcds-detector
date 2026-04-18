"""Tests for web_app.py — config building, result formatting, provider detection."""

import json
import pytest
import models
from web_app import build_config, format_results, format_feature


# ---------------------------------------------------------------------------
# build_config
# ---------------------------------------------------------------------------

class TestBuildConfig:
    def test_gcs_provider(self):
        config = build_config(provider_type="GCS")
        assert config.creative_provider_type == models.CreativeProviderType.GCS

    def test_youtube_provider(self):
        config = build_config(provider_type="YOUTUBE")
        assert config.creative_provider_type == models.CreativeProviderType.YOUTUBE

    def test_defaults(self):
        config = build_config()
        assert config.run_long_form_abcd is True
        assert config.run_shorts is False
        assert config.run_creative_intelligence is True

    def test_toggle_flags(self):
        config = build_config(use_abcd=False, use_shorts=True, use_ci=False)
        assert config.run_long_form_abcd is False
        assert config.run_shorts is True
        assert config.run_creative_intelligence is False


# ---------------------------------------------------------------------------
# Provider detection (inline logic in evaluate_video)
# ---------------------------------------------------------------------------

class TestProviderDetection:
    """The provider_type in web_app is derived from the gcs_uri string."""

    @pytest.mark.parametrize("url,expected", [
        ("https://www.youtube.com/watch?v=abc", "YOUTUBE"),
        ("https://youtu.be/abc", "YOUTUBE"),
        ("https://m.youtube.com/watch?v=abc", "YOUTUBE"),
        ("gs://my-bucket/video.mp4", "GCS"),
    ])
    def test_detection(self, url, expected):
        detected = "YOUTUBE" if "youtube.com" in url or "youtu.be" in url else "GCS"
        assert detected == expected


# ---------------------------------------------------------------------------
# format_feature
# ---------------------------------------------------------------------------

class TestFormatFeature:
    def _make_fe(self, detected=True):
        feat = models.VideoFeature(
            id="F1", name="Test",
            category=models.VideoFeatureCategory.LONG_FORM_ABCD,
            sub_category=models.VideoFeatureSubCategory.ATTRACT,
            video_segment=models.VideoSegment.FULL_VIDEO,
            evaluation_criteria="c", prompt_template=None,
            extra_instructions=[], evaluation_method=models.EvaluationMethod.LLMS,
            evaluation_function="", include_in_evaluation=True, group_by="FULL_VIDEO",
        )
        return models.FeatureEvaluation(
            feature=feat, detected=detected, confidence_score=0.85,
            rationale="r", evidence="e", strengths="s", weaknesses="w",
        )

    def test_returns_dict(self):
        result = format_feature(self._make_fe())
        assert isinstance(result, dict)

    def test_detected_key(self):
        result = format_feature(self._make_fe(detected=True))
        assert result["detected"] is True

    def test_not_detected(self):
        result = format_feature(self._make_fe(detected=False))
        assert result["detected"] is False

    def test_json_serializable(self):
        result = format_feature(self._make_fe())
        json.dumps(result)  # should not raise

    def test_has_no_evaluation_key(self):
        """FeatureEvaluation uses 'detected', not 'evaluation'."""
        fe = self._make_fe()
        assert not hasattr(fe, "evaluation")
        assert hasattr(fe, "detected")


# ---------------------------------------------------------------------------
# format_results
# ---------------------------------------------------------------------------

class TestFormatResults:
    def test_empty_evaluations_json_serializable(self):
        result = format_results(
            brand_name="TestBrand",
            video_uri="https://www.youtube.com/watch?v=abc",
            long_form=[], shorts=[], creative_intel=[],
            scenes=[], keyframes=[], volumes=[],
            brand_intel={}, video_metadata={},
        )
        serialized = json.dumps(result)
        parsed = json.loads(serialized)
        assert parsed["brand_name"] == "TestBrand"
        assert parsed["abcd"]["score"] == 0
        assert parsed["abcd"]["total"] == 0

    def test_none_brand_name(self):
        result = format_results(
            brand_name=None,
            video_uri="gs://bucket/video.mp4",
            long_form=[], shorts=[], creative_intel=[],
        )
        json.dumps(result)  # should not raise TypeError

    def test_predictions_included(self):
        result = format_results(
            brand_name="X",
            video_uri="gs://bucket/video.mp4",
            long_form=[], shorts=[], creative_intel=[],
        )
        assert "predictions" in result
        assert isinstance(result["predictions"], dict)

    def test_with_real_evaluations(self):
        fe = TestFormatFeature()._make_fe(detected=True)
        result = format_results(
            brand_name="Acme",
            video_uri="gs://bucket/video.mp4",
            long_form=[fe], shorts=[], creative_intel=[],
        )
        assert result["abcd"]["total"] == 1
        assert result["abcd"]["passed"] == 1
        assert result["abcd"]["score"] == 100.0
