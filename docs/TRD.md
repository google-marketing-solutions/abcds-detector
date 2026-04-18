# Technical Requirements Document (TRD)
# AI Creative Review — ABCDs Detector

**Version:** 2.1
**Last Updated:** February 2026

---

## 1. Executive Summary

AI Creative Review (internally: ABCDs Detector) is an AI-powered SaaS platform that automatically evaluates video advertisements against YouTube's research-backed ABCD creative framework (Attract, Brand, Connect, Direct). The system combines Google's Video Intelligence API with Gemini LLMs to produce per-feature pass/fail reports with rationale, evidence, confidence scores, and actionable recommendations — delivering in minutes what a human reviewer would take hours to produce.

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌────────────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                                  │
│  Web UI (static HTML/JS)  │  REST API clients  │  CLI (main.py)   │
└──────────────┬─────────────────────┬──────────────────┬────────────┘
               │                     │                  │
               ▼                     ▼                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER (FastAPI)                       │
│                                                                    │
│  web_app.py — FastAPI app (uvicorn, 1 worker)                      │
│  ├── Auth (Google SSO + email/password, JWT sessions)              │
│  ├── Credit system (token-based, 10 tokens/sec of video)           │
│  ├── Evaluation pipeline (ABCD + Shorts + Creative Intelligence)   │
│  ├── Report generation (HTML, PDF, JSON)                           │
│  ├── SSE progress streaming                                        │
│  ├── A/B comparison engine                                         │
│  └── Admin dashboard API                                           │
│                                                                    │
│  Middleware: CORS, Security Headers, Rate Limiting (slowapi)       │
└──────────────┬─────────────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────────────┐
│                    DATA & AI LAYER                                  │
│                                                                    │
│  Google Video Intelligence API (annotations)                       │
│  Google Gemini 2.5 Pro (LLM video Q&A)                             │
│  Google Gemini 2.5 Flash (metadata + scene detection)              │
│  Google Knowledge Graph API (brand enrichment)                     │
│  FFmpeg / FFprobe (video trimming, duration detection)             │
└──────────────┬─────────────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                    │
│                                                                    │
│  Google Cloud Storage (video files, reports JSON, keyframes)       │
│  BigQuery (feature evaluations, confidence calibration data)       │
│  SQLAlchemy DB (users, credits, renders, feedback, Stripe events)  │
│    └── SQLite (dev) / PostgreSQL (production)                      │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 Deployment

- **Runtime:** Python 3.11 on Cloud Run (single container)
- **Container:** Docker image based on `python:3.11-slim` with FFmpeg
- **Web Server:** Uvicorn (1 worker, async)
- **Database:** SQLite for development, PostgreSQL for production
- **GCP Project:** `abcds-detector-488021`
- **Region:** `us-central1`

### 2.3 Technology Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI 0.115 |
| Server | Uvicorn 0.34 |
| AI / LLM | Gemini 2.5 Pro + Flash (Vertex AI) |
| Video Analysis | Google Video Intelligence API |
| Object Storage | Google Cloud Storage |
| Analytics DB | BigQuery |
| App DB | SQLAlchemy 2.x + Alembic (SQLite / PostgreSQL) |
| Auth | Google OAuth 2.0, bcrypt, PyJWT |
| Payments | Stripe |
| PDF Generation | fpdf2 |
| Video Processing | FFmpeg, moviepy, yt-dlp |
| Rate Limiting | slowapi |
| Container | Docker, Cloud Run |

---

## 3. Core Domain: ABCD Evaluation Engine

### 3.1 ABCD Framework

The engine evaluates 23 long-form ABCD features across 4 dimensions:

**A — Attract (7 features):** Dynamic Start, Quick Pacing, Quick Pacing (First 5s), Supers, Supers with Audio, Overall Pacing, Audio Speech Early.

**B — Brand (4 features):** Brand Visuals, Brand Visuals (First 5s), Brand Mention (Speech), Brand Mention (Speech) (First 5s).

