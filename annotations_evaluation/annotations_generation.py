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

from enum import Enum
from google.cloud import videointelligence
from google.cloud.videointelligence import VideoContext
from google.cloud import videointelligence_v1 as videointelligence2
from configuration import Configuration
from helpers.generic_helpers import (
    execute_tasks_in_parallel,
)
from gcp_api_services.gcs_api_service import gcs_api_service


class Annotations(Enum):
  """Annotation types enum"""

  GENERIC_ANNOTATIONS = "generic_annotations"
  FACE_ANNOTATIONS = "face_annotations"
  PEOPLE_ANNOTATIONS = "people_annotations"
  SPEECH_ANNOTATIONS = "speech_annotations"


def standard_annotations_detection(
    video_client: videointelligence.VideoIntelligenceServiceClient,
    video_uri: str,
    annotations_uri: str,
) -> None:
  """Detect the following standard annotations: Text, Shot, Logo and Label"""
  features = [
      videointelligence.Feature.TEXT_DETECTION,
      videointelligence.Feature.SHOT_CHANGE_DETECTION,
      videointelligence.Feature.LOGO_RECOGNITION,
      videointelligence.Feature.LABEL_DETECTION,
  ]
  operation = video_client.annotate_video(
      request={
          "features": features,
          "input_uri": video_uri,
          "output_uri": annotations_uri,
      }
  )
  print(f"\nProcessing video {video_uri} for {str(features)} annotations...")
  operation.result(timeout=800)
  print(
      f"\nFinished processing video {video_uri} for"
      f" {str(features)} annotations...\n"
  )


def custom_annotations_detection(
    video_client: videointelligence.VideoIntelligenceServiceClient,
    context: VideoContext,
    features: list[videointelligence.Feature],
    video_uri: str,
    annotations_uri: str,
) -> None:
  """Detect the following custom annotations: Face, People and Speech"""

  operation = video_client.annotate_video(
      request={
          "features": features,
          "input_uri": video_uri,
          "video_context": context,
          "output_uri": annotations_uri,
      }
  )
  print(f"\nProcessing video {video_uri} for {str(features)} annotations...")
  operation.result(timeout=800)
  print(
      f"\nFinished processing video {video_uri} for"
      f" {str(features)} annotations...\n"
  )


def generate_video_annotations(config: Configuration, video_uri: str) -> None:
  """Generates video annotations for videos in Google Cloud Storage"""

  standard_video_client = videointelligence.VideoIntelligenceServiceClient()
  custom_video_client = videointelligence2.VideoIntelligenceServiceClient()

  # Face Detection
  face_config = videointelligence.FaceDetectionConfig(
      include_bounding_boxes=True, include_attributes=True
  )
  face_context = videointelligence.VideoContext(
      face_detection_config=face_config
  )

  # People Detection
  person_config = videointelligence2.types.PersonDetectionConfig(
      include_bounding_boxes=True,
      include_attributes=True,
      include_pose_landmarks=True,
  )
  person_context = videointelligence2.types.VideoContext(
      person_detection_config=person_config
  )

  # Speech Detection
  speech_config = videointelligence.SpeechTranscriptionConfig(
      language_code="en-US", enable_automatic_punctuation=True
  )
  speech_context = videointelligence.VideoContext(
      speech_transcription_config=speech_config
  )

  # Video annotations processing

  tasks = []
  annotation_uri = gcs_api_service.get_annotation_uri(config, video_uri)

  standard_annotations_uri = (
      f"{annotation_uri}{Annotations.GENERIC_ANNOTATIONS.value}.json"
  )
  standard_annotations_blob = gcs_api_service.get_blob(standard_annotations_uri)
  face_annotations_uri = (
      f"{annotation_uri}{Annotations.FACE_ANNOTATIONS.value}.json"
  )
  face_annotations_blob = gcs_api_service.get_blob(face_annotations_uri)
  people_annotations_uri = (
      f"{annotation_uri}{Annotations.PEOPLE_ANNOTATIONS.value}.json"
  )
  people_annotations_blob = gcs_api_service.get_blob(people_annotations_uri)
  speech_annotations_uri = (
      f"{annotation_uri}{Annotations.SPEECH_ANNOTATIONS.value}.json"
  )
  speech_annotations_blob = gcs_api_service.get_blob(speech_annotations_uri)

  # Detect Standard annotations & Custom annotations
  if not standard_annotations_blob:
    tasks.append(
        lambda: standard_annotations_detection(
            standard_video_client, video_uri, standard_annotations_uri
        ),
    )
  else:
    print(
        f"Text, Shot, Logo and Label annotations for video {video_uri} already"
        " exist, API request skipped.\n"
    )
  if not face_annotations_blob:
    tasks.append(
        lambda: custom_annotations_detection(
            standard_video_client,
            face_context,
            [videointelligence.Feature.FACE_DETECTION],
            video_uri,
            face_annotations_uri,
        )
    )
  else:
    print(
        f"Face annotations for video {video_uri} already exist, API request"
        " skipped.\n"
    )

  if not people_annotations_blob:
    tasks.append(
        lambda: custom_annotations_detection(
            custom_video_client,
            person_context,
            [videointelligence2.Feature.PERSON_DETECTION],
            video_uri,
            people_annotations_uri,
        )
    )
  else:
    print(
        f"People annotations for video {video_uri} already exist, API request"
        " skipped.\n"
    )

  if not speech_annotations_blob:
    tasks.append(
        lambda: custom_annotations_detection(
            standard_video_client,
            speech_context,
            [videointelligence.Feature.SPEECH_TRANSCRIPTION],
            video_uri,
            speech_annotations_uri,
        )
    )
  else:
    print(
        f"Speech annotations for video {video_uri} already exist, API request"
        " skipped.\n"
    )

  # Execute annotations generation tasks only for the ones that haven't been processed.
  execute_tasks_in_parallel(tasks)
