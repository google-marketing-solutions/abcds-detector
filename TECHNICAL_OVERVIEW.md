# Creative Reviewer — Complete Technical Overview

## What It Does

A web application that evaluates video advertisements against YouTube's **ABCD creative framework** (Attract, Brand, Connect, Direct) using AI. Users upload a video (or paste a YouTube URL), and the app produces a detailed report covering creative effectiveness, persuasion tactics, brand intelligence, scene analysis, performance predictions, and more.

## Tech Stack

**Backend:** Python 3.11 + **FastAPI** (async web framework), served via **Uvicorn** ASGI server.

**AI / LLM:** Google **Gemini 2.5 Pro** (primary model for ABCD evaluation, brand intelligence, creative intelligence) and **Gemini 2.5 Flash** (faster model for metadata extraction + scene detection). Accessed via the **Google GenAI SDK** (`google-genai`) with Vertex AI as the backend.

**Video Processing:** **FFmpeg** — transcodes uploads to 720p, extracts keyframe images per scene, runs `volumedetect` audio analysis per scene, and uses **ffprobe** for technical metadata (resolution, codec, FPS, duration). **yt-dlp** downloads YouTube videos locally for processing.

**Cloud Infrastructure:** Hosted on **Google Cloud Run** (`us-central1`, 2 CPU / 2GB RAM, min 1 instance). Video files stored in **Google Cloud Storage** (`gs://abcds-detector-488021-videos`). Evaluation results logged to **BigQuery** (`abcd_detector_ds.abcd_assessments` + `confidence_calibration`).

**Database:** **SQLite** (WAL mode) via **SQLAlchemy** ORM — stores users, credit transactions, render history, and processed Stripe events. DB file at `data/app.db`.

**Auth:** **Google OAuth 2.0** (Workspace accounts only — consumer Gmail is blocked). Session managed via signed **JWT** cookies (HS256, 24-hour TTL). New users get 1,000 signup credits.

**Billing:** **Stripe** Checkout Sessions for token pack purchases. Webhook fulfillment with idempotency (tracks processed event IDs). Two packs: 1,000 tokens/$10, 3,000 tokens/$25.

**Notifications:** **Slack** incoming webhook — sends a rich Block Kit message with scores, scene timeline, brand intel, and a report link after each evaluation.

**Reports:** Self-contained **HTML** report (inline styles, Google Fonts, embedded base64 keyframes, YouTube iframe or `<video>` embed). Also generates **PDF** reports via **fpdf2**. Both formats include all report sections.

**Frontend:** Single-page HTML/CSS/JS app (`static/index.html`) with an admin dashboard (`static/admin.html`). Dark branded theme. No build tooling — vanilla JS with SSE for real-time progress.

---

## Evaluation Pipeline (Step by Step)

The core pipeline runs in `run_evaluation()` in `web_app.py`:

### Step 0 — Cache Check

In-memory dict keyed by MD5 of `video_uri + config flags`. Returns instantly if the same video/config was already evaluated this instance lifetime.

### Step 1 — Video Trim

For GCS videos with ABCD evaluation enabled, trims the video for first-5-seconds feature analysis using FFmpeg.

### Step 2 — Metadata + Scenes (parallel with download)

Two tasks run in parallel via `ThreadPoolExecutor(2)`:

- **Combined metadata + scene detection** — single **Gemini Flash** call (`extract_metadata_and_scenes`). Returns brand name, brand variations, products, CTAs, and a chronological scene list with timestamps, descriptions, and transcripts.
- **Video download** — downloads the video from GCS (via `gcs_api_service`) or YouTube (via `yt-dlp`) to a local temp directory for FFmpeg processing.

### Step 3 — ABCD + Creative Intelligence (parallel)

Up to 3 tasks in parallel via `ThreadPoolExecutor(3)`:

