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
    dynamic_cutoff_ms,
)

from helpers.annotations_helpers import get_shot_annotations

### REMOVE FOR COLAB - START


# @title 3) Attract: Dynamic Start

# @markdown **Features:**

# @markdown **Dynamic Start:** The first shot in the video changes in less than 3 seconds.


def detect_dynamic_start(
    feature_name: str, bucket: any, annotation_location: str
) -> dict:
    """Detects Dynamic Start
    Args:
        feature_name: the name of the feature
        brand_name: the brand to generate the video annotations for
        video_name: full video name
    Returns:
        dynamic_start: dynamic start evaluation
    """
    shot_annotation_results = get_shot_annotations(bucket, annotation_location)
    # Feature Dynamic Start
    dynamic_start = False

    # Video API: Evaluate dynamic_start_feature
    if "shot_annotations" in shot_annotation_results:
        first_shot_end_time_off_set = shot_annotation_results.get("shot_annotations")[0]
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
            f"No Shot annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {dynamic_start}")

    return dynamic_start
