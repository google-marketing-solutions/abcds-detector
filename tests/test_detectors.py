###########################################################################
#
#  Copyright 2024 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
###########################################################################

"""Tests for ABCD feature evaluation detectors (LLM and Custom)."""

import unittest
from unittest import mock

import configuration
from custom_evaluation import custom_detector
from llm_evaluation import llm_detector
import models


class TestDetectors(unittest.TestCase):
  """Tests for LLMDetector and CustomDetector execution and validation."""

  def test_llm_detector_returns_feature_evaluations(self) -> None:
    """Tests that LLMDetector parses Gemini JSON into FeatureEvaluations."""
    feature = models.VideoFeature(
        id="a_dynamic_start",
        name="Dynamic Start",
        category=models.VideoFeatureCategory.UNIVERSAL,
        sub_category=models.VideoFeatureSubCategory.ATTRACT,
        evaluation_criteria="Criteria",
    )
    mock_gemini_service = mock.MagicMock()
    mock_gemini_service.call_gemini_vertex_ai.return_value = [{
        "id": "a_dynamic_start",
        "is_detected": True,
        "confidence_score": 0.88,
        "rationale": "High energy visual opening.",
        "evidence": "Opening cut at 00:01",
        "strengths": "Fast visual motion",
        "weaknesses": "",
        "recommended_actions": "Add hook text",
        "first_appearance_timestamp": 1.2,
        "feature_density_score": 0.9,
        "feature_quality_score": 0.85,
        "feature_specifics": {"framing_cadence": "fast"},
    }]

    detector = llm_detector.LLMDetector()
    results = detector.evaluate_features(
        gemini_service=mock_gemini_service,
        video_uri="gs://test/video.mp4",
        feature_configs=[feature],
        slice_name="universal",
    )

    self.assertEqual(len(results), 1)
    self.assertIsInstance(results[0], models.FeatureEvaluation)
    self.assertEqual(results[0].feature.id, "a_dynamic_start")
    self.assertTrue(results[0].is_detected)
    self.assertEqual(results[0].confidence_score, 0.88)
    self.assertEqual(results[0].rationale, "High energy visual opening.")
    self.assertEqual(results[0].evidence, "Opening cut at 00:01")
    self.assertEqual(results[0].strengths, "Fast visual motion")
    self.assertEqual(results[0].weaknesses, "")
    self.assertEqual(results[0].recommended_actions, "Add hook text")
    self.assertEqual(results[0].first_appearance_timestamp, 1.2)
    self.assertEqual(results[0].feature_density_score, 0.9)
    self.assertEqual(results[0].feature_quality_score, 0.85)
    self.assertEqual(results[0].feature_specifics, {"framing_cadence": "fast"})
    _, kwargs = mock_gemini_service.call_gemini_vertex_ai.call_args
    self.assertEqual(kwargs.get("response_schema"), models.VIDEO_EVAL_SCHEMA)

    # Verify shorts also uses the exact same models.VIDEO_EVAL_SCHEMA
    mock_gemini_service.reset_mock()
    mock_gemini_service.call_gemini_vertex_ai.return_value = []
    detector.evaluate_features(
        gemini_service=mock_gemini_service,
        video_uri="gs://test/video.mp4",
        feature_configs=[feature],
        slice_name="shorts",
    )
    _, kwargs_shorts = mock_gemini_service.call_gemini_vertex_ai.call_args
    self.assertEqual(
        kwargs_shorts.get("response_schema"), models.VIDEO_EVAL_SCHEMA
    )

  def test_custom_evaluator_registry(self) -> None:
    """Tests registering and invoking a custom evaluation function."""

    @custom_detector.register_evaluator("test_dummy_evaluator")
    def dummy_eval(
        gemini_config: configuration.GeminiConfig,
        feature_config: models.VideoFeature,
        video_uri: str,
        brand_context: configuration.BrandContext | None = None,
    ) -> models.FeatureEvaluation:
      """Returns a valid FeatureEvaluation for testing."""
      return models.FeatureEvaluation(
          feature=feature_config,
          is_detected=True,
          confidence_score=0.99,
          rationale="Good performance",
          evidence="Evidence found",
          strengths="Good audio",
          weaknesses="None",
      )

    test_feature = models.VideoFeature(
        id="test_custom_feature",
        name="Test Custom Feature",
        category=models.VideoFeatureCategory.UNIVERSAL,
        sub_category=models.VideoFeatureSubCategory.ATTRACT,
        evaluation_criteria="Test criteria",
        evaluation_function="test_dummy_evaluator",
    )

    gemini_config = configuration.GeminiConfig(api_key="test-key")
    detector = custom_detector.CustomDetector()
    result = detector.evaluate_feature(
        gemini_config=gemini_config,
        feature_config=test_feature,
        video_uri="gs://test-bucket/video.mp4",
    )
    self.assertIsInstance(result, models.FeatureEvaluation)
    self.assertTrue(result.is_detected)
    self.assertEqual(result.confidence_score, 0.99)
    self.assertEqual(result.feature.id, "test_custom_feature")

  def test_custom_evaluator_invalid_return_type_raises(self) -> None:
    """Tests that returning non-FeatureEvaluation raises TypeError."""

    @custom_detector.register_evaluator("test_dict_evaluator")
    def dict_eval(
        gemini_config: configuration.GeminiConfig,
        feature_config: models.VideoFeature,
        video_uri: str,
        brand_context: configuration.BrandContext | None = None,
    ) -> dict[str, bool]:
      """Returns an invalid dict for testing return type enforcement."""
      return {"is_detected": True}

    test_feature = models.VideoFeature(
        id="test_invalid_feature",
        name="Test Invalid Feature",
        category=models.VideoFeatureCategory.UNIVERSAL,
        sub_category=models.VideoFeatureSubCategory.ATTRACT,
        evaluation_criteria="Test criteria",
        evaluation_function="test_dict_evaluator",
    )

    gemini_config = configuration.GeminiConfig(api_key="test-key")
    detector = custom_detector.CustomDetector()
    with self.assertRaises(TypeError) as ctx:
      detector.evaluate_feature(
          gemini_config=gemini_config,
          feature_config=test_feature,
          video_uri="gs://test-bucket/video.mp4",
      )
    self.assertIn(
        "must return a FeatureEvaluation instance", str(ctx.exception)
    )


if __name__ == "__main__":
  unittest.main()
