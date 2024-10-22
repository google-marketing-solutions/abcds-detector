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

"""Module to detect Brand: Product Visuals & Product Visuals (First 5 seconds)
Annotations used:
    1. Label annotations to identify products (objects)
"""

from annotations_evaluation.annotations_generation import Annotations
from helpers.annotations_helpers import calculate_time_seconds
from helpers.generic_helpers import load_blob, get_annotation_uri
from helpers.generic_helpers import get_knowledge_graph_entities
from configuration import Configuration


def detect_product_visuals(config: Configuration, feature_name: str, video_uri: str) -> bool:
    """Detect Product Visuals
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_visuals: product visuals evaluation
    """
    product_visuals, na = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {product_visuals} \n")

    return product_visuals


def detect_product_visuals_1st_5_secs(config: Configuration, feature_name: str, video_uri: str) -> bool:
    """Detect Product Visuals (First 5 seconds)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_visuals_1st_5_secs: product visuals evaluation
    """
    na, product_visuals_1st_5_secs = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {product_visuals_1st_5_secs} \n")

    return product_visuals_1st_5_secs


def detect_annotation(
    entity: dict,
    segment: dict,
    branded_products_kg_entities: dict,
    branded_products: list[str],
    branded_products_categories: list[str],
):
    """Detect Product Visuals & Product Visuals (First 5 seconds)
    Args:
        entity: entity found in annotations
        segment: segment of the video
        branded_products_kg_entities
        branded_products: list of products
        branded_products_categories: list of products categories
    Returns:
        product_visuals,
        product_visuals_1st_5_secs: evaluation
    """
    product_visuals = False
    product_visuals_1st_5_secs = False
    entity_id = entity.get("entity_id")
    entity_description = entity.get("description")
    # Check if any of the provided products or categories
    # match the label segment description
    found_branded_products = [
        bp for bp in branded_products if bp.lower() == entity_description.lower()
    ]
    found_branded_product_categories = [
        bp
        for bp in branded_products_categories
        if bp.lower() == entity_description.lower()
    ]
    if (
        entity_id in branded_products_kg_entities
        or len(found_branded_products) > 0
        or len(found_branded_product_categories) > 0
    ):
        # Check confidence against user defined threshold
        if segment.get("confidence") >= config.confidence_threshold:
            product_visuals = True
            start_time_secs = calculate_time_seconds(
                segment.get("segment"), "start_time_offset"
            )
            if start_time_secs <= config.early_time_seconds:
                product_visuals_1st_5_secs = True

    return product_visuals, product_visuals_1st_5_secs


def detect(config: Configuration, feature_name: str, video_uri: str) -> tuple[bool, bool]:
    """Detect Product Visuals & Product Visuals (First 5 seconds)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        product_visuals,
        product_visuals_1st_5_secs: product visuals evaluation
    """

    annotation_uri = (
        f"{get_annotation_uri(config, video_uri)}{Annotations.GENERIC_ANNOTATIONS.value}.json"
    )
    label_annotation_results = load_blob(annotation_uri)

    # Feature Product Visuals
    product_visuals = False

    # Feature Product Visuals (First 5 seconds)
    product_visuals_1st_5_secs = False

    branded_products_kg_entities = get_knowledge_graph_entities(config, config.branded_products)

    # Video API: Evaluate product_visuals_feature and product_visuals_1st_5_secs_feature
    # Check in annotations at segment level
    if "segment_label_annotations" in label_annotation_results:
        # Process video/segment level label annotations
        for segment_label in label_annotation_results.get("segment_label_annotations"):
            for segment in segment_label.get("segments"):
                pv, pv_1st_5_secs = detect_annotation(
                    segment_label.get("entity"),
                    segment,
                    branded_products_kg_entities,
                    config.branded_products,
                    config.branded_products_categories,
                )
                if pv:
                    product_visuals = True
                if pv_1st_5_secs:
                    product_visuals_1st_5_secs = True
    else:
        print(
            f"No Segment Label annotations found. Skipping {feature_name} Segment Label evaluation with Video Intelligence API."
        )

    # Check in annotations at shot level
    if "shot_label_annotations" in label_annotation_results:
        # Process shot level label annotations
        for shot_label in label_annotation_results.get("shot_label_annotations"):
            for segment in shot_label.get("segments"):
                pv, pv_1st_5_secs = detect_annotation(
                    shot_label.get("entity"),
                    segment,
                    branded_products_kg_entities,
                    config.branded_products,
                    config.branded_products_categories,
                )
                if pv:
                    product_visuals = True
                if pv_1st_5_secs:
                    product_visuals_1st_5_secs = True
    else:
        print(
            f"No Shot Label annotations found. Skipping {feature_name} Shot Label evaluation with Video Intelligence API."
        )

    # Check in annotations at frame level
    if "frame_label_annotations" in label_annotation_results:
        # Process frame level label annotations
        for frame_label in label_annotation_results.get("frame_label_annotations"):
            for frame in frame_label.get("frames"):
                pv, pv_1st_5_secs = detect_annotation(
                    frame_label.get("entity"),
                    frame,
                    branded_products_kg_entities,
                    config.branded_products,
                    config.branded_products_categories,
                )
                if pv:
                    product_visuals = True
                if pv_1st_5_secs:
                    product_visuals_1st_5_secs = True
    else:
        print(
            f"No Frame Label annotations found. Skipping {feature_name} Frame Label evaluation with Video Intelligence API."
        )

    return product_visuals, product_visuals_1st_5_secs
