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

### REMOVE FOR COLAB - START
from input_parameters import (
    early_time_seconds,
    confidence_threshold,
    branded_products,
    branded_products_categories,
)

from helpers.annotations_helpers import calculate_time_seconds, get_label_annotations

from helpers.generic_helpers import (
    get_knowledge_graph_entities,
)

### REMOVE FOR COLAB - END

# @title 10 & 11) Brand: Product Visuals & Product Visuals (First 5 seconds)

# @markdown **Features:**

# @markdown 1. **Product Visuals:** A product or branded packaging is visually present at any time in the video. Where the product is a service a relevant substitute should be shown such as via a branded app or branded service personnel.

# @markdown 2. **Product Visuals (First 5 seconds):** A product or branded packaging is visually present in the first 5 seconds (up to 4.99s) of the video. Where the product is a service a relevant substitute should be shown such as via a branded app or branded service personnel.


def detect_product_visuals(
    feature_name: str, bucket: any, annotation_location: str
) -> bool:
    """Detect Product Visuals
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        product_visuals: product visuals evaluation
    """
    product_visuals, na = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {product_visuals}")

    return product_visuals


def detect_product_visuals_1st_5_secs(
    feature_name: str, bucket: any, annotation_location: str
) -> bool:
    """Detect Product Visuals (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        product_visuals_1st_5_secs: product visuals evaluation
    """
    na, product_visuals_1st_5_secs = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {product_visuals_1st_5_secs}")

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
        if segment.get("confidence") >= confidence_threshold:
            product_visuals = True
            start_time_secs = calculate_time_seconds(
                segment.get("segment"), "start_time_offset"
            )
            if start_time_secs <= early_time_seconds:
                product_visuals_1st_5_secs = True

    return product_visuals, product_visuals_1st_5_secs


def detect(
    feature_name: str, bucket: any, annotation_location: str
) -> tuple[bool, bool]:
    """Detect Product Visuals & Product Visuals (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        product_visuals,
        product_visuals_1st_5_secs: product visuals evaluation
    """
    label_annotation_results = get_label_annotations(bucket, annotation_location)
    # Feature Product Visuals
    product_visuals = False

    # Feature Product Visuals (First 5 seconds)
    product_visuals_1st_5_secs = False

    branded_products_kg_entities = get_knowledge_graph_entities(branded_products)

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
                    branded_products,
                    branded_products_categories,
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
                    branded_products,
                    branded_products_categories,
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
                    branded_products,
                    branded_products_categories,
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
