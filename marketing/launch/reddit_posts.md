# Reddit Launch Posts

**General rules:**
- Don't post to all subreddits on the same day — spread across 3-4 days
- Be a genuine community member, not a drive-by promoter
- Answer every comment
- Each post is tailored to the subreddit's culture

---

## r/PPC

**Title:** I built a free, open-source tool that automatically scores video ads against YouTube's ABCD framework

**Body:**

Hey r/PPC — I've been lurking here for a while and wanted to share something I built.

If you run YouTube ads, you probably know about the ABCD framework (Attract, Brand, Connect, Direct). Google's research shows ads that follow it see 30%+ better performance.

The problem: manually reviewing each ad against 23+ ABCD checklist items is tedious and inconsistent.

So I built Creative Reviewer — it uses AI (Gemini 2.5 Pro + Video Intelligence API) to automate the whole thing.

**What it does:**
- Upload a video (or paste a YouTube URL)
- AI evaluates 23+ features: pacing, brand visibility, CTAs, product presence, etc.
- Each feature gets pass/fail + confidence score + specific recommendations
- Performance predictions: CPA risk, ROAS tier, creative fatigue
- Full PDF report

**Speed:** 30s video in ~2 min
**Cost:** $0.10-0.30 per video (GCP API costs)
**Accuracy:** 90-95% vs. human reviewers

It's open source and free. You just need a GCP project.

Would love feedback from people who actually run YouTube campaigns. What ABCD features matter most to you? What would make this more useful?

[LINK]

---

## r/advertising

**Title:** Built an AI tool that reviews video ads against YouTube's ABCD creative framework — free and open source

**Body:**

I work in the intersection of marketing and AI, and I kept seeing the same problem: creative teams spend hours manually reviewing video ads against best practice checklists, and the results are inconsistent between reviewers.

So I built Creative Reviewer — an open-source platform that uses Google AI to automatically score video ads against YouTube's ABCD framework:

- **Attract:** Hook effectiveness, pacing, dynamic start
- **Brand:** Logo presence, brand mentions (visual and audio)
- **Connect:** Human presence, faces, emotional elements
- **Direct:** Call-to-action clarity (spoken and text)

Beyond ABCD, it also detects persuasion tactics (social proof, scarcity, authority, etc.), analyzes narrative structure, and predicts performance metrics like CPA risk and ROAS potential.

Each feature comes with a confidence score, rationale, evidence, and actionable recommendations.

I've been using it to do "Ad of the Week" analyses on well-known campaigns and the results have been surprisingly insightful — especially when it reveals what even big-budget ads miss.

It's free, open source, and runs in your own GCP project. Happy to answer any questions or run your ads through it.

[LINK]

---

## r/machinelearning

**Title:** [P] Video ad evaluation system using Gemini 2.5 Pro + Video Intelligence API — hybrid annotation/LLM approach

**Body:**

I built an open-source system that evaluates video ads against a structured framework (YouTube's ABCD) using a hybrid approach combining Google's Video Intelligence API annotations with Gemini 2.5 Pro LLM reasoning.

**Architecture:**

The core challenge is that some evaluation features are objective (e.g., "are there 5+ shot changes in 5 seconds?" — measurable from annotations) while others are subjective (e.g., "does this ad create emotional resonance?" — requires LLM reasoning).

**Three evaluation modes per feature:**

1. **Annotations only** — Video Intelligence API extracts structured data: shot boundaries, face detection (size, position, timing), OCR (text on screen), speech transcription, logo recognition. Used for features where ground truth is available.

2. **LLM only** — Video sent to Gemini 2.5 Pro with a per-feature prompt. Returns: detected (bool), confidence (0.0-1.0), rationale, evidence, strengths, weaknesses. Used for subjective/abstract features.

3. **Hybrid** — Both pipelines run. Annotations provide structured data, LLM provides reasoning on top. Best results for features needing both.

**Feature batching:** Features are grouped by video segment (full video vs. first 5 seconds) and evaluated in batched LLM calls to reduce cost and latency.

**Accuracy:** ~90-95% agreement with human expert panel on a test set of 200+ ads. Main failure modes: LLM hallucination on edge cases, especially for brief/ambiguous visual elements.

**Performance predictions** are fully deterministic — a weighted scoring model maps binary feature results to CPA risk, ROAS tier, creative fatigue, and funnel strength. No LLM involved in predictions.

**Stack:** Python 3.11, FastAPI, Gemini 2.5 Pro + Flash, Video Intelligence API, FFmpeg, GCS, BigQuery.

Would appreciate feedback on the hybrid approach and how you'd handle LLM confidence calibration for video understanding tasks.

GitHub: [LINK]

---

## r/SideProject

**Title:** I built an AI that reviews video ads in 2 minutes — open source, free to use

**Body:**

Hey! I've been working on this for a while and finally got it to a point where I'm happy to share.

**What it is:** Creative Reviewer — an AI-powered tool that scores video ads against YouTube's ABCD creative framework.

**The problem:** Manually reviewing video ads is slow (30-60 min per video), expensive, and inconsistent.

**The solution:** Upload a video → AI evaluates 23+ features → Get a detailed PDF report with scores, evidence, and recommendations in ~2 minutes.

**Tech:** Gemini 2.5 Pro, Video Intelligence API, FastAPI, vanilla JS frontend with SSE streaming.

**What I learned building it:**
- LLMs are surprisingly good at video analysis but hallucinate on edge cases
- Combining structured annotations with LLM reasoning (hybrid approach) significantly improves accuracy
- Feature batching (grouping multiple evaluation prompts into one API call) cut costs by ~40%

It's open source: [LINK]

Would love feedback on the product and any features you'd want to see!
