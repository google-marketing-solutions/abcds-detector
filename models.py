"""Modules to define business logic modules"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VideoFeatureCategory(Enum):
  """Enum that represents video feature categories"""

  LONG_FORM_ABCD = "LONG_FORM_ABCD"
  SHORTS = "SHORTS"
  CREATIVE_INTELLIGENCE = "CREATIVE_INTELLIGENCE"


class VideoFeatureSubCategory(Enum):
  """Enum that represents video feature sub categories"""

  ATTRACT = "ATTRACT"
  BRAND = "BRAND"
  CONNECT = "CONNECT"
  DIRECT = "DIRECT"
  PERSUASION = "PERSUASION"
  STRUCTURE = "STRUCTURE"
  ACCESSIBILITY = "ACCESSIBILITY"
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
  timestamps: list[dict] = field(default_factory=list)
  recommendation: str = ""
  recommendation_priority: str = ""  # high / medium / low


@dataclass
class VideoAssessment:
  """Class that represents the evaluation of a feature"""

  brand_name: str
  video_uri: str
  long_form_abcd_evaluated_features: list[FeatureEvaluation]
  shorts_evaluated_features: list[FeatureEvaluation]
  creative_intelligence_evaluated_features: list[FeatureEvaluation]
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
            "timestamps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                        "label": {"type": "string"},
                    },
                    "required": ["start", "end", "label"],
                },
            },
            "recommendation": {
                "type": "string",
            },
            "recommendation_priority": {
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
            "timestamps",
            "recommendation",
            "recommendation_priority",
        ],
    },
}


SCENE_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "scene_number": {
                "type": "integer",
            },
            "start_time": {
                "type": "string",
            },
            "end_time": {
                "type": "string",
            },
            "description": {
                "type": "string",
            },
            "transcript": {
                "type": "string",
            },
            "emotion": {
                "type": "string",
            },
            "sentiment_score": {
                "type": "number",
            },
            "music_mood": {
                "type": "string",
            },
            "has_music": {
                "type": "boolean",
            },
            "speech_ratio": {
                "type": "number",
            },
        },
        "required": [
            "scene_number",
            "start_time",
            "end_time",
            "description",
            "transcript",
            "emotion",
            "sentiment_score",
            "music_mood",
            "has_music",
            "speech_ratio",
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


METADATA_AND_SCENES_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "metadata": VIDEO_METADATA_RESPONSE_SCHEMA,
        "scenes": SCENE_RESPONSE_SCHEMA,
    },
    "required": ["metadata", "scenes"],
}


CONCEPT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "one_line_pitch": {"type": "string"},
        "key_message": {"type": "string"},
        "emotional_hook": {"type": "string"},
        "narrative_technique": {"type": "string"},
        "unique_selling_proposition": {"type": "string"},
        "target_emotion": {"type": "string"},
        "creative_territory": {"type": "string"},
        "messaging_hierarchy": {
            "type": "object",
            "properties": {
                "primary": {"type": "string"},
                "secondary": {"type": "string"},
                "proof_points": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["primary", "secondary", "proof_points"],
        },
    },
    "required": [
        "one_line_pitch",
        "key_message",
        "emotional_hook",
        "narrative_technique",
        "unique_selling_proposition",
        "target_emotion",
        "creative_territory",
        "messaging_hierarchy",
    ],
}


BRAND_INTELLIGENCE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "website": {"type": "string"},
        "founders_leadership": {"type": "string"},
        "product_service": {"type": "string"},
        "launched": {"type": "string"},
        "description": {"type": "string"},
        "brand_positioning": {"type": "string"},
        "core_value_proposition": {"type": "string"},
        "mission": {"type": "string"},
        "taglines": {"type": "string"},
        "social_proof_overview": {"type": "string"},
        "target_audience_primary": {"type": "string"},
        "target_audience_secondary": {"type": "string"},
        "key_insight": {"type": "string"},
        "secondary_insight": {"type": "string"},
        "products_pricing": {
            "type": "array",
            "items": {"type": "string"},
        },
        "tone": {"type": "string"},
        "voice": {"type": "string"},
        "what_it_is_not": {"type": "string"},
        "credibility_signals": {
            "type": "array",
            "items": {"type": "string"},
        },
        "paid_media_channels": {
            "type": "array",
            "items": {"type": "string"},
        },
        "creative_formats": {
            "type": "array",
            "items": {"type": "string"},
        },
        "messaging_themes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "offers_and_ctas": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "company_name",
        "website",
        "founders_leadership",
        "product_service",
        "launched",
        "description",
        "brand_positioning",
        "core_value_proposition",
        "mission",
        "taglines",
        "social_proof_overview",
        "target_audience_primary",
        "target_audience_secondary",
        "key_insight",
        "secondary_insight",
        "products_pricing",
        "tone",
        "voice",
        "what_it_is_not",
        "credibility_signals",
        "paid_media_channels",
        "creative_formats",
        "messaging_themes",
        "offers_and_ctas",
    ],
}
