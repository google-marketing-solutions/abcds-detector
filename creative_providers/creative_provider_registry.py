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

"""Module that registers all the required providers for each creative
data source

For example:
    - GCSProviderService - retrieves uris from Google Cloud storage
    - YoutubeProviderService - retrieves uris from Youtube
"""

import models
from creative_providers import creative_provider_factory
from creative_providers import gcs_creative_provider
from creative_providers import youtube_creative_provider

# Content Generation Service Factory
provider_factory = creative_provider_factory.CreativeProviderFactory()


def register_content_generation_services():
  """Register the different creative providers"""
  provider_factory.register_provider(
      models.CreativeProviderType.GCS.value,
      gcs_creative_provider.GCSCreativeProvider,
  )
  provider_factory.register_provider(
      models.CreativeProviderType.YOUTUBE.value,
      youtube_creative_provider.YoutubeCreativeProvider,
  )


register_content_generation_services()
