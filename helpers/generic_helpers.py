#!/usr/bin/env python3

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

"""Module to load generic helper functions"""

import json
import os
import urllib
from google.cloud import storage
from moviepy.editor import VideoFileClip


### REMOVE FOR COLAB - START
from input_parameters import (
    VERBOSE,
    KNOWLEDGE_GRAPH_API_KEY,
    BUCKET_NAME,
    ANNOTATION_PATH,
    FFMPEG_BUFFER
)

### REMOVE FOR COLAB - END



def get_blob(uri: str) -> any:
    """Return GCS blob object from full uri."""
    bucket, path = uri.replace("gs://", "").split("/", 1)
    return storage.Client().get_bucket(bucket).get_blob(path)


def upload_blob(uri: str, filename: str) -> any:
    """Uploads GCS blob object from file."""
    bucket, path = uri.replace("gs://", "").split("/", 1)
    storage.Client().get_bucket(bucket).blob(path).upload_from_filename(FFMPEG_BUFFER)


def get_annotation_uri(video_uri: str) -> str:
  """Helper to translate video to annotation uri."""
  return video_uri.replace('gs://', ANNOTATION_PATH).replace('.', '_') + '/'


def get_reduced_uri(video_uri: str) -> str:
  """Helper to translate video to reduced video uri."""
  return get_annotation_uri(video_uri) + "reduced_1st_5_secs.mp4"


def get_knowledge_graph_entities(queries: list[str]) -> dict[str, dict]:
    """Get the knowledge Graph Entities for a list of queries
    Args:
        queries: a list of entities to find in KG
    Returns:
        kg_entities: entities found in KG
        Format example: entity id is the key and entity details the value
        kg_entities = {
            "mcy/12": {} TODO (ae) add here
        }
    """
    kg_entities = {}
    try:
        for query in queries:
            service_url = "https://kgsearch.googleapis.com/v1/entities:search"
            params = {
                "query": query,
                "limit": 10,
                "indent": True,
                "key": KNOWLEDGE_GRAPH_API_KEY,
            }
            url = f"{service_url}?{urllib.parse.urlencode(params)}"
            response = json.loads(urllib.request.urlopen(url).read())
            for element in response["itemListElement"]:
                kg_entity_name = element["result"]["name"]
                # To only add the exact KG entity
                if query.lower() == kg_entity_name.lower():
                    kg_entities[element["result"]["@id"][3:]] = element["result"]
        return kg_entities
    except Exception as ex:
        print(
            f"\n\x1b[31mERROR: There was an error fetching the Knowledge Graph entities. Please check that your API key is correct. ERROR: {ex}\x1b[0m"
        )
        raise


def trim_video(video_uri: str):
    """Trims videos to create new versions of 5 secs
    Args:
        video_uri: the video to trim the length for
    """

    reduced_uri = get_reduced_uri(video_uri)
    reduced_blob = get_blob(reduced_uri)
    print('REDUCED:', reduced_uri)
    if reduced_blob is None:
        print(f"Shortening video {video_uri}.")

        # download
        with open(FFMPEG_BUFFER, "wb") as f:
            f.write(get_blob(video_uri).download_as_string(client=None))

        # trim
        clip = VideoFileClip(FFMPEG_BUFFER)
        clip = clip.subclip(0, 5)
        clip.write_videofile(FFMPEG_BUFFER)

        # upload
        upload_blob(reduced_uri, FFMPEG_BUFFER)

    else:
        print(f"Video {video_uri} has already been trimmed. Skipping...\n")
