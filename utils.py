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

"""Utilities for parsing CLI arguments and building evaluation requests."""

import argparse
import json
import os
import textwrap

import configuration


def parse_features_to_evaluate(
    val: dict[str, list[str]] | str | None,
) -> dict[str, list[str]] | None:
  """Parses features_to_evaluate argument into a slice-to-features dictionary.

  Args:
    val: JSON string or dict mapping slice names to feature ID lists.

  Returns:
    Dictionary mapping slice names to lists of feature IDs, or None.

  Raises:
    ValueError: If the input cannot be parsed into the expected format.
  """
  if not val:
    return None

  if isinstance(val, dict):
    return {str(k): list(v) for k, v in val.items()}

  if not isinstance(val, str):
    raise ValueError(
        "Invalid features_to_evaluate type: expected JSON string or dict, "
        f"got {type(val).__name__}."
    )

  val = val.strip()
  try:
    parsed = json.loads(val)
    if isinstance(parsed, dict):
      return {str(k): list(v) for k, v in parsed.items()}
  except json.JSONDecodeError as err:
    raise ValueError(
        f"Invalid features_to_evaluate JSON string: '{val}'. Error: {err}. "
        'Expected JSON dict like \'{"universal": ["a_dynamic_start", '
        '"b_brand_visuals"], "shorts": ["tight_framing"]}\';'
    ) from err

  raise ValueError(
      f"Invalid features_to_evaluate format: '{val}'. "
      "Expected a JSON object mapping slices to lists of feature IDs, "
      'e.g. \'{"universal": ["a_dynamic_start", "b_brand_visuals"], '
      '"shorts": ["tight_framing"]}\'.'
  )


def _normalize_string_or_list(
    val: str | list[str] | tuple[str, ...] | None,
) -> list[str]:
  """Converts a comma-separated string or sequence into a cleaned list.

  Args:
    val: Comma-separated string, list, tuple, or None.

  Returns:
    Cleaned list of non-empty strings.
  """
  if not val:
    return []
  if isinstance(val, str):
    return [v.strip() for v in val.split(",") if v.strip()]
  if isinstance(val, (list, tuple)):
    return [str(v).strip() for v in val if str(v).strip()]
  return []