**C — Connect (10 features):** Product Visuals, Product Visuals (First 5s), Product Mention (Speech), Product Mention (Speech) (First 5s), Product Mention (Text), Product Mention (Text) (First 5s), Presence of People, Presence of People (First 5s), Visible Face (First 5s), Visible Face (Close Up).

**D — Direct (2 features):** Call To Action (Speech), Call To Action (Text).

### 3.2 Scoring

- **≥ 80%** → Excellent
- **65–79%** → Might Improve
- **< 65%** → Needs Review

### 3.3 Evaluation Methods

Each feature uses one of three evaluation methods (configured in `features_repository/`):

1. **Annotations Only** — Video Intelligence API extracts structured data (face detection, OCR, speech transcription, shot boundaries, logo recognition). Best for objective, measurable features.
2. **LLMs Only** — Gemini receives the video with a tailored prompt and returns `{detected, confidence_score, rationale, evidence, strengths, weaknesses}`. Best for subjective or abstract features.
3. **Hybrid (Annotations + LLMs)** — Both pipelines run; annotations provide structured data, Gemini provides reasoning on top.

### 3.4 Feature Categories

| Category | Description |
|---|---|
| `LONG_FORM_ABCD` | Core 23-feature ABCD evaluation |
| `SHORTS` | YouTube Shorts-specific features (22 features) |
| `CREATIVE_INTELLIGENCE` | Persuasion, structure, and accessibility analysis |

### 3.5 Video Segments

Features are grouped by which video segment they analyze:
- `FULL_VIDEO` — Entire video
- `FIRST_5_SECS_VIDEO` — First 5 seconds (trimmed via FFmpeg)
- `LAST_5_SECS_VIDEO` — Last 5 seconds
- `NO_GROUPING` — Evaluated individually

### 3.6 Creative Providers

| Provider | Description |
|---|---|
| `GCS` | Videos from a Google Cloud Storage bucket. Supports annotations + LLMs. |
| `YOUTUBE` | Public YouTube URLs. LLMs only (annotations require GCS). |
| Custom | Implement `get_creative_uris()` per `creative_provider_proto.py`. |

---

## 4. Evaluation Pipeline (Web App)

The web-facing pipeline (`run_evaluation()`) is optimised for latency:

1. **Cache check** — MD5 hash of `(video_uri, use_abcd, use_shorts, use_ci)`.
2. **Video trim** — FFmpeg trims to first 5 seconds for "first 5s" features (GCS only).
3. **Metadata + scene detection** (parallel) — Single Gemini Flash call extracts brand metadata (name, variations, products, CTAs) and scene-by-scene breakdown. Video download runs concurrently.
4. **ABCD + CI + Shorts evaluation** (parallel, up to 3 threads) — Gemini Pro evaluates all enabled feature categories concurrently.
5. **Post-processing** (parallel, up to 6 threads) — Keyframe extraction, volume analysis, brand intelligence, video metadata, creative brief generation, audio richness analysis.
6. **BigQuery logging** — Fire-and-forget background thread.
7. **Report assembly** — Formats results into JSON with scores, action plan, feature timeline, platform fit, benchmarks, and comparison data.

### 4.1 Output Structure

The evaluation produces a comprehensive JSON report containing:

- `abcd` — Score, result tier, per-feature pass/fail with evidence
- `persuasion` — Persuasion density score and detected techniques
- `structure` — Narrative structure analysis
- `accessibility` — Captions, contrast, speech rate, audio dependence
- `scenes` — Per-scene breakdown with keyframes, emotion, sentiment, music mood
- `concept` — Creative brief (one-line pitch, key message, emotional hook, USP)
- `predictions` — Performance prediction scores
- `brand_intelligence` — Company profile, positioning, target audience
- `video_metadata` — Duration, resolution, codec
- `emotional_coherence` — Smooth emotional flow score, flagged shifts
- `audio_analysis` — Audio richness metrics
- `action_plan` — Prioritised recommendations (high/medium/low)
- `feature_timeline` — Time-mapped feature activations
- `platform_fit` — YouTube, Instagram, TikTok optimisation scores
- `benchmarks` — Performance vs. industry benchmarks
- `reference_ads` — Similar high-performing reference ads

