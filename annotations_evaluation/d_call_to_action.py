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

### REMOVE FOR COLAB - START

from input_parameters import branded_call_to_actions

from helpers.annotations_helpers import (
    find_elements_in_transcript,
    get_speech_annotations,
    get_text_annotations,
)


### REMOVE FOR COLAB - END

# @title 22 & 23) Direct: Call To Action (Text) & Call To Action (Speech)

# @markdown: **Features**

# @markdown **Call To Action (Text):** A 'Call To Action' phrase is detected in the video supers (overlaid text) at any time in the video.

# @markdown **Call To Action (Speech):** A 'Call To Action' phrase is heard or mentioned in the audio or speech at any time in the video.


CALL_TO_ACTION_API_LIST = [
    "LEARN MORE",
    "GET QUOTE",
    "APPLY NOW",
    "SIGN UP",
    "CONTACT US",
    "SUBSCRIBE",
    "DOWNLOAD",
    "BOOK NOW",
    "SHOP NOW",
    "BUY NOW",
    "DONATE NOW",
    "ORDER NOW",
    "PLAY NOW",
    "SEE MORE",
    "START NOW",
    "VISIT SITE",
    "WATCH NOW",
]

CALL_TO_ACTION_VERBS_APILIST = [
    "LEARN",
    "QUOTE",
    "APPLY",
    "SIGN UP",
    "CONTACT",
    "SUBSCRIBE",
    "DOWNLOAD",
    "BOOK",
    "SHOP",
    "BUY",
    "DONATE",
    "ORDER",
    "PLAY",
    "SEE",
    "START",
    "VISIT",
    "WATCH",
]


def detect_call_to_action_speech(
    feature_name: str, bucket: any, annotation_location: str
) -> bool:
    """Detect Call To Action (Speech)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        call_to_action_speech: call to action speech evaluation
    """
    speech_annotation_results = get_speech_annotations(bucket, annotation_location)
    # Feature Call To Action (Speech)
    call_to_action_speech = False

    CALL_TO_ACTION_API_LIST.extend(branded_call_to_actions)

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
            elements=CALL_TO_ACTION_API_LIST,
            elements_categories=[],
            apply_condition=False,
        )
    else:
        print(
            f"No Speech annotations found. Skipping {call_to_action_speech} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {call_to_action_speech}")

    return call_to_action_speech


def detect_call_to_action_text(
    feature_name: str, bucket: any, annotation_location: str
) -> bool:
    """Detect Call To Action (Text)
    Args:
        feature_name: the name of the feature
        bucket: gcs bucket where the annotations are stored
        annotation_location: path to the annotation json file
    Returns:
        call_to_action_text: call to action text evaluation
    """
    text_annotation_results = get_text_annotations(bucket, annotation_location)
    # Feature Call To Action (Text)
    call_to_action_text = False

    CALL_TO_ACTION_API_LIST.extend(branded_call_to_actions)

    # Video API: Evaluate call_to_action_text_feature
    if "text_annotations" in text_annotation_results:
        # Video API: Evaluate call_to_action_text_feature
        for text_annotation in text_annotation_results.get("text_annotations"):
            text = text_annotation.get("text")
            found_call_to_actions = [
                cta for cta in CALL_TO_ACTION_API_LIST if cta.lower() in text.lower()
            ]
            if len(found_call_to_actions) > 0:
                call_to_action_text = True
    else:
        print(
            f"No Text annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    print(f"{feature_name}: {call_to_action_text}")

    return call_to_action_text
