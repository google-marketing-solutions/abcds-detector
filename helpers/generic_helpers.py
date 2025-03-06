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

"""Module to load generic helper functions"""

import json
import os
import urllib
import datetime
from concurrent.futures import ThreadPoolExecutor
import pandas
import logging
from google.cloud import bigquery
from google.cloud import storage
from moviepy.editor import VideoFileClip
from helpers.bq_service import BigQueryService
from feature_configs.features import get_feature_configs
from configuration import FFMPEG_BUFFER, FFMPEG_BUFFER_REDUCED, Configuration


def get_blob(uri: str) -> any:
    """Return GCS blob object from full uri."""
    bucket, path = uri.replace("gs://", "").split("/", 1)
    return storage.Client().get_bucket(bucket).get_blob(path)


def upload_blob(uri: str, file_path: str) -> any:
    """Uploads GCS blob object from file."""
    bucket, path = uri.replace("gs://", "").split("/", 1)
    storage.Client().get_bucket(bucket).blob(path).upload_from_filename(file_path)


def load_blob(annotation_uri: str):
    """Loads a blob to json"""
    blob = get_blob(annotation_uri)
    blob_json = json.loads(blob.download_as_string()).get("annotation_results")[0]
    return blob_json


def expand_uris(uris: list) -> any:
    """Expands any GCS URI entry that is a folder path into its files."""
    for uri in uris:
        if uri.endswith("/"):
            print(f"EXPANDING URI: {uri} \n")
            bucket, prefix = uri.replace("gs://", "").split("/", 1)
            for blob in (
                storage.Client()
                .get_bucket(bucket)
                .list_blobs(prefix=prefix, delimiter="/")
            ):
                if not blob.name.endswith("/"):
                    yield f"gs://{bucket}/{blob.name}"
        else:
            yield uri


def get_annotation_uri(config: Configuration, video_uri: str) -> str:
    """Helper to translate video to annotation uri."""
    return video_uri.replace("gs://", config.annotation_path).replace(".", "_") + "/"


def get_reduced_uri(config: Configuration, video_uri: str) -> str:
    """Helper to translate video to reduced video uri."""
    return get_annotation_uri(config, video_uri) + "reduced_1st_5_secs.mp4"


def get_knowledge_graph_entities(config: Configuration, queries: list[str]) -> dict[str, dict]:
    """Get the knowledge Graph Entities for a list of queries
    Args:
        config: All the parameters
        queries: a list of entities to find in KG
    Returns:
        kg_entities: entities found in KG
        Format example: entity id is the key and entity details the value
        kg_entities = {
            "mcy/12": {} TODO (ae) add here
        }
    """
    kg_entities = {}
    try:
        for query in queries:
            service_url = "https://kgsearch.googleapis.com/v1/entities:search"
            params = {
                "query": query,
                "limit": 10,
                "indent": True,
                "key": config.knowledge_graph_api_key,
            }
            url = f"{service_url}?{urllib.parse.urlencode(params)}"
            response = json.loads(urllib.request.urlopen(url).read())
            for element in response["itemListElement"]:
                kg_entity_name = element["result"]["name"]
                # To only add the exact KG entity
                if query.lower() == kg_entity_name.lower():
                    kg_entities[element["result"]["@id"][3:]] = element["result"]
        return kg_entities
    except Exception as ex:
        print(
            f"\n\x1b[31mERROR: There was an error fetching the Knowledge Graph entities. Please check that your API key is correct. ERROR: {ex}\x1b[0m"
        )
        raise


def remove_local_video_files():
    """Removes local video files"""
    if os.path.exists(FFMPEG_BUFFER):
        os.remove(FFMPEG_BUFFER)
    if os.path.exists(FFMPEG_BUFFER_REDUCED):
        os.remove(FFMPEG_BUFFER_REDUCED)


