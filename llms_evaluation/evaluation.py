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

"""Module to evaluate features for ABCDs using llms."""

import functools
from configuration import Configuration
from helpers.generic_helpers import get_reduced_uri, execute_tasks_in_parallel
from helpers.vertex_ai_service import LLMParameters, detect_features_with_llm_in_bulk
from prompts.prompts_generator import PromptParams, get_abcds_prompt
from feature_configs.features import get_groups_of_features


def evaluate_features(
    config: Configuration,
    evaluation_details: dict,
):
    """Evaluates ABCD features using LLMs."""
    print(
        f"Starting LLM evaluation for features grouped by {evaluation_details.get('group_by')}... \n"
    )
    prompt = get_abcds_prompt(
        evaluation_details.get("feature_configs"),
        evaluation_details.get("prompt_params"),
    )
    evaluation_details.get("llm_params").set_modality(
        {"type": "video", "video_uri": evaluation_details.get("video_uri")}
    )
    evaluated_features = detect_features_with_llm_in_bulk(
        config, prompt, evaluation_details.get("llm_params"), evaluation_details.get("group_by")
    )
    if config.verbose:
        if len(evaluated_features) == 0:
            print(
                f"WARNING: ABCD Detector was not able to process features for video {evaluation_details.get('video_uri')}... Please review. \n"
            )

    return evaluated_features


def evaluate_abcd_features_using_llms(
    config: Configuration,
    video_uri: str,
    prompt_params: PromptParams,
    llm_params: LLMParameters,
) -> list[dict]:
    """Evaluates ABCD features using LLMs.
    Builds functions that will execute in parallel using ThreadPoolExecutor
    Args:
        config: All the parameters
        video_uri: the video location in gcs.
        prompt_params: required params for the prompt.
        llm_params: required params for the LLM.
    Returns:
        feature_evaluations: a list of evaluated features
    """
    feature_evaluations = []
    tasks = []
    feature_groups = get_groups_of_features()
    uri = video_uri  # use full video uri by default

    for group_key in feature_groups:
        feature_configs = feature_groups.get(group_key)
        # Process the features that are not grouped individually
        # meaning, each will be a separate request to the LLM
        if group_key == "no_grouping":
            for f_confing in feature_configs:
                if f_confing.get("type") == "first_5_secs_video":
                    uri = get_reduced_uri(config, video_uri)
                else:
                    uri = video_uri
                # Build function to execute in parallel
                func = functools.partial(
                    evaluate_features,
                    config,
                    {
                        "group_by": f"{group_key}-{f_confing.get('id')}",
                        "video_uri": uri,
                        "feature_configs": [f_confing],  # process feature individually
                        "llm_params": llm_params,
                        "prompt_params": prompt_params,
                    },
                )
                # Add task to be process
                tasks.append(func)
        else:
            if group_key == "first_5_secs_video":
                uri = get_reduced_uri(config, video_uri)
            else:
                uri = video_uri
            # Build function to execute in parallel
            func = functools.partial(
                evaluate_features,
                config,
                {
                    "group_by": group_key,
                    "video_uri": uri,
                    "feature_configs": feature_configs,  # process each group
                    "llm_params": llm_params,
                    "prompt_params": prompt_params,
                },
            )
            # Add task to be process
            tasks.append(func)

    print("Starting ABCD evaluation using LLMs... \n")

    llm_evals = execute_tasks_in_parallel(tasks)

    # Process LLM results and create feature objs in the required format
    for evals in llm_evals:
        for evaluated_feature in evals:
            # Warning: This could be a hallucination - False Positive answer
            detected = (
                evaluated_feature.get("detected")
                or evaluated_feature.get("detected") == "True"
                or evaluated_feature.get("detected") == "true"
            )
            feature_evaluations.append(
                {
                    "id": evaluated_feature.get("id"),
                    "name": evaluated_feature.get("name"),
                    "category": evaluated_feature.get("category"),
                    "criteria": evaluated_feature.get("criteria"),
                    "detected": detected,
                    "llm_explanation": evaluated_feature.get("llm_explanation"),
                }
            )

    # Sort features for presentation
    feature_evaluations = sorted(
        feature_evaluations,
        key=lambda feature: feature.get("id"),
        reverse=False,
    )

    return feature_evaluations
