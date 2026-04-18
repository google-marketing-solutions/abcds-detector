# AI Creative Review — Product Requirements Document

**Product:** AI Creative Review (Upscale TV Creative Reviewer)
**Base Project:** ABCDs Detector (forked from Google Marketing Solutions)
**Version:** 2.1
**Date:** February 23, 2026

# 1. Problem Statement

Manually evaluating video advertisements against creative best practices is slow, expensive, subjective, and doesn't scale. A single human review of one video against YouTube's 23-point ABCD framework takes 30–60 minutes, and results vary between reviewers. Agencies, brands, and media buyers need a fast, consistent, and data-driven way to score video creatives before launch — identifying weaknesses, predicting performance, and benchmarking against historical data.

# 2. Product Vision

AI Creative Review is a SaaS platform that uses Google AI to automatically evaluate video ads against YouTube's research-backed ABCD framework, detect persuasion tactics, predict performance metrics, analyze scenes, and generate shareable reports — delivering in minutes what a human reviewer does in an hour, at a fraction of the cost (~$0.10–$0.30 per video).

# 3. Target Users

**Primary:**
- **Performance Marketing Agencies** — Pre-test client ads, QA creative output, enforce guidelines across teams
- **Brand Marketing Teams** — Audit video libraries, ensure creative consistency, train internal creators
- **Media Buyers** — Creative QA before campaign launch, predict CPA/ROAS, detect fatigue risk

**Secondary:**
- **Ad Platforms / Networks** — Automated quality scoring, creative gates, attribution
- **Researchers** — Large-scale creative analysis, trend identification across verticals

# 4. Core Capabilities

## 4.1 ABCD Framework Evaluation

Evaluates 23 features across YouTube's four ABCD dimensions:

**Attract (7 features):** Dynamic Start, Quick Pacing, Quick Pacing (First 5s), Supers, Supers with Audio, Overall Pacing, Audio Speech Early

**Brand (4 features):** Brand Visuals, Brand Visuals (First 5s), Brand Mention (Speech), Brand Mention (Speech) (First 5s)

**Connect (10 features):** Product Visuals, Product Visuals (First 5s), Product Mention (Speech/Text with 5s variants), Presence of People (with 5s variant), Visible Face (First 5s), Visible Face (Close Up)

**Direct (2 features):** Call To Action (Speech), Call To Action (Text)

Each feature returns: `detected` (bool), `confidence_score` (0.0–1.0), `rationale`, `evidence`, `strengths`, `weaknesses`.

**Scoring:** ≥80% → Excellent | 65–79% → Might Improve | <65% → Needs Review

**Evaluation methods per feature:**
- Annotations Only — Video Intelligence API structured data (faces, objects, text, speech, shots, logos)
- LLMs Only — Gemini 2.5 Pro watches the video with tailored prompts
- Hybrid — Both pipelines combined for higher reliability

**Key files:** `features_repository/long_form_abcd_features.py`, `evaluation_services/video_evaluation_service.py`, `llms_evaluation/llms_detector.py`

## 4.2 Creative Intelligence Layer

### 4.2.1 Persuasion Tactic Detection (7 features)

Detects psychological persuasion principles via Gemini:

1. **Scarcity** — Limited-time offers, limited stock messaging
2. **Social Proof** — Testimonials, reviews, ratings, endorsements
3. **Authority** — Expert endorsements, credentials, "clinically proven"
4. **Urgency** — Time-based pressure, countdown timers
5. **Risk Reversal** — Money-back guarantees, free trials
6. **Anchoring** — Crossed-out prices, value comparisons
7. **Price Framing** — Installment pricing, bundle values

Returns a **Persuasion Density** score (percentage of tactics detected).

### 4.2.2 Creative Structure Classification

Classifies videos into 9 narrative archetypes: UGC Testimonial, Founder Story, Problem-Solution, Before-After, Offer-Driven, Authority-Led, Demo-Focused, Lifestyle, Montage. Multiple archetypes can apply simultaneously.

**Key file:** `features_repository/creative_intelligence_features.py`

## 4.3 Performance Prediction Engine

Deterministic rules-based engine (model: `deterministic-rules.v1`). No additional LLM calls — same inputs always produce same outputs.

