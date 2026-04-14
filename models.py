"""Modules to define business logic modules"""

from dataclasses import dataclass, field
from enum import Enum


class VideoFeatureCategory(Enum):
  """Enum that represents video feature categories"""

  LONG_FORM_ABCD = "LONG_FORM_ABCD"
  SHORTS = "SHORTS"


class VideoFeatureSubCategory(Enum):
  """Enum that represents video feature sub categories"""

  ATTRACT = "ATTRACT"
  BRAND = "BRAND"
  CONNECT = "CONNECT"
  DIRECT = "DIRECT"
  NONE = "NONE"  # Remove this later


class VideoSegment(Enum):
  """Enum that represents video segments"""

  FULL_VIDEO = "FULL_VIDEO"
  FIRST_5_SECS_VIDEO = "FIRST_5_SECS_VIDEO"
  LAST_5_SECS_VIDEO = "LAST_5_SECS_VIDEO"
  NONE = "NO_GROUPING"


class EvaluationMethod(Enum):
  """Enum that represents evaluation methods"""

  LLMS_AND_ANNOTATIONS = "LLMS_AND_ANNOTATIONS"
  LLMS = "LLMS"
  ANNOTATIONS = "ANNOTATIONS"


class CreativeProviderType(Enum):
  """Enum that represents evaluation methods"""

  GCS = "GCS"
  YOUTUBE = "YOUTUBE"


@dataclass
class VideoFeature:
  """Class that represents a video feature"""

  id: str
  name: str
  category: VideoFeatureCategory
  sub_category: VideoFeatureSubCategory
  video_segment: VideoSegment
  evaluation_criteria: str
  prompt_template: str | None
  extra_instructions: list[str]
  evaluation_method: EvaluationMethod
  evaluation_function: str | None
  include_in_evaluation: bool
  group_by: str


@dataclass
class FeatureEvaluation:
  """Class that represents the evaluation of a feature"""

  feature: VideoFeature
  detected: bool
  confidence_score: float
  rationale: str
  evidence: str
  strengths: str
  weaknesses: str


@dataclass
class VideoAssessment:
  """Class that represents the evaluation of a feature"""

  brand_name: str
  video_uri: str
  long_form_abcd_evaluated_features: list[FeatureEvaluation]
  shorts_evaluated_features: list[FeatureEvaluation]
  config: any  # TODO (ae) change this later


@dataclass
class LLMParameters:
  """Class that represents the required params to make a prediction to the LLM"""

  model_name: str = "gemini-2.5-pro"
  location: str = "us-central1"
  modality: dict = field(default_factory=lambda: {"type": "TEXT"})
  generation_config: dict = field(
      default_factory=lambda: {
          "max_output_tokens": 65535,
          "temperature": 1,
          "top_p": 0.95,
          "response_schema": {"type": "string"},
      }
  )

  def set_modality(self, modality: dict) -> None:
    """Sets the modality to use in the LLM
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


@dataclass
class PromptConfig:
  """Class that represents a prompt with its system instructions"""

  prompt: str
  system_instructions: str


VIDEO_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
            },
            "name": {
                "type": "string",
            },
            "category": {
                "type": "string",
            },
            "sub_category": {
                "type": "string",
            },
            "video_segment": {
                "type": "string",
            },
            "evaluation_criteria": {
                "type": "string",
            },
            "detected": {
                "type": "boolean",
            },
            "confidence_score": {
                "type": "number",
            },
            "rationale": {
                "type": "string",
            },
            "evidence": {
                "type": "string",
            },
            "strengths": {
                "type": "string",
            },
            "weaknesses": {
                "type": "string",
            },
        },
        "required": [
            "id",
            "name",
            "category",
            "sub_category",
            "video_segment",
            "evaluation_criteria",
            "detected",
            "confidence_score",
            "rationale",
            "evidence",
            "strengths",
            "weaknesses",
        ],
    },
}


VIDEO_METADATA_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_name": {"type": "string"},
        "brand_variations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "branded_products": {
            "type": "array",
            "items": {"type": "string"},
        },
        "branded_products_categories": {
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
        "brand_variations",
        "branded_products",
        "branded_products_categories",
        "branded_call_to_actions",
    ],
}
