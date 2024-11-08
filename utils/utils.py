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

""" Utils Module for generic functions """

import argparse
import textwrap
from configuration import Configuration


def build_abcd_params_config(args: any) -> Configuration:
    """Builds ABCD configuration with all the required parameters.

    Args:
        args: The parser arguments.
    Returns:
        config: The parameter configuration for ABCD.

    """
    config = Configuration()
    config.set_parameters(
        project_id=args.project_id,
        project_zone=args.project_zone,
        bucket_name=args.bucket_name,
        knowledge_graph_api_key=args.knowledge_graph_api_key,
        bigquery_dataset=args.bigquery_dataset,
        bigquery_table=args.bigquery_table,
        assessment_file=args.assessment_file,
        use_annotations=args.use_annotations,
        use_llms=args.use_llms,
        verbose=args.verbose,
    )
    config.set_videos(args.video_uris)
    config.set_brand_details(
        brand_name=args.brand_name,
        brand_variations=args.brand_variations,
        products=args.branded_products,
        products_categories=args.branded_products_categories,
        call_to_actions=args.branded_call_to_actions,
    )
    return config


def parse_args(arg_list: list[str] | None = None) -> None:
  """Parses command line arguments"""

  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent(
          """\
          Command line to execute ABCD detector with parameters.

          This loads the minimal parameters needed to configure the tool.
          See the configuration.py file for additional parameters.

          Example: python main.py -pi my_project -pz "us-central1" -bn "my_bucket" -vu "gs://my_bucket/Google/videos/" -ua -ul -v
      """
      ),
  )

  parser.add_argument("-project_id", "-pi", help="Google Cloud Project ID.")
  parser.add_argument("-project_zone", "-pz", help="Google Cloud Project Zone.")
  parser.add_argument(
      "-bucket_name", "-bn", help="Google Cloud Project Bucket Name (not url)."
  )
  parser.add_argument(
      "-video_uris", "-vu", help="Comma delimited string of video or folder URIs."
  )
  parser.add_argument(
      "-brand_name", "-brn", help="The name of the brand.", default=None
  )
  parser.add_argument(
      "-brand_variations",
      "-brv",
      help="The list of brand name variations.",
      default=None,
  )
  parser.add_argument(
      "-branded_products",
      "-brprs",
      help="The list of branded products.",
      default=None,
  )
  parser.add_argument(
      "-branded_products_categories",
      "-brprscts",
      help="The list of branded product categories",
      default=None,
  )
  parser.add_argument(
      "-branded_call_to_actions",
      "-brcallacts",
      help="The list of branded call to actions",
      default=None,
  )
  parser.add_argument(
      "-knowledge_graph_api_key",
      "-kgak",
      help="Knowledge Graph Key for API.",
      default=None,
  )
  parser.add_argument(
      "-bigquery_dataset",
      "-bd",
      help="Name of BigQuery dataset to write to",
      default=None,
  )
  parser.add_argument(
      "-bigquery_table",
      "-bt",
      help="Name of BigQuery table to write to",
      default=None,
  )
  parser.add_argument(
      "-assessment_file",
      "-af",
      help="Local file path to write results to",
      default=None,
  )
  parser.add_argument(
      "-use_annotations",
      "-ua",
      help="Analyze videos using annotations.",
      action="store_true",
      default=False,
  )
  parser.add_argument(
      "-use_llms",
      "-ul",
      help="Analyze videos using LLMs.",
      action="store_true",
      default=False,
  )
  parser.add_argument(
      "-verbose",
      "-v",
      help="Print all the steps as they happen.",
      action="store_true",
      default=False,
  )

  args = parser.parse_args(arg_list)

  return args