**9 Section Scores** (weighted sums of feature evaluations):
Hook & Attention (max 15), Brand Visibility (max 10), Social Proof & Trust (max 15), Product Clarity (max 15), Funnel Alignment (max 10), Call to Action (max 10), Creative Diversity (max 10), Measurement Readiness (max 10), Audience Leverage (max 5).

**4 Composite Indices:**
1. **Conversion Readiness Index (CRI)** → Predicted CPA Risk (Low / Medium / High)
2. **Revenue Efficiency Index (REI)** → Predicted ROAS Tier (High / Moderate / Low)
3. **Refreshability Index (RFI)** → Creative Fatigue Risk (Low / Medium / High)
4. **Funnel Strength** → Best-fit funnel stage (TOF / MOF / BOF / Hybrid)

**6 Boolean Flags:** hook_within_3s, brand_mentions_3x, has_trackable_anchor, has_testimonial_or_ugc, product_demo_present, end_card_present.

**Explainability:** Returns top 3 positive drivers, top 3 negative drivers, and all applied adjustments.

**Key file:** `performance_predictor.py` (~370 lines)

## 4.4 Scene Detection & Video Intelligence

### Scene Detection
Single Gemini Flash call extracts both brand metadata AND scene breakdown (`extract_metadata_and_scenes()`). Per scene: scene_number, start/end timestamps, description, transcript, emotion, sentiment_score, music_mood, has_music, speech_ratio.

### Keyframe Extraction
FFmpeg extracts one 640×360 JPEG frame per detected scene at the scene start time. Supports both GCS and YouTube videos (via yt-dlp download).

### Volume Analysis
FFmpeg `volumedetect` per scene. Outputs: volume_db, volume_pct (0–100), volume_change_pct, volume_flag (>10% jump between scenes).

### Emotional Arc
Sentiment scores per scene plotted as a line chart. Detects abrupt emotional shifts (>0.5 change between consecutive scenes).

### Video Metadata
FFprobe extracts: duration, resolution, aspect ratio, frame rate, file size, codec.

### Video Transcoding
Auto-downscales large videos to 720p (libx264, CRF 23) before processing.

**Key file:** `scene_detector.py` (~530 lines)

## 4.5 Brand Intelligence

Gemini Flash researches the brand and returns a 24-field brand brief: company name, website, founders, product/service, positioning, value proposition, mission, taglines, social proof, target audiences (primary + secondary), audience insights, pricing, tone, voice, credibility signals, paid media channels, creative formats, messaging themes, offers/CTAs.

**Key file:** `scene_detector.py` → `generate_brand_intelligence()`

## 4.6 Platform Optimization

Deterministic scoring engine (0–100) with optimization tips for 5 platforms:

- **YouTube Pre-Roll** — 16:9 aspect ratio, 15–60s duration, hook within 5s, brand early
- **Meta Feed** — Square/4:5, 15–30s, sound-off friendly, captions required
- **Meta Reels** — 9:16 vertical, <30s, fast pacing, UGC-style
- **TikTok** — 9:16 vertical, <60s, native feel, fast hook
- **Connected TV** — 16:9, 15–30s, high production, sound-on

Each platform returns a fit score and up to 3 actionable tips.

**Key file:** `platform_optimizer.py`

## 4.7 Historical Benchmarking

Maintains a local JSON history of evaluation scores. Computes percentile ranks (p10/p25/p50/p75/p90) for ABCD score, persuasion density, and performance score. Supports optional vertical filtering (e.g., e-commerce, SaaS, CPG) with fallback to global benchmarks when filtered set is too small (<10 entries).

**Key file:** `benchmarking.py`

## 4.8 Reference Ad Library

Curated library of high-scoring reference ads. Uses cosine similarity on 9-element normalized performance section score vectors to find the most similar ads. Supports optional vertical filtering. Returns top-K matches with similarity scores.

**Key file:** `reference_library.py`

## 4.9 Confidence Calibration

Human feedback loop: users can mark feature detections as "correct" or "incorrect" via `FeatureFeedback` table. System computes per-feature reliability levels (high/medium/low) based on accuracy and sample size. Applies Platt-style scaling (70% raw LLM confidence + 30% historical accuracy) to calibrate confidence scores over time.

**Key file:** `calibration.py`

## 4.10 YouTube Shorts Evaluation

