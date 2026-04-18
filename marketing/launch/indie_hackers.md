# Indie Hackers Launch Post

---

## Title

I built an AI that reviews video ads in 2 minutes — here's the journey

## Body

Hey IH community 👋

I just launched **Creative Reviewer** — an open-source, AI-powered platform that automatically evaluates video ads against YouTube's ABCD framework.

### The Origin Story

I watched a creative team spend an entire afternoon manually scoring video ads against a 23-item checklist. One person with a stopwatch, counting shot changes, checking for brand visibility in the first 5 seconds, looking for calls-to-action.

For each video. One at a time.

I realized AI was finally good enough to automate this — especially with Google's Gemini model being able to actually "watch" videos and reason about them.

### What It Does

You upload a video (or paste a YouTube URL), and the AI:

- Scores 23+ creative features (pacing, branding, CTAs, product visibility, etc.)
- Detects persuasion tactics (social proof, scarcity, authority)
- Analyzes narrative structure
- Predicts performance (CPA risk, ROAS potential, creative fatigue)
- Generates a full PDF report with confidence scores and evidence

**Speed:** 30s video → ~2 min analysis
**Cost:** $0.10-$0.30 per video (GCP API costs)
**Accuracy:** 90-95% vs. human experts

### The Tech Stack

- **AI:** Gemini 2.5 Pro + Flash, Video Intelligence API
- **Backend:** Python 3.11, FastAPI
- **Frontend:** Vanilla JS, SSE streaming for real-time progress
- **Infrastructure:** GCS, BigQuery, FFmpeg

### Building in Public

I'm tracking the journey of growing this from a side project into something agencies and brands actually use. No paid marketing budget — just organic content, community building, and making the product genuinely useful.

My plan:
- **Weekly "Ad of the Week"** — Run famous ads through the tool and publish the analysis
- **Open source community** — Make it easy for developers to contribute and extend
- **Agency pilots** — Partner with agencies for case studies

### Try It

GitHub: [LINK]
Web UI: [LINK]

It's 100% open source under Apache 2.0. Self-hosted in your own GCP project.

**Would love to hear:**
1. Has anyone here built tools for the advertising/marketing space?
2. What's your experience with open-source growth strategies?
3. Any feedback on the product itself?
