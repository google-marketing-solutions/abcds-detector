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

### REMOVE FOR COLAB - START
from input_parameters import (
    early_time_seconds,
    confidence_threshold,
)

from helpers.annotations_helpers import calculate_time_seconds, get_speech_annotations

### REMOVE FOR COLAB - START

# @title 20) Direct: Audio Speech Early

# @markdown **Features**

# @markdown **Audio Early (First 5 seconds):** Speech is detected in the audio in the first 5 seconds (up to 4.99s) of the video


def detect_audio_speech_early_1st_5_secs(
    feature_name: str, bucket: any, annotation_location: str
) -> bool:
    """Detect Audio Early (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        audio_speech_early: audio early evaluation
    """
    speech_annotation_results = get_speech_annotations(bucket, annotation_location)
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
                    and alternative.get("confidence") >= confidence_threshold
                ):
                    # For 1st 5 secs, check elements and elements_categories in words
                    # since only the words[] contain times
                    words = alternative.get("words") if "words" in alternative else []
                    for word_info in words:
                        start_time_secs = calculate_time_seconds(
                            word_info, "start_time"
                        )
                        if start_time_secs <= early_time_seconds:
                            audio_speech_early_1st_5_secs = True
    else:
        print(
            f"No Speech annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {audio_speech_early_1st_5_secs}")

    return audio_speech_early_1st_5_secs