def build_evaluation_request(
    args: argparse.Namespace,
) -> configuration.EvaluationRequest:
  """Builds a validated EvaluationRequest from parsed command-line arguments.

  Args:
    args: Parsed command-line arguments namespace.

  Returns:
    Validated EvaluationRequest instance.
  """
  raw_project_id = getattr(args, "project_id", None) or os.getenv(
      "PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", "")
  )
  raw_location = getattr(args, "location", None) or os.getenv(
      "GCP_LOCATION", os.getenv("LOCATION", "us-central1")
  )
  gcp_config = configuration.GCPConfig(
      project_id=(
          raw_project_id.strip() if isinstance(raw_project_id, str) else ""
      ),
      location=(
          raw_location.strip()
          if isinstance(raw_location, str)
          else "us-central1"
      ),
  )

  gemini_config = configuration.GeminiConfig(
      api_key=getattr(args, "api_key", None) or os.getenv("GEMINI_API_KEY", ""),
      model_name=getattr(args, "model_name", None) or "gemini-3.8-flash",
      model_location=getattr(args, "model_location", None) or "global",
      temperature=(
          float(args.temperature)
          if getattr(args, "temperature", None) is not None
          else 0.1
      ),
      top_p=(
          float(args.top_p)
          if getattr(args, "top_p", None) is not None
          else 0.95
      ),
      max_output_tokens=(
          int(args.max_output_tokens)
          if getattr(args, "max_output_tokens", None) is not None
          else 65536
      ),
  )

  video_uris = _normalize_string_or_list(getattr(args, "video_uris", None))

  raw_slices = _normalize_string_or_list(getattr(args, "slices", None))
  slices = (
      [s.lower() for s in raw_slices] if raw_slices else ["universal", "shorts"]
  )

  features_to_evaluate = parse_features_to_evaluate(
      getattr(args, "features_to_evaluate", None)
  )

  mode_str = str(
      getattr(args, "mode", None) or getattr(args, "execution_mode", "BULK")
  ).upper()
  execution_mode = (
      configuration.ExecutionMode.INDIVIDUAL
      if mode_str == "INDIVIDUAL"
      else configuration.ExecutionMode.BULK
  )

  brand_context = None
  if getattr(args, "brand_name", None):
    brand_context = configuration.BrandContext(
        brand_name=args.brand_name.strip(),
        branded_products=_normalize_string_or_list(
            getattr(args, "branded_products", None)
        ),
        branded_call_to_actions=_normalize_string_or_list(
            getattr(args, "branded_call_to_actions", None)
        ),
    )

  bq_dataset = getattr(args, "bigquery_dataset", None) or os.getenv(
      "BQ_DATASET", ""
  )
  bq_table = getattr(args, "bigquery_table", None) or os.getenv("BQ_TABLE", "")
  bq_settings = None
  if bq_dataset or bq_table:
    bq_settings = configuration.BigQuerySettings(
        project_id=gcp_config.project_id,
        dataset_name=(
            bq_dataset.strip() if isinstance(bq_dataset, str) else ""
        ),
        table_name=bq_table.strip() if isinstance(bq_table, str) else "",
    )

  request = configuration.EvaluationRequest(
      gcp_config=gcp_config,
      gemini_config=gemini_config,
      video_uris=video_uris,
      slices=slices,
      features_to_evaluate=features_to_evaluate,
      execution_mode=execution_mode,
      extract_brand_metadata=getattr(args, "extract_brand_metadata", True),
      brand_context=brand_context,
      bigquery_settings=bq_settings,
  )

  request.validate()
  return request


