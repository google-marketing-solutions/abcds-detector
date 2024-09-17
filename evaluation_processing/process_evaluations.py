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

"""Module to evaluate features for ABCDs in full video and first 5 seconds video."""

### REMOVE FOR COLAB - START

from functools import partial
import concurrent.futures

from helpers.generic_helpers import (
    get_n_secs_video_uri_from_uri,
    get_bucket,
)
from helpers.vertex_ai_service import LLMParameters
from prompts.prompts_generator import PromptParams
from input_parameters import USE_ANNOTATIONS, USE_LLMS
import annotations_evaluation.annotations_all_features as annotations_module

from llm_evaluation.llm_all_features import evaluate_features_with_llm

from features.features import get_feature_configs, get_feature_configs_by_type

### REMOVE FOR COLAB - END


def evaluate_abcd_features(
    brand_name: str,
    video_name: str,
    video_uri: str,
    prompt_params: PromptParams,
    llm_params: LLMParameters,
) -> list[dict]:
    """Evaluates ABCD features using annotations and LLMs.
    Args:
        video_uri: the video location in gcs.
        prompt_params: required params for the prompt.
        llm_params: required params for the LLM.
    Returns:
        features: a list of evaluated features
    """
    all_features_configs = get_feature_configs()
    feature_evaluations: list = []

    if USE_ANNOTATIONS:

        print("ABCD evaluation using annotations... \n")
        bucket = get_bucket()
        annotation_location = f"{brand_name}/annotations/{video_name}"

        # Process annotations for all features
        for feature_config in all_features_configs:
            print(
                f"Stating annotation evaluation for feature {feature_config.get('name')}... \n"
            )
            function_name = feature_config.get("annotations_function")
            feature_detected = False
            if function_name:
                func = getattr(annotations_module, function_name)
                feature_detected = func(
                    feature_config.get("name"), bucket, annotation_location
                )
            # Add annotation evaluation
            build_feature_evaluation_result(
                feature_evaluations, feature_config, feature_detected
            )

    if USE_LLMS:

        print("ABCDs evaluation using LLMs... \n")

        eval_details = [
            {
                "evaluation_type": "full_video",
                "video_uri": video_uri,
                "feature_configs": get_feature_configs_by_type("full_video"),
                "llm_params": llm_params,
                "prompt_params": prompt_params,
            },
            {
                "evaluation_type": "1st_5_secs",
                "video_uri": get_n_secs_video_uri_from_uri(video_uri, "1st_5_secs"),
                "feature_configs": get_feature_configs_by_type("first_5_secs_video"),
                "llm_params": llm_params,
                "prompt_params": prompt_params,
            },
        ]
        # Evaluate llm features in paralell to optimize execution
        llm_evals: list[list] = []
        llm_func = partial(evaluate_features_with_llm)
        with concurrent.futures.ThreadPoolExecutor(3) as executor:
            evals = executor.map(llm_func, eval_details)
            llm_evals.extend(evals)

        process_llm_evaluated_features(feature_evaluations, llm_evals)

        feature_evaluations = sorted(
            feature_evaluations,
            key=lambda x: int(x.get("idx")),
            reverse=False,
        )

    return feature_evaluations


def build_feature_evaluation_result(
    feature_evaluations: list[dict],
    feature_config: dict,
    feature_detected: bool,
) -> dict:
    """TODO"""
    # Check if feature was already processed and stored
    processed_feature = get_processed_feature_by_id(
        feature_evaluations, feature_config.get("id")
    )
    # If feature was already processed and stored using annotations,
    # override value with LLM evaluation
    if processed_feature:
        # Override annotations only if feature was detected by LLM.
        if feature_detected:
            processed_feature["feature_detected"] = feature_detected
    else:
        processed_feature = {
            "idx": feature_config.get("idx"),
            "feature_id": feature_config.get("id"),
            "feature_name": feature_config.get("name"),
            "feature_description": feature_config.get("criteria"),
            "feature_detected": feature_detected,
        }
        # Insert at index to keep order regardless of how features are processed
        feature_evaluations.append(processed_feature)

    return processed_feature


def process_llm_evaluated_features(
    feature_evaluations: list[dict],
    llm_evals: list[dict],
) -> None:
    """TODO"""
    for evals in llm_evals:
        for llm_evaluated_feature in evals:
            # Warning: This could be a hallucination - False Positive answer
            feature_detected = (
                llm_evaluated_feature.get("feature_detected") == "True"
                or llm_evaluated_feature.get("feature_detected") == "true"
            )
            # Add llm_feature details as new results entry
            new_entry = build_feature_evaluation_result(
                feature_evaluations,
                llm_evaluated_feature,
                feature_detected,
            )
            new_entry["llm_explanation"] = llm_evaluated_feature.get("llm_explanation")


def get_processed_feature_by_id(
    feature_evaluations: list[dict], feature_id: str
) -> dict:
    """TODO"""
    processed_feature = [
        feature
        for feature in feature_evaluations
        if feature.get("feature_id") == feature_id
    ]
    # If feature found, it's the first element
    if len(processed_feature) > 0:
        return processed_feature[0]
    return None
