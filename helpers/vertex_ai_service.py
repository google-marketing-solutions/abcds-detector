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

"""Module to load helper functions and classes to interact with Vertex AI"""

import time
import json
import vertexai
import vertexai.preview.generative_models as generative_models
from vertexai.preview.generative_models import GenerativeModel, Part, GenerationConfig
from google.api_core.exceptions import ResourceExhausted
from feature_configs.features import RESPONSE_SCHEMA
from configuration import Configuration


class LLMParameters:
    """Class that represents the required params to make a prediction to the LLM"""

    model_name: str
    location: str
    modality: dict
    generation_config: dict = {  # Default model config
        "max_output_tokens": 2048,
        "temperature": 0.5,
        "top_p": 1,
        "top_k": 40,
    }

    def __init__(
        self,
        model_name: str,
        location: str,
        generation_config: dict,
        modality: dict = None,
    ):
        self.model_name = model_name
        self.location = location
        self.generation_config = generation_config
        self.modality = modality

    def set_modality(self, modality: dict) -> None:
        """Sets the modal to use in the LLM
        The modality object changes depending on the type.
        For video:
        {
            "type": "video", # prompt is handled separately
            "video_uri": ""
        }
        For text:
        {
            "type": "text" # prompt is handled separately
        }
        """
        self.modality = modality


class VertexAIService:
    """Vertex AI Service to leverage the Vertex APIs for inference"""

    def __init__(self, project_id: str):
        self.project_id = project_id

    def execute_gemini_pro(self, prompt: str, params: LLMParameters) -> str:
        """Makes a request to Gemini to get a prediction based on the provided prompt
        and multi-modal params
        Args:
            prompt: a string with the prompt for LLM
            params: llm params model_name, location, modality and generation_config
        Returns:
            response.text: a string with the generated response
        """
        retries = 3
        for this_retry in range(retries):
            try:
                vertexai.init(project=self.project_id, location=params.location)
                model = GenerativeModel(params.model_name)
                modality_params = self._get_modality_params(prompt, params)
                response = model.generate_content(
                    modality_params,
                    generation_config=GenerationConfig(
                        temperature=params.generation_config.get("temperature"),
                        max_output_tokens=params.generation_config.get(
                            "max_output_tokens"
                        ),
                        top_p=params.generation_config.get("top_p"),
                        response_mime_type="application/json",
                        response_schema=RESPONSE_SCHEMA,
                    ),
                    safety_settings={
                        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    },
                    stream=False,
                )
                return response.text if response else ""
            except ResourceExhausted as ex:
                print(f"QUOTA RETRY: {this_retry + 1}. ERROR {str(ex)} ...")
                wait = 10 * 2**this_retry
                time.sleep(wait)
            except AttributeError as ex:
                error_message = str(ex)
                if "Content has no parts" in error_message:
                    # Retry request
                    print(
                        f"Error: {ex} Gemini might be blocking the response due to safety issues. Retrying {retries} times using exponential backoff. Retry number {this_retry + 1}...\n"
                    )
                    wait = 10 * 2**this_retry
                    time.sleep(wait)
            except Exception as ex:
                print("GENERAL EXCEPTION...\n")
                error_message = str(ex)
                # Check quota issues for now
                if (
                    "429 Quota exceeded" in error_message
                    or "503 The service is currently unavailable" in error_message
                    or "500 Internal error encountered" in error_message
                    or "403" in error_message
                ):
                    if config.verbose:
                        print(
                            f"Error {error_message}. Retrying {retries} times using exponential backoff. Retry number {this_retry + 1}...\n"
                        )
                    # Retry request
                    wait = 10 * 2**this_retry
                    time.sleep(wait)
                else:
                    if config.verbose:
                        print(
                            f"ERROR: the following issue can't be retried: {error_message}\n"
                        )
                    # Raise exception for non-retriable errors
                    raise
        return ""

    def _get_modality_params(self, prompt: str, params: LLMParameters) -> list[any]:
        """Build the modality params based on the type of llm capability to use
        Args:
            prompt: a string with the prompt for LLM
            model_params: the model params for inference, see defaults above
        Returns:
            modality_params: list of modality params based on the model capability to use
        """
        if params.modality["type"] == "video":
            mime_type = f"video/{params.modality['video_uri'].rsplit('.', 1)[-1]}"
            video = Part.from_uri(uri=params.modality["video_uri"], mime_type=mime_type)
            return [video, prompt]
        elif params.modality["type"] == "text":
            return [prompt]
        return []


def get_vertex_ai_service(config:Configuration):
    """Gets Vertex AI service to interact with Gemini"""
    vertex_ai_service = VertexAIService(config.project_id)
    return vertex_ai_service


def detect_features_with_llm_in_bulk(
    config: Configuration,
    prompt: str, llm_params: LLMParameters, features_group_by: str
) -> list[dict]:
    """Detect features in bulk using LLM
    Args:
        config: all the variables
        prompt: prompt for the llm
        llm_params: object with llm params
    Returns:
        features: list of evaluated features
    """
    retries = 3
    for this_retry in range(retries):
        try:
            vertex_ai_service = get_vertex_ai_service(config)
            if llm_params.model_name == config.llm_name:
                # Gemini 1.5 does not support top_k param
                if "top_k" in llm_params.generation_config:
                    del llm_params.generation_config["top_k"]
                llm_response = vertex_ai_service.execute_gemini_pro(
                    prompt=prompt, params=llm_params
                )
            else:
                print(f"LLM {llm_params.model_name} not supported.")
                return False
            # Parse response
            features = json.loads(clean_llm_response(llm_response))
            if isinstance(features, list) and len(features) > 0:
                if config.verbose:
                    print(
                        f"***Powered by LLMs*** \n\n FEATURES in group {features_group_by}: \n\n {str(features)} \n"
                    )
                return features
            else:
                print(
                    f"LLM response is not a dict. Response was: {features}. Retrying request {this_retry + 1} times... \n"
                )
                if this_retry == retries - 1:
                    break

                # Retry if response is not an array or response was empty
                wait = 10 * 2**this_retry
                time.sleep(wait)
        except json.JSONDecodeError as ex:
            if this_retry == retries - 1:
                break

            if config.verbose:
                print(
                    f"LLM response could not be parsed. Error: {ex}.\n Using string version...\n"
                )
                if llm_response:
                    print(f"***Powered by LLMs*** \n LLM response: {llm_response} \n")

            # Retry if response could not be parsed
            wait = 10 * 2**this_retry
            time.sleep(wait)
        except Exception as ex:
            print(ex)  # raise?
    # return empty list if not possible to get response after retries
    return []


def clean_llm_response(response: str) -> str:
    """Cleans LLM response
    Args:
        response: llm response to clean
    Returns:
        reponse: without extra characters
    """
    return response.replace("```", "").replace("json", "")
