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

"""Module to detect Brand: Product Mention (Speech), Product Mention (Speech) (First 5 seconds)
Annotations used:
    1. Speech annotations to identify products in audio (speech)
"""

### REMOVE FOR COLAB - START

from input_parameters import branded_products, branded_products_categories

from helpers.annotations_helpers import (
    find_elements_in_transcript,
    get_speech_annotations,
)

### REMOVE FOR COLAB - END


# @title 14, 15) Brand: Product Mention (Speech), Product Mention (Speech) (First 5 seconds)

# @markdown **Features:**

# @markdown **Product Mention (Speech):** The branded product names or generic product categories are heard or mentioned in the audio or speech at any time in the video.

# @markdown **Product Mention (Speech) (First 5 seconds):** The branded product names or generic product categories are heard or mentioned in the audio or speech in the first 5 seconds (up to 4.99s) of the video.


def detect_product_mention_speech(
    feature_name: str, bucket: any, annotation_location: str
) -> tuple[bool, bool]:
    """Detect Product Mention (Speech)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        product_mention_speech: product mention speech evaluation
    """
    product_mention_speech, na = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {product_mention_speech}")

    return product_mention_speech


def detect_product_mention_speech_1st_5_secs(
    feature_name: str, bucket: any, annotation_location: str
) -> tuple[bool, bool]:
    """Detect Product Mention (Speech)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        product_mention_speech_1st_5_secs: product mention speech evaluation
    """
    na, product_mention_speech_1st_5_secs = detect(
        feature_name, bucket, annotation_location
    )

    print(f"{feature_name}: {product_mention_speech_1st_5_secs}")

    return product_mention_speech_1st_5_secs


def detect(
    feature_name: str, bucket: any, annotation_location: str
) -> tuple[bool, bool]:
    """Detect Product Mention (Speech) & Product Mention (Speech) (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        product_mention_speech,
        product_mention_speech_1st_5_secs: product mention speech evaluation
    """
    speech_annotation_results = get_speech_annotations(bucket, annotation_location)
    # Feature Product Mention (Speech)
    product_mention_speech = False

    # Feature Product Mention (Speech) (First 5 seconds)
    product_mention_speech_1st_5_secs = False

    # Video API: Evaluate product_mention_speech_feature and product_mention_speech_1st_5_secs_feature
    if "speech_transcriptions" in speech_annotation_results:
        # Video API: Evaluate product_mention_speech & product_mention_speech_1st_5_secs
        (
            product_mention_speech,
            product_mention_speech_1st_5_secs,
        ) = find_elements_in_transcript(
            speech_transcriptions=speech_annotation_results.get(
                "speech_transcriptions"
            ),
            elements=branded_products,
            elements_categories=branded_products_categories,
            apply_condition=False,
        )
    else:
        print(
            f"No Speech annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    return (
        product_mention_speech,
        product_mention_speech_1st_5_secs,
    )
