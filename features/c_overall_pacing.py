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

"""Module to detect Connect: Overall Pacing
Annotations used:
    1. Shot annotations to calculate the overall video pacing
"""

### REMOVE FOR COLAB - START
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    avg_shot_duration_seconds,
    use_llms,
    use_annotations,
    context_and_examples,
)

from helpers.helpers import (
    LLMParameters,
    calculate_time_seconds,
    detect_feature_with_llm,
)

### REMOVE FOR COLAB - END

# @title 21) Connect: Overall Pacing

# @markdown **Features:**

# @markdown **Overall Pacing:** The pace of the video is greater than 2 seconds per shot/frame

# Features
overall_pacing_feature = "Overall Pacing"


def detect_overall_pacing(shot_annotation_results: any, video_uri: str) -> bool:
    """Detect Overall Pacing
    Args:
        shot_annotation_results: shot annotations
        video_location: video location in gcs
    Returns:
        overall_pacing: evaluation
    """
    overall_pacing = False
    total_time_all_shots = 0
    total_shots = 0

    if use_annotations:
        if "shot_annotations" in shot_annotation_results:
            # Video API: Evaluate overall_pacing_feature
            for shot in shot_annotation_results.get("shot_annotations"):
                start_time_secs = calculate_time_seconds(shot, "start_time_offset")
                end_time_secs = calculate_time_seconds(shot, "end_time_offset")
                total_shot_time = end_time_secs - start_time_secs
                total_time_all_shots += total_shot_time
                total_shots += 1
            avg_pacing = total_time_all_shots / total_shots
            if avg_pacing <= avg_shot_duration_seconds:
                overall_pacing = True
        else:
            print(
                f"No Shot annotations found. Skipping {overall_pacing_feature} evaluation with Video Intelligence API."
            )

    if use_llms:
        # 1. Evaluate overall_pacing_feature
        overall_pacing_criteria = (
            """The pace of the video is greater than 2 seconds per shot/frame"""
        )
        prompt = (
            """Is the pace of video greater than 2 seconds per shot/frame?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Return True if and only if the pace of video greater than 2 seconds per shot/frame
            {context_and_examples}
        """.replace(
                "{feature}", overall_pacing_feature
            )
            .replace("{criteria}", overall_pacing_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected = detect_feature_with_llm(
            overall_pacing_feature, prompt, llm_params
        )
        if feature_detected:
            overall_pacing = True

    print(f"{overall_pacing_feature}: {overall_pacing}")

    return overall_pacing
