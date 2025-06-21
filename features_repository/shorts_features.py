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
    Returns:
    feature_configs: list of feature configurations
    """
    feature_configs = [
        VideoFeature(
            id="shorts_production_style",
            name="Shorts Production Style",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Analyze whether the video uses full studio production or user-generated studio style.
                    Full studio production involves professional equipment, controlled environments, and skilled crews.
                    User-generated studio style mimics authenticity while maintaining some production value,
                    featuring more relaxed and personal presentation despite being filmed in controlled settings.
                """,
            prompt_template="""
                    Analyze the production style of this short-form video.

                    VIDEO METADATA:
                    {metadata_summary}

                    ANALYZE FOR TWO DISTINCT STYLES:
                    1. STUDIO PRODUCTION CHARACTERISTICS:
                        a) Technical Quality:
                            - Professional lighting setup
                            - Multiple camera angles
                            - Perfect focus and exposure
                            - High-end equipment use
                            - Professional audio setup
                        b) Environment Control:
                            - Studio/controlled setting
                            - Professional backdrops
                            - Perfect set arrangement
                            - Controlled lighting
                            - Staged elements
                        c) Performance Elements:
                            - Skilled actors/talent
                            - Polished delivery
                            - Perfect timing
                            - Professional pacing
                            - Scripted presentation
                    2. USER-GENERATED STUDIO CHARACTERISTICS:
                        a) Technical Aspects:
                            - Good but not perfect lighting
                            - Simple camera setups
                            - Basic but clean audio
                            - Mixed equipment quality
                            - Casual but controlled shots
                        b) Environment Elements:
                            - Semi-controlled settings
                            - Personal spaces
                            - Natural arrangements
                            - Mixed lighting styles
                            - Authentic props
                        c) Performance Style:
                            - Natural delivery
                            - Casual pacing
                            - Personal tone
                            - Relaxed timing
                            - Semi-scripted feel

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # TRUE for studio, FALSE for user-gen
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_quality": {{
                                "observed_style": str,  # "Studio" or "User-Generated Studio"
                                "production_elements": [
                                    {{
                                        "element": str,  # What was observed
                                        "type": str,     # "Studio" or "User-Gen"
                                        "timestamp": float,
                                        "confidence": float
                                    }}
                                ],
                                "overall_quality": str  # Description of technical quality
                            }},
                            "environment_analysis": {{
                                "setting_type": str,
                                "control_level": str,
                                "key_elements": [str],
                                "authenticity_markers": [str]
                            }},
                            "performance_assessment": {{
                                "delivery_style": str,
                                "scripting_level": str,
                                "authenticity_score": float,
                                "key_moments": [
                                    {{
                                        "timestamp": float,
                                        "description": str,
                                        "style_indicator": str
                                    }}
                                ]
                            }},
                            "production_markers": {{
                                "studio_elements": [
                                    {{
                                        "type": str,
                                        "description": str,
                                        "timestamp": float
                                    }}
                                ],
                                "user_gen_elements": [
                                    {{
                                        "type": str,
                                        "description": str,
                                        "timestamp": float
                                    }}
                                ]
                            }},
                            "overall_assessment": {{
                                "primary_style": str,
                                "distinguishing_features": [str],
                                "production_level": str,
                                "authenticity_level": str
                            }}
                        }}
                    }}

                    EVALUATION NOTES:
                    1. Technical Quality:
                        - Assess equipment usage
                        - Note production values
                        - Consider consistency
                        - Evaluate polish level
                    2. Environment Control:
                        - Check setting control
                        - Analyze backgrounds
                        - Assess staging
                        - Note authenticity
                    3. Performance Elements:
                        - Evaluate delivery
                        - Check naturality
                        - Assess timing
                        - Note authenticity

                    CONFIDENCE CONSIDERATIONS:
                        - Strong Studio (0.8-1.0): Clear professional production
                        - Moderate Studio (0.6-0.7): Mixed but primarily professional
                        - Strong User-Gen (0.2-0.3): Clear authentic style
                        - Moderate User-Gen (0.4-0.5): Mixed but primarily authentic

                    IMPORTANT NOTES:
                        1. High production quality can exist in both styles
                        2. Focus on intentional authenticity vs polished presentation
                        3. Consider overall feel and consistency
                        4. Look for intentional "casualness" in user-gen studio
                        5. Note mixed elements that may appear in either style
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,  # confirm
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_tv_ad_style",
            name="Shorts TV Ad Style",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Analyze if the short-form video matches traditional TV advertisement style.
                    Consider production quality, editing patterns, and overall composition.
                    TV ad style typically shows professional studio lighting, clean editing,
                    perfect framing, and polished transitions, while natural short-form content
                    often features dynamic editing, casual framing, and trend-based styles.
                """,
            prompt_template="""
                    Analyze if this short-form video matches traditional TV advertisement style.

                    VIDEO METADATA:
                    {metadata_summary}

                    STYLE INDICATORS TO CONSIDER:
                    1. TV AD CHARACTERISTICS:
                        a) Production Quality:
                            - Professional studio lighting
                            - Perfect exposure control
                            - Stable camera movements
                            - Clean, controlled framing
                            - High production polish

                        b) Editing Style:
                            - Traditional commercial pacing
                            - Professional transitions
                            - Perfectly timed cuts
                            - Montage-style sequences
                            - Beauty shots

                        c) Composition:
                            - Formal framing
                            - Perfect subject placement
                            - Professional depth of field
                            - Controlled backgrounds
                            - Strategic visual design

                    2. NATURAL SHORT-FORM STYLE:
                        a) Production Approach:
                            - Natural or mixed lighting
                            - Dynamic camera work
                            - Authentic environments
                            - Casual framing
                            - Real-world settings

                        b) Editing Patterns:
                            - Quick, energetic cuts
                            - Trend-based transitions
                            - Dynamic pacing
                            - Informal sequences
                            - Personal style
                        c) Composition Elements:
                            - Flexible framing
                            - Natural placement
                            - Authentic backgrounds
                            - Personal spaces
                            - Spontaneous layout

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # TRUE if matches TV ad style
                        "confidence_score": float,
                        "evaluation": {{
                            "style_analysis": {{
                                "production_quality": {{
                                    "observed_level": str,
                                    "tv_ad_elements": [str],
                                    "natural_elements": [str],
                                    "confidence": float
                                }},
                                "editing_patterns": {{
                                    "style_type": str,
                                    "tv_ad_markers": [str],
                                    "natural_markers": [str],
                                    "confidence": float
                                }},
                                "composition_elements": {{
                                    "overall_style": str,
                                    "formal_aspects": [str],
                                    "casual_aspects": [str],
                                    "confidence": float
                                }}
                            }},
                            "timestamps": [
                                {{
                                    "time": float,
                                    "element_type": str,
                                    "style_indicator": str,
                                    "description": str
                                }}
                            ],
                            "key_evidence": {{
                                "tv_ad_style": [
                                    {{
                                        "aspect": str,
                                        "evidence": str,
                                        "impact": str
                                    }}
                                ],
                                "natural_style": [
                                    {{
                                        "aspect": str,
                                        "evidence": str,
                                        "impact": str
                                    }}
                                ]
                            }},
                            "overall_assessment": {{
                                "primary_style": str,
                                "style_confidence": float,
                                "distinguishing_features": [str]
                            }}
                        }}
                    }}

                    EVALUATION NOTES:
                    1. Production Quality:
                        - High production ≠ automatically TV style
                        - Consider intentional vs polished
                        - Note lighting and camera work
                        - Assess environment control
                    2. Editing Patterns:
                        - Look for pacing patterns
                        - Note transition styles
                        - Consider timing choices
                        - Evaluate flow and rhythm
                    3. Composition Choices:
                        - Analyze framing decisions
                        - Consider subject placement
                        - Evaluate background control
                        - Note visual hierarchy

                    RESPONSE REQUIREMENTS:
                        1. Clear style categorization
                        2. Specific evidence points
                        3. Detailed timestamps
                        4. Confidence assessment
                        5. Overall style evaluation
            """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,  # confirm
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_sfv_adaptation_low",
            name="Native Content Style_LOW",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Evaluate if the video emulates native, organic shortform video content vs appearing commercial/polished.
                    Videos should feel like authentic social media content with:
                        1. Raw/authentic visual style (natural lighting, minimal editing)
                        2. Casual/conversational audio (natural acoustics, informal speech)
                        3. Personal presentation (direct address, unscripted feel)
                        4. Organic pacing (natural flow, spontaneous moments)

                    Commercial characteristics that reduce native feel include:
                        - Professional production quality
                        - Studio lighting/sound
                        - Heavy editing
                        - Formal presentation
                        - TV commercial-style execution
                """,
            prompt_template="""
            Using both the provided metadata AND your understanding of social media content styles, evaluate how well this video emulates native shortform content.

            BRAND/PRODUCT CONTEXT:
            - Brand: {brand}
            - Product: {product}
            - Industry: {vertical}

            VIDEO METADATA:
            {metadata_summary}

            ANALYZE THESE ASPECTS:
            1. Visual Style:
            a) Native Indicators:
                - Handheld camera work
                - Natural lighting
                - Raw/minimal editing
                - Authentic settings
                - Personal spaces
                - Imperfect framing

            b) Commercial Indicators:
                - Steady camera work
                - Professional lighting
                - Polished editing
                - Studio settings
                - Perfect framing
                - Commercial spaces

            2. Audio Quality:
            a) Native Indicators:
                - Natural acoustics
                - Ambient sound
                - Conversational tone
                - Casual voices
                - Informal speech

            b) Commercial Indicators:
                - Studio sound
                - Clean audio mix
                - Professional voices
                - Scripted delivery
                - Perfect balance

            3. Presentation Style:
            a) Native Indicators:
                - Direct address
                - Personal tone
                - Natural pauses
                - Informal language
                - Authentic reactions

            b) Commercial Indicators:
                - Formal delivery
                - Marketing language
                - Perfect timing
                - Scripted speech
                - Controlled reactions

            4. Content Structure:
            a) Native Indicators:
                - Personal narrative
                - Natural flow
                - Spontaneous moments
                - Creator-style
                - Organic pacing

            b) Commercial Indicators:
                - Brand messaging
                - Planned sequences
                - Staged moments
                - TV commercial style
                - Professional flow

            FORMAT RESPONSE AS JSON:
            {
                "detected": boolean,  # True if predominantly native style
                "confidence_score": float,
                "score": integer between 1-4,
                "evaluation": {
                    "rationale": "detailed explanation",
                    "evidence": [
                        {
                            "aspect": "visual/audio/presentation/content",
                            "native_elements": ["found native style markers"],
                            "commercial_elements": ["found commercial markers"],
                            "dominant_style": "native/commercial",
                            "timestamps": [relevant timestamps]
                        }
                    ],
                    "strengths": ["strongest native elements"],
                    "weaknesses": ["areas appearing commercial"]
                }
            }

            EVALUATION CRITERIA:
            1. Technical Evidence:
            - Visual style markers
            - Audio characteristics
            - Presentation patterns
            - Content structure
            - Timing and pacing

            2. Style Assessment:
            - Balance native vs commercial
            - Authenticity of execution
            - Consistency throughout
            - Overall effectiveness

            3. Scoring Guide:
            4 - Highly authentic native style
            3 - Good native style with some commercial elements
            2 - More commercial with some native elements
            1 - Fully commercial/professional style

            Remember: Focus on distinguishing between authentic native-style content and professionally produced content attempting to appear native.
            """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,  # confirm
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_sfv_adaptation_medium",
            name="SFV Adaptation Balance",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Evaluate if the video achieves an effective balance between professional production and native social content style.
                    Videos should blend polished elements with authentic feel through:
                        1. Production Quality: Well-produced but not overly polished (good lighting/sound while maintaining natural feel)
                        2. Content Style: Professional execution with authentic elements (real scenarios, genuine testimonials)
                        3. Presentation: Balanced formality (polished but personable delivery)
                        4. Authenticity: Strategic inclusion of native content elements (direct address, personal stories)
                    The goal is finding middle ground between high production value and relatable social content.
                """,
            prompt_template="""
                    Using both the provided metadata AND your understanding of balanced content style, evaluate how well
                    this video combines professional and native elements.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    ANALYZE BALANCED EXECUTION:
                    1. Production Elements:
                        a) Professional Components:
                            - Quality lighting
                            - Clear audio
                            - Stable camera work
                            - Good editing
                            - Clean composition
                        b) Natural Elements:
                            - Real locations
                            - Authentic settings
                            - Natural light mix
                            - Dynamic shooting
                            - Environmental sound
                    2. Content Approach:
                        a) Professional Structure:
                            - Clear messaging
                            - Strategic flow
                            - Quality transitions
                            - Focused storytelling
                            - Brand integration
                        b) Authentic Elements:
                            - Real scenarios
                            - Customer stories
                            - Genuine reactions
                            - Natural moments
                            - Personal experiences
                    3. Presentation Style:
                        a) Professional Delivery:
                            - Clear speech
                            - Good pacing
                            - Confident delivery
                            - Quality performance
                            - Structured flow
                        b) Natural Connection:
                            - Direct address
                            - Conversational tone
                            - Personal engagement
                            - Natural enthusiasm
                            - Authentic reactions
                    4. Authenticity Balance:
                        a) Strategic Polish:
                            - Refined moments
                            - Key messaging
                            - Brand standards
                            - Quality control
                            - Professional touch
                        b) Deliberate Authenticity:
                            - Real testimonials
                            - Behind-scenes moments
                            - Candid interactions
                            - Natural dialogue
                            - Genuine emotion

                    FORMAT RESPONSE AS JSON:
                    {
                        "detected": boolean,  # True if balanced style achieved
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {
                            "rationale": "detailed explanation of balance achieved",
                            "evidence": [
                                {
                                    "aspect": "production/content/presentation/authenticity",
                                    "professional_elements": ["polished elements found"],
                                    "authentic_elements": ["native elements found"],
                                    "balance_quality": "how well elements combine",
                                    "timestamps": [relevant timestamps]
                                }
                            ],
                            "strengths": ["successful balance points"],
                            "weaknesses": ["areas needing better balance"]
                        }
                    }

                    EVALUATION CRITERIA:
                    1. Technical Balance:
                    - Production quality level
                    - Authenticity markers
                    - Style integration
                    - Overall execution

                    2. Content Balance:
                    - Message clarity
                    - Natural elements
                    - Flow effectiveness
                    - Authenticity level

                    3. Scoring Guide:
                    4 - Perfect balance of professional and authentic elements
                    3 - Good balance with slight lean toward one style
                    2 - Imbalanced but attempts at combination
                    1 - Too heavily weighted to one extreme

                    Remember: Look for strategic combination of professional quality and authentic elements that creates relatable yet polished content.
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,  # confirm
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_sfv_adaptation_high",
            name="Short Form Video Adaptation_high",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Analyze how well the video adapts to native short form video style versus maintaining
                    traditional commercial production. Low adaptation videos maintain professional and polished
                    commercial style without incorporating platform-native elements, while high adaptation
                    successfully emulates organic social media content.
                """,
            prompt_template="""
                    Analyze whether this video maintains traditional commercial production or successfully adapts to short form style.

                    VIDEO METADATA:
                    {metadata_summary}

                    TWO KEY PRODUCTION STYLES:
                    1. TRADITIONAL COMMERCIAL STYLE (LOW ADAPTATION):
                        a) Production Quality:
                            - Professional studio lighting
                            - Perfect exposure control
                            - Steady camera work
                            - Polished transitions
                            - Commercial-grade audio
                        b) Content Approach:
                            - Standard commercial pacing
                            - Formal presentation
                            - Professional talent
                            - Scripted delivery
                            - Brand-first messaging
                        c) Visual Elements:
                            - Perfect framing
                            - Commercial graphics
                            - Professional effects
                            - Studio environment
                            - Controlled staging
                    2. NATIVE SHORT FORM STYLE (HIGH ADAPTATION):
                        a) Production Elements:
                            - Natural or mixed lighting
                            - Dynamic camera work
                            - Casual transitions
                            - Authentic feel
                            - Raw audio elements
                        b) Content Approach:
                            - Platform-native pacing
                            - Personal presentation
                            - Authentic delivery
                            - Natural moments
                            - Creator-style messaging
                        c) Visual Elements:
                            - Flexible framing
                            - Native graphics/text
                            - Trend-based effects
                            - Real environments
                            - Natural staging

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # TRUE for high adaptation, FALSE for low
                        "confidence_score": float,
                        "evaluation": {{
                            "production_style": {{
                                "observed_level": str,  # "Traditional Commercial" or "Native Short Form"
                                "key_elements": [
                                    {{
                                        "element": str,
                                        "style_type": str,
                                        "timestamp": float,
                                        "description": str
                                    }}
                                ],
                                "overall_quality": str
                            }},
                            "content_approach": {{
                                "presentation_style": str,
                                "delivery_type": str,
                                "authenticity_level": str,
                                "key_moments": [
                                    {{
                                        "timestamp": float,
                                        "description": str,
                                        "style_indicator": str
                                    }}
                                ]
                            }},
                            "visual_elements": {{
                                "framing_style": str,
                                "graphics_type": str,
                                "effects_approach": str,
                                "environment": str,
                                "key_visuals": [str]
                            }},
                            "adaptation_markers": {{
                                "traditional_elements": [
                                    {{
                                        "type": str,
                                        "description": str,
                                        "impact": str
                                    }}
                                ],
                                "native_elements": [
                                    {{
                                        "type": str,
                                        "description": str,
                                        "impact": str
                                    }}
                                ]
                            }},
                            "overall_assessment": {{
                                "adaptation_level": str,  # "High", "Medium", or "Low"
                                "style_balance": str,
                                "authenticity_score": float,
                                "key_observations": [str]
                            }}
                        }}
                    }}

                    EVALUATION NOTES:
                    1. Production Assessment:
                        - Note production quality
                        - Consider intentional style choices
                        - Evaluate overall approach
                        - Assess technical elements
                    2. Content Analysis:
                        - Check presentation style
                        - Evaluate authenticity
                        - Note delivery approach
                        - Consider engagement style
                    3. Visual Elements:
                        - Analyze framing choices
                        - Assess graphics style
                        - Review effects usage
                        - Consider environment

                    CONFIDENCE SCORING:
                        - Clear Commercial (0.0-0.3): Maintains traditional style
                        - Mixed Elements (0.4-0.6): Combines both styles
                        - Platform Native (0.7-1.0): Successfully adapts to platform

                    IMPORTANT CONSIDERATIONS:
                        1. High production doesn't automatically mean low adaptation
                        2. Look for intentional style choices
                        3. Consider platform-specific elements
                        4. Note authenticity markers
                        5. Evaluate overall effectiveness
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,  # confirm
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_emoji_usage",
            name="Emoji Usage",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video use emojis as visual elements? Detection includes:
                    1. Standard emoji characters in text overlays
                    2. Animated emoji effects
                    3. Emoji-style stickers or graphics
                    4. Platform-specific emoji features
                    Emojis must be intentionally added as creative elements, not incidentally captured in screenshots or user content.
                """,
            prompt_template="""
                    Using the provided metadata, analyze for intentional emoji usage in the video.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    EMOJI INDICATORS:
                    1. Visual Elements:
                        - Standard emoji graphics
                        - Animated emoji effects
                        - Emoji-style stickers
                        - Reaction emojis
                        - Decorative emojis
                    2. Text Integration:
                        - Emoji in captions
                        - Text-emoji combinations
                        - Emoji punctuation
                        - Emoji emphasis
                        - Emoji sequences
                    3. Creative Usage:
                    - Transition effects
                    - Reaction overlays
                    - Mood indicators
                    - Visual emphasis
                    - Story elements

                    DETECTION REQUIREMENTS:
                    1. Visual Presence:
                        - Clear emoji display
                        - Intentional placement
                        - Creative purpose
                        - Good visibility
                        - Proper rendering
                    2. Usage Context:
                        - Strategic placement
                        - Message support
                        - Visual enhancement
                        - Audience engagement
                        - Style elements

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if emojis are used
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of emoji usage",
                            "evidence": [
                                {{
                                    "type": "visual/text/animated",
                                    "emoji_content": "description of emoji",
                                    "usage_type": "how emoji is used",
                                    "timestamp": float,
                                    "impact": "effect on content"
                                }}
                            ],
                            "strengths": ["effective emoji usage"],
                            "weaknesses": ["questionable or unclear usage"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Presence Verification:
                        - Clear emoji identification
                        - Intentional usage
                        - Proper display
                        - Creative purpose
                    2. Usage Assessment:
                        - Strategic placement
                        - Visual effectiveness
                        - Message enhancement
                        - Style integration
                    3. Scoring Guide:
                        - Clear, strategic emoji usage
                        - Present but limited emoji usage
                        - Minimal or unclear emoji elements
                        - No emoji usage detected

                    Remember: Focus on intentionally added emoji elements used for creative or communicative purposes.
            """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_micro_trend",
            name="Micro-Trend Usage",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video incorporate a micro-trend? Micro-trends are short-lived content patterns that:
                    1. Capture attention briefly (days to weeks)
                    2. Often stem from relatable human behaviors
                    3. Follow recognizable patterns:
                        - Specific audio/music trends
                        - Visual style patterns
                        - Specific transitions or effects
                        - Popular challenge formats
                        - Trending content structures
                        - Viral behavioral patterns
                    Detection focuses on identifying elements that match known micro-trend characteristics,
                    even if the specific trend is no longer current."
                """,
            prompt_template="""
                    Using both provided metadata AND your understanding of social media trends, analyze for micro-trend implementation.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    MICRO-TREND INDICATORS:
                    1. Audio Patterns:
                        - Trending sounds/music
                        - Popular audio clips
                        - Sound effect trends
                        - Voice effect patterns
                        - Audio transitions
                    2. Visual Elements:
                        - Signature transitions
                        - Trending effects
                        - Style patterns
                        - Popular formats
                        - Visual challenges
                    3. Content Structure:
                        - Trend-based formats
                        - Challenge structures
                        - Pattern repetition
                        - Setup-payoff trends
                        - Behavioral loops
                    4. Engagement Elements:
                        - Trend participation
                        - Pattern recognition
                        - Community references
                        - Shared behaviors
                        - Cultural moments

                    TREND CHARACTERISTICS:
                    1. Pattern Recognition:
                        - Clear format adoption
                        - Trend-based structure
                        - Pattern replication
                        - Style matching
                        - Element copying
                    2. Implementation Quality:
                        - Pattern accuracy
                        - Trend understanding
                        - Element execution
                        - Style authenticity
                        - Format adherence

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if micro-trend identified
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of trend identification",
                            "evidence": [
                                {{
                                    "trend_type": "audio/visual/structural/behavioral",
                                    "pattern": "specific trend elements",
                                    "implementation": "how trend is used",
                                    "timestamps": [float],
                                    "quality": "execution assessment"
                                }}
                            ],
                            "strengths": ["successful trend elements"],
                            "weaknesses": ["questionable or weak elements"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Trend Identification:
                        - Clear pattern match
                        - Element recognition
                        - Structure alignment
                        - Format adherence
                    2. Implementation Analysis:
                        - Pattern accuracy
                        - Element quality
                        - Style authenticity
                        - Execution effectiveness
                    3. Scoring Guide:
                        - Clear, well-executed micro-trend usage
                        - Identifiable trend with some execution issues
                        - Attempted trend usage but unclear or poor execution
                        - No identifiable micro-trend elements

                    Remember: Focus on identifying pattern matches to known micro-trend characteristics, even if trend
                    is no longer current.
                    Consider both obvious trend elements (audio, visuals) and subtle patterns (behavior, structure).
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_meso_trend",
            name="Meso-Trend Usage",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video utilize a meso-trend? Meso-trends are established content patterns that:
                    1. Have longer lifespans than micro-trends
                    2. Are integrated into platform culture
                    3. Include established formats such as:
                        - Storytime video structures
                        - Platform-specific challenges
                        - Signature transition styles
                        - Standard reveal formats
                        - Common tutorial structures
                        - Established content templates
                    Detection focuses on identifying elements that match established platform-specific content patterns and formats.
                """,
            prompt_template="""
                    Using both provided metadata AND your understanding of platform content patterns, analyze for meso-trend implementation.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    MESO-TREND CATEGORIES:
                    1. Content Formats:
                        - Storytime structures
                        - Tutorial patterns
                        - Review formats
                        - Challenge templates
                        - Reveal sequences
                        - List-style content
                    2. Platform Conventions:
                        - Standard transitions
                        - Common effects
                        - Established filters
                        - Traditional edits
                        - Regular formats
                    3. Structural Elements:
                        - Hook patterns
                        - Pacing structures
                        - Timing conventions
                        - Setup-payoff formats
                        - Narrative flows
                    4. Engagement Patterns:
                        - Call-to-action styles
                        - Interaction prompts
                        - Community formats
                        - Response structures
                        - Participation models

                    ASSESSMENT CRITERIA:
                        1. Format Recognition:
                            - Clear pattern match
                            - Established structure
                            - Platform alignment
                            - Cultural fit
                            - Format adherence
                        2. Implementation Quality:
                            - Structure accuracy
                            - Format understanding
                            - Element execution
                            - Style authenticity
                            - Pattern consistency

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if meso-trend identified
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of trend identification",
                            "evidence": [
                                {{
                                    "format_type": "content/platform/structural/engagement",
                                    "pattern": "specific format elements",
                                    "implementation": "how format is used",
                                    "timestamps": [float],
                                    "quality": "execution assessment"
                                }}
                            ],
                            "strengths": ["successful format elements"],
                            "weaknesses": ["questionable or weak elements"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Format Identification:
                        - Clear structure match
                        - Pattern recognition
                        - Platform alignment
                        - Cultural integration
                    2. Implementation Analysis:
                        - Format accuracy
                        - Element quality
                        - Style consistency
                        - Execution effectiveness
                    3. Scoring Guide:
                        - Clear, well-executed meso-trend format
                        - Identifiable format with some execution issues
                        - Attempted format but unclear or poor execution
                        - No identifiable meso-trend elements

                    Remember: Focus on identifying established, longer-lasting content formats and platform-specific patterns.
                    Consider both structural elements (format, pacing) and cultural elements (conventions, expectations).
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_macro_trend",
            name="Macro-Trend Implementation",
            category="shorts",
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video align with broader cultural macro-trends? Macro-trends are long-term societal movements that:
                        1. Reflect major cultural shifts (up to a decade in duration)
                        2. Address significant societal values or movements such as:
                            - Social justice and equality
                            - Environmental sustainability
                            - Mental health awareness
                            - Body positivity
                            - Digital transformation
                            - Cultural diversity
                            - Generational values
                    Detection focuses on identifying authentic alignment with and contribution to these broader cultural conversations.
                """,
            prompt_template="""
                    Using both provided metadata AND your understanding of societal trends, analyze for macro-trend implementation.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    MACRO-TREND CATEGORIES:
                    1. Social Movements:
                        - Gender equality
                        - Racial justice
                        - LGBTQ+ rights
                        - Body positivity
                        - Age inclusion
                        - Disability rights
                        - Cultural representation
                    2. Environmental Concerns:
                        - Sustainability
                        - Climate action
                        - Eco-consciousness
                        - Ethical consumption
                        - Zero waste
                        - Clean energy
                        - Environmental justice
                    3. Wellness & Health:
                        - Mental health awareness
                        - Work-life balance
                        - Digital wellbeing
                        - Holistic health
                        - Self-care
                        - Mindfulness
                        - Health equity
                    4. Technological Shifts:
                        - Digital transformation
                        - AI integration
                        - AR/VR adoption
                        - Remote lifestyle
                        - Digital privacy
                        - Tech ethics
                        - Digital inclusion

                    5. Cultural Values:
                        - Authenticity
                        - Transparency
                        - Community focus
                        - Ethical practices
                        - Social responsibility
                        - Inclusivity
                    - Cultural heritage

                    IMPLEMENTATION ANALYSIS:
                    1. Authenticity Check:
                        - Genuine commitment
                        - Deep understanding
                        - Meaningful contribution
                        - Long-term alignment
                        - Value integration
                    2. Message Quality:
                        - Clear communication
                        - Value alignment
                        - Cultural sensitivity
                        - Impact potential
                        - Message authenticity

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if macro-trend identified
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of macro-trend alignment",
                            "evidence": [
                                {{
                                    "trend_category": "social/environmental/wellness/tech/cultural",
                                    "specific_trend": "identified macro-trend",
                                    "implementation": {{
                                        "approach": "how trend is addressed",
                                        "authenticity": "authenticity assessment",
                                        "depth": "depth of engagement",
                                        "impact": "potential influence"
                                    }},
                                    "timestamps": [float],
                                    "elements": ["specific trend elements"]
                                }}
                            ],
                            "strengths": ["effective trend elements"],
                            "weaknesses": ["areas needing improvement"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Trend Identification:
                    - Clear movement alignment
                    - Cultural relevance
                    - Societal impact
                    - Value reflection
                    2. Implementation Quality:
                        - Authenticity level
                        - Message clarity
                        - Cultural sensitivity
                        - Value integration
                    3. Scoring Guide:
                        - Deep, authentic engagement with macro-trend
                        - Clear trend alignment with some depth
                        - Surface-level trend connection
                        - No clear macro-trend engagement

                    Remember: Focus on identifying genuine engagement with significant cultural movements and societal values.
                    Consider both explicit statements and implicit demonstrations of macro-trend alignment.
                    Evaluate authenticity and depth of engagement versus superficial trend adoption.
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_traditional_ad",
            name="Traditional Ad Style",
            category=VideoFeatureCategory.SHORTS,  # Changed to Shorts category
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video feel like a traditional TV commercial rather than social video content?
                    Traditional ad indicators include:
                        1. Professional production quality matching TV standards
                        2. Formal advertising structure and pacing
                        3. Commercial-style presentation and messaging
                        4. Professional talent and scripted delivery
                        5. Studio-quality lighting and sound
                        6. Standard advertising format execution
                """,
            prompt_template="""
                    Using the provided metadata, evaluate if this content matches traditional TV commercial style rather than social media content.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    TRADITIONAL AD INDICATORS:
                    1. Production Elements:
                        - Studio-quality lighting
                        - Professional audio mix
                        - Commercial-grade editing
                        - Perfect framing
                        - High-end equipment usage
                        - Professional color grading
                    2. Content Structure:
                        - Standard ad narrative
                        - Traditional pacing
                        - Commercial messaging
                        - Brand presentation
                        - Product demonstration
                        - Professional scripting
                    3. Presentation Style:
                        - Professional talent
                        - Scripted delivery
                        - Formal presentation
                        - Polished performance
                        - Commercial acting
                        - Brand spokesperson style
                    4. Commercial Elements:
                        - Traditional ad format
                        - Standard shot sequences
                        - Professional transitions
                        - Commercial music
                        - Professional voice-over
                        - Standard ad timing
                    NON-TRADITIONAL INDICATORS:
                    1. Social Elements Missing:
                        - Creator-style delivery
                        - Platform-specific features
                        - Native content feel
                        - Community engagement
                        - Authentic moments
                        - Personal touch

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if traditional TV ad style
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of traditional ad assessment",
                            "evidence": [
                                {{
                                    "element_type": "production/content/presentation/format",
                                    "commercial_indicators": ["specific traditional elements"],
                                    "timestamps": [float],
                                    "impact": "how it creates TV ad feel"
                                }}
                            ],
                            "strengths": ["clear traditional ad elements"],
                            "weaknesses": ["elements deviating from traditional style"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Commercial Style:
                        - Professional production
                        - Traditional structure
                        - Commercial delivery
                        - Standard format

                    2. Social Style Absence:
                        - Lacks platform features
                        - Missing native elements
                        - No creator style
                        - Formal vs authentic

                    3. Scoring Guide:
                        - Completely traditional TV ad style
                        - Mostly traditional with minor social elements
                        - Mixed style but leaning traditional
                        - Does not feel like traditional TV ad

                    Remember: Focus on identifying clear markers of traditional TV commercial style versus social media content approaches.
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_partial_social",
            name="Partial Social Style (25-50%)",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video show moderate social media characteristics (25-50% social feel)? Content should:
                    1. Maintain primarily professional/commercial style
                    2. Include some social media elements
                    3. Balance roughly 25-50% social characteristics with traditional production
                    4. Show intentional but limited platform-style elements
                    Detection focuses on identifying clear but limited social media content characteristics while
                    maintaining primarily traditional production values.
                """,
            prompt_template="""
                    Using the provided metadata, evaluate if this content shows partial (25-50%) social media characteristics.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    SOCIAL ELEMENTS TO DETECT (25-50%):
                    1. Limited Platform Features:
                        - Some native elements
                        - Basic platform tools
                        - Simple effects
                        - Light social formatting
                        - Casual moments
                    2. Partial Creator Style:
                        - Occasional direct address
                        - Some informal elements
                        - Limited personal touch
                        - Brief authentic moments
                        - Casual segments
                    3. Mixed Production Quality:
                        - Mostly professional
                        - Some natural lighting
                        - Occasional raw footage
                        - Limited casual shots
                        - Mixed editing styles
                    4. Balanced Delivery:
                        - Primarily scripted
                        - Some natural moments
                        - Limited casual speech
                        - Occasional authenticity
                        - Mixed presentation

                    ASSESS RATIO (25-50%):
                    1. Time Distribution:
                        - Social elements duration
                        - Traditional segments
                        - Style transitions
                        - Element balance
                        - VideoFeature timing
                    2. Element Integration:
                        - VideoFeature mixing
                        - Style blending
                        - Transition quality
                        - Balance maintenance
                        - Integration smoothness

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if 25-50% social elements
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of partial social style",
                            "evidence": [
                                {{
                                    "element_type": "platform/creator/production/delivery",
                                    "social_aspects": ["specific social elements"],
                                    "traditional_aspects": ["professional elements"],
                                    "ratio_estimate": "percentage social vs traditional",
                                    "timestamps": [float]
                                }}
                            ],
                            "strengths": ["successful partial integration"],
                            "weaknesses": ["balance issues"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Social Element Detection:
                        - Clear social features
                        - Limited implementation
                        - Intentional usage
                        - Controlled integration
                    2. Balance Assessment:
                        - 25-50% social feel
                        - Majority traditional
                        - Appropriate mixing
                        - Intentional limitation
                    3. Scoring Guide:
                        - Perfect 25-50% social balance
                        - Close to target range but slightly off
                        - Uneven balance or unclear ratio
                        - Outside 25-50% range entirely

                    Remember: Focus on identifying clear but limited (25-50%) social media characteristics while maintaining
                    primarily traditional production elements.
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_mostly_social",
            name="Predominantly Social Style (75%+)",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video predominantly display social media characteristics (75% or more social feel)? Content should:
                        1. Strongly align with platform-native content style
                        2. Show minimal traditional commercial elements
                        3. Maintain authentic, creator-style approach
                        4. Use platform-specific features extensively
                        5. Follow social media content conventions
                    Detection focuses on identifying strong social media characteristics that comprise at least 75% of the content's
                    style and approach.""",
            prompt_template="""
                    Using the provided metadata, evaluate if this content shows predominant (75%+) social media characteristics.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    STRONG SOCIAL INDICATORS (75%+):
                    1. Platform-Native Elements:
                        - Heavy platform feature use
                        - Native content structure
                        - Platform-specific effects
                        - Social formatting
                        - Community engagement style
                    2. Creator-Style Approach:
                        - Direct audience address
                        - Personal tone/style
                        - Authentic delivery
                        - Natural presentation
                        - Community connection
                    3. Production Style:
                        - Natural lighting
                        - Raw/authentic footage
                        - Platform-typical editing
                        - Casual shooting style
                        - Native visual approach
                    4. Content Delivery:
                        - Conversational tone
                        - Unscripted moments
                        - Natural speech patterns
                        - Authentic reactions
                        - Community language

                    LIMITED COMMERCIAL ELEMENTS (≤25%):
                    1. Production Elements:
                        - Minimal studio quality
                        - Limited professional polish
                        - Few formal sequences
                        - Rare commercial styling
                        - Minimal traditional ads
                    2. Content Approach:
                        - Few scripted moments
                        - Limited formal messaging
                        - Minimal traditional structure
                        - Rare commercial formats
                        - Few professional techniques

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if 75%+ social elements
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of predominantly social style",
                            "evidence": [
                                {{
                                    "element_type": "platform/creator/production/delivery",
                                    "social_elements": ["specific social features"],
                                    "traditional_elements": ["limited commercial aspects"],
                                    "ratio_estimate": "percentage social vs traditional",
                                    "timestamps": [float]
                                }}
                            ],
                            "strengths": ["strong social characteristics"],
                            "weaknesses": ["deviations from social style"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Social Dominance:
                        - Extensive platform features
                        - Strong creator style
                        - Natural production
                        - Authentic delivery
                    2. Commercial Limitation:
                        - Minimal professional elements
                        - Limited traditional aspects
                        - Few formal approaches
                        - Rare commercial styling
                    3. Scoring Guide:
                        - Clear 75%+ social media style
                        - Close to 75% but slightly below
                        - Mixed style but below 75%
                        - Predominantly traditional/commercial

                    Remember: Focus on identifying strong social media characteristics that clearly dominate (75%+) the content style and approach.
                    Look for authentic, platform-native elements while noting limited commercial aspects.
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_transitions",
            name="Creative Transitions",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video use creative transitions between scenes or segments? Detection includes:
                        1. Stylized editing transitions
                        2. Dramatic scene changes
                        3. Creative match cuts
                        4. Platform-style transitions
                        5. Visual transformation effects
                    Transitions must be intentionally creative or dramatic, not just standard cuts between scenes.
                """,
            prompt_template="""
                    Using the provided metadata, analyze for creative transition usage.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    TRANSITION TYPES:
                    1. Visual Transitions:
                        - Match cuts
                        - Whip pans
                        - Spin transitions
                        - Wipe effects
                        - Jump cuts
                        - Zoom transitions
                        - Color transitions
                    2. Platform Transitions:
                        - Finger snap changes
                        - Hand swipe effects
                        - Sound-synced cuts
                        - Outfit changes
                        - Location switches
                        - Object transformations
                        - Time shifts
                    3. Effect Transitions:
                        - Digital effects
                        - Visual overlays
                        - Screen wipes
                        - Dissolves
                        - Morphs
                        - Glitch effects
                        - Color shifts
                    4. Creative Elements:
                        - Coordinated movements
                        - Prop transitions
                        - Seamless edits
                        - Visual tricks
                        - Creative cuts
                        - Scene transformations
                        - Dramatic reveals

                    TRANSITION CHARACTERISTICS:
                    1. Technical Aspects:
                        - Timing precision
                        - Visual smoothness
                        - Effect quality
                        - Execution clarity
                        - Scene integration
                    2. Creative Impact:
                        - Visual interest
                        - Dramatic effect
                        - Style enhancement
                        - Flow contribution
                        - Viewer engagement

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if creative transitions found
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of transition usage",
                            "evidence": [
                                {{
                                    "transition_type": "visual/platform/effect/creative",
                                    "description": "specific transition details",
                                    "timestamp": float,
                                    "duration": float,
                                    "impact": "transition effectiveness"
                                }}
                            ],
                            "strengths": ["successful transition elements"],
                            "weaknesses": ["problematic or unclear transitions"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Transition Identification:
                        - Clear creative intent
                        - Dramatic change
                        - Intentional styling
                        - Visual impact
                        - Scene connection
                    2. Quality Assessment:
                        - Execution precision
                        - Effect clarity
                        - Visual appeal
                        - Style integration
                        - Flow enhancement
                    3. Scoring Guide:
                        - Multiple well-executed creative transitions
                        - Clear creative transitions with minor issues
                        - Basic or limited transition usage
                        - No creative transitions detected

                    Remember: Focus on identifying intentionally creative or dramatic transitions, not just standard cuts between scenes.
                    Consider both technical execution and creative impact of transitions.
            """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_gap_utilization",
            name="Creative Gap Utilization",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Does the video creatively utilize the top and bottom gaps created when adapting horizontal/square content
                    to vertical format? Creative usage includes:
                        1. Product imagery in gaps
                        2. Selling point text/supers
                        3. Brand elements/logos
                        4. Complementary visuals
                        5. Static or animated content
                    Detection focuses on intentional use of letterbox spaces to enhance the viewing experience and deliver
                    additional content.
                """,
            prompt_template="""
                    Using the provided metadata, analyze how effectively vertical gaps are utilized for additional content.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    GAP CONTENT TYPES:
                    1. Product Elements:
                        - Product images
                        - VideoFeature showcases
                        - Detail shots
                        - Package displays
                        - Product variations
                    2. Text Content:
                        - Selling points
                        - VideoFeature lists
                        - Call-to-actions
                        - Price information
                        - Product details
                    3. Brand Elements:
                        - Logo placements
                        - Brand colors
                        - Visual identity
                        - Brand graphics
                        - Company info
                    4. Visual Enhancements:
                        - Complementary graphics
                        - Background patterns
                        - Design elements
                        - Decorative content
                        - Visual effects

                    USAGE CHARACTERISTICS:
                    1. Content Quality:
                        - Visual clarity
                        - Text readability
                        - Design integration
                        - Brand alignment
                        - Element balance
                    2. Animation/Movement:
                        - Static elements
                        - Subtle animations
                        - Motion effects
                        - Transitions
                        - Dynamic changes

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if gaps are creatively utilized
                        "confidence_score": float,
                        "score": integer between 1-4,
                        "evaluation": {{
                            "rationale": "explanation of gap utilization",
                            "evidence": [
                                {{
                                    "location": "top/bottom",
                                    "content_type": "product/text/brand/visual",
                                    "elements": ["specific content details"],
                                    "animation": "static/animated",
                                    "timestamps": [float],
                                    "effectiveness": "usage quality"
                                }}
                            ],
                            "strengths": ["successful gap usage"],
                            "weaknesses": ["problematic or missing elements"]
                        }}
                    }}

                    EVALUATION CRITERIA:
                    1. Content Identification:
                        - Clear intentional use
                        - Relevant content
                        - Quality elements
                        - Brand alignment
                        - Visual integration
                    2. Implementation Quality:
                        - Design effectiveness
                        - Content clarity
                        - Space utilization
                        - Animation quality
                        - Overall impact
                    3. Scoring Guide:
                        - Excellent creative use of gaps with multiple content types
                        - Good gap utilization with some content
                        - Basic or limited gap usage
                        - No intentional gap utilization

                    Remember: Focus on identifying intentional and strategic use of vertical letterbox spaces.
                    Consider both static and animated content in these areas.
                    Evaluate effectiveness of content integration with main video.
            """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_product_result",
            name="Product/Service Result",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Ad demonstrates clear product/service outcomes through before/after comparisons, side-by-side
                    demonstrations, or effectiveness proof. Must show tangible or visible results of using the product/service.
                """,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate for clear product/service results.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Review Technical Evidence:
                        - Visual scene comparisons
                        - Split-screen content
                        - Time-lapse sequences
                        - Result demonstrations
                        - Transformation shots
                    2. Result Types to Detect:
                    a) Before/After:
                        - Clear transformations
                        - State changes
                        - Visible improvements
                        - Progress shots
                        - Outcome displays
                    b) Comparisons:
                        - Side-by-side views
                        - With/without product
                        - Alternative methods
                        - Competitive demos
                        - Contrasting results
                    c) Effectiveness Evidence:
                        - Performance proof
                        - Success metrics
                        - Visible outcomes
                        - Achievement displays
                        - Impact demonstration

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_analysis": {{
                                "result_demonstrations": [
                                    {{
                                        "timestamp": float,
                                        "type": "before_after/comparison/effectiveness",
                                        "demonstration_method": str,
                                        "visual_evidence": str,
                                        "clarity_score": float
                                    }}
                                ],
                                "supporting_elements": {{
                                    "visual_aids": [str],
                                    "text_overlays": [str],
                                    "speech_context": [str]
                                }}
                            }},
                            "result_quality": {{
                                "clarity_level": str,
                                "evidence_strength": str,
                                "demonstration_effectiveness": str,
                                "outcome_visibility": str
                            }},
                            "combined_assessment": {{
                                "primary_result_type": str,
                                "evidence_quality": {{
                                    "visual_proof": str,
                                    "supporting_content": str,
                                    "presentation_clarity": str
                                }},
                                "effectiveness_metrics": {{
                                    "result_clarity": float,
                                    "proof_strength": float,
                                    "viewer_understanding": str
                                }}
                            }}
                        }}
                    }}

                    DETECTION REQUIREMENTS:
                    1. Valid Result Types:
                        - Clear before/after demonstrations
                        - Direct product comparisons
                        - Measurable effectiveness
                        - Visible transformations
                        - Tangible outcomes
                    2. Result Quality Standards:
                        - Clear visibility
                        - Obvious connection to product
                        - Understandable outcome
                        - Demonstrable change
                        - Credible presentation
                    3. Short-Form Considerations:
                        - Quick result revelation
                        - Efficient comparison
                        - Clear outcome display
                        - Direct demonstration
                        - Impactful proof

                    CONFIDENCE SCORING:
                        - High (0.8-1.0): Clear, undeniable results with strong evidence
                        - Medium (0.5-0.7): Visible results with some ambiguity
                        - Low (0.2-0.4): Suggested results but limited proof

                    Remember: Focus on clear, demonstrable outcomes that prove product/service effectiveness in short-form context.
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_creator_name_mention",
            name="Creator Name Mention",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Ad explicitly mentions the YouTube Creator's name either in visual text overlays or
                    spoken audio. Must be clear, direct mention of creator's name to qualify.
                """,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate for explicit creator name mentions.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Review Technical Evidence:
                        - Text overlay content
                        - Speech transcriptions
                        - Visual graphics
                        - Scene composition
                        - Audio clarity
                    2. Analyze Name References:
                        - Direct name mentions
                        - Text displays
                        - Channel names
                        - Creator handles
                        - Personal branding

                    DETECTION REQUIREMENTS:
                    1. Text Evidence Types:
                        a) Visual Name Displays:
                            - Creator name text
                            - Channel name overlay
                            - Personal branding text
                            - Handle/username display
                            - Name graphics
                        b) Text Placement:
                            - Clear visibility
                            - Readable size
                            - Intentional display
                            - Proper formatting
                            - On-screen duration
                    2. Audio Evidence Types:
                        a) Spoken References:
                            - Direct name mention
                            - Channel name usage
                            - Personal introduction
                            - Self-reference
                            - Brand identity
                        b) Speech Clarity:
                            - Clear pronunciation
                            - Audible mention
                            - Intentional reference
                            - Distinct delivery
                        - Proper context

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,
                        "confidence_score": float,
                        "evaluation": {{
                            "metadata_analysis": {{
                                "name_mentions": [
                                    {{
                                        "timestamp": float,
                                        "type": "text/speech",
                                        "content": str,
                                        "mention_type": "direct_name/channel/handle",
                                        "clarity": "high/medium/low"
                                    }}
                                ],
                                "detection_quality": {{
                                    "text_clarity": str,
                                    "audio_quality": str,
                                    "evidence_strength": str
                                }}
                            }},
                            "mention_analysis": {{
                                "reference_types": [str],
                                "display_methods": [str],
                                "context_quality": str
                            }},
                            "overall_assessment": {{
                                "mention_confidence": float,
                                "primary_evidence": str,
                                "supporting_factors": [str]
                            }}
                        }}
                    }}

                    DETECTION CRITERIA:
                    1. Valid Mentions:
                        - Explicit creator name
                        - Clear channel name
                        - Recognizable handle
                        - Personal branding
                        - Direct self-reference
                    2. Invalid Examples:
                        - Generic greetings
                        - Unclear references
                        - Ambiguous terms
                        - Implied mentions
                        - Vague identifiers

                    Remember: Only count explicit, clear mentions of creator name/identity - implied or unclear references don't qualify.

                    CONFIDENCE SCORING:
                        - High (0.8-1.0): Clear, explicit name mentions with strong evidence
                        - Medium (0.5-0.7): Identifiable mentions with some uncertainty
                        - Low (0.2-0.4): Possible mentions but limited/unclear evidence
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_partnership_disclosure",
            name="Partnership Clearly Disclosed",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Video contains clear disclosure of partnership between creator and brand through explicit statements,
                    text overlays, or other unmistakable indicators of sponsored/paid content or brand collaboration.
                """,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate for clear partnership disclosure.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Detect Disclosure Methods:
                        a) Visual Disclosures:
                            - "#ad" or "#sponsored" text
                            - "Paid partnership" labels
                            - Sponsored content markers
                            - Brand collaboration notices
                            - Partnership declarations
                        b) Verbal Disclosures:
                            - "Sponsored by" statements
                            - Partnership announcements
                            - Collaboration mentions
                            - Brand partnership notes
                            - Sponsorship acknowledgments
                    2. Disclosure Requirements:
                        a) Clear Language:
                            - Explicit partnership terms
                            - Unambiguous wording
                            - Direct statements
                            - Clear sponsorship markers
                            - Obvious indicators
                        b) Proper Placement:
                            - Visible positioning
                            - Early mention
                            - Adequate duration
                            - Legible text
                            - Audible statements

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_analysis": {{
                                "disclosure_instances": [
                                    {{
                                        "timestamp": float,
                                        "type": "visual/verbal",
                                        "content": str,
                                        "method": str,
                                        "clarity_score": float
                                    }}
                                ],
                                "placement_quality": {{
                                    "visibility": str,
                                    "timing": str,
                                    "duration": float
                                }}
                            }},
                            "disclosure_assessment": {{
                                "clarity_level": str,
                                "language_explicitness": str,
                                "disclosure_methods": [str],
                                "effectiveness": str
                            }},
                            "combined_insights": {{
                                "primary_disclosure": {{
                                    "content": str,
                                    "timestamp": float,
                                    "method": str,
                                    "effectiveness": str
                                }},
                                "supporting_elements": [str],
                                "overall_clarity": str
                            }}
                        }}
                    }}

                    VALID DISCLOSURE INDICATORS:
                    1. Direct Terms:
                        - "Sponsored"
                        - "Paid partnership"
                        - "Ad"/"Advertisement"
                        - "Brand partner"
                        - "In collaboration with"
                        - "Thanks to [brand]"
                        - "Partnered with"
                        - "[Brand] sponsored"
                    2. Visual Markers:
                        - #ad
                        - #sponsored
                        - #paidpartnership
                        - #brandpartner
                        - Partnership labels
                        - Sponsorship notices

                    DETECTION REQUIREMENTS:
                    1. Clear Disclosure:
                        - Explicit partnership language
                        - Unambiguous indicators
                        - Obvious brand connection
                        - Proper disclosure placement
                        - Adequate visibility/audibility
                    2. Invalid/Insufficient:
                        - Vague references
                        - Unclear connections
                        - Hidden disclosures
                        - Ambiguous terms
                        - Implied partnerships
                    3. Short-Form Considerations:
                        - Early disclosure timing
                        - Clear visibility
                        - Efficient communication
                        - Direct language
                        - Proper placement

                    CONFIDENCE SCORING:
                        - High (0.8-1.0): Clear, explicit disclosure with proper placement
                        - Medium (0.5-0.7): Present but less prominent disclosure
                        - Low (0.2-0.4): Ambiguous or unclear disclosure

                    Remember: Focus on explicit, unmistakable partnership disclosures that meet legal and ethical standards for sponsored content identification.
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_personal_character_talk",
            name="Personal Character Talk",
            category=VideoFeatureCategory.SHORTS,
            evaluation_criteria="The story is driven by a single character (person, mascot etc.) that talks directly to camera, creating a personal connection with the viewer.",
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate if a single character drives the story while directly addressing the camera.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Review Technical Evidence (from metadata):
                        - Face detection data
                        - Speaking patterns
                        - Camera angle information
                        - Screen time distribution
                        - Eye direction indicators
                    2. Analyze Character Dominance:
                        - Single character identification
                        - Screen time percentage
                        - Narrative control
                        - Story progression role
                        - Central vs. supporting presence
                    3. Evaluate Direct Address:
                        - Eye contact with camera
                        - Personal pronouns usage
                        - Viewer engagement patterns
                        - Direct questions/statements
                        - Connection techniques

                    DUAL ANALYSIS APPROACH:
                    1. Technical Pattern Recognition:
                        a) Character Presence Markers:
                            - Face detection continuity
                            - Speaking time allocation
                            - Visual focus patterns
                            - Screen positioning
                            - Scene dominance
                        b) Direct Address Indicators:
                            - Forward-facing orientation
                            - Eye contact maintenance
                            - Camera angle relationship
                            - Viewer acknowledgment
                            - Engagement techniques
                    2. Communication Psychology Analysis:
                        a) Character Centrality:
                            - Story driving role
                            - Narrative ownership
                            - Message delivery dominance
                            - Supporting character contrast
                            - Plot advancement control
                        b) Viewer Connection:
                            - Parasocial relationship cues
                            - Engagement effectiveness
                            - Personal connection techniques
                            - Intimacy establishment
                            - Trust-building methods

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_analysis": {{
                                "primary_character": {{
                                    "appearances": [
                                        {{
                                            "timestamp": float,
                                            "duration": float,
                                            "speaking": boolean,
                                            "direct_address": boolean,
                                            "screen_dominance": "high/medium/low"
                                        }}
                                    ],
                                    "total_screen_time": float,
                                    "percentage_of_video": float,
                                    "technical_dominance": {{
                                        "visual_focus": str,
                                        "speech_control": str,
                                        "screen_presence": str
                                    }}
                                }},
                                "direct_address_markers": {{
                                    "camera_engagement_points": [float],
                                    "eye_contact_duration": float,
                                    "viewer_acknowledgment_moments": [float]
                                }}
                            }},
                            "communication_analysis": {{
                                "character_centrality": {{
                                    "story_control": str,
                                    "narrative_ownership": str,
                                    "message_delivery_role": str
                                }},
                                "viewer_connection": {{
                                    "engagement_quality": str,
                                    "personal_relationship_building": str,
                                    "trust_establishment": str
                                }}
                            }},
                            "combined_insights": {{
                                "single_character_assessment": {{
                                    "is_primary_driver": boolean,
                                    "screen_time_dominance": float,
                                    "story_control_level": str,
                                    "supporting_character_contrast": str
                                }},
                                "direct_address_quality": {{
                                    "camera_relationship": str,
                                    "viewer_engagement": str,
                                    "connection_effectiveness": str
                                }},
                                "overall_evaluation": {{
                                    "character_driven_score": int,  # 1-4 scale
                                    "direct_address_score": int,  # 1-4 scale
                                    "combined_effectiveness": str,
                                    "distinctive_techniques": [str]
                                }}
                            }}
                        }}
                    }}

                    PROVIDE BOTH:
                    1. Technical Analysis (from metadata):
                        - Character detection
                        - Screen time measurement
                        - Direct address instances
                        - Camera relationship
                    2. Communication Analysis (your evaluation):
                        - Story driving effectiveness
                        - Single character dominance
                        - Direct address quality
                        - Viewer connection impact

                    Remember: Evaluate BOTH aspects - (1) story being driven by a single character AND (2) that character
                    directly addressing the camera.

                    SCORING CONSIDERATIONS:
                    1. Single Character Dominance (50%):
                        - One clear protagonist
                        - Consistent presence
                        - Story advancement control
                        - Minimal supporting roles
                        - Message delivery ownership
                    2. Direct Camera Address (50%):
                        - Clear eye contact
                        - Viewer acknowledgment
                        - Personal pronouns (you, we)
                        - Questions to viewer
                        - Conversation simulation

                    EVIDENCE EXAMPLES - STRONG DETECTION:
                        - One person speaks throughout most of video
                        - Character clearly looks at camera when speaking
                        - Uses "you" language to address viewer
                        - Maintains consistent eye contact
                        - Minimal or no other speaking characters
                        - Story progresses through main character

                    EVIDENCE EXAMPLES - WEAK DETECTION:
                        - Multiple equal characters
                        - Character rarely faces camera
                        - Third-person narrative style
                        - No direct viewer engagement
                        - Divided screen time
                        - Ensemble-driven narrative
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_native_brand_context",
            name="Native Brand Context",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Brand is positioned as a secondary element rather than the main focus of the ad, integrating naturally within
                    the content.
                """,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate native brand integration.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Review Technical Evidence (from metadata):
                        - Brand placement/positioning
                        - Screen time allocation
                        - Visual emphasis patterns
                        - Brand mention context
                        - Content-to-brand ratio
                    2. Analyze Integration Strategy:
                        - How naturally brand appears
                        - Content-first vs. brand-first approach
                        - Contextual relevance
                        - Value-add integration
                        - Storytelling cohesion
                    3. Evaluate Brand Balance:
                        - Content-to-promotion ratio
                        - Natural vs. forced mentions
                        - User value prioritization
                        - Brand prominence level
                        - Integration authenticity

                    DUAL ANALYSIS APPROACH:
                    1. Technical Pattern Recognition:
                        a) Brand Presence Markers:
                            - Visual appearances
                            - Text mentions
                            - Logo placements
                            - Product displays
                            - Speaking references
                        b) Content Emphasis Indicators:
                            - Story focus
                            - Value delivery
                            - Entertainment priority
                            - Information sharing
                            - User benefit focus
                    2. Integration Psychology Analysis:
                        a) Authenticity Assessment:
                            - Natural fit evaluation
                            - Forced vs. organic
                            - Contextual relevance
                            - User value alignment
                            - Experience cohesion
                        b) Balance Measurement:
                            - Prominence evaluation
                            - Secondary positioning
                            - Content prioritization
                            - Brand subordination
                            - Integration quality

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_analysis": {{
                                "brand_instances": [
                                    {{
                                        "timestamp": float,
                                        "type": "visual/verbal/text",
                                        "context": str,
                                        "prominence": "primary/secondary/subtle",
                                        "integration_quality": str
                                    }}
                                ],
                                "content_emphasis": {{
                                    "story_focus": str,
                                    "value_priority": str,
                                    "user_benefit_clarity": str
                                }}
                            }},
                            "integration_analysis": {{
                                "authenticity_assessment": {{
                                    "natural_fit": str,
                                    "contextual_relevance": str,
                                    "forced_rating": str
                                }},
                                "balance_evaluation": {{
                                    "brand_vs_content": str,
                                    "secondary_positioning": str,
                                    "prominence_level": str
                                }}
                            }},
                            "combined_insights": {{
                                "key_integration_points": [
                                    {{
                                        "timestamp": float,
                                        "technical_aspects": {{
                                            "brand_presence": str,
                                            "content_context": str
                                        }},
                                        "strategic_value": {{
                                            "integration_quality": str,
                                            "naturalness": str,
                                            "user_value": str
                                        }}
                                    }}
                                ],
                                "overall_assessment": {{
                                    "native_quality_score": int,  # 1-4 scale
                                    "content_first_rating": str,
                                    "key_strengths": [str],
                                    "authenticity_level": str
                                }}
                            }}
                        }}
                    }}

                    PROVIDE BOTH:
                    1. Technical Analysis (from metadata):
                        - Brand appearances
                        - Visual prominence
                        - Mention frequency
                        - Content-to-brand ratio
                    2. Integration Analysis (your evaluation):
                        - Authenticity level
                        - Natural vs. forced
                        - Secondary positioning
                        - User value prioritization

                    Remember: Native brand context means the brand supports the content without dominating it - analyze both
                    technical prominence and psychological integration quality.

                    SCORING CONSIDERATIONS:
                    1. Brand Position (40%):
                        - Clearly secondary role
                        - Content remains primary
                        - Brand supports not dominates
                        - Non-intrusive placement
                    2. Natural Integration (30%):
                        - Contextual relevance
                        - Logical brand presence
                        - Authentic mentions
                        - Value-adding integration
                    3. User Value (30%):
                        - Content quality preserved
                        - User experience prioritized
                        - Value delivery focus
                        - Entertainment/information first

                    EVIDENCE EXAMPLES - NATIVE (HIGH SCORE):
                        - Brand appears naturally in relevant context
                        - Product used organically in story
                        - Content remains entertaining/valuable
                        - Brand supports rather than interrupts
                        - Integration feels authentic and helpful

                    EVIDENCE EXAMPLES - NON-NATIVE (LOW SCORE):
                        - Frequent forced brand mentions
                        - Overly prominent logo placements
                        - Interrupted content flow for promotion
                        - Brand dominates screen time
                        - Promotional language overshadows content
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_personal_character_type",
            name="Personal Character Type",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    The video ad uses everyday people, influencer, or content creator as the main character
                    rather than actors, celebrities, or fictional characters.
                """,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate the type of main character
                    featured in the video.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Review Technical Evidence (from metadata):
                        - Person/face detection data
                        - Speech patterns and style
                        - Visual presentation cues
                        - Production quality indicators
                        - Setting and context markers
                    2. Analyze Character Type:
                        - Everyday person vs. celebrity
                        - Authentic vs. polished presentation
                        - Relatable vs. aspirational qualities
                        - Amateur vs. professional delivery
                        - Personal vs. scripted style
                    3. Evaluate Authenticity Markers:
                        - Natural speech patterns
                        - Personal environment indicators
                        - Genuine reactions/emotions
                        - Real-life context elements
                        - Unscripted quality indicators

                    CHARACTER CATEGORIES TO IDENTIFY:
                    1. Everyday People:
                        - Regular individuals
                        - Authentic presentation
                        - Non-professional delivery
                        - Real-life settings
                        - Natural speech/behavior
                    2. Influencers/Content Creators:
                        - Social media personality style
                        - Personal connection approach
                        - Direct audience relationship
                        - Content creator mannerisms
                        - Platform-specific techniques
                    3. Actors/Celebrities (Non-Qualifying):
                        - Professional performance
                        - High production polish
                        - Celebrity recognition
                        - Scripted delivery
                        - Aspirational presentation

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # True if everyday person or influencer
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_analysis": {{
                                "main_character": {{
                                    "appearance_markers": {{
                                        "production_quality": str,
                                        "setting_type": str,
                                        "presentation_style": str,
                                        "visual_indicators": [str]
                                    }},
                                    "speech_patterns": {{
                                        "delivery_style": str,
                                        "scripting_level": str,
                                        "naturalness": str,
                                        "linguistic_markers": [str]
                                    }}
                                }},
                                "supporting_evidence": [
                                    {{
                                        "timestamp": float,
                                        "element": str,
                                        "character_type_indicator": str
                                    }}
                                ]
                            }},
                            "character_assessment": {{
                                "identified_type": str,  # "everyday_person", "influencer", "celebrity", "actor", etc.
                                "confidence_factors": [str],
                                "authenticity_markers": {{
                                    "natural_elements": [str],
                                    "relatable_qualities": [str],
                                    "genuine_indicators": [str]
                                }},
                                "counter_indicators": [str]
                            }},
                            "combined_insights": {{
                                "character_authenticity": {{
                                    "relatability_score": int,  # 1-4 scale
                                    "authenticity_level": str,
                                    "everyday_qualities": str
                                }},
                                "viewer_connection": {{
                                    "identification_potential": str,
                                    "parasocial_relationship": str,
                                    "authenticity_impact": str
                                }},
                                "overall_assessment": {{
                                    "everyday/influencer_qualities": float,  # 0-1 scale
                                    "celebrity/actor_qualities": float,  # 0-1 scale
                                    "primary_classification": str,
                                    "key_determining_factors": [str]
                                }}
                            }}
                        }}
                    }}

                    PROVIDE BOTH:
                    1. Technical Analysis (from metadata):
                        - Production quality indicators
                        - Setting/environment assessment
                        - Speech pattern analysis
                        - Visual presentation cues
                    2. Character Analysis (your evaluation):
                        - Character type identification
                        - Authenticity assessment
                        - Relatability evaluation
                        - Viewer connection potential

                    Remember: VideoFeature detects if the main character is an everyday person or influencer/content
                    creator rather than actor, celebrity, or fictional character.

                    SCORING CONSIDERATIONS:
                    1. Authenticity Markers (40%):
                        - Natural speech patterns
                        - Unscripted moments
                        - Genuine reactions
                        - Real environment
                        - Personal elements
                    2. Relatable Qualities (30%):
                        - Everyday appearance
                        - Accessible presentation
                        - Non-aspirational qualities
                        - Typical situations
                        - Common experiences
                    3. Content Creator Indicators (30%):
                        - Platform-specific mannerisms
                        - Creator techniques
                        - Audience relationship cues
                        - Personal brand elements
                        - Community connection

                    EVIDENCE EXAMPLES - QUALIFYING CHARACTERS:
                        - Person speaks in unscripted, natural manner
                        - Setting appears to be real home/environment
                        - Delivery includes natural pauses/imperfections
                        - Content creator uses platform-specific language
                        - Person shares personal opinions/experiences
                        - Individual displays authentic reactions

                    EVIDENCE EXAMPLES - NON-QUALIFYING CHARACTERS:
                        - Polished, professional delivery
                        - Clearly scripted performance
                        - Recognizable celebrity
                        - Professional actor portrayal
                        - Fictional or animated character
                        - Highly aspirational presentation
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_product_context",
            name="Product Context",
            category=VideoFeatureCategory.SHORTS,
            evaluation_criteria="""
                    The product is positioned as a secondary element rather than the main focus of the ad,
                    appearing in a natural and realistic context.
                """,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate product positioning
                    within the video content.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Review Technical Evidence (from metadata):
                        - Product appearances and timing
                        - Screen position and prominence
                        - Visual focus indicators
                        - Mention frequency and context
                        - Screen time allocation
                    2. Analyze Content-Product Balance:
                        - Story/content primacy vs. product focus
                        - Natural integration vs. forced placement
                        - Contextual relevance of product
                        - Background vs. foreground positioning
                        - Supporting vs. central role
                    3. Evaluate User Experience:
                        - Content value independence
                        - Product intrusiveness level
                        - Viewing experience quality
                        - Information vs. promotion balance
                        - Entertainment value preservation

                    DUAL ANALYSIS APPROACH:
                    1. Technical Pattern Recognition:
                        a) Product Presence Markers:
                            - Visual appearances
                            - Verbal mentions
                            - Text references
                            - Focus indicators
                            - Prominence measures
                        b) Content Priority Indicators:
                            - Story development
                            - User value delivery
                            - Entertainment elements
                            - Information sharing
                            - Experience quality
                    2. Integration Psychology Analysis:
                        a) Balance Assessment:
                            - Content-to-product ratio
                            - Focus distribution
                            - Attention direction
                            - Value hierarchy
                            - Primary experience element
                        b) Contextual Evaluation:
                            - Natural fit quality
                            - Realistic usage
                            - Authentic integration
                            - Scenario believability
                            - Environmental appropriateness

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_analysis": {{
                                "product_instances": [
                                    {{
                                        "timestamp": float,
                                        "type": "visual/verbal/text",
                                        "prominence": "background/mid-ground/foreground",
                                        "duration": float,
                                        "screen_position": str
                                    }}
                                ],
                                "content_emphasis": {{
                                    "story_development": str,
                                    "content_value": str,
                                    "user_experience": str
                                }},
                                "balance_metrics": {{
                                    "product_screen_time_ratio": float,
                                    "mention_frequency": float,
                                    "visual_prominence_score": float
                                }}
                            }},
                            "integration_analysis": {{
                                "secondary_positioning": {{
                                    "background_quality": str,
                                    "supporting_role": str,
                                    "natural_presence": str
                                }},
                                "contextual_relevance": {{
                                    "realistic_usage": str,
                                    "scenario_authenticity": str,
                                    "environmental_fit": str
                                }}
                            }},
                            "combined_insights": {{
                                "secondary_element_indicators": [
                                    {{
                                        "timestamp": float,
                                        "context": str,
                                        "technical_aspects": {{
                                            "positioning": str,
                                            "prominence": str
                                        }},
                                        "integration_quality": {{
                                            "naturalness": str,
                                            "relevance": str
                                        }}
                                    }}
                                ],
                                "overall_assessment": {{
                                    "secondary_positioning_score": int,  # 1-4 scale
                                    "content_primacy_level": str,
                                    "integration_effectiveness": str,
                                    "key_success_factors": [str]
                                }}
                            }}
                        }}
                    }}

                    PROVIDE BOTH:
                    1. Technical Analysis (from metadata):
                        - Product appearance timings
                        - Screen positioning data
                        - Visual prominence metrics
                        - Mention frequency analysis
                    2. Integration Analysis (your evaluation):
                        - Content-product balance
                        - Secondary positioning quality
                        - Natural integration assessment
                        - Context authenticity evaluation

                    Remember: Secondary positioning means content/story takes precedence while product appears in a
                    supporting, naturally integrated role.

                    SCORING CONSIDERATIONS:
                    1. Secondary Position (40%):
                        - Product not center of attention
                        - Brief/occasional appearances
                        - Background/mid-ground placement
                        - Content clearly prioritized
                        - Supporting rather than starring role
                    2. Natural Integration (30%):
                        - Contextually relevant appearances
                        - Realistic usage scenarios
                        - Authentic environment
                        - Logical presence
                        - Non-disruptive placement

                    3. Content Priority (30%):
                        - Story/information leads
                        - Independent value delivery
                        - Entertainment priority
                        - Experience quality maintained
                        - User benefit focus

                    EVIDENCE EXAMPLES - SECONDARY POSITION (HIGH SCORE):
                        - Product appears naturally in environment
                        - Content/story remains primary focus
                        - Product integrates without disruption
                        - Natural usage within narrative
                        - Brief, contextual appearances
                        - Supports rather than dominates content

                    EVIDENCE EXAMPLES - PRIMARY FOCUS (LOW SCORE):
                        - Product constantly center frame
                        - Frequent close-ups of product
                        - Story serves product demonstration
                        - Extended focus on features/benefits
                        - Content interrupted for product focus
                        - Excessive feature highlighting
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="shorts_video_format",
            name="Video Format",
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    The ad is in a vertical format with portrait aspect ratio, specifically designed
                    for mobile device viewing.
                """,
            prompt_template="""
                    Using both provided metadata AND your analytical capabilities, evaluate if the video uses vertical (portrait) format.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA PROVIDES:
                    {metadata_summary}

                    YOUR ANALYTICAL TASKS:
                    1. Review Technical Evidence (from metadata):
                        - Video dimensions/resolution
                        - Aspect ratio indicators
                        - Frame composition
                        - Object positioning
                        - Text placement
                    2. Analyze Mobile Optimization:
                        - Vertical orientation indicators
                        - Mobile-friendly elements
                        - Portrait-specific composition
                        - Device-appropriate sizing
                        - Vertical viewing adaptations
                    3. Evaluate Format Effectiveness:
                        - Content framing for vertical
                        - Subject positioning
                        - Mobile viewer experience
                        - Intentional vertical design
                        - Platform-specific optimization

                    ANALYTICAL APPROACH:
                    1. Technical Detection:
                        a) Aspect Ratio Markers:
                            - Height greater than width
                            - Vertical rectangle shape
                            - Portrait dimensions
                            - Mobile-standard ratios (9:16, 4:5)
                            - Vertical orientation signals
                        b) Composition Indicators:
                            - Vertical scene arrangement
                            - Central vertical alignment
                            - Portrait-style framing
                            - Mobile-optimized spacing
                            - Vertical viewing flow
                    2. Mobile Design Analysis:
                        a) Intentional Vertical Elements:
                            - Platform-specific formatting
                            - Mobile-native design choices
                            - Vertical scrolling accommodation
                            - Portrait viewing optimization
                            - Thumb-zone considerations

                        b) Viewing Experience Assessment:
                            - Mobile viewing comfort
                            - Vertical content flow
                            - Portrait engagement patterns
                            - Hand-held viewing adaptation
                            - Platform alignment quality

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,
                        "confidence_score": float,
                        "evaluation": {{
                            "technical_analysis": {{
                                "aspect_ratio": {{
                                    "height_to_width": float,
                                    "orientation": "portrait/landscape/square",
                                    "dimensions": {{
                                        "width": int,
                                        "height": int
                                    }},
                                    "standard_format": str  # "9:16", "4:5", etc.
                                }},
                                "composition_indicators": {{
                                    "vertical_framing": str,
                                    "object_alignment": str,
                                    "text_positioning": str
                                }}
                            }},
                            "mobile_design_assessment": {{
                                "vertical_optimization": {{
                                    "content_flow": str,
                                    "viewing_experience": str,
                                    "platform_compatibility": str
                                }},
                                "intentional_design": {{
                                    "purpose_indicators": [str],
                                    "mobile_native_elements": [str],
                                    "adaptation_quality": str
                                }}
                            }},
                            "combined_insights": {{
                                "format_determination": {{
                                    "primary_evidence": [str],
                                    "technical_confidence": float,
                                    "design_intention": str
                                }},
                                "overall_assessment": {{
                                    "vertical_format_score": int,  # 1-4 scale
                                    "mobile_optimization_level": str,
                                    "platform_appropriateness": str,
                                    "key_format_indicators": [str]
                                }}
                            }}
                        }}
                    }}

                    PROVIDE BOTH:
                    1. Technical Analysis (from metadata):
                        - Aspect ratio calculation
                        - Dimensional assessment
                        - Format classification
                        - Composition evaluation
                    2. Design Analysis (your evaluation):
                        - Mobile optimization quality
                        - Vertical design intentionality
                        - Platform appropriateness
                        - Viewing experience impact

                    Remember: Vertical format is specifically designed for mobile viewing with height greater than width,
                    typically using 9:16 or 4:5 aspect ratios.

                    DETECTION REQUIREMENTS:
                    1. Aspect Ratio Verification:
                        - Height clearly greater than width
                        - Portrait orientation
                        - Mobile-standard dimensions
                        - Vertical composition
                    2. Intentional Design Evidence:
                        - Purposeful vertical framing
                        - Mobile-optimized elements
                        - Platform-appropriate design
                        - Vertical viewing flow

                    STANDARD VERTICAL FORMATS:
                        - 9:16 ratio (1080x1920, 720x1280)
                        - 4:5 ratio (1080x1350)
                        - Other portrait formats with height > width

                    CONFIDENCE SCORING:
                        - High (0.8-1.0): Clear vertical format with mobile-optimized design
                        - Medium (0.5-0.7): Vertical orientation but less optimal for mobile
                        - Low (0.2-0.4): Some vertical elements but not fully optimized
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="content_type_ad_style_creator",
            name="Ad Style Analysis (Creator vs. Traditional)",  # Slightly more descriptive name
            category=VideoFeatureCategory.SHORTS,
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    Distinguish whether the video's advertising approach primarily follows a creator/influencer pattern
                    (personality-driven, authentic integration, direct audience connection) or a traditional brand advertisement format
                    (brand-centric messaging, formal presentation, standardized commercial structure), irrespective of production quality.
                    # Sharpened criteria focus
                """,
            prompt_template="""
                    Analyze this video's advertising style to determine if it aligns more closely with Creator/Influencer
                    style or Traditional Ad style. Focus on the core narrative approach, presenter's role, tone, and method
                    of brand integration.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary} # e.g., Channel name, Video title, duration, view count

                    STYLE INDICATORS TO EVALUATE:
                    CREATOR/INFLUENCER STYLE HALLMARKS:
                    1. Content Focus & Narrative:
                        - Driven by personal experience, opinion, or storytelling (creator is central).
                        - Direct, informal address to the audience (vlogging style, community language).
                        - Often includes unscripted moments or authentic reactions.
                        - Conversational, relatable, and personality-infused tone.
                        - Leverages existing creator-audience relationship/trust.
                    2. Role of Presenter & Authenticity:
                        - Presenter acts as a trusted individual/peer sharing experience.
                        - Emphasis on perceived genuineness and personal connection.
                        - Environment often feels personal (home, studio setup) even if professional.
                        - Mistakes or imperfections might be left in to enhance authenticity.
                    3. Brand Integration Method:
                        - Product presented as part of the creator's life/workflow/experience.
                        - Feels like a recommendation or personal endorsement.
                        - Discussion often includes subjective benefits or personal take.
                        - Call-to-action may involve creator codes or affiliate links.
                        - Integration aims to feel organic within the creator's usual content style.
                    4. Production Style Nuances:
                        - Can range from basic to high-end, but *serves the personal narrative*.
                        - Editing might use vlog conventions (jump cuts, overlays relevant to personality).
                        - Pacing often driven by the creator's speaking style.

                    TRADITIONAL AD STYLE HALLMARKS:
                    1. Content Focus & Narrative:
                        - Brand or product is the primary subject or 'hero'.
                        - Often follows a clear, persuasive script with marketing objectives.
                        - Uses actors or carefully directed individuals representing consumers/experts.
                        - Formal, polished, often aspirational or problem/solution focused tone.
                        - Aims for broad appeal, often less personality-specific.
                    2. Role of Presenter & Authenticity:
                        - Presenter acts as a spokesperson or demonstrator for the brand.
                        - Focus is on professional delivery and clarity of message.
                        - Environment is typically a set, idealized location, or studio.
                        - Emphasis on flawlessness and professional execution.
                    3. Brand Integration Method:
                        - Explicit showcasing of product features and benefits.
                        - Uses standard marketing language, slogans, taglines.
                        - Demonstrations are often idealized or highly controlled.
                        - Call-to-action is typically direct (buy now, visit website).
                        - The ad exists *solely* to promote the product/brand.
                    4. Production Style Nuances:
                        - Consistently high-polish, often cinematic or slick commercial look.
                        - Editing is typically smooth, conventional, emphasizes clarity.
                        - Pacing designed for maximum impact and message retention.

                    COMPARATIVE EVALUATION (Weighing the Evidence): # Renamed and refocused evaluation
                        1. Primary Focus: Is the core narrative about the creator's perspective/story, or about the brand/product's features and benefits?
                        2. Tone & Delivery: Is the language primarily conversational, personal, and informal (Creator) or scripted, formal, and promotional (Traditional)?
                        3. Audience Relationship: Does the video speak *to* an existing community/follower base (Creator) or broadcast *at* a general audience (Traditional)?
                        4. Brand Placement Feel: Does the product integration feel like a natural part of the creator's content (Creator) or a distinct commercial message (Traditional)?
                        5. Authenticity Signals: Are there elements aiming for perceived genuineness (personal anecdotes, less polish, direct interaction) even if production is high (Creator), or is the focus on idealized perfection (Traditional)?

                    FORMAT RESPONSE AS JSON (Strictly adhere to this structure):
                    {{
                        "detected": boolean,  # TRUE if predominantly Creator style, FALSE if predominantly Traditional style
                        "confidence_score": float, # Confidence in the classification (0.0 to 1.0)
                        "content_type": "Creator Ad Style" if detected else "Traditional Ad Style", # Label based on 'detected'
                        "evaluation": {{
                            "content_analysis": {{
                                "narrative_style": "Describe the primary narrative approach (e.g., 'Personal experience sharing', 'Product feature showcase')",
                                "engagement_approach": "Describe how the audience is addressed (e.g., 'Direct informal address', 'Formal voiceover narration')",
                                "messaging_tone": "Describe the overall tone (e.g., 'Conversational and enthusiastic', 'Professional and persuasive')",
                                "authenticity_level": "Assess perceived authenticity (e.g., 'High - feels genuine', 'Moderate - polished but personal', 'Low - clearly scripted/staged')"
                            }},
                            "production_analysis": {{
                                "technical_quality": "Describe overall production level (e.g., 'High-end cinematic', 'Professional vlog style', 'Mixed polish levels')",
                                "visual_style": "Describe the look and feel (e.g., 'Naturalistic personal space', 'Idealized commercial set', 'Dynamic run-and-gun')",
                                "audio_elements": "Note key audio characteristics (e.g., 'Clear conversational dialogue', 'Professional voiceover', 'Stock music dominant')",
                                "editing_approach": "Describe editing style (e.g., 'Jump cuts common', 'Smooth seamless transitions', 'Fast-paced montage')"
                            }},
                            "style_markers": {{
                                "creator_elements": ["List specific observed elements fitting Creator style (e.g., 'Used first-person story', 'Showed personal workspace', 'Offered discount code')"],
                                "traditional_elements": ["List specific observed elements fitting Traditional style (e.g., 'Focused solely on product features', 'Used professional actors', 'Showcased idealized results')"],
                                "distinguishing_features": ["Explain the key factors that differentiate this video, especially if mixed elements exist (e.g., 'High production but narrative remained personal', 'Tone shifted distinctly for ad segment')"]
                            }},
                            "evidence": {{
                                "timestamps": [ # Provide specific examples
                                    {{
                                        "time": float, # Time in seconds (start of relevant segment)
                                        "element": "Describe the specific visual or audio cue",
                                        "style_type": "Creator or Traditional", # Which style does this cue support?
                                        "description": "Briefly explain *why* this cue supports the style type"
                                    }}
                                    # Add more timestamped evidence points as needed
                                ],
                                "key_moments": ["Describe 1-3 moments that strongly exemplify the determined style"],
                                "production_notes": ["Overall comments on how production choices reinforce the style (e.g., 'Editing pace matched conversational tone', 'Lighting created idealized product shots')"]
                            }}
                        }},
                        "reasoning_summary": "Provide a concise (1-2 sentence) justification for the final classification, synthesizing the key evaluation points." # Added summary field
                    }}

                    IMPORTANT NOTES (Critical Considerations):
                        1. High production value alone DOES NOT equal Traditional style. Focus on intent and narrative.
                        2. Creator ads can be extremely well-produced while maintaining core authentic/personal elements.
                        3. Prioritize the *overall feel*, *presenter's role*, and *narrative approach* over isolated technical aspects.
                        4. Look for *signals of authenticity* (even subtle ones) in creator content, regardless of budget.
                        5. Assess *how* production choices *serve the core message*: Is it enhancing a personal story or creating a brand showcase?
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
        VideoFeature(
            id="content_type_ad_style",
            name="Ad Style Analysis",
            category="Content_Type",
            sub_category=VideoFeatureSubCategory.NONE,
            video_segment=VideoSegment.FULL_VIDEO,
            evaluation_criteria="""
                    "Analyze if content follows creator/influencer ad patterns or traditional ad format. "
                    "Creator ads typically feature personal narrative, direct audience engagement, and authentic style "
                    "even with high production value. Traditional ads follow standard commercial formats with "
                    "formal presentation and brand-first messaging.
                """,
            prompt_template="""
                    Analyze this video's advertising style and production approach.

                    BRAND/PRODUCT CONTEXT:
                    - Brand: {brand}
                    - Product: {product}
                    - Industry: {vertical}

                    VIDEO METADATA:
                    {metadata_summary}

                    STYLE INDICATORS:

                    CREATOR/INFLUENCER STYLE:
                    1. Content Approach:
                        - Personal narrative/experience sharing
                        - Direct, informal audience engagement
                        - Behind-the-scenes elements
                        - Authentic, conversational tone
                        - Community-focused messaging
                    2. Production Elements:
                        - Dynamic, energetic pacing
                        - Mix of polished and casual moments
                        - Natural location shooting
                        - Personal workspace/environment
                        - Authentic reaction shots
                    3. Brand Integration:
                        - Personal experience with product
                        - Natural usage demonstrations
                        - Honest feedback/reviews
                        - Relatable scenarios
                        - Organic product placement

                    TRADITIONAL STYLE:
                    1. Content Approach:
                        - Brand-first messaging
                        - Professional scripting
                        - Formal presentation
                        - Marketing-focused language
                        - Product-centric focus
                    2. Production Elements:
                        - Consistent high polish
                        - Studio-quality lighting
                        - Professional staging
                        - Commercial-grade effects
                        - Perfect technical execution
                    3. Brand Integration:
                        - Formal product showcasing
                        - Standard marketing messages
                        - Professional demonstrations
                        - Idealized scenarios
                        - Strategic placement

                    EVALUATE BOTH:
                    1. Content Style:
                        - Narrative approach
                        - Speaking patterns
                        - Audience engagement
                        - Message delivery
                        - Brand integration
                    2. Production Quality:
                        - Technical execution
                        - Visual composition
                        - Audio quality
                        - Editing style
                        - Overall polish
                    3. Creator Authenticity:
                        - Personal connection
                        - Natural delivery
                        - Genuine reactions
                        - Real environment
                        - Honest messaging

                    FORMAT RESPONSE AS JSON:
                    {{
                        "detected": boolean,  # TRUE for Creator style, FALSE for Traditional
                        "confidence_score": float,
                        "content_type": "Creator Ad Style" if detected else "Traditional Ad Style",
                        "evaluation": {{
                            "content_analysis": {{
                                "narrative_style": str,
                                "engagement_approach": str,
                                "messaging_tone": str,
                                "authenticity_level": str
                            }},
                            "production_analysis": {{
                                "technical_quality": str,
                                "visual_style": str,
                                "audio_elements": str,
                                "editing_approach": str
                            }},
                            "style_markers": {{
                                "creator_elements": [str],
                                "traditional_elements": [str],
                                "distinguishing_features": [str]
                            }},
                            "evidence": {{
                                "timestamps": [
                                    {{
                                        "time": float,
                                        "element": str,
                                        "style_type": str,
                                        "description": str
                                    }}
                                ],
                                "key_moments": [str],
                                "production_notes": [str]
                            }}
                        }}
                    }}

                    IMPORTANT NOTES:
                        1. High production value alone doesn't indicate traditional style
                        2. Creator ads can be well-produced while maintaining authenticity
                        3. Consider overall approach and tone more than technical quality
                        4. Look for authentic elements even in polished content
                        5. Evaluate how production serves the content style
                """,
            extra_instructions=[],
            evaluation_method=EvaluationMethod.LLMS,
            evaluation_function="",
            include_in_evaluation=True,
            group_by=VideoSegment.FULL_VIDEO,
        ),
    ]

    return feature_configs
