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
)

### REMOVE FOR COLAB - END


def get_bucket() -> any:
    """Builds GCS bucket"""
    # Init cloud storage bucket
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    return bucket


# Knowledge Graph module


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


def get_file_name_from_gcs_url(gcs_url: str) -> tuple[str]:
    """Get file name from GCS url
    Args:
        gcs_url: the gcs url with the file name
    Returns:
        file_name_with_format: the file name with its format
        file_name: the file name
    """
    url_parts = gcs_url.split("/")
    if len(url_parts) == 3:
        file_name = url_parts[2].split(".")[0]
        file_name_with_format = url_parts[2]
        return file_name, file_name_with_format
    return ""


def get_video_format(video_location: str):
    """Gets video format from gcs url
    Args:
        video_location: gcs video location
    Returns:
        video_format: video format
    """
    gcs_parts = video_location.split(".")
    if len(gcs_parts) == 2:
        video_format = gcs_parts[1]
        return video_format
    return ""


def get_n_secs_video_uri_from_uri(video_uri: str, new_name_part: str):
    """Get uri for the n seconds video
    Args:
        video_uri: str
    Return:
        video_name_n_secs
    """
    gcs_parts = video_uri.split(".")
    if len(gcs_parts) == 2:
        video_format = gcs_parts[1]
        long_video_name_parts = gcs_parts[0].split("/")
        if len(long_video_name_parts) == 6:
            gcs = long_video_name_parts[0]
            bucket_name = long_video_name_parts[2]
            brand = long_video_name_parts[3]
            videos_folder = long_video_name_parts[4]
            # Last element is the video name
            video_name = f"{long_video_name_parts[-1]}_{new_name_part}.{video_format}"
            n_secs_video_uri = (
                f"{gcs}//{bucket_name}/{brand}/{videos_folder}/{video_name}"
            )
        return n_secs_video_uri
    return ""


def store_assessment_results_locally(brand_name: str, assessment: any) -> None:
    """Store test results in a file"""
    file_name = f"results/{brand_name}_{assessment.get('video_uri')}.json"
    assessment = {
        "brand_name": brand_name,
        "assessment": assessment
    }
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(assessment, f, ensure_ascii=False, indent=4)


def trim_videos(brand_name: str):
    """Trims videos to create new versions of 5 secs
    Args:
        brand_name: the brand to trim the videos for
    """
    local_videos_path = "abcd_videos"
    # Check if the directory exists
    if not os.path.exists(local_videos_path):
        os.makedirs(local_videos_path)
    # Get videos from GCS
    brand_videos_folder = f"{brand_name}/videos"
    bucket = get_bucket()
    blobs = bucket.list_blobs(prefix=brand_videos_folder)
    # Video processing
    for video in blobs:
        if video.name == f"{brand_videos_folder}/" or "1st_5_secs" in video.name:
            # Skip parent folder and trimmed versions of videos
            continue
        video_name, video_name_with_format = get_file_name_from_gcs_url(video.name)
        video_name_1st_5_secs = (
            f"{video_name}_1st_5_secs.{get_video_format(video_name_with_format)}"
        )
        video_name_1st_5_secs_parent_folder = (
            f"{brand_videos_folder}/{video_name_1st_5_secs}"
        )
        video_1st_5_secs_metadata = bucket.get_blob(video_name_1st_5_secs_parent_folder)
        # Only process the video if it was not previously trimmed
        if not video_1st_5_secs_metadata:
            # Download the video from GCS
            download_and_save_video(
                output_path=local_videos_path,
                video_name_with_format=video_name_with_format,
                video_uri=video.name,
            )
            # Trim the video
            trim_and_push_video_to_gcs(
                local_videos_path=local_videos_path,
                gcs_output_path=brand_videos_folder,
                video_name_with_format=video_name_with_format,
                new_video_name=video_name_1st_5_secs,
                trim_start=0,
                trim_end=5,
            )
        else:
            print(f"Video {video.name} has already been trimmed. Skipping...\n")


def download_and_save_video(
    output_path: str, video_name_with_format: str, video_uri: str
) -> None:
    """Downloads a video from Google Cloud Storage
    and saves it locally
    Args:
        output_path: the path to store the video
        video_name_with_format: the video name with format
        video_uri: the video location
    """
    bucket = get_bucket()
    video_blob = bucket.blob(video_uri)
    video = video_blob.download_as_string(client=None)
    with open(f"{output_path}/{video_name_with_format}", "wb") as f:
        f.write(video)  # writing content to file
        if VERBOSE:
            print(f"Video {video_uri} downloaded and saved!\n")


def trim_and_push_video_to_gcs(
    local_videos_path: str,
    gcs_output_path: str,
    video_name_with_format: str,
    new_video_name: str,
    trim_start: int,
    trim_end: int,
) -> None:
    """Trims a video to generate a 5 secs version
    Args:
        local_videos_path: where the videos are stored locally
        gcs_output_path: the path to store the video in Google Cloud storage
        video_name_with_format: the original video name with format
        new_video_name: the new name for the trimmed video
        trim_start: the start time to trim the video
        trim_end: the end time to trim the video
    """
    bucket = get_bucket()
    # Load video dsa gfg intro video
    local_video_path = f"{local_videos_path}/{video_name_with_format}"
    clip = VideoFileClip(local_video_path)
    # Get only first N seconds
    clip = clip.subclip(trim_start, trim_end)
    # Save the clip
    new_video_name_path = f"{local_videos_path}/{new_video_name}"
    clip.write_videofile(new_video_name_path)
    # Upload back to Google Cloud Storage
    blob = bucket.blob(f"{gcs_output_path}/{new_video_name}")
    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions.
    generation_match_precondition = 0
    blob.upload_from_filename(
        new_video_name_path, if_generation_match=generation_match_precondition
    )
    if VERBOSE:
        print(f"File {new_video_name} uploaded to {gcs_output_path}.\n")
