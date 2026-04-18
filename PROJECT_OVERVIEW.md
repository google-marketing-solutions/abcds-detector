# ABCDs Detector — Project Overview

## What Is This?

ABCDs Detector is an AI-powered tool that watches your video ads and scores them against YouTube's proven ABCD creative framework. Instead of a human manually reviewing each ad against a checklist of 23+ best practices, the tool automates the entire process using Google's Video Intelligence API and Gemini LLM — delivering a detailed per-feature pass/fail report with rationale, evidence, and actionable feedback in minutes.

---

## The ABCD Framework

YouTube's ABCD framework is a research-backed set of creative principles that drive ad effectiveness. Every letter represents a dimension of what makes a video ad perform well:

### A — Attract
**Goal:** Hook the viewer immediately. You have ~5 seconds before they skip.

| Principle | What It Means |
|---|---|
| **Dynamic Start** | The first shot change happens within 3 seconds — no slow fades or static openings. |
| **Quick Pacing** | 5+ shot changes within any 5-second window — rapid cuts keep eyes locked. |
| **Quick Pacing (First 5s)** | Same rule, but specifically in the opening 5 seconds. |
| **Supers** | On-screen text overlays are present (titles, callouts, captions). |
| **Supers with Audio** | The text on screen is reinforced by matching spoken audio. |
| **Overall Pacing** | Average shot duration across the full video is under 2 seconds. |
| **Audio Early** | Speech or narration begins within the first 5 seconds. |

**Why it matters:** YouTube's own research shows that ads with a strong opening hook see significantly higher view-through rates and brand recall.

### B — Brand
**Goal:** Make the brand unmistakable. Viewers should know who's talking to them — early and often.

| Principle | What It Means |
|---|---|
| **Brand Visuals** | The brand logo or name appears on screen at any point. |
| **Brand Visuals (First 5s)** | Brand logo or name is visible within the first 5 seconds. |
| **Brand Mention (Speech)** | The brand name is spoken aloud at any point. |
| **Brand Mention (Speech) (First 5s)** | The brand name is spoken within the first 5 seconds. |

**Why it matters:** Ads that show or say the brand name in the first 5 seconds drive 2-3x higher ad recall compared to those that delay branding.

### C — Connect
**Goal:** Make the viewer feel something. Human presence creates emotional resonance.

| Principle | What It Means |
|---|---|
| **Product Visuals** | The product is visually shown at any point. |
| **Product Visuals (First 5s)** | The product appears on screen within the first 5 seconds. |
| **Product Mention (Speech)** | The product name is spoken aloud. |
| **Product Mention (Speech) (First 5s)** | The product name is spoken within the first 5 seconds. |
| **Product Mention (Text)** | The product name appears as on-screen text. |
| **Product Mention (Text) (First 5s)** | Product name appears as text within the first 5 seconds. |
| **Presence of People** | People (real or animated) appear anywhere in the video. |
| **Presence of People (First 5s)** | People are visible within the first 5 seconds. |
| **Visible Face (First 5s)** | A human face is visible within the first 5 seconds. |
| **Visible Face (Close Up)** | A close-up of a human face appears at any point. |

**Why it matters:** Ads featuring people — especially faces — generate stronger emotional engagement and purchase intent. Product visibility reinforces what's being sold so the message sticks.

### D — Direct
**Goal:** Tell the viewer what to do next. Don't leave them guessing.

| Principle | What It Means |
|---|---|
| **Call To Action (Speech)** | A spoken directive like "Shop now," "Learn more," or "Sign up." |
| **Call To Action (Text)** | A text overlay with the same type of directive. |

**Why it matters:** A clear CTA converts passive viewers into active customers. Ads with explicit CTAs see measurably higher click-through and conversion rates.

### Scoring
After evaluating all 23 features, the tool produces an overall adherence score:

- **≥ 80%** → ✅ **Excellent** — The ad follows ABCD best practices strongly.
- **65–79%** → ⚠ **Might Improve** — Solid foundation, but key gaps exist.
- **< 65%** → ❌ **Needs Review** — Significant ABCD gaps that likely hurt performance.

