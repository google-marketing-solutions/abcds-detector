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

"""Factory class to register and retrieve creative providers."""

from typing import Any

from creative_providers import creative_provider_proto
import models


class CreativeProviderFactory:
  """Factory to register and retrieve creative providers by source type."""

  def __init__(self) -> None:
    """Initializes the CreativeProviderFactory."""
    self._providers: dict[models.CreativeProviderType | str, Any] = {}

  def register_provider(
      self,
      provider_type: models.CreativeProviderType | str,
      provider: Any,
  ) -> None:
    """Registers a creative provider for a given provider type.

    Args:
      provider_type: CreativeProviderType enum or string key.
      provider: Class or factory implementing CreativeProviderProto.
    """
    self._providers[provider_type] = provider

  def get_provider(
      self, provider_type: models.CreativeProviderType | str
  ) -> creative_provider_proto.CreativeProviderProto:
    """Gets an instantiated creative provider by type.

    Args:
      provider_type: CreativeProviderType enum or string key.

    Returns:
      Instantiated provider conforming to CreativeProviderProto.

    Raises:
      ValueError: If provider_type is not registered in the factory.
    """
    provider = self._providers.get(provider_type)
    if not provider:
      raise ValueError(f"Provider not found for type: {provider_type}")
    return provider()
