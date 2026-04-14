"""Class that implements the creative provider to retrieve
creative uris from Youtube
"""

import configuration


class YoutubeCreativeProvider:
  """Class that implements the creative provider to
  retrieve creative uris from Youtube
  """

  def __init__(self):
    pass

  def get_creative_uris(self, config: configuration.Configuration) -> any:
    """Get Youtube URLs"""
    return config.video_uris