---

## How the Product Works

### Step 1: Video Ingestion
You provide video files via one of three **Creative Providers**:

- **Google Cloud Storage (GCS)** — Upload `.mp4` files to a GCS bucket. The tool reads them directly. Supports individual files or entire folders.
- **YouTube URLs** — Provide public YouTube video URLs. These are evaluated using LLMs only (annotations require GCS).
- **Custom Providers** — Build your own integration by implementing the `get_creative_uris()` interface.

### Step 2: Video Preprocessing
For features that analyze the "first 5 seconds," the tool:
1. Downloads the video from GCS
2. Uses **FFMPEG** to trim it to the first 5 seconds
3. Uploads the trimmed version back to GCS (cached for future runs)

### Step 3: Brand Metadata Extraction
If enabled (`-extvn` flag), the tool sends the full video to **Gemini** and asks it to identify:
- Brand name and variations
- Products shown and their categories
- Call-to-action phrases used

This metadata feeds into the subsequent feature evaluations, giving the LLM brand-specific context.

### Step 4: AI Evaluation (The Core Engine)
Each of the 23 features is evaluated using one of three methods:

```
┌─────────────────────────────────────────────────────────────┐
│                    EVALUATION METHODS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ANNOTATIONS ONLY                                          │
│  Google Video Intelligence API extracts structured data:    │
│  • Face detection (size, position, timing)                  │
│  • Object tracking (products, logos)                        │
│  • Text detection (OCR on supers/overlays)                  │
│  • Speech transcription (what's said and when)              │
│  • Shot boundary detection (cut timing)                     │
│  • Logo recognition (brand marks)                           │
│  Best for: measurable, objective features like shot count   │
│                                                             │
│  LLMs ONLY (Gemini)                                        │
│  The video is sent to Gemini with a tailored prompt:        │
│  "Does this video contain [specific feature]?"              │
│  Gemini watches the video and returns:                      │
│  • detected (true/false)                                    │
│  • confidence_score (0.0 – 1.0)                             │
│  • rationale (why it decided yes/no)                        │
│  • evidence (specific timestamps and observations)          │
│  • strengths (what the ad does well for this feature)       │
│  • weaknesses (what could improve)                          │
│  Best for: subjective or abstract features                  │
│                                                             │
│  ANNOTATIONS + LLMs (Hybrid)                               │
│  Both pipelines run. Annotations provide structured data,   │
│  and Gemini provides reasoning on top. The combined result  │
│  is more reliable than either alone.                        │
│  Best for: features requiring both data and interpretation  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Features are grouped by video segment (full video vs. first 5 seconds) and batched into efficient API calls to minimize cost.

### Step 5: Scoring & Output
After all features are evaluated, the tool:

1. **Prints a console report** — Pass/fail for each feature with detailed rationale, evidence, strengths, weaknesses, and confidence scores.
2. **Stores to BigQuery** (optional) — Every feature evaluation is written as a row with full metadata, enabling dashboards, trend analysis, and cross-video comparisons.
3. **Writes to file** (optional) — Local file output for offline review.

### End-to-End Flow Diagram

```
    ┌──────────────┐
    │  Your Videos  │
    │  (GCS/YouTube)│
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐     ┌─────────────────────┐
    │   Creative    │────▶│  FFMPEG Trim (5s)    │
    │   Provider    │     │  Upload trimmed copy  │
    └──────┬───────┘     └─────────────────────┘
           │
           ▼
    ┌──────────────┐
    │    Brand      │  Gemini extracts brand name,
    │   Metadata    │  products, categories, CTAs
    │  Extraction   │  from the video itself
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │         FEATURE EVALUATION               │
    │                                          │
    │  For each of 23 features:                │
    │  ┌────────────┐    ┌──────────────┐      │
    │  │ Annotations │    │  Gemini LLM  │      │
    │  │  (optional) │    │  (optional)  │      │
    │  └─────┬──────┘    └──────┬───────┘      │
    │        │                  │               │
    │        └────────┬─────────┘               │
    │                 ▼                         │
    │         ┌──────────────┐                  │
    │         │  Pass / Fail │                  │
    │         │  + Rationale │                  │
    │         │  + Evidence  │                  │
    │         │  + Strengths │                  │
    │         │  + Weaknesses│                  │
    │         └──────────────┘                  │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
    ┌─────────────────────────────────────────┐
    │              OUTPUT                      │
    │                                          │
    │  • Console: Full report with scores      │
    │  • BigQuery: Rows per feature per video  │
    │  • File: Local assessment output         │
    └─────────────────────────────────────────┘
