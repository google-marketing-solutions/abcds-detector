#!/usr/bin/env python3

"""Service for tracking evaluation confidence and annotation vs LLM agreement (Feature J)"""

import datetime
import logging
import pandas
from google.cloud import bigquery
from gcp_api_services import bigquery_api_service
import models


CALIBRATION_TABLE = "confidence_calibration"


def get_calibration_schema() -> list[bigquery.SchemaField]:
  """Gets the schema for the confidence calibration table in BQ."""
  return [
      bigquery.SchemaField(
          "execution_timestamp", bigquery.enums.SqlTypeNames.TIMESTAMP
      ),
      bigquery.SchemaField(
          "video_uri", bigquery.enums.SqlTypeNames.STRING
      ),
      bigquery.SchemaField(
          "feature_id", bigquery.enums.SqlTypeNames.STRING
      ),
      bigquery.SchemaField(
          "feature_name", bigquery.enums.SqlTypeNames.STRING
      ),
      bigquery.SchemaField(
          "evaluation_method", bigquery.enums.SqlTypeNames.STRING
      ),
      bigquery.SchemaField(
          "llm_detected", bigquery.enums.SqlTypeNames.BOOLEAN
      ),
      bigquery.SchemaField(
          "llm_confidence", bigquery.enums.SqlTypeNames.FLOAT64
      ),
      bigquery.SchemaField(
          "annotation_detected", bigquery.enums.SqlTypeNames.BOOLEAN
      ),
      bigquery.SchemaField(
          "agreement", bigquery.enums.SqlTypeNames.BOOLEAN
      ),
      bigquery.SchemaField(
          "human_override", bigquery.enums.SqlTypeNames.BOOLEAN
      ),
      bigquery.SchemaField(
          "human_override_value", bigquery.enums.SqlTypeNames.BOOLEAN
      ),
  ]


def log_evaluation_confidence(
    project_id: str,
    dataset_name: str,
    video_uri: str,
    feature_evaluations: list[models.FeatureEvaluation],
) -> None:
  """Log confidence data for each evaluated feature to BQ for calibration tracking."""
  if not dataset_name:
    return

  try:
    bq_service = bigquery_api_service.BigQueryAPIService(project_id)
    rows = []

    for eval_feature in feature_evaluations:
      row = {
          "execution_timestamp": datetime.datetime.now(),
          "video_uri": video_uri,
          "feature_id": eval_feature.feature.id,
          "feature_name": eval_feature.feature.name,
          "evaluation_method": eval_feature.feature.evaluation_method.value,
          "llm_detected": eval_feature.detected,
          "llm_confidence": eval_feature.confidence_score or 0.0,
          "annotation_detected": None,
          "agreement": None,
          "human_override": False,
          "human_override_value": None,
      }
      rows.append(row)

    if rows:
      schema = get_calibration_schema()
      columns = [field.name for field in schema]
      dataframe = pandas.DataFrame(rows, columns=columns)

      bq_service.create_dataset(dataset_name, "us-central1")
      bq_service.create_table(dataset_name, CALIBRATION_TABLE, schema)
      bq_service.load_table_from_dataframe(
          dataset_name,
          CALIBRATION_TABLE,
          dataframe,
          schema,
          "WRITE_APPEND",
      )
      logging.info(
          "Logged %d confidence calibration rows to %s.%s",
          len(rows),
          dataset_name,
          CALIBRATION_TABLE,
      )
  except Exception as ex:
    logging.warning("Failed to log confidence calibration data: %s", ex)
