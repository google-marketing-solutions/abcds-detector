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

"""Tests for ABCD Detector configuration models and validation."""

import os
import unittest

import configuration


class TestConfiguration(unittest.TestCase):
  """Tests for dataclass configurations and validation logic."""

  def test_gcp_config_missing_project_id_raises(self) -> None:
    """Tests that missing project_id in GCPConfig raises ValueError."""
    old_pid = os.environ.get("PROJECT_ID")
    old_gcp = os.environ.get("GOOGLE_CLOUD_PROJECT")
    try:
      if "PROJECT_ID" in os.environ:
        del os.environ["PROJECT_ID"]
      if "GOOGLE_CLOUD_PROJECT" in os.environ:
        del os.environ["GOOGLE_CLOUD_PROJECT"]
      with self.assertRaises(ValueError) as ctx:
        configuration.GCPConfig()
      self.assertIn("project_id is required", str(ctx.exception))
    finally:
      if old_pid is not None:
        os.environ["PROJECT_ID"] = old_pid
      if old_gcp is not None:
        os.environ["GOOGLE_CLOUD_PROJECT"] = old_gcp

  def test_gemini_config_valid(self) -> None:
    """Tests valid GeminiConfig creation with defaults."""
    config = configuration.GeminiConfig(api_key="valid-test-key")
    self.assertEqual(config.api_key, "valid-test-key")
    self.assertEqual(config.model_name, "gemini-3.8-flash")
    self.assertEqual(config.model_location, "global")
    self.assertEqual(config.temperature, 0.1)
    self.assertEqual(config.max_output_tokens, 65536)

  def test_gemini_config_missing_api_key_raises_error(self) -> None:
    """Ensures missing API key raises ValueError without silent fallbacks."""
    old_env = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
      del os.environ["GEMINI_API_KEY"]
    try:
      with self.assertRaises(ValueError) as ctx:
        configuration.GeminiConfig(api_key="")
      self.assertIn("GEMINI_API_KEY is required", str(ctx.exception))
    finally:
      if old_env is not None:
        os.environ["GEMINI_API_KEY"] = old_env

  def test_gemini_config_empty_model_location_raises(self) -> None:
    """Tests that empty model_location raises ValueError."""
    with self.assertRaises(ValueError) as ctx:
      configuration.GeminiConfig(api_key="valid-test-key", model_location="")
    self.assertIn(
        "model_location must be a non-empty string", str(ctx.exception)
    )

  def test_brand_context_valid_with_products(self) -> None:
    """Tests valid BrandContext with brand_name and branded_products."""
    ctx = configuration.BrandContext(
        brand_name="Google", branded_products=["Pixel 9"]
    )
    self.assertEqual(ctx.brand_name, "Google")
    self.assertEqual(ctx.branded_products, ["Pixel 9"])
    self.assertEqual(ctx.branded_call_to_actions, [])

  def test_brand_context_missing_brand_name_raises(self) -> None:
    """Tests that missing brand_name raises ValueError."""
    with self.assertRaises(ValueError) as exc_info:
      configuration.BrandContext(brand_name="", branded_products=["Pixel 9"])
    self.assertIn("brand_name is required", str(exc_info.exception))

  def test_brand_context_missing_products_raises(self) -> None:
    """Tests that missing branded_products raises ValueError."""
    with self.assertRaises(ValueError) as exc_info:
      configuration.BrandContext(brand_name="Google", branded_products=[])
    self.assertIn("branded_products is required", str(exc_info.exception))

  def test_bigquery_settings_generic_env(self) -> None:
    """Tests BigQuerySettings reading PROJECT_ID, BQ_DATASET, BQ_TABLE."""
    os.environ["PROJECT_ID"] = "test-project-123"
    os.environ["BQ_DATASET"] = "test_dataset"
    os.environ["BQ_TABLE"] = "test_table"
    try:
      bq = configuration.BigQuerySettings()
      self.assertEqual(bq.project_id, "test-project-123")
      self.assertEqual(bq.dataset_name, "test_dataset")
      self.assertEqual(bq.table_name, "test_table")
    finally:
      del os.environ["PROJECT_ID"]
      del os.environ["BQ_DATASET"]
      del os.environ["BQ_TABLE"]

  def test_bigquery_settings_missing_raises(self) -> None:
    """Tests that missing BigQuery settings raises ValueError."""
    with self.assertRaises(ValueError) as ctx:
      configuration.BigQuerySettings(
          project_id="", dataset_name="", table_name=""
      )
    self.assertIn("Missing required BigQuery settings", str(ctx.exception))

  def test_evaluation_request_empty_videos_raises(self) -> None:
    """Tests that empty video_uris list raises ValueError on instantiation."""
    config = configuration.GeminiConfig(api_key="valid-test-key")
    with self.assertRaises(ValueError) as ctx:
      configuration.EvaluationRequest(
          gcp_config=configuration.GCPConfig(project_id="test-project"),
          gemini_config=config,
          video_uris=[],
      )
    self.assertIn("At least one video URI must be provided", str(ctx.exception))

  def test_evaluation_request_missing_gcp_config_raises(self) -> None:
    """Tests that missing gcp_config raises ValueError."""
    config = configuration.GeminiConfig(api_key="valid-test-key")
    with self.assertRaises(ValueError) as ctx:
      configuration.EvaluationRequest(
          gcp_config=None,  # type: ignore
          gemini_config=config,
          video_uris=["gs://bucket/video.mp4"],
      )
    self.assertIn("gcp_config is required", str(ctx.exception))

  def test_evaluation_request_missing_gemini_config_raises(self) -> None:
    """Tests that missing gemini_config raises ValueError."""
    with self.assertRaises(ValueError) as ctx:
      configuration.EvaluationRequest(
          gcp_config=configuration.GCPConfig(project_id="test-project"),
          gemini_config=None,  # type: ignore
          video_uris=["gs://bucket/video.mp4"],
      )
    self.assertIn("gemini_config is required", str(ctx.exception))

  def test_evaluation_request_missing_brand_context_when_metadata_disabled(
      self,
  ) -> None:
    """Tests that disabling metadata extraction requires brand_context."""
    config = configuration.GeminiConfig(api_key="valid-test-key")
    with self.assertRaises(ValueError) as ctx:
      configuration.EvaluationRequest(
          gcp_config=configuration.GCPConfig(project_id="test-project"),
          gemini_config=config,
          video_uris=["gs://bucket/video.mp4"],
          extract_brand_metadata=False,
          brand_context=None,
      )
    self.assertIn(
        "brand_context with brand_name and branded_products",
        str(ctx.exception),
    )

  def test_evaluation_request_with_bigquery_settings(self) -> None:
    """Tests EvaluationRequest with valid BigQuerySettings."""
    config = configuration.GeminiConfig(api_key="valid-test-key")
    bq = configuration.BigQuerySettings(
        project_id="p", dataset_name="d", table_name="t"
    )
    req = configuration.EvaluationRequest(
        gcp_config=configuration.GCPConfig(project_id="test-project"),
        gemini_config=config,
        video_uris=["gs://bucket/video.mp4"],
        bigquery_settings=bq,
    )
    self.assertIsNotNone(req.bigquery_settings)
    self.assertEqual(req.bigquery_settings.dataset_name, "d")
    self.assertEqual(req.bigquery_settings.table_name, "t")

  def test_evaluation_request_without_bigquery_settings_is_none(self) -> None:
    """Tests that EvaluationRequest without BQ settings has None."""
    config = configuration.GeminiConfig(api_key="valid-test-key")
    req = configuration.EvaluationRequest(
        gcp_config=configuration.GCPConfig(project_id="test-project"),
        gemini_config=config,
        video_uris=["gs://bucket/video.mp4"],
    )
    self.assertIsNone(req.bigquery_settings)


if __name__ == "__main__":
  unittest.main()
