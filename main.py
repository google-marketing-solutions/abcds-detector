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
from configuration import Configuration
from utils import parse_args, build_abcd_params_config


def execute_abcd_assessment_for_videos(config: Configuration):
  """Execute ABCD Assessment for all brand videos in GCS"""

  prompt_params = PromptParams(
      config.brand_name,
      config.brand_variations,
      config.branded_products,
      config.branded_products_categories,
      config.branded_call_to_actions,
  )

  llm_params = LLMParameters(
      model_name=config.llm_name,
      location=config.project_zone,
      generation_config={
          "max_output_tokens": config.max_output_tokens,
          "temperature": config.temperature,
          "top_p": config.top_p,
          "top_k": config.top_k,
      }
  )

  brand_assessment = {
      "brand_name": config.brand_name,
      "video_assessments": [],
      "prompt_params": prompt_params.__dict__,
      "llm_params": llm_params.__dict__,
  }

  video_uris = expand_uris(config.video_uris)

  for video_uri in video_uris:
    print(f"\n\nProcessing ABCD Assessment for video {video_uri}... \n")

      # 1) Prepare video
    trim_video(config, video_uri)

    # Check size of video to avoid processing videos > 7MB
    video_metadata = get_blob(video_uri)
    size_mb = video_metadata.size / 1e6
    if config.use_llms and size_mb > config.video_size_limit_mb:
      print(
          f"The size of video {video_uri} is greater than {config.video_size_limit_mb} MB. Skipping execution."
      )
      continue

    # 3) Execute ABCD Assessment
    video_assessment = {
        "video_uri": video_uri,
    }

    if config.use_annotations:
      generate_video_annotations(config, video_uri)
      annotations_evaluated_features = evaluate_abcd_features_using_annotations(
          config,
          video_uri
      )
      video_assessment["annotations_evaluation"] = {
          "evaluated_features": annotations_evaluated_features,
      }

    if config.use_llms:
      llm_evaluated_features = evaluate_abcd_features_using_llms(
        config, video_uri, prompt_params, llm_params
      )
      video_assessment["llms_evaluation"] = {
        "evaluated_features": llm_evaluated_features,
      }

      if config.verbose:
        if len(llm_evaluated_features) < len(get_feature_configs()):
          print(
            f"WARNING: ABCD Detector was not able to process all the features for video {video_uri}. Please check and execute again. \n"
          )
        if len(llm_evaluated_features) > len(get_feature_configs()):
          print(
            f"WARNING: ABCD Detector processed more features than the original number features. \
            Processed features: {len(llm_evaluated_features)} - Original features: {len(get_feature_configs())}"
          )

    print_abcd_assessment(config.brand_name, video_assessment)
    brand_assessment.get("video_assessments").append(video_assessment)

    if config.bq_table_name:
      bq_service = BigQueryService(config.project_id)
      store_in_bq(config, bq_service, video_assessment, prompt_params, llm_params)

    # Remove local version of video files
    remove_local_video_files()

  if config.assessment_file:
    with open(config.assessment_file, "w", encoding="utf-8") as f:
      json.dump(brand_assessment, f, ensure_ascii=False, indent=4)

  return brand_assessment


def main(arg_list: list[str] | None = None) -> None:
  """Main ABCD Assessment execution. See docstring and args.

  Args:
    arg_list: A list of command line arguments

  """

  args = parse_args(arg_list)

  config = build_abcd_params_config(args)

  start_time = time.time()
  print("Starting ABCD assessment... \n")

  if config.video_uris:
    execute_abcd_assessment_for_videos(config)
    print("Finished ABCD assessment. \n")
  else:
    print("There are no videos to process. \n")

  print(f"ABCD assessment took - {(time.time() - start_time) / 60} mins. - \n")


if __name__ == "__main__":
  main()

