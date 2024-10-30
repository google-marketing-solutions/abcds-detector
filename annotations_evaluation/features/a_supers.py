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

"""Module to detect Attract: Supers & Supers with Audio
Annotations used:
    1. Text annotations to identify any supers
    2. Speech to identify supers in audio
"""

from annotations_evaluation.annotations_generation import Annotations
from helpers.generic_helpers import load_blob, get_annotation_uri
from helpers.annotations_helpers import find_elements_in_transcript
from configuration import Configuration


def detect_supers(config: Configuration, feature_name: str, video_uri: str) -> bool:
    """Detect Supers
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        supers: supers evaluation
    """

    annotation_uri = (
        f"{get_annotation_uri(config, video_uri)}{Annotations.GENERIC_ANNOTATIONS.value}.json"
    )
    text_annotation_results = load_blob(annotation_uri)

    # Feature Supers
    supers = False

    # Video API: Evaluate supers_feature
    if "text_annotations" in text_annotation_results:
        if len(text_annotation_results.get("text_annotations")) > 0:
            supers = True
    else:
        print(
            f"No Text annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {supers} \n")

    return supers


def detect_supers_with_audio(config: Configuration, feature_name: str, video_uri: str) -> bool:
    """Detect Supers with Audio
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        supers_with_audio: supers with audio evaluation
    """

    t_annotation_uri = (
        f"{get_annotation_uri(config, video_uri)}{Annotations.GENERIC_ANNOTATIONS.value}.json"
    )
    text_annotation_results = load_blob(t_annotation_uri)

    s_annotation_uri = (
        f"{get_annotation_uri(config, video_uri)}{Annotations.SPEECH_ANNOTATIONS.value}.json"
    )
    speech_annotation_results = load_blob(s_annotation_uri)

    # Feature Supers with Audio
    supers_with_audio = False

    detected_text_list = []

    # Video API: Evaluate supers_with_audio_feature
    if (
        "text_annotations" in text_annotation_results
        and "speech_transcriptions" in speech_annotation_results
    ):
        # Build list of found supers
        for text_annotation in text_annotation_results.get("text_annotations"):
            detected_text_list.append(text_annotation.get("text"))

        # Video API: Evaluate supers_with_audio
        (
            supers_with_audio,
            na,
        ) = find_elements_in_transcript(
            config,
            speech_transcriptions=speech_annotation_results.get(
                "speech_transcriptions"
            ),
            elements=detected_text_list,
            elements_categories=[],
            apply_condition=True,  # flag to filter out text with less than x chars. This is
            # only needed when elements come from text annotations since words are sometimes
            # 1 character only.
        )
    else:
        print(
            f"No Text or Speech annotations found. Skipping {feature_name} evaluation."
        )

    print(f"{feature_name}: {supers_with_audio} \n")

    return supers_with_audio
