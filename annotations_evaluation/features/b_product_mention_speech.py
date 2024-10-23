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

from annotations_evaluation.annotations_generation import Annotations
from helpers.annotations_helpers import find_elements_in_transcript
from helpers.generic_helpers import load_blob, get_annotation_uri
from configuration import Configuration


def detect_product_mention_speech(
    config: Configuration,
    feature_name: str, video_uri: str
) -> tuple[bool, bool]:
    """Detect Product Mention (Speech)
    Args:
        config: all the parameters 
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_mention_speech: product mention speech evaluation
    """
    product_mention_speech, na = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {product_mention_speech} \n")

    return product_mention_speech


def detect_product_mention_speech_1st_5_secs(
    config: Configuration,
    feature_name: str, video_uri: str
) -> tuple[bool, bool]:
    """Detect Product Mention (Speech)
    Args:
        config: all the parameters 
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_mention_speech_1st_5_secs: product mention speech evaluation
    """
    na, product_mention_speech_1st_5_secs = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {product_mention_speech_1st_5_secs} \n")

    return product_mention_speech_1st_5_secs


def detect(config: Configuration, feature_name: str, video_uri: str) -> tuple[bool, bool]:
    """Detect Product Mention (Speech) & Product Mention (Speech) (First 5 seconds)
    Args:
        config: all the parameters 
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_mention_speech,
        product_mention_speech_1st_5_secs: product mention speech evaluation
    """
    annotation_uri = f"{get_annotation_uri(config, video_uri)}{Annotations.SPEECH_ANNOTATIONS.value}.json"
    speech_annotation_results = load_blob(annotation_uri)

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
            config,
            speech_transcriptions=speech_annotation_results.get(
                "speech_transcriptions"
            ),
            elements=config.branded_products,
            elements_categories=config.branded_products_categories,
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