Dedicated feature set for short-form content: production style, TV ad style, native content style, adaptation levels, emoji/trend usage, creative transitions, creator partnerships, personal character analysis, product context, video format, ad style analysis.

**Key file:** `features_repository/shorts_features.py`

# 5. SaaS Platform Layer

## 5.1 Web Application

**Framework:** FastAPI (v2.1), served via uvicorn on port 8080.

**Frontend:** Single-page app (`static/index.html`) — vanilla JS with drag-and-drop upload, real-time SSE progress streaming, expandable feature results, scene timeline with keyframe thumbnails, volume chart, and platform optimization cards.

**Pipeline Optimizations:**
1. Cache check (MD5 hash of video_uri + config)
2. Combined metadata + scene detection in single Flash LLM call
3. Video download in parallel with metadata extraction
4. ABCD + Creative Intelligence evaluations in parallel (3 ThreadPoolExecutors)
5. Keyframes, volume analysis, brand intelligence, and video metadata in parallel (4 workers)
6. Fire-and-forget BigQuery logging in daemon thread
7. SSE progress streaming to frontend

**Security middleware:** Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS in production), CORS, rate limiting (slowapi, 200/min default).

**Key file:** `web_app.py` (~993 lines)

## 5.2 API Endpoints

**Public:**
- `GET /` — Serve frontend HTML
- `GET /health` — Health check (database + version)
- `GET /report/{id}` — Shareable standalone HTML report
- `GET /api/report/{id}/pdf` — Download PDF report
- `GET /api/keyframe/{id}/{idx}` — Serve scene keyframe image
- `GET /api/video/{id}` — Stream video from GCS
- `GET /api/results/{id}` — Get cached JSON results

**Authenticated:**
- `POST /api/upload` — Upload video to GCS (file size + credit pre-check)
- `POST /api/evaluate` — Run evaluation with SSE progress streaming
- `POST /api/evaluate_file` — Upload + evaluate in single request, returns JSON

**Auth:**
- `GET /auth/login` — Redirect to Google OAuth
- `GET /auth/callback` — Handle OAuth callback
- `POST /auth/logout` — Clear session
- `GET /auth/me` — Current user data + token model info
- `GET /auth/transactions` — Paginated credit transaction history
- `POST /auth/register` — Email/password signup
- `POST /auth/login-email` — Email/password login
- `GET /auth/verify-email` — Email verification
- `POST /auth/forgot-password` — Request password reset
- `POST /auth/reset-password` — Complete password reset

**Billing:**
- `GET /billing/packs` — List token packs + current balance
- `POST /billing/checkout-session` — Create Stripe Checkout Session
- `POST /webhooks/stripe` — Handle Stripe webhook (signature-verified)

**Admin (restricted to ADMIN_EMAILS):**
- `GET /admin/api/renders` — Paginated, filtered render list
- `GET /admin/api/renders/{id}` — Render detail
- `POST /admin/api/renders/{id}/rerun` — Re-queue render
- `POST /admin/api/renders/{id}/cancel` — Cancel render
- `POST /admin/api/renders/{id}/refund` — Refund credits
- `DELETE /admin/api/renders/{id}/output` — Delete output artifacts
- `GET /admin/api/renders/export` — CSV export
- `POST /admin/api/renders/bulk` — Bulk actions

**Key files:** `web_app.py`, `auth.py`, `billing.py`, `admin.py`

## 5.3 Authentication

**Method 1:** Google OAuth 2.0 SSO with JWT session cookies (24-hour TTL).

**Method 2:** Email/password registration with email verification, password reset, bcrypt hashing.

**Access control:** Consumer Gmail accounts blocked in Google SSO — only Google Workspace allowed. Rate limiting (10 auth attempts per 5 minutes per IP). Account lockout (5 failures → 15 minute lock).

**Signup bonus:** 1,000 credits for new users.

**Key file:** `auth.py` (~300 lines)

## 5.4 Credit / Token System

**Pricing model:** 10 tokens per second of video. Max 60 seconds per video (600 tokens max). Max 50 MB file size. Minimum 100 tokens required to start a render.

**Token packs (Stripe):**
- 1,000 tokens — $10
- 3,000 tokens — $25

**Concurrency control:** 1 concurrent job per user (in-memory slot tracking).

**Key file:** `credits.py` (~169 lines)

