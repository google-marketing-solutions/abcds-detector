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

"""Creative provider to retrieve creative URIs from Google Cloud Storage."""

from collections.abc import Iterator

import configuration
from gcp_api_services import gcs_api_service


class GCSCreativeProvider:
  """Retrieves and expands GCS video URIs for ABCD evaluation."""

  def __init__(
      self, gcs_service: gcs_api_service.GCSAPIService | None = None
  ) -> None:
    """Initializes the GCSCreativeProvider.

    Args:
      gcs_service: Optional GCSAPIService instance.
    """
    self.gcs_service = gcs_service

  def get_creative_uris(
      self, request: configuration.EvaluationRequest
  ) -> Iterator[str]:
    """Expands any GCS URI folder path into individual video file URIs.

    Args:
      request: EvaluationRequest containing video URIs and configurations.

    Returns:
      Iterator yielding individual GCS video URIs.
    """
    service = self.gcs_service or gcs_api_service.GCSAPIService(
        gcp_config=request.gcp_config
    )
    for uri in request.video_uris:
      if uri.endswith("/"):
        for blob_uri in service.list_blobs(uri):
          yield blob_uri
      else:
        yield uri
