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

from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    early_time_seconds,
    confidence_threshold,
    use_llms,
    use_annotations,
    context_and_examples,
)

from helpers.annotations_helpers import calculate_time_seconds
from helpers.vertex_ai_service import LLMParameters, detect_feature_with_llm
from helpers.generic_helpers import get_knowledge_graph_entities, get_reduced_uri

def detect(
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


def detect_product_visuals(
    label_annotation_results: any,
    video_uri: str,
    branded_products: list[str],
    branded_products_categories: list[str],
) -> tuple[dict, dict]:
    """Detect Product Visuals & Product Visuals (First 5 seconds)
    Args:
        label_annotation_results: label annotations
        video_location: video location in gcs
        branded_products: list of products
        branded_products_categories: list of products categories
    Returns:
        product_visuals_eval_details,
        product_visuals_1st_5_secs_eval_details: product visuals evaluation
    """
    # Feature Product Visuals
    product_visuals_feature = "Product Visuals"
    product_visuals = False
    product_visuals_criteria = """A product or branded packaging is visually present at any time in the video.
        Where the product is a service a relevant substitute should be shown such as via a branded app or branded
        service personnel."""
    product_visuals_eval_details = {
        "feature": product_visuals_feature,
        "feature_description": product_visuals_criteria,
        "feature_detected": product_visuals,
        "llm_details": [],
    }
    # Feature Product Visuals (First 5 seconds)
    product_visuals_1st_5_secs_feature = "Product Visuals (First 5 seconds)"
    product_visuals_1st_5_secs = False
    # Remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
    product_visuals_1st_5_secs_criteria = """A product or branded packaging is visually present the video.
    Where the product is a service a relevant substitute should be shown such as via a
    branded app or branded service personnel."""
    product_visuals_1st_5_secs_eval_details = {
        "feature": product_visuals_1st_5_secs_feature,
        "feature_description": product_visuals_1st_5_secs_criteria,
        "feature_detected": product_visuals_1st_5_secs,
        "llm_details": [],
    }

    branded_products_kg_entities = get_knowledge_graph_entities(branded_products)

    # Video API: Evaluate product_visuals_feature and product_visuals_1st_5_secs_feature
    if use_annotations:
        # Video API: Evaluate product_visuals and product_visuals_1st_5_secs
        # Check in annotations at segment level
        if "segment_label_annotations" in label_annotation_results:
            # Process video/segment level label annotations
            for segment_label in label_annotation_results.get(
                "segment_label_annotations"
            ):
                for segment in segment_label.get("segments"):
                    pv, pv_1st_5_secs = detect(
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
                f"No Segment Label annotations found. Skipping {product_visuals_feature} Segment Label evaluation with Video Intelligence API."
            )

        # Check in annotations at shot level
        if "shot_label_annotations" in label_annotation_results:
            # Process shot level label annotations
            for shot_label in label_annotation_results.get("shot_label_annotations"):
                for segment in shot_label.get("segments"):
                    pv, pv_1st_5_secs = detect(
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
                f"No Shot Label annotations found. Skipping {product_visuals_feature} Shot Label evaluation with Video Intelligence API."
            )

        # Check in annotations at frame level
        if "frame_label_annotations" in label_annotation_results:
            # Process frame level label annotations
            for frame_label in label_annotation_results.get("frame_label_annotations"):
                for frame in frame_label.get("frames"):
                    pv, pv_1st_5_secs = detect(
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
                f"No Frame Label annotations found. Skipping {product_visuals_feature} Frame Label evaluation with Video Intelligence API."
            )

    # LLM: Evaluate product_visuals_feature and product_visuals_1st_5_secs_feature
    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # 1. Evaluate product_visuals_feature
        prompt = (
            """Is any of the following products: {branded_products}
            or product categories: {branded_products_categories}
            visually present at any time in the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the products {branded_products}
            or product categories: {branded_products_categories} are found.
            {context_and_examples}
        """.replace(
                "{branded_products}", ", ".join(branded_products)
            )
            .replace(
                "{branded_products_categories}", ", ".join(branded_products_categories)
            )
            .replace("{feature}", product_visuals_feature)
            .replace("{criteria}", product_visuals_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected, llm_explanation = detect_feature_with_llm(
            product_visuals_feature, prompt, llm_params
        )
        if feature_detected:
            product_visuals = True

        # Include llm details
        product_visuals_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # 2. Evaluate product_visuals_1st_5_secs_feature
        prompt = (
            """Is any of the following products: {branded_products}
            or product categories: {branded_products_categories}
            visually present in the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the products {branded_products}
            or product categories: {branded_products_categories} are visually present.
            Return True if and only if the branded producs or product categories are
            visually present in the video.
            {context_and_examples}
        """.replace(
                "{branded_products}", ", ".join(branded_products)
            )
            .replace(
                "{branded_products_categories}", ", ".join(branded_products_categories)
            )
            .replace("{feature}", product_visuals_1st_5_secs_feature)
            .replace("{criteria}", product_visuals_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        llm_params.set_modality({"type": "video", "video_uri": get_reduced_uri(video_uri)})
        feature_detected, llm_explanation = detect_feature_with_llm(
            product_visuals_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            product_visuals_1st_5_secs = True

        product_visuals_1st_5_secs_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

    print(f"{product_visuals_feature}: {product_visuals}")
    product_visuals_eval_details["feature_detected"] = product_visuals
    print(f"{product_visuals_1st_5_secs_feature}: {product_visuals_1st_5_secs}")
    product_visuals_1st_5_secs_eval_details["feature_detected"] = (
        product_visuals_1st_5_secs
    )

    return product_visuals_eval_details, product_visuals_1st_5_secs_eval_details
