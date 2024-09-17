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
    early_time_seconds,
)

from helpers.annotations_helpers import calculate_time_seconds, get_shot_annotations


### REMOVE FOR COLAB - END

# @title 1, 2) Attract: Quick Pacing & Quick Pacing (First 5 seconds)

# @markdown **Features:**

# @markdown **Quick Pacing:** Within ANY 5 consecutive seconds there are 5 or more shots in the video. These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms, depth of field changes, tracking shots and movement of the camera.

# @markdown **Quick Pacing (First 5 seconds):** There are at least 5 shot changes or visual cuts detected within the first 5 seconds (up to 4.99s) of the video. These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms, depth of field changes, tracking shots and movement of the camera.


def detect_quick_pacing(
    feature_name: str, bucket: any, annotation_location: str
) -> dict:
    """Detect Quick Pacing
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        quick_pacing: quick pacing evaluation
    """
    quick_pacing, na = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {quick_pacing}")

    return quick_pacing


def detect_quick_pacing_1st_5_secs(
    feature_name: str, bucket: any, annotation_location: str
) -> dict:
    """Detect Quick Pacing (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        quick_pacing, quick_pacing_1st_5_secs: quick pacing evaluation
    """
    na, quick_pacing_1st_5_secs = detect(feature_name, bucket, annotation_location)

    print(f"{feature_name}: {quick_pacing_1st_5_secs}")

    return quick_pacing_1st_5_secs


def detect(
    feature_name: str, bucket: any, annotation_location: str
) -> tuple[bool, bool]:
    """Detect Quick Pacing & Quick Pacing (First 5 seconds)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        quick_pacing, quick_pacing_1st_5_secs: quick pacing evaluation
    """
    shot_annotation_results = get_shot_annotations(bucket, annotation_location)
    required_secs_for_quick_pacing = 5
    required_shots_for_quick_pacing = 5
    # Feature Quick Pacing
    quick_pacing = False
    total_shots_count = 0
    total_time_all_shots = 0
    # Feature Quick Pacing (First 5 secs)
    quick_pacing_1st_5_secs = False
    total_shots_count_1st_5_secs = 0

    # Video API: Evaluate quick_pacing_feature and quick_pacing_1st_5_secs_feature
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
            f"No Shot annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    return quick_pacing, quick_pacing_1st_5_secs
