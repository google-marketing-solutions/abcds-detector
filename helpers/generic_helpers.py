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

"""Module to load generic helper functions and BigQuery persistence."""

from concurrent import futures
import dataclasses
import datetime
import json
import logging
import sys
from typing import Any, Callable

from google.cloud import bigquery
import pandas

import configuration
from gcp_api_services import bigquery_api_service
import models


def setup_logger(level: int = logging.INFO) -> logging.Logger:
  """Configures and returns the main application logger.

  Args:
    level: Logging level threshold (default: logging.INFO).

  Returns:
    Configured Logger instance for the application.
  """
  logger = logging.getLogger("abcd_detector")
  logger.setLevel(level)

  if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [ABCD] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

  return logger


logger = setup_logger()


def player(video_url: str) -> None:
  """Placeholder function to test video playback locally or in a notebook.

  Args:
    video_url: URL or URI of the video to play.
  """
  logger.info("Video player target: %s", video_url)


def print_abcd_assessment(
    brand_name: str,
    video_uri: str,
    evaluated_features: list[models.FeatureEvaluation],
    timing_info: dict[str, Any] | None = None,
) -> None:
  """Prints ABCD Assessments in human-readable console format.

  Args:
    brand_name: Evaluated brand name.
    video_uri: URI of the analyzed video.
    evaluated_features: List of feature evaluation results to display.
    timing_info: Optional dictionary containing start_time, end_time, duration.
  """
  print(f"\n***** ABCD Assessment for brand: {brand_name} *****")
  print(f"Asset URI: {video_uri}")
  if timing_info and "start_time" in timing_info and "end_time" in timing_info:
    duration = timing_info.get("duration_seconds", 0.0)
    start_t = timing_info["start_time"]
    end_t = timing_info["end_time"]
    print(
        f"Execution Time: {duration:.2f}s "
        f"(Start: {start_t} | End: {end_t})"
    )
  print()
  print_score_details(evaluated_features)


def print_score_details(
    evaluated_features: list[models.FeatureEvaluation],
) -> None:
  """Prints adherence score and feature pass/fail details.

  Args:
    evaluated_features: List of evaluated features to summarize.
  """
  total_features = len(evaluated_features)
  total_detected = sum(1 for f in evaluated_features if f.is_detected)
  score = calculate_score(evaluated_features)

  print(
      f"Video Adherence Score: {score:.1f}% "
      f"({total_detected}/{total_features} features passed)\n"
  )

  if score >= 80:
    print("Rating: ✅ Excellent\n")
  elif score >= 65:
    print("Rating: ⚠️ Might Improve\n")
  else:
    print("Rating: ❌ Needs Review\n")

  print("Evaluated Features:")
  for eval_feature in evaluated_features:
    icon = "✅" if eval_feature.is_detected else "❌"
    print(f" * {icon} {eval_feature.feature.name}")
    if eval_feature.evidence:
      print(f"     Evidence: {eval_feature.evidence}")
  print("\n")


def calculate_score(
    evaluated_features: list[models.FeatureEvaluation],
) -> float:
  """Calculates ABCD adherence score percentage.

  Args:
    evaluated_features: List of FeatureEvaluation results.

  Returns:
    Percentage of detected features (0.0 to 100.0).
  """
  if not evaluated_features:
    return 0.0
  passed_count = sum(1 for f in evaluated_features if f.is_detected)
  return (passed_count * 100.0) / len(evaluated_features)


