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

from annotations_evaluation.annotations_generation import Annotations
from helpers.annotations_helpers import calculate_time_seconds
from helpers.generic_helpers import load_blob, get_annotation_uri
from configuration import Configuration


def detect_presence_of_people(config: Configuration, feature_name: str, video_uri: str) -> bool:
    """Detect Presence of People
    Args:
        config: all the parameters
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        presence_of_people,
        presence_of_people_1st_5_secs: presence of people evaluation
    """
    presence_of_people, na = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {presence_of_people} \n")

    return presence_of_people


def detect_presence_of_people_1st_5_secs(config: Configuration, feature_name: str, video_uri: str) -> bool:
    """Detect Presence of People (First 5 seconds)
    Args:
        config: all the parameters
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        presence_of_people_1st_5_secs: presence of people evaluation
    """
    na, presence_of_people_1st_5_secs = detect(config, feature_name, video_uri)

    print(f"{feature_name}: {presence_of_people_1st_5_secs} \n")

    return presence_of_people_1st_5_secs


def detect(config: Configuration, feature_name: str, video_uri: str) -> tuple[bool, bool]:
    """Detect Presence of People & Presence of People (First 5 seconds)
    Args:
        config: all the parameters
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        presence_of_people,
        presence_of_people_1st_5_secs: presence of people evaluation
    """

    annotation_uri = (
        f"{get_annotation_uri(config, video_uri)}{Annotations.PEOPLE_ANNOTATIONS.value}.json"
    )
    people_annotation_results = load_blob(annotation_uri)

    # Feature Presence of People
    presence_of_people = False

    # Feature Presence of People (First 5 seconds)
    presence_of_people_1st_5_secs = False

    # Video API: Evaluate presence_of_people_feature and presence_of_people_1st_5_secs_feature
    if "person_detection_annotations" in people_annotation_results:
        # Video API: Evaluate presence_of_people_feature and presence_of_people_1st_5_secs_feature
        for people_annotation in people_annotation_results.get(
            "person_detection_annotations"
        ):
            for track in people_annotation.get("tracks"):
                # Check confidence against user defined threshold
                if track.get("confidence") >= config.confidence_threshold:
                    presence_of_people = True
                    start_time_secs = calculate_time_seconds(
                        track.get("segment"), "start_time_offset"
                    )
                    if start_time_secs < config.early_time_seconds:
                        presence_of_people_1st_5_secs = True
                    # Each segment includes track.get("timestamped_objects") that include
                    # characteristics - -e.g.clothes, posture of the person detected.
    else:
        print(
            f"No People annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    return presence_of_people, presence_of_people_1st_5_secs
