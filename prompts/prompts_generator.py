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

"""Module to define the prompts that will contain the ABCD features."""

### REMOVE FOR COLAB - START

from helpers.utils import get_call_to_action_api_list

### REMOVE FOR COLAB - END


class PromptParams:
    """PromptParams class to define the required parameters for the llm evaluation"""

    brand_name: str
    brand_variations: list[str]
    branded_products: list[str]
    branded_products_categories: list[str]
    branded_call_to_actions: list[str]

    def __init__(
        self,
        brand_name: list[str],
        brand_variations: list[str],
        branded_products: list[str],
        branded_products_categories: list[str],
        branded_call_to_actions: list[str],
    ):
        self.brand_name = brand_name
        self.brand_variations = brand_variations
        self.branded_products = branded_products
        self.branded_products_categories = branded_products_categories
        self.branded_call_to_actions = branded_call_to_actions


def get_abcds_prompt(features: list[dict], prompt_params: PromptParams) -> str:
    """Gets the prompt with required ABCD features
    for full videos and first 5 secs videos
    Returns:
        prompt: string prompt template
    """
    features_questions = get_features_prompt_template(features, prompt_params)

    prompt = """You are a creative expert who analyzes and labels video ads to answer
    specific questions about the content in the video and how it adheres to a set of features.
    Answer the following questions with either "True" or "False" and provide a detailed explanation to
    support your answer. The explanation should be thorough and logically sound, incorporating relevant
    facts and reasoning. Only base your answers strictly on what information is available in the video
    attached. Do not make up any information that is not part of the video.
    Please present the information in a VALID JSON format list like the example below:
    [
        {
            "idx": "",
            "id": "",
            "name": "",
            "criteria": "criteria"
            "feature_detected": "True/False",
            "llm_explanation": "..."
        }
    ]

    Use the Feature Index as the idx field in the JSON.

    These are the questions that you have to answer for each feature:
    {features_questions}""".replace(
        "{features_questions}", features_questions
    )
    return prompt


def get_features_prompt_template(
    features: list[dict], prompt_params: PromptParams
) -> str:
    """TODO
    Returns:
        prompt: string prompt template
    """
    features_prompt = ""
    for feature in features:
        # Replace input parameters in instructions
        instructions = augment_instructions(feature, prompt_params)
        features_prompt += f"""
        Feature Index: {feature.get("idx")}
        Feature ID: {feature.get("id")}
        Feature Name: {feature.get("name")}
        Feature Criteria: {feature.get("criteria")}
        Question: {feature.get("question")}
        {instructions} \n\n
    """
    features_prompt = (
        features_prompt.replace("{brand_name}", prompt_params.brand_name)
        .replace("{brand_variations}", ", ".join(prompt_params.brand_variations))
        .replace("{branded_products}", ", ".join(prompt_params.branded_products))
        .replace(
            "{branded_products_categories}",
            ", ".join(prompt_params.branded_products_categories),
        )
        .replace(
            "{branded_call_to_actions_str}",
            ", ".join(prompt_params.branded_call_to_actions),
        )
    )
    return features_prompt


def augment_instructions(feature: dict, prompt_params: PromptParams) -> str:
    """TODO"""
    call_to_actions = ", ".join(get_call_to_action_api_list()) + ", ".join(
        prompt_params.branded_call_to_actions
    )
    instructions = (
        "\n".join(feature.get("instructions"))
        .replace("{criteria}", feature.get("criteria"))
        .replace("{call_to_actions}", ", ".join(call_to_actions))
    )
    return instructions
