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

"""Module with the supported ABCD feature configurations for Universal ABCDs."""

import models


def get_universal_feature_configs() -> list[models.VideoFeature]:
  """Gets all supported Universal ABCD feature configurations.

  Returns:
    List of VideoFeature instances for Universal ABCDs.
  """
  feature_configs = [
      models.VideoFeature(
          id="a_heartbeat_story_arc",
          name="Heartbeat Story Arc",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          evaluation_criteria=(
              "Heartbeat Story Arc: Message, strong scene/tease or conclusion "
              "revealed within the first 5 seconds (up to 4.99s)."
          ),
          prompt_template=(
              "Heartbeat Story Arc: Message, strong scene/tease or conclusion "
              "revealed within the first 5 seconds (up to 4.99s)."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Early Hook (0-5s): Directly analyze the key frames and "
                  "transcript from the first 5 seconds."
              ),
              (
                  "2. Final Verdict: Determine if this analysis confirms a "
                  "compelling message, scene, or conclusion is presented."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="a_tightly_framed_overall",
          name="Tightly Framed (Overall)",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          evaluation_criteria=(
              "Tightly Framed (Overall): One or more shots showcase the "
              "largest subject(s), product(s), animation(s), environment(s) "
              "or any object are tightly framed at any time."
          ),
          prompt_template=(
              "Tightly Framed (Overall): One or more shots showcase the "
              "largest subject(s), product(s), animation(s), environment(s) "
              "or any object are tightly framed at any time."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Key Frames: Review all key frames for close-ups "
                  "on a person or object."
              ),
              (
                  "2. Estimate Frame Coverage: Determine if any key object or "
                  "person's face covers at least 30% of the screen area."
              ),
              (
                  "3. Final Verdict: If this threshold is met in any frame, the"
                  " condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="a_has_audio",
          name="Has Sound",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          evaluation_criteria=(
              "Has Sound: Video includes any audible sound, including music, "
              "sound effects (water splashing, ‘crunch’ sound, etc.), "
              "voice-over, etc."
          ),
          prompt_template=(
              "Has Sound: Video includes any audible sound, including music, "
              "sound effects (water splashing, ‘crunch’ sound, etc.), "
              "voice-over, etc."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Transcript: Check if the provided transcript has "
                  "any text content at all."
              ),
              (
                  "2. Final Verdict: If the transcript is not empty, sound is "
                  "present."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="a_has_supers",
          name="Supers",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          evaluation_criteria=(
              "Supers: Videos meet this criteria if any supers (text "
              "overlays) have been incorporated into the video."
          ),
          prompt_template=(
              "Supers: Videos meet this criteria if any supers (text "
              "overlays) have been incorporated into the video."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              "1. Consult Key Frames: Directly examine the key frames.",
              (
                  "2. Final Verdict: If any text overlays are visible, the "
                  "condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="a_supers_w_audio",
          name="Supers w/ Audio",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          evaluation_criteria=(
              "Supers w/ Audio: Supers Augment OR Match the audio Creative "
              "meets this criteria, if the speech heard in the ad matches OR "
              "is contextually supportive of the overlaid text shown on screen."
          ),
          prompt_template=(
              "Supers w/ Audio: Supers Augment OR Match the audio Creative "
              "meets this criteria, if the speech heard in the ad matches OR "
              "is contextually supportive of the overlaid text shown on screen."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. See & Say (Match): Determine if spoken words in the "
                  "transcript EXACTLY match on-screen text in the key frames "
                  "at the same time."
              ),
              (
                  "2. Augmented (Support): Determine if the speech is "
                  "contextually supportive of the on-screen text."
              ),
              (
                  "3. Final Verdict: If either condition 1 OR 2 is met, the "
                  "condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="b_brand_visualized_in_first_5_sec",
          name="Brand Visualized (First 5s)",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.BRAND,
          evaluation_criteria=(
              "Brand Visualized (First 5s): Videos meet this criteria if "
              "branding, defined as the brand name or brand logo, or branded "
              "products and packaging are shown in-situation or overlaid "
              "within the ad in the first 5 seconds (up to 4.99s)."
          ),
          prompt_template=(
              "Brand Visualized (First 5s): Videos meet this criteria if "
              "branding, defined as the brand name or brand logo, or branded "
              "products and packaging are shown in-situation or overlaid "
              "within the ad in the first 5 seconds (up to 4.99s)."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Key Frames (0-5s): Review key frames from the "
                  "first 5 seconds."
              ),
              (
                  "2. Final Verdict: If the brand name, logo, or product "
                  "packaging is found in this window, the condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="b_brand_mention",
          name="Brand Mentioned",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.BRAND,
          evaluation_criteria=(
              "Brand Mentioned: Meets criteria if it has included an audible "
              "logo or if a brand-specific logo (i.e. jingle) is heard at any "
              "time. This DOES include a voice over mention of the brand name."
          ),
          prompt_template=(
              "Brand Mentioned: Meets criteria if it has included an audible "
              "logo or if a brand-specific logo (i.e. jingle) is heard at any "
              "time. This DOES include a voice over mention of the brand name."
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Transcript: Check the transcript for any spoken "
                  "mention of the brand name or description of a jingle."
              ),
              (
                  "2. Final Verdict: If either is found, the condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="b_brand_mention_speech_see_and_say_first_5s",
          name="Brand Mention (Speech) (See & Say) (First 5s)",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.BRAND,
          evaluation_criteria=(
              "Brand Mention (Speech) (See & Say) (First 5s): Is the Brand "
              "mentioned and visualized in the same frame in the First 5s?"
          ),
          prompt_template=(
              "Brand Mention (Speech) (See & Say) (First 5s): Is the Brand "
              "mentioned and visualized in the same frame in the First 5s?"
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Find Audio Mentions: Identify all times the brand is "
                  "spoken in the transcript in the first 5s."
              ),
              (
                  "2. Find Visuals: Identify all key frames where the brand is "
                  "visible in the first 5s."
              ),
              (
                  "3. Check for Overlap: Determine if any audio mention occurs "
                  "at the same time as a visual appearance."
              ),
              (
                  "4. Final Verdict: If an overlap exists in the first 5s, the "
                  "condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="b_brand_palette_multiple_brand_elements",
          name="Brand Palette Multiple Brand Elements",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.BRAND,
          evaluation_criteria=(
              "Brand Palette Multiple Brand Elements: Does the ad include the "
              "brand in 2 or more different audio or visual ways?"
          ),
          prompt_template=(
              "Brand Palette Multiple Brand Elements: Does the ad include the "
              "brand in 2 or more different audio or visual ways?"
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Create a checklist: (Visual Logo/Text, Spoken Name, "
                  "Visual Product, Jingle). Tick off each unique type of "
                  "brand element observed in the key frames and transcript."
              ),
              (
                  "2. Final Verdict: If the count of unique elements is 2 or "
                  "more, the condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="c_people_overall",
          name="People (Overall)",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.CONNECT,
          evaluation_criteria="People (Overall): Are there People in the ad?",
          prompt_template="People (Overall): Are there People in the ad?",
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Analyze Key Frames: Check if any key frames contain a "
                  "person or a face."
              ),
              (
                  "2. Final Verdict: If people or faces are present, the "
                  "condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="c_casual_language",
          name="Casual Language",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.CONNECT,
          evaluation_criteria=(
              "Casual Language: Does the ad use everyday language?"
          ),
          prompt_template=(
              "Casual Language: Does the ad use everyday language?"
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              "1. Analyze Transcript Language: Read the transcript.",
              (
                  "2. Final Verdict: If the language is predominantly "
                  "conversational and avoids jargon, the condition is met."
              ),
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
      models.VideoFeature(
          id="d_visual_cta",
          name="Call to Action (Text)",
          category=models.VideoFeatureCategory.UNIVERSAL,
          sub_category=models.VideoFeatureSubCategory.DIRECT,
          evaluation_criteria=(
              "Call to Action (Text): Is the CTA visualized in supers?"
          ),
          prompt_template=(
              "Call to Action (Text): Is the CTA visualized in supers?"
          ),
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}.",
              (
                  "1. Scan Key Frames: Look at all text overlays for "
                  "imperative verbs or phrases that instruct the viewer "
                  "(e.g., 'Shop Now', 'Learn More')."
              ),
              "2. Final Verdict: If a CTA is found, the condition is met.",
          ],
          evaluation_method=models.EvaluationMethod.GEMINI,
      ),
  ]
  return feature_configs
