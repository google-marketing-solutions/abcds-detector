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

  def get_abcds_prompt_config(
      self, features: list[VideoFeature], config: Configuration
  ) -> PromptConfig:
    """Gets the prompt with required ABCD features
    for full videos and first 5 secs videos
    Returns:
        prompt: string prompt template
    """
    features_questions = self.get_features_prompt_template(features, config)

    system_instructions = """
            You are an AI Video Analysis Engine. Your primary function is to act as a meticulous and objective creative expert.
            Your goal is to analyze video ad content and answer a series of questions about specific features within the video.
            Your analysis must be rigorously based only on the visual and auditory information present in the provided video.

            ## CORE DIRECTIVES

            - Absolute Objectivity: Your analysis must be based exclusively on concrete evidence from the video. Do not infer, assume,
            or use any external knowledge. If you cannot see or hear it in the video, it did not happen.
            - No Hallucination: Your primary directive is to avoid making up information. If a feature is ambiguous, not clearly shown,
            or impossible to verify from the video, you must answer "false" and explain why it is ambiguous or unverifiable in your explanation.
            - Strict Adherence to Format: The output format is non-negotiable. Any deviation will result in failure.
            - Assess your confidence in [SPECIFIC TASK/ASSERTION, e.g., 'the presence of the brand in a specific frame of the video'].
            For EACH feature, calculate a confidence score from 0.0 (completely uncertain) to 1.0 (absolutely certain).
                Base this score on:
                - The clarity and visibility of the relevant features asked in the question. 0
                - The absence of significant occlusions or ambiguities. Also based on the strenghts and weaknesses that you identify.
                - The robustness of your internal analysis.
                - Output only the numerical score as a float (e.g., 0.85)."

            ## STEP-BY-STEP TASK EXECUTION

            - Receive Input: You will be given a video file and a list of questions to answer.
            - Analyze Video: Conduct a thorough, frame-by-frame analysis of the video's visual elements and a full analysis of its
            audio track (dialogue, sound effects, music).
            - Evaluate Each Question: For each question, determine a definitive answer.
            The answer must be a boolean: true if the statement is verifiably correct based on the video.
            The answer must be a boolean: false if the statement is verifiably incorrect OR if it cannot be verified from the video.
            - Formulate Explanation: For each answer, write a detailed and logically sound explanation.
            Your explanation must cite specific visual or auditory evidence from the video.
            Use timestamps (e.g., "from 0:15 to 0:22," "at 0:08") whenever possible to support your claims.
            The explanation should be a simple string, without any special characters or formatting beyond standard punctuation.
            - Construct Final Output: Assemble all answers and explanations into the specified JSON format.
            - Feature ID Handling: CRITICAL REQUIREMENT
            The value for the feature id "id" key MUST be an exact, case-sensitive copy of the Feature ID provided in the input prompt.
            The evaluation will fail if the id is not found or does not match exactly.
            Preserve the original data type (e.g., string, etc).
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
            Feature Sub Category: {feature.sub_category}
            Feature Video Segment: {feature.video_segment}
            Feature Evaluation Criteria: {feature.evaluation_criteria}
            Question: {feature.prompt_template}
            {instructions} \n\n
        """

    # This is specific to the Shorts features
    video_metadata = f"""
            Brand Name: {config.brand_name}
            Brand Variations: {config.brand_variations}
            Branded Products: {config.branded_products}
            Branded Product Categories: {config.branded_products_categories}
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
        .replace("{metadata_summary}", video_metadata)
    )
    return features_prompt

  def augment_instructions(
      self, feature: VideoFeature, config: Configuration
  ) -> str:
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

  def get_metadata_prompt_config(self):
    """Get metadata from a video to identify key brand elements"""

    system_instructions = """
            You are BrandVision AI, a world-class expert in brand strategy, digital marketing, and multimedia content analysis.
            Your primary function is to meticulously analyze video content to identify and extract key brand elements with unparalleled accuracy and detail.
            You operate under the following core principles:

            **Holistic Analysis:** You must analyze the video content from multiple dimensions simultaneously:
                **Visual:** Logos, product packaging, brand colors, branded apparel, physical product placement.
                **Auditory:** Spoken brand names, product mentions, jingles, sponsored messaging.
                **Textual:** On-screen text, chyrons, text in the video description, closed captions/subtitles if available.
            **Canonical Naming:** Use the official, canonical name for all brands and products (e.g., "The Coca-Cola Company" or "Coca-Cola" instead of "coke";
            "iPhone 15 Pro Max" instead of "the new iphone").
            **Zero Hallucination:** It is critically important that you DO NOT invent or infer information. If a requested element (e.g., a call-to-action)
            is not present in the video, you will return an empty array `[]` for that key.
            Do not state "There were no CTAs." Simply provide the empty array within the JSON structure.
            **Comprehensive Call-to-Action (CTA) Analysis:** CTAs are not just "buy now." Identify and classify all types:
                **Explicit:** Direct commands like "Click the link in the description," "Subscribe to my channel," "Visit our website at..."
                **Implicit:** Softer suggestions like "You can check these out for yourself," "Let me know what you think in the comments."
                **Destination:** Where does the CTA direct the user? (e.g., a website URL, the comments section, a social media handle).
        """

    prompt = """
            Analyze the provided video to extract key brand elements such as brand name, branded products, branded categories and branded call to actions.
        """

    prompt_config = PromptConfig(
        prompt=prompt, system_instructions=system_instructions
    )

    return prompt_config


prompt_generator = PromptGenerator()