def trim_video(config: Configuration, video_uri: str):
    """Trims videos to create new versions of 5 secs
    Args:
        config: all the parameters
        video_uri: the video to trim the length for
    """
    reduced_uri = get_reduced_uri(config, video_uri)
    reduced_blob = get_blob(reduced_uri)
    print(f"REDUCED: {reduced_uri} \n")
    if reduced_blob is None:
        print(f"Shortening video {video_uri}. \n")

        # download
        with open(FFMPEG_BUFFER, "wb") as f:
            blob = get_blob(video_uri)
            if blob:
                f.write(blob.download_as_string(client=None))
            else:
                msg = f"Video URI: {video_uri} does not exist. Skipping execution."
                logging.error(msg)
                raise Exception(msg)

        # trim
        clip = VideoFileClip(FFMPEG_BUFFER)
        clip = clip.subclip(0, 5)
        clip.write_videofile(FFMPEG_BUFFER_REDUCED)

        # upload
        upload_blob(reduced_uri, FFMPEG_BUFFER_REDUCED)

    else:
        print(f"Video {video_uri} has already been trimmed. Skipping...\n")


def player(video_url: str):
    """Placeholder function to test locally"""
    print(f"{video_url} \n")


def print_abcd_assessment(brand_name: str, video_assessment: dict) -> None:
    """Print ABCD Assessments"""
    bucket_name, path = (
        video_assessment.get("video_uri").replace("gs://", "").split("/", 1)
    )
    video_url = f"/content/{bucket_name}/{path}"
    # Play Video
    player(video_url)
    print(f"***** ABCD Assessment for brand {brand_name} ***** \n")
    print(f"Asset name: {video_assessment.get('video_uri')} \n")

    # Get ABCD evaluations
    if video_assessment.get("annotations_evaluation"):
        print("***** ABCD Assessment using Annotations ***** \n")
        print_score_details(video_assessment.get("annotations_evaluation"))
    else:
        print("No annotations_evaluation found. Skipping from priting. \n")

    if video_assessment.get("llms_evaluation"):
        print("***** ABCD Assessment using LLMs ***** \n")
        print_score_details(video_assessment.get("llms_evaluation"))
    else:
        print("No llms_evaluation found. Skipping from priting. \n")


def print_score_details(abcd_eval: dict) -> None:
    """Print score details"""
    total_features = len(abcd_eval.get("evaluated_features"))
    total_features_detected = len(
        [
            feature
            for feature in abcd_eval.get("evaluated_features")
            if feature.get("detected")
        ]
    )
    score = calculate_score(abcd_eval.get("evaluated_features"))
    print(
        f"Video score: {round(score, 2)}%, adherence ({total_features_detected}/{total_features})\n"
    )
    if score >= 80:
        print("Asset result: ✅ Excellent \n")
    elif score >= 65 and score < 80:
        print("Asset result: ⚠ Might Improve \n")
    else:
        print("Asset result: ❌ Needs Review \n")

    print("Evaluated Features: \n")
    for feature in abcd_eval.get("evaluated_features"):
        if feature.get("detected"):
            print(f' * ✅ {feature.get("name")}')
        else:
            print(f' * ❌ {feature.get("name")}')
    print("\n")


def get_call_to_action_api_list() -> list[str]:
    """Gets a list of call to actions

    Returns
        list: call to actions
    """
    return [
        "LEARN MORE",
        "GET QUOTE",
        "APPLY NOW",
        "SIGN UP",
        "CONTACT US",
        "SUBSCRIBE",
        "DOWNLOAD",
        "BOOK NOW",
        "SHOP NOW",
        "BUY NOW",
        "DONATE NOW",
        "ORDER NOW",
        "PLAY NOW",
        "SEE MORE",
        "START NOW",
        "VISIT SITE",
        "WATCH NOW",
    ]


def get_call_to_action_verbs_api_list() -> list[str]:
    """Gets a list of call to action verbs

    Returns
        list: call to action verbs
    """
    return [
        "LEARN",
        "QUOTE",
        "APPLY",
        "SIGN UP",
        "CONTACT",
        "SUBSCRIBE",
        "DOWNLOAD",
        "BOOK",
        "SHOP",
        "BUY",
        "DONATE",
        "ORDER",
        "PLAY",
        "SEE",
        "START",
        "VISIT",
        "WATCH",
    ]


