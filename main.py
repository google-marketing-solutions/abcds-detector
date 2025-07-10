#!/usr/bin/env python3

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

"""Module to execute the ABCD Detector Assessment"""

import time
import traceback
import logging
import models
import utils
from annotations_evaluation import annotations_generation
from helpers import generic_helpers
from configuration import Configuration
from creative_providers import creative_provider_proto
from creative_providers import creative_provider_registry
from evaluation_services import video_evaluation_service


def execute_abcd_assessment_for_videos(config: Configuration):
  """Execute ABCD Assessment for all brand videos retrieved by the Creative Provider"""

  creative_provider: creative_provider_proto.CreativeProviderProto = (
      creative_provider_registry.provider_factory.get_provider(
          config.creative_provider_type.value
      )
  )

  video_uris = creative_provider.get_creative_uris(config)

  for video_uri in video_uris:

    print(f"\n\nProcessing ABCD Assessment for video {video_uri}... \n")

    # Generate video annotations for custom features. Annotations are supported only for GCS providers
    if config.creative_provider_type == models.CreativeProviderType.GCS:
      annotations_generation.generate_video_annotations(config, video_uri)

    # Full ABCD features require 1st_5_secs videos only for GCS providers
    if (
        config.run_full_abcd
        and config.creative_provider_type == models.CreativeProviderType.GCS
    ):
      generic_helpers.trim_video(config, video_uri)

    # Execute ABCD Assessment
    full_abcd_evaluated_features: models.FeatureEvaluation = []
    shorts_evaluated_features: models.FeatureEvaluation = []

    if config.run_full_abcd:
      full_abcd_evaluated_features = (
          video_evaluation_service.video_evaluation_service.evaluate_features(
              config=config,
              video_uri=video_uri,
              features_category=models.VideoFeatureCategory.FULL_ABCD,
          )
      )

    if config.run_shorts:
      shorts_evaluated_features = (
          video_evaluation_service.video_evaluation_service.evaluate_features(
              config=config,
              video_uri=video_uri,
              features_category=models.VideoFeatureCategory.SHORTS,
          )
      )

    video_assessment: models.VideoAssessment = models.VideoAssessment(
        brand_name=config.brand_name,
        video_uri=video_uri,
        full_abcd_evaluated_features=full_abcd_evaluated_features,
        shorts_evaluated_features=shorts_evaluated_features,
        config=config,
    )

    # Print assessments for Full ABCD and Shorts and store results
    if len(full_abcd_evaluated_features) > 0:
      generic_helpers.print_abcd_assessment(
          video_assessment.brand_name,
          video_assessment.video_uri,
          full_abcd_evaluated_features,
      )
    else:
      logging.info(
          "There are not Full ABCD evaluated features results to display."
      )
    if len(shorts_evaluated_features) > 0:
      generic_helpers.print_abcd_assessment(
          video_assessment.brand_name,
          video_assessment.video_uri,
          shorts_evaluated_features,
      )
    else:
      logging.info(
          "There are not Shorts evaluated features results to display."
      )

    if config.bq_table_name:
      generic_helpers.store_in_bq(config, video_assessment)

    # Remove local version of video files
    generic_helpers.remove_local_video_files()


def main(arg_list: list[str] | None = None) -> None:
  """Main ABCD Assessment execution. See docstring and args.

  Args:
    arg_list: A list of command line arguments

  """

  try:
    args = utils.parse_args(arg_list)

    config = utils.build_abcd_params_config(args)

    if utils.invalid_brand_metadata(config):
      logging.error(
          "The Extract Brand Metadata option is disabled and no brand details"
          " were defined. \n"
      )
      logging.error("Please enable the option or define brand details. \n")
      return

    start_time = time.time()
    logging.info("Starting ABCD assessment... \n")

    if config.video_uris:
      execute_abcd_assessment_for_videos(config)
      logging.info("Finished ABCD assessment. \n")
    else:
      logging.info("There are no videos to process. \n")

    logging.info(
        "ABCD assessment took - %s mins. - \n", (time.time() - start_time) / 60
    )
  except Exception as ex:
    logging.error("ERROR: %s", ex)
    traceback.print_exc()


if __name__ == "__main__":
  main()
