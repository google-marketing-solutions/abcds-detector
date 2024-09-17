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

"""Logo Detection: Function definition to detect logos in a video"""

### REMOVE FOR COLAB - START
from google.cloud import videointelligence

### REMOVE FOR COLAB - END


def detect_logos(input_gs_file_name: str, output_gs_file_name: str) -> None:
    """Detect logos in a video.
    Args:
      input_gs_file_name: gcs bucket where the video is located
      output_gs_file_name: gcs bucket output for the video annotations
    """
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.Feature.LOGO_RECOGNITION]

    operation = video_client.annotate_video(
        request={
            "features": features,
            "input_uri": input_gs_file_name,
            "output_uri": output_gs_file_name,
        }
    )

    print(f"\nProcessing video {input_gs_file_name} for logo annotations...")

    response = operation.result(timeout=800)

    print(f"\nFinished processing video {input_gs_file_name} for logo annotations...\n")
