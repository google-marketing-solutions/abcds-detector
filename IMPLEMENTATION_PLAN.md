# Creator-Reviewer Phase-Based Implementation Plan

**Product:** Upscale TV Creative Reviewer
**Base Project:** ABCDs Detector (forked from Google Marketing Solutions)
**Repo:** `~/abcds-detector/`
**Last Updated:** February 22, 2026

---

## Executive Summary

We transformed Google's open-source ABCDs Detector — a CLI tool that scores YouTube video ads against 23 ABCD features — into **Upscale TV Creative Reviewer**, a full SaaS product with a FastAPI web app, Google SSO auth, Stripe billing, an admin dashboard, performance prediction engine, brand intelligence, scene detection, and a rich shareable report output (HTML + PDF + Slack).

---

## Phase 1: Core Evaluation Engine (Foundation)

### What Was Built
The original Google Marketing Solutions ABCDs Detector provided CLI-based video evaluation using Google Video Intelligence API annotations and Gemini LLM. We kept this evaluation core intact and extended it.

### Core Evaluation Pipeline
**File:** `main.py` (CLI entrypoint), `evaluation_services/video_evaluation_service.py`

- **23 ABCD Features** across 4 dimensions (Attract, Brand, Connect, Direct)
- **3 Evaluation Methods:** Annotations-only, LLMs-only (Gemini), or Hybrid
- **Video Preprocessing:** FFMPEG trims first 5 seconds for time-gated features
- **Brand Metadata Extraction:** Gemini auto-identifies brand name, products, CTAs from video
- **BigQuery Logging:** Every feature evaluation stored as a row for dashboards

### Feature Repository
**Files:**
- `features_repository/long_form_abcd_features.py` — 23 ABCD features (Attract/Brand/Connect/Direct)
- `features_repository/shorts_features.py` — YouTube Shorts-specific features
- `features_repository/creative_intelligence_features.py` — 8 persuasion + structure features (Phase 2)
- `features_repository/feature_configs_handler.py` — Feature loading and grouping logic

### Data Models
**File:** `models.py`

- `VideoFeature` — Feature definition (id, name, category, sub_category, evaluation_criteria, prompt_template, evaluation_method)
- `FeatureEvaluation` — Result per feature (detected, confidence_score, rationale, evidence, strengths, weaknesses)
- `VideoAssessment` — Full video assessment container
- `LLMParameters` — Gemini model config (model_name, location, generation_config)
- `PromptConfig` — Prompt + system instructions
- JSON response schemas for video eval, scene detection, brand intelligence, metadata+scenes combo

### Creative Providers
**Files:** `creative_providers/`

- `gcs_creative_provider.py` — GCS bucket video ingestion
- `youtube_creative_provider.py` — YouTube URL evaluation (LLM-only)
- `creative_provider_proto.py` — Abstract base class
- `creative_provider_factory.py` — Factory pattern for provider selection
- `creative_provider_registry.py` — Provider registration

### GCP API Services
**Files:** `gcp_api_services/`

- `gemini_api_service.py` — Gemini 2.5 Pro/Flash integration via `google-genai` SDK
- `gcs_api_service.py` — Google Cloud Storage operations
- `bigquery_api_service.py` — BigQuery result storage

### Configuration
**File:** `configuration.py`

- Project ID, zone, bucket, BQ dataset/table
- LLM model selection (Gemini 2.5 Pro for eval, Flash for metadata)
- Feature evaluation toggles (ABCD, Shorts, Creative Intelligence)
- Brand details, video URIs, verbose mode

### Deployment
**File:** `Dockerfile`

- Python 3.11-slim base image
- FFmpeg installed for video processing
- Runs via `uvicorn` on port 8080
- Cloud Run compatible

---

## Phase 2: Creative Intelligence Layer

### What Was Built
Extended the evaluation engine beyond ABCD with persuasion tactic detection and creative structure classification.

### Persuasion Tactic Detection (7 features)
**File:** `features_repository/creative_intelligence_features.py`

Each tactic is evaluated by Gemini watching the full video:

