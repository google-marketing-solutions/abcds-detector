#!/usr/bin/env python3

###########################################################################
#
#  Copyright 2025 Google LLC
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

"""Module to evaluate features for ABCDs using custom functions"""

import annotations_evaluation.feature_modules as annotations_module  # Change this
from configuration import Configuration
from models import VideoFeature, FeatureEvaluation


class CustomDetector:
    """Module to evaluate features for ABCDs using annotations."""

    def __init__(self):
        pass

    def evaluate_features(
        self, config: Configuration, feature_config: VideoFeature, video_uri: str
    ) -> list[FeatureEvaluation]:
        """Evaluates ABCD features using custom functions."""

        print("Starting ABCD evaluation using custom functions... \n")

        feature_evaluations: list[FeatureEvaluation] = []

        print(f"Custom function evaluation for feature {feature_config.name}...")
        eval_function_name = feature_config.evaluation_function
        func = getattr(annotations_module, eval_function_name)
        detected = func(config, feature_config.name, video_uri)

        feature_evaluation = FeatureEvaluation(
            feature=feature_config,
            detected=detected,
            confidence_score=1,  # TODO (ae) calculate this for annotations
            rationale="",
            evidence="",
            strengths="",
            weaknesses="",
        )
        feature_evaluations.append(feature_evaluation)

        return feature_evaluations


custom_detector = CustomDetector()
