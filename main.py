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

### REMOVE FOR COLAB - START

import json

from input_parameters import (
    VIDEO_URIS,
    VIDEO_SIZE_LIMIT_MB,
    ASSESSMENT_FILE,
    brand_name,
    brand_variations,
    branded_products,
    branded_products_categories,
    branded_call_to_actions,
    use_llms,
    use_annotations,
)

from helpers.generic_helpers import get_blob, trim_video
from helpers.annotations_helpers import download_video_annotations, get_annotation_uri

from features.a_quick_pacing import detect_quick_pacing
from features.a_dynamic_start import detect_dynamic_start
from features.a_supers import detect_supers, detect_supers_with_audio
from features.b_brand_visuals import detect_brand_visuals
from features.b_brand_mention_speech import detect_brand_mention_speech
from features.b_product_visuals import detect_product_visuals
from features.b_product_mention_text import detect_product_mention_text
from features.b_product_mention_speech import detect_product_mention_speech
from features.c_visible_face import detect_visible_face
from features.c_presence_of_people import detect_presence_of_people
from features.d_audio_speech_early import detect_audio_speech_early
from features.c_overall_pacing import detect_overall_pacing
from features.d_call_to_action import (
    detect_call_to_action_speech,
    detect_call_to_action_text,
)


def player(video_url: str):
    """Placeholder function to test locally"""
    print(video_url)


### REMOVE FOR COLAB - END


def print_abcd_assetssments(abcd_assessment: dict) -> None:
    """Print ABCD Assessments
    Args:
        abcd_assessments: list of video abcd assessments
    """
    print(
        f"\n\n*****  ABCD Assessment for brand {abcd_assessment.get('brand_name')}  *****"
    )
    for video_assessment in abcd_assessment.get("video_assessments"):
        # Play Video
        player(video_assessment['video_url'])
        print(f"\nAsset name: {video_assessment.get('video_name')}\n")
        passed_features_count = video_assessment.get("passed_features_count")
        total_features = len(video_assessment.get("features"))
        print(
            f"Video score: {round(video_assessment.get('score'), 2)}%, adherence ({passed_features_count}/{total_features})\n"
        )
        if video_assessment.get("score") >= 80:
            print("Asset result: ✅ Excellent \n")
        elif video_assessment.get("score") >= 65 and video_assessment.get("score") < 80:
            print("Asset result: ⚠ Might Improve \n")
        else:
            print("Asset result: ❌ Needs Review \n")

        print("Evaluated Features:")
        for feature in video_assessment.get("features"):
            if feature.get("feature_detected"):
                print(f' * ✅ {feature.get("feature")}')
            else:
                print(f' * ❌ {feature.get("feature")}')


