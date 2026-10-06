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

"""Module to evaluate and detect ABCD features using Gemini."""

import datetime
import logging

import configuration
from gcp_api_services import gemini_api_service
import models
from prompts import prompt_generator

logger = logging.getLogger("abcd_detector")


class LLMDetector:
  """Class to evaluate and detect features using the Gemini API."""

  def evaluate_features(
      self,
      gemini_service: gemini_api_service.GeminiAPIService,
      video_uri: str,
      feature_configs: list[models.VideoFeature],
      slice_name: str,
      brand_context: configuration.BrandContext | None = None,
  ) -> list[models.FeatureEvaluation]:
    """Evaluates a batch or single feature for a video slice via Gemini.

    Args:
      gemini_service: Client service instance for calling the Gemini API.
      video_uri: Cloud Storage URI of the video to analyze.
      feature_configs: List of VideoFeature definitions to evaluate.
      slice_name: Name of the ABCD slice (e.g., 'universal', 'shorts').
      brand_context: Optional brand metadata for augmented prompts.

    Returns:
      List of FeatureEvaluation objects populated with evaluation results.
    """
    if not feature_configs:
      return []

    start_time = datetime.datetime.now(datetime.timezone.utc)
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info(
        "Evaluating %d feature(s) for slice '%s' on video: %s (Start: %s)",
        len(feature_configs),
        slice_name,
        video_uri,
        start_str,
    )

    prompt_config = prompt_generator.prompt_generator.get_abcds_prompt_config(
        features=feature_configs,
        brand_context=brand_context,
    )

    raw_evaluations = gemini_service.call_gemini_vertex_ai(
        video_uri=video_uri,
        prompt_config=prompt_config,
        response_schema=models.VIDEO_EVAL_SCHEMA,
    )

    end_time = datetime.datetime.now(datetime.timezone.utc)
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    duration = (end_time - start_time).total_seconds()
    logger.info(
        "Completed Gemini evaluation for slice '%s' on video: %s in %.2fs "
        "(Start: %s, End: %s)",
        slice_name,
        video_uri,
        duration,
        start_str,
        end_str,
    )

    features_by_id = {f.id: f for f in feature_configs}
    evaluations: list[models.FeatureEvaluation] = []

    for item in raw_evaluations:
      feature_def = features_by_id.get(item.get("id"))
      if not feature_def:
        continue

      eval_obj = models.FeatureEvaluation(
          feature=feature_def,
          is_detected=item.get("is_detected", False),
          confidence_score=item.get("confidence_score", 0.0),
          rationale=item.get("rationale", ""),
          evidence=item.get("evidence", ""),
          strengths=item.get("strengths", ""),
          weaknesses=item.get("weaknesses", ""),
          recommended_actions=item.get("recommended_actions", ""),
          first_appearance_timestamp=item.get("first_appearance_timestamp"),
          feature_density_score=item.get("feature_density_score"),
          feature_quality_score=item.get("feature_quality_score"),
          feature_specifics=item.get("feature_specifics"),
      )
      evaluations.append(eval_obj)

    return evaluations
