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

"""Module that defines ABCD Detector configuration structures and validation."""

import dataclasses
import enum
import os


class ExecutionMode(str, enum.Enum):
  """Execution mode for feature evaluation."""
  BULK = "BULK"
  INDIVIDUAL = "INDIVIDUAL"


@dataclasses.dataclass(frozen=True)
class GCPConfig:
  """Configuration settings for Google Cloud Platform."""
  project_id: str = dataclasses.field(
      default_factory=lambda: os.getenv(
          "PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", "")
      )
  )
  location: str = dataclasses.field(
      default_factory=lambda: os.getenv(
          "GCP_LOCATION", os.getenv("LOCATION", "us-central1")
      )
  )

  def __post_init__(self) -> None:
    """Validates GCP configuration fields post-initialization."""
    self.validate()

  def validate(self) -> None:
    """Strictly validates GCP settings.

    Raises:
      ValueError: If project_id or location is missing or empty.
    """
    if not self.project_id or not self.project_id.strip():
      raise ValueError(
          "project_id is required. Please set the PROJECT_ID or "
          "GOOGLE_CLOUD_PROJECT environment variable or pass project_id "
          "explicitly in GCPConfig."
      )
    if not self.location or not self.location.strip():
      raise ValueError("location is required and must be a non-empty string.")


@dataclasses.dataclass(frozen=True)
class GeminiConfig:
  """Configuration settings for Gemini models via Google GenAI SDK."""
  api_key: str = dataclasses.field(
      default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
  )
  model_name: str = "gemini-3.8-flash"
  model_location: str = "global"
  temperature: float = 0.1
  top_p: float = 0.95
  max_output_tokens: int = 65536

  def __post_init__(self) -> None:
    """Validates Gemini configuration fields post-initialization."""
    self.validate()

  def validate(self) -> None:
    """Strictly validates Gemini settings.

    Raises:
      ValueError: If api_key or model_location is empty, max_tokens <= 0,
        or temperature out of range.
    """
    if not self.api_key or not self.api_key.strip():
      raise ValueError(
          "GEMINI_API_KEY is required. Please set the GEMINI_API_KEY "
          "environment variable or pass api_key explicitly."
      )
    if not self.model_location or not self.model_location.strip():
      raise ValueError("model_location must be a non-empty string.")
    if self.max_output_tokens <= 0:
      raise ValueError("max_output_tokens must be greater than 0.")
    if not (0.0 <= self.temperature <= 2.0):
      raise ValueError("temperature must be between 0.0 and 2.0.")


@dataclasses.dataclass(frozen=True)
class BrandContext:
  """Brand metadata used for ABCD evaluation."""
  brand_name: str
  branded_products: list[str]
  branded_call_to_actions: list[str] = dataclasses.field(default_factory=list)

  def __post_init__(self) -> None:
    """Validates brand context fields post-initialization."""
    self.validate()

  def validate(self) -> None:
    """Validates brand context settings.

    Raises:
      ValueError: If brand_name is empty or branded_products is empty.
    """
    if not self.brand_name or not self.brand_name.strip():
      raise ValueError("brand_name is required and must be a non-empty string.")
    if not self.branded_products:
      raise ValueError(
          "branded_products is required and must contain at least one "
          "non-empty product name."
      )


@dataclasses.dataclass(frozen=True)
class BigQuerySettings:
  """Settings for exporting assessments to Google Cloud BigQuery."""
  project_id: str = dataclasses.field(
      default_factory=lambda: os.getenv(
          "PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", "")
      )
  )
  dataset_name: str = dataclasses.field(
      default_factory=lambda: os.getenv("BQ_DATASET", "")
  )
  table_name: str = dataclasses.field(
      default_factory=lambda: os.getenv("BQ_TABLE", "")
  )

  def __post_init__(self) -> None:
    """Validates BigQuery settings post-initialization."""
    self.validate()

  def validate(self) -> None:
    """Strictly validates BigQuery settings.

    Raises:
      ValueError: If project_id, dataset_name, or table_name is missing.
    """
    missing = []
    if not self.project_id or not self.project_id.strip():
      missing.append(
          "project_id (or PROJECT_ID / GOOGLE_CLOUD_PROJECT env var)"
      )
    if not self.dataset_name or not self.dataset_name.strip():
      missing.append("dataset_name (or BQ_DATASET env var)")
    if not self.table_name or not self.table_name.strip():
      missing.append("table_name (or BQ_TABLE env var)")

    if missing:
      raise ValueError(
          f"Missing required BigQuery settings: {', '.join(missing)}"
      )


@dataclasses.dataclass(frozen=True)
class EvaluationRequest:
  """Request definition for evaluating video ads against ABCD framework."""
  gcp_config: GCPConfig
  gemini_config: GeminiConfig
  video_uris: list[str]
  slices: list[str] = dataclasses.field(
      default_factory=lambda: ["universal", "shorts"]
  )
  features_to_evaluate: dict[str, list[str]] | None = None
  execution_mode: ExecutionMode = ExecutionMode.BULK
  extract_brand_metadata: bool = True
  brand_context: BrandContext | None = None
  bigquery_settings: BigQuerySettings | None = None

  def __post_init__(self) -> None:
    """Validates evaluation request fields post-initialization."""
    self.validate()

  def validate(self) -> None:
    """Strictly validates evaluation request parameters.

    Raises:
      ValueError: If configurations are invalid or required inputs are missing.
    """
    if self.gcp_config is None:
      raise ValueError("gcp_config is required and cannot be None.")
    self.gcp_config.validate()

    if self.gemini_config is None:
      raise ValueError("gemini_config is required and cannot be None.")
    self.gemini_config.validate()

    if not self.video_uris:
      raise ValueError("At least one video URI must be provided in video_uris.")

    if not self.slices:
      raise ValueError("At least one slice must be specified in slices.")

    if self.features_to_evaluate is not None and not isinstance(
        self.features_to_evaluate, dict
    ):
      raise ValueError(
          "features_to_evaluate must be a dict mapping slice names to list of "
          "feature IDs, e.g. {'universal': ['dynamic_start']}."
      )

    if not self.extract_brand_metadata:
      if not self.brand_context:
        raise ValueError(
            "When extract_brand_metadata is False, brand_context with "
            "brand_name and branded_products must be provided."
        )
      self.brand_context.validate()

    if self.bigquery_settings:
      self.bigquery_settings.validate()