def get_table_columns_schema() -> list[dict[str, Any]]:
  """Gets the standardized table columns schema for BigQuery.

  Returns:
    List of dicts defining column names and their BigQuery SqlTypeNames.
  """
  return [
      {
          "column": "execution_timestamp",
          "data_type": bigquery.enums.SqlTypeNames.TIMESTAMP,
      },
      {"column": "brand_name", "data_type": bigquery.enums.SqlTypeNames.STRING},
      {"column": "video_uri", "data_type": bigquery.enums.SqlTypeNames.STRING},
      {"column": "feature_id", "data_type": bigquery.enums.SqlTypeNames.STRING},
      {
          "column": "feature_name",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
      {
          "column": "feature_category",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
      {
          "column": "feature_sub_category",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
      {
          "column": "feature_evaluation_criteria",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
      {
          "column": "is_detected",
          "data_type": bigquery.enums.SqlTypeNames.BOOLEAN,
      },
      {
          "column": "confidence_score",
          "data_type": bigquery.enums.SqlTypeNames.FLOAT,
      },
      {"column": "rationale", "data_type": bigquery.enums.SqlTypeNames.STRING},
      {"column": "evidence", "data_type": bigquery.enums.SqlTypeNames.STRING},
      {"column": "strengths", "data_type": bigquery.enums.SqlTypeNames.STRING},
      {"column": "weaknesses", "data_type": bigquery.enums.SqlTypeNames.STRING},
      {
          "column": "recommended_actions",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
      {
          "column": "first_appearance_timestamp",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
      {
          "column": "feature_density_score",
          "data_type": bigquery.enums.SqlTypeNames.FLOAT,
      },
      {
          "column": "feature_quality_score",
          "data_type": bigquery.enums.SqlTypeNames.FLOAT,
      },
      {
          "column": "feature_specifics",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
      {
          "column": "brand_context",
          "data_type": bigquery.enums.SqlTypeNames.STRING,
      },
  ]


def get_table_schema() -> list[bigquery.SchemaField]:
  """Builds BigQuery SchemaField list for assessments table.

  Returns:
    List of bigquery.SchemaField instances for table creation.
  """
  return [
      bigquery.SchemaField(col["column"], col["data_type"])
      for col in get_table_columns_schema()
  ]


def get_table_columns() -> list[str]:
  """Returns list of column names for assessments table.

  Returns:
    List of string column names.
  """
  return [col["column"] for col in get_table_columns_schema()]


def store_in_bq(
    request: configuration.EvaluationRequest,
    video_assessment: models.VideoAssessment,
) -> None:
  """Stores ABCD assessment results in BigQuery.

  Args:
    request: EvaluationRequest containing GCP and BigQuery configurations.
    video_assessment: VideoAssessment containing evaluation results.
  """
  if not request.bigquery_settings:
    return

  bq_settings = request.bigquery_settings
  bq_service = bigquery_api_service.BigQueryAPIService(bq_settings.project_id)
  bq_service.create_dataset(
      bq_settings.dataset_name, request.gcp_config.location
  )

  now = datetime.datetime.now(datetime.timezone.utc)
  schema = get_table_schema()
  columns = get_table_columns()
  table_name = bq_settings.table_name

  rows = []
  brand_ctx = video_assessment.brand_context or request.brand_context
  brand_ctx_dict = dataclasses.asdict(brand_ctx)
  brand_context_str = json.dumps(brand_ctx_dict)

  for eval_list in video_assessment.slice_evaluations.values():
    for eval_item in eval_list:
      row = {
          "execution_timestamp": now,
          "brand_name": video_assessment.brand_name,
          "video_uri": video_assessment.video_uri,
          "feature_id": eval_item.feature.id,
          "feature_name": eval_item.feature.name,
          "feature_category": (
              eval_item.feature.category.value
              if hasattr(eval_item.feature.category, "value")
              else str(eval_item.feature.category)
          ),
          "feature_sub_category": (
              eval_item.feature.sub_category.value
              if hasattr(eval_item.feature.sub_category, "value")
              else str(eval_item.feature.sub_category)
          ),
          "feature_evaluation_criteria": (
              eval_item.feature.evaluation_criteria
          ),
          "is_detected": eval_item.is_detected,
          "confidence_score": eval_item.confidence_score,
          "rationale": eval_item.rationale,
          "evidence": eval_item.evidence,
          "strengths": eval_item.strengths,
          "weaknesses": eval_item.weaknesses,
          "recommended_actions": eval_item.recommended_actions,
          "first_appearance_timestamp": str(
              eval_item.first_appearance_timestamp or ""
          ),
          "feature_density_score": eval_item.feature_density_score,
          "feature_quality_score": eval_item.feature_quality_score,
          "feature_specifics": json.dumps(eval_item.feature_specifics or {}),
          "brand_context": brand_context_str,
      }
      rows.append(row)

  if rows:
    df = pandas.DataFrame(rows, columns=columns)
    table_created = bq_service.create_table(
        bq_settings.dataset_name, table_name, schema
    )
    if table_created:
      logger.info(
          "Inserting %d rows into BigQuery table '%s'...", len(rows), table_name
      )
      bq_service.load_table_from_dataframe(
          bq_settings.dataset_name,
          table_name,
          df,
          schema,
          "WRITE_APPEND",
      )
    else:
      logger.error(
          "Failed to create or access BigQuery table '%s'.", table_name
      )


def execute_tasks_in_parallel(tasks: list[Callable[[], Any]]) -> list[Any]:
  """Executes a list of callable tasks in parallel using ThreadPoolExecutor.

  Args:
    tasks: List of zero-argument callable tasks to execute.

  Returns:
    List of results returned by each completed task in original order.
  """
  if not tasks:
    return []

  results = []
  max_workers = min(len(tasks), 10)
  with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    task_futures = [executor.submit(task) for task in tasks]
    for task_future in task_futures:
      results.append(task_future.result())
  return results