---

## 5. Authentication & Authorization

### 5.1 Auth Methods

1. **Google SSO** — OAuth 2.0 authorization code flow. Verified email required.
2. **Email/Password** — bcrypt-hashed passwords, email verification via token.
3. **Account Linking** — Google login auto-links to existing email/password account.

### 5.2 Session Management

- JWT tokens stored in `httponly`, `secure`, `samesite=lax` cookies.
- 24-hour session TTL.
- Secret key: `SESSION_SECRET` env var (must be set in production).

### 5.3 Security Measures

- **Rate limiting:** 200 req/min global, 10 auth attempts per 5-min window per IP.
- **Account lockout:** 5 failed logins → 15-minute lockout.
- **Password policy:** 8+ chars, letters + numbers, common password blocklist.
- **CSRF protection:** JSON content-type enforcement on mutation endpoints.
- **Security headers:** X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS (production).

### 5.4 Admin Access

Admin privileges are email-allowlisted in `admin.py`. Admins can manage renders, grant credits, issue refunds, export data, and access calibration stats.

---

## 6. Credit System

### 6.1 Pricing Model

| Parameter | Value |
|---|---|
| Rate | 10 tokens per second of video |
| Max video duration | 60 seconds |
| Max tokens per video | 600 |
| Min balance to start | 100 tokens |
| Max file size | 50 MB |
| Signup bonus | 1,000 tokens |

### 6.2 Token Packs (Stripe)

| Pack | Price | Tokens |
|---|---|---|
| `TOKENS_1000` | $10 | 1,000 |
| `TOKENS_3000` | $25 | 3,000 |

### 6.3 Credit Flow

1. User uploads video → file size validated.
2. FFprobe detects duration → tokens calculated (`ceil(duration_s) * 10`).
3. Credits deducted upfront (max 600 for SSE flow, actual for direct API).
4. `CreditTransaction` logged with type `debit`, reason `video_evaluation`.
5. Admin can refund credits via admin API.

### 6.4 Concurrency Control

One active evaluation job per user, enforced via in-memory slot tracking (`_active_jobs` dict).

---

## 7. Database Schema

### 7.1 Tables

**`users`** — User accounts.
- `id` (PK), `google_sub`, `email` (unique), `password_hash`, `email_verified`, `verification_token`, `reset_token`, `token_expires_at`, `stripe_customer_id`, `is_admin`, `credits_balance`, `created_at`, `updated_at`, `last_login`.

**`credit_transactions`** — Credit ledger.
- `id` (PK), `user_id` (FK → users), `type` ("grant" | "debit"), `amount`, `reason`, `job_id`, `created_at`.

**`renders`** — Evaluation job history.
- `render_id` (PK), `status`, `progress_pct`, `created_at`, `started_at`, `finished_at`, `user_id` (FK → users), `user_email`, `source_type`, `source_ref`, `input_assets` (JSON), `prompt_text`, `config_json`, `output_url`, `thumbnail_url`, `duration_seconds`, `file_size_mb`, `pipeline_version`, `model`, `tokens_estimated`, `tokens_used`, `error_code`, `error_message`, `logs_url`, `webhook_failures_count`.

**`feature_feedback`** — Human accuracy feedback.
- `id` (PK), `report_id`, `feature_id`, `verdict` ("correct" | "incorrect"), `user_id` (FK → users), `created_at`.

**`processed_stripe_events`** — Idempotency guard for Stripe webhooks.
- `stripe_event_id` (PK), `stripe_session_id`, `processed_at`.

