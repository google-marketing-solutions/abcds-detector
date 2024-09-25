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

"""Face Detection: Function definition to detect faces in a video"""

from google.cloud import videointelligence

def detect_faces(input_gs_file_name: str, output_gs_file_name: str) -> None:
    """Detects faces in a video.
    Args:
      input_gs_file_name: gcs bucket where the video is located
      output_gs_file_name: gcs bucket output for the video annotations
    """

    video_client = videointelligence.VideoIntelligenceServiceClient()

    # Configure the request
    config = videointelligence.FaceDetectionConfig(
        include_bounding_boxes=True, include_attributes=True
    )
    context = videointelligence.VideoContext(face_detection_config=config)

    # Start the asynchronous request
    operation = video_client.annotate_video(
        request={
            "features": [videointelligence.Feature.FACE_DETECTION],
            "input_uri": input_gs_file_name,
            "output_uri": output_gs_file_name,
            "video_context": context,
        }
    )

    print(f"\nProcessing video {input_gs_file_name} for face annotations...")

    result = operation.result(timeout=800)

    print(f"\nFinished processing video {input_gs_file_name} for face annotations...\n")
