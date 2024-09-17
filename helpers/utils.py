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

"""Utils module for generic code"""


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
