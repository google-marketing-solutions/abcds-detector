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

"""Module to detect Brand: Product Mention (Text) & Product Mention (Text) (First 5 seconds)
Annotations used:
    1. Text annotations to identify products in text overlays (text)
"""

from annotations_evaluation.annotations_generation import Annotations
from gcp_api_services.gcs_api_service import gcs_api_service
from helpers.annotations_helpers import detected_text_in_first_5_seconds
from configuration import Configuration


def detect_product_mention_text(
    config: Configuration, feature_name: str, video_uri: str
) -> bool:
    """Detect Product Mention (Text)
    Args:
        config: all the parameters
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_mention_text: product mention text evaluation
    """
    product_mention_text, na = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {product_mention_text} \n")

    return product_mention_text


def detect_product_mention_text_1st_5_secs(
    config: Configuration, feature_name: str, video_uri: str
) -> bool:
    """Product Mention (Text) (First 5 seconds)
    Args:
        config: all the parameters
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_mention_text_1st_5_secs: product mention text evaluation
    """
    na, product_mention_text_1st_5_secs = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {product_mention_text_1st_5_secs} \n")

    return product_mention_text_1st_5_secs


def detect(
    config: Configuration, feature_name: str, video_uri: str
) -> tuple[bool, bool]:
    """Detect Product Mention (Text) & Product Mention (Text) (First 5 seconds)
    Args:
        config: all the parameters
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_mention_text,
        product_mention_text_1st_5_secs: product mention text evaluation
    """

    annotation_uri = f"{gcs_api_service.get_annotation_uri(config, video_uri)}{Annotations.GENERIC_ANNOTATIONS.value}.json"
    text_annotation_results = gcs_api_service.load_blob(annotation_uri)

    # Feature Product Mention (Text)
    product_mention_text = False

    # Feature Product Mention (Text) (First 5 seconds)
    product_mention_text_1st_5_secs = False

    # Video API: Evaluate product_mention_text_feature and product_mention_text_1st_5_secs_feature
    if "text_annotations" in text_annotation_results:
        # Video API: Evaluate product_mention_text_feature and product_mention_text_1st_5_secs_feature
        for text_annotation in text_annotation_results.get("text_annotations"):
            text = text_annotation.get("text")
            found_branded_products = [
                prod for prod in config.branded_products if prod.lower() in text.lower()
            ]
            found_branded_products_categories = [
                prod
                for prod in config.branded_products_categories
                if prod.lower() in text.lower()
            ]
            if (
                len(found_branded_products) > 0
                or len(found_branded_products_categories) > 0
            ):
                product_mention_text = True
                pmt_1st_5_secs, frame = detected_text_in_first_5_seconds(
                    config, text_annotation
                )
                if pmt_1st_5_secs:
                    product_mention_text_1st_5_secs = True
    else:
        print(
            f"No Text annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    return (
        product_mention_text,
        product_mention_text_1st_5_secs,
    )
