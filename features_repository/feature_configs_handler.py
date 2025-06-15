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

"""Module with the supported ABCD feature configurations"""

import logging
from models import (
    VideoFeature,
    VideoFeatureCategory,
)
from features_repository.full_abcd_features import get_full_abcd_feature_configs
from features_repository.shorts_features import get_shorts_feature_configs


class FeaturesConfigsHandler:
    """Service that handles video evaluations using AI (LLMs + Annotations)"""

    def get_feature_configs_by_category(
        self, category: VideoFeatureCategory
    ) -> list[VideoFeature]:
        """Gets all the supported features by category
        Full ABCD, Shorts.
        Returns:
        feature_configs: list of feature configurations
        """
        if category.value == VideoFeatureCategory.SHORTS.value:
            shorts_features = get_shorts_feature_configs()
            return shorts_features
        elif category.value == VideoFeatureCategory.FULL_ABCD.value:
            full_abcd_features = get_full_abcd_feature_configs()
            return full_abcd_features
        else:
            logging.log("Category %s not supported. Please check", category)

    def get_features_by_category_by_group_config(
        self, category: VideoFeatureCategory
    ) -> list[VideoFeature]:
        """Groups features by video_segment in feature_configs"""
        feature_configs = self.get_feature_configs_by_category(category)
        grouped_features = {}
        for d in feature_configs:
            grouped_features.setdefault(d.group_by.value, []).append(
                d
            )  # Check this video_segment!
        return grouped_features

    def get_all_features(self):
        """Gets all feature configs for Full ABCD and Shorts"""
        feature_configs = []
        feature_configs.extend(
            self.get_feature_configs_by_category(VideoFeatureCategory.FULL_ABCD)
        )
        feature_configs.extend(
            self.get_feature_configs_by_category(VideoFeatureCategory.SHORTS)
        )

        return feature_configs

    def get_feature_by_id(self, feature_id: str):
        """Gets a feature by id"""
        feature_configs = self.get_all_features()
        feature = [feature for feature in feature_configs if feature.id == feature_id]
        if len(feature) > 0:
            return feature[0]

        return None


features_configs_handler = FeaturesConfigsHandler()