## 5.5 Stripe Billing

Checkout Sessions + Webhooks integration. Signature verification, idempotent webhook processing via `ProcessedStripeEvent` table, automatic credit granting on successful payment.

**Key file:** `billing.py` (~196 lines)

## 5.6 Admin Dashboard

Full render management UI at `/admin`. Paginated, filtered render list with full-text search, status/source/user/time-range/duration/size/credit filters. Individual and bulk actions: rerun, cancel, refund, delete output, CSV export.

**Key files:** `admin.py` (~495 lines), `static/admin.html`

## 5.7 Database

**ORM:** SQLAlchemy 2.0+ with SQLite (WAL mode) for development, PostgreSQL-ready for production.

**Tables:**
- `users` — id, google_sub, email, password_hash, email_verified, stripe_customer_id, is_admin, credits_balance, timestamps
- `credit_transactions` — id, user_id, type (grant/debit), amount, reason, job_id, created_at
- `renders` — render_id, status, progress_pct, timestamps, user info, source info, input/output assets, config, pipeline metadata, error tracking
- `feature_feedback` — id, report_id, feature_id, verdict (correct/incorrect), user_id, created_at
- `processed_stripe_events` — stripe_event_id, stripe_session_id, processed_at

**Key file:** `db.py` (~191 lines)

# 6. Report Generation & Notifications

## 6.1 HTML Report

Self-contained, shareable HTML page served at `/report/{id}`. Sections: Header with branding, Video embed (YouTube iframe or GCS player), Score cards (Performance, ABCD, Persuasion Density, Brand), Executive summary, Video filename tags, Creative concept synthesis, Creative metadata (duration, resolution, etc.), Scene timeline with keyframe thumbnails, Voiceover volume levels (inline SVG bar chart), Emotional arc chart, Platform optimization scores, Reference ads, Performance prediction breakdown, ABCD feature results, Persuasion tactics, Creative structure archetypes, Brand intelligence brief.

