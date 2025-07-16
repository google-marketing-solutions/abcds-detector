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

import time
import traceback
import logging
import utils
from helpers import generic_helpers
from configuration import build_config_from_file
from assessment_service import execute_abcd_assessment_for_videos


def main(arg_list: list[str] | None = None) -> None:
  """Main ABCD Assessment execution. See docstring and args.

  Args:
    arg_list: A list of command line arguments

  """

  try:
    args = utils.parse_args(arg_list)

    if args.config_file:
        config = build_config_from_file(args.config_file)
    else:
        config = utils.build_abcd_params_config(args)

    error_message = utils.validate_config(config)
    if error_message:
      logging.error(error_message)
      return

    start_time = time.time()
    logging.info("Starting ABCD assessment... \n")

    assessments = execute_abcd_assessment_for_videos(config)

    for video_assessment in assessments:
        # Print assessments for Full ABCD and Shorts and store results
        if len(video_assessment.full_abcd_evaluated_features) > 0:
          generic_helpers.print_abcd_assessment(
              video_assessment.brand_name,
              video_assessment.video_uri,
              video_assessment.full_abcd_evaluated_features,
          )
        else:
          logging.info(
              "There are not Full ABCD evaluated features results to display for video %s.", video_assessment.video_uri
          )
        if len(video_assessment.shorts_evaluated_features) > 0:
          generic_helpers.print_abcd_assessment(
              video_assessment.brand_name,
              video_assessment.video_uri,
              video_assessment.shorts_evaluated_features,
          )
        else:
          logging.info(
              "There are not Shorts evaluated features results to display for video %s.", video_assessment.video_uri
          )

        if config.bq_table_name:
          generic_helpers.store_in_bq(config, video_assessment)

    logging.info("Finished ABCD assessment. \n")

    logging.info(
        "ABCD assessment took - %s mins. - \n", (time.time() - start_time) / 60
    )
  except Exception as ex:
    logging.error("ERROR: %s", ex)
    traceback.print_exc()



if __name__ == "__main__":
  main()
