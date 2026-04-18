# Hacker News — Show HN Post

**Best time to post:** Weekday mornings, 8-10 AM ET
**Key principle:** Lead with technical substance. HN readers value architecture and engineering decisions over marketing language.

---

## Title (80 chars max)

Show HN: AI video ad reviewer using Gemini 2.5 Pro + Video Intelligence API

---

## Post Body

I built an open-source tool that automatically evaluates video advertisements against YouTube's ABCD creative framework using Google AI.

**Architecture:**

The system uses three evaluation methods per feature:

1. **Annotations only** — Google Video Intelligence API extracts structured data (face detection, OCR, shot boundaries, speech transcription, logo recognition). Best for objective, measurable features like "are there 5+ shot changes in the first 5 seconds?"

2. **LLMs only** — Video is sent to Gemini 2.5 Pro with a tailored prompt per feature. Returns detected (bool), confidence (0-1), rationale, evidence, strengths, and weaknesses. Best for subjective features.

3. **Hybrid** — Both pipelines run. Annotations provide ground truth, Gemini provides reasoning on top. Most reliable for features requiring both data and interpretation.

**Pipeline:**
- FFmpeg trims video to first 5 seconds for time-gated features
- Flash model (Gemini 2.5 Flash) extracts brand metadata + scenes in a single call
- Pro model (Gemini 2.5 Pro) evaluates features in batched groups to minimize API calls
- Features are configured in a JSON repository — adding a new feature is just adding an entry
- Results go to BigQuery for trend analysis across videos

**Performance predictions** are deterministic (no LLM): a weighted scoring model maps feature pass/fail results to CPA risk, ROAS tier, creative fatigue, and funnel strength predictions.

**Accuracy:** ~90-95% vs. human expert review on a test set of 200+ ads. Main failure mode is LLM hallucination on edge cases (e.g., is a product "visible" when it appears for 0.3 seconds?).

**Cost:** ~$0.10-0.30 per video depending on length and which pipelines are enabled.

**Stack:** Python 3.11, FastAPI, Gemini 2.5 Pro/Flash, Video Intelligence API, FFmpeg, GCS, BigQuery. Web UI is vanilla JS with SSE streaming.

GitHub: [LINK]

---

## Tips for HN

1. **Don't use marketing language.** No "revolutionary" or "game-changing." Just describe what it does technically.
2. **Be ready to answer architecture questions.** HN readers will ask about accuracy, cost, hallucination handling, and scaling.
3. **Engage genuinely.** Answer every question in detail. Share failure modes honestly.
4. **Don't ask for upvotes.** Share the link with a few people and let it happen naturally.
