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

"""Tests for ABCD feature repository configurations and filtering."""

import unittest

from features_repository import feature_configs_handler
import models


class TestFeaturesRepository(unittest.TestCase):
  """Tests for feature configurations retrieval, slices, and filtering."""

  def test_feature_configs_handler_filtering(self) -> None:
    """Tests filtering features by slice and ID."""
    features = (
        feature_configs_handler.features_configs_handler.get_features_for_slice(
            slice_name="universal",
            features_filter=["a_heartbeat_story_arc"],
        )
    )
    self.assertEqual(len(features), 1)
    self.assertEqual(features[0].id, "a_heartbeat_story_arc")

  def test_get_all_features_includes_universal_and_shorts(self) -> None:
    """Tests that all features include universal and shorts definitions."""
    all_features = (
        feature_configs_handler.features_configs_handler.get_all_features()
    )
    self.assertGreater(len(all_features), 0)
    categories = {f.category for f in all_features}
    self.assertIn(models.VideoFeatureCategory.UNIVERSAL, categories)
    self.assertIn(models.VideoFeatureCategory.SHORTS, categories)

  def test_get_feature_by_id_found_and_not_found(self) -> None:
    """Tests retrieving features by unique ID."""
    feature = (
        feature_configs_handler.features_configs_handler.get_feature_by_id(
            "a_heartbeat_story_arc"
        )
    )
    self.assertIsNotNone(feature)
    self.assertEqual(feature.id, "a_heartbeat_story_arc")

    missing = (
        feature_configs_handler.features_configs_handler.get_feature_by_id(
            "non_existent_id"
        )
    )
    self.assertIsNone(missing)


if __name__ == "__main__":
  unittest.main()
