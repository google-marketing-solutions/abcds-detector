"""Modules to define business logic modules"""

from dataclasses import dataclass, field
from enum import Enum


class VideoFeatureCategory(Enum):
    """Enum that represents video feature categories"""

    FULL_ABCD = "FULL_ABCD"
    SHORTS = "SHORTS"


class VideoFeatureSubCategory(Enum):
    """Enum that represents video feature sub categories"""

    ATTRACT = "ATTRACT"
    BRAND = "BRAND"
    CONNECT = "CONNECT"
    DIRECT = "DIRECT"


class VideoSegment(Enum):
    """Enum that represents video segments"""

    FULL_VIDEO = "FULL_VIDEO"
    FIRST_5_SECS_VIDEO = "FIRST_5_SECS_VIDEO"
    LAST_5_SECS_VIDEO = "LAST_5_SECS_VIDEO"


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
class EvaluationDetails:
    """Class that represents the evaluation details of a feature"""

    rationale: str
    evidence: str
    strengths: str
    weaknesses: str


@dataclass
class FeatureEvaluation:
    """Class that represents the evaluation of a feature"""

    feature: VideoFeature
    detected: bool
    confidence_score: float
    evaluation_details: EvaluationDetails


@dataclass
class LLMParameters:
    """Class that represents the required params to make a prediction to the LLM"""

    model_name: str = "gemini-2.5-pro-preview-05-06"
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
                "type": "float",
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
