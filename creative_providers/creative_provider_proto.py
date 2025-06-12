"""Parent class to provide structural inheritance for creative providers
that will implement specific logic to retrieve creative URLs depending on the
data source.

For example:
    - GCSProviderService - retrieves uris from Google Cloud storage
    - YoutubeProviderService - retrieves uris from Youtube
"""

from typing import Protocol


class CreativeProviderProto(Protocol):
    """Parent class to provide structural inheritance for creative providers"""

    def __init__(self):
        pass

    def get_creative_uris(self) -> list[str]:
        """Implements specific logic depending on the provider
        to retrieve creative uris to process
        """
        pass
