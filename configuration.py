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

"""Module that defines global parameters"""

import os

FFMPEG_BUFFER = "reduced/buffer.mp4"
FFMPEG_BUFFER_REDUCED = "reduced/buffer_reduced.mp4"

if not os.path.exists("reduced"):
    os.makedirs("reduced")


class Configuration:
    """Class that stores all parameters used by ABCD."""

    def __init__(self):
        """Initialize with only the required parameters.

          We set all optional parameter defaults in this class because
          we do not want anyone importing the global constants. Hence
          no global variables for hard coded values by design.
        """
        # set parameters
        self.project_id = "" 
        self.project_zone = "us-central1"
        self.bucket_name = ""
        self.knowledge_graph_api_key = ""
        self.bq_dataset_name = "abcd_detector_ds"
        self.bq_table_name = "abcd_assessments"
        self.assessment_file = ""
        self.use_annotations = True
        self.use_llms = True
        self.verbose = True
        self.annotation_path = ""

        # set videos
        self.video_uris = []

        # set brand
        self.brand_name = ""
        self.brand_variations = []
        self.branded_products = []
        self.branded_products_categories = []
        self.branded_call_to_actions = []

        # set thresholds
        self.early_time_seconds = 5
        self.confidence_threshold = 0.5
        self.face_surface_threshold = 0.15
        self.logo_size_threshold = 3.5
        self.avg_shot_duration_seconds = 2
        self.dynamic_cutoff_ms = 3000

        # set model
        self.llm_name = "gemini-1.5-pro-002"
        self.video_size_limit_mb = 50
        self.max_output_tokens = 8192
        self.temperature = 1
        self.top_p = 0.95
        self.top_k = 32


    def set_parameters(self,
        project_id: str,
        project_zone: str,
        bucket_name: str,
        knowledge_graph_api_key: str,
        bigquery_dataset:str,
        bigquery_table:str,
        assessment_file: str,
        use_annotations: bool,
        use_llms: bool,
        verbose: bool
    ) -> None:
        """Set the required parameters for ABCD to run.
            
          Having a separate method for this allows colab multi cell edits.

        Args:
          project_id: Google Cloud Project ID
          project_zone: Google Cloud Project zone (us-central1 if None)
          bucket_name: Google Cloud Storage Bucket name (not uri) 
          knowledge_graph_api_key: Google Cloud API Key (limit this)
          bigquery_dataset: name of dataset in BigQuery.
          bigquery_table: name of table to append results to in BigQuery.
          assessment_file: If present, results will be written to the file path.
          use_annotations: Use video annotation AI.
          use_llms: Use LLM AI.
          verbose: Turn on extra debug and execution prints.
        """
        self.project_id = project_id
        self.project_zone = project_zone or "us-central1"
        self.bucket_name = bucket_name
        self.knowledge_graph_api_key = knowledge_graph_api_key
        self.bq_dataset_name = bigquery_dataset
        self.bq_table_name = bigquery_table
        self.assessment_file = assessment_file
        self.use_annotations = use_annotations
        self.use_llms = use_llms
        self.verbose = verbose
        self.annotation_path = f"gs://{bucket_name}/ABCD/"


    def set_videos(self, video_uris: list) -> None:
        """Set the videos that will be processed.
            
          Having a separate method for this allows multiple runs.
          We accept a string in case someone passes only one video.

          Args:
            video_uris: a list of Google Cloud Storage URIs for videos or paths.
        """
        if isinstance(video_uris, str):
            self.video_uris = [v.strip() for v in video_uris.split(",")]
        elif isinstance(video_uris, (list, tuple)):
            self.video_uris = video_uris
        else:
            self.video_uris = [video_uris]


    def set_brand(self,
        name: str,
        variations: str,
        products: str,
        products_categories: str,
        call_to_actions: str
    ) -> None:
        """Set brand values to help AI evaluate videos.

          Args:
            name: name of brand featured in video.
            variations: comma delimited variations on the brand name.
            products: comma delimited list of products in the video.
            products_categories: comma delimited list of product types.
            call_to_actions: comma delimited list of actions
        """
        self.brand_name = name
        self.brand_variations = [t.strip() for t in variations.split(",")]
        self.branded_products = [t.strip() for t in products.split(",")]
        self.branded_products_categories = [t.strip() for t in products_categories.split(",")]
        self.branded_call_to_actions = [t.strip() for t in call_to_actions.split(",")]


    def set_annotation(self,
        early_time_seconds: int,
        confidence_threshold: float,
        face_surface_threshold: float,
        logo_size_threshold: float,
        avg_shot_duration_seconds: int,
        dynamic_cutoff_ms: int
    ):
        """Set annotation thresholds to help the AI recognize content.

          Args:
            early_time_seconds: how soon in the video something appears
            confidence_threshold: level of certainty for a positive match
            face_surface_threshold: level of certainty for face detection
            logo_size_threshold: minimal logo size
            avg_shot_duration_seconds: video timing
            dynamic_cutoff_ms: longest clip analyzed
        """
        self.early_time_seconds = early_time_seconds
        self.confidence_threshold = confidence_threshold
        self.face_surface_threshold = face_surface_threshold
        self.logo_size_threshold = logo_size_threshold
        self.avg_shot_duration_seconds = avg_shot_duration_seconds
        self.dynamic_cutoff_ms = dynamic_cutoff_ms

            
    def set_model(self,
        llm_name: str,
        video_size_limit_mb: int,
        max_output_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int
    ):
        """Set LLM model parameters.
        
          Args:
            llm_name: name of LLm model to use
            video_size_limit_mb: largest video file to analyze (limit API costs)
            max_output_tokens: largest response (limit API costs)
            temperature: how creative the model gets
            top_p: how varied the model gets
            top_k: how consistent the model gets
        """
        self.llm_name = llm_name
        self.video_size_limit_mb = video_size_limit_mb
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
