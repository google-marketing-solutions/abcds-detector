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

"""Module to detect Brand: Brand Visuals & Brand Visuals (First 5 seconds)
Annotations used:
    1.Text annotations to identify brand name
    2.Logo annotations to identify brand logo
"""

### REMOVE FOR COLAB - START
from input_parameters import (
    GEMINI_PRO,
    llm_location,
    llm_generation_config,
    early_time_seconds,
    confidence_threshold,
    logo_size_threshold,
    use_llms,
    use_annotations,
    context_and_examples,
)

from helpers.annotations_helpers import (
    calculate_time_seconds,
    detected_text_in_first_5_seconds,
)

from helpers.vertex_ai_service import LLMParameters, detect_feature_with_llm

from helpers.generic_helpers import (
    get_knowledge_graph_entities,
    get_n_secs_video_uri_from_uri,
)

### REMOVE FOR COLAB - END

# @title 6 & 7) Brand: Brand Visuals & Brand Visuals (First 5 seconds)

# @markdown **Features:**

# @markdown 1. **Brand Visuals:** Branding, defined as the brand name or brand logo are shown in-situation or overlaid at any time in the video.

# @markdown 2. **Brand Visuals (First 5 seconds):** Branding, defined as the brand name or brand logo are shown in-situation or overlaid in the first 5 seconds (up to 4.99s) of the video.
# @markdown Including Logo Big & Logo Early. Is Logo larger than x% (3.5% default) of screen in the first 5 seconds?


def calculate_surface_area(points) -> float:
    """Calculate surface area of an object"""
    if len(points) != 4:
        return 0
    area1 = 0.5 * abs(points[0][0] * points[1][1] - points[1][0] * points[0][1])
    area2 = 0.5 * abs(points[1][0] * points[2][1] - points[2][0] * points[1][1])
    area3 = 0.5 * abs(points[2][0] * points[3][1] - points[3][0] * points[2][1])
    area4 = 0.5 * abs(points[3][0] * points[0][1] - points[0][0] * points[3][1])

    # Add the areas of the four triangles to get the total surface area.
    surface_area = area1 + area2 + area3 + area4
    return surface_area * 100