- **ABCD evaluation** — sends the video + all ABCD feature definitions to **Gemini Pro**. The LLM returns structured JSON per the `VIDEO_RESPONSE_SCHEMA` (id, name, detected, confidence_score, rationale, evidence, strengths, weaknesses). All features grouped as `FULL_VIDEO` — single LLM call.
- **Creative Intelligence** — same flow for persuasion tactics + structure features.
- **Shorts** (optional) — YouTube Shorts-specific features.

Partial results are streamed to the frontend via SSE as each task completes (score preview).

### Step 4 — BigQuery Logging

Fire-and-forget daemon thread writes all feature evaluations to BigQuery (`abcd_assessments` table) plus confidence calibration data.

### Step 5 — Post-processing (parallel)

Four tasks in parallel via `ThreadPoolExecutor(4)`:

- **Keyframe extraction** — FFmpeg seeks to each scene's start timestamp and extracts a 640×360 JPEG, base64-encoded.
- **Volume analysis** — FFmpeg `volumedetect` measures mean dB per scene, normalised to 0–100%. Flags jumps > 10% between adjacent scenes.
- **Brand intelligence** — **Gemini Pro** with the video produces a comprehensive brand brief (company info, audience, products/pricing, tone/voice, credibility signals, media channels, messaging themes, offers/CTAs). Uses `BRAND_INTELLIGENCE_RESPONSE_SCHEMA`.
- **Video metadata** — `ffprobe` extracts duration, resolution, aspect ratio, frame rate, codec, file size.

### Step 6 — Result Formatting

`format_results()` aggregates everything into a single JSON dict:

- **ABCD score** — `passed / total × 100`, labeled Excellent (≥80%), Might Improve (≥65%), or Needs Review.
- **Persuasion density** — detected tactics / total × 100.
- **Creative structure** — archetype identification.
- **Creative concept** — synthesized from scene descriptions + structure.
- **Performance predictions** — computed by `performance_predictor.py` (see below).
- **Scenes** — merged with keyframes + volume data.

---

## Performance Prediction Engine

`performance_predictor.py` — fully **deterministic, rule-based** (no LLM). Takes ABCD features, persuasion features, and structure features as input.

Groups ABCD features by sub-category (Attract, Brand, Connect, Direct) and computes **9 section scores**:

1. Hook & Attention
2. Brand Visibility
3. Social Proof & Trust
4. Product Clarity
5. Funnel Alignment
6. Call to Action
7. Creative Diversity
8. Measurement Readiness
9. Audience Leverage

From these, it derives 4 composite indices:

- **CPA Risk** — Conversion Readiness Index (CRI): weighted blend of section scores with penalty flags (missing hook, no trackable anchor, no product demo, no testimonial).
- **ROAS Tier** — Revenue Efficiency Index (REI): weighted blend with boosts/penalties.
- **Creative Fatigue Risk** — Refreshability Index (RFI): diversity + hook + measurement.
- **Funnel Strength** — scores TOF/MOF/BOF separately, picks winner (or hybrid if within 5%).

Overall performance score is the raw sum of all section scores (0–100).

---

## Credit / Token System

- **10 tokens per second** of video duration.
- **Max 60 seconds** per video, **50MB** file size limit.
- **Max 600 tokens** per evaluation.
- Credits deducted upfront before processing. 1 concurrent job per user.
- Duration measured via `ffprobe`. YouTube URL evaluations charge max (600) since duration is unknown upfront.

---

## API Endpoints

### Public

- `GET /` — frontend SPA
- `GET /report/{id}` — shareable HTML report
- `GET /auth/login` — Google OAuth redirect
- `GET /auth/callback` — OAuth callback
- `POST /webhooks/stripe` — Stripe webhook (signature verified)

### Authenticated

