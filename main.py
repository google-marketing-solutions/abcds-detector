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
from annotations_evaluation.annotations_generation import generate_video_annotations
from helpers.generic_helpers import (
    print_abcd_assessment,
    trim_video,
    store_in_bq,
    remove_local_video_files,
)
from configuration import Configuration
from models import VideoFeatureCategory, FeatureEvaluation, VideoAssessment
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

    video_uris = creative_provider.get_creative_uris(config.video_uris)

    for video_uri in video_uris:

        if not config.brand_name:
            pass
            # Extract video metadata
            # config.brand_name =

        print(f"\n\nProcessing ABCD Assessment for video {video_uri}... \n")

        # Generate video annotations for custom features
        generate_video_annotations(config, video_uri)

        if config.run_full_abcd:
            # 1) Full ABCD features require 1st_5_secs videos
            trim_video(config, video_uri)

        # 3) Execute ABCD Assessment

        evaluated_features: FeatureEvaluation = []

        if config.run_full_abcd:
            full_abcd_evaluated_features = video_evaluation_service.evaluate_features(
                config=config,
                video_uri=video_uri,
                features_category=VideoFeatureCategory.FULL_ABCD,
            )
            evaluated_features.extend(full_abcd_evaluated_features)

        if config.run_shorts:
            shorts_evaluated_features = video_evaluation_service.evaluate_features(
                config=config,
                video_uri=video_uri,
                features_category=VideoFeatureCategory.SHORTS,
            )
            evaluated_features.extend(shorts_evaluated_features)

        video_assessment: VideoAssessment = VideoAssessment(
            brand_name=config.brand_name,
            video_uri=video_uri,
            evaluated_features=evaluated_features,
            config=config,
        )

        # Print assessment and store results
        print_abcd_assessment(config.brand_name, video_assessment)

        if config.bq_table_name:
            bq_service = BigQueryAPIService(config.project_id)
            store_in_bq(config, bq_service, video_assessment)

        # Remove local version of video files
        remove_local_video_files()


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
