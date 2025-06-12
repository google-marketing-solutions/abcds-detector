#!/usr/bin/env python3

###########################################################################
#
#    Copyright 2024 Google LLC
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#            https://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
###########################################################################

"""Service factory that implements a factory class to retrieve/register
providers for the different creative data sources"""

from creative_providers.creative_provider_proto import CreativeProviderProto
from models import CreativeProviderType


class CreativeProviderFactory:
    """Service factory that implements a factory class to retrieve/register
    services for the different content generation types"""

    def __init__(self):
        """Init method for CreativeProviderFactory."""
        self._providers = {}

    def register_provider(
        self, provider_type: CreativeProviderType, provider: CreativeProviderProto
    ) -> None:
        """Register creative provider

        Args:
            provider_type: the type of the provider (e.g. GCS, Youtube, etc.)
            provider: an instance (concrete implementation) of the provider
        """
        self._providers[provider_type] = provider

    def get_provider(
        self, provider_type: CreativeProviderType
    ) -> CreativeProviderProto:
        """Get content generation service by type

        Args:
            provider_type: the type of the provider (e.g. GCS, Youtube, etc.)
        Returns:
            provider: an instance (concrete implementation) of the service
        """
        provider = self._providers.get(provider_type)
        if not provider:
            raise ValueError(provider_type)
        return provider()
