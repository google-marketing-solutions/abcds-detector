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

"""Module to detect Direct: Audio Speech Early
Annotations used:
    1. Speech annotations to check for audio speech early
"""

### REMOVE FOR COLAB - START
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    early_time_seconds,
    confidence_threshold,
    use_llms,
    use_annotations,
    context_and_examples,
)

from helpers.annotations_helpers import (
    calculate_time_seconds,
    get_speech_transcript_1st_5_secs,
)

from helpers.vertex_ai_service import LLMParameters, detect_feature_with_llm

from helpers.generic_helpers import (
    get_reduced_uri,
)

### REMOVE FOR COLAB - START

# @title 20) Direct: Audio Speech Early

# @markdown **Features**

# @markdown **Audio Early (First 5 seconds):** Speech is detected in the audio in the first 5 seconds (up to 4.99s) of the video


def detect_audio_speech_early(speech_annotation_results: any, video_uri: str) -> bool:
    """Detect Audio Early (First 5 seconds)
    Args:
        speech_annotation_results: speech annotations
        video_uri: video location in gcs
    Returns:
        audio_speech_early_eval_details: audio early evaluation
    """
    # Feature Audio Early (First 5 seconds)
    audio_speech_early_feature = "Audio Early (First 5 seconds)"
    audio_speech_early = False
    # Remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
    audio_speech_early_criteria = """Speech is detected in the audio of the video."""
    audio_speech_early_eval_details = {
        "feature": audio_speech_early_feature,
        "feature_description": audio_speech_early_criteria,
        "feature_detected": audio_speech_early,
        "llm_details": [],
    }

    # Video API: Evaluate audio_speech_early_feature
    if use_annotations:
        if "speech_transcriptions" in speech_annotation_results:
            # Video API: Evaluate audio_speech_early_feature
            for speech_transcription in speech_annotation_results.get(
                "speech_transcriptions"
            ):
                for alternative in speech_transcription.get("alternatives"):
                    # Check confidence against user defined threshold
                    if (
                        alternative
                        and alternative.get("confidence") >= confidence_threshold
                    ):
                        # For 1st 5 secs, check elements and elements_categories in words
                        # since only the words[] contain times
                        words = (
                            alternative.get("words") if "words" in alternative else []
                        )
                        for word_info in words:
                            start_time_secs = calculate_time_seconds(
                                word_info, "start_time"
                            )
                            if start_time_secs <= early_time_seconds:
                                audio_speech_early = True
        else:
            print(
                f"No Speech annotations found. Skipping {audio_speech_early_feature} evaluation with Video Intelligence API."
            )

    # LLM: Evaluate audio_speech_early_feature
    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )

        # LLM Only
        # 1. Evaluate product_mention_speech_feature
        prompt = (
            """Is speech detected in the audio of the video?
            Consider the following criteria for your answer: {criteria}
            Only strictly use the speech of the video to answer.
            {context_and_examples}
        """.replace(
                "{feature}", audio_speech_early_feature
            )
            .replace("{criteria}", audio_speech_early_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        llm_params.set_modality({"type": "video", "video_uri": get_reduced_uri(video_uri)})
        feature_detected, llm_explanation = detect_feature_with_llm(
            audio_speech_early_feature, prompt, llm_params
        )
        if feature_detected:
            audio_speech_early = True

        # Include llm details
        audio_speech_early_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # Combination of Annotations + LLM
        if use_annotations:
            if "speech_transcriptions" in speech_annotation_results:
                # 1. Evaluate product_mention_speech_feature
                transcript_1st_5_secs = get_speech_transcript_1st_5_secs(
                    speech_annotation_results.get("speech_transcriptions")
                )
                prompt = (
                        """Does the provided speech transcript mention any words?
                        This is the speech transcript: "{transcript}"
                        Consider the following criteria for your answer: {criteria}
                        {context_and_examples}
                    """.replace(
                            "{transcript}", transcript_1st_5_secs
                        )
                        .replace("{feature}", audio_speech_early_feature)
                        .replace("{criteria}", audio_speech_early_criteria)
                        .replace("{context_and_examples}", context_and_examples)
                    )
                # Set modality to text since we are not using video for Annotations + LLM
                llm_params.set_modality({"type": "text"})
                # If transcript is empty, this feature should be False
                if transcript_1st_5_secs:
                    feature_detected, llm_explanation = detect_feature_with_llm(
                        audio_speech_early_feature, prompt, llm_params
                    )
                    if feature_detected:
                        audio_speech_early = True

                    # Include llm details
                    audio_speech_early_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": llm_explanation,
                        }
                    )
                else:
                    audio_speech_early = False
                    # Include default details
                    audio_speech_early_eval_details["llm_details"].append(
                        {
                            "llm_params": llm_params.__dict__,
                            "prompt": prompt,
                            "llm_explanation": "Annotations + LLM: Speech was not found in annotations.",
                        }
                    )
            else:
                print(
                    f"No Speech annotations found. Skipping {audio_speech_early_feature} evaluation with LLM."
                )

    print(f"{audio_speech_early_feature}: {audio_speech_early}")
    audio_speech_early_eval_details["feature_detected"] = audio_speech_early

    return audio_speech_early_eval_details
