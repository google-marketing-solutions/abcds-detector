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
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    context_and_examples,
    use_llms,
    use_annotations,
)

from helpers.annotations_helpers import (
    find_elements_in_transcript,
    get_speech_transcript,
    get_speech_transcript_1st_5_secs,
)

from helpers.vertex_ai_service import LLMParameters, detect_feature_with_llm

from helpers.generic_helpers import (
    get_reduced_uri,
)

### REMOVE FOR COLAB - END

# @title 8 & 9) Brand: Brand Mention (Speech) & Brand Mention (Speech) (First 5 seconds)

# @markdown **Features:**

# @markdown **Brand Mention (Speech):** The brand name is heard in the audio or speech at any time in the video.

# @markdown **Brand Mention (Speech) (First 5 seconds):** The brand name is heard in the audio or speech in the first 5 seconds (up to 4.99s) of the video.


def detect_brand_mention_speech(
    speech_annotation_results: any,
    video_uri: str,
    brand_name: str,
    brand_variations: list[str],
) -> tuple[dict, dict]:
    """Detect Brand Mention (Speech) & Brand Mention (Speech) (First 5 seconds)
    Args:
        speech_annotation_results: speech annotations
        video_uri: video location in gcs
        brand_name: name of the brand
        brand_variations: a list of brand name variations
    Retirns:
        brand_mention_speech_eval_details,
        brand_mention_speech_1st_5_secs_eval_details: brand mention speech evaluation
    """
    # Feature Brand Mention (Speech)
    brand_mention_speech_feature = "Brand Mention (Speech)"
    brand_mention_speech = False
    brand_mention_speech_criteria = (
        """The brand name is heard in the audio or speech at any time in the video."""
    )
    brand_mention_speech_eval_details = {
        "feature": brand_mention_speech_feature,
        "feature_description": brand_mention_speech_criteria,
        "feature_detected": brand_mention_speech,
        "llm_details": [],
    }
    # Feature Brand Mention (Speech) (First 5 seconds)
    brand_mention_speech_1st_5_secs_feature = "Brand Mention (Speech) (First 5 seconds)"
    brand_mention_speech_1st_5_secs = False
    # remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
    brand_mention_speech_1st_5_secs_criteria = (
        """The brand name is heard in the audio or speech in the video."""
    )
    brand_mention_speech_1st_5_secs_eval_details = {
        "feature": brand_mention_speech_1st_5_secs_feature,
        "feature_description": brand_mention_speech_1st_5_secs_criteria,
        "feature_detected": brand_mention_speech_1st_5_secs,
        "llm_details": [],
    }

    # Video API: Evaluate brand_mention_speech and brand_mention_speech_1st_5_secs
    if use_annotations:
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
                f"No Speech annotations found. Skipping {brand_mention_speech_feature} evaluation with Video Intelligence API."
            )

    # LLM: Evaluate brand_mention_speech and brand_mention_speech_1st_5_secs
    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )

        # LLM Only
        # 1. Evaluate brand_mention_speech_feature
        prompt = (
            """Does the speech mention the brand {brand_name} at any time on the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the brand {brand_name} is heard in the speech of the video.
            {context_and_examples}
        """.replace(
                "{brand_name}", brand_name
            )
            .replace("{feature}", brand_mention_speech_feature)
            .replace("{criteria}", brand_mention_speech_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected, llm_explanation = detect_feature_with_llm(
            brand_mention_speech_feature, prompt, llm_params
        )
        if feature_detected:
            brand_mention_speech = True

        # Include llm details
        brand_mention_speech_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # 2. Evaluate brand_mention_speech_feature_1st_5_secs
        prompt = (
            """Does the speech mention the brand {brand_name} in the video?
            Consider the following criteria for your answer: {criteria}
            Provide the exact timestamp when the brand {brand_name} is heard in the speech of the video.
            Return True if and only if the brand {brand_name} is heard in the speech of the video.
            {context_and_examples}
        """.replace(
                "{brand_name}", brand_name
            )
            .replace("{feature}", brand_mention_speech_1st_5_secs_feature)
            .replace("{criteria}", brand_mention_speech_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        llm_params.set_modality({"type": "video", "video_uri": get_reduced_uri(video_uri)})
        feature_detected, llm_explanation = detect_feature_with_llm(
            brand_mention_speech_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            brand_mention_speech_1st_5_secs = True

        # Include llm details
        brand_mention_speech_1st_5_secs_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # Combination of Annotations + LLM
        if use_annotations:
            if "speech_transcriptions" in speech_annotation_results:
                # 1. Evaluate brand_mention_speech_feature
                transcript = get_speech_transcript(
                    speech_annotation_results.get("speech_transcriptions")
                )
                prompt = (
                    """Does the provided speech transcript mention the brand {brand_name}?
                        This is the speech transcript: "{transcript}"
                        Consider the following criteria for your answer: {criteria}
                        {context_and_examples}
                    """.replace(
                        "{brand_name}", brand_name
                    )
                    .replace("{transcript}", transcript)
                    .replace("{feature}", brand_mention_speech_feature)
                    .replace("{criteria}", brand_mention_speech_criteria)
                    .replace("{context_and_examples}", context_and_examples)
                )
                # Set modality to text since we are not using video for Annotations + LLM
                llm_params.set_modality({"type": "text"})
                # If transcript is empty, this feature should be False
                if transcript:
                    feature_detected, llm_explanation = detect_feature_with_llm(
                        brand_mention_speech_feature, prompt, llm_params
                    )
                    if feature_detected:
                        brand_mention_speech = True

                    # Include llm details
                    brand_mention_speech_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": llm_explanation,
                        }
                    )
                else:
                    brand_mention_speech = False
                    # Include default details
                    brand_mention_speech_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": "Annotations + LLM: Speech was not found in annotations.",
                        }
                    )

                # 2. Evaluate brand_mention_speech_feature_1st_5_secs
                transcript_1st_5_secs = get_speech_transcript_1st_5_secs(
                    speech_annotation_results.get("speech_transcriptions")
                )
                prompt = (
                    """Does the provided speech transcript mention the brand {brand_name}?
                        This is the speech transcript: "{transcript}"
                        Consider the following criteria for your answer: {criteria}
                        {context_and_examples}
                    """.replace(
                        "{brand_name}", brand_name
                    )
                    .replace("{transcript}", transcript_1st_5_secs)
                    .replace("{feature}", brand_mention_speech_1st_5_secs_feature)
                    .replace("{criteria}", brand_mention_speech_1st_5_secs_criteria)
                    .replace("{context_and_examples}", context_and_examples)
                )
                # Set modality to text since we are not using video for Annotations + LLM
                llm_params.set_modality({"type": "text"})
                # If transcript is empty, this feature should be False
                if transcript_1st_5_secs:
                    feature_detected, llm_explanation = detect_feature_with_llm(
                        brand_mention_speech_1st_5_secs_feature, prompt, llm_params
                    )
                    if feature_detected:
                        brand_mention_speech_1st_5_secs = True

                    # Include llm details
                    brand_mention_speech_1st_5_secs_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": llm_explanation,
                        }
                    )
                else:
                    brand_mention_speech_1st_5_secs = False
                    # Include default details
                    brand_mention_speech_1st_5_secs_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": "Annotations + LLM: Speech was not found in annotations.",
                        }
                    )
            else:
                print(
                    f"No Speech annotations found. Skipping {brand_mention_speech_feature} evaluation with LLM."
                )

    print(f"{brand_mention_speech_feature}: {brand_mention_speech}")
    brand_mention_speech_eval_details["feature_detected"] = brand_mention_speech
    print(
        f"{brand_mention_speech_1st_5_secs_feature}: {brand_mention_speech_1st_5_secs}"
    )
    brand_mention_speech_1st_5_secs_eval_details["feature_detected"] = (
        brand_mention_speech_1st_5_secs
    )

    return (
        brand_mention_speech_eval_details,
        brand_mention_speech_1st_5_secs_eval_details,
    )