def execute_tasks_in_parallel(tasks: list[any]) -> None:
    """Executes a list of tasks in parallel"""
    results = []
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            results.append(running_task.result())
    return results


def calculate_score(evaluated_features: list[str]) -> float:
    """Calculate ABCD final score"""
    total_features = len(evaluated_features)
    passed_features_count = 0
    for feature in evaluated_features:
        if feature.get("detected"):
            passed_features_count += 1
    # Get score
    score = (
        ((passed_features_count * 100) / total_features) if total_features > 0 else 0
    )
    return score


def get_video_name_from_uri(uri: str):
    """Gets the video name from the video uri"""
    video_parts = uri.split("/")
    if len(video_parts) > 0:
        # Video name is the last element
        return video_parts[-1]
    return ""


def get_feature_by_id(features: list[dict], feature_id: str) -> list[str]:
    """Get feature configs by id"""
    features_found = [
        feature_config
        for feature_config in features
        if feature_config.get("feature_id") == feature_id
    ]
    if len(features_found) > 0:
        return features_found[0]
    return None


def get_table_columns_schema() -> list[str]:
    """Gets the table columns schema for the assessments table in BQ."""
    return [
        {
            "column": "execution_timestamp",
            "data_type": bigquery.enums.SqlTypeNames.TIMESTAMP,
        },
        {"column": "brand_name", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "video_id", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "video_name", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "video_uri", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "feature_id", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "feature_name", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "feature_category", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "feature_criteria", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {
            "column": "using_annotations",
            "data_type": bigquery.enums.SqlTypeNames.BOOLEAN,
        },
        {
            "column": "annotations_evaluation",
            "data_type": bigquery.enums.SqlTypeNames.BOOLEAN,
        },
        {"column": "using_llms", "data_type": bigquery.enums.SqlTypeNames.BOOLEAN},
        {"column": "llms_evaluation", "data_type": bigquery.enums.SqlTypeNames.BOOLEAN},
        {"column": "llm_explanation", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "prompt_params", "data_type": bigquery.enums.SqlTypeNames.STRING},
        {"column": "llm_params", "data_type": bigquery.enums.SqlTypeNames.STRING},
    ]


def get_table_columns() -> list[str]:
    """Gets the table columns for the assessments table in BQ."""
    columns = []
    for column_schema in get_table_columns_schema():
        columns.append(column_schema.get("column"))
    return columns


def get_table_schema() -> list[bigquery.SchemaField]:
    """Gets the schema for the assessments table in BQ."""
    schema = []
    for column_schema in get_table_columns_schema():
        schema.append(
            bigquery.SchemaField(
                column_schema.get("column"), column_schema.get("data_type")
            )
        )
    return schema


def build_features_for_bq(video_uri: str, brand_name: str) -> list[dict]:
    """Builds features schema with values and default values for table in BQ"""
    assessment_bq = []
    feature_configs = get_feature_configs()
    # Insert all feature configs first
    for f_config in feature_configs:
        assessment_bq.append(
            {
                "execution_timestamp": datetime.datetime.now(),
                "brand_name": brand_name,
                "video_id": video_uri,
                "video_name": get_video_name_from_uri(video_uri),
                "video_uri": video_uri,
                "feature_id": f_config.get("id"),
                "feature_name": f_config.get("name"),
                "feature_category": f_config.get("category"),
                "feature_criteria": f_config.get("criteria"),
                "using_annotations": False,  # Default value to build a correct schema from the beginning
                "annotations_evaluation": False,  # Default value to build a correct schema from the beginning
                "using_llms": False,  # Default value to build a correct schema from the beginning
                "llms_evaluation": False,  # Default value to build a correct schema from the beginning
                "llm_explanation": "",  # Default value to build a correct schema from the beginning
                "prompt_params": "",  # Default value to build a correct schema from the beginning
                "llm_params": "",  # Default value to build a correct schema from the beginning
            }
        )
    return assessment_bq


def update_annotations_evaluated_features(
    assessment_bq: list[dict], annotations_evaluation: list[dict]
) -> None:
    """Updates default values with annotations evaluated features values
    Finds the feature in assessment_bq and updates with annotations evaluation
    """
    if annotations_evaluation:
        for annotations_eval_feature in annotations_evaluation.get(
            "evaluated_features"
        ):
            feature_found = get_feature_by_id(
                assessment_bq, annotations_eval_feature.get("id")
            )
            if feature_found:
                feature_found["using_annotations"] = True
                feature_found["annotations_evaluation"] = annotations_eval_feature.get(
                    "detected"
                )
            else:
                print(
                    f"Annotations evaluation: Feature {annotations_eval_feature.get('id')} not found. Skipping from storing it in BQ. \n"
                )
    else:
        print("No annotations_evaluation found. Skipping from storing it in BQ. \n")


def update_llms_evaluated_features(
    assessment_bq: list[dict],
    llms_evaluation: list[dict],
    prompt_params: dict,
    llm_params: dict,
) -> None:
    """Updates default values with llms evaluated features values
    Finds the feature in assessment_bq and updates with llms evaluation
    """
    if llms_evaluation:
        for llms_eval_feature in llms_evaluation.get("evaluated_features"):
            feature_found = get_feature_by_id(
                assessment_bq, llms_eval_feature.get("id")
            )

            if feature_found:
                feature_found["using_llms"] = True
                feature_found["llms_evaluation"] = llms_eval_feature.get("detected")
                feature_found["llm_explanation"] = llms_eval_feature.get(
                    "llm_explanation"
                )
                feature_found["prompt_params"] = str(prompt_params)
                feature_found["llm_params"] = str(llm_params)
            else:
                print(
                    f"LLMs evaluation: Feature {llms_eval_feature.get('id')} not found. Skipping from storing it in BQ. \n"
                )
    else:
        print("No llms_evaluation found. Skipping from storing it in BQ. \n")


def store_in_bq(
    config: Configuration,
    bq_service: BigQueryService,
    video_assessment: dict,
    prompt_params: any,
    llm_params: any,
):
    """Store ABCD assessment results in BQ"""

    print(
        f"Storing ABCD assessment for video {video_assessment.get('video_uri')} in BigQuery... \n"
    )

    assessment_bq = build_features_for_bq(
        video_assessment.get("video_uri"), prompt_params.brand_name
    )

    annotations_evaluation = video_assessment.get("annotations_evaluation")
    update_annotations_evaluated_features(assessment_bq, annotations_evaluation)

    llms_evaluation = video_assessment.get("llms_evaluation")
    update_llms_evaluated_features(
        assessment_bq, llms_evaluation, prompt_params.__dict__, llm_params.__dict__
    )

    # Insert if there is any feature evaluation
    if (annotations_evaluation or llms_evaluation) and len(assessment_bq) > 0:
        columns = get_table_columns()
        dataframe = pandas.DataFrame(
            assessment_bq,
            # In the loaded table, the column order reflects the order of the
            # columns in the DataFrame.
            columns=columns,
        )
        # Create dataset if it does not exist
        bq_service.create_dataset(config.bq_dataset_name, config.project_zone)
        schema = get_table_schema()
        table_created = bq_service.create_table(config.bq_dataset_name, config.bq_table_name, schema)
        # Wait for table creation
        if table_created:
            print(f"Inserting {len(assessment_bq)} rows into BQ... \n")
            bq_service.load_table_from_dataframe(
                config.bq_dataset_name, config.bq_table_name, dataframe, schema, "WRITE_APPEND"
            )
        else:
            print(
                f"Error: ABCD assessments not loaded to table {config.bq_dataset_name}.{config.bq_table_name} because the table could not be created. \n"
            )
    else:
        print(
            f"There are no rows to insert into BQ for video {video_assessment.get('video_uri')}. \n"
        )
