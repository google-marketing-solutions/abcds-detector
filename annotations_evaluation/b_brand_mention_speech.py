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

### REMOVE FOR COLAB - START

from helpers.annotations_helpers import (
    find_elements_in_transcript,
    get_speech_annotations,
)

from input_parameters import brand_variations

### REMOVE FOR COLAB - END

# @title 8 & 9) Brand: Brand Mention (Speech) & Brand Mention (Speech) (First 5 seconds)

# @markdown **Features:**

# @markdown **Brand Mention (Speech):** The brand name is heard in the audio or speech at any time in the video.

# @markdown **Brand Mention (Speech) (First 5 seconds):** The brand name is heard in the audio or speech in the first 5 seconds (up to 4.99s) of the video.


def detect_brand_mention_speech(
    feature_name: str,
    bucket: any,
    annotation_location: str,
) -> bool:
    """Detect Brand Mention (Speech)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        brand_mention_speech: brand mention speech evaluation
    """
    brand_mention_speech, na = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {brand_mention_speech}")

    return brand_mention_speech


def detect_brand_mention_speech_1st_5_secs(
    feature_name: str,
    bucket: any,
    annotation_location: str,
) -> bool:
    """Detect Brand Mention (Speech) (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        brand_mention_speech_1st_5_secs: brand mention speech evaluation
    """
    na, brand_mention_speech_1st_5_secs = detect(feature_name, bucket, annotation_location)

    print(
        f"{feature_name}: {brand_mention_speech_1st_5_secs}"
    )

    return brand_mention_speech_1st_5_secs


def detect(
    feature_name: str,
    bucket: any,
    annotation_location: str,
) -> tuple[bool, bool]:
    """Detect Brand Mention (Speech) & Brand Mention (Speech) (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        brand_mention_speech,
        brand_mention_speech_1st_5_secs: brand mention speech evaluation
    """
    speech_annotation_results = get_speech_annotations(bucket, annotation_location)
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
            speech_transcriptions=speech_annotation_results.get(
                "speech_transcriptions"
            ),
            elements=brand_variations,
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
