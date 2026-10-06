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

"""Structural protocol for creative providers retrieving video URLs."""

from typing import Protocol

import configuration


class CreativeProviderProto(Protocol):
  """Protocol providing structural typing for creative providers."""

  def __init__(self) -> None:
    """Initializes the creative provider protocol."""
    ...

  def get_creative_uris(
      self, request: configuration.EvaluationRequest
  ) -> list[str]:
    """Retrieves creative URIs to process based on the provider type.

    Args:
      request: EvaluationRequest containing video URIs and configurations.

    Returns:
      List or iterable of creative URI strings.
    """
    ...
