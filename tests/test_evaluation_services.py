###########################################################################
#
#  Copyright 2025 Google LLC
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

"""Tests for VideoEvaluationService execution and orchestration."""

import unittest
from unittest import mock

import configuration
from evaluation_services import video_evaluation_service
from features_repository import feature_configs_handler
from gcp_api_services import gemini_api_service
import models


class TestVideoEvaluationService(unittest.TestCase):
  """Tests for VideoEvaluationService pipeline execution and dispatching."""

  @mock.patch.object(
      feature_configs_handler.features_configs_handler,
      "get_features_for_slice",
  )
  def test_evaluate_video_bulk_mode(
      self, mock_get_features: mock.MagicMock
  ) -> None:
    """Tests that evaluate_video evaluates features and produces assessment."""
    mock_gemini_service = mock.MagicMock(
        spec=gemini_api_service.GeminiAPIService
    )
    mock_gemini_service.extract_brand_metadata.return_value = (
        configuration.BrandContext(
            brand_name="TestBrand",
            branded_products=["Product A"],
            branded_call_to_actions=["Learn more"],
        )
    )

    mock_llm_detector = mock.MagicMock()
    feature = models.VideoFeature(
        id="test_feature",
        name="Test Feature",
        category=models.VideoFeatureCategory.UNIVERSAL,
        sub_category=models.VideoFeatureSubCategory.ATTRACT,
        evaluation_criteria="Test criteria",
    )
    eval_result = models.FeatureEvaluation(
        feature=feature,
        is_detected=True,
        confidence_score=0.95,
        rationale="Strong opening hook",
        evidence="Found at 00:01",
    )
    mock_llm_detector.evaluate_features.return_value = [eval_result]
    mock_get_features.return_value = [feature]

    service = video_evaluation_service.VideoEvaluationService(
        detector_llm=mock_llm_detector,
    )

    req = configuration.EvaluationRequest(
        video_uris=["gs://bucket/test.mp4"],
        gcp_config=configuration.GCPConfig(project_id="test-proj"),
        gemini_config=configuration.GeminiConfig(api_key="test-key"),
        slices=["universal"],
        extract_brand_metadata=True,
    )

    assessment = service.evaluate_video(
        request=req,
        video_uri="gs://bucket/test.mp4",
        gemini_service=mock_gemini_service,
    )

    mock_get_features.assert_called_once_with(
        slice_name="universal",
        features_filter=None,
    )
    self.assertEqual(assessment.brand_name, "TestBrand")
    self.assertEqual(assessment.video_uri, "gs://bucket/test.mp4")
    self.assertIsNotNone(assessment.brand_context)
    self.assertEqual(assessment.brand_context.brand_name, "TestBrand")
    self.assertIn("universal", assessment.slice_evaluations)
    self.assertEqual(len(assessment.slice_evaluations["universal"]), 1)
    self.assertEqual(
        assessment.slice_evaluations["universal"][0].feature.id,
        "test_feature",
    )
    self.assertIn("start_time", assessment.metadata)
    self.assertIn("end_time", assessment.metadata)
    self.assertIn("duration_seconds", assessment.metadata)
    self.assertGreaterEqual(assessment.metadata["duration_seconds"], 0.0)

  @mock.patch.object(
      feature_configs_handler.features_configs_handler,
      "get_features_for_slice",
  )
  def test_evaluate_video_with_custom_features(
      self, mock_get_features: mock.MagicMock
  ) -> None:
    """Tests that custom evaluation features dispatch to custom detector."""
    mock_gemini_service = mock.MagicMock(
        spec=gemini_api_service.GeminiAPIService
    )
    mock_gemini_service.extract_brand_metadata.return_value = None

    mock_custom_detector = mock.MagicMock()
    mock_llm_detector = mock.MagicMock()

    custom_feat = models.VideoFeature(
        id="custom_feat",
        name="Custom Feature",
        category=models.VideoFeatureCategory.UNIVERSAL,
        sub_category=models.VideoFeatureSubCategory.ATTRACT,
        evaluation_criteria="Custom criteria",
        evaluation_function="detect_custom",
    )
    llm_feat = models.VideoFeature(
        id="llm_feat",
        name="LLM Feature",
        category=models.VideoFeatureCategory.UNIVERSAL,
        sub_category=models.VideoFeatureSubCategory.BRAND,
        evaluation_criteria="LLM criteria",
    )
    mock_get_features.return_value = [custom_feat, llm_feat]

    custom_eval = models.FeatureEvaluation(
        feature=custom_feat,
        is_detected=True,
        confidence_score=1.0,
        rationale="Custom code passed",
        evidence="Found via heuristic",
    )
    llm_eval = models.FeatureEvaluation(
        feature=llm_feat,
        is_detected=False,
        confidence_score=0.8,
        rationale="Not present",
        evidence="None",
    )

    mock_custom_detector.evaluate_feature.return_value = custom_eval
    mock_llm_detector.evaluate_features.return_value = [llm_eval]

    service = video_evaluation_service.VideoEvaluationService(
        detector_custom=mock_custom_detector,
        detector_llm=mock_llm_detector,
    )

    brand_ctx = configuration.BrandContext(
        brand_name="GivenBrand",
        branded_products=["Product X"],
    )
    req = configuration.EvaluationRequest(
        video_uris=["gs://bucket/test.mp4"],
        gcp_config=configuration.GCPConfig(project_id="test-proj"),
        gemini_config=configuration.GeminiConfig(api_key="test-key"),
        slices=["universal"],
        extract_brand_metadata=False,
        brand_context=brand_ctx,
    )

    assessment = service.evaluate_video(
        request=req,
        video_uri="gs://bucket/test.mp4",
        gemini_service=mock_gemini_service,
    )

    mock_custom_detector.evaluate_feature.assert_called_once()
    mock_llm_detector.evaluate_features.assert_called_once()
    self.assertEqual(assessment.brand_name, "GivenBrand")
    self.assertEqual(len(assessment.slice_evaluations["universal"]), 2)


if __name__ == "__main__":
  unittest.main()
