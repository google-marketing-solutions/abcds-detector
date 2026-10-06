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

"""Creative provider to retrieve video URIs from YouTube."""

import configuration


class YoutubeCreativeProvider:
  """Retrieves YouTube video URIs for ABCD evaluation."""

  def __init__(self) -> None:
    """Initializes the YoutubeCreativeProvider."""
    pass

  def get_creative_uris(
      self, request: configuration.EvaluationRequest
  ) -> list[str]:
    """Retrieves YouTube URLs from the evaluation request.

    Args:
      request: EvaluationRequest containing video URIs.

    Returns:
      List of YouTube video URIs to evaluate.
    """
    return request.video_uris
