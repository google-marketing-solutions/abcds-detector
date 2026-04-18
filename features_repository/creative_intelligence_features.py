#!/usr/bin/env python3

"""Module with Creative Intelligence feature configurations (Persuasion + Structure)"""

from models import (
    VideoFeature,
    VideoFeatureCategory,
    VideoSegment,
    EvaluationMethod,
    VideoFeatureSubCategory,
)


def get_creative_intelligence_feature_configs() -> list[VideoFeature]:
  """Gets all Creative Intelligence features (persuasion tactics + structure classification)
  Returns:
  feature_configs: list of feature configurations
  """
  feature_configs = [
      # ===== PERSUASION DETECTION FEATURES =====
      VideoFeature(
          id="p_scarcity",
          name="Scarcity",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.PERSUASION,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                A scarcity tactic is used in the video. This includes limited-time offers,
                limited stock messaging, exclusive access, countdown timers, or phrases like
                "while supplies last", "only X left", "limited edition", "selling fast",
                "don't miss out", or any implication that availability is restricted.
            """,
          prompt_template="""
                Does this video use any scarcity tactics to create a sense of limited availability?
                Look for limited-time offers, limited stock, exclusivity, countdown timers,
                or language implying restricted availability.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Analyze both visual elements (text overlays, countdown timers) and audio (speech, narration).",
              "Provide the exact timestamp and description of each scarcity tactic found.",
              "Return True if any scarcity tactic is detected, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="p_social_proof",
          name="Social Proof",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.PERSUASION,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Social proof is present in the video. This includes customer testimonials,
                reviews, ratings, user counts, celebrity or influencer endorsements,
                "as seen on" mentions, award badges, customer story references,
                phrases like "thousands of customers", "5-star rated", "best-selling",
                or any evidence that others have validated the product or brand.
            """,
          prompt_template="""
                Does this video use social proof to build credibility?
                Look for testimonials, reviews, ratings, user counts, endorsements,
                "as seen on" references, awards, or any indication that others trust the product.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Analyze both visual elements and audio for social proof signals.",
              "Provide the exact timestamp and description of each social proof element found.",
              "Return True if any social proof is detected, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="p_authority",
          name="Authority",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.PERSUASION,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                An authority signal is present in the video. This includes expert endorsements,
                professional credentials, scientific claims, certifications, patents,
                "doctor recommended", "clinically proven", "industry-leading", founder credentials,
                institutional affiliations, or any appeal to expertise or authoritative knowledge.
            """,
          prompt_template="""
                Does this video leverage authority or expertise to build trust?
                Look for expert endorsements, credentials, certifications, scientific claims,
                professional titles, institutional affiliations, or appeals to authoritative knowledge.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Analyze both visual elements (credentials on screen, lab coats, certifications) and audio.",
              "Provide the exact timestamp and description of each authority signal found.",
              "Return True if any authority signal is detected, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="p_urgency",
          name="Urgency",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.PERSUASION,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                An urgency tactic is used in the video. This includes time-limited offers,
                countdown timers, "act now", "today only", "ends soon", "last chance",
                flash sale messaging, deadline references, or any language or visual element
                that pressures immediate action based on time constraints.
                Note: Urgency is time-based pressure, distinct from scarcity which is quantity-based.
            """,
          prompt_template="""
                Does this video create a sense of urgency through time-based pressure?
                Look for time-limited offers, deadlines, "act now" language, countdown timers,
                or any element pressuring immediate action due to time constraints.
                Note: Focus on TIME pressure, not quantity/stock limitations.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Distinguish between urgency (time-based) and scarcity (quantity-based).",
              "Provide the exact timestamp and description of each urgency tactic found.",
              "Return True if any urgency tactic is detected, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="p_risk_reversal",
          name="Risk Reversal",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.PERSUASION,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                A risk reversal tactic is present in the video. This includes money-back guarantees,
                free trials, free returns, warranty mentions, "satisfaction guaranteed",
                "no questions asked", "risk-free", "try before you buy", free shipping and returns,
                or any mechanism that reduces the perceived risk of purchase.
            """,
          prompt_template="""
                Does this video use risk reversal to reduce purchase hesitation?
                Look for guarantees, free trials, free returns, warranties,
                "risk-free" language, or any element that shifts risk away from the buyer.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Analyze both visual elements (guarantee badges, return policy text) and audio.",
              "Provide the exact timestamp and description of each risk reversal element found.",
              "Return True if any risk reversal tactic is detected, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="p_anchoring",
          name="Anchoring",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.PERSUASION,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Price anchoring is used in the video. This includes showing a higher original price
                crossed out next to a sale price, comparing to competitor prices, "was $X now $Y",
                "save X%", value comparisons ("less than a cup of coffee per day"),
                or any technique that establishes a reference point to make the actual price
                seem more attractive.
            """,
          prompt_template="""
                Does this video use price anchoring to make the offer seem more attractive?
                Look for crossed-out prices, price comparisons, "was/now" pricing, percentage savings,
                value comparisons to everyday items, or any reference point that frames the price favorably.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Analyze both visual elements (price displays, strikethrough text) and audio.",
              "Provide the exact timestamp and description of each anchoring tactic found.",
              "Return True if any anchoring tactic is detected, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="p_price_framing",
          name="Price Framing",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.PERSUASION,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Price framing is used in the video. This includes presenting the price in a
                favorable context such as monthly installments instead of total price,
                "starting at" pricing, bundle value messaging, "free" with purchase,
                bonus item stacking, percentage-off framing vs dollar-off,
                or any technique that makes the price appear smaller or the value appear greater
                through how it is presented.
            """,
          prompt_template="""
                Does this video use price framing to present the offer favorably?
                Look for installment pricing, "starting at" language, bundle values,
                bonus stacking, "free" offers, or any technique that frames the price
                to appear smaller or the value to appear greater.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Analyze both visual elements (price displays, offer text) and audio.",
              "Provide the exact timestamp and description of each price framing tactic found.",
              "Return True if any price framing tactic is detected, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      # ===== ACCESSIBILITY FEATURES =====
      VideoFeature(
          id="acc_captions_present",
          name="Captions / Subtitles Present",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.ACCESSIBILITY,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Burned-in captions or subtitles are visible in the video. This includes
                hard-coded text overlays that transcribe or summarize the spoken dialogue,
                auto-generated caption styling, or any persistent text that conveys the
                audio content visually. Captions should cover the majority of spoken
                segments, not just a few words.
            """,
          prompt_template="""
                Does this video include burned-in (hard-coded) captions or subtitles
                that visually convey the spoken content? Look for persistent text overlays
                that transcribe dialogue or narration. Brief title cards or CTAs alone
                do not count as captions.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Check whether the captions cover the majority of spoken dialogue, not just a few words.",
              "Distinguish between burned-in captions and decorative text overlays or CTAs.",
              "Return True if captions/subtitles are present for most speech, False otherwise.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="acc_text_contrast",
          name="Text Contrast & Readability",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.ACCESSIBILITY,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                All text overlays in the video are clearly readable against their backgrounds.
                Text should have sufficient contrast (e.g., dark text on light backgrounds
                or light text on dark backgrounds), adequate font size (not too small to read
                on a mobile screen), and sufficient on-screen duration to be read comfortably.
                Text that is very small, low-contrast, or flashes too quickly fails this check.
            """,
          prompt_template="""
                Are all text overlays in this video clearly readable? Evaluate contrast
                against backgrounds, font size (readable on mobile), and on-screen duration
                (enough time to read). Flag any text that is too small, low-contrast,
                or appears too briefly to read comfortably.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Analyze all text overlays, supers, and title cards throughout the video.",
              "Check for adequate contrast, size, and display duration.",
              "Return True if all significant text is readable, False if any text has contrast or readability issues.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="acc_speech_rate",
          name="Speech Rate",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.ACCESSIBILITY,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                The speech rate in the video is comfortable for comprehension.
                Speech that is too fast (above 180 words per minute) may be difficult for
                non-native speakers, hearing-impaired viewers, or elderly audiences to follow.
                Speech that is too slow (below 100 words per minute) may lose viewer attention.
                An optimal speech rate is between 120-170 words per minute.
                This feature is evaluated computationally from the transcript.
            """,
          prompt_template="""
                Evaluate whether the speech pacing in this video is appropriate for a
                broad audience. Consider whether the narration or dialogue is too fast
                to follow comfortably, or if there are sections with rushed speech.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "This feature is primarily evaluated computationally from speech rate (words per minute).",
              "Return True if speech rate is between 100-180 WPM, False if it is outside this range.",
              "If there is no speech in the video, return True (no speech rate issue).",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="acc_audio_dependence",
          name="Audio Independence",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.ACCESSIBILITY,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                The video's core message is understandable without audio (sound-off viewing).
                Critical information should be conveyed visually — through text overlays,
                demonstrations, product shots, and visual storytelling — not solely through
                voiceover or dialogue. This is crucial for platforms where users scroll with
                sound off (Meta, Instagram, LinkedIn). If turning off the sound causes the
                viewer to lose the core message, value proposition, or call to action,
                this check fails.
            """,
          prompt_template="""
                Can a viewer understand the core message, value proposition, and call to
                action of this video with the sound turned off? Evaluate whether critical
                information is conveyed visually (text overlays, product demos, visual
                storytelling) or depends entirely on audio (voiceover, dialogue, narration).
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              "Imagine watching the video on mute. Can you understand the product/service, the key benefit, and the CTA?",
              "Return True if the core message is understandable visually (sound-off friendly), False if audio is required.",
              "Look for text overlays, captions, visual demonstrations, and on-screen CTAs as positive signals.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      # ===== STRUCTURE CLASSIFICATION FEATURE =====
      VideoFeature(
          id="s_creative_structure",
          name="Creative Structure",
          category=VideoFeatureCategory.CREATIVE_INTELLIGENCE,
          sub_category=VideoFeatureSubCategory.STRUCTURE,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Classify the narrative structure of this video ad into one of the following archetypes:
                - UGC Testimonial: User-generated content style with real or staged customer reviews
                - Founder Story: Brand founder or team member tells the origin/mission story
                - Problem-Solution: Opens with a pain point, then presents the product as the answer
                - Before-After: Shows transformation from before using the product to after
                - Offer-Driven: Leads with a deal, discount, or promotional offer
                - Authority-Led: Expert, professional, or credentialed person endorses/explains
                - Demo-Focused: Primary focus is showing the product in use, features, or how it works
                - Lifestyle: Shows the product integrated into an aspirational lifestyle context
                - Montage: Rapid sequence of scenes/images with music, minimal narrative arc
                The ad must match at least one archetype. Multiple can apply.
            """,
          prompt_template="""
                What is the narrative structure of this video advertisement?
                Classify it into one or more of the following archetypes:
                UGC Testimonial, Founder Story, Problem-Solution, Before-After,
                Offer-Driven, Authority-Led, Demo-Focused, Lifestyle, or Montage.

                For the primary archetype detected, return True.
                Provide the archetype name(s) in the evidence field.
                Provide reasoning for why this structure was chosen in the rationale field.
            """,
          extra_instructions=[
              "Consider the following criteria for your answer: {criteria}",
              (
                  "Look through the entire video and identify the primary"
                  " narrative pattern."
              ),
              (
                  "List ALL matching archetypes in the evidence field,"
                  " with the primary one first."
              ),
              (
                  "In strengths, describe how well the structure is executed."
                  " In weaknesses, note any structural confusion or missed"
                  " opportunities."
              ),
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
  ]

  return feature_configs