def execute_abcd_assessment_for_videos():
    """Execute ABCD Assessment for all brand videos in GCS"""

    assessments = {"brand_name": brand_name, "video_assessments": []}

    for video_uri in VIDEO_URIS:
        # 1) Prepare video

        trim_video(video_uri)

        # Check size of video to avoid processing videos > 7MB
        video_metadata = get_blob(video_uri)
        size_mb = video_metadata.size / 1e6
        if use_llms and size_mb > VIDEO_SIZE_LIMIT_MB:
            print(
                f"The size of video {video_uri} is greater than {VIDEO_SIZE_LIMIT_MB} MB. Skipping execution."
            )
            continue

        print(f"\n\nProcessing ABCD Assessment for video {video_uri}...")

        face_annotation_results = {}
        label_annotation_results = {}
        logo_annotation_results = {}
        object_annotation_results = {}
        people_annotation_results = {}
        shot_annotation_results = {}
        speech_annotation_results = {}
        text_annotation_results = {}

        if use_annotations:
            # 2) Download generated video annotations
            (
                face_annotation_results,
                label_annotation_results,
                logo_annotation_results,
                object_annotation_results,
                people_annotation_results,
                shot_annotation_results,
                speech_annotation_results,
                text_annotation_results,
            ) = download_video_annotations(video_uri)

        # 3) Execute ABCD Assessment
        features = []

        # Quick pacing
        quick_pacing, quick_pacing_1st_5_secs = detect_quick_pacing(
            shot_annotation_results, video_uri
        )
        features.append(quick_pacing)
        features.append(quick_pacing_1st_5_secs)

        # Dynamic Start
        dynamic_start = detect_dynamic_start(shot_annotation_results, video_uri)
        features.append(dynamic_start)

        # Supers and Supers with Audio
        supers = detect_supers(text_annotation_results, video_uri)
        supers_with_audio = detect_supers_with_audio(
            text_annotation_results, speech_annotation_results, video_uri
        )
        features.append(supers)
        features.append(supers_with_audio)

        # Brand Visuals & Brand Visuals (First 5 seconds)
        (
            brand_visuals,
            brand_visuals_1st_5_secs,
            brand_visuals_logo_big_1st_5_secs,
        ) = detect_brand_visuals(
            text_annotation_results,
            logo_annotation_results,
            video_uri,
            brand_name,
            brand_variations,
        )
        features.append(brand_visuals)
        features.append(brand_visuals_1st_5_secs)

        # Brand Mention (Speech) & Brand Mention (Speech) (First 5 seconds)
        (
            brand_mention_speech,
            brand_mention_speech_1st_5_secs,
        ) = detect_brand_mention_speech(
            speech_annotation_results, video_uri, brand_name, brand_variations
        )
        features.append(brand_mention_speech)
        features.append(brand_mention_speech_1st_5_secs)

        # Product Visuals & Product Visuals (First 5 seconds)
        product_visuals, product_visuals_1st_5_secs = detect_product_visuals(
            label_annotation_results,
            video_uri,
            branded_products,
            branded_products_categories,
        )
        features.append(product_visuals)
        features.append(product_visuals_1st_5_secs)

        # Product Mention (Text) & Product Mention (Text) (First 5 seconds)
        (
            product_mention_text,
            product_mention_text_1st_5_secs,
        ) = detect_product_mention_text(
            text_annotation_results,
            video_uri,
            branded_products,
            branded_products_categories,
        )
        features.append(product_mention_text)
        features.append(product_mention_text_1st_5_secs)

        # Product Mention (Speech) & Product Mention (Speech) (First 5 seconds)
        (
            product_mention_speech,
            product_mention_speech_1st_5_secs,
        ) = detect_product_mention_speech(
            speech_annotation_results,
            video_uri,
            branded_products,
            branded_products_categories,
        )
        features.append(product_mention_speech)
        features.append(product_mention_speech_1st_5_secs)

        # Visible Face (First 5s) & Visible Face (Close Up)
        visible_face_1st_5_secs, visible_face_close_up = detect_visible_face(
            face_annotation_results, video_uri
        )
        features.append(visible_face_1st_5_secs)
        features.append(visible_face_close_up)

        # Presence of People & Presence of People (First 5 seconds)
        presence_of_people, presence_of_people_1st_5_secs = detect_presence_of_people(
            people_annotation_results, video_uri
        )
        features.append(presence_of_people)
        features.append(presence_of_people_1st_5_secs)

        #  Audio Early (First 5 seconds)
        audio_speech_early = detect_audio_speech_early(
            speech_annotation_results, video_uri
        )
        features.append(audio_speech_early)

        # Overall Pacing
        overall_pacing = detect_overall_pacing(shot_annotation_results, video_uri)
        features.append(overall_pacing)

        # Call To Action (Speech)
        call_to_action_speech = detect_call_to_action_speech(
            speech_annotation_results, video_uri, branded_call_to_actions
        )
        features.append(call_to_action_speech)

        # Call To Action (Text)
        call_to_action_text = detect_call_to_action_text(
            text_annotation_results, video_uri, branded_call_to_actions
        )
        features.append(call_to_action_text)

        # Calculate ABCD final score
        total_features = len(features)
        passed_features_count = 0
        for feature in features:
            if feature.get("feature_detected"):
                passed_features_count += 1
        # Get score
        score = (passed_features_count * 100) / total_features
        video_assessment = {
            "video_uri": video_uri,
            "video_url": video_metadata.public_url,
            "video_annotations": get_annotation_uri(video_uri),
            "features": features,
            "passed_features_count": passed_features_count,
            "score": score,
        }
        assessments.get("video_assessments").append(video_assessment)

    if ASSESSMENT_FILE:
      with open(ASSESSMENT_FILE, "w", encoding="utf-8") as f:
        json.dump(assessments, f, ensure_ascii=False, indent=4)

    return assessments


def execute_abcd_detector():
    """Main ABCD Assessment execution"""

    if VIDEO_URIS:
      abcd_assessments = execute_abcd_assessment_for_videos()
      print_abcd_assetssments(abcd_assessments)
    else:
      print("There are no videos to display.")


### Main ABCD Assessment execution ###
if __name__ == "__main__":
    execute_abcd_detector()
