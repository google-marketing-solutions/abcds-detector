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

from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    context_and_examples,
    use_llms,
    use_annotations,
)

from helpers.annotations_helpers import detected_text_in_first_5_seconds
from helpers.vertex_ai_service import LLMParameters, detect_feature_with_llm
from helpers.generic_helpers import get_reduced_uri

def detect_product_mention_text(
    text_annotation_results: any,
    video_uri: str,
    branded_products: list[str],
    branded_products_categories: list[str],
) -> tuple[dict, dict]:
    """Detect Product Mention (Text) & Product Mention (Text) (First 5 seconds)
    Args:
        text_annotation_results: text annotations
        video_uri: video location in gcs
        branded_products: list of products
        branded_products_categories: list of products categories
    Returns:
        product_mention_text_eval_details,
        product_mention_text_1st_5_secs_eval_details: product mention text evaluation
    """
    # Feature Product Mention (Text)
    product_mention_text_feature = "Product Mention (Text)"
    product_mention_text = False
    product_mention_text_criteria = """The branded product names or generic product categories
        are present in any text or overlay at any time in the video."""
    product_mention_text_eval_details = {
        "feature": product_mention_text_feature,
        "feature_description": product_mention_text_criteria,
        "feature_detected": product_mention_text,
        "llm_details": [],
    }
    # Feature Product Mention (Text) (First 5 seconds)
    product_mention_text_1st_5_secs_feature = "Product Mention (Text) (First 5 seconds)"
    product_mention_text_1st_5_secs = False
    # Remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
    product_mention_text_1st_5_secs_criteria = """The branded product names or generic product categories
    are present in any text or overlay in the video."""
    product_mention_text_1st_5_secs_eval_details = {
        "feature": product_mention_text_1st_5_secs_feature,
        "feature_description": product_mention_text_1st_5_secs_criteria,
        "feature_detected": product_mention_text_1st_5_secs,
        "llm_details": [],
    }

    # Video API: Evaluate product_mention_text_feature and product_mention_text_1st_5_secs_feature
    if use_annotations:
        if "text_annotations" in text_annotation_results:
            # Video API: Evaluate product_mention_text_feature and product_mention_text_1st_5_secs_feature
            for text_annotation in text_annotation_results.get("text_annotations"):
                text = text_annotation.get("text")
                found_branded_products = [
                    prod for prod in branded_products if prod.lower() in text.lower()
                ]
                found_branded_products_categories = [
                    prod
                    for prod in branded_products_categories
                    if prod.lower() in text.lower()
                ]
                if (
                    len(found_branded_products) > 0
                    or len(found_branded_products_categories) > 0
                ):
                    product_mention_text = True
                    pmt_1st_5_secs, frame = detected_text_in_first_5_seconds(
                        text_annotation
                    )
                    if pmt_1st_5_secs:
                        product_mention_text_1st_5_secs = True
        else:
            print(
                f"No Text annotations found. Skipping {product_mention_text_feature} evaluation with Video Intelligence API."
            )

    # LLM: Evaluate product_mention_text_feature and product_mention_text_1st_5_secs_feature
    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # 1. Evaluate product_mention_text_feature
        prompt = (
            """Is any of the following products: {branded_products}
            or product categories: {branded_products_categories}
            present in any text or overlay at any time in the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the products {branded_products}
            or product categories: {branded_products_categories} are found
            in any text or overlay in the video.
            {context_and_examples}
        """.replace(
                "{branded_products}", f"{', '.join(branded_products)}"
            )
            .replace(
                "{branded_products_categories}",
                f"{', '.join(branded_products_categories)}",
            )
            .replace("{feature}", product_mention_text_feature)
            .replace("{criteria}", product_mention_text_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected, llm_explanation = detect_feature_with_llm(
            product_mention_text_feature, prompt, llm_params
        )
        if feature_detected:
            product_mention_text = True

        # Include llm details
        product_mention_text_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # 2. Evaluate product_mention_text_1st_5_secs_feature
        prompt = (
            """Is any of the following products: {branded_products}
            or product categories: {branded_products_categories}
            present in any text or overlay in the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the products {branded_products}
            or product categories: {branded_products_categories} are found
            in any text or overlay in the video.
            {context_and_examples}
        """.replace(
                "{branded_products}", f"{', '.join(branded_products)}"
            )
            .replace(
                "{branded_products_categories}",
                f"{', '.join(branded_products_categories)}",
            )
            .replace("{feature}", product_mention_text_1st_5_secs_feature)
            .replace("{criteria}", product_mention_text_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        llm_params.set_modality({"type": "video", "video_uri": get_reduced_uri(video_uri)})
        feature_detected, llm_explanation = detect_feature_with_llm(
            product_mention_text_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            product_mention_text_1st_5_secs = True

        product_mention_text_1st_5_secs_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

    print(f"{product_mention_text_feature}: {product_mention_text}")
    product_mention_text_eval_details["feature_detected"] = product_mention_text
    print(
        f"{product_mention_text_1st_5_secs_feature}: {product_mention_text_1st_5_secs}"
    )
    product_mention_text_1st_5_secs_eval_details["feature_detected"] = (
        product_mention_text_1st_5_secs
    )

    return (
        product_mention_text_eval_details,
        product_mention_text_1st_5_secs_eval_details,
    )