def parse_args(arg_list: list[str] | None = None) -> argparse.Namespace:
  """Parses command-line arguments for ABCD Detector.

  Args:
    arg_list: Optional explicit list of CLI argument strings.

  Returns:
    Populated argparse.Namespace with parsed parameters.
  """
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent("""\
        ABCD Detector: Evaluate video ads against Google's ABCD Framework.

        Example:
          python main.py -project_id $PROJECT_ID -api_key $GEMINI_API_KEY \\
            -vu "gs://my-bucket/ad.mp4" -slices "universal,shorts"
      """),
  )

  # 1. Google Cloud Platform (GCP) Configuration
  gcp_group = parser.add_argument_group(
      "Google Cloud Platform (GCP) Configuration"
  )
  gcp_group.add_argument(
      "-project_id",
      "--project_id",
      "-project",
      "--project",
      "-pi",
      help=(
          "Google Cloud Project ID (required; or set PROJECT_ID / "
          "GOOGLE_CLOUD_PROJECT env var)."
      ),
      default=None,
  )
  gcp_group.add_argument(
      "-location",
      "--location",
      "-gcp_location",
      "--gcp_location",
      help=(
          "Google Cloud region/location (default: us-central1; or set "
          "GCP_LOCATION / LOCATION env var)."
      ),
      default="us-central1",
  )

  # 2. Gemini AI Configuration
  gemini_group = parser.add_argument_group("Gemini AI Configuration")
  gemini_group.add_argument(
      "-api_key",
      "--api_key",
      "-gemini_api_key",
      "--gemini_api_key",
      "-k",
      "--key",
      help="Gemini API Key (required; or set GEMINI_API_KEY env var).",
      default=None,
  )
  gemini_group.add_argument(
      "-model_name",
      "--model_name",
      "-model",
      "--model",
      "-m",
      help="Gemini model name (default: gemini-3.8-flash).",
      default="gemini-3.8-flash",
  )
  gemini_group.add_argument(
      "-model_location",
      "--model_location",
      help="Gemini model location (default: global).",
      default="global",
  )
  gemini_group.add_argument(
      "-temperature",
      "--temperature",
      "-temp",
      type=float,
      help="Temperature for inference between 0.0 and 2.0 (default: 0.1).",
      default=0.1,
  )
  gemini_group.add_argument(
      "-top_p",
      "--top_p",
      type=float,
      help="Top P for nucleus sampling between 0.0 and 1.0 (default: 0.95).",
      default=0.95,
  )
  gemini_group.add_argument(
      "-max_output_tokens",
      "--max_output_tokens",
      "-tokens",
      type=int,
      help="Max output tokens for model response (default: 65536).",
      default=65536,
  )

  # 3. Video Execution & Evaluation
  exec_group = parser.add_argument_group("Video Execution & Evaluation")
  exec_group.add_argument(
      "-video_uris",
      "--video_uris",
      "-videos",
      "--videos",
      "-vu",
      help=(
          "Comma-delimited video URIs (e.g. gs://bucket/vid.mp4, "
          "gs://bucket/folder/, or YouTube URL)."
      ),
      default="",
  )
  exec_group.add_argument(
      "-slices",
      "--slices",
      "-s",
      help=(
          "Comma-delimited ABCD slices to evaluate (default: universal,shorts)."
      ),
      default="universal,shorts",
  )
  exec_group.add_argument(
      "-features_to_evaluate",
      "--features_to_evaluate",
      "-features",
      "--features",
      "-fteval",
      help=(
          "Feature filter: JSON dict e.g. '{\"universal\": "
          "[\"a_dynamic_start\"], \"shorts\": [\"tight_framing\"]}'."
      ),
      default=None,
  )
  exec_group.add_argument(
      "-mode",
      "--mode",
      "-execution_mode",
      "--execution_mode",
      choices=["BULK", "INDIVIDUAL"],
      help="Execution mode (BULK or INDIVIDUAL, default: BULK).",
      default="BULK",
  )

  # 4. Brand & Product Context
  brand_group = parser.add_argument_group("Brand & Product Context")
  brand_group.add_argument(
      "-extract_brand_metadata",
      "--extract_brand_metadata",
      action="store_true",
      default=True,
      help=(
          "Extract brand metadata dynamically per video using Gemini "
          "(default: True)."
      ),
  )
  brand_group.add_argument(
      "-no_extract_brand_metadata",
      "--no_extract_brand_metadata",
      dest="extract_brand_metadata",
      action="store_false",
      help=(
          "Disable dynamic extraction; requires -brand_name and "
          "-branded_products."
      ),
  )
  brand_group.add_argument(
      "-brand_name",
      "--brand_name",
      "-brand",
      "--brand",
      "-brn",
      help="Brand name (required if extract_brand_metadata is disabled).",
      default=None,
  )
  brand_group.add_argument(
      "-branded_products",
      "--branded_products",
      "-products",
      "--products",
      "-brprs",
      help="Comma-delimited list of branded products.",
      default=None,
  )
  brand_group.add_argument(
      "-branded_call_to_actions",
      "--branded_call_to_actions",
      "-call_to_actions",
      "--call_to_actions",
      "-ctas",
      "-brcallacts",
      help="Comma-delimited list of expected brand call to actions.",
      default=None,
  )

  # 5. BigQuery Persistence (Optional)
  bq_group = parser.add_argument_group("BigQuery Persistence (Optional)")
  bq_group.add_argument(
      "-bigquery_dataset",
      "--bigquery_dataset",
      "-bq_dataset",
      "--bq_dataset",
      "-bd",
      help=(
          "BigQuery dataset name (or set BQ_DATASET env var). If provided "
          "along with table, saves results to BigQuery."
      ),
      default=None,
  )
  bq_group.add_argument(
      "-bigquery_table",
      "--bigquery_table",
      "-bq_table",
      "--bq_table",
      "-bt",
      help="BigQuery table name (or set BQ_TABLE env var).",
      default=None,
  )

  return parser.parse_args(arg_list)
