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

"""Module to detect Connect: Presence of People & Presence of People (First 5 seconds)
Annotations used:
    1. People annotations to identify people in the video
"""

### REMOVE FOR COLAB - START
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

from helpers.generic_helpers import (
    get_n_secs_video_uri_from_uri,
)

### REMOVE FOR COLAB - END

# @title 18 & 19) Connect: Presence of People & Presence of People (First 5 seconds)

# @markdown **Features:**

# @markdown  **Presence of People:** People are shown in any capacity at any time in the video. Any human body parts are acceptable to pass this guideline. Alternate representations of people such as Animations or Cartoons ARE acceptable.

# @markdown  **Presence of People (First 5 seconds):** People are shown in any capacity in the first 5 seconds (up to 4.99s) of the video. Any human body parts are acceptable to pass this guideline. Alternate representations of people such as Animations or Cartoons ARE acceptable.


def detect_presence_of_people(
    people_annotation_results: any, video_uri: str
) -> tuple[dict, dict]:
    """Detect Presence of People & Presence of People (First 5 seconds)
    Args:
        people_annotation_results: people annotations
        video_uri: video location in gcs
    Returns:
        presence_of_people_eval_details,
        presence_of_people_1st_5_secs_eval_details: presence of people evaluation
    """
    # Feature Presence of People
    presence_of_people_feature = "Presence of People"
    presence_of_people = False
    presence_of_people_criteria = """People are shown in any capacity at any time in the video.
        Any human body parts are acceptable to pass this guideline. Alternate representations of
        people such as Animations or Cartoons ARE acceptable."""
    presence_of_people_eval_details = {
        "feature": presence_of_people_feature,
        "feature_description": presence_of_people_criteria,
        "feature_detected": presence_of_people,
        "llm_details": [],
    }
    # Feature Presence of People (First 5 seconds)
    presence_of_people_1st_5_secs_feature = "Presence of People (First 5 seconds)"
    presence_of_people_1st_5_secs = False
    # Remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
    presence_of_people_1st_5_secs_criteria = """People are shown in any capacity in the video.
    Any human body parts are acceptable to pass this guideline. Alternate
    representations of people such as Animations or Cartoons ARE acceptable."""
    presence_of_people_1st_5_secs_eval_details = {
        "feature": presence_of_people_1st_5_secs_feature,
        "feature_description": presence_of_people_1st_5_secs_criteria,
        "feature_detected": presence_of_people_1st_5_secs,
        "llm_details": [],
    }

    # Video API: Evaluate presence_of_people_feature and presence_of_people_1st_5_secs_feature
    if use_annotations:
        if "person_detection_annotations" in people_annotation_results:
            # Video API: Evaluate presence_of_people_feature and presence_of_people_1st_5_secs_feature
            for people_annotation in people_annotation_results.get(
                "person_detection_annotations"
            ):
                for track in people_annotation.get("tracks"):
                    # Check confidence against user defined threshold
                    if track.get("confidence") >= confidence_threshold:
                        presence_of_people = True
                        start_time_secs = calculate_time_seconds(
                            track.get("segment"), "start_time_offset"
                        )
                        if start_time_secs < early_time_seconds:
                            presence_of_people_1st_5_secs = True
                        # Each segment includes track.get("timestamped_objects") that include
                        # characteristics - -e.g.clothes, posture of the person detected.
        else:
            print(
                f"No People annotations found. Skipping {presence_of_people_feature} evaluation with Video Intelligence API."
            )

    # LLM: Evaluate presence_of_people_feature and presence_of_people_1st_5_secs_feature
    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # 1. Evaluate presence_of_people_feature
        prompt = (
            """Are there people present at any time in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when people are present in the video.
            {context_and_examples}
        """.replace(
                "{feature}", presence_of_people_feature
            )
            .replace("{criteria}", presence_of_people_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected, llm_explanation = detect_feature_with_llm(
            presence_of_people_feature, prompt, llm_params
        )
        if feature_detected:
            presence_of_people = True

        # Include llm details
        presence_of_people_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # 2. Evaluate presence_of_people_1st_5_secs_feature
        prompt = (
            """Are there people present in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when people are present in the video.
            {context_and_examples}
        """.replace(
                "{feature}", presence_of_people_1st_5_secs_feature
            )
            .replace("{criteria}", presence_of_people_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        video_uri_1st_5_secs = get_n_secs_video_uri_from_uri(video_uri, "1st_5_secs")
        llm_params.set_modality({"type": "video", "video_uri": video_uri_1st_5_secs})
        feature_detected, llm_explanation = detect_feature_with_llm(
            presence_of_people_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            presence_of_people_1st_5_secs = True

        # Include llm details
        presence_of_people_1st_5_secs_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

    print(f"{presence_of_people_feature}: {presence_of_people}")
    presence_of_people_eval_details["feature_detected"] = presence_of_people
    print(f"{presence_of_people_1st_5_secs_feature}: {presence_of_people_1st_5_secs}")
    presence_of_people_1st_5_secs_eval_details["feature_detected"] = (
        presence_of_people_1st_5_secs
    )

    return presence_of_people_eval_details, presence_of_people_1st_5_secs_eval_details
