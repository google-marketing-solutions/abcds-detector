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

"""Parent class to provide structural inheritance for creative providers
that will implement specific logic to retrieve creative URLs depending on the
data source.

For example:
    - GCSProviderService - retrieves uris from Google Cloud storage
    - YoutubeProviderService - retrieves uris from Youtube
"""

from typing import Protocol
import configuration


class CreativeProviderProto(Protocol):
    """Parent class to provide structural inheritance for creative providers"""

    def __init__(self):
        pass

    def get_creative_uris(self, config: configuration.Configuration) -> list[str]:
        """Implements specific logic depending on the provider
        to retrieve creative uris to process
        """
        pass
