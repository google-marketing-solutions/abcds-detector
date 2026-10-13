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

  def test_universal_features_count_and_brand_visualized(self) -> None:
    """Tests that Universal slice has 13 features including brand_visualized."""
    features = (
        feature_configs_handler.features_configs_handler.get_features_for_slice(
            slice_name="universal"
        )
    )
    self.assertEqual(len(features), 13)
    feature_ids = {f.id for f in features}
    self.assertIn("b_brand_visualized", feature_ids)
    self.assertIn("b_brand_visualized_in_first_5_sec", feature_ids)

  def test_universal_subcategories_mapping(self) -> None:
    """Tests that Universal features map to ABCD subcategories."""
    features = (
        feature_configs_handler.features_configs_handler.get_features_for_slice(
            slice_name="universal"
        )
    )
    feature_map = {f.id: f.sub_category for f in features}

    # Attention features
    attention_ids = [
        "a_heartbeat_story_arc",
        "a_has_audio",
        "a_supers_w_audio",
        "a_tightly_framed_overall",
        "a_has_supers",
    ]
    for fid in attention_ids:
      self.assertEqual(
          feature_map[fid],
          models.VideoFeatureSubCategory.ATTENTION,
          f"Expected {fid} to have sub_category ATTENTION",
      )

    # Branding features
    branding_ids = [
        "b_brand_visualized",
        "b_brand_visualized_in_first_5_sec",
        "b_brand_mention",
        "b_brand_mention_speech_see_and_say_first_5s",
        "b_brand_palette_multiple_brand_elements",
    ]
    for fid in branding_ids:
      self.assertEqual(
          feature_map[fid],
          models.VideoFeatureSubCategory.BRANDING,
          f"Expected {fid} to have sub_category BRANDING",
      )

    # Connection features
    connection_ids = [
        "c_people_overall",
        "c_casual_language",
    ]
    for fid in connection_ids:
      self.assertEqual(
          feature_map[fid],
          models.VideoFeatureSubCategory.CONNECTION,
          f"Expected {fid} to have sub_category CONNECTION",
      )

    # Direction features
    self.assertEqual(
        feature_map["d_visual_cta"],
        models.VideoFeatureSubCategory.DIRECTION,
        "Expected d_visual_cta to have sub_category DIRECTION",
    )




if __name__ == "__main__":
  unittest.main()