**Design:** Light theme, Inter font, brand colors (#0A6D86 primary, #831F80 accent), responsive layout, printable.

## 6.2 PDF Report

fpdf2-based generation mirroring all HTML report sections in print-friendly format.

## 6.3 Slack Notifications

Rich Block Kit messages posted to Slack webhook. Includes all major report sections with link to full HTML report. Fire-and-forget via daemon thread.

## 6.4 Email Service

SMTP-based email service for auth flows (verification, password reset). Supports SendGrid, Gmail relay, SES, Mailgun via environment variables. Falls back to console logging in development.

**Key file:** `report_service.py` (~1306 lines), `email_service.py`

# 7. Video Ingestion & Providers

**Factory pattern** for pluggable creative providers:

1. **GCS Creative Provider** — Upload .mp4 files to GCS bucket. Supports individual files or entire folders. Full pipeline (annotations + LLMs).
2. **YouTube Creative Provider** — Provide public YouTube URLs. LLM-only evaluation (annotations require GCS). Keyframes extracted via yt-dlp download.
3. **Custom Providers** — Implement `get_creative_uris()` interface, register in `creative_provider_registry.py`.

**Video preprocessing:** FFMPEG trims first 5 seconds for time-gated features. Trimmed video uploaded to GCS and cached for future runs. Large videos auto-transcoded to 720p.

**Key files:** `creative_providers/` directory

# 8. GCP API Integrations

- **Google Video Intelligence API** — Label, face, text, object, people, speech, shot, and logo annotations
- **Vertex AI (Gemini 2.5 Pro)** — Feature evaluation (ABCD, Creative Intelligence)
- **Vertex AI (Gemini 2.5 Flash)** — Metadata extraction, scene detection, brand intelligence, creative concept synthesis
- **Google Cloud Storage** — Video storage and retrieval
- **BigQuery** — Evaluation result logging for dashboards and trend analysis
- **Knowledge Graph API** — Brand entity resolution (optional)

**Key files:** `gcp_api_services/` directory

# 9. CLI Interface

Original CLI entrypoint preserved for power users and batch processing:

```bash
python main.py -pi PROJECT_ID -bn BUCKET -vu "gs://..." -extvn -ull -rfa -v
```

Key flags: `-pi` (project ID), `-bn` (bucket), `-vu` (video URIs), `-brn` (brand name), `-extvn` (auto-extract brand metadata), `-ull` (use LLMs), `-uan` (use annotations), `-rfa` (run ABCD features), `-rs` (run Shorts), `-rci` (run Creative Intelligence), `-kgak` (Knowledge Graph API key), `-bd`/`-bt` (BigQuery dataset/table), `-v` (verbose).

**Key files:** `main.py`, `utils.py`

# 10. Infrastructure & Deployment

**Docker:** Python 3.11-slim base, FFmpeg installed, Cloud Run compatible. Health check at `/health` with 30s interval.

**Environment variables:**
- Google OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Session: `SESSION_SECRET` (enforced in production)
- Stripe: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_1000`, `STRIPE_PRICE_3000`
- Notifications: `SLACK_WEBHOOK_URL`, `SMTP_HOST/PORT/USER/PASSWORD/FROM`
- Application: `PUBLIC_BASE_URL`, `ABCD_KG_API_KEY`, `DATABASE_URL`, `ENVIRONMENT`, `ALLOWED_ORIGINS`
- Media: `IMAGEIO_FFMPEG_EXE`

**Database migrations:** Alembic for schema versioning.

**CI:** `.github/workflows/ci.yml` pipeline.

**Production hardening:** SESSION_SECRET enforcement, structured JSON logging for Cloud Logging, docs/redoc disabled, HSTS headers, CORS restricted.

# 11. Performance Characteristics

- **Processing time:** 30s video ≈ 2 min, 60s video ≈ 5 min
- **Accuracy:** 90–95% vs. human expert reviewers
- **Cost per video:** $0.10–$0.30 (both pipelines), $0.05–$0.15 (LLM-only)
- **Video limits:** Max 60 seconds, max 50 MB
- **Caching:** MD5-based evaluation caching; in-memory report storage by report_id
- **Concurrency:** 1 job per user; 3 ThreadPoolExecutors for parallel feature evaluation

# 12. Dependencies

**Python packages (22):** google-cloud-aiplatform, google-cloud-videointelligence, google-cloud-storage, google-cloud-bigquery, moviepy, google-api-python-client, pandas, pyarrow, fastapi, uvicorn, python-multipart, fpdf2, yt-dlp, sqlalchemy, alembic, psycopg2-binary, google-auth, requests, PyJWT, stripe, bcrypt, slowapi.

**System:** Python 3.11+, FFmpeg, yt-dlp.

**GCP APIs:** Video Intelligence, Vertex AI, Cloud Storage, BigQuery, Knowledge Graph (optional).

**External services:** Stripe (billing), Google OAuth (auth), SMTP provider (email, optional), Slack (notifications, optional).

# 13. Known Limitations & Caveats

1. **LLM accuracy is not 100%.** Gemini can hallucinate — false positives and negatives are expected. The tool is designed for screening at scale with human QA for critical decisions.
2. **YouTube URLs support LLM evaluation only.** Video Intelligence API requires GCS-hosted videos, so annotation-based features are skipped for YouTube URLs.
3. **Feature grouping affects cost.** Features can be batched (grouped) or evaluated individually (ungrouped). Individual evaluation costs more.
4. **First 5 seconds window is configurable.** Default is 5 seconds (`early_time_seconds`), adjustable in configuration.
5. **SQLite in development.** Production deployments should use PostgreSQL for concurrency.
6. **In-memory rate limiting and job slots.** Lost on process restart. Suitable for single-worker deployment.

# 14. Version History

**v2.1 (February 2026):** Direct upload API endpoint (`/api/evaluate_file`), YouTube keyframe extraction via yt-dlp, platform optimization scoring, reference ad library, historical benchmarking, confidence calibration, emotional arc analysis, email/password auth, email verification/password reset, cross-platform FFmpeg auto-detection, 30% faster processing via feature batching.

**v2.0:** FastAPI web application, Google SSO, SQLAlchemy database, credit/token system, Stripe billing, admin dashboard, SSE progress streaming, Creative Intelligence features, performance prediction engine, scene detection with keyframes, volume analysis, brand intelligence, HTML/PDF reports, Slack notifications, Docker deployment.

**v1.0 (Google original):** CLI-based ABCD evaluation using Video Intelligence API + Gemini, GCS video ingestion, BigQuery logging.
