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

"""Module with the supported ABCD feature configurations for Shorts"""


from models import (
    VideoFeature,
    VideoSegment,
    EvaluationMethod,
    VideoFeatureCategory,
    VideoFeatureSubCategory,
)


def get_shorts_feature_configs() -> list[VideoFeature]:
  """Gets all the supported ABCD/Shorts features
  
  Returns original shorts features PLUS new organized ABCD features
  (Attract, Brand, Connect, Direct, Other)
  
  Returns:
    feature_configs: list of feature configurations
  """
  # Get original shorts features
  feature_configs = [
      
      
    VideoFeature(
    id="tight_framing_index",
    name="Tight Framing & Visual Dominance",
    category=VideoFeatureCategory.SHORTS,
    sub_category=VideoFeatureSubCategory.ATTRACT,
    video_segment=VideoSegment.FULL_VIDEO,
    evaluation_criteria="""
        Quantifies the spatial dominance of the primary subject. 
        Tight framing is defined by a Subject-to-Frame Ratio (SfR) of ≥65%.
        The score should reflect the persistence of tight framing throughout 
        the video duration, distinguishing between 'momentary' and 'thematic' tight framing.
    """,
    prompt_template="""
        Act as a professional Cinematographer and Video Analyst. Your goal is to measure 
        'Visual Weight' through Tight Framing detection.

        VIDEO METADATA: {metadata_summary}

        ### 1. QUANTITATIVE HEURISTICS:
        - **Extreme Close-Up (ECU):** Subject fills >80% of frame. (High Impact)
        - **Close-Up (CU):** Subject fills 60% - 80% of frame. (Standard Tight)
        - **Medium Shot (MS):** Subject fills 30% - 59% of frame. (Not Tight)
        - **Wide/Long Shot (LS):** Subject fills <30% of frame. (Loose)

        ### 2. TEMPORAL DENSITY CALCULATION:
        Don't just detect if it exists. Calculate the "Tight Framing Density":
        (Total seconds of CU or ECU shots) / (Total video duration) = Density Score
        
        this Density Score, referred to as feature_quality_score below, is crucial for assessing this feature's contribution 
        to overall impact and will be used in the final scoring logic below.

        ### 3. DYNAMIC SCORING (0.0 - 1.0):
        - **0.9 - 1.0 (Dominant):** Density > 70%. Subject is the constant focal point.
        - **0.7 - 0.8 (Strong):** Density 40-70%. Clear alternation between context and tight focus.
        - **0.4 - 0.6 (Balanced):** Density 20-40%. Mixed framing; used for emphasis only.
        - **0.1 - 0.3 (Incidental):** Single brief shot or macro-cutaway.
        - **0.0:** Entirely wide or medium shots.

        ### FORMAT RESPONSE AS JSON:
        {{
            "detected": boolean,
            "confidence_score": float, # Certainty of detected presence (0.0 - 1.0)
            "feature_quality_score": float, # Calculated from above
            "metrics": {{
                "tight_framing_density": float, # Percentage of total runtime that is tight-framed
                "peak_sfr_percentage": float, # The highest Subject-to-Frame ratio observed
                "primary_subject_class": str, # "Product", "Human_Face", "Text", "Abstract"
                "framing_cadence": str # "Static", "Fast-Cutting", "Zoom-In-Progressive"
            }},
            "spatial_analysis": {{
                "average_negative_space_ratio": float, # 1.0 - SfR
                "edge_collision": boolean, # Does the subject bleed off the edges? (Indicates very tight framing)
                "occlusion_level": "None" | "Partial" | "Heavy"
            }},
            "temporal_segments": [
                {{
                    "start": float,
                    "end": float,
                    "shot_type": "ECU" | "CU",
                    "subject_dominance_score": float # 0.0 to 1.0 for this specific segment
                }}
            ],
            "overall_assessment": {{
                "visual_impact_score": float, # How effective is the framing for mobile viewing?
                "summary": "Concise technical summary of framing strategy"
            }}
        }}

        ### EVALUATION LOGIC:
        - Prioritize the "Hook" (first 5 seconds). If the hook is tight-framed, increase the impact score.
        - Ignore "Negative Space" if it is pure solid color (like a graphic background), focus on the Subject's bounding box.
    """,
        extra_instructions=[],
        evaluation_method=EvaluationMethod.LLMS,
        evaluation_function="",
        include_in_evaluation=True,
        group_by=VideoSegment.FULL_VIDEO
        
    )
      
    # VideoFeature(
    #     id="shorts_product_context",
    #     name="Product Context",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Evaluates the "Show, Don't Tell" quality of the ad. The product/service must be 
    #         actively used or interacted with by a person in a realistic, relatable context 
    #         that demonstrates its practical utility or value proposition naturally.
    #         """,
    #     prompt_template="""
    #         Analyze the video to determine if the product/service is used realistically 
    #         to solve a problem or enhance a moment.

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. INTERACTION DEPTH (40%)
    #         - Focus: Physical contact and active engagement.
    #         - Criteria: Is the product being handled, worn, consumed, or operated?
    #         - 90-100: Detailed, multi-step interaction or sustained use (>4s).
    #         - 70-89: Clear physical interaction but brief (2-4s).
    #         - 0-69: Minimal touching or product is merely a prop in the frame.

    #         2. CONTEXTUAL REALISM (30%)
    #         - Focus: The "Where" and "Who". 
    #         - Criteria: Is the environment a "lived-in" space (home, gym, office) vs. a sterile studio? 
    #         - 90-100: Authentic daily-life setting with natural lighting and relatable user behavior.
    #         - 70-89: Recognizable setting but feels slightly "staged" or over-polished.
    #         - 0-69: Infomercial style, white backgrounds, or disconnected from reality.

    #         3. UTILITY DEMONSTRATION (30%)
    #         - Focus: The "Why".
    #         - Criteria: Does the interaction show the product's purpose/benefit without needing a voiceover?
    #         - 90-100: The usage clearly solves a pain point or achieves a goal (e.g., thirst quenched, app task finished).
    #         - 70-89: Product is used correctly but the "benefit" is implied rather than obvious.
    #         - 0-69: Random interaction that doesn't showcase what the product actually does.

    #         FINAL CALCULATION:
    #         Overall Score = (Interaction * 0.4) + (Realism * 0.3) + (Utility * 0.3)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "interaction_depth": {{
    #                     "score": int,
    #                     "action_type": "physical|consumption|digital|service",
    #                     "duration": float,
    #                     "evidence": str
    #                 }},
    #                 "contextual_realism": {{
    #                     "score": int,
    #                     "environment": str,
    #                     "authenticity_level": "natural|staged|studio",
    #                     "observation": str
    #                 }},
    #                 "utility_demo": {{
    #                     "score": int,
    #                     "benefit_shown": str,
    #                     "clarity": "explicit|implicit|none"
    #                 }},
    #                 "final_scoring": {{
    #                     "interaction_weighted": float,
    #                     "realism_weighted": float,
    #                     "utility_weighted": float,
    #                     "total_score": float # Sum of the three weighted scores above
    #                 }}
    #             }}
    #         }}

    #         SCORING GUIDANCE:
    #         - HIGH (80+): A "Day-in-the-life" feel. User solves a problem using the product in a real room.
    #         - MED (50-79): Product is used, but it feels like a "commercial." Correct use, but overly scripted.
    #         - LOW (<50): Product is just sitting there, or being held like a trophy for the camera.
    #         """,
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO
    # ),
    
    # VideoFeature(
    #     id="relevant_call_to_action",
    #     name="Relevant Call-To-Action",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         A 'Call To Action' phrase is heard or mentioned in the audio or speech at any time in the video.
    #     """,
    #     prompt_template="""
    #         Is any call to action heard or mentioned in the speech of the video?
    #     """,
    #     extra_instructions=[
    #         "Consider the following criteria for your answer: {criteria}",
    #         "Some examples of call to actions are: {call_to_actions}",
    #         (
    #             "Provide the exact timestamp when the call to actions are"
    #             " heard or mentioned in the speech of the video."
    #         ),
    #     ],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),
    
    # VideoFeature(
    #     id="call_to_action_text",
    #     name="Call To Action (Text)",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         A 'Call To Action' phrase is detected in the video supers (overlaid text) at any time in the video.
    #     """,
    #     prompt_template="""
    #         Is any call to action detected in any text overlay at any time in the video?
    #     """,
    #     extra_instructions=[
    #         "Consider the following criteria for your answer: {criteria}",
    #         "Some examples of call to actions are: {call_to_actions}",
    #         (
    #             "Look through each frame in the video carefully and answer"
    #             " the question."
    #         ),
    #         (
    #             "Provide the exact timestamp when the call to action is"
    #             " detected in any text overlay in the video."
    #         ),
    #     ],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),
    
    # VideoFeature(
    #     id="sound_effects",
    #     name="Sound Effects",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Strategic sound effects enhance the video through impactful audio cues such as
    #         revving engine, can opening, crunching sounds, water splashing, door closing,
    #         fingers snapping, or bottle opening. Excludes background music or ambient sounds.
    #         """,
    #     prompt_template="""
    #         Evaluate: Are SOUND EFFECTS (distinct, intentional audio cues) used?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON TWO DIMENSIONS (0-100 each):

    #         1. PRESENCE (60% weight)
    #            Are there sound effects (not music/speech)?
    #            - 90-100: Clear, distinct sound effects present
    #            - 70-89: Sound effects present, somewhat clear
    #            - 50-69: Subtle sound effects, hard to distinguish
    #            - 0-49: No sound effects

    #         2. RELEVANCE (40% weight)
    #            Do sound effects enhance the product/emotion?
    #            - 90-100: Directly enhance product action/emotion
    #            - 70-89: Mostly relevant to content
    #            - 50-69: Generic or loosely connected
    #            - 0-49: Distracting or irrelevant

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "sfx_present": boolean,
    #                 "sfx_types": [str],
    #                 "presence_score": int,
    #                 "relevance_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="heartbeat_story_arc",
    #     name="Heartbeat Story Arc",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Video contains compelling moments that capture viewer attention: key message revealed,
    #         strong visual tease, narrative hook, or conclusion/resolution shown early.
    #         """,
    #     prompt_template="""
    #         Evaluate: Does video contain compelling HEARTBEAT MOMENTS?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON FOUR DIMENSIONS (0-100 each):

    #         1. STRONG VISUAL TEASE (30% weight)
    #            Striking visual moment, product reveal, scene change, before/after, motion
    #            - 90-100: Highly compelling visual moment
    #            - 70-89: Clear visual appeal, attention-grabbing
    #            - 50-69: Some visual interest present
    #            - 0-49: No visual tease

    #         2. NARRATIVE HOOK (30% weight)
    #            Question posed, mystery, challenge, curiosity gap, or call to action
    #            - 90-100: Strong hook that demands answer/action
    #            - 70-89: Clear narrative hook present
    #            - 50-69: Weak hook, mild curiosity created
    #            - 0-49: No narrative hook

    #         3. KEY MESSAGE REVEALED (25% weight)
    #            Important benefit stated, punchline, emotional statement, or problem intro
    #            - 90-100: Clear key message with impact
    #            - 70-89: Message present and clear
    #            - 50-69: Message stated but unclear
    #            - 0-49: No clear key message

    #         4. CONCLUSION/RESOLUTION (15% weight)
    #            Story conclusion, result revealed, transformation shown, or climax
    #            - 90-100: Strong resolution shown early
    #            - 70-89: Clear resolution present
    #            - 50-69: Partial resolution shown
    #            - 0-49: No resolution

    #         FINAL CALCULATION:
    #         Overall Score = (Visual × 0.30) + (Hook × 0.30) + (Message × 0.25) + (Resolution × 0.15)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "visual_tease_score": int,
    #                 "narrative_hook_score": int,
    #                 "key_message_score": int,
    #                 "resolution_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="delight",
    #     name="Delight",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Video creates surprising moment of joy, humor, or unexpected positive outcome.
    #         """,
    #     prompt_template="""
    #         Evaluate: Does the video create a DELIGHT moment?

    #         BRAND/PRODUCT: {brand} - {product}
    #         VIDEO: {metadata_summary}

    #         SCORE ON TWO DIMENSIONS (0-100 each):

    #         1. NOVELTY/SURPRISE (60% weight)
    #            Unexpected twist, clever reveal, or surprising moment
    #            - 90-100: Strong surprise or unexpected moment
    #            - 70-89: Some novelty present
    #            - 50-69: Mildly interesting but predictable
    #            - 0-49: Boring or expected

    #         2. POSITIVE EMOTION (40% weight)
    #            Creates joy, delight, laughter, or satisfaction
    #            - 90-100: Strong positive emotional response
    #            - 70-89: Clear positive feeling
    #            - 50-69: Mild positive emotion
    #            - 0-49: No positive response

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "delight_type": str,
    #                 "novelty_level": str,
    #                 "novelty_score": int,
    #                 "emotion_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="large_supers",
    #     name="Large Supers",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Text overlays (supers) are incorporated into the video and match or support the spoken audio.
    #         Speech and text should be synchronized and work together to reinforce the message.
    #         """,
    #     prompt_template="""
    #         Evaluate: Do SUPERS (text overlays) match or support the AUDIO?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON FOUR DIMENSIONS (0-100 each):

    #         1. DIRECT MATCH (30% weight)
    #            Text overlay contains exact or nearly exact words being spoken
    #            - 90-100: Text and speech use identical or nearly identical wording
    #            - 70-89: Most of the spoken words match the text
    #            - 50-69: Partial match between text and speech
    #            - 0-49: No direct match between text and speech

    #         2. CONTEXTUAL SUPPORT (25% weight)
    #            Text reinforces, summarizes, or elaborates on spoken content
    #            - 90-100: Text strongly reinforces/elaborates on speech thematically
    #            - 70-89: Text mostly supports the spoken message
    #            - 50-69: Text loosely related to speech
    #            - 0-49: Text contradicts or unrelated to speech

    #         3. TIMING & SYNC (25% weight)
    #            Text appears when relevant audio is spoken, stays on-screen during speech
    #            - 90-100: Perfect synchronization between text and speech timing
    #            - 70-89: Mostly synchronized, minor timing gaps
    #            - 50-69: Some synchronization, noticeable timing issues
    #            - 0-49: Poor or no synchronization

    #         4. COMMUNICATION EFFECTIVENESS (20% weight)
    #            Dual reinforcement strengthens message, improves clarity and retention
    #            - 90-100: Excellent multi-sensory reinforcement, enhanced clarity
    #            - 70-89: Good reinforcement, clear benefit to message
    #            - 50-69: Moderate reinforcement
    #            - 0-49: No additional benefit from dual presentation

    #         FINAL CALCULATION:
    #         Overall Score = (DirectMatch × 0.30) + (Contextual × 0.25) + (Timing × 0.25) + (Effectiveness × 0.20)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "supers_present": boolean,
    #                 "direct_match_score": int,
    #                 "contextual_support_score": int,
    #                 "timing_sync_score": int,
    #                 "effectiveness_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="emotions",
    #     name="Emotions",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Video evokes emotional connection - joy, humor, inspiration, aspiration, or relatability.
    #         """,
    #     prompt_template="""
    #         Evaluate: Does the video evoke EMOTIONAL CONNECTION?

    #         BRAND/PRODUCT: {brand} - {product}
    #         VIDEO: {metadata_summary}

    #         SCORE ON TWO DIMENSIONS (0-100 each):

    #         1. EMOTIONAL PRESENCE (70% weight)
    #            Strong emotion present (joy, humor, inspiration, aspiration)
    #            - 90-100: Strong clear emotion
    #            - 70-89: Clear emotion present
    #            - 50-69: Mild emotion
    #            - 0-49: Flat, no emotion

    #         2. AUTHENTICITY (30% weight)
    #            Genuine, relatable emotion vs artificial/forced
    #            - 90-100: Genuine, relatable emotion
    #            - 70-89: Mostly authentic
    #            - 50-69: Somewhat forced
    #            - 0-49: Artificial/manipulative

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "emotion_type": str,
    #                 "authenticity": str,
    #                 "presence_score": int,
    #                 "authenticity_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="path_to_purchase",
    #     name="Path to Purchase",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Video shows specific purchase methods and provides clear instructions on how and where to buy.
    #         Examples: website shown, store location indicated, QR code/link provided, app mentioned, or phone number displayed.
    #         """,
    #     prompt_template="""
    #         Evaluate: Does video show HOW and WHERE to purchase?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON TWO DIMENSIONS (0-100 each):

    #         1. PURCHASE METHODS (60% weight)
    #            Specific purchase channels shown (website, store, QR code, app, phone number)
    #            - 90-100: Multiple purchase methods shown (2+ types)
    #            - 70-89: Clear purchase method shown (website, store location, app, etc.)
    #            - 50-69: One purchase method visible but unclear
    #            - 0-49: No purchase method shown

    #         2. CLARITY (40% weight)
    #            How to purchase explained, where to go indicated, clear instructions provided
    #            - 90-100: Crystal clear instructions on how/where to purchase
    #            - 70-89: Mostly clear directions provided
    #            - 50-69: Some indication of where/how but somewhat unclear
    #            - 0-49: Confusing or no clear purchase instructions

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "purchase_methods": [str],
    #                 "methods_count": int,
    #                 "method_clarity": str,
    #                 "methods_score": int,
    #                 "clarity_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="purchase_incentive",
    #     name="Purchase Incentive (Limited Time/Quantities)",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Video communicates limited-time offer, limited quantities, or scarcity to create urgency.
    #         Evaluates presence of time limits, quantity limits, and effectiveness of delivery medium.
    #         """,
    #     prompt_template="""
    #         Evaluate: Is there a PURCHASE INCENTIVE (limited time/quantity)?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. TIME LIMIT PRESENCE (35% weight)
    #            Specific time-based scarcity indicators mentioned
    #            Look for: "Today only", "Limited time", "Deadline mentioned", "Expiration date", "24-hour offer"
    #            - 90-100: Clear time limit with specific deadline (e.g., "ends today", "48-hour offer")
    #            - 70-89: Time limit mentioned, reasonably specific
    #            - 50-69: Time pressure implied but vague
    #            - 0-49: No time limit mentioned

    #         2. QUANTITY LIMIT PRESENCE (35% weight)
    #            Specific quantity-based scarcity indicators mentioned
    #            Look for: "Limited quantities", "While supplies last", "Stock limited", "Exclusive availability"
    #            - 90-100: Clear quantity limit with specific numbers/scarcity (e.g., "only 100 left")
    #            - 70-89: Quantity limit mentioned, clear scarcity implied
    #            - 50-69: Quantity constraint implied but vague
    #            - 0-49: No quantity limit mentioned

    #         3. DELIVERY MEDIUM STRENGTH (30% weight)
    #            Effectiveness of how incentive is communicated
    #            Channels: Text supers (on-screen), Voice-over (audio), Dialogue (character speech)
    #            - 90-100: Multiple delivery methods or highly prominent single method
    #            - 70-89: Clear delivery through one strong medium (e.g., large text, emphasized voiceover)
    #            - 50-69: Present but subtle delivery
    #            - 0-49: Poorly delivered or hard to notice

    #         FINAL CALCULATION:
    #         Overall Score = (TimeLimit × 0.35) + (QuantityLimit × 0.35) + (DeliveryStrength × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "time_limit_present": boolean,
    #                 "time_limit_type": str,
    #                 "quantity_limit_present": boolean,
    #                 "quantity_limit_type": str,
    #                 "delivery_medium": [str],
    #                 "time_limit_score": int,
    #                 "quantity_limit_score": int,
    #                 "delivery_strength_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="character_driven",
    #     name="Character-Driven",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Video features a relatable character whose journey or transformation resonates with audience.
    #         Evaluates character prominence, relatability, and narrative journey shown.
    #         """,
    #     prompt_template="""
    #         Evaluate: Is the video CHARACTER-DRIVEN and relatable?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. CHARACTER PROMINENCE (40% weight)
    #            Character is clear protagonist with distinct personality/role
    #            Look for: Clear lead character, distinct personality traits, on-screen presence
    #            - 90-100: Strong, well-developed protagonist
    #            - 70-89: Clear character with distinct personality
    #            - 50-69: Character present but underdeveloped
    #            - 0-49: No clear character focus

    #         2. CHARACTER JOURNEY/TRANSFORMATION (30% weight)
    #            Character shows visible journey, change, or problem-solving
    #            Look for: Before/after transformation, challenge faced, goal achieved, emotional arc
    #            - 90-100: Clear narrative journey with visible transformation
    #            - 70-89: Character shows clear journey or growth
    #            - 50-69: Some journey element but subtle
    #            - 0-49: No journey or transformation shown

    #         3. AUDIENCE RELATABILITY (30% weight)
    #            Character is relatable to target audience (emotional, realistic, authentic)
    #            Look for: Authentic emotion, realistic situation, audience alignment, genuine engagement
    #            - 90-100: Highly relatable, authentic emotion
    #            - 70-89: Mostly relatable character
    #            - 50-69: Somewhat relatable
    #            - 0-49: Not relatable or inauthentic

    #         FINAL CALCULATION:
    #         Overall Score = (Prominence × 0.40) + (Journey × 0.30) + (Relatability × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "character_present": boolean,
    #                 "character_type": str,
    #                 "personality_traits": [str],
    #                 "journey_type": str,
    #                 "prominence_score": int,
    #                 "journey_score": int,
    #                 "relatability_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="special_offer_speech",
    #     name="Special Offer (Speech)",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Audio/voiceover explicitly announces special offer, discount, or deal.
    #         Evaluates clarity of offer type, specific details mentioned, and delivery emphasis.
    #         """,
    #     prompt_template="""
    #         Evaluate: Is there a SPECIAL OFFER announced in speech?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. OFFER TYPE CLARITY (40% weight)
    #            Clear announcement of what offer is (discount %, deal, promotion type)
    #            Look for: "20% off", "Free with purchase", "Buy one get one", "Limited time deal"
    #            - 90-100: Very clear offer type with specific details (e.g., "20% off")
    #            - 70-89: Clear offer mentioned with reasonable detail
    #            - 50-69: Offer mentioned but details vague or implied
    #            - 0-49: No offer details in audio

    #         2. DELIVERY EMPHASIS (35% weight)
    #            Strong emphasis given through voice tone, repetition, or prominence
    #            Look for: Emphatic tone, repeated mention, early in spot, vocal excitement
    #            - 90-100: Strong emphasis with enthusiastic delivery
    #            - 70-89: Clear emphasis given in delivery
    #            - 50-69: Mentioned with moderate emphasis
    #            - 0-49: Buried or casual mention

    #         3. OFFER PROMINENCE (25% weight)
    #            Offer featured continuously or at strategic moments in video
    #            Look for: Multiple mentions, mentioned early, highlighted throughout
    #            - 90-100: Prominent throughout, multiple emphatic mentions
    #            - 70-89: Clear prominence in video
    #            - 50-69: Mentioned but not prominent
    #            - 0-49: Single casual mention

    #         FINAL CALCULATION:
    #         Overall Score = (OfferClarity × 0.40) + (Emphasis × 0.35) + (Prominence × 0.25)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "offer_type": str,
    #                 "offer_details": str,
    #                 "delivery_tone": str,
    #                 "mention_count": int,
    #                 "offer_clarity_score": int,
    #                 "emphasis_score": int,
    #                 "prominence_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="supers_see_and_say",
    #     name="Supers (Audio See & Say)",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Text supers reinforce/echo key words or phrases spoken in audio (synchronized captions).
    #         Evaluates timing synchronization, text readability, and message reinforcement.
    #         """,
    #     prompt_template="""
    #         Evaluate: Are SUPERS synchronized with AUDIO (See & Say)?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. TIMING & SYNC (40% weight)
    #            Text overlay appears when relevant audio is spoken, stays on-screen during speech
    #            Look for: Text appears with spoken words, timing matches, duration appropriate
    #            - 90-100: Perfect synchronization between text and audio timing
    #            - 70-89: Mostly synchronized with minor timing gaps
    #            - 50-69: Some synchronization but noticeable timing issues
    #            - 0-49: Poor or no synchronization

    #         2. TEXT READABILITY (30% weight)
    #            Text is clearly visible, easy to read, appropriate size and contrast
    #            Look for: Clear font, good size, high contrast, not obscured
    #            - 90-100: Text very clear and highly readable
    #            - 70-89: Text mostly clear and readable
    #            - 50-69: Text somewhat unclear or hard to read
    #            - 0-49: Hard to read or obscured

    #         3. REINFORCEMENT VALUE (30% weight)
    #            Dual audio-text presentation strengthens message, improves retention
    #            Look for: Text echoes key audio words, reinforces meaning, adds visual clarity
    #            - 90-100: Strong multi-sensory reinforcement, excellent clarity
    #            - 70-89: Good reinforcement of spoken message
    #            - 50-69: Moderate reinforcement
    #            - 0-49: No clear reinforcement benefit

    #         FINAL CALCULATION:
    #         Overall Score = (TimingSync × 0.40) + (Readability × 0.30) + (Reinforcement × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "sync_present": boolean,
    #                 "sync_quality": str,
    #                 "text_samples": [str],
    #                 "readability": str,
    #                 "timing_sync_score": int,
    #                 "readability_score": int,
    #                 "reinforcement_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="supers_audio_augmenting",
    #     name="Supers (Audio Augmenting)",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Text supers add information NOT in audio, expanding/contextualizing the message.
    #         Evaluates information addition, clarity of augmented content, and strategic value.
    #         """,
    #     prompt_template="""
    #         Evaluate: Do SUPERS AUGMENT (add to) the audio message?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. INFORMATION ADDITION (40% weight)
    #            Supers add key details NOT mentioned in audio (price, features, process, benefits)
    #            Look for: Product details, pricing, instructions, specifications, URLs, contact info
    #            - 90-100: Supers add important missing information
    #            - 70-89: Supers add useful additional context
    #            - 50-69: Supers add some complementary information
    #            - 0-49: Supers are redundant or add minimal value

    #         2. CLARITY OF ADDED INFORMATION (35% weight)
    #            Supplemental information is clear, readable, and easy to understand
    #            Look for: Clear font, good size, logical presentation, not overcrowded
    #            - 90-100: Added information very clear and well-presented
    #            - 70-89: Information mostly clear
    #            - 50-69: Information somewhat unclear
    #            - 0-49: Information confusing or hard to parse

    #         3. STRATEGIC VALUE (25% weight)
    #            Added information strategically enhances product understanding or purchase intent
    #            Look for: Information supports purchase decision, clarifies offer, enables action
    #            - 90-100: Strong strategic value, significantly enhances message
    #            - 70-89: Clear strategic benefit
    #            - 50-69: Some strategic value
    #            - 0-49: No clear strategic benefit

    #         FINAL CALCULATION:
    #         Overall Score = (InformationAddition × 0.40) + (Clarity × 0.35) + (StrategicValue × 0.25)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "information_added": str,
    #                 "info_types": [str],
    #                 "information_addition_score": int,
    #                 "clarity_score": int,
    #                 "strategic_value_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="focused_messaging",
    #     name="Focused Messaging",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Video communicates ONE clear core message (not scattered or conflicting messages).
    #         Evaluates message unity, core message clarity, and consistency throughout.
    #         """,
    #     prompt_template="""
    #         Evaluate: Is the messaging FOCUSED on ONE core message?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. MESSAGE UNITY (40% weight)
    #            ONE clear primary message; no competing or contradictory messages
    #            Look for: Single central theme, supporting messages align, no conflicting info
    #            - 90-100: Single, crystal-clear message throughout
    #            - 70-89: Clearly focused on one message
    #            - 50-69: Mostly focused but with some tangential messages
    #            - 0-49: Multiple competing or unclear messages

    #         2. CORE MESSAGE CLARITY (35% weight)
    #            Central message is unmistakably clear and easy to understand
    #            Look for: Explicit statement, obvious benefit, clear value prop
    #            - 90-100: Core message crystal clear
    #            - 70-89: Message is clear and understandable
    #            - 50-69: Message somewhat unclear or implied
    #            - 0-49: Message confusing or unclear

    #         3. MESSAGE CONSISTENCY (25% weight)
    #            Message maintained throughout video without deviation or contradiction
    #            Look for: Consistent theme from start to finish, reinforced throughout
    #            - 90-100: Perfectly consistent throughout
    #            - 70-89: Mostly consistent message
    #            - 50-69: Some inconsistency or mixed messages
    #            - 0-49: Inconsistent or contradictory messaging

    #         FINAL CALCULATION:
    #         Overall Score = (MessageUnity × 0.40) + (Clarity × 0.35) + (Consistency × 0.25)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "core_message": str,
    #                 "message_count": int,
    #                 "supporting_messages": [str],
    #                 "unity_score": int,
    #                 "clarity_score": int,
    #                 "consistency_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="jingle",
    #     name="Jingle",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Memorable musical phrase, brand sound, or sonic signature identifying the brand.
    #         Evaluates presence of sonic brand elements, distinctiveness, and memorability.
    #         """,
    #     prompt_template="""
    #         Evaluate: Is there a memorable JINGLE or sonic brand element?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. SONIC ELEMENT PRESENCE (35% weight)
    #            Clear, distinctive musical phrase or brand sound is present
    #            Look for: Jingle, brand theme, signature sound, sonic logo, memorable tune
    #            - 90-100: Clear, distinctive sonic brand element
    #            - 70-89: Sonic element present and recognizable
    #            - 50-69: Sonic element exists but not very distinctive
    #            - 0-49: No jingle or sonic branding present

    #         2. DISTINCTIVENESS (35% weight)
    #            Sonic element is unique and clearly associated with the brand
    #            Look for: Original composition, brand-specific, stands out from competitors
    #            - 90-100: Highly distinctive, clearly brand-identifiable
    #            - 70-89: Distinctive and recognizable as brand element
    #            - 50-69: Somewhat distinctive but generic
    #            - 0-49: Generic or not distinctive

    #         3. MEMORABILITY (30% weight)
    #            Jingle is catchy and stays with viewer (earns recall)
    #            Look for: Catchiness, repetition, musical appeal, hook quality
    #            - 90-100: Highly catchy and memorable
    #            - 70-89: Fairly memorable and catchy
    #            - 50-69: Somewhat memorable
    #            - 0-49: Not memorable

    #         FINAL CALCULATION:
    #         Overall Score = (Presence × 0.35) + (Distinctiveness × 0.35) + (Memorability × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "jingle_type": str,
    #                 "jingle_description": str,
    #                 "presence_score": int,
    #                 "distinctiveness_score": int,
    #                 "memorability_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="special_offer_text",
    #     name="Special Offer (Text)",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Text overlay explicitly displays discount, deal, or special offer details.
    #         Evaluates text visibility, offer clarity, and visual emphasis/prominence.
    #         """,
    #     prompt_template="""
    #         Evaluate: Is there a SPECIAL OFFER displayed as TEXT?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. TEXT VISIBILITY (35% weight)
    #            Text overlay is clearly visible and readable on-screen
    #            Look for: Good contrast, readable size, not obscured, appropriate duration
    #            - 90-100: Text very clear and highly visible
    #            - 70-89: Offer text clearly visible and readable
    #            - 50-69: Offer text visible but somewhat hard to read
    #            - 0-49: Text not visible or hard to read

    #         2. OFFER CLARITY (35% weight)
    #            Offer details are clear (discount amount, deal type, terms)
    #            Look for: "20% OFF", "Save $10", "Buy One Get One", specific terms
    #            - 90-100: Crystal clear offer with specific details (e.g., "20% OFF")
    #            - 70-89: Clear offer with good detail
    #            - 50-69: Offer shown but details vague
    #            - 0-49: Unclear offer or missing details

    #         3. VISUAL EMPHASIS (30% weight)
    #            Text is bold, large, prominently placed with strong visual hierarchy
    #            Look for: Large font, bold styling, contrasting colors, prime placement
    #            - 90-100: Bold, large, very prominent with strong visual impact
    #            - 70-89: Clearly emphasized with good visibility
    #            - 50-69: Visible but modest emphasis
    #            - 0-49: Buried or barely emphasized

    #         FINAL CALCULATION:
    #         Overall Score = (Visibility × 0.35) + (Clarity × 0.35) + (Emphasis × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "offer_text": str,
    #                 "offer_type": str,
    #                 "text_size": str,
    #                 "visibility_score": int,
    #                 "clarity_score": int,
    #                 "emphasis_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="direct_to_camera",
    #     name="Direct to Camera",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Person looks directly at camera creating direct eye contact and personal connection with viewer.
    #         Evaluates direct address, eye contact quality, and authenticity of delivery.
    #         """,
    #     prompt_template="""
    #         Evaluate: Does anyone speak/look DIRECTLY TO CAMERA?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. DIRECT ADDRESS (40% weight)
    #            Person directly addresses camera, speaks/looks to viewer
    #            Look for: Clear camera address, person speaks to camera, intentional engagement
    #            - 90-100: Clear direct address to camera throughout segment
    #            - 70-89: Direct address with clear camera communication
    #            - 50-69: Some direct address but not consistent
    #            - 0-49: No direct camera address

    #         2. EYE CONTACT QUALITY (30% weight)
    #            Clear, sustained eye contact with camera creates connection
    #            Look for: Direct gaze, sustained eye contact, natural eye contact (not forced)
    #            - 90-100: Strong, sustained eye contact (2+ seconds)
    #            - 70-89: Clear eye contact present
    #            - 50-69: Intermittent or brief eye contact
    #            - 0-49: No eye contact or averted gaze

    #         3. AUTHENTICITY (30% weight)
    #            Delivery feels natural, conversational, and genuine (not scripted/awkward)
    #            Look for: Natural tone, conversational delivery, genuine emotion, comfortable demeanor
    #            - 90-100: Very natural, conversational, authentic delivery
    #            - 70-89: Mostly natural and authentic
    #            - 50-69: Somewhat scripted or slightly awkward
    #            - 0-49: Very scripted or uncomfortable

    #         FINAL CALCULATION:
    #         Overall Score = (DirectAddress × 0.40) + (EyeContact × 0.30) + (Authenticity × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "direct_address_present": boolean,
    #                 "eye_contact_present": boolean,
    #                 "duration_seconds": float,
    #                 "delivery_tone": str,
    #                 "direct_address_score": int,
    #                 "eye_contact_score": int,
    #                 "authenticity_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="high_contrast_visuals",
    #     name="High Contrast Visuals",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Strong visual contrast (color, light/dark, size) makes product/brand stand out.
    #         Evaluates contrast strength, product visibility, and overall visual impact.
    #         """,
    #     prompt_template="""
    #         Evaluate: Are there HIGH CONTRAST VISUALS?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. CONTRAST STRENGTH (40% weight)
    #            Strong visual contrast present (color, light/dark, size differences)
    #            Look for: Bold color combinations, light vs dark, size emphasis, visual separation
    #            - 90-100: Very strong contrast throughout
    #            - 70-89: Clear, noticeable contrast
    #            - 50-69: Some contrast present
    #            - 0-49: Low or minimal contrast

    #         2. PRODUCT VISIBILITY (30% weight)
    #            Product/brand stands out and is easily visible due to contrast
    #            Look for: Product clearly distinct from background, high visibility, easy to spot
    #            - 90-100: Product stands out prominently
    #            - 70-89: Product clearly visible
    #            - 50-69: Product somewhat stands out
    #            - 0-49: Product blends in or hard to see

    #         3. VISUAL IMPACT (30% weight)
    #            Contrast creates strong visual impact and commands viewer attention
    #            Look for: Eye-catching, attention-grabbing, memorable visual effect
    #            - 90-100: Strong visual impact, commands attention
    #            - 70-89: Good visual impact
    #            - 50-69: Mild visual impact
    #            - 0-49: Little to no visual impact

    #         FINAL CALCULATION:
    #         Overall Score = (ContrastStrength × 0.40) + (ProductVisibility × 0.30) + (VisualImpact × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "contrast_types": [str],
    #                 "contrast_strength": str,
    #                 "product_visibility": str,
    #                 "contrast_strength_score": int,
    #                 "visibility_score": int,
    #                 "impact_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # ),

    # VideoFeature(
    #     id="product_mention_speech",
    #     name="Product Mention (Speech)",
    #     category=VideoFeatureCategory.SHORTS,
    #     sub_category=VideoFeatureSubCategory.NONE,
    #     video_segment=VideoSegment.FULL_VIDEO,
    #     evaluation_criteria="""
    #         Product or brand name is verbally mentioned in audio/voiceover.
    #         Evaluates mention presence, clarity of product name, and emphasis in delivery.
    #         """,
    #     prompt_template="""
    #         Evaluate: Is the PRODUCT verbally MENTIONED in audio?

    #         BRAND/PRODUCT CONTEXT:
    #         Brand: {brand} | Product: {product} | Industry: {vertical}

    #         VIDEO METADATA:
    #         {metadata_summary}

    #         SCORE ON THREE DIMENSIONS (0-100 each):

    #         1. MENTION PRESENCE (35% weight)
    #            Product/brand name is audibly mentioned in audio/voiceover
    #            Look for: Clear product name mention, brand name spoken, multiple mentions
    #            - 90-100: Clear, audible mention (multiple times or prominent)
    #            - 70-89: Product clearly mentioned once
    #            - 50-69: Mention exists but somewhat unclear
    #            - 0-49: No mention or inaudible

    #         2. MENTION CLARITY (35% weight)
    #            Product name is clearly spoken/pronounced without ambiguity
    #            Look for: Clear pronunciation, distinct mention, easy to understand
    #            - 90-100: Very clear, distinct product name mention
    #            - 70-89: Clear product name mention
    #            - 50-69: Somewhat unclear or muffled
    #            - 0-49: Unclear, mumbled, or inaudible

    #         3. EMPHASIS & INTEGRATION (30% weight)
    #            Product mention is emphasized and naturally integrated into the message
    #            Look for: Emphatic delivery, prominent placement, natural flow, repeated
    #            - 90-100: Strong emphasis, prominent and natural integration
    #            - 70-89: Clear emphasis given
    #            - 50-69: Mentioned casually, minimal emphasis
    #            - 0-49: Buried or no emphasis

    #         FINAL CALCULATION:
    #         Overall Score = (MentionPresence × 0.35) + (Clarity × 0.35) + (Emphasis × 0.30)

    #         FORMAT RESPONSE AS JSON:
    #         {{
    #             "detected": boolean,
    #             "confidence_score": float,
    #             "evaluation": {{
    #                 "mention_count": int,
    #                 "product_name_mentioned": str,
    #                 "mention_clarity": str,
    #                 "emphasis_level": str,
    #                 "presence_score": int,
    #                 "clarity_score": int,
    #                 "emphasis_score": int,
    #                 "weighted_overall": float
    #             }}
    #         }}""",
    #     extra_instructions=[],
    #     evaluation_method=EvaluationMethod.LLMS,
    #     evaluation_function="",
    #     include_in_evaluation=True,
    #     group_by=VideoSegment.FULL_VIDEO,
    # )

  ]
  
  return feature_configs