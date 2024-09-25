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

"""Module to detect Attract: Dynamic Start
Annotations used:
    1. Shot annotations to calculate how dynamic the video is
"""

### REMOVE FOR COLAB - START
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    dynamic_cutoff_ms,
    use_annotations,
    use_llms,
    context_and_examples,
)

from helpers.generic_helpers import (
    get_reduced_uri,
)

from helpers.vertex_ai_service import LLMParameters, detect_feature_with_llm

### REMOVE FOR COLAB - START


# @title 3) Attract: Dynamic Start

# @markdown **Features:**

# @markdown **Dynamic Start:** The first shot in the video changes in less than 3 seconds.


def detect_dynamic_start(shot_annotation_results: any, video_uri: str) -> dict:
    """Detects Dynamic Start
    Args:
        shot_annotation_results: shot annotations
        video_uri: video location in gcs
    Returns:
        dynamic_start_eval_details: dynamic start evaluation
    """
    # Feature Dynamic Start
    dynamic_start_feature = "Dynamic Start"
    dynamic_start = False
    dynamic_start_criteria = (
        """The first shot in the video changes in less than 3 seconds."""
    )
    dynamic_start_eval_details = {
        "feature": dynamic_start_feature,
        "feature_description": dynamic_start_criteria,
        "feature_detected": dynamic_start,
        "llm_details": [],
    }

    # Video API: Evaluate dynamic_start_feature
    if use_annotations:
        if "shot_annotations" in shot_annotation_results:
            first_shot_end_time_off_set = shot_annotation_results.get(
                "shot_annotations"
            )[0]
            nanos = first_shot_end_time_off_set.get("end_time_offset").get("nanos")
            seconds = first_shot_end_time_off_set.get("end_time_offset").get("seconds")
            if nanos:
                if seconds:
                    total_ms_first_shot = (nanos + seconds * 1e9) / 1e6
                else:
                    total_ms_first_shot = nanos / 1e6
            else:
                if seconds:
                    total_ms_first_shot = (seconds * 1e9) / 1e6

            if total_ms_first_shot < dynamic_cutoff_ms:
                dynamic_start = True
        else:
            print(
                f"No Shot annotations found. Skipping {dynamic_start_feature} evaluation with Video Intelligence API."
            )

    # LLM: Evaluate dynamic_start_feature
    if use_llms:
        # 1. Evaluate dynamic_start_feature
        prompt = (
            """Does the first shot in the video change in less than 3 seconds?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when the first shot in the video changes.
            Return True if and only if the first shot in the video changes in less than 3 seconds.
            {context_and_examples}
        """.replace(
                "{feature}", dynamic_start_feature
            )
            .replace("{criteria}", dynamic_start_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # Use first 5 secs video for this feature
        llm_params.set_modality({"type": "video", "video_uri": get_reduced_uri(video_uri)})
        feature_detected, llm_explanation = detect_feature_with_llm(
            dynamic_start_feature, prompt, llm_params
        )
        if feature_detected:
            dynamic_start = True

        # Include llm details
        dynamic_start_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

    print(f"{dynamic_start_feature}: {dynamic_start}")
    dynamic_start_eval_details["feature_detected"] = dynamic_start

    return dynamic_start_eval_details
