# Creative Reviewer Report Guide

The report is an AI-powered evaluation of video ad creative. It analyzes a video against Google's ABCD framework, persuasion psychology, emotional storytelling, accessibility, and media buying signals. It's generated in three formats: an interactive HTML page (in-app), a shareable standalone HTML report (`/report/{id}`), and a downloadable PDF.

---

## Sections

### 1. Score Cards (top of report)

Six headline metrics at a glance — **Performance Score** (0–100 composite), **ABCD Score** (% of framework features detected), **Persuasion Density** (% of tactics used), **Emotional Coherence** (0–100 sentiment consistency), **Accessibility** (% of checks passed), and **Brand** (detected brand name + video download). Each card shows benchmark percentile badges when enough historical data exists (n≥5). **Use this** as the first pass — green (≥80) is strong, yellow (65–79) needs polish, red (<65) needs work.

### 2. Executive Summary

A bullet-point digest aggregating the key findings: scores, scene count, volume warnings, emotional shift alerts, percentile rankings, accessibility issues, and audio analysis notes. **Use this** to quickly brief stakeholders or write a summary email without reading the full report.

### 3. Action Plan

A prioritized list of recommendations. Each item has a priority (high/medium/low), a feature name, and a specific recommendation. Items marked "Fix" are for missing features; "Optimize" is for detected features that could be stronger. **Use this** as a to-do list when handing off to editors or creative teams — work top-down by priority.

### 4. Creative Brief / Creative Concept

If the AI extracted a structured brief, this shows the **one-line pitch**, key message, emotional hook, narrative technique, USP, target emotion, creative territory, and messaging hierarchy (primary/secondary messages + proof points). Falls back to a simpler name + description if the brief format wasn't detected. **Use this** to verify the ad communicates what you intended, or to reverse-engineer a brief from an existing ad.

### 5. Creative Metadata

Technical specs: duration, resolution, aspect ratio, frame rate, file size, codec. **Use this** to check platform compliance (e.g., is it 9:16 for Reels? Under 60s for Shorts?).

### 6. Scene Timeline

Visual cards for each detected scene with keyframe thumbnails, timestamps, description, transcript, **emotion pills** (e.g., "excitement +0.7"), and **music mood pills** (e.g., "♪ energetic"). **Use this** to review the creative beat-by-beat — verify the story flow, check that key messages land in the right scenes, and spot scenes with weak descriptions or missing voiceover.

### 7. Audio Analysis

Three summary cards — **A/V Congruence** (how well audio matches visuals, 0–100), **Silence Gaps** (count + total duration), and **Avg Speech Ratio** — followed by a per-scene volume bar chart. Red-flagged bars indicate sudden volume jumps between scenes. **Use this** to catch audio mixing issues before media spend: unintentional silence, jarring volume spikes, or low speech-to-music ratio.

### 8. Emotional Arc

An SVG line chart plotting **sentiment score** (−1.0 to +1.0) across scenes, with colored dots per emotion and red highlights on abrupt shifts (Δ > 0.5). An alert box calls out specific scene transitions with sharp emotional changes. **Use this** to evaluate storytelling flow — a good ad typically has a deliberate emotional arc, not random swings.

### 9. Feature Timeline

A swimlane chart mapping detected features to their **exact timestamps** in the video. Each row is a feature (color-coded by sub-category: Attract, Brand, Connect, Direct, Persuasion, Structure), with horizontal bars showing when it's active. **Use this** to see feature coverage across the video — identify dead zones where no features are active, or verify that branding appears early enough.

### 10. Performance Score

Predictive analytics section with four cards — **CPA Risk** (Low/Medium/High), **ROAS Potential**, **Fatigue Risk**, and **Funnel Strength** (TOF/MOF/BOF split) — plus section-level score bars (Hook & Attention, Brand Visibility, Social Proof, Product Clarity, Funnel Alignment, CTA, Creative Diversity, Measurement Readiness, Audience Leverage) and top positive/negative score drivers. **Use this** to predict how the ad will perform in paid media before spending budget. Focus on red bars and negative drivers for the highest-leverage improvements.

### 11. Platform Compatibility

Per-platform scores (0–100) for **YouTube, Meta Feed, Meta Reels, TikTok, and CTV**, each with specific optimization tips. **Use this** to decide which platforms to run the ad on as-is, and what to change for platforms where it scores low (e.g., "add captions for TikTok" or "shorten to 15s for Reels").

### 12. Reference Ads

Up to 3 top-performing ads with similar creative profiles, showing their name, brand, vertical, structure archetype, why they're effective, and comparison badges (ABCD score, Performance score, Similarity %). **Use this** for creative inspiration — watch the reference ads to see how high performers in your category handle similar creative challenges.

### 13. Accessibility

Summary cards for overall accessibility score and speech rate (WPM with too-fast/too-slow flagging), followed by per-check feature rows with rationale, evidence, and **remediation callouts** (specific "FIX" instructions for failed checks). **Use this** to ensure the ad is inclusive — failed checks like missing captions, low contrast text, or too-fast speech directly reduce reach and can violate platform guidelines.

### 14. ABCD Feature Results

Detailed pass/fail for each feature in Google's **Attract, Brand, Connect, Direct** framework. Each feature shows a confidence %, rationale, evidence, strengths, weaknesses, clickable timestamps, reliability badge, and a prioritized recommendation. **Use this** for the deepest drill-down — click a feature to see exactly why it passed or failed, with specific video timestamps to review.

### 15. Persuasion Tactics

Same detailed format as ABCD, but for **psychological persuasion techniques** (social proof, scarcity, authority, reciprocity, etc.). **Use this** to understand which persuasion levers the ad pulls and which are missing.

### 16. Creative Structure

Identifies the ad's **narrative archetype(s)** (e.g., "Problem-Solution, Testimonial") with rationale, strengths, and weaknesses. **Use this** to understand the creative's storytelling DNA and compare against what works for your vertical.

### 17. Brand Intelligence Brief

Auto-researched brand dossier covering company overview, product/service, brand positioning, core value proposition, target audiences (primary + secondary), key insights, tone & voice, products & pricing, credibility signals, paid media channels, creative formats, messaging themes, and CTA patterns. **Use this** to verify the ad aligns with the brand's positioning, or as a ready-made brief when onboarding a new brand.

---

## Color Coding

Throughout the report, scores are color-coded:

- 🟢 **Green** (≥80) — Strong
- 🟡 **Yellow** (65–79) — Needs polish
- 🔴 **Red** (<65) — Needs work