```

---

## Our Deployment

| Component | Detail |
|---|---|
| **GCP Project** | `abcds-detector-488021` |
| **Authenticated As** | `kevin@kwangel.fund` |
| **APIs Enabled** | Video Intelligence, Vertex AI, Knowledge Graph, Cloud Storage, BigQuery |
| **Service Account** | `abcds-detector-sa` (storage, AI platform, BigQuery roles) |
| **GCS Bucket** | `gs://abcds-detector-488021-videos/` (us-central1) |
| **BigQuery Dataset** | `abcd_detector_ds.abcd_assessments` |
| **Local Repo** | `~/abcds-detector/` |
| **Python** | 3.11 with venv at `~/abcds-detector/.venv/` |
| **LLM Model** | Gemini 2.5 Pro |
| **FFMPEG** | `/opt/homebrew/bin/ffmpeg` |

### Running an Evaluation

```bash
source ~/.zshrc && source ~/abcds-detector/.venv/bin/activate && \
export IMAGEIO_FFMPEG_EXE=/opt/homebrew/bin/ffmpeg && \
python ~/abcds-detector/main.py \
  -pi abcds-detector-488021 \
  -bn abcds-detector-488021-videos \
  -vu "gs://abcds-detector-488021-videos/YOUR_VIDEO.mp4" \
  -extvn -ull -rfa -v \
  -kgak "$ABCD_KG_API_KEY" \
  -bd abcd_detector_ds -bt abcd_assessments
```

### Key Flags

| Flag | Purpose |
|---|---|
| `-pi` | GCP Project ID |
| `-bn` | GCS bucket name (not URI) |
| `-vu` | Comma-separated video URIs |
| `-brn` | Brand name (or use `-extvn` for auto-detection) |
| `-extvn` | Auto-extract brand metadata from video |
| `-ull` | Use LLMs for evaluation |
| `-uan` | Use Annotations for evaluation |
| `-rfa` | Run long-form ABCD features |
| `-rs` | Run YouTube Shorts features |
| `-kgak` | Knowledge Graph API key |
| `-bd` / `-bt` | BigQuery dataset / table for result storage |
| `-v` | Verbose output |

---

## Cost Per Video

| Service | Estimated Cost |
|---|---|
| Video Intelligence API | ~$0.10–$0.30 (per minute of video, per feature type) |
| Gemini (Vertex AI) | ~$0.05–$0.15 (per 1K chars input/output + per second of video) |
| BigQuery | Negligible (small row inserts) |
| **Total with both pipelines** | **~$0.15–$0.45 per video** |
| **Total LLM-only** | **~$0.05–$0.15 per video** |

---

## Important Caveats

1. **LLM results are not 100% accurate.** Gemini can hallucinate — false positives and false negatives are expected. The tool is designed for screening at scale, with human QA for critical decisions.

2. **YouTube URLs only support LLM evaluation.** The Video Intelligence API requires videos hosted in GCS, so annotation-based features are skipped for YouTube URLs.

3. **Feature grouping affects cost.** Features can be batched into single API calls (grouped) or evaluated individually (ungrouped). Individual evaluation is more expensive. This is configured in `features_repository.py`.

4. **The "first 5 seconds" window is configurable.** The default is 5 seconds (`early_time_seconds`), but this threshold can be adjusted in the configuration.
