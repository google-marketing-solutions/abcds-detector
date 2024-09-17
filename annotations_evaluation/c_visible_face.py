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
    early_time_seconds,
    confidence_threshold,
    face_surface_threshold,
)

from helpers.annotations_helpers import calculate_time_seconds, get_face_annotations

### REMOVE FOR COLAB - END

# @title 16 & 17) Connect: Visible Face (First 5 seconds) & Visible Face (Close Up)

# @markdown **Features:**

# @markdown  **Visible Face (First 5 seconds):** At least one human face is present in the first 5 seconds (up to 4.99s) of the video. Alternate representations of people such as Animations or Cartoons ARE acceptable.

# @markdown  **Visible Face (Close Up):** There is a close up of a human face at any time in the video.


def detect_visible_face(
    feature_name: str, bucket: any, annotation_location: str
) -> bool:
    """Detect Visible Face (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        visible_face_1st_5_secs: visible face evaluation
    """
    visible_face_1st_5_secs, na = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {visible_face_1st_5_secs}")

    return visible_face_1st_5_secs


def detect_visible_face_close_up(
    feature_name: str, bucket: any, annotation_location: str
) -> tuple[bool, bool]:
    """Detect Visible Face (Close Up)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        visible_face_1st_5_secs,
        visible_face_close_up: visible face evaluation
    """
    na, visible_face_close_up = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {visible_face_close_up}")

    return visible_face_close_up


def detect(
    feature_name: str, bucket: any, annotation_location: str
) -> tuple[bool, bool]:
    """Detect Visible Face (First 5 seconds) & Visible Face (Close Up)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        visible_face_1st_5_secs,
        visible_face_close_up: visible face evaluation
    """
    face_annotation_results = get_face_annotations(bucket, annotation_location)
    # Feature Visible Face (First 5 seconds)
    visible_face_1st_5_secs = False

    # Feature Visible Face (Close Up)
    visible_face_close_up = False

    # Video API: Evaluate visible_face_1st_5_secs_feature and visible_face_close_up_feature
    if "face_detection_annotations" in face_annotation_results:
        # Video API: Evaluate visible_face_1st_5_secs_feature and visible_face_close_up_feature
        if face_annotation_results.get("face_detection_annotations"):
            for annotation in face_annotation_results.get("face_detection_annotations"):
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
            f"No Face annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    return visible_face_1st_5_secs, visible_face_close_up
