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
from annotations_evaluation.annotations_generation import generate_video_annotations
from helpers.generic_helpers import (
    print_abcd_assessment,
    trim_video,
    store_in_bq,
    remove_local_video_files,
)
from configuration import Configuration
from models import VideoFeatureCategory
from gcp_api_services.gemini_api_service import LLMParameters
from gcp_api_services.bigquery_api_service import BigQueryAPIService
from creative_providers.creative_provider_proto import CreativeProviderProto
from creative_providers.creative_provider_registry import provider_factory
from evaluation_services.video_evaluation_service import video_evaluation_service
from utils import parse_args, build_abcd_params_config


def execute_abcd_assessment_for_videos(config: Configuration):
    """Execute ABCD Assessment for all brand videos in GCS"""

    creative_provider: CreativeProviderProto = provider_factory.get_provider(
        config.creative_provider_type.value
    )

    brand_assessment = {
        "brand_name": config.brand_name,
        "video_assessments": [],
        "llm_params": config.llm_params.__dict__,
    }

    video_uris = creative_provider.get_creative_uris(config.video_uris)

    for video_uri in video_uris:
        print(f"\n\nProcessing ABCD Assessment for video {video_uri}... \n")

        # Generate video annotations for custom features
        generate_video_annotations(config, video_uri)

        if config.run_full_abcd:
            # 1) Full ABCD features require 1st_5_secs videos
            trim_video(config, video_uri)

        # 3) Execute ABCD Assessment
        video_assessment = {
            "video_uri": video_uri,
        }

        if config.run_full_abcd:
            video_evaluation_service.evaluate_features(
                config=config,
                video_uri=video_uri,
                features_category=VideoFeatureCategory.FULL_ABCD,
            )

        if config.run_shorts:
            video_evaluation_service.evaluate_features(
                config=config,
                video_uri=video_uri,
                features_category=VideoFeatureCategory.SHORTS,
            )

        print_abcd_assessment(config.brand_name, video_assessment)
        brand_assessment.get("video_assessments").append(video_assessment)

        if config.bq_table_name:
            bq_service = BigQueryAPIService(config.project_id)
            store_in_bq(config, bq_service, video_assessment, config.llm_params)

        # Remove local version of video files
        remove_local_video_files()

    if config.assessment_file:
        with open(config.assessment_file, "w", encoding="utf-8") as f:
            json.dump(brand_assessment, f, ensure_ascii=False, indent=4)

    return brand_assessment


def main(arg_list: list[str] | None = None) -> None:
    """Main ABCD Assessment execution. See docstring and args.

    Args:
      arg_list: A list of command line arguments

    """

    try:
        args = parse_args(arg_list)

        config = build_abcd_params_config(args)

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
