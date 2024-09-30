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

from annotations_evaluation.annotations_generation import Annotations
from helpers.generic_helpers import load_blob, get_annotation_uri, get_knowledge_graph_entities
from helpers.annotations_helpers import (
    calculate_time_seconds,
    detected_text_in_first_5_seconds
)
from input_parameters import (
    early_time_seconds,
    confidence_threshold,
    logo_size_threshold,
    brand_variations,
)


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


def detect_brand_visuals(feature_name: str, video_uri: str) -> bool:
    """Detect Brand Visuals
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        brand_visuals: brand visuals evaluation
    """
    brand_visuals, na = detect(feature_name, video_uri)

    print(f"{feature_name}: {brand_visuals} \n")

    return brand_visuals


def detect_brand_visuals_1st_5_secs(feature_name: str, video_uri: str) -> bool:
    """Detect Brand Visuals (First 5 seconds)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        brand_visuals_1st_5_secs: brand visuals evaluation

    """
    na, brand_visuals_1st_5_secs = detect(feature_name, video_uri)

    print(f"{feature_name}: {brand_visuals_1st_5_secs} \n")

    return brand_visuals_1st_5_secs


def detect(feature_name: str, video_uri: str) -> tuple[bool, bool]:
    """Detect Brand Visuals & Brand Visuals (First 5 seconds)
    Args:
        feature_name: the name of the feature
        video_uri: video location in gcs
    Returns:
        brand_visuals,
        brand_visuals_1st_5_secs: brand visuals evaluation
    """

    annotation_uri = (
        f"{get_annotation_uri(video_uri)}{Annotations.GENERIC_ANNOTATIONS.value}.json"
    )
    annotation_results = load_blob(annotation_uri)

    # Feature Brand Visuals
    brand_visuals = False

    # Feature Brand Visuals (First 5 seconds)
    brand_visuals_1st_5_secs = False

    # Feature Logo Big (First 5 seconds)
    brand_visuals_logo_big_1st_5_secs = False

    # Video API: Evaluate brand_visuals_feature and brand_visuals_1st_5_secs_feature 1st_5_secs
    # Evaluate brand_visuals_brand_feature & brand_visuals_brand_1st_5_secs
    # in text annotations
    if "text_annotations" in annotation_results:
        for text_annotation in annotation_results.get("text_annotations"):
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
            f"No Text annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
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

    if "logo_recognition_annotations" in annotation_results:
        for logo_recognition_annotation in annotation_results.get(
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
                            for timestamped_object in track.get("timestamped_objects"):
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
            f"No Logo annotations found. Skipping {feature_name} evaluation with Video Intelligence API."
        )

    return (
        brand_visuals,
        brand_visuals_1st_5_secs,
    )
