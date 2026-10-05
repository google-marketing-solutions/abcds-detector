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

"""Module with the supported ABCD feature configurations."""

import logging

from features_repository import shorts_features
from features_repository import universal_features
import models

logger = logging.getLogger("abcd_detector")


class FeaturesConfigsHandler:
  """Service managing retrieval and filtering of ABCD feature configs."""

  def get_features_for_slice(
      self,
      slice_name: str,
      features_filter: list[str] | None = None,
  ) -> list[models.VideoFeature]:
    """Gets all features for a given slice, optionally filtered by feature IDs.

    Args:
      slice_name: ABCD slice name ('universal' or 'shorts').
      features_filter: Optional list of feature IDs to filter by.

    Returns:
      List of active VideoFeature definitions matching the criteria.
    """
    normalized_slice = slice_name.lower().strip()
    if normalized_slice == "universal":
      features = universal_features.get_universal_feature_configs()
    elif normalized_slice == "shorts":
      features = shorts_features.get_shorts_feature_configs()
    else:
      logger.warning(
          "Slice '%s' is not recognized. Returning empty features.",
          slice_name,
      )
      return []

    # Include only features marked for evaluation
    active_features = [f for f in features if f.include_in_evaluation]

    # Filter by specific feature IDs if requested
    if features_filter is not None:
      filter_set = set(features_filter)
      active_features = [f for f in active_features if f.id in filter_set]

    return active_features

  def get_feature_configs_by_category(
      self, category: models.VideoFeatureCategory
  ) -> list[models.VideoFeature]:
    """Gets feature configurations by category enum.

    Args:
      category: VideoFeatureCategory enum instance.

    Returns:
      List of VideoFeature definitions for the category.
    """
    if category.value == models.VideoFeatureCategory.SHORTS.value:
      return shorts_features.get_shorts_feature_configs()
    return universal_features.get_universal_feature_configs()

  def get_all_features(self) -> list[models.VideoFeature]:
    """Gets all registered feature configurations across all slices.

    Returns:
      List of all VideoFeature definitions.
    """
    feature_configs = []
    feature_configs.extend(universal_features.get_universal_feature_configs())
    feature_configs.extend(shorts_features.get_shorts_feature_configs())
    return feature_configs

  def get_feature_by_id(self, feature_id: str) -> models.VideoFeature | None:
    """Gets a feature by its unique ID.

    Args:
      feature_id: Unique identifier string for the feature.

    Returns:
      Matching VideoFeature instance, or None if not found.
    """
    for feature in self.get_all_features():
      if feature.id == feature_id:
        return feature
    return None


features_configs_handler = FeaturesConfigsHandler()
