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

### REMOVE FOR COLAB - START
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    context_and_examples,
    use_llms,
    use_annotations,
)

from helpers.helpers import (
    LLMParameters,
    detect_feature_with_llm,
    find_elements_in_transcript,
    get_speech_transcript,
)

### REMOVE FOR COLAB - END


# @title 4 & 5) Attract: Supers & Supers with Audio

# @markdown **Features:**

# @markdown 1. **Supers:** Any supers (text overlays) have been incorporated at any time in the video.

# @markdown 2. **Supers with Audio**: The speech heard in the audio of the video matches OR is contextually supportive of the overlaid text shown on screen.

# Features
supers_feature = "Supers"
supers_with_audio_feature = "Supers with Audio"


def detect_supers(text_annotation_results: any, video_uri: str) -> bool:
    """Detect Supers
    Args:
        text_annotation_results: text annotations
        video_location: video location in gcs
    Returns:
        supers: evaluation
    """
    # Video API: Evaluate supers_feature
    supers = False

    if use_annotations:
        if "text_annotations" in text_annotation_results:
            if len(text_annotation_results.get("text_annotations")) > 0:
                supers = True
        else:
            print(
                f"No Text annotations found. Skipping {supers_feature} evaluation with Video Intelligence API."
            )

    if use_llms:
        # 1. Evaluate supers_feature
        supers_criteria = """Any supers (text overlays) have been incorporated at any time in the video."""
        prompt = (
            """Are there any supers (text overlays) at any time in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp where supers are found as well as the list of supers.
            {context_and_examples}
        """.replace(
                "{feature}", supers_feature
            )
            .replace("{criteria}", supers_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected = detect_feature_with_llm(supers_feature, prompt, llm_params)
        if feature_detected:
            supers = True

    print(f"{supers_feature}: {supers}")

    return supers


def detect_supers_with_audio(
    text_annotation_results: any,
    speech_annotation_results: any,
    video_uri: str,
) -> bool:
    """Detect Supers with Audio
    Args:
        text_annotation_results: text annotations
        speech_annotation_results: speech annotations
        video_location: video location in gcs
    Returns:
        supers_with_audio: evaluation
    """
    supers_with_audio = False
    detected_text_list = []

    if use_annotations:
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
                f"No Text or Speech annotations found. Skipping {supers_with_audio_feature} evaluation."
            )

    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        supers_with_audio_criteria = """The speech heard in the audio of the video matches OR is contextually
        supportive of the overlaid text shown on screen."""

        # LLM Only
        # 1. Evaluate supers_with_audio_feature
        prompt = (
            """Does the speech match any supers (text overlays) in the video or is the speech
            contextually supportive of the overlaid text shown on the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp where supers are found and the timestamp when the speech matches
            the supers or is contextually supportive of the overlaid text shown on the video.
            {context_and_examples}
        """.replace(
                "{feature}", supers_with_audio_feature
            )
            .replace("{criteria}", supers_with_audio_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected = detect_feature_with_llm(
            supers_with_audio_feature, prompt, llm_params
        )
        if feature_detected:
            supers_with_audio = True

        # Combination of Annotations + LLM
        if use_annotations:
            if "speech_transcriptions" in speech_annotation_results:
                # 1. Evaluate supers_with_audio_feature
                transcript = get_speech_transcript(
                    speech_annotation_results.get("speech_transcriptions")
                )
                # If transcript is empty, this feature should be False
                if transcript:
                    prompt = (
                        """Does the provided speech transcript matches any supers (text overlays) in the video or is the speech transcript
                        contextually supportive of the overlaid text shown on the video?
                        This is the speech transcript: "{transcript}"
                        Consider the following criteria for your answer: {criteria}
                        {context_and_examples}
                    """.replace(
                            "{feature}", supers_with_audio_feature
                        )
                        .replace("{transcript}", transcript)
                        .replace("{criteria}", supers_with_audio_criteria)
                        .replace("{context_and_examples}", context_and_examples)
                    )
                    # Use full video for this feature
                    llm_params.set_modality({"type": "video", "video_uri": video_uri})
                    feature_detected = detect_feature_with_llm(
                        supers_with_audio_feature, prompt, llm_params
                    )
                    if feature_detected:
                        supers_with_audio = True
                else:
                    supers_with_audio = False
            else:
                print(
                    f"No Speech annotations found. Skipping {supers_with_audio_feature} evaluation with LLM."
                )

    print(f"{supers_with_audio_feature}: {supers_with_audio}")

    return supers_with_audio
