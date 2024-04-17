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

"""Module to detect Direct: Quick Pacing & Quick Pacing (First 5 seconds)
Annotations used:
    1. Shot annotations to calculate the pacing of the video
"""

### REMOVE FOR COLAB - START
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    early_time_seconds,
    use_llms,
    use_annotations,
    context_and_examples,
)

from helpers.helpers import (
    LLMParameters,
    calculate_time_seconds,
    detect_feature_with_llm,
    get_n_secs_video_uri_from_uri,
)

### REMOVE FOR COLAB - END

# @title 1, 2) Attract: Quick Pacing & Quick Pacing (First 5 seconds)

# @markdown **Features:**

# @markdown **Quick Pacing:** Within ANY 5 consecutive seconds there are 5 or more shots in the video. These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms, depth of field changes, tracking shots and movement of the camera.

# @markdown **Quick Pacing (First 5 seconds):** There are at least 5 shot changes or visual cuts detected within the first 5 seconds (up to 4.99s) of the video. These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms, depth of field changes, tracking shots and movement of the camera.

# Features
quick_pacing_feature = "Quick Pacing"
quick_pacing_1st_5_secs_feature = "Quick Pacing (First 5 seconds)"


def detect_quick_pacing(
    shot_annotation_results: any, video_uri: str
) -> tuple[bool, bool]:
    """Detect Quick Pacing & Quick Pacing (First 5 seconds)
    Args:
        shot_annotation_results: shot annotations
    Returns:
        quick_pacing, quick_pacing_1st_5_secs: quick pacing evaluation tuple
    """
    required_secs_for_quick_pacing = 5
    required_shots_for_quick_pacing = 5
    # Quick Pacing calculation
    quick_pacing = False
    total_shots_count = 0
    total_time_all_shots = 0
    # Quick Pacing (First 5 secs) calculation
    quick_pacing_1st_5_secs = False
    total_shots_count_1st_5_secs = 0

    if use_annotations:
        if "shot_annotations" in shot_annotation_results:
            sorted_shots = sorted(
                shot_annotation_results.get("shot_annotations"),
                key=lambda x: calculate_time_seconds(x, "start_time_offset"),
                reverse=False,
            )
            # Video API: Evaluate quick_pacing_feature & quick_pacing_1st_5_secs_feature
            for shot in sorted_shots:
                start_time_secs = calculate_time_seconds(shot, "start_time_offset")
                end_time_secs = calculate_time_seconds(shot, "end_time_offset")
                shot_total_time = end_time_secs - start_time_secs
                # Quick Pacing calculation
                # TODO (ae) is it completed shots or just started shots?
                total_time_all_shots += shot_total_time
                if total_time_all_shots < required_secs_for_quick_pacing:
                    total_shots_count += 1
                    # Quick Pacing (First 5 secs) calculation
                    if start_time_secs < early_time_seconds:
                        total_shots_count_1st_5_secs += 1
                else:
                    # To start counting shot time and # shots again
                    if total_shots_count >= required_shots_for_quick_pacing:
                        quick_pacing = True
                    # Quick Pacing (First 5 secs) calculation
                    if total_shots_count_1st_5_secs >= required_shots_for_quick_pacing:
                        quick_pacing_1st_5_secs = True
                    total_time_all_shots = 0
                    total_shots_count = 0
        else:
            print(
                f"No Shot annotations found. Skipping {quick_pacing_feature} evaluation with Video Intelligence API."
            )

    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # 1. Evaluate quick_pacing_feature
        quick_pacing_criteria = """Within ANY 5 consecutive seconds there are 5 or more shots in the video.
        These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms,
        depth of field changes, tracking shots and movement of the camera."""
        prompt = (
            """Are there 5 or more shots within ANY 5 consecutive seconds in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the shot changes count in the following format:
            Number of shots: #
            Provide the exact timestamp when the shot changes happen and the shot description.
            Return False if the number of shots identified is less than 5.
            {context_and_examples}
        """.replace(
                "{feature}", quick_pacing_feature
            )
            .replace("{criteria}", quick_pacing_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected = detect_feature_with_llm(
            quick_pacing_feature, prompt, llm_params
        )
        if feature_detected:
            quick_pacing = True

        # 2. Evaluate quick_pacing_1st_5_secs_feature
        # remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
        quick_pacing_1st_5_secs_criteria = """There are at least 5 shot changes or visual cuts detected in the video.
        These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms, depth of
        field changes, tracking shots and movement of the camera."""
        prompt = (
            """Are there at least 5 shot changes or visual cuts detected in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the shot changes count in the following format:
            Number of shots: #
            Provide the exact timestamp when the shot changes happen and the shot description.
            Return False if the number of shots identified is less than 5.
            {context_and_examples}
        """.replace(
                "{feature}", quick_pacing_1st_5_secs_feature
            )
            .replace("{criteria}", quick_pacing_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        video_uri_1st_5_secs = get_n_secs_video_uri_from_uri(video_uri, "1st_5_secs")
        llm_params.set_modality({"type": "video", "video_uri": video_uri_1st_5_secs})
        feature_detected = detect_feature_with_llm(
            quick_pacing_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            quick_pacing_1st_5_secs = True

    print(f"{quick_pacing_feature}: {quick_pacing}")
    print(f"{quick_pacing_1st_5_secs_feature}: {quick_pacing_1st_5_secs}")

    return quick_pacing, quick_pacing_1st_5_secs
