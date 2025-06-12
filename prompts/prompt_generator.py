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

from helpers.generic_helpers import get_call_to_action_api_list
from configuration import Configuration
from models import VideoFeature, PromptConfig


class PromptGenerator:
    """Class to generate the prompts that will contain the ABCD features."""

    def __init__(self):
        pass

    def get_abcds_prompt(
        self, features: list[VideoFeature], config: Configuration
    ) -> PromptConfig:
        """Gets the prompt with required ABCD features
        for full videos and first 5 secs videos
        Returns:
            prompt: string prompt template
        """
        features_questions = self.get_features_prompt_template(features, config)

        system_instructions = """
            You are a creative expert who analyzes and labels video ads to answer
            specific questions about the content in the video and how it adheres to a set of features.
            Answer the following questions with either "True" or "False" and provide a detailed explanation to
            support your answer. The explanation should be thorough and logically sound, incorporating relevant
            facts and reasoning. Only base your answers strictly on what information is available in the video
            attached. Do not make up any information that is not part of the video.
            Please present the information in a VALID JSON format list like the example below:
            [
                {
                    "id": "",
                    "name": "",
                    "category": "",
                    "criteria": "",
                    "detected": "True/False",
                    "llm_explanation": "..."
                }
            ]

            Please remove any double quotes from the values in the JSON object. The only double quotes should be in the JSON keys.
            Just return the JSON object without any other text before or after the brackets.
        """

        prompt = """These are the questions that you have to answer for each feature:
        {features_questions}""".replace(
            "{features_questions}", features_questions
        )

        prompt_config = PromptConfig(
            prompt=prompt, system_instructions=system_instructions
        )

        return prompt_config

    def get_features_prompt_template(
        self, features: list[VideoFeature], config: Configuration
    ) -> str:
        """Gets features prompt template"""
        features_prompt = ""
        for feature in features:
            # Replace input parameters in instructions
            instructions = self.augment_instructions(feature, config)
            features_prompt += f"""
            Feature ID: {feature.id}
            Feature Name: {feature.name}
            Feature Category: {feature.category}
            Feature Criteria: {feature.evaluation_criteria}
            Question: {feature.prompt_template}
            {instructions} \n\n
        """
        features_prompt = (
            features_prompt.replace("{brand_name}", config.brand_name)
            .replace("{brand_variations}", ", ".join(config.brand_variations))
            .replace("{branded_products}", ", ".join(config.branded_products))
            .replace(
                "{branded_products_categories}",
                ", ".join(config.branded_products_categories),
            )
            .replace(
                "{branded_call_to_actions_str}",
                ", ".join(config.branded_call_to_actions),
            )
        )
        return features_prompt

    def augment_instructions(self, feature: VideoFeature, config: Configuration) -> str:
        """Augment LLM instructions in the prompt"""
        call_to_actions = ", ".join(get_call_to_action_api_list()) + ", ".join(
            config.branded_call_to_actions
        )
        instructions = (
            "\n".join(feature.extra_instructions)
            .replace("{criteria}", feature.evaluation_criteria)  # TODO fix this
            .replace("{call_to_actions}", ", ".join(call_to_actions))
        )
        return instructions


prompt_generator = PromptGenerator()
