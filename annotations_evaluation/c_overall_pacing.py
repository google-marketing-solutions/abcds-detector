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
    avg_shot_duration_seconds,
)

from helpers.annotations_helpers import calculate_time_seconds, get_shot_annotations

### REMOVE FOR COLAB - END

# @title 21) Connect: Overall Pacing

# @markdown **Features:**

# @markdown **Overall Pacing:** The pace of the video is greater than 2 seconds per shot/frame


def detect_overall_pacing(feature_name: str, bucket: any, annotation_location: str) -> dict:
    """Detect Overall Pacing
    Args:
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        overall_pacing: overall pacing evaluation
    """
    shot_annotation_results = get_shot_annotations(bucket, annotation_location)
    # Feature Overall Pacing
    overall_pacing = False
    total_time_all_shots = 0
    total_shots = 0

    # Video API: Evaluate overall_pacing_feature
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
            f"No Shot annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {overall_pacing}")

    return overall_pacing
