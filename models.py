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

"""Modules to define ABCD business logic models and schemas."""

import dataclasses
import enum
from typing import Any


class VideoFeatureCategory(enum.Enum):
  """Enum that represents video feature categories / slices."""
  UNIVERSAL = "UNIVERSAL"
  SHORTS = "SHORTS"


class VideoFeatureSubCategory(enum.Enum):
  """Enum that represents video feature sub-categories in ABCD framework."""
  ATTRACT = "ATTRACT"
  BRAND = "BRAND"
  CONNECT = "CONNECT"
  DIRECT = "DIRECT"
  NONE = "NONE"


class VideoSegment(enum.Enum):
  """Enum that represents video segments (legacy)."""
  FULL_VIDEO = "FULL_VIDEO"
  FIRST_5_SECS_VIDEO = "FIRST_5_SECS_VIDEO"
  LAST_5_SECS_VIDEO = "LAST_5_SECS_VIDEO"
  NONE = "NO_GROUPING"


class EvaluationMethod(enum.Enum):
  """Enum that represents evaluation methods."""
  GEMINI = "GEMINI"
  CUSTOM = "CUSTOM"


class CreativeProviderType(enum.Enum):
  """Creative provider types for fetching video creatives."""
  GCS = "GCS"
  YOUTUBE = "YOUTUBE"


@dataclasses.dataclass
class VideoFeature:
  """Class that represents a video feature definition in the repository."""
  id: str
  name: str
  category: VideoFeatureCategory
  sub_category: VideoFeatureSubCategory
  evaluation_criteria: str
  prompt_template: str | None = None
  extra_instructions: list[str] = dataclasses.field(default_factory=list)
  evaluation_method: EvaluationMethod = EvaluationMethod.GEMINI
  evaluation_function: str | None = None
  include_in_evaluation: bool = True
  video_segment: VideoSegment | str | None = None
  group_by: VideoSegment | str | None = None


@dataclasses.dataclass
class FeatureEvaluation:
  """Standardized evaluation result for any ABCD feature."""
  feature: VideoFeature
  is_detected: bool
  confidence_score: float
  rationale: str = ""
  evidence: str = ""
  strengths: str = ""
  weaknesses: str = ""
  recommended_actions: str = ""
  first_appearance_timestamp: float | str | None = None
  feature_density_score: float | None = None
  feature_quality_score: float | None = None
  feature_specifics: dict[str, Any] | None = None


@dataclasses.dataclass
class VideoAssessment:
  """Class that holds the complete assessment for a video across all slices.

  Attributes:
    brand_name: Name of evaluated brand.
    video_uri: Storage or web URI of evaluated video.
    slice_evaluations: Mapping from slice names to list of feature evaluations.
    metadata: Optional extra metadata dictionary.
    brand_context: Optional BrandContext containing products and CTAs.
  """
  brand_name: str
  video_uri: str
  slice_evaluations: dict[str, list[FeatureEvaluation]] = dataclasses.field(
      default_factory=dict
  )
  metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
  brand_context: Any | None = None


@dataclasses.dataclass
class PromptConfig:
  """Class that represents a prompt with its system instructions."""
  prompt: str
  system_instructions: str


VIDEO_EVAL_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "category": {"type": "string"},
            "sub_category": {"type": "string"},
            "evaluation_criteria": {"type": "string"},
            "is_detected": {"type": "boolean"},
            "confidence_score": {"type": "number"},
            "rationale": {"type": "string"},
            "evidence": {"type": "string"},
            "strengths": {"type": "string"},
            "weaknesses": {"type": "string"},
            "recommended_actions": {"type": "string"},
            "first_appearance_timestamp": {"type": "string"},
            "feature_density_score": {"type": "number"},
            "feature_quality_score": {"type": "number"},
            "feature_specifics": {
                "type": "object",
                "properties": {
                    "readability_score": {"type": "number"},
                    "synchronicity_score": {"type": "number"},
                    "quality_bonus_score": {"type": "number"},
                    "text_coverage_ratio": {"type": "number"},
                    "primary_supers_type": {"type": "string"},
                    "peak_sfr_percentage": {"type": "number"},
                    "primary_subject_class": {"type": "string"},
                    "framing_cadence": {"type": "string"},
                    "vocal_clarity_score": {"type": "number"},
                    "primary_voice_type": {"type": "string"},
                    "speech_cadence": {"type": "string"},
                    "background_noise_level": {"type": "string"},
                    "camera_stability": {"type": "string"},
                    "lighting_type": {"type": "string"},
                    "equipment_look": {"type": "string"},
                    "environment_realism": {"type": "string"},
                },
            },
        },
        "required": [
            "id",
            "name",
            "category",
            "sub_category",
            "evaluation_criteria",
            "is_detected",
            "confidence_score",
            "rationale",
            "evidence",
            "strengths",
            "weaknesses",
            "recommended_actions",
            "first_appearance_timestamp",
            "feature_density_score",
            "feature_quality_score",
        ],
    },
}

VIDEO_METADATA_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_name": {"type": "string"},
        "branded_products": {
            "type": "array",
            "items": {"type": "string"},
        },
        "branded_call_to_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "brand_name",
        "branded_products",
    ],
}
