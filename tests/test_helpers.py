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

"""Tests for ABCD generic helpers, BigQuery schemas, and data persistence."""

import json
import unittest
from unittest import mock

import configuration
from helpers import generic_helpers
import models


class TestHelpers(unittest.TestCase):
  """Tests for BigQuery schemas, tables, and storage helpers."""

  def test_generic_helpers_unified_table_schema(self) -> None:
    """Tests that BigQuery schema defines the 20-column schema."""
    columns = generic_helpers.get_table_columns()
    self.assertEqual(len(columns), 20)

    expected_cols = [
        "execution_timestamp",
        "brand_name",
        "video_uri",
        "feature_id",
        "feature_name",
        "feature_category",
        "feature_sub_category",
        "feature_evaluation_criteria",
        "is_detected",
        "confidence_score",
        "rationale",
        "evidence",
        "strengths",
        "weaknesses",
        "recommended_actions",
        "first_appearance_timestamp",
        "feature_density_score",
        "feature_quality_score",
        "feature_specifics",
        "brand_context",
    ]
    self.assertEqual(columns, expected_cols)

    table_schema = generic_helpers.get_table_schema()
    self.assertEqual(len(table_schema), 20)
    schema_names = [f.name for f in table_schema]
    self.assertEqual(schema_names, expected_cols)

  @mock.patch("gcp_api_services.bigquery_api_service.BigQueryAPIService")
  def test_store_in_bq_unified_rows(
      self, mock_bq_class: mock.MagicMock
  ) -> None:
    """Tests that store_in_bq outputs the identical 20-column schema."""
    mock_service = mock.MagicMock()
    mock_service.create_table.return_value = True
    mock_bq_class.return_value = mock_service

    req = configuration.EvaluationRequest(
        video_uris=["gs://bucket/test.mp4"],
        gcp_config=configuration.GCPConfig(project_id="test-proj"),
        gemini_config=configuration.GeminiConfig(api_key="test-key"),
        bigquery_settings=configuration.BigQuerySettings(
            project_id="test-proj",
            dataset_name="test_dataset",
            table_name="test_table",
        ),
    )

    feature_u = models.VideoFeature(
        id="f_univ",
        name="Universal Feature",
        category=models.VideoFeatureCategory.UNIVERSAL,
        sub_category=models.VideoFeatureSubCategory.ATTRACT,
        evaluation_criteria="Test criteria",
    )
    feature_s = models.VideoFeature(
        id="f_short",
        name="Shorts Feature",
        category=models.VideoFeatureCategory.SHORTS,
        sub_category=models.VideoFeatureSubCategory.BRAND,
        evaluation_criteria="Test shorts criteria",
    )

    eval_u = models.FeatureEvaluation(
        feature=feature_u,
        is_detected=True,
        confidence_score=0.9,
        rationale="Univ rationale",
        evidence="Univ evidence",
        strengths="Univ strengths",
        weaknesses="Univ weaknesses",
        recommended_actions="Univ actions",
    )
    eval_s = models.FeatureEvaluation(
        feature=feature_s,
        is_detected=False,
        confidence_score=0.3,
        rationale="Shorts rationale",
        evidence="Shorts evidence",
        strengths="Shorts strengths",
        weaknesses="Shorts weaknesses",
        recommended_actions="Shorts actions",
        first_appearance_timestamp="00:02",
        feature_density_score=0.8,
        feature_quality_score=0.75,
        feature_specifics={"framing_cadence": "fast"},
    )

    brand_ctx = configuration.BrandContext(
        brand_name="TestBrand",
        branded_products=["Product A", "Product B"],
        branded_call_to_actions=["Try Now"],
    )
    assessment = models.VideoAssessment(
        brand_name="TestBrand",
        video_uri="gs://bucket/test.mp4",
        slice_evaluations={
            "universal": [eval_u],
            "shorts": [eval_s],
        },
        brand_context=brand_ctx,
    )

    generic_helpers.store_in_bq(req, assessment)

    self.assertEqual(mock_service.load_table_from_dataframe.call_count, 1)
    expected_cols = generic_helpers.get_table_columns()

    args, _ = mock_service.load_table_from_dataframe.call_args_list[0]
    self.assertEqual(args[0], "test_dataset")
    self.assertEqual(args[1], "test_table")
    df = args[2]
    self.assertEqual(len(df), 2)
    self.assertEqual(list(df.columns), expected_cols)
    self.assertEqual(df.iloc[0]["brand_name"], "TestBrand")
    self.assertEqual(
        json.loads(df.iloc[0]["brand_context"]),
        {
            "brand_name": "TestBrand",
            "branded_products": ["Product A", "Product B"],
            "branded_call_to_actions": ["Try Now"],
        },
    )
    self.assertEqual(df.iloc[0]["feature_id"], "f_univ")
    self.assertTrue(df.iloc[0]["is_detected"])
    self.assertEqual(df.iloc[0]["rationale"], "Univ rationale")
    self.assertEqual(df.iloc[0]["evidence"], "Univ evidence")
    self.assertEqual(df.iloc[0]["strengths"], "Univ strengths")
    self.assertEqual(df.iloc[0]["weaknesses"], "Univ weaknesses")
    self.assertEqual(df.iloc[0]["recommended_actions"], "Univ actions")
    self.assertEqual(df.iloc[1]["feature_id"], "f_short")
    self.assertFalse(df.iloc[1]["is_detected"])
    self.assertEqual(df.iloc[1]["rationale"], "Shorts rationale")
    self.assertEqual(df.iloc[1]["evidence"], "Shorts evidence")
    self.assertEqual(df.iloc[1]["strengths"], "Shorts strengths")
    self.assertEqual(df.iloc[1]["weaknesses"], "Shorts weaknesses")
    self.assertEqual(df.iloc[1]["recommended_actions"], "Shorts actions")
    self.assertEqual(df.iloc[1]["first_appearance_timestamp"], "00:02")
    self.assertEqual(df.iloc[1]["feature_density_score"], 0.8)
    self.assertEqual(df.iloc[1]["feature_quality_score"], 0.75)
    self.assertEqual(
        df.iloc[1]["feature_specifics"], '{"framing_cadence": "fast"}'
    )


if __name__ == "__main__":
  unittest.main()
