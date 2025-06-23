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


from configuration import Configuration
from gcp_api_services.gemini_api_service import get_gemini_api_service
from prompts.prompt_generator import prompt_generator
from models import VIDEO_RESPONSE_SCHEMA, VIDEO_METADATA_RESPONSE_SCHEMA


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
        "Starting LLM evaluation for features grouped by"
        f" {evaluation_details.get('category')} and"
        f" {evaluation_details.get('group_by')}... \n"
    )
    prompt_config = prompt_generator.get_abcds_prompt_config(
        evaluation_details.get("feature_configs"),
        config,
    )
    # Set modality for API
    config.llm_params.set_modality(
        {"type": "video", "video_uri": evaluation_details.get("video_uri")}
    )
    # Set the required schema for the LLM response
    config.llm_params.generation_config["response_schema"] = (
        VIDEO_RESPONSE_SCHEMA
    )
    evaluated_features = get_gemini_api_service(
        config
    ).execute_gemini_with_genai(prompt_config, config.llm_params)

    if config.verbose:
      if len(evaluated_features) == 0:
        print(
            "WARNING: ABCD Detector was not able to process features for video"
            f" {evaluation_details.get('video_uri')}... Please review. \n"
        )

    return evaluated_features

  def get_video_metadata(self, config: Configuration, video_uri: str):
    print(f"Extracting brand metadata for video {video_uri}... \n")
    prompt_config = prompt_generator.get_metadata_prompt_config()
    # Set modality for API
    config.llm_params.set_modality({"type": "video", "video_uri": video_uri})
    # Set the required schema for the LLM response
    config.llm_params.generation_config["response_schema"] = (
        VIDEO_METADATA_RESPONSE_SCHEMA
    )
    metadata = get_gemini_api_service(config).execute_gemini_with_genai(
        prompt_config, config.llm_params
    )

    return metadata


llms_detector = LLMDetector()
