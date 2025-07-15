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

"""Module to run the ABCD assessment and return the results."""

import logging
from configuration import Configuration
import models
from annotations_evaluation import annotations_generation
from helpers import generic_helpers
from creative_providers import creative_provider_proto
from creative_providers import creative_provider_registry
from evaluation_services import video_evaluation_service


def execute_abcd_assessment_for_videos(config: Configuration) -> list[models.VideoAssessment]:
    """Executes ABCD Assessment for all videos in the config and returns the results."""
    creative_provider: creative_provider_proto.CreativeProviderProto = (
        creative_provider_registry.provider_factory.get_provider(
            config.creative_provider_type.value
        )
    )

    video_uris = creative_provider.get_creative_uris(config)
    assessments = []

    for video_uri in video_uris:
        logging.info(f"\n\nProcessing ABCD Assessment for video {video_uri}... \n")

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

        video_assessment = models.VideoAssessment(
            brand_name=config.brand_name,
            video_uri=video_uri,
            full_abcd_evaluated_features=full_abcd_evaluated_features,
            shorts_evaluated_features=shorts_evaluated_features,
            config=config,
        )
        assessments.append(video_assessment)

    # Remove local version of video files
    generic_helpers.remove_local_video_files()

    return assessments
