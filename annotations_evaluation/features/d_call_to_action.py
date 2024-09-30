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

"""Module to detect Direct: Call To Action (Text) & Call To Action (Speech)
Annotations used:
    1. Text annotations to detect call to actions
    2. Speech annotations to detect call to actions in audio or speech
"""

from annotations_evaluation.annotations_generation import Annotations
from helpers.annotations_helpers import find_elements_in_transcript
from helpers.generic_helpers import load_blob, get_annotation_uri, get_call_to_action_api_list
from input_parameters import branded_call_to_actions


def detect_call_to_action_speech(feature_name: str, video_uri: str) -> bool:
    """Detect Call To Action (Speech)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        call_to_action_speech: call to action speech evaluation
    """

    annotation_uri = (
        f"{get_annotation_uri(video_uri)}{Annotations.SPEECH_ANNOTATIONS.value}.json"
    )
    speech_annotation_results = load_blob(annotation_uri)

    # Feature Call To Action (Speech)
    call_to_action_speech = False

    call_to_action_examples = get_call_to_action_api_list()
    all_call_to_actions = [cta for cta in call_to_action_examples]
    all_call_to_actions.extend(branded_call_to_actions)

    # Video API: Evaluate call_to_action_speech_feature
    if "speech_transcriptions" in speech_annotation_results:
        # Video API: Evaluate call_to_action_speech_feature
        (
            call_to_action_speech,
            na,
        ) = find_elements_in_transcript(
            speech_transcriptions=speech_annotation_results.get(
                "speech_transcriptions"
            ),
            elements=all_call_to_actions,
            elements_categories=[],
            apply_condition=False,
        )
    else:
        print(
            f"No Speech annotations found. Skipping {call_to_action_speech} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {call_to_action_speech} \n")

    return call_to_action_speech


def detect_call_to_action_text(feature_name: str, video_uri: str) -> bool:
    """Detect Call To Action (Text)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        call_to_action_text: call to action text evaluation
    """

    annotation_uri = (
        f"{get_annotation_uri(video_uri)}{Annotations.GENERIC_ANNOTATIONS.value}.json"
    )
    text_annotation_results = load_blob(annotation_uri)

    # Feature Call To Action (Text)
    call_to_action_text = False

    call_to_action_examples = get_call_to_action_api_list()
    all_call_to_actions = [cta for cta in call_to_action_examples]
    all_call_to_actions.extend(branded_call_to_actions)

    # Video API: Evaluate call_to_action_text_feature
    if "text_annotations" in text_annotation_results:
        # Video API: Evaluate call_to_action_text_feature
        for text_annotation in text_annotation_results.get("text_annotations"):
            text = text_annotation.get("text")
            found_call_to_actions = [
                cta for cta in all_call_to_actions if cta.lower() in text.lower()
            ]
            if len(found_call_to_actions) > 0:
                call_to_action_text = True
    else:
        print(
            f"No Text annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {call_to_action_text} \n")

    return call_to_action_text
