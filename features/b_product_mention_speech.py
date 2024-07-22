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
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    use_llms,
    use_annotations,
    context_and_examples,
)

from helpers.annotations_helpers import (
    find_elements_in_transcript,
    get_speech_transcript,
    get_speech_transcript_1st_5_secs,
)

from helpers.vertex_ai_service import LLMParameters, detect_feature_with_llm

from helpers.generic_helpers import (
    get_n_secs_video_uri_from_uri,
)

### REMOVE FOR COLAB - END


# @title 14, 15) Brand: Product Mention (Speech), Product Mention (Speech) (First 5 seconds)

# @markdown **Features:**

# @markdown **Product Mention (Speech):** The branded product names or generic product categories are heard or mentioned in the audio or speech at any time in the video.

# @markdown **Product Mention (Speech) (First 5 seconds):** The branded product names or generic product categories are heard or mentioned in the audio or speech in the first 5 seconds (up to 4.99s) of the video.


def detect_product_mention_speech(
    speech_annotation_results: any,
    video_uri: str,
    branded_products: list[str],
    branded_products_categories: list[str],
) -> tuple[dict, dict]:
    """Detect Product Mention (Speech) & Product Mention (Speech) (First 5 seconds)
    Args:
        speech_annotation_results: peech annotations
        video_uri: video location in gcs
        branded_products: list of products
        branded_products_categories: list of products categories
    Returns:
        product_mention_speech_eval_details,
        product_mention_speech_1st_5_secs_eval_details: product mention speech evaluation
    """
    # Feature Product Mention (Speech)
    product_mention_speech_feature = "Product Mention (Speech)"
    product_mention_speech = False
    product_mention_speech_criteria = """The branded product names or generic product categories
        are heard or mentioned in the audio or speech at any time in the video."""
    product_mention_speech_eval_details = {
        "feature": product_mention_speech_feature,
        "feature_description": product_mention_speech_criteria,
        "feature_detected": product_mention_speech,
        "llm_details": [],
    }
    # Feature Product Mention (Speech) (First 5 seconds)
    product_mention_speech_1st_5_secs_feature = (
        "Product Mention (Speech) (First 5 seconds)"
    )
    product_mention_speech_1st_5_secs = False
    # remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
    product_mention_speech_1st_5_secs_criteria = """The branded product names or generic product categories
    are heard or mentioned in the audio or speech in the the video."""
    product_mention_speech_1st_5_secs_eval_details = {
        "feature": product_mention_speech_1st_5_secs_feature,
        "feature_description": product_mention_speech_1st_5_secs_criteria,
        "feature_detected": product_mention_speech_1st_5_secs,
        "llm_details": [],
    }

    # Video API: Evaluate product_mention_speech_feature and product_mention_speech_1st_5_secs_feature
    if use_annotations:
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
                f"No Speech annotations found. Skipping {product_mention_speech_feature} evaluation with Video Intelligence API."
            )

    # LLM: Evaluate product_mention_speech_feature and product_mention_speech_1st_5_secs_feature
    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )

        # LLM Only
        # 1. Evaluate product_mention_speech_feature
        prompt = (
            """Are any of the following products: {branded_products}
            or product categories: {branded_products_categories} heard
            at any time in the speech of the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the products {branded_products}
            or product categories {branded_products_categories} are heard in the speech of the video.
            Return False if the products or product categories are not heard in the speech.
            Only strictly use the speech of the video to answer, don't consider visual elements.
            {context_and_examples}
        """.replace(
                "{branded_products}", f"{', '.join(branded_products)}"
            )
            .replace(
                "{branded_products_categories}",
                f"{', '.join(branded_products_categories)}",
            )
            .replace("{feature}", product_mention_speech_feature)
            .replace("{criteria}", product_mention_speech_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected, llm_explanation = detect_feature_with_llm(
            product_mention_speech_feature, prompt, llm_params
        )
        if feature_detected:
            product_mention_speech = True

        # Include llm details
        product_mention_speech_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # 2. Evaluate product_mention_speech_feature_1st_5_secs
        prompt = (
            """Are any of the following products: {branded_products}
            or product categories: {branded_products_categories} heard in the speech of the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the products {branded_products}
            or product categories {branded_products_categories} are heard in the speech of the video.
            Return False if the products or product categories are not heard in the speech.
            Only strictly use the speech of the video to answer, don't consider visual elements.
            {context_and_examples}
        """.replace(
                "{branded_products}", f"{', '.join(branded_products)}"
            )
            .replace(
                "{branded_products_categories}",
                f"{', '.join(branded_products_categories)}",
            )
            .replace("{feature}", product_mention_speech_1st_5_secs_feature)
            .replace("{criteria}", product_mention_speech_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        video_uri_1st_5_secs = get_n_secs_video_uri_from_uri(video_uri, "1st_5_secs")
        llm_params.set_modality({"type": "video", "video_uri": video_uri_1st_5_secs})
        feature_detected, llm_explanation = detect_feature_with_llm(
            product_mention_speech_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            product_mention_speech_1st_5_secs = True

        # Include llm details
        product_mention_speech_1st_5_secs_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # Combination of Annotations + LLM
        if use_annotations:
            if "speech_transcriptions" in speech_annotation_results:
                # 1. Evaluate product_mention_speech_feature
                transcript = get_speech_transcript(
                    speech_annotation_results.get("speech_transcriptions")
                )
                prompt = (
                    """Does the provided speech transcript mention any of the following products: {branded_products}
                        or product categories: {branded_products_categories} at any time in the video?
                        This is the speech transcript: "{transcript}"
                        Consider the following criteria for your answer: {criteria}
                        {context_and_examples}
                    """.replace(
                        "{branded_products}", f"{', '.join(branded_products)}"
                    )
                    .replace(
                        "{branded_products_categories}",
                        f"{', '.join(branded_products_categories)}",
                    )
                    .replace("{transcript}", transcript)
                    .replace("{feature}", product_mention_speech_feature)
                    .replace("{criteria}", product_mention_speech_criteria)
                    .replace("{context_and_examples}", context_and_examples)
                )
                # Set modality to text since we are not using video for Annotations + LLM
                llm_params.set_modality({"type": "text"})
                # If transcript is empty, this feature should be False
                if transcript:
                    feature_detected, llm_explanation = detect_feature_with_llm(
                        product_mention_speech_feature, prompt, llm_params
                    )
                    if feature_detected:
                        product_mention_speech = True

                    # Include llm details
                    product_mention_speech_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": llm_explanation,
                        }
                    )
                else:
                    product_mention_speech = False
                    # Include default details
                    product_mention_speech_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": "Annotations + LLM: Speech was not found in annotations.",
                        }
                    )

                # 2. Evaluate product_mention_speech_feature_1st_5_secs
                transcript_1st_5_secs = get_speech_transcript_1st_5_secs(
                    speech_annotation_results.get("speech_transcriptions")
                )
                prompt = (
                    """Does the provided speech transcript mention any of the following products: {branded_products}
                        or product categories: {branded_products_categories} in the video?
                        This is the speech transcript: "{transcript}"
                        Consider the following criteria for your answer: {criteria}
                        {context_and_examples}
                    """.replace(
                        "{branded_products}", f"{', '.join(branded_products)}"
                    )
                    .replace(
                        "{branded_products_categories}",
                        f"{', '.join(branded_products_categories)}",
                    )
                    .replace("{transcript}", transcript_1st_5_secs)
                    .replace("{feature}", product_mention_speech_1st_5_secs_feature)
                    .replace("{criteria}", product_mention_speech_1st_5_secs_criteria)
                    .replace("{context_and_examples}", context_and_examples)
                )
                # Set modality to text since we are not using video for Annotations + LLM
                llm_params.set_modality({"type": "text"})
                # If transcript is empty, this feature should be False
                if transcript_1st_5_secs:
                    feature_detected, llm_explanation = detect_feature_with_llm(
                        product_mention_speech_1st_5_secs_feature, prompt, llm_params
                    )
                    if feature_detected:
                        product_mention_speech_1st_5_secs = True

                    # Include llm details
                    product_mention_speech_1st_5_secs_eval_details[
                        "llm_details"
                    ].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": llm_explanation,
                        }
                    )
                else:
                    product_mention_speech_1st_5_secs = False
                    # Include default details
                    product_mention_speech_1st_5_secs_eval_details[
                        "llm_details"
                    ].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": "Annotations + LLM: Speech was not found in annotations.",
                        }
                    )
            else:
                print(
                    f"No Speech annotations found. Skipping {product_mention_speech_feature} evaluation with LLM."
                )

    print(f"{product_mention_speech_feature}: {product_mention_speech}")
    product_mention_speech_eval_details["feature_detected"] = product_mention_speech
    print(
        f"{product_mention_speech_1st_5_secs_feature}: {product_mention_speech_1st_5_secs}"
    )
    product_mention_speech_1st_5_secs_eval_details["feature_detected"] = (
        product_mention_speech_1st_5_secs
    )

    return (
        product_mention_speech_eval_details,
        product_mention_speech_1st_5_secs_eval_details,
    )
