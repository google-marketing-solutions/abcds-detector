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

"""Module to trim videos stored in Google Cloud Storage"""

import os
from moviepy.editor import VideoFileClip

### REMOVE FOR COLAB - START
from input_parameters import VERBOSE
from helpers.helpers import bucket, get_file_name_from_gcs_url, get_video_format

### REMOVE FOR COLAB - END


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
        bucket: bucket where the video lives
        video_uri: the video location
    """
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
