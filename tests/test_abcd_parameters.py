#!/usr/bin/env python3

###########################################################################
#
#    Copyright 2024 Google LLC
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#            https://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
###########################################################################

"""Module to test ABCD parameters"""

from utils import build_abcd_params_config
from dataclasses import dataclass


@dataclass
class ArgsMock:
  """Mock class to define params"""

  project_id: str
  project_zone: str
  bucket_name: str
  knowledge_graph_api_key: str
  bigquery_dataset: str
  bigquery_table: str
  assessment_file: str
  use_annotations: str
  use_llms: bool
  verbose: bool
  annotation_path: str
  # set videos
  video_uris: str
  # set brand
  brand_name: str
  brand_variations: list[str]
  branded_products: list[str]
  branded_products_categories: list[str]
  branded_call_to_actions: list[str]
  # set thresholds
  early_time_seconds: float
  confidence_threshold: float
  face_surface_threshold: float
  logo_size_threshold: float
  avg_shot_duration_seconds: float
  dynamic_cutoff_ms: float
  # set model
  llm_name: str
  video_size_limit_mb: int
  max_output_tokens: int
  temperature: float
  top_p: float
  top_k: float


def test_not_empty_abcd_params():
  """Tests that all brand parameters are provided"""

  args = ArgsMock(
      project_id="tighlock-test",
      project_zone="us-central1",
      bucket_name="abcd-detector-input",
      knowledge_graph_api_key="asdfds",
      bigquery_dataset="abcd_detector_ds",
      bigquery_table="my_table",
      assessment_file="",
      use_annotations=True,
      use_llms=True,
      verbose=True,
      annotation_path="",
      video_uris="gs://abcd-detector-input/Google/videos/",
      brand_name="Google",
      brand_variations="Google,google",
      branded_products="Google pixel, Google pixel buds, Google pixel watch",
      branded_products_categories="phone, watch, buds",
      branded_call_to_actions="buy it!, buy",
      early_time_seconds=5,
      confidence_threshold=0.5,
      face_surface_threshold=0.5,
      logo_size_threshold=0.5,
      avg_shot_duration_seconds=3,
      dynamic_cutoff_ms=3000,
      llm_name="gemini-1.5-pro-002",
      top_p=0.1,
      video_size_limit_mb=50,
      max_output_tokens=8000,
      temperature=1,
      top_k=0.1,
  )

  config = build_abcd_params_config(args)

  assert config.project_id is not None
  assert config.project_zone is not None
  assert config.bucket_name is not None
  assert config.knowledge_graph_api_key is not None
  assert config.bq_dataset_name is not None
  assert config.bq_table_name is not None
  assert config.assessment_file == ""
  assert config.use_annotations is not None
  assert config.use_llms is not None
  assert config.verbose is not None
  assert config.annotation_path is not None

  # set videos
  assert config.video_uris is not None

  # set brand
  assert config.brand_name is not None
  assert (
      config.brand_variations is not None and len(config.brand_variations) > 0
  )
  assert (
      config.branded_products is not None and len(config.branded_products) > 0
  )
  assert (
      config.branded_products_categories is not None
      and len(config.branded_products_categories) > 0
  )
  assert (
      config.branded_call_to_actions is not None
      and len(config.branded_call_to_actions) > 0
  )

  # set thresholds
  assert config.early_time_seconds is not None
  assert config.confidence_threshold is not None
  assert config.face_surface_threshold is not None
  assert config.logo_size_threshold is not None
  assert config.avg_shot_duration_seconds is not None
  assert config.dynamic_cutoff_ms is not None

  # set model
  assert config.llm_name is not None
  assert config.video_size_limit_mb is not None
  assert config.max_output_tokens is not None
  assert config.temperature is not None
  assert config.top_p is not None
  assert config.top_k is not None