- `POST /api/upload` — upload video to GCS (size + credit pre-check)
- `POST /api/evaluate` — run evaluation with SSE progress streaming
- `POST /api/evaluate_file` — upload + evaluate in one call (JSON response)
- `GET /api/report/{id}/pdf` — download PDF report
- `GET /api/results/{id}` — get raw JSON results
- `GET /api/video/{id}` — stream video from GCS
- `GET /api/keyframe/{id}/{idx}` — serve scene keyframe image
- `GET /auth/me` — current user + balance + token model
- `GET /auth/transactions` — credit transaction history
- `POST /auth/logout` — clear session
- `GET /billing/packs` — available token packs
- `POST /billing/checkout-session` — create Stripe checkout

### Admin (`/admin/api/*`, restricted to allowlisted emails)

- `GET /renders` — paginated, filterable render list
- `GET /renders/{id}` — render detail
- `POST /renders/{id}/rerun` — re-queue a render
- `POST /renders/{id}/cancel` — cancel in-progress render
- `POST /renders/{id}/refund` — refund credits
- `DELETE /renders/{id}/output` — delete output artifacts
- `GET /renders/export` — CSV export
- `POST /renders/bulk` — bulk rerun/refund/delete

---

## Report Generation

`report_service.py` generates both HTML and PDF reports.

**HTML report** — self-contained single HTML file with inline CSS, Google Inter font, and embedded base64 keyframe images. Sections: video embed (YouTube iframe or `<video>`), score cards, executive summary, scene timeline with keyframes, creative metadata, creative concept, performance score breakdown with bar charts, ABCD feature results table (pass/fail + rationale/evidence/strengths/weaknesses per feature), persuasion tactics, creative structure, volume chart (SVG bar chart), and brand intelligence brief.

**PDF report** — generated with fpdf2. Same sections as HTML. Text sanitised for latin-1 encoding.

**Slack notification** — Block Kit message with all sections, truncated to Slack's 3000-char limits.

---

## Database Schema

### `users`

- `id` (PK, UUID), `google_sub` (unique), `email` (unique), `stripe_customer_id`, `is_admin`, `credits_balance`, `created_at`, `updated_at`, `last_login`

### `credit_transactions`

- `id` (PK, UUID), `user_id` (FK → users), `type` ("grant" | "debit"), `amount`, `reason`, `job_id`, `created_at`

### `renders`

- `render_id` (PK), `status` (queued/rendering/succeeded/failed/canceled), `progress_pct`, timestamps, `user_id` (FK → users), `user_email`, `source_type` (upload/url/api), `source_ref`, `prompt_text`, `config_json`, `output_url`, `duration_seconds`, `file_size_mb`, `pipeline_version`, `model`, `tokens_estimated`, `tokens_used`, `error_code`, `error_message`

### `processed_stripe_events`

- `stripe_event_id` (PK), `stripe_session_id`, `processed_at`

---

## Key Files

| File | Purpose |
|---|---|
| `web_app.py` | FastAPI app, endpoints, evaluation pipeline orchestration |
| `models.py` | Data classes (VideoFeature, FeatureEvaluation, VideoAssessment), enums, JSON schemas |
| `configuration.py` | Configuration class with all pipeline parameters |
| `scene_detector.py` | Gemini scene detection, brand metadata extraction, FFmpeg keyframes/volume/metadata |
| `performance_predictor.py` | Deterministic performance prediction engine |
| `report_service.py` | HTML/PDF report generation, Slack notifications |
| `db.py` | SQLAlchemy models and session management |
| `auth.py` | Google OAuth 2.0 login, JWT session, user endpoints |
| `billing.py` | Stripe checkout and webhook fulfillment |
| `credits.py` | Token pricing, duration detection, credit management |
| `admin.py` | Admin API: render management, CSV export, bulk actions |
| `Dockerfile` | Python 3.11-slim + FFmpeg, runs on port 8080 |

---

## Startup Behavior

On app startup (`@app.on_event("startup")`):

1. Initialises SQLite database (creates tables if missing).
2. Pre-warms Gemini connection in a background thread (tiny "ping" request to Flash model to establish HTTP connection pool).