1. **Scarcity** (`p_scarcity`) — Limited-time offers, limited stock, "while supplies last"
2. **Social Proof** (`p_social_proof`) — Testimonials, reviews, ratings, endorsements, "as seen on"
3. **Authority** (`p_authority`) — Expert endorsements, credentials, "clinically proven"
4. **Urgency** (`p_urgency`) — Time-based pressure: "act now", "today only", countdown timers
5. **Risk Reversal** (`p_risk_reversal`) — Money-back guarantees, free trials, "risk-free"
6. **Anchoring** (`p_anchoring`) — Crossed-out prices, "was $X now $Y", value comparisons
7. **Price Framing** (`p_price_framing`) — Installment pricing, "starting at", bundle values

### Creative Structure Classification (1 feature)
**Feature:** `s_creative_structure`

Classifies video into 9 archetypes:
- UGC Testimonial
- Founder Story
- Problem-Solution
- Before-After
- Offer-Driven
- Authority-Led
- Demo-Focused
- Lifestyle
- Montage

Multiple archetypes can apply. Returns primary archetype(s) in evidence field with reasoning.

### Performance Prediction Engine
**File:** `performance_predictor.py` (~370 lines)

**Model:** `deterministic-rules.v1` — same inputs always produce same outputs, no additional LLM calls.

**9 Section Scores** (weighted sums of feature evaluations):
- Hook & Attention (max 15)
- Brand Visibility (max 10)
- Social Proof & Trust (max 15)
- Product Clarity (max 15)
- Funnel Alignment (max 10)
- Call to Action (max 10)
- Creative Diversity (max 10)
- Measurement Readiness (max 10)
- Audience Leverage (max 5)

**4 Composite Indices:**

1. **Conversion Readiness Index (CRI) → Predicted CPA Risk**
   - Weighted: 22% Hook, 18% Product, 18% CTA, 14% Social Proof, 12% Brand, 10% Funnel, 6% Measurement
   - Penalties: no hook within 3s (-10%), no trackable anchor (-10%), no product demo (-7%), no testimonial/UGC (-5%)
   - Labels: CRI ≥ 0.72 → Low risk, ≥ 0.52 → Medium, else High

2. **Revenue Efficiency Index (REI) → Predicted ROAS Tier**
   - Weighted: 24% Product, 18% Social Proof, 14% Brand, 12% Funnel, 12% Hook, 10% CTA, 10% Creative Diversity
   - Boosts: trackable anchor (+5%), 3+ brand mentions (+3%), end card (+2%)
   - Penalties: low product clarity (-7%), low social proof (-5%)
   - Labels: REI ≥ 0.70 → High, ≥ 0.50 → Moderate, else Low

3. **Refreshability Index (RFI) → Creative Fatigue Risk**
   - Weighted: 55% Creative Diversity, 25% Hook, 20% Measurement
   - Labels: RFI ≥ 0.70 → Low risk, ≥ 0.50 → Medium, else High

4. **Funnel Strength (TOF / MOF / BOF)**
   - TOF: 35% Hook, 25% Brand, 20% Social Proof, 20% Story
   - MOF: 25% Social Proof, 25% Product, 20% Brand, 15% Hook, 15% CTA
   - BOF: 30% CTA, 25% Product, 20% Social Proof, 15% Measurement, 10% Funnel
   - Hybrid label when top two are within 5% (e.g., "TOF/MOF")

**6 Boolean Flags:**
- `hook_within_3s` — Dynamic start detected
- `brand_mentions_3x` — 3+ brand features detected
- `has_trackable_anchor` — URL, QR code, promo code in evidence
- `has_testimonial_or_ugc` — UGC/testimonial content detected
- `product_demo_present` — Product visuals shown
- `end_card_present` — CTA text overlay detected

**Explainability:** Top 3 positive drivers, top 3 negative drivers, and applied adjustments returned for transparency.

---

## Phase 3: Web Application & SaaS Layer

### FastAPI Web Application
**File:** `web_app.py` (~993 lines)

**App:** `Upscale TV Creative Review` (FastAPI, version 2.0)

**Mounted Routers:**
- `auth_router` — Google SSO authentication
- `billing_router` — Stripe billing
- `admin_router` — Admin dashboard API

**Core Pipeline Optimizations:**
1. Cache check (MD5 hash of video_uri + config)
2. Combined metadata + scene detection in single Flash LLM call
3. Video download in parallel with metadata extraction
4. ABCD + CI evaluations in parallel (3 ThreadPoolExecutors)
5. Keyframes + volume analysis + brand intelligence + video metadata in parallel (4 workers)
6. Fire-and-forget BigQuery logging in daemon thread
7. SSE progress streaming to frontend