### 7.2 Migrations

Managed via Alembic. Initial schema in `alembic/versions/001_initial_schema.py`.

---

## 8. Integrations

### 8.1 Google Cloud

| Service | Purpose |
|---|---|
| Vertex AI (Gemini) | LLM-based video analysis, brand intelligence, scene detection |
| Video Intelligence API | Face, object, text, speech, shot, logo annotations |
| Cloud Storage | Video file hosting, report persistence |
| BigQuery | Evaluation history, confidence calibration data |
| Knowledge Graph API | Brand enrichment |

### 8.2 Stripe

- Customer creation on user signup.
- Checkout Sessions for token pack purchases.
- Webhook (`checkout.session.completed`) for credit fulfillment with idempotency.

### 8.3 Slack

- Optional webhook notifications on evaluation completion.
- Configured via `SLACK_WEBHOOK_URL` env var.

### 8.4 SMTP (Email)

- Verification emails and password reset links.
- Configured via `email_service.py`. Falls back to console logging if not configured.

---

## 9. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_CLIENT_ID` | For SSO | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For SSO | Google OAuth client secret |
| `SESSION_SECRET` | Production | JWT signing key (must be unique, secure) |
| `DATABASE_URL` | No | DB connection string (default: `sqlite:///data/app.db`) |
| `STRIPE_SECRET_KEY` | For billing | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | For billing | Stripe webhook signing secret |
| `STRIPE_PRICE_1000` | For billing | Stripe Price ID for 1000-token pack |
| `STRIPE_PRICE_3000` | For billing | Stripe Price ID for 3000-token pack |
| `ABCD_KG_API_KEY` | For KG | Knowledge Graph API key |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for notifications |
| `PUBLIC_BASE_URL` | Production | Public URL for report links |
| `ALLOWED_ORIGINS` | Production | Comma-separated CORS origins |
| `ENVIRONMENT` | Production | Set to `production` for security hardening |
| `IMAGEIO_FFMPEG_EXE` | Local dev | Path to FFmpeg binary |

---

## 10. Non-Functional Requirements

### 10.1 Performance

- Evaluation latency: 2-5 minutes per video (LLM-dependent).
- SSE streaming provides real-time progress updates during evaluation.
- Results cached in-memory and persisted to GCS for subsequent retrieval.

### 10.2 Scalability

- Cloud Run auto-scales container instances.
- PostgreSQL connection pooling (pool_size=5, max_overflow=10).
- Background threads for non-critical I/O (BQ logging, GCS persistence, Slack).

### 10.3 Reliability

- Health check endpoint (`/health`) with database probe.
- Stripe webhook idempotency via `processed_stripe_events` table.
- Graceful error handling with per-task exception isolation in parallel pipelines.

### 10.4 Security

- Session cookies: httponly, secure, samesite=lax.
- HSTS in production.
- Rate limiting on auth and evaluation endpoints.
- Filename sanitisation on uploads.
- No plaintext secrets in logs or responses.

### 10.5 Cost

| Service | Estimated Cost per Video |
|---|---|
| Video Intelligence API | ~$0.10–$0.30 / min |
| Gemini (Vertex AI) | ~$0.05–$0.15 / video |
| BigQuery | Negligible |
| **Total (both pipelines)** | **~$0.15–$0.45** |
| **Total (LLM-only)** | **~$0.05–$0.15** |

---

## 11. Known Limitations

1. **LLM accuracy:** Gemini can hallucinate — false positives/negatives are expected. Designed for screening at scale with optional human QA.
2. **YouTube URLs:** LLM evaluation only (Video Intelligence API requires GCS-hosted videos).
3. **Concurrency:** One active evaluation per user (in-memory slot tracking).
4. **Results cache:** In-memory dict — lost on container restart (GCS persistence mitigates this).
5. **Max video duration:** 60 seconds.
6. **Max file size:** 50 MB.
