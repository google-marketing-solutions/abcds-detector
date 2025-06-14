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

"""Module to detect Brand Mention (Speech) & Brand Mention (Speech) (First 5 seconds)
Annotations used:
    1.Speech annotations to detect the brand in the audio of the video
"""

from annotations_evaluation.annotations_generation import Annotations
from gcp_api_services.gcs_api_service import gcs_api_service
from helpers.annotations_helpers import find_elements_in_transcript
from configuration import Configuration


def detect_brand_mention_speech(
    config: Configuration, feature_name: str, video_uri: str
) -> bool:
    """Detect Brand Mention (Speech)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        brand_mention_speech: brand mention speech evaluation
    """
    brand_mention_speech, na = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {brand_mention_speech} \n")

    return brand_mention_speech


def detect_brand_mention_speech_1st_5_secs(
    config: Configuration, feature_name: str, video_uri: str
) -> bool:
    """Detect Brand Mention (Speech) (First 5 seconds)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        brand_mention_speech_1st_5_secs: brand mention speech evaluation
    """
    na, brand_mention_speech_1st_5_secs = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {brand_mention_speech_1st_5_secs} \n")

    return brand_mention_speech_1st_5_secs


def detect(
    config: Configuration, feature_name: str, video_uri: str
) -> tuple[bool, bool]:
    """Detect Brand Mention (Speech) & Brand Mention (Speech) (First 5 seconds)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        brand_mention_speech,
        brand_mention_speech_1st_5_secs: brand mention speech evaluation
    """

    annotation_uri = f"{gcs_api_service.get_annotation_uri(config, video_uri)}{Annotations.SPEECH_ANNOTATIONS.value}.json"
    speech_annotation_results = gcs_api_service.load_blob(annotation_uri)

    # Feature Brand Mention (Speech)
    brand_mention_speech = False

    # Feature Brand Mention (Speech) (First 5 seconds)
    brand_mention_speech_1st_5_secs = False

    # Video API: Evaluate brand_mention_speech and brand_mention_speech_1st_5_secs
    if "speech_transcriptions" in speech_annotation_results:
        # Video API: Evaluate brand_mention & brand_mention_speech_1st_5_secs
        (
            brand_mention_speech,
            brand_mention_speech_1st_5_secs,
        ) = find_elements_in_transcript(
            config,
            speech_transcriptions=speech_annotation_results.get(
                "speech_transcriptions"
            ),
            elements=config.brand_variations,
            elements_categories=[],
            apply_condition=False,
        )
    else:
        print(
            f"No Speech annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    return (
        brand_mention_speech,
        brand_mention_speech_1st_5_secs,
    )