def detect_brand_visuals(
    text_annotation_results: any,
    logo_annotation_results: any,
    video_uri: str,
    brand_name: str,
    brand_variations: list[str],
) -> tuple[dict, dict, bool]:
    """Detect Brand Visuals & Brand Visuals (First 5 seconds)
    Args:
        text_annotation_results: text annotations
        logo_annotation_results: logo annotations
        video_uri: video location in gcs
        brand_name: name of the brand
        brand_variations: a list of brand name variations
    Returns:
        brand_visuals_eval_details,
        brand_visuals_1st_5_secs_eval_details,
        brand_visuals_logo_big_1st_5_secs: brand visuals evaluation
    """
    # Feature Brand Visuals
    brand_visuals_feature = "Brand Visuals"
    brand_visuals = False
    brand_visuals_criteria = """Branding, defined as the brand name or brand logo are shown
        in-situation or overlaid at any time in the video."""
    brand_visuals_eval_details = {
        "feature": brand_visuals_feature,
        "feature_description": brand_visuals_criteria,
        "feature_detected": brand_visuals,
        "llm_details": [],
    }
    # Feature Brand Visuals (First 5 seconds)
    brand_visuals_1st_5_secs_feature = "Brand Visuals (First 5 seconds)"
    brand_visuals_1st_5_secs = False
    # Remove 1st 5 secs references from prompt to avoid hallucinations since the video is already 5 secs
    brand_visuals_1st_5_secs_criteria = """Branding, defined as the brand name or brand logo are shown in-situation
    or overlaid in the video"""
    brand_visuals_1st_5_secs_eval_details = {
        "feature": brand_visuals_1st_5_secs_feature,
        "feature_description": brand_visuals_1st_5_secs_criteria,
        "feature_detected": brand_visuals_1st_5_secs,
        "llm_details": [],
    }
    # Feature Logo Big (First 5 seconds)
    brand_visuals_logo_big_1st_5_secs = False

    # Video API: Evaluate brand_visuals_feature and brand_visuals_1st_5_secs_feature 1st_5_secs
    if use_annotations:
        # Evaluate brand_visuals_brand_feature & brand_visuals_brand_1st_5_secs
        # in text annotations
        if "text_annotations" in text_annotation_results:
            for text_annotation in text_annotation_results.get("text_annotations"):
                text = text_annotation.get("text")
                found_brand = [
                    brand for brand in brand_variations if brand.lower() in text.lower()
                ]
                if found_brand:
                    brand_visuals = True
                    found_brand_1st_5_secs, frame = detected_text_in_first_5_seconds(
                        text_annotation
                    )
                    if found_brand_1st_5_secs:
                        brand_visuals_1st_5_secs = True
                    # Check surface area
                    if brand_visuals_1st_5_secs and frame:
                        coordinates = []
                        for vertex in frame.get("rotated_bounding_box").get("vertices"):
                            coordinates.append(
                                ((float(vertex.get("x"))), float(vertex.get("y")))
                            )
                        surface_area = calculate_surface_area(coordinates)
                        if surface_area > logo_size_threshold:
                            brand_visuals_logo_big_1st_5_secs = True
        else:
            print(
                f"No Text annotations found. Skipping {brand_visuals_feature} evaluation with Video Intelligence API."
            )

        # Evaluate brand_visuals_feature & brand_visuals_1st_5_secs in logo annotations
        brand_kg_entities = get_knowledge_graph_entities(brand_variations)
        brand_kg_entities_list = []
        for key, value in brand_kg_entities.items():
            entity_id = value["@id"][3:] if "@id" in value else ""
            entity_name = value["name"] if "name" in value else ""
            entity_description = value["description"] if "description" in value else ""
            brand_kg_entities_list.append(
                {
                    "entity_id": entity_id,
                    "entity_name": entity_name,
                    "entity_description": entity_description,
                }
            )

        if "logo_recognition_annotations" in logo_annotation_results:
            for logo_recognition_annotation in logo_annotation_results.get(
                "logo_recognition_annotations"
            ):
                entity_id = logo_recognition_annotation.get("entity").get("entity_id")
                entity_description = logo_recognition_annotation.get("entity").get(
                    "description"
                )
                found_entities = [
                    ent
                    for ent in brand_kg_entities_list
                    if ent["entity_id"] == entity_id
                    or ent["entity_description"].lower() == entity_description.lower()
                ]
                if len(found_entities) > 0:
                    # All logo tracks where the recognized logo appears. Each track corresponds
                    # to one logo instance appearing in consecutive frames.
                    for track in logo_recognition_annotation.get("tracks"):
                        # Check confidence against user defined threshold
                        if track.get("confidence") >= confidence_threshold:
                            brand_visuals = True
                            # Video segment of a track.
                            start_time_secs = calculate_time_seconds(
                                track.get("segment"), "start_time_offset"
                            )
                            if start_time_secs <= early_time_seconds:
                                brand_visuals_1st_5_secs = True
                                # The object with timestamp and attributes per frame in the track.
                                for timestamped_object in track.get(
                                    "timestamped_objects"
                                ):
                                    # Normalized Bounding box in a frame, where the object is located.
                                    normalized_bounding_box = timestamped_object.get(
                                        "normalized_bounding_box"
                                    )
                                    bottom_top = (
                                        normalized_bounding_box.get("bottom") or 0
                                    ) - (normalized_bounding_box.get("top") or 0)
                                    right_left = (
                                        normalized_bounding_box.get("right") or 0
                                    ) - (normalized_bounding_box.get("left") or 0)
                                    surface = bottom_top * right_left * 100
                                    if surface > logo_size_threshold:
                                        brand_visuals_logo_big_1st_5_secs = True

                    # All video segments where the recognized logo appears. There might be
                    # multiple instances of the same logo class appearing in one VideoSegment.
                    # Since there is no confidence here, just check 1st 5 mins feature - CHECK
                    for segment in logo_recognition_annotation.get("segments"):
                        start_time_secs = calculate_time_seconds(
                            segment, "start_time_offset"
                        )
                        if start_time_secs <= early_time_seconds:
                            brand_visuals_1st_5_secs = True
        else:
            print(
                f"No Logo annotations found. Skipping {brand_visuals_feature} evaluation with Video Intelligence API."
            )

    # LLM: Evaluate brand_visuals_feature and brand_visuals_1st_5_secs_feature 1st_5_secs
    if use_llms:
        llm_params = LLMParameters(
            model_name=GEMINI_PRO,
            location=llm_location,
            generation_config=llm_generation_config,
        )
        # 1. Evaluate brand_visuals_feature
        prompt = (
            """Is the brand {brand_name} or brand logo {brand_name} visible at any time in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when the brand {brand_name} or brand logo {brand_name} is found.
            {context_and_examples}
        """.replace(
                "{brand_name}", brand_name
            )
            .replace("{feature}", brand_visuals_feature)
            .replace("{criteria}", brand_visuals_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use full video for this feature
        llm_params.set_modality({"type": "video", "video_uri": video_uri})
        feature_detected, llm_explanation = detect_feature_with_llm(
            brand_visuals_feature, prompt, llm_params
        )
        if feature_detected:
            brand_visuals = True

        # Include llm details
        brand_visuals_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

        # 2. Evaluate brand_visuals_1st_5_secs_feature
        prompt = (
            """Is the brand {brand_name} or brand logo {brand_name} visible in the video?
            Consider the following criteria for your answer: {criteria}
            Look through each frame in the video carefully and answer the question.
            Provide the exact timestamp when the brand {brand_name} or brand logo {brand_name} is found.
            {context_and_examples}
        """.replace(
                "{brand_name}", brand_name
            )
            .replace("{feature}", brand_visuals_1st_5_secs_feature)
            .replace("{criteria}", brand_visuals_1st_5_secs_criteria)
            .replace("{context_and_examples}", context_and_examples)
        )
        # Use first 5 secs video for this feature
        video_uri_1st_5_secs = get_n_secs_video_uri_from_uri(video_uri, "1st_5_secs")
        llm_params.set_modality({"type": "video", "video_uri": video_uri_1st_5_secs})
        feature_detected, llm_explanation = detect_feature_with_llm(
            brand_visuals_1st_5_secs_feature, prompt, llm_params
        )
        if feature_detected:
            brand_visuals_1st_5_secs = True

        # Include llm details
        brand_visuals_1st_5_secs_eval_details["llm_details"].append(
            {
                "llm_params": llm_params.__dict__,
                "prompt": prompt,
                "llm_explanation": llm_explanation,
            }
        )

    print(f"{brand_visuals_feature}: {brand_visuals}")
    brand_visuals_eval_details["feature_detected"] = brand_visuals
    print(
        f"""{brand_visuals_1st_5_secs_feature}: {brand_visuals_1st_5_secs}
        Logo Big: {brand_visuals_logo_big_1st_5_secs}"""
    )
    brand_visuals_1st_5_secs_eval_details["feature_detected"] = brand_visuals_1st_5_secs

    return (
        brand_visuals_eval_details,
        brand_visuals_1st_5_secs_eval_details,
        brand_visuals_logo_big_1st_5_secs,
    )
