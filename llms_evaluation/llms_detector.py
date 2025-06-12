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

"""Module to evaluate and detect features using LLMs."""

import functools
from configuration import Configuration
from helpers.generic_helpers import execute_tasks_in_parallel
from gcp_api_services.gemini_api_service import (
    LLMParameters,
    get_gemini_api_service,
)
from gcp_api_services.gcs_api_service import gcs_api_service
from prompts.prompt_generator import prompt_generator
from feature_configs.features import get_groups_of_features
from models import VIDEO_RESPONSE_SCHEMA


class LLMDetector:
    """Class to evaluate and detect features using LLMs."""

    def __init__(self):
        pass

    def evaluate_features(
        self,
        config: Configuration,
        evaluation_details: dict,
    ):
        """Evaluates ABCD features using LLMs."""
        print(
            f"Starting LLM evaluation for features grouped by {evaluation_details.get('group_by')}... \n"
        )
        prompt_config = prompt_generator.get_abcds_prompt(
            evaluation_details.get("feature_configs"),
            config,
        )
        # Set modality for API
        config.llm_params.set_modality(
            {"type": "video", "video_uri": evaluation_details.get("video_uri")}
        )
        # Set the required schema for the LLM response
        config.llm_params.generation_config["response_schema"] = VIDEO_RESPONSE_SCHEMA
        evaluated_features = get_gemini_api_service(config).execute_gemini_with_genai(
            prompt_config, config.llm_params
        )

        if config.verbose:
            if len(evaluated_features) == 0:
                print(
                    f"WARNING: ABCD Detector was not able to process features for video {evaluation_details.get('video_uri')}... Please review. \n"
                )

        return evaluated_features

    def evaluate_abcd_features_using_llms(
        self,
        config: Configuration,
        video_uri: str,
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
                        uri = gcs_api_service.get_reduced_uri(config, video_uri)
                    else:
                        uri = video_uri
                    # Build function to execute in parallel
                    func = functools.partial(
                        self.evaluate_features,
                        config,
                        {
                            "group_by": f"{group_key}-{f_confing.get('id')}",
                            "video_uri": uri,
                            "feature_configs": [
                                f_confing
                            ],  # process feature individually
                            "llm_params": llm_params,
                        },
                    )
                    # Add task to be process
                    tasks.append(func)
            else:
                if group_key == "first_5_secs_video":
                    uri = gcs_api_service.get_reduced_uri(config, video_uri)
                else:
                    uri = video_uri
                # Build function to execute in parallel
                func = functools.partial(
                    self.evaluate_features,
                    config,
                    {
                        "group_by": group_key,
                        "video_uri": uri,
                        "feature_configs": feature_configs,  # process each group
                        "llm_params": llm_params,
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


llm_detector = LLMDetector()