**API Endpoints:**

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/` | GET | No | Serve frontend HTML |
| `/admin` | GET | Admin | Serve admin dashboard |
| `/api/upload` | POST | Yes | Upload video to GCS (file size + credit pre-check) |
| `/api/evaluate` | POST | Yes | Run eval with SSE progress streaming |
| `/api/evaluate_file` | POST | Yes | Upload + evaluate in single request, returns JSON |
| `/report/{id}` | GET | No | Shareable standalone HTML report |
| `/api/report/{id}/pdf` | GET | No | Download PDF report |
| `/api/keyframe/{id}/{idx}` | GET | No | Serve scene keyframe image |
| `/api/video/{id}` | GET | No | Stream video from GCS |
| `/api/results/{id}` | GET | No | Get cached JSON results |

**Startup:** Database initialization, Slack webhook check, Gemini connection pre-warm (Flash model ping).

**Models Used:**
- `gemini-2.5-pro` — Feature evaluation (ABCD, CI)
- `gemini-2.5-flash` — Metadata extraction, scene detection, brand intelligence

### Database Layer
**File:** `db.py` (~157 lines)

**ORM:** SQLAlchemy 2.0+ with SQLite (WAL mode for concurrency)
**Database:** `data/app.db`

**Tables:**

1. **`users`**
   - `id` (UUID PK), `google_sub` (unique), `email` (unique)
   - `stripe_customer_id`, `is_admin`, `credits_balance`
   - `created_at`, `updated_at`, `last_login`
   - Relationships: `transactions`, `renders`

2. **`credit_transactions`**
   - `id` (UUID PK), `user_id` (FK), `type` ("grant" | "debit")
   - `amount`, `reason`, `job_id`, `created_at`

3. **`renders`**
   - `render_id` (UUID PK), `status` (queued/rendering/succeeded/failed/canceled)
   - `progress_pct`, `created_at`, `started_at`, `finished_at`
   - `user_id` (FK), `user_email`, `user_name`
   - `source_type` (upload/url/api), `source_ref`
   - `input_assets` (JSON), `prompt_text`, `brand_guide`, `config_json` (JSON)
   - `output_url`, `thumbnail_url`
   - `duration_seconds`, `file_size_mb`
   - `pipeline_version`, `model`
   - `tokens_estimated`, `tokens_used`
   - `error_code`, `error_message`, `logs_url`, `webhook_failures_count`

4. **`processed_stripe_events`**
   - `stripe_event_id` (PK), `stripe_session_id`, `processed_at`
   - Used for idempotent webhook processing

### Authentication
**File:** `auth.py` (~300 lines)

**Method:** Google OAuth 2.0 SSO with JWT session cookies

**Flow:**
1. `GET /auth/login` → Redirect to Google OAuth consent screen
2. `GET /auth/callback` → Exchange code for tokens, validate ID token, upsert user
3. JWT session cookie (`session_token`) set with 24-hour TTL
4. `get_current_user` FastAPI dependency extracts and validates session from cookie

**Access Control:**
- Consumer Gmail accounts (`@gmail.com`) are blocked
- Only Google Workspace accounts allowed
- New users receive 1,000 signup credits
- Stripe customer created on first login (best-effort)

**Endpoints:**
- `GET /auth/login` — Redirect to Google
- `GET /auth/callback` — Handle OAuth callback
- `POST /auth/logout` — Clear session cookie
- `GET /auth/me` — Return current user data + token model info
- `GET /auth/transactions` — Paginated credit transaction history

### Credit / Token System
**File:** `credits.py` (~169 lines)

**Pricing Model:**
- **10 tokens per second** of video
- **Max 60 seconds** per video (600 tokens max)
- **Max 50 MB** file size

**Token Packs (Stripe):**
- TOKENS_1000: $10 for 1,000 tokens
- TOKENS_3000: $25 for 3,000 tokens

**Credit Management:**
- `validate_upload()` — Pre-flight checks: file size, duration, credit balance
- `deduct_credits()` — Deduct and log transaction
- `required_tokens()` — Calculate tokens for duration
- `get_video_duration()` — FFprobe duration extraction

**Concurrency Control:**
- 1 concurrent job per user (in-memory `_active_jobs` dict)
- `acquire_job_slot()` / `release_job_slot()`

### Stripe Billing
**File:** `billing.py` (~196 lines)

**Integration:** Stripe Checkout Sessions + Webhooks

**Endpoints:**
- `GET /billing/packs` — List available token packs + current balance
- `POST /billing/checkout-session` — Create Stripe Checkout Session for purchase
- `POST /webhooks/stripe` — Handle `checkout.session.completed` event

**Webhook Processing:**
- Signature verification with `STRIPE_WEBHOOK_SECRET`
- Idempotent processing via `ProcessedStripeEvent` table
- Credits user account on successful payment
- Logs `CreditTransaction` with type "grant"

### Admin Dashboard
**File:** `admin.py` (~495 lines)

**Access:** Restricted to `ADMIN_EMAILS` set (currently `kevin@kwangel.fund`)

**Frontend:** `static/admin.html` — Full admin dashboard UI

**API Endpoints (all under `/admin/api/`):**

- `GET /renders` — Paginated, filtered render list with sorting
- `GET /renders/{id}` — Single render detail
- `POST /renders/{id}/rerun` — Re-queue a render with same inputs
- `POST /renders/{id}/cancel` — Cancel in-progress render
- `POST /renders/{id}/refund` — Refund credits for a render
- `DELETE /renders/{id}/output` — Delete output artifacts
- `GET /renders/export` — CSV export of filtered renders
- `POST /renders/bulk` — Bulk actions (rerun, refund, delete_output)

**Filter Parameters:**
- `q` — Full-text search across render_id, email, name, prompt, source
- `status` — Comma-separated status filter
- `source` — Source type filter
- `user` — User email/name filter
- `time_range` — 1h, 24h, 7d, 30d
- `min_duration` / `max_duration`, `min_size` / `max_size`, `min_credits` / `max_credits`
- `errors_only`, `webhook_failures`
- `sort_by` / `sort_dir`

---

## Phase 4: Scene Detection & Video Intelligence

### Scene Detection
**File:** `scene_detector.py` (~530 lines)

**Combined Metadata + Scene Detection (Single LLM Call):**
- `extract_metadata_and_scenes()` — Single Gemini Flash call extracts both brand metadata AND scene breakdown
- Previously two separate calls; combined for latency reduction
- Returns: (metadata_dict, scenes_list)

**Scene Data Per Scene:**
- `scene_number` (sequential integer)
- `start_time` / `end_time` (M:SS format)
- `description` (1-2 sentences: subjects, actions, text overlays, mood)
- `transcript` (exact spoken words, or "[No speech]")

### Keyframe Extraction
- `extract_keyframes()` — FFmpeg extracts one JPEG frame per scene at scene start_time
- Output: 640x360 base64-encoded JPEG images
- Supports both GCS and YouTube videos

### YouTube Video Support
- `download_video_locally()` — Downloads via `yt-dlp` for YouTube URLs, GCS API for gs:// URIs
- Auto-detects yt-dlp binary
- Temporary directory with cleanup

### Volume Analysis
- `analyze_volume_levels()` — FFmpeg `volumedetect` per scene
- Outputs: `volume_db`, `volume_pct` (0-100 scale), `volume_change_pct`, `volume_flag`
- Flags scenes with >10% volume jump between consecutive scenes

### Video Metadata Extraction
- `extract_video_metadata()` — FFprobe extracts duration, resolution, aspect ratio, frame rate, file size, codec

### Brand Intelligence
- `generate_brand_intelligence()` — Gemini Flash researches the brand and returns comprehensive brand brief
- 24 fields: company name, website, founders, product, positioning, value prop, mission, taglines, social proof, target audiences, insights, pricing, tone, voice, credibility signals, paid media channels, creative formats, messaging themes, offers/CTAs

### Cross-Platform FFmpeg Detection
- `_find_ffmpeg()` — Checks PATH, then falls back to:
  - `/opt/homebrew/bin/ffmpeg` (macOS Apple Silicon)
  - `/usr/local/bin/ffmpeg` (macOS Intel / Linux)
  - `/usr/bin/ffmpeg` (Linux system)

### Video Transcoding
- `transcode_to_720p()` — Downscales large videos to 720p before processing (libx264, CRF 23)

---

## Phase 5: Report Generation & Notifications

### HTML Report
**File:** `report_service.py` (~1306 lines)

**Function:** `generate_report_html()` — Self-contained, shareable HTML page

**Report Sections:**
1. **Header** — "Creative Reviewer" branding, timestamp, print button
2. **Video Embed** — YouTube iframe or GCS video player with download link
3. **Score Cards** — Performance Score, ABCD Score, Persuasion Density, Brand name
4. **Executive Summary** — Bullet points: ABCD score, persuasion density, structure archetype, scene count, volume warnings
5. **Video Filename Tags** — Parsed from underscore-separated filename
6. **Creative Concept** — Synthesized concept name + description from scenes and structure
7. **Creative Metadata** — Duration, resolution, aspect ratio, frame rate, file size, codec
8. **Scene Timeline** — Grid of scene cards with keyframe thumbnails, timestamps, descriptions, transcripts
9. **Voiceover Volume Levels** — Inline SVG bar chart with per-scene volume, average line, jump flags
10. **Performance Score** — CPA Risk, ROAS Potential, Fatigue Risk, Funnel Strength cards + section score bars + driver analysis
11. **ABCD Feature Results** — Pass/fail table with rationale, evidence, strengths, weaknesses per feature
12. **Persuasion Tactics** — Same format as ABCD
13. **Creative Structure** — Archetype tags + rationale + strengths/weaknesses
14. **Brand Intelligence Brief** — Company overview, target audience, products/pricing, brand tone/voice, credibility signals, paid media channels, creative formats, messaging themes, offers/CTAs

**Design:** Light theme, Inter font, Upscale TV brand colors (#0A6D86 primary, #831F80 accent), responsive layout

### PDF Report
**Function:** `generate_report_pdf()` — fpdf2-based PDF generation

Mirrors all HTML report sections in print-friendly format:
- Score summary boxes
- Executive summary
- Creative concept
- Scene timeline with timestamps and transcripts
- Volume level bar chart (drawn with PDF rectangles)
- Video metadata
- ABCD + Persuasion feature tables with full details
- Creative structure
- Brand intelligence brief (multi-page)

### Slack Notifications
**Function:** `send_slack_notification()` — Posts rich Block Kit message to Slack webhook

**Slack Message Sections:**
- Header + video/brand info
- Score cards (ABCD, Persuasion, Performance)
- Creative structure + concept
- Scene timeline with volume levels
- Performance breakdown with drivers
- ABCD feature results (passed/failed lists)
- Persuasion tactics (detected/not detected)
- Brand intelligence summary
- Video metadata
- Link to full HTML report

**Implementation:** Uses `urllib.request` (no extra dependency), fire-and-forget via daemon thread

---

## Complete File Inventory

### Core Application
- `web_app.py` — FastAPI application (993 lines)
- `main.py` — CLI entrypoint
- `configuration.py` — Configuration class
- `models.py` — Data models + JSON schemas (340 lines)
- `utils.py` — CLI argument parsing (257 lines)

### Database & Auth
- `db.py` — SQLAlchemy models + session management (157 lines)
- `auth.py` — Google SSO + JWT sessions (300 lines)
- `billing.py` — Stripe integration (196 lines)
- `credits.py` — Token system + credit management (169 lines)
- `admin.py` — Admin dashboard API (495 lines)

### AI / Evaluation
- `evaluation_services/video_evaluation_service.py` — Feature evaluation orchestrator
- `evaluation_services/confidence_calibration_service.py` — Confidence logging
- `llms_evaluation/llms_detector.py` — Gemini LLM evaluation logic
- `annotations_evaluation/` — Video Intelligence API evaluation modules
- `custom_evaluation/custom_detector.py` — Custom evaluation support
- `prompts/prompt_generator.py` — Prompt construction

### Feature Definitions
- `features_repository/long_form_abcd_features.py` — 23 ABCD features
- `features_repository/shorts_features.py` — Shorts features
- `features_repository/creative_intelligence_features.py` — 8 CI features (278 lines)
- `features_repository/feature_configs_handler.py` — Feature loading

### Intelligence & Prediction
- `performance_predictor.py` — Deterministic performance engine (371 lines)
- `scene_detector.py` — Scene detection, keyframes, volume, metadata (~530 lines)
- `report_service.py` — HTML, PDF, Slack reports (1306 lines)

### Frontend
- `static/index.html` — Main application UI
- `static/admin.html` — Admin dashboard UI

### Infrastructure
- `Dockerfile` — Python 3.11 + ffmpeg, Cloud Run ready
- `requirements.txt` — 18 dependencies
- `.env` / `.env.example` — Environment variables
- `.github/workflows/ci.yml` — CI pipeline
- `pyproject.toml` — Project metadata
- `seed_renders.py` — Demo data seeder (144 lines)
- `data/app.db` — SQLite database

### Documentation
- `README.md` — Project README
- `PROJECT_OVERVIEW.md` — Comprehensive project overview
- `API_DOCUMENTATION.md` — Full API reference
- `API_QUICKSTART.md` — Quick start guide
- `LAUNCH_POST.md` — Launch overview
- `KEYFRAME_FIX.md` — YouTube keyframe fix details
- `SESSION_SUMMARY.md` — Development session log
- `CHANGELOG_v2.1.md` — Version 2.1 changelog
- `CONTRIBUTING.md` — Contribution guidelines

### Tests & Examples
- `test_keyframe_extraction.py` — YouTube keyframe test
- `test_api_endpoint.sh` — API integration test
- `examples/api_client_example.py` — Python usage examples (270 lines)
- `tests/test_abcd_parameters.py` — Parameter tests

---

## Environment & Deployment

### GCP Project
- **Project:** `abcds-detector-488021`
- **Auth:** `kevin@kwangel.fund`
- **APIs:** Video Intelligence, Vertex AI, Knowledge Graph, Cloud Storage, BigQuery
- **Service Account:** `abcds-detector-sa`
- **GCS Bucket:** `gs://abcds-detector-488021-videos/` (us-central1)
- **BigQuery:** `abcd_detector_ds.abcd_assessments`

