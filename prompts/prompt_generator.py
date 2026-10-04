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

"""Module defining prompts for ABCD feature evaluation and brand metadata."""

import configuration
import models


class PromptGenerator:
  """Generates prompts for ABCD feature evaluation and brand extraction."""

  def get_abcds_prompt_config(
      self,
      features: list[models.VideoFeature],
      brand_context: configuration.BrandContext | None = None,
  ) -> models.PromptConfig:
    """Gets the prompt and system instructions for ABCD features.

    Args:
      features: List of VideoFeature definitions to evaluate.
      brand_context: Optional brand metadata for prompt augmentation.

    Returns:
      PromptConfig containing the formatted prompt and system instructions.
    """
    features_questions = self.get_features_prompt_template(
        features, brand_context
    )

    system_instructions = (
        "You are an AI Video Analysis Engine. Your primary function is to act"
        " as a meticulous and objective creative expert.\n"
        "Your goal is to analyze video ad content and answer a series of"
        " questions about specific features within the video.\n"
        "Your analysis must be rigorously based only on the visual and"
        " auditory information present in the provided video.\n\n"
        "## CORE DIRECTIVES\n\n"
        "- Absolute Objectivity: Your analysis must be based exclusively on"
        " concrete evidence from the video. Do not infer, assume, or use any"
        " external knowledge. If you cannot see or hear it in the video, it did"
        " not happen.\n"
        "- No Hallucination: Your primary directive is to avoid making up"
        " information. If a feature is ambiguous, not clearly shown, or"
        " impossible to verify from the video, you must answer 'false' and"
        " explain why it is ambiguous or unverifiable in your explanation.\n"
        "- Strict Adherence to Format: The output format is non-negotiable."
        " Any deviation will result in failure.\n"
        "- Assess your confidence for EACH feature: calculate a confidence"
        " score from 0.0 (completely uncertain) to 1.0 (absolutely certain).\n"
        "  Base this score on:\n"
        "  - The clarity and visibility of the relevant features asked in the"
        " question.\n"
        "  - The absence of significant occlusions or ambiguities.\n"
        "  - Output only the numerical score as a float (e.g., 0.85).\n\n"
        "## STEP-BY-STEP TASK EXECUTION\n\n"
        "- Receive Input: You will be given a video file and a list of"
        " questions to answer.\n"
        "- Analyze Video: Conduct a thorough analysis of the video's visual"
        " elements and audio track (dialogue, sound effects, music).\n"
        "- Timecode Grounding: Pay careful attention to timestamps. If a"
        " feature specifies the first 5 seconds (00:00 to 00:05), strictly base"
        " your evaluation on occurrences within that exact time window.\n"
        "- Evaluate Each Question: For each question, determine a definitive"
        " answer:\n"
        "  true if the statement is verifiably correct based on the video.\n"
        "  false if the statement is verifiably incorrect OR cannot be verified"
        " from the video.\n"
        "- Formulate Explanation: For each answer, write a detailed and"
        " logically sound explanation citing specific visual or auditory"
        " evidence from the video with exact timestamps (e.g. 'at 00:03').\n"
        "- Feature ID Handling: CRITICAL REQUIREMENT\n"
        "The value for the feature id 'id' key MUST be an exact, case-sensitive"
        " copy of the Feature ID provided in the input prompt."
    )

    prompt = (
        "These are the questions that you have to answer for each feature:\n"
        f"{features_questions}\n"
    )

    return models.PromptConfig(
        prompt=prompt, system_instructions=system_instructions
    )

  def get_features_prompt_template(
      self,
      features: list[models.VideoFeature],
      brand_context: configuration.BrandContext | None = None,
  ) -> str:
    """Builds features prompt template string.

    Args:
      features: List of VideoFeature objects to build question blocks for.
      brand_context: Optional BrandContext to inject into questions.

    Returns:
      Formatted string of feature questions and evaluation criteria.
    """
    features_prompt = ""
    for feature in features:
      instructions = self.augment_instructions(feature, brand_context)
      features_prompt += (
          f"Feature ID: {feature.id}\n"
          f"Feature Name: {feature.name}\n"
          f"Feature Category: {feature.category.value}\n"
          f"Feature Sub Category: {feature.sub_category.value}\n"
          "Feature Evaluation Criteria: "
          f"{feature.evaluation_criteria.strip()}\n"
          f"Question: {feature.prompt_template or feature.name}\n"
          f"{instructions}\n\n"
      )

    if brand_context:
      brand_name = brand_context.brand_name or ""
      branded_products_str = (
          ", ".join(brand_context.branded_products)
          if brand_context.branded_products
          else ""
      )
      branded_ctas_str = (
          ", ".join(brand_context.branded_call_to_actions)
          if brand_context.branded_call_to_actions
          else ""
      )
      metadata_summary = (
          f"Brand Name: {brand_name}\n"
          f"Branded Products: {branded_products_str}\n"
          f"Branded Call To Actions: {branded_ctas_str}\n"
      )
      features_prompt = (
          features_prompt.replace("{brand_name}", brand_name)
          .replace("{branded_products}", branded_products_str)
          .replace("{branded_call_to_actions_str}", branded_ctas_str)
          .replace("{metadata_summary}", metadata_summary)
      )

    return features_prompt

  def augment_instructions(
      self,
      feature: models.VideoFeature,
      brand_context: configuration.BrandContext | None = None,
  ) -> str:
    """Augments LLM instructions in the prompt.

    Args:
      feature: The VideoFeature containing criteria and extra instructions.
      brand_context: Optional BrandContext containing branded call-to-actions.

    Returns:
      Augmented instructions string.
    """
    branded_ctas = (
        brand_context.branded_call_to_actions
        if brand_context and brand_context.branded_call_to_actions
        else []
    )

    raw_instructions = "\n".join(feature.extra_instructions)
    instructions = raw_instructions.replace(
        "{criteria}", feature.evaluation_criteria.strip()
    ).replace("{call_to_actions}", ", ".join(branded_ctas))
    return instructions

  def get_metadata_prompt_config(self) -> models.PromptConfig:
    """Gets prompt configuration to extract key brand elements from a video.

    Returns:
      PromptConfig containing instructions to extract brand elements.
    """
    system_instructions = (
        "You are BrandVision AI, an expert in brand strategy and multimedia"
        " content analysis.\n"
        "Your primary function is to meticulously analyze video content to"
        " identify and extract key brand elements.\n"
        "You operate under the following core principles:\n\n"
        "- Holistic Analysis: Analyze the video content across visual (logos,"
        " product packaging, on-screen text) and auditory (spoken brand"
        " names, product mentions, jingles) dimensions.\n"
        "- Canonical Naming: Use the official, canonical name for all brands"
        " and products (e.g., 'Google' or 'Coca-Cola').\n"
        "- Zero Hallucination: If an element is not present in the video,"
        " return an empty array `[]`.\n"
        "- Comprehensive Call-to-Action (CTA) Analysis: Identify direct or"
        " implied CTAs (e.g., 'Visit our website', 'Subscribe', 'Buy now')."
    )

    prompt = (
        "Analyze the provided video to extract key brand elements:\n"
        "1. Brand Name (brand_name)\n"
        "2. Branded Products (branded_products)\n"
        "3. Branded Call-to-Actions (branded_call_to_actions)"
    )

    return models.PromptConfig(
        prompt=prompt, system_instructions=system_instructions
    )


prompt_generator = PromptGenerator()
