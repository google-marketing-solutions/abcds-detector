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

"""Module to generate video annotations using the Video Intelligence API"""

from google.cloud import videointelligence

### REMOVE FOR COLAB - START
from helpers.generic_helpers import (
    get_bucket,
    get_file_name_from_gcs_url,
)

from helpers.annotations_helpers import get_existing_annotations_from_gcs

from input_parameters import BUCKET_NAME
from .label_detection import detect_labels
from .face_detection import detect_faces
from .people_detection import detect_people
from .shot_detection import detect_shots
from .text_detection import detect_text
from .logo_detection import detect_logos
from .speech_detection import detect_speech

### REMOVE FOR COLAB - END


def generate_video_annotations(brand_name: str):
    """Generates video annotations for videos in Google Cloud Storage
    Args:
        brand_name: the brand to generate the video annotations for
    """
    # Get videos from GCS
    bucket = get_bucket()
    brand_videos_folder = f"{brand_name}/videos"
    blobs = bucket.list_blobs(prefix=brand_videos_folder)
    # Video processing
    for video in blobs:
        if video.name == f"{brand_videos_folder}/" or "1st_5_secs" in video.name:
            # Skip parent folder and trimmed versions of videos
            continue
        video_name, video_name_with_format = get_file_name_from_gcs_url(video.name)
        video_location = f"gs://{BUCKET_NAME}/{video.name}"
        video_annotations = get_existing_annotations_from_gcs(brand_name)
        # Generate video annotations
        generate_annotations_for_video(
            brand_name,
            video_name,
            video_name_with_format,
            video_location,
            video_annotations,
        )


def generate_annotations_for_video(
    brand_name: str,
    video_name: str,
    video_name_with_format: str,
    video_location: str,
    existing_video_annotations: list[str],
):
    """Generates video annotations only if the video hasn't been processed
    Args:
        brand_name: the brand to generate the video annotations for
        video_name: the name of the video to generate the annotations for
        video_name_with_format: video name and format
        existing_video_annotations: a list of existing annotations to avoid generating
        them for the same video
    """

    # Label Detection
    label_detection_output = (
        f"gs://{BUCKET_NAME}/{brand_name}/annotations/{video_name}/label-detection.json"
    )
    if label_detection_output not in existing_video_annotations:
        detect_labels(video_location, label_detection_output)
    else:
        print(
            f"Label annotations for video {video_name_with_format} already exist, API request skipped.\n"
        )

    # Face Detection
    face_detection_output = (
        f"gs://{BUCKET_NAME}/{brand_name}/annotations/{video_name}/face-detection.json"
    )
    if face_detection_output not in existing_video_annotations:
        detect_faces(video_location, face_detection_output)
    else:
        print(
            f"Face annotations for video {video_name_with_format} already exist, API request skipped.\n"
        )

    # People Detection
    people_detection_output = f"gs://{BUCKET_NAME}/{brand_name}/annotations/{video_name}/people-detection.json"
    if people_detection_output not in existing_video_annotations:
        detect_people(video_location, people_detection_output)
    else:
        print(
            f"People annotations for video {video_name_with_format} already exist, API request skipped.\n"
        )

    # Shot Detection
    shot_detection_output = (
        f"gs://{BUCKET_NAME}/{brand_name}/annotations/{video_name}/shot-detection.json"
    )
    if shot_detection_output not in existing_video_annotations:
        detect_shots(video_location, shot_detection_output)
    else:
        print(
            f"Shot annotations for video {video_name_with_format} already exist, API request skipped.\n"
        )

    # Text Detection
    text_detection_output = (
        f"gs://{BUCKET_NAME}/{brand_name}/annotations/{video_name}/text-detection.json"
    )
    if text_detection_output not in existing_video_annotations:
        detect_text(video_location, text_detection_output)
    else:
        print(
            f"Text annotations for video {video_name_with_format} already exist, API request skipped.\n"
        )

    # Logo Detection
    logo_detection_output = (
        f"gs://{BUCKET_NAME}/{brand_name}/annotations/{video_name}/logo-detection.json"
    )
    if logo_detection_output not in existing_video_annotations:
        detect_logos(video_location, logo_detection_output)
    else:
        print(
            f"Logo annotations for video {video_name_with_format} already exist, API request skipped.\n"
        )

    # Speech Detection
    speech_detection_output = f"gs://{BUCKET_NAME}/{brand_name}/annotations/{video_name}/speech-detection.json"
    if speech_detection_output not in existing_video_annotations:
        detect_speech(video_location, speech_detection_output)
    else:
        print(
            f"Speech annotations for video {video_name_with_format} already exist, API request skipped.\n"
        )
