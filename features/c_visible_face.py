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

"""Module to detect Connect: Visible Face (First 5 seconds) & Visible Face (Close Up)
Annotations used:
    1. Face annotations to identify faces in the video
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
    face_surface_threshold,
    context_and_examples,
)

from helpers.helpers import (
    LLMParameters,
    calculate_time_seconds,
    detect_feature_with_llm,
    get_n_secs_video_uri_from_uri,
)

### REMOVE FOR COLAB - END

# @title 16 & 17) Connect: Visible Face (First 5 seconds) & Visible Face (Close Up)

# @markdown **Features:**

# @markdown  **Visible Face (First 5 seconds):** At least one human face is present in the first 5 seconds (up to 4.99s) of the video. Alternate representations of people such as Animations or Cartoons ARE acceptable.

# @markdown  **Visible Face (Close Up):** There is a close up of a human face at any time in the video.

# Features
visible_face_1st_5_secs_feature = "Visible Face (First 5 seconds)"
visible_face_close_up_feature = "Visible Face (Close Up)"


def detect_visible_face(
    face_annotation_results: any, video_uri: str
) -> tuple[bool, bool]:
    """Detect Visible Face (First 5 seconds) & Visible Face (Close Up)
    Args:
        face_annotation_results: face annotations
        video_location: video location in gcs
    Returns:
        visible_face_1st_5_secs,
        visible_face_close_up: evaluation
    """
    visible_face_1st_5_secs = False
    visible_face_close_up = False

    if use_annotations:
        if "face_detection_annotations" in face_annotation_results:
            # Video API: Evaluate visible_face_1st_5_secs_feature and visible_face_close_up_feature
            if face_annotation_results.get("face_detection_annotations"):
                for annotation in face_annotation_results.get(
                    "face_detection_annotations"
                ):
                    for track in annotation.get("tracks"):
                        start_time_secs = calculate_time_seconds(
                            track.get("segment"), "start_time_offset"
                        )
                        # Check confidence against user defined threshold
                        if track.get("confidence") >= confidence_threshold:
                            if start_time_secs < early_time_seconds:
                                visible_face_1st_5_secs = True
                            for face_object in track.get("timestamped_objects"):
                                box = face_object.get("normalized_bounding_box")
                                left = box.get("left") or 0
                                right = box.get("right") or 1
                                top = box.get("top") or 0
                                bottom = box.get("bottom") or 1
                                width = right - left
                                height = bottom - top
                                surface = width * height
                                if surface >= face_surface_threshold:
                                    visible_face_close_up = True
        else:
            print(
                f"No Face annotations found. Skipping {visible_face_1st_5_secs_feature} evaluation with Video Intelligence API."
            )

    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # 1. Evaluate visible_face_1st_5_secs_feature
        # remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
        visible_face_1st_5_secs_criteria = """At least one human face is present in the video.
        Alternate representations of people such as Animations or Cartoons ARE acceptable."""
        prompt = (
            """Is there a human face present in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when the human face is present.
            {context_and_examples}
        """.replace(
                "{feature}", visible_face_1st_5_secs_feature
            )
            .replace("{criteria}", visible_face_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        video_uri_1st_5_secs = get_n_secs_video_uri_from_uri(video_uri, "1st_5_secs")
        llm_params.set_modality({"type": "video", "video_uri": video_uri_1st_5_secs})
        feature_detected = detect_feature_with_llm(
            visible_face_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            visible_face_1st_5_secs = True

        # 2. Evaluate visible_face_close_up_feature
        visible_face_close_up_criteria = (
            """There is a close up of a human face at any time in the video."""
        )
        prompt = (
            """Is there a close up of a human face present at any time the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when there is a close up of a human face.
            {context_and_examples}
        """.replace(
                "{feature}", visible_face_close_up_feature
            )
            .replace("{criteria}", visible_face_close_up_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected = detect_feature_with_llm(
            visible_face_close_up_feature, prompt, llm_params
        )
        if feature_detected:
            visible_face_close_up = True

    print(f"{visible_face_1st_5_secs_feature}: {visible_face_1st_5_secs}")
    print(f"{visible_face_close_up_feature}: {visible_face_close_up}")

    return visible_face_1st_5_secs, visible_face_close_up
