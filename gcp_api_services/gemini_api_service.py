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

"""Module to interact with Gemini models using Vertex AI and GenAI SDK."""

import json
import logging
import time
from typing import Any

from google.api_core import exceptions as api_exceptions
import google.auth
from google import genai
from google.genai import types

import configuration
import models
from prompts import prompt_generator

logger = logging.getLogger("abcd_detector")


class GeminiAPIService:
  """Gemini API Service supporting Vertex AI and Interactions API."""

  def __init__(
      self,
      gcp_config: configuration.GCPConfig | None,
      gemini_config: configuration.GeminiConfig,
  ) -> None:
    """Initializes the GeminiAPIService.

    Args:
      gcp_config: Optional Google Cloud Platform configuration.
      gemini_config: Configuration settings for the Gemini API.
    """
    self.config = gemini_config
    self.gcp_config = gcp_config
    self.client = (
        genai.Client(api_key=gemini_config.api_key)
        if gemini_config.api_key
        else None
    )
    self._registered_files_cache: dict[str, str] = {}

  def _resolve_video_uri(self, video_uri: str) -> str:
    """Registers a GCS video with the Gemini File Service if needed.

    Args:
      video_uri: URI of the video (e.g. gs://bucket/video.mp4).

    Returns:
      Registered file URI or the original URI if not GCS.
    """
    if not video_uri.startswith("gs://"):
      return video_uri

    if video_uri in self._registered_files_cache:
      return self._registered_files_cache[video_uri]

    logger.info("Registering GCS video with Gemini File Service: %s", video_uri)
    credentials, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/devstorage.read_only",
            "https://www.googleapis.com/auth/generative-language",
        ]
    )

    response = self.client.files.register_files(
        auth=credentials,
        uris=[video_uri],
    )
    if not response.files:
      raise ValueError(
          f"Failed to register video file with Gemini: {video_uri}"
      )

    file_ref = response.files[0]

    # Wait for processing if necessary
    while getattr(file_ref, "state", None) == types.FileState.PROCESSING:
      time.sleep(2)
      file_ref = self.client.files.get(name=file_ref.name)

    if getattr(file_ref, "state", None) == types.FileState.FAILED:
      raise ValueError(
          f"Gemini failed to process registered video: {file_ref.error}"
      )

    resolved_uri = file_ref.uri
    self._registered_files_cache[video_uri] = resolved_uri
    logger.info(
        "Successfully registered video with Gemini: %s -> %s",
        video_uri,
        resolved_uri,
    )
    return resolved_uri

  def execute_interaction(
      self,
      video_uri: str,
      prompt_config: models.PromptConfig,
      response_schema: dict[str, Any],
      retries: int = 3,
  ) -> list[dict[str, Any]] | dict[str, Any]:
    """Executes a request to Gemini using the Interactions API.

    Args:
      video_uri: Cloud Storage URI of the video.
      prompt_config: PromptConfig containing prompt and system instructions.
      response_schema: JSON schema dict for the structured response.
      retries: Maximum number of retry attempts for transient errors.

    Returns:
      Parsed JSON response from Gemini as a list of dicts or dict.
    """
    resolved_uri = self._resolve_video_uri(video_uri)
    for attempt in range(retries):
      try:
        logger.info(
            "Calling Gemini Interactions API (attempt %d/%d) for video: %s with"
            " model %s",
            attempt + 1,
            retries,
            video_uri,
            self.config.model_name,
        )

        interaction = self.client.interactions.create(
            model=self.config.model_name,
            input=[
                {"type": "video", "uri": resolved_uri},
                {"type": "text", "text": prompt_config.prompt},
            ],
            system_instruction=prompt_config.system_instructions,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": response_schema,
            },
            generation_config={
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "max_output_tokens": self.config.max_output_tokens,
            },
        )

        raw_text = None
        if hasattr(interaction, "output_text") and interaction.output_text:
          raw_text = interaction.output_text
        elif hasattr(interaction, "outputs") and interaction.outputs:
          raw_text = interaction.outputs[-1].text

        if not raw_text:
          logger.warning(
              "Empty output received from Gemini for video: %s", video_uri
          )
          return []

        parsed = json.loads(raw_text)
        return parsed

      except api_exceptions.ResourceExhausted as ex:
        wait = 10 * (2**attempt)
        logger.warning(
            "Quota/Rate limit hit (%s). Retrying in %ds...", ex, wait
        )
        time.sleep(wait)
      except Exception as ex:
        error_msg = str(ex)
        if "429" in error_msg or "503" in error_msg or "500" in error_msg:
          wait = 10 * (2**attempt)
          logger.warning(
              "Transient API error (%s). Retrying in %ds...", error_msg, wait
          )
          time.sleep(wait)
        else:
          logger.error(
              "Non-retriable error calling Gemini Interactions API: %s",
              error_msg,
          )
          raise

    logger.error("Max retries exceeded for video: %s", video_uri)
    return []

  def _get_modality_parts(
      self, prompt: str, modality: dict[str, Any]
  ) -> list[Any]:
    """Builds the modality parameters based on the type of LLM capability.

    Args:
      prompt: The text prompt.
      modality: The type of modality (e.g., "text", "VIDEO", "DOCUMENT").

    Returns:
      A list of parameters for the specified modality.
    """
    prompt_part = types.Part.from_text(text=prompt)
    modality_type = (
        str(modality.get("type", "")).upper()
        if isinstance(modality, dict)
        else "TEXT"
    )
    if modality_type == "TEXT":
      return [prompt_part]
    if modality_type == "VIDEO":
      video_uri = modality.get("video_uri") or modality.get("gcs_uri", "")
      mime_type = (
          f"video/{video_uri.rsplit('.', 1)[-1]}"
          if "." in video_uri
          else "video/mp4"
      )
      video = types.Part.from_uri(file_uri=video_uri, mime_type=mime_type)
      return [video, prompt_part]
    if modality_type == "DOCUMENT":
      gcs_uri = modality.get("gcs_uri", "")
      extension = gcs_uri.rsplit(".", 1)[-1] if "." in gcs_uri else ""
      if extension == "pdf":
        mime_type = f"application/{extension}"
      elif extension == "txt":
        mime_type = "text/plain"
      else:
        mime_type = "application/octet-stream"
      document = types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type)
      return [document, prompt_part]
    return [prompt_part]

  def call_gemini_vertex_ai(
      self,
      video_uri: str,
      prompt_config: models.PromptConfig,
      response_schema: dict[str, Any],
      retries: int = 3,
  ) -> list[dict[str, Any]] | dict[str, Any]:
    """Calls Gemini via Vertex AI enforcing structured JSON output.

    Args:
      video_uri: Cloud Storage URI of the video.
      prompt_config: PromptConfig containing prompt and system instructions.
      response_schema: JSON schema dict for the structured response.
      retries: Maximum number of retry attempts for transient errors.

    Returns:
      Parsed structured JSON response from Gemini as a list of dicts or dict.
    """
    project = self.gcp_config.project_id if self.gcp_config else ""
    location = self.config.model_location if self.config else ""

    modality = {"type": "VIDEO", "video_uri": video_uri}
    parts = self._get_modality_parts(prompt_config.prompt, modality)
    contents = [types.Content(role="user", parts=parts)]

    generate_content_config = types.GenerateContentConfig(
        temperature=self.config.temperature,
        top_p=self.config.top_p,
        seed=0,
        max_output_tokens=self.config.max_output_tokens,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT", threshold="OFF"
            ),
        ],
        system_instruction=[
            types.Part.from_text(text=prompt_config.system_instructions)
        ],
        response_mime_type="application/json",
        response_schema=response_schema,
    )

    for this_retry in range(retries):
      try:
        client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

        logger.info(
            "Calling Gemini Vertex AI (attempt %d/%d) for video: %s with"
            " model %s in %s",
            this_retry + 1,
            retries,
            video_uri,
            self.config.model_name,
            location,
        )

        response = client.models.generate_content(
            model=self.config.model_name,
            contents=contents,
            config=generate_content_config,
        )

        if getattr(response, "parsed", None) is not None:
          return response.parsed

        if hasattr(response, "text") and response.text:
          return json.loads(response.text.strip())

        return []

      except api_exceptions.ResourceExhausted as ex:
        logger.warning(
            "QUOTA RETRY: %d. ERROR %s ...", this_retry + 1, str(ex)
        )
        wait = 10 * 2**this_retry
        time.sleep(wait)
      except Exception as ex:
        error_message = str(ex)
        if any(code in error_message for code in ("503", "429")):
          logger.warning(
              "Error %s. Retrying %d times using exponential backoff. Retry"
              " number %d...\n",
              error_message,
              retries,
              this_retry + 1,
          )
          wait = 10 * 2**this_retry
          time.sleep(wait)
        else:
          logger.error(
              "ERROR: the following issue can't be retried: %s\n",
              error_message,
          )
          raise

    logger.error("Max retries exceeded for video: %s", video_uri)
    return []

  def extract_brand_metadata(
      self, video_uri: str
  ) -> configuration.BrandContext:
    """Extracts brand metadata dynamically from a video.

    Args:
      video_uri: Cloud Storage URI of the video to analyze.

    Returns:
      BrandContext populated with brand name, products, and CTAs.
    """
    logger.info("Extracting brand metadata for video: %s", video_uri)
    metadata_prompt_config = (
        prompt_generator.prompt_generator.get_metadata_prompt_config()
    )

    result = self.call_gemini_vertex_ai(
        video_uri=video_uri,
        prompt_config=metadata_prompt_config,
        response_schema=models.VIDEO_METADATA_RESPONSE_SCHEMA,
    )

    if (
        isinstance(result, dict)
        and result.get("brand_name")
        and result.get("branded_products")
    ):
      return configuration.BrandContext(
          brand_name=result["brand_name"],
          branded_products=result["branded_products"],
          branded_call_to_actions=result.get("branded_call_to_actions", []),
      )

    raise ValueError(
        "Unable to extract required brand metadata (brand_name and"
        f" branded_products) for video: {video_uri}. Gemini returned: {result}"
    )
