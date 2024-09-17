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

"""Module to define the prompts that will contain the ABCD features."""

### START FOR COLAB - END

import time
from evaluation_processing.process_evaluations import (
    PromptParams,
    evaluate_abcd_features,
    get_feature_configs,
)
from annotations_evaluation.annotations_generation.annotations_generation import (
    generate_video_annotations,
)
from helpers.generic_helpers import (
    get_bucket,
    get_file_name_from_gcs_url,
    store_assessment_results_locally,
    trim_videos,
    print_abcd_assetssments,
)
from helpers.vertex_ai_service import LLMParameters
from input_parameters import (
    BUCKET_NAME,
    GEMINI_PRO,
    STORE_ASSESSMENT_RESULTS_LOCALLY,
    USE_ANNOTATIONS,
    USE_LLMS,
    VIDEO_SIZE_LIMIT_MB,
    VERBOSE,
    NOT_PROCESSED_VIDEOS,
    brand_name,
    brand_variations,
    branded_call_to_actions,
    branded_products_categories,
    branded_products,
    llm_location,
    llm_generation_config,
)

### REMOVE FOR COLAB - END


def execute_abcd_assessment_for_videos():
    """Execute ABCD Assessment for all brand videos in GCS"""

    prompt_params = PromptParams(
        brand_name,
        brand_variations,
        branded_products,
        branded_products_categories,
        branded_call_to_actions,
    )

    llm_params = LLMParameters(
        model_name=GEMINI_PRO,
        location=llm_location,
        generation_config=llm_generation_config,
    )

    assessment = {
        "brand_name": brand_name,
        "video_assessments": [],
        "prompt_params": prompt_params,
        "llm_params": llm_params,
    }

    # Get videos for ABCD Assessment
    brand_videos_folder = f"{brand_name}/videos"
    bucket = get_bucket()
    blobs = bucket.list_blobs(prefix=brand_videos_folder)
    # Video processing
    for video in blobs:
        if video.name == f"{brand_videos_folder}/" or "1st_5_secs" in video.name:
            # Skip parent folder
            continue
        video_name, video_name_with_format = get_file_name_from_gcs_url(video.name)
        if not video_name or not video_name_with_format:
            print(f"Video name not resolved for {video.name}... Skipping execution. \n")
            continue
        # Check size of video to avoid processing videos > 7MB
        video_metadata = bucket.get_blob(video.name)
        size_mb = video_metadata.size / 1e6
        if USE_LLMS and size_mb > VIDEO_SIZE_LIMIT_MB:
            print(
                f"The size of video {video.name} is greater than {VIDEO_SIZE_LIMIT_MB} MB. Skipping execution. \n"
            )
            continue

        print(f"\n\nProcessing ABCD Assessment for video {video.name}... \n")

        # 3) Execute ABCD Assessment
        video_uri = f"gs://{BUCKET_NAME}/{video.name}"
        evaluated_features = evaluate_abcd_features(
            brand_name, video_name, video_uri, prompt_params, llm_params
        )

        if VERBOSE:
            if len(evaluated_features) != len(get_feature_configs()):
                print(
                    f"WARNING: ABCD Detector was not able to process all the features for video {video_uri}. Please check and execute again."
                )
                NOT_PROCESSED_VIDEOS.append(video_uri)

        # Calculate ABCD final score
        total_features = len(evaluated_features)
        passed_features_count = 0
        for feature in evaluated_features:
            if feature.get("feature_detected"):
                passed_features_count += 1
        # Get score
        score = (passed_features_count * 100) / total_features
        video_assessment = {
            "video_name": video_name_with_format,
            "video_uri": video_uri,
            "features": evaluated_features,
            "passed_features_count": passed_features_count,
            "score": score,
        }
        assessment.get("video_assessments").append(video_assessment)

        # Store brand assessment results locally
        if STORE_ASSESSMENT_RESULTS_LOCALLY:
            store_assessment_results_locally(brand_name, video_assessment)

    return assessment


def main():
    """Main ABCD Assessment execution"""

    start_time = time.time()
    print("Starting ABCD evaluation... \n")

    if USE_ANNOTATIONS:
        generate_video_annotations(brand_name)

    trim_videos(brand_name)

    abcd_assessments = execute_abcd_assessment_for_videos()
    if len(abcd_assessments.get("video_assessments")) == 0:
        print("There are no videos to display.")
        exit()

    # Print ABCD Assessments
    print_abcd_assetssments(brand_name, abcd_assessments)
    print(f"ABCD evaluation took --- {(time.time() - start_time) / 60} mins. ---")


### Main ABCD Assessment execution ###
if __name__ == "__main__":
    main()
