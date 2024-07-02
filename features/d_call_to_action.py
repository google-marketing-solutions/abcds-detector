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
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    use_llms,
    use_annotations,
    context_and_examples,
)

from helpers.helpers import (
    LLMParameters,
    detect_feature_with_llm,
    find_elements_in_transcript,
    get_speech_transcript,
)

### REMOVE FOR COLAB - END

# @title 22 & 23) Direct: Call To Action (Text) & Call To Action (Speech)

# @markdown: **Features**

# @markdown **Call To Action (Text):** A 'Call To Action' phrase is detected in the video supers (overlaid text) at any time in the video.

# @markdown **Call To Action (Speech):** A 'Call To Action' phrase is heard or mentioned in the audio or speech at any time in the video.

# Features
call_to_action_text_feature = "Call To Action (Text)"
call_to_action_speech_feature = "Call To Action (Speech)"

call_to_action_api_list = [
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
call_to_action_verbs_api_list = [
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
    speech_annotation_results: any,
    video_uri: str,
    branded_call_to_actions: list[str],
) -> bool:
    """Detect Call To Action (Speech)
    Args:
        speech_annotation_results: speech annotations
        video_location: video location in gcs
        branded_call_to_actions: list of branded call to actions
    Returns:
        call_to_action_speech: evaluation
    """
    call_to_action_speech = False
    call_to_action_api_list.extend(branded_call_to_actions)

    if use_annotations:
        if "speech_transcriptions" in speech_annotation_results:
            # Video API: Evaluate call_to_action_speech_feature
            (
                call_to_action_speech,
                na,
            ) = find_elements_in_transcript(
                speech_transcriptions=speech_annotation_results.get("speech_transcriptions"),
                elements=call_to_action_api_list,
                elements_categories=[],
                apply_condition=False
            )
        else:
            print(
                f"No Speech annotations found. Skipping {call_to_action_speech} evaluation with Video Intelligence API."
            )

    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        call_to_action_speech_criteria = """A 'Call To Action' phrase is heard or mentioned in the audio or speech
        at any time in the video."""

        # LLM Only
        prompt = (
            """Is any call to action heard or mentioned in the speech of the video?
            Consider the following criteria for your answer: {criteria}
            Some examples of call to actions are: {call_to_actions}
            Provide the exact timestamp when the call to actions are heard or mentioned in the
            speech of the video.
            {context_and_examples}
        """.replace(
                "{call_to_actions}", ", ".join(call_to_action_api_list)
            )
            .replace("{feature}", call_to_action_speech_feature)
            .replace("{criteria}", call_to_action_speech_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected = detect_feature_with_llm(
            call_to_action_speech_feature, prompt, llm_params
        )
        if feature_detected:
            call_to_action_speech = True

        # Combination of Annotations + LLM
        if use_annotations:
            if "speech_transcriptions" in speech_annotation_results:
                # Evaluate call_to_action_speech_feature
                transcript = get_speech_transcript(
                    speech_annotation_results.get("speech_transcriptions")
                )
                # If transcript is empty, this feature should be False
                if transcript:
                    prompt = (
                        """Does the provided speech transcript mention any call to actions in the video?
                        This is the speech transcript: "{transcript}"
                        Consider the following criteria for your answer: {criteria}
                        Some examples of call to actions are: {call_to_actions}
                        {context_and_examples}
                    """.replace(
                            "{call_to_actions}", ", ".join(call_to_action_api_list)
                        )
                        .replace("{transcript}", transcript)
                        .replace("{feature}", call_to_action_speech_feature)
                        .replace("{criteria}", call_to_action_speech_criteria)
                        .replace("{context_and_examples}", context_and_examples)
                    )
                    # Set modality to text since we are not using video for Annotations + LLM
                    llm_params.set_modality({"type": "text"})
                    feature_detected = detect_feature_with_llm(
                        call_to_action_speech_feature, prompt, llm_params
                    )
                    if feature_detected:
                        call_to_action_speech = True
                else:
                    call_to_action_speech = False
            else:
                print(
                    f"No Speech annotations found. Skipping {call_to_action_speech_feature} evaluation with Video Intelligence API."
                )

    print(f"{call_to_action_speech_feature}: {call_to_action_speech}")

    return call_to_action_speech


def detect_call_to_action_text(
    text_annotation_results: any,
    video_uri: str,
    branded_call_to_actions: list[str],
) -> bool:
    """Detect Call To Action (Text)
    Args:
        text_annotation_results: text annotations
        video_location: video location in gcs
        branded_call_to_actions: list of branded call to actions
    Returns:
        call_to_action_text: evaluation
    """
    call_to_action_text = False
    call_to_action_api_list.extend(branded_call_to_actions)

    if use_annotations:
        if "text_annotations" in text_annotation_results:
            # Video API: Evaluate call_to_action_text_feature
            for text_annotation in text_annotation_results.get("text_annotations"):
                text = text_annotation.get("text")
                found_call_to_actions = [
                    cta
                    for cta in call_to_action_api_list
                    if cta.lower() in text.lower()
                ]
                if len(found_call_to_actions) > 0:
                    call_to_action_text = True
        else:
            print(
                f"No Text annotations found. Skipping {call_to_action_text_feature} evaluation with Video Intelligence API."
            )

    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # 1. Evaluate call_to_action_text_feature
        call_to_action_text_criteria = """A 'Call To Action' phrase is detected in the video supers (overlaid text)
        at any time in the video."""
        prompt = (
            """Is any call to action detected in any text overlay at any time in the video?
            Consider the following criteria for your answer: {criteria}
            Some examples of call to actions are: {call_to_actions}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when the call to action is detected in any text overlay in the video.
            {context_and_examples}
        """.replace(
                "{call_to_actions}", ", ".join(call_to_action_api_list)
            )
            .replace("{feature}", call_to_action_text_feature)
            .replace("{criteria}", call_to_action_text_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected = detect_feature_with_llm(
            call_to_action_text_feature, prompt, llm_params
        )
        if feature_detected:
            call_to_action_text = True

    print(f"{call_to_action_text_feature}: {call_to_action_text}")

    return call_to_action_text
