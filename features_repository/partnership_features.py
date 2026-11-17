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

"""Module with supported ABCD feature configurations for Partnership Ads."""

import models


def get_partnership_feature_configs() -> list[models.VideoFeature]:
  """Gets all supported Partnership Ads ABCD feature configurations.

  Returns:
    List of VideoFeature instances for Partnership Ads ABCDs.
  """
  feature_configs = [
      models.VideoFeature(
          id="b_brand_visual_3_plus_times",
          name="Brand Visual 3+ Times",
          category=models.VideoFeatureCategory.PARTNERSHIP_ADS,
          sub_category=models.VideoFeatureSubCategory.BRANDING,
          evaluation_criteria=(
              "Any branding is present on at least 3 frames.The same branding "
              "instance can appear on more than one frame, but NOT on "
              "consecutive frames - i.e. there must be a gap between each "
              "instance of branding."
          ),
          prompt_template=(
              "Any branding is present on at least 3 frames.The same branding "
              "instance can appear on more than one frame, but NOT on "
              "consecutive frames - i.e. there must be a gap between each "
              "instance of branding."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Compile Evidence: Gather all key frames showing the "
                  "brand name, logo, or product packaging."
              ),
              (
                  "2. Count Distinct Moments: Count the number of separate, "
                  "non-consecutive frames where the brand appears."
              ),
              (
                  "3. Final Verdict: If the count is 3 or more, the condition "
                  "is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="b_product_mention_speech_or_text",
          name="Product Mention (Speech or Text)",
          category=models.VideoFeatureCategory.PARTNERSHIP_ADS,
          sub_category=models.VideoFeatureSubCategory.BRANDING,
          evaluation_criteria=(
              "Is the Product featured in audio (VO / characters mentions) or "
              "in supers?"
          ),
          prompt_template=(
              "Is the Product featured in audio (VO / characters mentions) or "
              "in supers?"
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Review Transcript and Key Frames: Check the transcript "
                  "for spoken mentions of the product and the key frames for "
                  "text overlays mentioning the product."
              ),
              (
                  "2. Final Verdict: If the product name is found in either "
                  "source, the condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="b_product_visualized_first_5s",
          name="Product Visualized (First 5s)",
          category=models.VideoFeatureCategory.PARTNERSHIP_ADS,
          sub_category=models.VideoFeatureSubCategory.BRANDING,
          evaluation_criteria=(
              "Videos meet this criteria if a product or branded packaging is "
              "present in the first 5 seconds (up to 4.99s)."
          ),
          prompt_template=(
              "Videos meet this criteria if a product or branded packaging is "
              "present in the first 5 seconds (up to 4.99s)."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Key Frames (0-5s): Review key frames from the "
                  "first 5 seconds."
              ),
              (
                  "2. Final Verdict: If the product is visible in this window, "
                  "the condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="c_has_face_in_first_5_sec",
          name="Has Face in First 5s",
          category=models.VideoFeatureCategory.PARTNERSHIP_ADS,
          sub_category=models.VideoFeatureSubCategory.CONNECTION,
          evaluation_criteria=(
              "One or more clearly identifiable human faces are shown on "
              "screen within the first 5 seconds (up to 4.99s) of the video's "
              "run time."
          ),
          prompt_template=(
              "One or more clearly identifiable human faces are shown on "
              "screen within the first 5 seconds (up to 4.99s) of the video's "
              "run time."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Key Frames (0-5s): Review the visual key frames "
                  "extracted from the 0 to 5-second mark."
              ),
              (
                  "2. Visual Confirmation: Scan the frames to detect the "
                  "presence of any human face, whether it belongs to the "
                  "main talent, a background character, or an animated "
                  "subject."
              ),
              (
                  "3. Final Verdict: If at least one face is visually "
                  "confirmed within this initial 5-second window, the "
                  "condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="c_people_using_product",
          name="People Using Product",
          category=models.VideoFeatureCategory.PARTNERSHIP_ADS,
          sub_category=models.VideoFeatureSubCategory.CONNECTION,
          evaluation_criteria="Is the product used/held by characters?",
          prompt_template="Is the product used/held by characters?",
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Key Frames: Look for frames where a person's "
                  "hands or body are physically interacting with the product."
              ),
              (
                  "2. Check Proximity: The person should be very close to or "
                  "overlapping with the product."
              ),
              (
                  "3. Final Verdict: If this interaction is confirmed, the "
                  "condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
  ]
  return feature_configs
