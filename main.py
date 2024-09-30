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

"""Module to execute the ABCD Detector Assessment"""

import json
import time
from annotations_evaluation.annotations_generation import generate_video_annotations
from annotations_evaluation.evaluation import evaluate_abcd_features_using_annotations
from llms_evaluation.evaluation import evaluate_abcd_features_using_llms
from feature_configs.features import get_feature_configs
from prompts.prompts_generator import PromptParams
from helpers.generic_helpers import (
    expand_uris,
    get_blob,
    print_abcd_assessment,
    trim_video,
    store_in_bq,
    remove_local_video_files
)
from helpers.vertex_ai_service import LLMParameters
from helpers.bq_service import BigQueryService
from input_parameters import (
    PROJECT_ID,
    ASSESSMENT_FILE,
    LLM_NAME,
    USE_ANNOTATIONS,
    USE_LLMS,
    VERBOSE,
    VIDEO_SIZE_LIMIT_MB,
    VIDEO_URIS,
    STORE_IN_BQ,
    brand_name,
    brand_variations,
    branded_call_to_actions,
    branded_products,
    branded_products_categories,
    llm_generation_config,
    llm_location,
)


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
        model_name=LLM_NAME,
        location=llm_location,
        generation_config=llm_generation_config,
    )

    if STORE_IN_BQ:
        bq_service = BigQueryService(PROJECT_ID)

    brand_assessment = {
        "brand_name": brand_name,
        "video_assessments": [],
        "prompt_params": prompt_params.__dict__,
        "llm_params": llm_params.__dict__,
    }

    video_uris = expand_uris(VIDEO_URIS)

    for video_uri in video_uris:
        print(f"\n\nProcessing ABCD Assessment for video {video_uri}... \n")

        # 1) Prepare video
        trim_video(video_uri)

        # Check size of video to avoid processing videos > 7MB
        video_metadata = get_blob(video_uri)
        size_mb = video_metadata.size / 1e6
        if USE_LLMS and size_mb > VIDEO_SIZE_LIMIT_MB:
            print(
                f"The size of video {video_uri} is greater than {VIDEO_SIZE_LIMIT_MB} MB. Skipping execution."
            )
            continue

        # 3) Execute ABCD Assessment
        video_assessment = {
            "video_uri": video_uri,
        }

        if USE_ANNOTATIONS:
            generate_video_annotations(video_uri)
            annotations_evaluated_features = evaluate_abcd_features_using_annotations(
                video_uri
            )
            video_assessment["annotations_evaluation"] = {
                "evaluated_features": annotations_evaluated_features,
            }

        if USE_LLMS:
            llm_evaluated_features = evaluate_abcd_features_using_llms(
                video_uri, prompt_params, llm_params
            )
            video_assessment["llms_evaluation"] = {
                "evaluated_features": llm_evaluated_features,
            }

            if VERBOSE:
                if len(llm_evaluated_features) < len(get_feature_configs()):
                    print(
                        f"WARNING: ABCD Detector was not able to process all the features for video {video_uri}. Please check and execute again. \n"
                    )
                if len(llm_evaluated_features) > len(get_feature_configs()):
                    print(
                        f"WARNING: ABCD Detector processed more features than the original number features. \
                    Processed features: {len(llm_evaluated_features)} - Original features: {len(get_feature_configs())}"
                    )

        print_abcd_assessment(brand_name, video_assessment)
        brand_assessment.get("video_assessments").append(video_assessment)
        if STORE_IN_BQ:
            store_in_bq(bq_service, video_assessment, prompt_params, llm_params)
        # Remove local version of video files
        remove_local_video_files()

    if ASSESSMENT_FILE:
        with open(ASSESSMENT_FILE, "w", encoding="utf-8") as f:
            json.dump(brand_assessment, f, ensure_ascii=False, indent=4)

    return brand_assessment


def execute_abcd_detector():
    """Main ABCD Assessment execution"""

    start_time = time.time()
    print("Starting ABCD assessment... \n")

    if VIDEO_URIS:
        execute_abcd_assessment_for_videos()
        print("Finished ABCD assessment. \n")
    else:
        print("There are no videos to process. \n")

    print(f"ABCD assessment took --- {(time.time() - start_time) / 60} mins. --- \n")


if __name__ == "__main__":
    execute_abcd_detector()
