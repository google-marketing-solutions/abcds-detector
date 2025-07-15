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

import json
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


def execute_abcd_assessment_for_videos(config_file: str):
  """Execute ABCD Assessment for all brand videos retrieved by the Creative Provider"""

  with open(config_file, 'r') as f:
    config_data = json.load(f)

  config = Configuration()
  config.set_parameters(
      project_id=config_data['project_details']['project_id'],
      project_zone=config_data['project_details']['project_zone'],
      bucket_name=config_data['project_details']['bucket_name'],
      knowledge_graph_api_key=config_data['project_details']['knowledge_graph_api_key'],
      bigquery_dataset=config_data['project_details']['bigquery_dataset'],
      bigquery_table=config_data['project_details']['bigquery_table'],
      assessment_file=config_data['project_details']['assessment_file'],
      use_annotations=config_data['project_details']['use_annotations'],
      use_llms=config_data['project_details']['use_llms'],
      verbose=config_data['project_details']['verbose']
  )
  config.set_brand_details(
      brand_name=config_data['brand_details']['brand_name'],
      brand_variations=config_data['brand_details']['brand_variations'],
      products=config_data['brand_details']['products'],
      products_categories=config_data['brand_details']['products_categories'],
      call_to_actions=config_data['brand_details']['call_to_actions']
  )
  config.set_annotation(
      early_time_seconds=config_data['abcd_framework_details']['early_time_seconds'],
      confidence_threshold=config_data['abcd_framework_details']['confidence_threshold'],
      face_surface_threshold=config_data['abcd_framework_details']['face_surface_threshold'],
      logo_size_threshold=config_data['abcd_framework_details']['logo_size_threshold'],
      avg_shot_duration_seconds=config_data['abcd_framework_details']['avg_shot_duration_seconds'],
      dynamic_cutoff_ms=config_data['abcd_framework_details']['dynamic_cutoff_ms']
  )
  config.set_model(
      llm_name=config_data['llm_configuration']['llm_name'],
      video_size_limit_mb=config_data['llm_configuration']['video_size_limit_mb'],
      max_output_tokens=config_data['llm_configuration']['max_output_tokens'],
      temperature=config_data['llm_configuration']['temperature'],
      top_p=config_data['llm_configuration']['top_p'],
      top_k=config_data['llm_configuration']['top_k']
  )
  config.set_videos(config_data['videos'])
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

    if args.config_file:
        execute_abcd_assessment_for_videos(args.config_file)
    else:
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
