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

"""Module to evaluate features for ABCDs using LLMs"""

### REMOVE FOR COLAB - START

from input_parameters import STORE_PROMPT, VERBOSE
from helpers.generic_helpers import store_prompt_in_file
from helpers.vertex_ai_service import detect_features_with_llm_in_bulk
from prompts.prompts_generator import get_abcds_prompt

### REMOVE FOR COLAB - END


def evaluate_features_with_llm(
    evaluation_details: dict,
):
    """TODO"""
    print(f"Starting LLM evaluation for features using {evaluation_details.get('evaluation_type')}... \n")

    prompt_full_video = get_abcds_prompt(
        evaluation_details.get("feature_configs"),
        evaluation_details.get("prompt_params"),
    )
    if STORE_PROMPT:
        store_prompt_in_file(
            file_name=f"prompt_{evaluation_details.get('evaluation_type')}",
            prompt=prompt_full_video,
        )
    # Use full video for this feature
    evaluation_details.get("llm_params").set_modality(
        {"type": "video", "video_uri": evaluation_details.get("video_uri")}
    )
    evaluated_features = detect_features_with_llm_in_bulk(
        prompt_full_video, evaluation_details.get("llm_params")
    )

    if VERBOSE:
        if len(evaluated_features) == 0:
            print(
                f"WARNING: ABCD Detector was not able to process features_full_video for video {evaluation_details.get('video_uri')}... Please review. \n"
            )

    return evaluated_features
