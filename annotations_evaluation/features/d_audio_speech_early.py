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

"""Module to detect Direct: Audio Speech Early
Annotations used:
    1. Speech annotations to check for audio speech early
"""

from annotations_evaluation.annotations_generation import Annotations
from gcp_api_services.gcs_api_service import gcs_api_service
from helpers.annotations_helpers import calculate_time_seconds
from configuration import Configuration


def detect_audio_speech_early_1st_5_secs(
    config: Configuration, feature_name: str, video_uri: str
) -> bool:
    """Detect Audio Early (First 5 seconds)
    Args:
        config: all the parameters
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        audio_speech_early: audio early evaluation
    """

    annotation_uri = f"{gcs_api_service.get_annotation_uri(config, video_uri)}{Annotations.SPEECH_ANNOTATIONS.value}.json"
    speech_annotation_results = gcs_api_service.load_blob(annotation_uri)

    # Feature Audio Early (First 5 seconds)
    audio_speech_early_1st_5_secs = False

    # Video API: Evaluate audio_speech_early_feature
    if "speech_transcriptions" in speech_annotation_results:
        # Video API: Evaluate audio_speech_early_feature
        for speech_transcription in speech_annotation_results.get(
            "speech_transcriptions"
        ):
            for alternative in speech_transcription.get("alternatives"):
                # Check confidence against user defined threshold
                if (
                    alternative
                    and alternative.get("confidence") >= config.confidence_threshold
                ):
                    # For 1st 5 secs, check elements and elements_categories in words
                    # since only the words[] contain times
                    words = alternative.get("words") if "words" in alternative else []
                    for word_info in words:
                        start_time_secs = calculate_time_seconds(
                            word_info, "start_time"
                        )
                        if start_time_secs <= config.early_time_seconds:
                            audio_speech_early_1st_5_secs = True
    else:
        print(
            f"No Speech annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {audio_speech_early_1st_5_secs} \n")

    return audio_speech_early_1st_5_secs
