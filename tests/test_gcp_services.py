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

"""Tests for Google Cloud Platform services (GCS and BigQuery APIs)."""

import json
import unittest
from unittest import mock

import configuration
from gcp_api_services import gcs_api_service
from gcp_api_services import gemini_api_service
import models


class TestGCPServices(unittest.TestCase):
  """Tests for Google Cloud Storage service utilities and parsing."""

  def test_gcs_api_service_requires_project_id(self) -> None:
    """Tests that GCSAPIService raises ValueError if gcp_config is None."""
    with self.assertRaises(ValueError) as ctx:
      gcs_api_service.GCSAPIService(gcp_config=None)  # type: ignore
    self.assertIn("gcp_config is required", str(ctx.exception))

  def test_gcs_api_service_parse_valid_uri(self) -> None:
    """Tests that GCSAPIService parses gs://bucket/path correctly."""
    service = gcs_api_service.GCSAPIService(
        gcp_config=configuration.GCPConfig(project_id="test-project")
    )
    bucket, path = service.parse_gcs_uri("gs://my-bucket/videos/sample.mp4")
    self.assertEqual(bucket, "my-bucket")
    self.assertEqual(path, "videos/sample.mp4")

  def test_gcs_api_service_parse_invalid_uri_raises(self) -> None:
    """Tests that non-gs:// URI raises ValueError."""
    service = gcs_api_service.GCSAPIService(
        gcp_config=configuration.GCPConfig(project_id="test-project")
    )
    with self.assertRaises(ValueError) as ctx:
      service.parse_gcs_uri("https://storage.googleapis.com/b/v.mp4")
    self.assertIn("Must start with 'gs://'", str(ctx.exception))

  def test_gcs_api_service_get_video_name(self) -> None:
    """Tests extracting video name from various URI formats."""
    service = gcs_api_service.GCSAPIService(
        gcp_config=configuration.GCPConfig(project_id="test-project")
    )
    self.assertEqual(
        service.get_video_name_from_uri("gs://bucket/path/my_ad.mp4"),
        "my_ad.mp4",
    )
    self.assertEqual(
        service.get_video_name_from_uri("https://youtube.com/watch?v=12345"),
        "watch?v=12345",
    )

  @mock.patch("google.cloud.storage.Client")
  def test_gcs_api_service_list_blobs(
      self, mock_storage_client_cls: mock.MagicMock
  ) -> None:
    """Tests listing blobs with a mocked storage client."""
    mock_client = mock.MagicMock()
    mock_storage_client_cls.return_value = mock_client
    mock_bucket = mock.MagicMock()
    mock_blob1 = mock.MagicMock()
    mock_blob1.name = "folder/vid1.mp4"
    mock_blob2 = mock.MagicMock()
    mock_blob2.name = "folder/"  # Directory marker, should be skipped
    mock_blob3 = mock.MagicMock()
    mock_blob3.name = "folder/vid2.mp4"

    mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2, mock_blob3]
    mock_client.bucket.return_value = mock_bucket

    service = gcs_api_service.GCSAPIService(
        gcp_config=configuration.GCPConfig(project_id="test-project")
    )
    blobs = service.list_blobs("gs://test-bucket/folder/")
    self.assertEqual(
        blobs,
        [
            "gs://test-bucket/folder/vid1.mp4",
            "gs://test-bucket/folder/vid2.mp4",
        ],
    )

  def test_gemini_api_service_initialization(self) -> None:
    """Tests that GeminiAPIService initializes with GCPConfig."""
    gcp_config = configuration.GCPConfig(project_id="test-project")
    gemini_config = configuration.GeminiConfig(api_key="test-api-key")
    service = gemini_api_service.GeminiAPIService(gcp_config, gemini_config)
    self.assertEqual(service.config.api_key, "test-api-key")
    self.assertEqual(service.config.model_name, "gemini-3.8-flash")
    self.assertEqual(service.gcp_config.project_id, "test-project")

  def test_gemini_api_service_resolve_video_uri_non_gcs(self) -> None:
    """Tests that non-GCS URIs are returned as-is without registration."""
    service = gemini_api_service.GeminiAPIService(
        configuration.GCPConfig(project_id="test-project"),
        configuration.GeminiConfig(api_key="test-api-key"),
    )
    result = service._resolve_video_uri("https://example.com/video.mp4")
    self.assertEqual(result, "https://example.com/video.mp4")

  @mock.patch("google.auth.default")
  def test_gemini_api_service_resolve_video_uri_gcs(
      self, mock_auth_default: mock.MagicMock
  ) -> None:
    """Tests that GCS URIs are registered and cached."""
    mock_auth_default.return_value = (mock.MagicMock(), "test-project")
    service = gemini_api_service.GeminiAPIService(
        configuration.GCPConfig(project_id="test-project"),
        configuration.GeminiConfig(api_key="test-api-key"),
    )
    mock_file = mock.MagicMock()
    mock_file.uri = (
        "https://generativelanguage.googleapis.com/v1beta/files/"
        "mock-registered-id"
    )
    mock_file.state = None

    mock_response = mock.MagicMock()
    mock_response.files = [mock_file]
    service.client = mock.MagicMock()
    service.client.files.register_files.return_value = mock_response

    # First call - registers and caches
    result = service._resolve_video_uri("gs://test-bucket/video.mp4")
    self.assertEqual(
        result,
        "https://generativelanguage.googleapis.com/v1beta/files/"
        "mock-registered-id",
    )
    service.client.files.register_files.assert_called_once()

    # Second call - returns from cache without calling register_files again
    result2 = service._resolve_video_uri("gs://test-bucket/video.mp4")
    self.assertEqual(
        result2,
        "https://generativelanguage.googleapis.com/v1beta/files/"
        "mock-registered-id",
    )
    self.assertEqual(service.client.files.register_files.call_count, 1)

  def test_get_modality_parts_video(self) -> None:
    """Tests _get_modality_parts for video modality."""
    service = gemini_api_service.GeminiAPIService(
        configuration.GCPConfig(project_id="test-project"),
        configuration.GeminiConfig(api_key="test-api-key"),
    )
    parts = service._get_modality_parts(
        "test prompt", {"type": "VIDEO", "video_uri": "gs://bucket/test.mp4"}
    )
    self.assertEqual(len(parts), 2)
    self.assertEqual(parts[0].file_data.file_uri, "gs://bucket/test.mp4")
    self.assertEqual(parts[0].file_data.mime_type, "video/mp4")
    self.assertEqual(parts[1].text, "test prompt")

  @mock.patch("google.genai.Client")
  def test_call_gemini_vertex_ai_success(
      self, mock_client_cls: mock.MagicMock
  ) -> None:
    """Tests that call_gemini_vertex_ai invokes generate_content."""
    mock_client = mock.MagicMock()
    mock_client_cls.return_value = mock_client
    mock_response = mock.MagicMock()
    mock_response.parsed = [{"id": "test_feature", "is_detected": True}]
    mock_response.text = json.dumps(
        [{"id": "test_feature", "is_detected": True}]
    )
    mock_client.models.generate_content.return_value = mock_response

    service = gemini_api_service.GeminiAPIService(
        configuration.GCPConfig(project_id="test-proj", location="us-central1"),
        configuration.GeminiConfig(
            api_key="test-api-key", model_location="us-central1"
        ),
    )
    result = service.call_gemini_vertex_ai(
        video_uri="gs://test-bucket/video.mp4",
        prompt_config=models.PromptConfig(
            prompt="prompt", system_instructions="system"
        ),
        response_schema={"type": "array"},
    )
    self.assertEqual(result, [{"id": "test_feature", "is_detected": True}])
    mock_client_cls.assert_called_with(
        vertexai=True,
        project="test-proj",
        location="us-central1",
    )


if __name__ == "__main__":
  unittest.main()
