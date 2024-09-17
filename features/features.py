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

"""Module with the supported ABCD feature configurations"""


def get_feature_configs() -> list[dict]:
    """Gets all the supported ABCD features
    Returns:
    feature_configs: list of feature configurations
    """
    feature_configs = [
        {
            "idx": "0",
            "id": "dynamic_start",
            "name": "Dynamic Start",
            "criteria": "The first shot in the video changes in less than 3 seconds.",
            "type": "first_5_secs_video",
            "question": "Does the first shot in the video change in less than 3 seconds?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}.",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when the first shot in the video changes.",
                "Return True if and only if the first shot in the video changes in less than 3 seconds.",
            ],
            "annotations_function": "detect_dynamic_start",
        },
        {
            "idx": "1",
            "id": "quick_pacing",
            "name": "Quick Pacing",
            "criteria": "Within ANY 5 consecutive seconds there are 5 or more shots in the video. These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms, depth of field changes, tracking shots and movement of the camera.",
            "type": "full_video",
            "question": "Are there 5 or more shots within ANY 5 consecutive seconds in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the shot changes count in the following format: Number of shots: #",
                "Provide the exact timestamp when the shot changes happen and a description of the shot.",
                "Return False if and only if the number of identified shots is less than 5.",
            ],
            "annotations_function": "detect_quick_pacing",
        },
        {
            "idx": "2",
            "id": "quick_pacing_1st_secs",
            "name": "Quick Pacing (First 5 seconds)",
            "criteria": "There are at least 5 shot changes or visual cuts detected in the video. These include hard cuts, soft transitions and camera changes such as camera pans, swipes, zooms, depth of field changes, tracking shots and movement of the camera.",
            "type": "first_5_secs_video",
            "question": "Are there at least 5 shot changes or visual cuts detected in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the shot changes count in the following format: Number of shots: #",
                "Provide the exact timestamp when the shot changes happen and a description of the shot.",
                "Return False if the number of shots identified is less than 5.",
            ],
            "annotations_function": "detect_quick_pacing_1st_5_secs",
        },
        {
            "idx": "3",
            "id": "supers",
            "name": "Supers",
            "criteria": "Any supers (text overlays) have been incorporated at any time in the video.",
            "type": "full_video",
            "question": "Are there any supers (text overlays) at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp where supers are found as well as the list of supers.",
            ],
            "annotations_function": "detect_supers",
        },
        {
            "idx": "4",
            "id": "supers_with_audio",
            "name": "Supers with Audio",
            "criteria": "The speech heard in the audio of the video matches OR is contextually supportive of the overlaid text shown on screen.",
            "type": "full_video",
            "question": "Does the speech match any supers (text overlays) in the video or is the speech contextually supportive of the overlaid text shown on the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp where supers are found and the timestamp when the speech matches the supers or is contextually supportive of the overlaid text shown on the video.",
            ],
            "annotations_function": "detect_supers_with_audio",
        },
        {
            "idx": "5",
            "id": "brand_mention_speech",
            "name": "Brand Mention (Speech)",
            "criteria": "The brand name is heard in the audio or speech at any time in the video.",
            "type": "full_video",
            "question": "Does the speech mention the brand {brand_name} at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the brand {brand_name} is heard in the speech of the video.",
            ],
            "annotations_function": "detect_brand_mention_speech",
        },
        {
            "idx": "6",
            "id": "brand_mention_speech_1st_5_secs",
            "name": "Brand Mention (Speech) (First 5 seconds)",
            "criteria": "The brand name is heard in the audio or speech in the video.",
            "type": "first_5_secs_video",
            "question": "Does the speech mention the brand {brand_name} in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the brand {brand_name} is heard in the speech of the video.",
                "Return True if and only if the brand {brand_name} is heard in the speech of the video.",
            ],
            "annotations_function": "detect_brand_mention_speech_1st_5_secs",
        },
        {
            "idx": "7",
            "id": "brand_visuals",
            "name": "Brand Visuals",
            "criteria": "Branding, defined as the brand name or brand logo are shown in-situation or overlaid at any time in the video.",
            "type": "full_video",
            "question": "Is the brand {brand_name} or brand logo {brand_name} visible at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when the brand {brand_name} or brand logo {brand_name} is found.",
            ],
            "annotations_function": "detect_brand_visuals",
        },
        {
            "idx": "8",
            "id": "brand_visuals_1st_5_secs",
            "name": "Brand Visuals (First 5 seconds)",
            "criteria": "Branding, defined as the brand name or brand logo are shown in-situation or overlaid in the video.",
            "type": "first_5_secs_video",
            "question": "Is the brand {brand_name} or brand logo {brand_name} visible in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when the brand {brand_name} or brand logo {brand_name} is found.",
            ],
            "annotations_function": "detect_brand_visuals_1st_5_secs",
        },
        {
            "idx": "9",
            "id": "product_mention_speech",
            "name": "Product Mention (Speech)",
            "criteria": "The branded product names or generic product categories are heard or mentioned in the audio or speech at any time in the video.",
            "type": "full_video",
            "question": "Are any of the following products: {branded_products} or product categories: {branded_products_categories} heard at any time in the speech of the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the products {branded_products} or product categories {branded_products_categories} are heard in the speech of the video.",
                "Return False if the products or product categories are not heard in the speech.",
                "Only strictly use the speech of the video to answer, don't consider visual elements.",
            ],
            "annotations_function": "detect_product_mention_speech",
        },
        {
            "idx": "10",
            "id": "product_mention_speech_1st_5_secs",
            "name": "Product Mention (Speech) (First 5 seconds)",
            "criteria": "The branded product names or generic product categories are heard or mentioned in the audi or speech in the the video.",
            "type": "first_5_secs_video",
            "question": "Are any of the following products: {branded_products} or product categories: {branded_products_categories} heard in the speech of the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the products {branded_products} or product categories {branded_products_categories} are heard in the speech of the video.",
                "Return False if the products or product categories are not heard in the speech.",
                "Only strictly use the speech of the video to answer, don't consider visual elements.",
            ],
            "annotations_function": "detect_product_mention_speech_1st_5_secs",
        },
        {
            "idx": "11",
            "id": "product_mention_text",
            "name": "Product Mention (Text)",
            "criteria": "The branded product names or generic product categories are present in any text or overlay at any time in the video.",
            "type": "full_video",
            "question": "Is any of the following products: {branded_products} or product categories: {branded_products_categories} present in any text or overlay at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the products {branded_products} or product categories: {branded_products_categories} are found  in any text or overlay in the video.",
            ],
            "annotations_function": "detect_product_mention_text",
        },
        {
            "idx": "12",
            "id": "product_mention_text_1st_5_secs",
            "name": "Product Mention (Text) (First 5 seconds)",
            "criteria": "The branded product names or generic product categories are present in any text or overlay in the video.",
            "type": "first_5_secs_video",
            "question": "Is any of the following products: {branded_products} or product categories: {branded_products_categories} present in any text or overlay in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the products {branded_products} or product categories: {branded_products_categories} are found in any text or overlay in the video.",
            ],
            "annotations_function": "detect_product_mention_text_1st_5_secs",
        },
        {
            "idx": "13",
            "id": "product_visuals",
            "name": "Product Visuals",
            "criteria": "A product or branded packaging is visually present at any time in the video. Where the product is a service a relevant substitute should be shown such as via a branded app or branded service personnel.",
            "type": "full_video",
            "question": "Is any of the following products: {branded_products} or product categories: {branded_products_categories} visually present at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the products {branded_products} or product categories: {branded_products_categories} are visually present.",
                "Return True if and only if the branded products or product categories are visually present in the video.",
            ],
            "annotations_function": "detect_product_visuals",
        },
        {
            "idx": "14",
            "id": "product_visuals_1st_5_secs",
            "name": "Product Visuals (First 5 seconds)",
            "criteria": "A product or branded packaging is visually present at any time in the video. Where the product is a service a relevant substitute should be shown such as via a branded app or branded service personnel.",
            "type": "first_5_secs_video",
            "question": "Is any of the following products: {branded_products} or product categories: {branded_products_categories} visually present in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Provide the exact timestamp when the products {branded_products} or product categories: {branded_products_categories} are visually present.",
                "Return True if and only if the branded products or product categories are visually present in the video.",
            ],
            "annotations_function": "detect_product_visuals_1st_5_secs",
        },
        {
            "idx": "15",
            "id": "overall_pacing",
            "name": "Overall Pacing",
            "criteria": "The pace of the video is greater than 2 seconds per shot/frame.",
            "type": "full_video",
            "question": "Is the pace of video greater than 2 seconds per shot/frame?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Return True if and only if the pace of video greater than 2 seconds per shot/frame.",
            ],
            "annotations_function": "detect_overall_pacing",
        },
        {
            "idx": "16",
            "id": "presence_of_people",
            "name": "Presence of People",
            "criteria": "People are shown in any capacity at any time in the video. Any human body parts are acceptable to pass this guideline. Alternate representations of people such as Animations or Cartoons ARE acceptable.",
            "type": "full_video",
            "question": "Are there people present at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when people are present in the video.",
            ],
            "annotations_function": "detect_presence_of_people",
        },
        {
            "idx": "17",
            "id": "presence_of_people_1st_5_secs",
            "name": "Presence of People (First 5 seconds)",
            "criteria": "People are shown in any capacity in the video. Any human body parts are acceptable to pass this guideline. Alternate representations of people such as Animations or Cartoons ARE acceptable.",
            "type": "first_5_secs_video",
            "question": "Are there people present at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when people are present in the video.",
            ],
            "annotations_function": "detect_presence_of_people_1st_5_secs",
        },
        {
            "idx": "18",
            "id": "visible_face",
            "name": "Visible Face (First 5 seconds)",
            "criteria": "At least one human face is present in the video. Alternate representations of people such as Animations or Cartoons ARE acceptable.",
            "type": "first_5_secs_video",
            "question": "Is there a human face present in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when the human face is present.",
            ],
            "annotations_function": "detect_visible_face",
        },
        {
            "idx": "19",
            "id": "visible_face_close_up",
            "name": "Visible Face (Close Up)",
            "criteria": "There is a close up of a human face at any time in the video.",
            "type": "full_video",
            "question": "Is there a close up of a human face present at any time the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when there is a close up of a human face.",
            ],
            "annotations_function": "detect_visible_face_close_up",
        },
        {
            "idx": "20",
            "id": "audio_speech_early_1st_5_secs",
            "name": "Audio Early (First 5 seconds)",
            "criteria": "Speech is detected in the audio of the video.",
            "type": "first_5_secs_video",
            "question": "Is speech detected in the audio of the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Only strictly use the speech of the video to answer.",
            ],
            "annotations_function": "detect_audio_speech_early_1st_5_secs",
        },
        {
            "idx": "21",
            "id": "call_to_action_speech",
            "name": "Call To Action (Speech)",
            "criteria": "A 'Call To Action' phrase is heard or mentioned in the audio or speech at any time in the video.",
            "type": "full_video",
            "question": "Is any call to action heard or mentioned in the speech of the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Some examples of call to actions are: {call_to_actions}",
                "Provide the exact timestamp when the call to actions are heard or mentioned in the speech of the video.",
            ],
            "annotations_function": "detect_call_to_action_speech",
        },
        {
            "idx": "22",
            "id": "call_to_action_text",
            "name": "Call To Action (Text)",
            "criteria": "A 'Call To Action' phrase is detected in the video supers (overlaid text) at any time in the video.",
            "type": "full_video",
            "question": "Is any call to action detected in any text overlay at any time in the video?",
            "instructions": [
                "Consider the following criteria for your answer: {criteria}",
                "Some examples of call to actions are: {call_to_actions}",
                "Look through each frame in the video carefully and answer the question.",
                "Provide the exact timestamp when the call to action is detected in any text overlay in the video.",
            ],
            "annotations_function": "detect_call_to_action_text",
        },
    ]

    return feature_configs


def get_feature_configs_by_type(feature_type: str) -> list[str]:
    """TODO"""
    feature_configs = get_feature_configs()
    feature_configs_by_type = [
        feature_config
        for feature_config in feature_configs
        if feature_config.get("type") == feature_type
    ]
    return feature_configs_by_type
