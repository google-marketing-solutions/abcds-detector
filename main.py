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

"""Main module to execute the ABCD Detector Assessment."""

import datetime

import configuration
from creative_providers import gcs_creative_provider
from evaluation_services import video_evaluation_service
from gcp_api_services import gemini_api_service
from helpers import generic_helpers
import models
import utils

logger = generic_helpers.setup_logger()


def execute_abcd_assessment_for_videos(
    request: configuration.EvaluationRequest,
) -> list[models.VideoAssessment]:
  """Executes ABCD assessment for all videos specified in the request.

  Args:
    request: Validated EvaluationRequest containing videos and configurations.

  Returns:
    List of VideoAssessment results for each processed video.
  """
  gemini_service = gemini_api_service.GeminiAPIService(
      request.gcp_config, request.gemini_config
  )
  evaluation_service = video_evaluation_service.VideoEvaluationService()
  assessments: list[models.VideoAssessment] = []

  # Expand GCS folder URIs into individual video files if any folder is provided
  has_folder = any(
      u.startswith("gs://") and u.endswith("/") for u in request.video_uris
  )
  video_uris = (
      list(
          gcs_creative_provider.GCSCreativeProvider().get_creative_uris(request)
      )
      if has_folder
      else request.video_uris
  )

  for video_uri in video_uris:
    video_start = datetime.datetime.now(datetime.timezone.utc)
    start_str = video_start.strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info(
        "Processing ABCD assessment for video: %s (Start: %s)",
        video_uri,
        start_str,
    )

    assessment = evaluation_service.evaluate_video(
        request=request,
        video_uri=video_uri,
        gemini_service=gemini_service,
    )
    assessments.append(assessment)

    video_end = datetime.datetime.now(datetime.timezone.utc)
    end_str = video_end.strftime("%Y-%m-%d %H:%M:%S UTC")
    duration = (video_end - video_start).total_seconds()
    logger.info(
        "Finished ABCD assessment for video: %s in %.2fs (Start: %s, End:"
        " %s)",
        video_uri,
        duration,
        start_str,
        end_str,
    )

    # Print assessment details to console / Colab output
    for slice_name, evaluations in assessment.slice_evaluations.items():
      if evaluations:
        print("\n" + "=" * 56)
        print(f"  SLICE ASSESSMENT: {slice_name.upper()}")
        print("=" * 56)
        generic_helpers.print_abcd_assessment(
            assessment.brand_name,
            video_uri,
            evaluations,
            timing_info=assessment.metadata,
        )

    # Store in BigQuery if configured
    if request.bigquery_settings:
      generic_helpers.store_in_bq(request, assessment)

  return assessments


def main(arg_list: list[str] | None = None) -> list[models.VideoAssessment]:
  """Main entry point for command-line and programmatic ABCD execution.

  Args:
    arg_list: Optional explicit list of command-line arguments.

  Returns:
    List of completed VideoAssessment objects.
  """
  try:
    args = utils.parse_args(arg_list)
    request = utils.build_evaluation_request(args)

    start_dt = datetime.datetime.now(datetime.timezone.utc)
    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info(
        "Starting ABCD Assessment pipeline (Start: %s)...", start_str
    )

    assessments = execute_abcd_assessment_for_videos(request)

    end_dt = datetime.datetime.now(datetime.timezone.utc)
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    elapsed_secs = (end_dt - start_dt).total_seconds()
    logger.info(
        "ABCD assessment completed in %.2fs (%.2f mins) (Start: %s, End:"
        " %s).",
        elapsed_secs,
        elapsed_secs / 60.0,
        start_str,
        end_str,
    )
    return assessments

  except ValueError as err:
    logger.error("Configuration / validation error: %s", err)
    raise
  except Exception as ex:
    logger.exception("Assessment execution failed: %s", ex)
    raise


if __name__ == "__main__":
  main()
