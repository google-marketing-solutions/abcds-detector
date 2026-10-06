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

"""Tests for ABCD Detector utility functions and CLI argument parsing."""

import os
import unittest

import utils


class TestUtils(unittest.TestCase):
  """Tests for CLI arguments parsing, normalization, and request building."""

  def test_parse_args_comprehensive(self) -> None:
    """Tests parse_args recognizes all flags and aliases across configs."""
    args = utils.parse_args([
        "-project_id",
        "my-gcp-proj",
        "-api_key",
        "my-api-key",
        "-model_name",
        "gemini-3.8-flash",
        "-location",
        "us-central1",
        "-model_location",
        "global",
        "-temp",
        "0.2",
        "-top_p",
        "0.9",
        "-tokens",
        "8192",
        "-vu",
        "gs://bucket/vid.mp4",
        "-slices",
        "universal,shorts",
        "-mode",
        "INDIVIDUAL",
        "-bq_dataset",
        "my_ds",
        "-bq_table",
        "my_tbl",
        "-brand",
        "MyBrand",
        "-products",
        "Product A, Product B",
        "-ctas",
        "Buy Now",
    ])
    self.assertEqual(args.project_id, "my-gcp-proj")
    self.assertEqual(args.location, "us-central1")
    self.assertEqual(args.api_key, "my-api-key")
    self.assertEqual(args.model_name, "gemini-3.8-flash")
    self.assertEqual(args.model_location, "global")
    self.assertEqual(args.temperature, 0.2)
    self.assertEqual(args.top_p, 0.9)
    self.assertEqual(args.max_output_tokens, 8192)
    self.assertEqual(args.video_uris, "gs://bucket/vid.mp4")
    self.assertEqual(args.slices, "universal,shorts")
    self.assertEqual(args.mode, "INDIVIDUAL")
    self.assertEqual(args.bigquery_dataset, "my_ds")
    self.assertEqual(args.bigquery_table, "my_tbl")
    self.assertEqual(args.brand_name, "MyBrand")
    self.assertEqual(args.branded_products, "Product A, Product B")
    self.assertEqual(args.branded_call_to_actions, "Buy Now")

  def test_build_evaluation_request_comprehensive(self) -> None:
    """Tests build_evaluation_request accurately populates all sub-configs."""
    args = utils.parse_args([
        "-project_id",
        "my-gcp-proj",
        "-api_key",
        "my-api-key",
        "-location",
        "us-central1",
        "-model_location",
        "global",
        "-vu",
        "gs://bucket/vid.mp4",
        "-slices",
        "universal",
        "-bq_dataset",
        "my_ds",
        "-bq_table",
        "my_tbl",
        "-brand",
        "MyBrand",
        "-products",
        "Product A",
    ])
    req = utils.build_evaluation_request(args)
    self.assertIsNotNone(req.gcp_config)
    self.assertEqual(req.gcp_config.project_id, "my-gcp-proj")
    self.assertEqual(req.gcp_config.location, "us-central1")
    self.assertEqual(req.gemini_config.model_location, "global")
    self.assertEqual(req.gemini_config.api_key, "my-api-key")
    self.assertIsNotNone(req.bigquery_settings)
    self.assertEqual(req.bigquery_settings.project_id, "my-gcp-proj")
    self.assertEqual(req.bigquery_settings.dataset_name, "my_ds")
    self.assertEqual(req.bigquery_settings.table_name, "my_tbl")
    self.assertIsNotNone(req.brand_context)
    self.assertEqual(req.brand_context.brand_name, "MyBrand")

  def test_build_evaluation_request_omits_bigquery_settings_when_not_provided(
      self,
  ) -> None:
    """Tests that build_evaluation_request sets bigquery_settings to None."""
    old_ds = os.environ.get("BQ_DATASET")
    old_tbl = os.environ.get("BQ_TABLE")
    try:
      if "BQ_DATASET" in os.environ:
        del os.environ["BQ_DATASET"]
      if "BQ_TABLE" in os.environ:
        del os.environ["BQ_TABLE"]
      args = utils.parse_args([
          "-project_id",
          "my-gcp-proj",
          "-api_key",
          "my-api-key",
          "-vu",
          "gs://bucket/vid.mp4",
      ])
      req = utils.build_evaluation_request(args)
      self.assertIsNone(req.bigquery_settings)
    finally:
      if old_ds is not None:
        os.environ["BQ_DATASET"] = old_ds
      if old_tbl is not None:
        os.environ["BQ_TABLE"] = old_tbl

  def test_parse_features_to_evaluate_dict(self) -> None:
    """Tests parsing when input is already a Python dict."""
    input_dict = {
        "universal": ["a_dynamic_start"],
        "shorts": ["tight_framing"],
    }
    parsed = utils.parse_features_to_evaluate(input_dict)
    self.assertEqual(parsed, input_dict)

  def test_parse_features_to_evaluate_json(self) -> None:
    """Tests parsing JSON format for features_to_evaluate."""
    raw = (
        '{"universal": ["a_dynamic_start", "b_brand_visuals"], '
        '"shorts": ["tight_framing"]}'
    )
    parsed = utils.parse_features_to_evaluate(raw)
    self.assertEqual(
        parsed,
        {
            "universal": ["a_dynamic_start", "b_brand_visuals"],
            "shorts": ["tight_framing"],
        },
    )

  def test_parse_features_to_evaluate_invalid_format_raises(self) -> None:
    """Tests that non-JSON format raises ValueError."""
    with self.assertRaises(ValueError) as ctx:
      utils.parse_features_to_evaluate(
          "universal:a_dynamic_start,b_brand_visuals;shorts:tight_framing"
      )
    self.assertIn("Invalid features_to_evaluate", str(ctx.exception))

  def test_parse_features_to_evaluate_malformed_json_raises(self) -> None:
    """Tests that malformed JSON raises ValueError."""
    with self.assertRaises(ValueError) as ctx:
      utils.parse_features_to_evaluate("{universal: [dynamic_start]}")
    self.assertIn(
        "Invalid features_to_evaluate JSON string", str(ctx.exception)
    )


if __name__ == "__main__":
  unittest.main()
