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

"""Service that handles ABCD video evaluations across slices and modes."""

import datetime
import functools
import logging

import configuration
from custom_evaluation import custom_detector
from features_repository import feature_configs_handler
from gcp_api_services import gemini_api_service
from helpers import generic_helpers
from llm_evaluation import llm_detector
import models

logger = logging.getLogger("abcd_detector")


class VideoEvaluationService:
  """Service that orchestrates ABCD video evaluations in a 4-step pipeline."""

  def __init__(
      self,
      detector_custom: custom_detector.CustomDetector | None = None,
      detector_llm: llm_detector.LLMDetector | None = None,
  ) -> None:
    """Initializes the VideoEvaluationService.

    Args:
      detector_custom: Optional CustomDetector for custom evaluation functions.
      detector_llm: Optional LLMDetector for Gemini LLM evaluations.
    """
    self.custom_detector = detector_custom or custom_detector.CustomDetector()
    self.llm_detector = detector_llm or llm_detector.LLMDetector()

  def evaluate_video(
      self,
      request: configuration.EvaluationRequest,
      video_uri: str,
      gemini_service: gemini_api_service.GeminiAPIService,
  ) -> models.VideoAssessment:
    """Evaluates all requested slices for a single video using a pipeline.

    Args:
      request: EvaluationRequest specifying slices, mode, and configs.
      video_uri: Cloud Storage URI of the video to evaluate.
      gemini_service: Client service instance for calling Gemini.

    Returns:
      VideoAssessment containing evaluation results grouped by slice.
    """
    start_time = datetime.datetime.now(datetime.timezone.utc)
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info(
        "Starting ABCD evaluation for video: %s (Start: %s)",
        video_uri,
        start_str,
    )

    # Step 1: Resolve Brand Context
    if request.extract_brand_metadata:
      brand_context = gemini_service.extract_brand_metadata(video_uri)
    else:
      brand_context = request.brand_context

    slice_evaluations: dict[str, list[models.FeatureEvaluation]] = {}

    for slice_name in request.slices:
      slice_start_time = datetime.datetime.now(datetime.timezone.utc)
      slice_start_str = slice_start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
      logger.info(
          "Processing slice '%s' for video: %s (Start: %s)",
          slice_name,
          video_uri,
          slice_start_str,
      )

      # Step 2: Filter features for this slice
      slice_filter = None
      if (
          request.features_to_evaluate
          and slice_name in request.features_to_evaluate
      ):
        slice_filter = request.features_to_evaluate[slice_name]

      features = (
          feature_configs_handler.features_configs_handler
          .get_features_for_slice(
              slice_name=slice_name,
              features_filter=slice_filter,
          )
      )

      if not features:
        logger.info(
            "No active features found for slice '%s'. Skipping.", slice_name
        )
        slice_evaluations[slice_name] = []
        continue

      # Step 3: Partition features into Custom and Gemini groups
      custom_features: list[models.VideoFeature] = []
      gemini_features: list[models.VideoFeature] = []

      for f in features:
        if f.evaluation_function:
          custom_features.append(f)
        else:
          gemini_features.append(f)

      # Step 4: Build dispatch tasks
      tasks = []

      # 4a. Custom features: evaluated via registered custom functions
      for cf in custom_features:
        func = functools.partial(
            self.custom_detector.evaluate_feature,
            gemini_config=request.gemini_config,
            feature_config=cf,
            video_uri=video_uri,
            brand_context=brand_context,
        )
        tasks.append(func)

      # 4b. Gemini features: evaluated in BULK or INDIVIDUAL mode
      if gemini_features:
        if request.execution_mode == configuration.ExecutionMode.BULK:
          func = functools.partial(
              self.llm_detector.evaluate_features,
              gemini_service=gemini_service,
              video_uri=video_uri,
              feature_configs=gemini_features,
              slice_name=slice_name,
              brand_context=brand_context,
          )
          tasks.append(func)
        else:
          for gf in gemini_features:
            func = functools.partial(
                self.llm_detector.evaluate_features,
                gemini_service=gemini_service,
                video_uri=video_uri,
                feature_configs=[gf],
                slice_name=slice_name,
                brand_context=brand_context,
            )
            tasks.append(func)

      # Execute parallel tasks
      logger.info(
          "Dispatching %d evaluation task(s) for slice '%s'...",
          len(tasks),
          slice_name,
      )
      task_results = generic_helpers.execute_tasks_in_parallel(tasks)

      # Step 5: Aggregate results
      evaluations_for_slice: list[models.FeatureEvaluation] = []

      for result in task_results:
        if isinstance(result, list):
          evaluations_for_slice.extend(
              item
              for item in result
              if isinstance(item, models.FeatureEvaluation)
          )
        elif isinstance(result, models.FeatureEvaluation):
          evaluations_for_slice.append(result)

      # Sort for consistent presentation
      evaluations_for_slice.sort(
          key=lambda e: (e.feature.sub_category.value, e.feature.id)
      )
      slice_evaluations[slice_name] = evaluations_for_slice

      slice_end_time = datetime.datetime.now(datetime.timezone.utc)
      slice_end_str = slice_end_time.strftime("%Y-%m-%d %H:%M:%S UTC")
      slice_duration = (slice_end_time - slice_start_time).total_seconds()
      logger.info(
          "Slice '%s' completed in %.2fs (Start: %s, End: %s).",
          slice_name,
          slice_duration,
          slice_start_str,
          slice_end_str,
      )

    end_time = datetime.datetime.now(datetime.timezone.utc)
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    total_duration = (end_time - start_time).total_seconds()
    logger.info(
        "Completed ABCD evaluation for video: %s in %.2fs (Start: %s, End:"
        " %s).",
        video_uri,
        total_duration,
        start_str,
        end_str,
    )

    timing_metadata = {
        "start_time": start_str,
        "end_time": end_str,
        "duration_seconds": round(total_duration, 2),
    }

    brand_name = brand_context.brand_name if brand_context else ""
    return models.VideoAssessment(
        brand_name=brand_name,
        video_uri=video_uri,
        slice_evaluations=slice_evaluations,
        metadata=timing_metadata,
        brand_context=brand_context,
    )
