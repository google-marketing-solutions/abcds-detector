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

"""Module with the supported ABCD feature configurations for Shorts."""

import models

BASE_RESPONSE_FORMAT = """

        ### 3. GENERAL GUIDANCE FOR FIELDS:
        - Shorts Benchmarking:
            * All evaluations must be tailored specifically to Short-Form
              Video (Shorts) content
            * Use the creative criteria and best practices of successful
              short-form video advertisers as your benchmark
        - confidence_score:
            * This score must reflect your confidence in your final
              is_detected decision (whether True or False).
            * A high score means you are certain about your answer
            * A low score means the video evidence is ambiguous or hard to
              evaluate.
        - rationale:
            * High-level summary of the decision.
        - evidence:
            * Always include specific timestamps and visual/audible cues to
              support your claims.
        - strengths:
            * What the editor did right and should not change.
        - weaknesses:
            * Creative flaws or aspects where the execution falls short.
        - recommended_actions:
            * Must be a specific, concrete, and actionable next step for the
              editor to improve this feature. Avoid generic advice.
            * You MUST provide a specific recommendation if the feature is
              missing or if the feature_quality_score is low (<= 0.4).
            * If the feature is fully optimized and no improvement is needed,
              return "Great job! This feature is already fully optimized."

        ### 4. FORMAT RESPONSE AS JSON:

        **OUTPUT STRUCTURE:**
        (Note: The comments starting with # are for your guidance only. Do not
        include them in your final JSON response.)
        {{
            "is_detected": boolean,  # True if feature is present, False
            otherwise; as calculated in EVALUATION LOGIC
            "confidence_score": float,  # 0.0 to 1.0; confidence in decision;
            as calculated in EVALUATION LOGIC
            "rationale": string,  # High-level summary of the decision
            "evidence": string,  # Description of cues and timestamps
            "strengths": string,  # What the editor did right and should not
            change
            "weaknesses": string,  # Creative flaws or aspects where execution
            falls short
            "recommended_actions": string,  # Actionable next step for the
            editor to improve this feature
            "first_appearance_timestamp": string,  # When this feature first
            appeared, format MM:SS
            "feature_density_score": float,  # 0.0 to 1.0; represents the
            percentage of video duration the feature is present; as calculated
            in EVALUATION LOGIC
            "feature_quality_score": float,  # 0.0 to 1.0; represents the
            creative quality of the execution; as calculated in EVALUATION
            LOGIC
            "feature_specifics": {{
                {specifics}
            }}
        }}
"""


