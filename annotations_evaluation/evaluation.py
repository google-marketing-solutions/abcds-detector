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

"""Module to evaluate features for ABCDs using annotations."""

import annotations_evaluation.feature_modules as annotations_module
from features_repository.full_abcd_features import get_feature_configs
from configuration import Configuration


class AnnotationsDectector:
  """Module to evaluate features for ABCDs using annotations."""

  def __init__(self):
    pass

  def evaluate_abcd_features_using_annotations(
      self, config: Configuration, video_uri: str
  ) -> list[dict]:
    """Evaluates ABCD features using annotations."""

    feature_configs = get_feature_configs()
    feature_evaluations: list = []

    print("Starting ABCD evaluation using annotations... \n")

    # Process annotations for all features
    for feature_config in feature_configs:
      print(
          f"Annotation evaluation for feature {feature_config.get('name')}..."
      )
      function_name = feature_config.get("annotations_function")
      detected = False
      if function_name:
        func = getattr(annotations_module, function_name)
        detected = func(config, feature_config.get("name"), video_uri)
        feature_evaluations.append({
            "id": feature_config.get("id"),
            "name": feature_config.get("name"),
            "category": feature_config.get("category"),
            "criteria": feature_config.get("criteria"),
            "detected": detected,
        })
    return feature_evaluations