### Runtime
- **Python:** 3.11 with venv at `~/abcds-detector/.venv/`
- **LLM Models:** Gemini 2.5 Pro (evaluation), Gemini 2.5 Flash (metadata/scenes/brand intel)
- **FFmpeg:** Auto-detected (`/opt/homebrew/bin/ffmpeg` on macOS)
- **Database:** SQLite with WAL mode (`data/app.db`)

### Environment Variables
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google OAuth
- `SESSION_SECRET` — JWT signing key
- `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` — Stripe billing
- `STRIPE_PRICE_1000` / `STRIPE_PRICE_3000` — Stripe Price IDs
- `SLACK_WEBHOOK_URL` — Slack notifications
- `PUBLIC_BASE_URL` — Public URL for report links
- `ABCD_KG_API_KEY` — Knowledge Graph API key
- `DATABASE_URL` — Database connection string (default: SQLite)

### Running Locally
```bash
source ~/.zshrc && source ~/abcds-detector/.venv/bin/activate
export IMAGEIO_FFMPEG_EXE=/opt/homebrew/bin/ffmpeg
python ~/abcds-detector/web_app.py
# → http://localhost:8080
```

### Cost Per Video
- Video Intelligence API: ~$0.10–$0.30/min/feature
- Gemini (Vertex AI): ~$0.05–$0.15 per video
- BigQuery: Negligible
- **Total with both pipelines:** ~$0.15–$0.45/video
- **Total LLM-only:** ~$0.05–$0.15/video

---

## Version History

### v2.0 — SaaS Platform
- FastAPI web application
- Google SSO authentication (Workspace only)
- SQLAlchemy database (users, renders, transactions)
- Credit/token system (10 tokens/sec, 60s max)
- Stripe billing (checkout sessions + webhooks)
- Admin dashboard with full render management
- SSE progress streaming
- Creative Intelligence features (7 persuasion + 1 structure)
- Performance prediction engine (CRI, REI, RFI, Funnel Strength)
- Scene detection with keyframe extraction
- Volume analysis with jump detection
- Brand intelligence brief (24 fields)
- HTML report (shareable, printable)
- PDF report (fpdf2)
- Slack notifications (Block Kit)
- Video metadata extraction
- Evaluation caching
- Docker deployment (Cloud Run ready)

### v2.1 — API & YouTube Enhancements
- `POST /api/evaluate_file` — Direct upload + evaluate endpoint
- YouTube keyframe extraction via yt-dlp
- Cross-platform FFmpeg auto-detection
- Enhanced scene detection with volume analysis
- API documentation (full reference + quickstart)
- Python client examples
- Test scripts for keyframes and API
- 30% faster processing via feature batching
