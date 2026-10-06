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

"""Service that interacts with the Google Cloud Storage API."""

import logging

from google.cloud import storage

import configuration

logger = logging.getLogger("abcd_detector")


class GCSAPIService:
  """Service that interacts with Google Cloud Storage."""

  def __init__(self, gcp_config: configuration.GCPConfig) -> None:
    """Initializes the GCSAPIService.

    Args:
      gcp_config: GCP configuration including project ID.
    """
    if gcp_config is None:
      raise ValueError("gcp_config is required and cannot be None.")
    self.gcp_config = gcp_config
    self.project_id = gcp_config.project_id

  def parse_gcs_uri(self, uri: str) -> tuple[str, str]:
    """Parses a GCS URI into bucket and blob name components.

    Args:
      uri: GCS URI formatted as 'gs://bucket/blob_path'.

    Returns:
      Tuple of (bucket_name, blob_name).

    Raises:
      ValueError: If URI does not start with 'gs://'.
    """
    if not uri.startswith("gs://"):
      raise ValueError(f"Invalid GCS URI: '{uri}'. Must start with 'gs://'.")
    raw_path = uri[5:]
    if "/" not in raw_path:
      return raw_path, ""
    bucket_name, blob_name = raw_path.split("/", 1)
    return bucket_name, blob_name

  def get_blob(self, uri: str) -> storage.Blob | None:
    """Returns GCS Blob object for a URI if found.

    Args:
      uri: Full GCS URI ('gs://bucket/blob_path').

    Returns:
      storage.Blob instance, or None if not found.
    """
    bucket_name, blob_name = self.parse_gcs_uri(uri)
    client = storage.Client(project=self.gcp_config.project_id)
    bucket = client.bucket(bucket_name)
    return bucket.get_blob(blob_name)

  def upload_blob(self, uri: str, file_path: str) -> None:
    """Uploads a local file to the destination GCS URI.

    Args:
      uri: Destination GCS URI ('gs://bucket/blob_path').
      file_path: Local path to the file to upload.
    """
    bucket_name, blob_name = self.parse_gcs_uri(uri)
    if not blob_name:
      raise ValueError(f"Cannot upload to GCS URI without blob path: '{uri}'")
    client = storage.Client(project=self.gcp_config.project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    logger.info("Uploaded '%s' to '%s'", file_path, uri)

  def download_blob_to_file(
      self, uri: str, destination_file_path: str
  ) -> None:
    """Downloads a GCS blob to a local file path.

    Args:
      uri: Source GCS URI ('gs://bucket/blob_path').
      destination_file_path: Local destination file path.
    """
    bucket_name, blob_name = self.parse_gcs_uri(uri)
    client = storage.Client(project=self.gcp_config.project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    if blob is None:
      raise FileNotFoundError(f"GCS object not found: '{uri}'")
    blob.download_to_filename(destination_file_path)
    logger.info("Downloaded '%s' to '%s'", uri, destination_file_path)

  def list_blobs(self, uri: str) -> list[str]:
    """Lists all full gs:// URIs under a bucket folder or prefix.

    Args:
      uri: GCS URI folder prefix ('gs://bucket/prefix/').

    Returns:
      List of full GCS URIs matching the prefix.
    """
    bucket_name, prefix = self.parse_gcs_uri(uri)
    client = storage.Client(project=self.gcp_config.project_id)
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix if prefix else None)
    return [
        f"gs://{bucket_name}/{blob.name}"
        for blob in blobs
        if not blob.name.endswith("/")
    ]

  def get_video_name_from_uri(self, uri: str) -> str:
    """Extracts the video file name from any URI or path.

    Args:
      uri: Video URI or file path string.

    Returns:
      Base filename extracted from the URI.
    """
    stripped = uri.rstrip("/")
    if "/" in stripped:
      return stripped.split("/")[-1]
    return stripped