def get_shorts_feature_configs() -> list[models.VideoFeature]:
  """Gets all supported Shorts ABCD feature configurations.

  Returns:
    List of VideoFeature instances for Shorts ABCDs.
  """
  # Get original shorts features
  feature_configs = [
      models.VideoFeature(
          id="a_tight_framing",
          name="Tight Framing & Visual Dominance",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Quantifies the spatial dominance of the primary subject.
                Tight framing is defined by a Subject-to-Frame Ratio (SfR) of
                ≥60%.
                The score reflects the 'Density' (persistence) of tight
                framing,
                differentiating between incidental close-ups and thematic
                visual dominance.
            """,
          prompt_template="""
                Act as a professional Cinematographer and Video Analyst. Your
                goal is to measure
                'Visual Weight' through Tight Framing detection.

                VIDEO METADATA: {metadata_summary}

                ### 1. SHOT CLASSIFICATION (for reference):
                    - Extreme Close-Up (ECU): Subject fills >80% of frame.
                    - Close-Up (CU): Subject fills 60%-80% of frame.
                    - Medium Shot (MS): Subject fills 30%-59% of frame.
                    - Wide/Long Shot (LS): Subject fills <30% of frame.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the subject fills the frame
                       - how unambiguous the shot type is. Otherwise set to
                         False.
                    2. Set confidence_score: Score from 0.0 to 1.0 reflecting
                    your confidence in your final detected decision.
                    3. Calculate feature_density_score:
                        - Formula: (Total CU+ECU duration) / (Total video
                          duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on the "Goldilocks Zone" of density
                          (ideal is 30%-60%).
                        - Give a bonus if the first 3 seconds (The Hook)
                          contain tight framing.
                        - Score from 0.0 to 1.0 reflecting effectiveness.
                    5. Rationale & Evidence: Cite specific timestamps and shot
                    durations.
        """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "peak_sfr_percentage": float (Highest Subject-to-Frame
                        Ratio observed in the video, e.g., 0.85),
                        "primary_subject_class": string (Category of the main
                        subject, e.g., Human, Product, Text),
                        "framing_cadence": string (Rhythm of shot changes,
                        e.g., Rapid cuts, Static, Smooth transitions)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="a_human_voice",
          name="Human Voice Presence",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Quantifies the presence, duration, and quality of human
                speech.
                Voice includes Voice-Overs (VO), direct-to-camera dialogue, or
                background
                narration. The metric measures 'Vocal Density' (percentage of
                video containing
                speech) and assesses the clarity and role of the speaker.
            """,
          prompt_template="""
                Act as a professional Cinematographer and Video Analyst.
                Your goal is to analyze the audio track of this video
                specifically for human vocal presence.

                VIDEO METADATA: {metadata_summary}

                ### 1. DEFINITIONS (for reference):
                    - Voice Over (VO): Narrative voice added in
                      post-production.
                    - Dialogue: On-camera person speaking.
                    - Ambient Speech: Overheard background talking.
                    - Synthetic/AI Voice: Clear AI-generated narration
                      (text-to-speech).
                    - Vocal Clarity: The ease with which the voice is
                      understood (0.0 - 1.0).
                      High score = studio quality/clear; Low score = muffled,
                      heavy background noise.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the voice is audible
                       - how identifiable it is. Otherwise set to False.
                    2. Set confidence_score: Score from 0.0 to 1.0 reflecting
                    your confidence in your final detected decision.
                    3. Calculate feature_density_score:
                        - Formula: (Total duration of audible human speech) /
                          (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on Vocal Clarity (0.0 to 1.0).
                        - Give a bonus (+0.1) if the speech starts in the
                          first 3 seconds (The Hook).
                        - Score from 0.0 to 1.0 reflecting effectiveness.
                    5. Rationale & Evidence: Cite specific timestamps and
                    durations.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "vocal_clarity_score": float (Clarity of speech from
                        0.0 to 1.0, where 1.0 is studio quality),
                        "primary_voice_type": string (Type of voice, e.g.,
                        Voice Over, Dialogue, Ambient, Synthetic),
                        "speech_cadence": string (Pace of speaking, e.g.,
                        Fast, Measured, Conversational),
                        "background_noise_level": string (Level of background
                        noise, e.g., Low, Moderate, High)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="a_direct_camera",
          name="Direct to Camera",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.ATTRACT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Quantifies the duration and intensity of direct eye contact
                between the
                on-screen subject and the camera lens. This feature measures
                the
                'Direct Address Density' and assesses the intimacy of the
                framing
                (e.g., face-to-face address).
            """,
          prompt_template="""
                Act as a professional Cinematographer and Video Analyst.
                Your goal is to analyze the video for instances where a person
                looks
                directly into the camera lens to address the viewer.

                VIDEO METADATA: {metadata_summary}

                ### 1. ADDRESS MODES (for reference):
                    - Direct Address: Subject is looking into the lens and
                      speaking.
                    - Silent Gaze: Subject maintains eye contact without
                      speaking.
                    - Glance: Brief, intermittent eye contact (less than
                      0.5s).
                    - Off-Camera: Subject is looking at a secondary point, not
                      the viewer.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the subject's pupils are directed at the
                         camera lens. Otherwise set to False.
                    2. Set confidence_score: Score from 0.0 to 1.0 reflecting
                    your confidence in your final detected decision.
                    3. Calculate feature_density_score:
                        - Formula: (Total duration of direct eye contact /
                          address) / (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on Eye Contact Intensity (0.0 to 1.0).
                        - Give a bonus (+0.1) if direct address starts in the
                          first 2 seconds (Hook).
                        - Score from 0.0 to 1.0 reflecting effectiveness.
                    5. Rationale & Evidence: Cite specific timestamps and
                    durations.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "eye_contact_intensity": float (Strength of gaze from
                        0.0 to 1.0),
                        "subject_distance": string (e.g., Extreme Close-Up,
                        Close-Up, Medium),
                        "address_style": string (e.g., Direct Address, Silent
                        Gaze, Glance),
                        "emotional_delivery": string (e.g., Enthusiastic,
                        Serious, Casual)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="b_product_closeup",
          name="Product Close-Up",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.BRAND,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Quantifies segments where the product occupies at least 30% of
                the frame.
                This measures standard product visibility and presence within
                a recognizable context or environment.
            """,
          prompt_template="""
                Act as a professional Cinematographer and Video Analyst. Your
                goal is to
                measure 'Product Presence' via Close-Up detection.

                VIDEO METADATA: {metadata_summary}

                ### 1. SHOT CLASSIFICATION (for reference):
                    - Product Close-Up (CU): Product occupies 30% to 59% of
                      the frame area.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the product is identifiable
                       - how in focus it is (regardless of duration).
                         Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Total duration of Product CU shots) /
                          (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on Product Identifiability (0.0 to 1.0)
                          and Framing
                          Style (is it centered or following rule of thirds?).
                        - Score from 0.0 to 1.0 reflecting effectiveness.
                    5. Rationale & Evidence: Cite specific timestamps and shot
                    durations.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "average_sfr_percentage": float (Average
                        Subject-to-Frame Ratio for product shots),
                        "product_identifiability": float (Clarity of branding
                        from 0.0 to 1.0),
                        "framing_style": string (e.g., Centered, Rule of
                        Thirds)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="b_product_extreme_closeup",
          name="Product Extreme Close-Up",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.BRAND,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Quantifies segments where the product is the dominant visual
                element,
                occupying 60% or more of the frame. This measures 'Macro'
                focus and
                high-detail product showcasing.
            """,
          prompt_template="""
                Act as a professional Cinematographer and Video Analyst. Your
                goal is to
                measure 'Product Dominance' via Extreme Close-Up (ECU)
                detection.

                VIDEO METADATA: {metadata_summary}

                ### 1. SHOT CLASSIFICATION (for reference):
                    - Product Extreme Close-Up (ECU): Product occupies 60% or
                      more of the frame area.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the product's fine details and textures
                         are visible
                       - how in focus it is (regardless of duration).
                         Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Total duration of Product ECU shots) /
                          (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on Texture Visibility and Lighting
                          Quality (0.0 to 1.0).
                        - Score from 0.0 to 1.0 reflecting effectiveness in
                          showcasing high detail.
                    5. Rationale & Evidence: Cite specific timestamps and shot
                    durations.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "peak_sfr_percentage": float (Highest Subject-to-Frame
                        Ratio for product shots),
                        "texture_visibility": string (Visibility of fine
                        details, e.g., High, Moderate, Low),
                        "lighting_quality": string (Quality of lighting, e.g.,
                        Soft, Harsh, Studio)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="c_people_using_product",
          name="Product Context & Usage Quality",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.CONNECT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Evaluates the 'Show, Don't Tell' quality. Quantifies physical
                interaction, environmental realism, and utility demonstration.
                Measures both the duration of usage (Density) and the
                effectiveness
                of the demonstration (Quality Score).
            """,
          prompt_template="""
                Act as a professional Cinematographer and Video Analyst.
                Analyze the 'Product-in-Use' effectiveness.

                VIDEO METADATA:
                {metadata_summary}

                ### 1. SCORE DIMENSIONS (for reference):
                    - INTERACTION DEPTH (40% weight): Physical contact and
                      active engagement.
                    - CONTEXTUAL REALISM (30% weight): "Lived-in" space vs.
                      sterile studio.
                    - UTILITY DEMONSTRATION (30% weight): Shows product's
                      purpose/benefit.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly identifiable the product is
                       - how clearly identifiable its usage are (regardless of
                         duration or quality score). Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of active product usage) / (Total
                          video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Score each of the three dimensions in Step 1 from 0
                          to 100.
                        - Calculate the weighted total: `(Interaction Depth *
                          0.40) +
                          (Contextual Realism * 0.30) + (Utility Demonstration
                          * 0.30)`.
                        - Divide the weighted total by 100 to get the final
                          `feature_quality_score` as a float between 0.0 and
                          1.0.
                    5. Rationale & Evidence: Cite specific timestamps and
                    actions
                       supporting the scores.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "interaction_depth_score": int (Score for physical
                        engagement from 0 to 100),
                        "contextual_realism_score": int (Score for realistic
                        environment from 0 to 100),
                        "utility_demo_score": int (Score for showing
                        purpose/benefit from 0 to 100)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="c_humor",
          name="Humor & Comedic Timing",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.CONNECT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Detects and quantifies attempts at humor, including wit,
                physical comedy,
                satire, or comedic timing.
            """,
          prompt_template="""
                Act as a Creative Strategist. Analyze the video for 'Comedic
                Intent.'

                VIDEO METADATA:
                {metadata_summary}

                ### 1. DEFINITIONS (for reference):
                    - Humor Type: "Observational", "Slapstick", "Deadpan",
                      "Satirical".

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly you can identify attempts at humor
                       - how clearly you can identify comedic timing
                         (regardless of duration). Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of comedic setups/payoffs) /
                          (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on Edge Factor (how daring or unique the
                          humor is)
                          and Comedic Timing (0.0 to 1.0).
                        - Score from 0.0 to 1.0 reflecting effectiveness.
                    5. Rationale & Evidence: Cite specific timestamps and
                    comedic moments.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "humor_mechanism": string (Type of humor, e.g.,
                        Observational, Slapstick, Deadpan),
                        "edge_factor": float (How daring or unique the humor
                        is from 0.0 to 1.0)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="c_character_driven",
          name="Character-Driven",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.CONNECT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Video features a relatable character whose journey or
                transformation resonates with audience.
                Evaluates character prominence, relatability, and narrative
                journey shown.
            """,
          prompt_template="""
                Act as a Narrative Strategist and Video Analyst. Your goal is
                to measure
                'Character Dominance' and 'Persona-Led Storytelling.'

                VIDEO METADATA:
                {metadata_summary}

                ### 1. SCORE DIMENSIONS (for reference):
                    - CHARACTER PROMINENCE (40% weight): Protagonist with
                      distinct personality/role.
                    - CHARACTER JOURNEY (30% weight): Visible journey, change,
                      or problem-solving.
                    - AUDIENCE RELATABILITY (30% weight): Relatable to target
                      audience.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the character is identifiable as a
                         protagonist (regardless of duration). Otherwise set
                         to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of character prominence) / (Total
                          video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Score each of the three dimensions in Step 1 from 0
                          to 100.
                        - Calculate the weighted total: `(Character Prominence
                          * 0.40) +
                          (Character Journey * 0.30) + (Audience Relatability
                          * 0.30)`.
                        - Divide the weighted total by 100 to get the final
                          `feature_quality_score` as a float between 0.0 and
                          1.0.
                    5. Rationale & Evidence: Cite specific timestamps and
                    actions
                       supporting the scores.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "character_type": string (e.g., Creator, Actor,
                        Celebrity),
                        "prominence_score": int (Score for character dominance
                        from 0 to 100),
                        "journey_score": int (Score for visible journey from 0
                        to 100),
                        "relatability_score": int (Score for audience
                        relatability from 0 to 100)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="d_audio_cta",
          name="Call to Action (Audio)",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.DIRECT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Detects and quantifies spoken instructions that direct the
                viewer to take
                action. This includes verbal commands from Voice-Overs (VO) or
                on-screen talent.
                Measures 'CTA Density' and 'Urgency Level' to determine the
                strength of the
                conversion signal.
            """,
          prompt_template="""
                Act as a Direct Response Marketing Analyst. Your goal is to
                identify and
                quantify the spoken Call to Action (CTA).

                VIDEO METADATA: {metadata_summary}

                ### 1. CTA DELIVERY MODES (for reference):
                    - Direct Address: On-screen talent looks at camera and
                      gives the CTA.
                    - Voice-Over (VO): Narrator delivers the CTA over b-roll
                      or product shots.
                    - Off-Camera: Secondary character or background voice
                      mentions the action.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the spoken CTA is audible
                       - how identifiable it is (regardless of duration).
                         Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Total duration of the spoken CTA) / (Total
                          video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on CTA Urgency (0.0 to 1.0). 1.0 =
                          Explicit command
                          with time-sensitivity; 0.5 = General suggestion; 0.1
                          = Brand mention only.
                        - Score from 0.0 to 1.0 reflecting effectiveness.
                    5. Rationale & Evidence: Cite specific timestamps and the
                    verbatim
                       text of the CTA.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "cta_urgency_score": float (Urgency of command from
                        0.0 to 1.0),
                        "delivery_method": string (e.g., Direct Address,
                        Voice-Over),
                        "cta_type": string (e.g., Explicit command,
                        Suggestion),
                        "placement_type": string (e.g., End of video,
                        Beginning, Middle)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="d_special_offer_speech",
          name="Special Offer (Speech)",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.DIRECT,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Audio/voiceover explicitly announces special offer, discount,
                or deal.
                Evaluates clarity of offer type, specific details mentioned,
                and delivery emphasis.
            """,
          prompt_template="""
                Act as a Direct Response Marketing Analyst. Your goal is to
                evaluate: Is there a SPECIAL OFFER announced in speech?

                VIDEO METADATA:
                {metadata_summary}

                ### 1. SCORE DIMENSIONS (for reference):
                    - OFFER TYPE CLARITY (40% weight): Clear announcement of
                      what offer is.
                    - DELIVERY EMPHASIS (35% weight): Strong emphasis given
                      through voice tone.
                    - OFFER PROMINENCE (25% weight): Featured continuously or
                      at strategic moments.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the special offer is audible
                       - how identifiable it is (regardless of duration).
                         Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of offer announcement) / (Total
                          video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Score each of the three dimensions in Step 1 from 0
                          to 100.
                        - Calculate the weighted total: `(Offer Clarity *
                          0.40) +
                          (Delivery Emphasis * 0.35) + (Offer Prominence *
                          0.25)`.
                        - Divide the weighted total by 100 to get the final
                          `feature_quality_score` as a float between 0.0 and
                          1.0.
                    5. Rationale & Evidence: Cite specific timestamps and the
                    verbatim
                       text of the offer.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "offer_type": string (Type of offer, e.g., Discount,
                        Deal, Freebie),
                        "offer_clarity_score": int (Score for clarity of offer
                        from 0 to 100),
                        "emphasis_score": int (Score for delivery emphasis
                        from 0 to 100),
                        "prominence_score": int (Score for prominence from 0
                        to 100)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_production_style",
          name="Production Style (User Generated)",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Quantifies the ad's balance between a 'native social
                appearance' and 'premium brand quality.'
                Measures the strategic integration of UGC markers (handheld
                motion, casual framing, natural lighting)
                with studio polish (clear audio, stabilization). Assesses if
                the video successfully delivers
                a high-converting 'organic ad' feel rather than an
                over-produced traditional commercial.
            """,
          prompt_template="""
                Act as a Data-Driven Performance Ad Creative Strategist and
                Media
                Buyer. Your goal is to evaluate how effectively this video
                blends
                high-quality commercial standards with native social UGC
                mechanics
                to optimize viewer retention and brand trust.

                VIDEO METADATA: {metadata_summary}

                ### 1. PRODUCTION MARKERS REFERENCE:
                    - Raw UGC: Raw mobile camera footage, handheld jitter,
                      natural
                      lighting, "face-to-lens" creator delivery.
                    - Premium UGC / Studio-UGC: High-end mobile or mirrorless
                      capture,
                      stabilized motion, softbox/ring lighting, crisp external
                      microphone audio, retaining a highly relatable,
                      platform-native
                      look.
                    - Over-Produced Commercial: Cinema-grade cameras, heavy
                      3-point
                      studio lighting, deep color grading, highly polished
                      actors;
                      feels explicitly like a traditional TV commercial.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly you identify platform-native ad styles
                         (Raw UGC or Premium UGC). Otherwise set to False.
                    2. Set confidence_score: Float from 0.0 to 1.0 reflecting
                    your confidence in your final detected decision.
                    3. Calculate feature_density_score:
                        - Formula: (Estimated duration of native-feeling
                          footage) / (Total video duration)
                        - Estimate the ratio by approximating the combined
                          duration of Raw UGC and Premium UGC segments using
                          metadata timestamps.
                        - Returns a float between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Rate the creative execution on a scale from 0.0 to
                          1.0.
                        - 1.0 = Exceptional Premium UGC that seamlessly
                          balances high production value with organic social
                          authenticity.
                        - 0.5 = Forced or poorly executed UGC that feels
                          overtly scripted.
                        - 0.0 = Traditional, rigid commercial style with zero
                          platform-native integration.
                    5. Rationale & Evidence: Provide text justification
                    showing your estimated duration math and analyzing how the
                    production style impacts ad performance or brand safety.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "camera_stability": string (e.g., Handheld jitter,
                        Stabilized, Tripod),
                        "lighting_type": string (e.g., Natural, Softbox, Ring
                        light),
                        "equipment_look": string (e.g., Mobile phone,
                        Mirrorless camera),
                        "environment_realism": string (e.g., Lived-in space,
                        Sterile studio)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_sfv_adaptation_high",
          name="Short Form Video Adaptation",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Quantifies the 'Native Emulation' of the production. Measures
                how effectively
                the video mimics organic social content through lo-fi
                aesthetics, handheld
                camera physics, and non-commercial editing patterns.
            """,
          prompt_template="""
                Act as a Social Media Trends Analyst and Video Strategist.
                Your goal is to quantify the 'UGC Authenticity' of the
                production
                style.

                VIDEO METADATA: {metadata_summary}

                ### 1. PRODUCTION MARKERS (for reference):
                    - Native/Lo-Fi: Handheld jitter, natural ambient lighting,
                      mobile sensor resolution, face-to-lens intimacy.
                    - Studio-Hybrid: Vertical framing and casual tone but with
                      professional lighting or stabilized movement.
                    - Commercial/Glossy: Cinema lenses, 3-point lighting,
                      professional color grading, or traditional ad pacing.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present
                    in the video, based on:
                       - how clearly you can identify the native/organic style
                         markers (regardless of duration). Otherwise set to
                         False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of shots that appear
                          native/organic) / (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on the Authenticity Rating (0.0 to 1.0).
                          1.0 =
                          Indistinguishable from an organic user post; 0.5 =
                          Studio-Hybrid; 0.0 = Traditional commercial.
                        - Score from 0.0 to 1.0 reflecting effectiveness in
                          sounding/looking native.
                    5. Rationale & Evidence: Cite specific timestamps and
                    style types.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "camera_stability": string (e.g., Handheld jitter,
                        Smooth mobile),
                        "lighting_type": string (e.g., Natural ambient,
                        Softbox),
                        "edit_style": string (e.g., Jump cuts,
                        Platform-native, Traditional)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_emoji_usage",
          name="Emoji Usage",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Detects intentional creative emoji use: 1. Standard characters
                in text,
                2. Animated effects, 3. Emoji-style stickers/graphics,
                4. Platform-specific features. Excludes incidental background
                captures.
            """,
          prompt_template="""
                Act as a Visual Researcher and Social Media Analyst. Your goal
                is to
                identify and quantify the use of emojis as creative overlays.

                VIDEO METADATA: {metadata_summary}

                ### 1. EMOJI TYPES (for reference):
                    - Standard: Unicode emoji characters within text overlays.
                    - Animated: Emojis that pop, shake, or move.
                    - Stickers: Large, graphical emoji-style elements or
                      platform-native stickers.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly you can identify emojis as intentional
                         creative overlays
                       - whether they are clearly identifiable (regardless of
                         duration). Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Sum of seconds with visible emojis) /
                          (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on Relevance (do they match the
                          tone/content?) and
                          Placement (avoiding dead zones).
                        - Score from 0.0 to 1.0 reflecting effectiveness.
                    5. Rationale & Evidence: Cite specific timestamps and
                    emoji types used.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "emoji_count_estimate": int (Estimated number of
                        emojis used),
                        "style": string (e.g., Standard, Animated, Sticker),
                        "placement": string (e.g., Safe zone, Center, Edge),
                        "primary_purpose": string (e.g., Emphasis, Humor,
                        Aesthetic)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_personal_character_talk",
          name="Direct to Camera Character Talk",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Evaluates the intimacy and continuity of direct lens address.
                Measures the 'Breaking of the Fourth Wall' through gaze and
                conversational delivery.
            """,
          prompt_template="""
                Act as a Cinematographer and Parasocial Interaction
                Specialist.
                Evaluate: How effectively does the character connect with the
                viewer
                via direct lens address?

                VIDEO METADATA: {metadata_summary}

                ### 1. SCORE DIMENSIONS (for reference):
                    - GAZE CONTINUITY & INTENSITY (45% weight): Eyes locked on
                      lens, "FaceTime" feel.
                    - DELIVERY INTIMACY (30% weight): Casual, peer-to-peer
                      tone.
                    - TEMPORAL DOMINANCE (25% weight): How much of the
                      narrative is led by direct address.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the character is identifiable as
                         addressing the lens (regardless of duration).
                         Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of direct lens address) / (Total
                          video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Score each of the three dimensions in Step 1 from 0
                          to 100.
                        - Calculate the weighted total: `(Gaze Continuity *
                          0.45) +
                          (Delivery Intimacy * 0.30) + (Temporal Dominance *
                          0.25)`.
                        - Divide the weighted total by 100 to get the final
                          `feature_quality_score` as a float between 0.0 and
                          1.0.
                    5. Rationale & Evidence: Cite specific timestamps and
                    character
                       actions supporting the scores.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "gaze_consistency": string (e.g., Consistent,
                        Intermittent, Rare),
                        "delivery_style": string (e.g., Conversational,
                        Scripted, Dynamic),
                        "gaze_intensity_score": int (Score for intensity of
                        gaze from 0 to 100),
                        "delivery_intimacy_score": int (Score for intimacy of
                        delivery from 0 to 100)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_native_brand_context",
          name="Brand Secondary Element",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Evaluates if the brand is positioned as a secondary, natural
                element.
                High scores indicate the brand is positioned as a secondary
                element and feels like part of the environment,
                not a forced ad.
            """,
          prompt_template="""
                Act as a Brand Integration Analyst.
                Evaluate: Is the brand naturally secondary within the organic
                content?

                VIDEO METADATA:
                {metadata_summary}

                ### 1. SCORE DIMENSIONS (for reference):
                    - NARRATIVE INTEGRATION (40% weight): Brand exists as a
                      natural prop or mention.
                    - VISUAL SUBTLETY (35% weight): Positioned to avoid "Ad
                      Blindness".
                    - CONTEXTUAL RELEVANCE (25% weight): Fits the "Lived-in"
                      environment.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly the brand is identifiable (regardless of
                         duration). Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of brand visibility) / (Total
                          video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Score each of the three dimensions in Step 1 from 0
                          to 100.
                        - Calculate the weighted total: `(Narrative
                          Integration * 0.40) +
                          (Visual Subtlety * 0.35) + (Contextual Relevance *
                          0.25)`.
                        - Divide the weighted total by 100 to get the final
                          `feature_quality_score` as a float between 0.0 and
                          1.0.
                    5. Rationale & Evidence: Cite specific timestamps and
                    visual cues.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "integration_method": string (e.g., Prop, Mention,
                        Background),
                        "narrative_score": int (Score for narrative
                        integration from 0 to 100),
                        "visual_subtle_score": int (Score for visual subtlety
                        from 0 to 100),
                        "context_score": int (Score for contextual relevance
                        from 0 to 100)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_personal_character_type",
          name="Everyday Persona Validation",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Determines if the video is led by a relatable 'everyday
                person' or creator.
                Returns negative if the character is a professional actor,
                celebrity,
                or fictional/animated entity.
            """,
          prompt_template="""
                Evaluate if the primary character in this ad is an 'Everyday
                Person'.

                VIDEO METADATA: {metadata_summary}

                ### 1. DEFINITION (for reference):
                    An 'Everyday Person' is an organic creator or real user
                    who feels
                    unpolished and relatable. This feature is FALSE if the
                    person is a
                    professional actor, a famous celebrity, or a fictional
                    character.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video AND `is_everyday_person`
                    is True, based on:
                       - how clearly you can identify the character type
                         (regardless of duration). Otherwise set to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration of everyday person on screen) /
                          (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Base score on Authenticity Rating (0.0 to 1.0). 1.0
                          =
                          Indistinguishable from an organic user; 0.0 =
                          Obvious professional actor.
                        - Score from 0.0 to 1.0 reflecting effectiveness in
                          looking authentic.
                    5. Rationale & Evidence: Cite specific timestamps and
                    reasons.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "is_everyday_person": boolean (True if character feels
                        like an everyday person),
                        "is_commercial_actor": boolean (True if character
                        appears to be a professional actor),
                        "is_celebrity": boolean (True if character is a known
                        celebrity),
                        "is_fictional_mascot": boolean (True if character is a
                        fictional entity or mascot)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_product_context",
          name="Secondary Product Context",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Evaluates if the product is positioned as a secondary element
                rather than the main focus of the ad,
                appearing in a natural and realistic context.
            """,
          prompt_template="""
                Act as a Product Stylist and Video Analyst.
                Evaluate: Is the product used naturally as a secondary element
                in a realistic context?

                VIDEO METADATA:
                {metadata_summary}

                ### 1. SCORE DIMENSIONS (for reference):
                    - PRACTICAL UTILITY (45% weight): Product used for its
                      actual purpose naturally.
                    - ENVIRONMENTAL REALISM (30% weight): Messy, real-world
                      environment.
                    - VISUAL WEIGHT (25% weight): Product occupies <20% of
                      frame while in use.

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly you can identify the product being used
                         as a secondary, contextual element. Otherwise set to
                         False.
                    2. Set `detected_confidence_score`: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Calculate feature_density_score:
                        - Formula: (Duration where product is a secondary
                          element) / (Total video duration)
                        - Returns a raw float value between 0.0 and 1.0.
                    4. Calculate feature_quality_score:
                        - Score each of the three dimensions in Step 1 from 0
                          to 100.
                        - Calculate the weighted total: `(Practical Utility *
                          0.45) +
                          (Environmental Realism * 0.30) + (Visual Weight *
                          0.25)`.
                        - Divide the weighted total by 100 to get the final
                          `feature_quality_score` as a float between 0.0 and
                          1.0.
                    5. Rationale & Evidence: Cite specific timestamps and
                    contexts
                       supporting the scores.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "usage_type": string (e.g., Active use, Passive
                        placement),
                        "environment_type": string (e.g., Real-world,
                        Studio-like),
                        "utility_score": int (Score for practical utility from
                        0 to 100),
                        "realism_score": int (Score for environmental realism
                        from 0 to 100),
                        "visual_weight_score": int (Score for visual weight
                        from 0 to 100)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
      models.VideoFeature(
          id="shorts_video_format",
          name="Vertical Format Designed For Mobile",
          category=models.VideoFeatureCategory.SHORTS,
          sub_category=models.VideoFeatureSubCategory.NONE,
          video_segment=models.VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Verifies 9:16 portrait ratio and detects
                letterboxing/pillarboxing.
            """,
          prompt_template="""
                Verify if the video is optimized for mobile (9:16).

                VIDEO METADATA:
                {metadata_summary}

                ### 1. SCORE MAPPING (for reference):
                    - feature_density_score: 1.0 (True 9:16), 0.5
                      (Letterboxed/Square),
                      0.0 (Horizontal).

                ### 2. EVALUATION LOGIC:
                    1. Detection Decision: Set `detected` to True if the
                    feature is present in the video, based on:
                       - how clearly you can determine the aspect ratio
                       - how clearly you can determine the presence of
                         letterboxing (regardless of duration). Otherwise set
                         to False.
                    2. Set detected_confidence_score: Score from 0.0 to 1.0
                    reflecting your confidence in your final detected
                    decision.
                    3. Set feature_density_score: Based on the format (1.0 for
                    9:16,
                       0.5 for square/letterboxed, 0.0 for horizontal).
                    4. Calculate feature_quality_score:
                        - 1.0 if the video is True 9:16 AND compliant with the
                          Mobile
                          Safe Zone (no key content cut off by UI).
                        - 0.5 if True 9:16 but violates Safe Zone.
                        - 0.0 if not optimized for vertical viewing.
                    5. Rationale & Evidence: Cite the aspect ratio and
                    presence of
                       letterboxing.
            """
                + BASE_RESPONSE_FORMAT.format(
                    specifics="""
                        "format": string (e.g., 9:16, Square, Horizontal),
                        "is_letterboxed": boolean (True if letterboxing or
                        pillarboxing is present),
                        "safe_zone_compliant": boolean (True if key content
                        avoids UI dead zones)""",
          ),
          extra_instructions=[],
          evaluation_method=models.EvaluationMethod.GEMINI,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=models.VideoSegment.FULL_VIDEO,
      ),
  ]

  return feature_configs
