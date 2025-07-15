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

"""Module to execute the ABCD Detector Assessment via API"""

import utils
from fastapi import FastAPI, Request, HTTPException
from configuration import build_config_from_file
from assessment_service import execute_abcd_assessment_for_videos

app = FastAPI()

config = build_config_from_file("config.json")

@app.post("/abcd-assessment/")
async def abcd_assessment(request: Request):
    """Runs the ABCD assessment for the given brand details and videos."""
    body = await request.json()


    config.set_brand_details(
        brand_name=body.get('brand_name'),
        brand_variations=body.get('brand_variations'),
        products=body.get('branded_products'),
        products_categories=body.get('branded_products_categories'),
        call_to_actions=body.get('branded_call_to_actions')
    )
    config.set_videos(body.get('video_uris', []))

    error_message = utils.validate_config(config)
    if error_message:
        raise HTTPException(status_code=400, detail=error_message)

    assessments = execute_abcd_assessment_for_videos(config)

    return [assessment.to_dict() for assessment in assessments]

