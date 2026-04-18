# API Documentation
# AI Creative Review — ABCDs Detector

**Base URL:** `https://your-domain.com` (or `http://localhost:8080` for local dev)
**Version:** 2.1
**Authentication:** Session cookie (`session_token`) — obtained via Google SSO or email/password login.

---

## Table of Contents

1. [Health & System](#1-health--system)
2. [Authentication](#2-authentication)
3. [Video Upload & Evaluation](#3-video-upload--evaluation)
4. [Reports & Results](#4-reports--results)
5. [Comparison (A/B Testing)](#5-comparison-ab-testing)
6. [Billing & Credits](#6-billing--credits)
7. [Feedback & Calibration](#7-feedback--calibration)
8. [Admin API](#8-admin-api)
9. [Data Models](#9-data-models)
10. [Error Codes](#10-error-codes)

---

## 1. Health & System

### `GET /health`

Health check for uptime monitoring and load balancer probes. No authentication required.

**Response `200`:**
```json
{
  "status": "healthy",
  "version": "2.1",
  "database": "ok"
}
```

**Response `503` (degraded):**
```json
{
  "status": "degraded",
  "version": "2.1",
  "database": "unreachable"
}
```

---

## 2. Authentication

All auth endpoints are prefixed with `/auth`.

### `GET /auth/config`

Returns auth configuration for frontend feature detection.

**Response:**
```json
{
  "google_enabled": true
}
```

---

### `GET /auth/login`

Redirects the user to Google's OAuth consent screen. On successful authentication, redirects back to `/auth/callback`, which sets a session cookie and redirects to `/`.

**Requires:** `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` env vars.

---

### `GET /auth/callback`

OAuth callback handler. Exchanges the authorization code for an ID token, validates it, upserts the user, and sets a session cookie.

**Query Parameters:**
- `code` — Authorization code from Google.
- `error` — Error string if auth failed.

**Side Effects:**
- New users receive 1,000 signup credits.
- Stripe customer is created (best-effort).
- Sets `session_token` cookie (httponly, secure, samesite=lax, 24h TTL).

---

### `POST /auth/register`

Register a new user with email and password.

**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePass1"
}
```

**Response `201`:**
```json
{
  "status": "registered",
  "email": "user@example.com"
}
```

Sets session cookie. Sends verification email.

**Errors:**
- `400` — Invalid email or weak password.
- `409` — Email already registered.
- `415` — Content-Type must be application/json.
- `429` — Rate limited.

**Password Requirements:**
- Minimum 8 characters
- At least one letter and one number
- Not in the common passwords blocklist

---

### `POST /auth/login/email`

Authenticate with email and password.

**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePass1"
}
```

**Response `200`:**
```json
{
  "status": "ok"
}
```

Sets session cookie.

**Errors:**
- `401` — Invalid email or password.
- `429` — Account locked (5 failed attempts → 15-min lockout).

---

### `POST /auth/logout`

Clears the session cookie.

**Response:**
```json
{
  "status": "logged_out"
}
```

---

### `GET /auth/me`

Returns the current authenticated user's profile and credit balance.

**Requires:** Valid session cookie.

**Response:**
```json
{
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "email_verified": true,
    "has_google": true,
    "credits_balance": 850,
    "created_at": "2026-01-15T10:30:00",
    "token_model": {
      "tokens_per_second": 10,
      "max_video_seconds": 60,
      "max_tokens_per_video": 600
    }
  }
}
```

---

### `GET /auth/verify-email?token={token}`

Verifies a user's email via the link sent during registration.

**Redirects to:** `/?email_verified=true` on success, or `/?auth_error=...` on failure.

---

### `POST /auth/forgot-password`

Request a password reset email. Always returns 200 to prevent email enumeration.

**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "If that email exists, a reset link has been sent."
}
```

---

### `POST /auth/reset-password`

Reset password using a valid reset token.

**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "token": "reset-token-string",
  "password": "newSecurePass1"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Password has been reset. You can now sign in."
}
```

---

### `GET /auth/transactions`

Returns paginated credit transaction history for the current user.

**Query Parameters:**
- `limit` (int, default: 50, max: 100) — Page size.
- `offset` (int, default: 0) — Pagination offset.

**Response:**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "type": "debit",
      "amount": 300,
      "reason": "video_evaluation",
      "job_id": "abc123",
      "created_at": "2026-02-20T14:00:00"
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

---

## 3. Video Upload & Evaluation

### `POST /api/upload`

Upload a video file to GCS. Rate limited to 10/minute.

**Requires:** Valid session cookie.

**Request:** `multipart/form-data`
- `file` — Video file (MP4, max 50 MB).

**Response `200`:**
```json
{
  "status": "uploaded",
  "filename": "my_ad.mp4",
  "gcs_uri": "gs://abcds-detector-488021-videos/my_ad.mp4",
  "size_mb": 12.4
}
```

**Errors:**
- `402` — Insufficient credits (includes purchase offers).
- `413` — File exceeds 50 MB limit.

---

### `POST /api/evaluate`

Run a full ABCD evaluation with real-time SSE progress streaming. Rate limited to 5/minute.

**Requires:** Valid session cookie.

**Request:** `application/x-www-form-urlencoded`
- `gcs_uri` (string, required) — GCS URI (`gs://...`) or YouTube URL.
- `use_abcd` (bool, default: true) — Run ABCD evaluation.
- `use_shorts` (bool, default: false) — Run Shorts evaluation.
- `use_ci` (bool, default: true) — Run Creative Intelligence evaluation.

**Response:** `text/event-stream` (Server-Sent Events)

Each SSE message is a JSON object with `step`, `message`, `pct` (0-100), and optional `partial` data:

```
data: {"step": "trim", "message": "Preparing video...", "pct": 5}
data: {"step": "metadata", "message": "Extracting brand metadata & detecting scenes...", "pct": 8}
data: {"step": "metadata_done", "message": "Brand: Nike | 12 scenes", "pct": 18, "partial": {"brand_name": "Nike", "scene_count": 12}}
data: {"step": "evaluating", "message": "Evaluating creative features...", "pct": 20}
data: {"step": "abcd_done", "message": "ABCD features complete", "pct": 50, "partial": {"abcd": {"score": 78, "passed": 18, "total": 23}}}
data: {"step": "ci_done", "message": "Creative intelligence complete", "pct": 60, "partial": {"persuasion": {"density": 65, "detected": 8, "total": 12}}}
data: {"step": "keyframes_done", "message": "Keyframes extracted", "pct": 75}
data: {"step": "volume_done", "message": "Volume analysis complete", "pct": 82}
data: {"step": "brand_done", "message": "Brand intelligence complete", "pct": 90}
data: {"step": "brief_done", "message": "Creative brief generated", "pct": 92}
data: {"step": "audio_done", "message": "Audio richness analysis complete", "pct": 93}
data: {"step": "formatting", "message": "Generating report...", "pct": 95}
data: {"step": "complete", "pct": 100, "data": { /* full EvaluationReport */ }}
data: {"step": "error", "message": "Pipeline error description"}
```

**Pipeline Steps:**

| Step | Phase | Description |
|---|---|---|
| `trim` | Pre-processing | Video trimming for first-5-second features (GCS only) |
| `metadata` | Extraction | Combined brand metadata + scene detection (single Flash LLM call) |
| `metadata_done` | Extraction | Metadata complete; includes `partial` with `brand_name` and `scene_count` |
| `evaluating` | Evaluation | ABCD + CI + Shorts evaluated in parallel (Pro model) |
| `abcd_done` | Evaluation | ABCD features complete; includes `partial` with score summary |
| `ci_done` | Evaluation | Creative Intelligence features complete; includes `partial` with persuasion density |
| `keyframes_done` | Post-processing | Scene keyframe extraction |
| `volume_done` | Post-processing | Audio volume level analysis per scene |
| `brand_done` | Post-processing | Brand intelligence profile generation |
| `brief_done` | Post-processing | Creative brief (concept) generation |
| `audio_done` | Post-processing | Audio richness analysis |
| `formatting` | Finalization | Report assembly and formatting |
| `complete` | Done | Full results in `data` field |
| `error` | Failure | Error message in `message` field |

The final `complete` event contains the full evaluation results (see [Data Models > EvaluationReport](#evaluationreport)).

**Errors:**
- `402` — Insufficient credits.
- `429` — Concurrent job limit (1 per user) or rate limited.

---

### `POST /api/evaluate_file`

Upload a video file and return the complete evaluation report as JSON (no SSE). Rate limited to 5/minute.

**Requires:** Valid session cookie.

**Request:** `multipart/form-data`
- `file` — Video file (MP4, max 50 MB, max 60s).
- `use_abcd` (bool, default: true)
- `use_shorts` (bool, default: false)
- `use_ci` (bool, default: true)

**Response `200`:** Full [EvaluationReport](#evaluationreport) JSON.

**Errors:**
- `400` — Invalid video or duration exceeds 60s.
- `402` — Insufficient credits.
- `429` — Concurrent job limit.
- `500` — Evaluation pipeline failure.

---

## 4. Reports & Results

### `GET /api/results/{report_id}`

Retrieve cached evaluation results by report ID.

**Response `200`:** Full [EvaluationReport](#evaluationreport) JSON.

**Response `404`:**
```json
{
  "error": "No results found"
}
```

---

### `GET /report/{report_id}`

Serve a standalone, shareable HTML report page.

**Response:** `text/html` — Fully rendered evaluation report.

---

### `GET /api/report/{report_id}/pdf`

Generate and download a PDF of the evaluation report.

**Response:** `application/pdf`
- Header: `Content-Disposition: attachment; filename="abcd_report_{video_name}_{report_id}.pdf"`

---

### `GET /api/keyframe/{report_id}/{scene_idx}`

Serve a keyframe image for a specific scene within a report.

**Path Parameters:**
- `report_id` — Report identifier.
- `scene_idx` — Zero-based scene index.

**Response:** `image/jpeg`

---

### `GET /api/video/{report_id}`

Stream the original video file from GCS for embedding or download.

**Response:** `video/mp4`
- Header: `Content-Disposition: inline; filename="{video_name}"`
- Header: `Cache-Control: public, max-age=86400`

Only available for GCS-hosted videos.

---

## 5. Comparison (A/B Testing)

### `POST /api/evaluate_compare`

Evaluate 2-5 videos in parallel and return a comparison report with deltas, feature diffs, and a recommended winner.

**Requires:** Valid session cookie.

**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "video_uris": [
    "gs://bucket/variant_a.mp4",
    "gs://bucket/variant_b.mp4"
  ],
  "use_abcd": true,
  "use_shorts": false,
  "use_ci": true
}
```

**Response `200`:**
```json
{
  "comparison_id": "abc123",
  "timestamp": "2026-02-23T10:30:00",
  "comparison": {
    "variant_count": 2,
    "variants": [
      {
        "index": 0,
        "video_name": "variant_a.mp4",
        "abcd_score": 78.3,
        "persuasion_density": 65.0,
        "performance_score": 72,
        "accessibility_score": 75.0,
        "emotional_coherence": 88.5,
        "report_id": "rpt123"
      }
    ],
    "deltas": [
      {
        "vs": "variant_b.mp4 vs variant_a.mp4",
        "abcd_delta": 4.3,
        "persuasion_delta": -2.0,
        "performance_delta": 6.0
      }
    ],
    "feature_diffs": [
      {
        "feature_id": "dynamic_start",
        "feature_name": "Dynamic Start",
        "results": [true, false]
      }
    ],
    "recommended_winner": {
      "index": 1,
      "video_name": "variant_b.mp4",
      "justification": "variant_b.mp4 leads with a performance score of 78..."
    }
  },
  "variants": [ /* full EvaluationReport for each variant */ ],
  "errors": []
}
```

**Errors:**
- `400` — Fewer than 2 or more than 5 URIs.
- `402` — Insufficient credits for all variants.
- `500` — Comparison failed (fewer than 2 variants evaluated successfully).

---

### `GET /report/compare/{comparison_id}`

Serve a standalone HTML comparison report.

**Response:** `text/html`

---

## 6. Billing & Credits

### `GET /billing/packs`

List available token packs and current balance.

**Requires:** Valid session cookie.

**Response:**
```json
{
  "credits_balance": 850,
  "packs": [
    {
      "key": "TOKENS_1000",
      "usd": 10,
      "tokens": 1000,
      "available": true
    },
    {
      "key": "TOKENS_3000",
      "usd": 25,
      "tokens": 3000,
      "available": true
    }
  ]
}
```

---

### `POST /billing/checkout-session`

Create a Stripe Checkout Session to purchase a token pack.

**Requires:** Valid session cookie.

**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "pack": "TOKENS_1000"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/..."
}
```

Redirect the user to `checkout_url` to complete payment. On success, Stripe fires a webhook that credits the user's account.

---

### `POST /webhooks/stripe`

Stripe webhook endpoint. No authentication — verified via Stripe signature.

Handles `checkout.session.completed` events:
- Credits the user account with the purchased token amount.
- Logs a `CreditTransaction` with type `grant`.
- Idempotent — duplicate events are safely ignored.

---

## 7. Feedback & Calibration

### `POST /api/report/{report_id}/feedback`

Submit human feedback on a feature detection result.

**Request Body:**
```json
{
  "feature_id": "dynamic_start",
  "verdict": "correct"
}
```

`verdict` must be `"correct"` or `"incorrect"`.

**Response:**
```json
{
  "status": "ok"
}
```

---

### `GET /admin/api/calibration`

Returns per-feature accuracy/reliability statistics computed from feedback data.

**Response:** Feature-level accuracy metrics.

---

## 8. Admin API

All admin endpoints require an authenticated user whose email is in the admin allowlist. Endpoints are prefixed with `/admin/api`.

### `GET /admin/api/renders`

Paginated, filtered list of all evaluation renders.

**Query Parameters:**
- `q` (string) — Full-text search across render_id, user_email, user_name, prompt_text, source_ref.
- `status` (string) — Comma-separated status filter: `queued`, `rendering`, `succeeded`, `failed`, `canceled`.
- `source` (string) — Comma-separated source type filter: `upload`, `url`, `api`.
- `user` (string) — Filter by user email or name.
- `time_range` (string) — `1h`, `24h`, `7d`, `30d`.
- `min_duration` / `max_duration` (float) — Duration range in seconds.
- `min_size` / `max_size` (float) — File size range in MB.
- `min_credits` / `max_credits` (int) — Token usage range.
- `errors_only` (bool) — Only renders with errors.
- `webhook_failures` (bool) — Only renders with webhook failures.
- `sort_by` (string, default: `created_at`) — `created_at`, `status`, `duration_seconds`, `file_size_mb`, `tokens_used`, `user_email`.
- `sort_dir` (string, default: `desc`) — `asc` or `desc`.
- `page` (int, default: 1) — Page number.
- `page_size` (int, default: 25, max: 100) — Items per page.

**Response:**
```json
{
  "renders": [ /* array of Render objects */ ],
  "total": 142,
  "page": 1,
  "page_size": 25
}
```

---

### `GET /admin/api/renders/{render_id}`

Full detail for a single render.

**Response:** [Render](#render) object.

---

### `POST /admin/api/renders/{render_id}/rerun`

Re-queue a render with the same inputs.

**Response:**
```json
{
  "status": "queued",
  "render_id": "new_id",
  "message": "Re-queued from original_id"
}
```

---

### `POST /admin/api/renders/{render_id}/cancel`

Cancel a render in progress (`queued` or `rendering` status only).

**Response:**
```json
{
  "status": "canceled",
  "render_id": "abc123"
}
```

---

### `POST /admin/api/renders/{render_id}/refund`

Refund credits for a render.

**Response:**
```json
{
  "status": "refunded",
  "credits_refunded": 300,
  "new_balance": 1150
}
```

---

### `DELETE /admin/api/renders/{render_id}/output`

Delete output artifacts (URLs) for a render.

**Response:**
```json
{
  "status": "deleted",
  "render_id": "abc123"
}
```

---

### `GET /admin/api/renders/export`

Export filtered renders as a CSV file.

**Query Parameters:**
- `q` (string) — Full-text search.
- `status` (string) — Comma-separated status filter.
- `source` (string) — Comma-separated source type filter.
- `user` (string) — Filter by user email or name.
- `time_range` (string) — `1h`, `24h`, `7d`, `30d`.
- `errors_only` (bool) — Only renders with errors.
- `webhook_failures` (bool) — Only renders with webhook failures.

**Response:** `text/csv` with `Content-Disposition: attachment; filename=renders_export.csv`

---

### `POST /admin/api/renders/bulk`

Perform bulk actions on multiple renders.

**Request Body:**
```json
{
  "action": "rerun",
  "render_ids": ["id1", "id2", "id3"]
}
```

`action` must be one of: `rerun`, `refund`, `delete_output`.

**Response:**
```json
{
  "action": "refund",
  "results": [
    {"render_id": "id1", "status": "refunded", "credits": 300},
    {"render_id": "id2", "status": "nothing_to_refund"}
  ]
}
```

---

### `POST /admin/api/users/grant`

Grant credits to a user by email.

**Request Body:**
```json
{
  "email": "user@example.com",
  "amount": 5000,
  "reason": "promotional_grant"
}
```

**Response:**
```json
{
  "status": "granted",
  "email": "user@example.com",
  "amount": 5000,
  "new_balance": 5850
}
```

---

## 9. Data Models

### EvaluationReport

The top-level JSON object returned by evaluation endpoints.

```json
{
  "report_id": "abc123",
  "timestamp": "2026-02-23T10:30:00",
  "brand_name": "Nike",
  "video_uri": "gs://bucket/video.mp4",
  "video_name": "video.mp4",
  "tokens_used": 300,
  "credits_remaining": 700,
  "report_url": "https://domain.com/report/abc123",

  "abcd": {
    "score": 78.3,
    "result": "Might Improve",
    "passed": 18,
    "total": 23,
    "features": [ /* FeatureEvaluation[] */ ]
  },

  "persuasion": {
    "density": 65.0,
    "detected": 8,
    "total": 12,
    "features": [ /* FeatureEvaluation[] */ ]
  },

  "structure": {
    "features": [ /* FeatureEvaluation[] */ ]
  },

  "shorts": {
    "features": [ /* FeatureEvaluation[] */ ]
  },

  "scenes": [
    {
      "scene_number": 1,
      "start_time": "0:00",
      "end_time": "0:03",
      "description": "Product close-up with brand logo",
      "transcript": "Introducing the new...",
      "keyframe": "base64-encoded-jpeg",
      "emotion": "excitement",
      "sentiment_score": 0.8,
      "music_mood": "upbeat",
      "has_music": true,
      "speech_ratio": 0.7,
      "peak_db": -6.2,
      "avg_db": -18.5,
      "silence_pct": 0.1
    }
  ],

  "concept": {
    "one_line_pitch": "...",
    "key_message": "...",
    "emotional_hook": "...",
    "narrative_technique": "...",
    "unique_selling_proposition": "...",
    "target_emotion": "...",
    "creative_territory": "...",
    "messaging_hierarchy": {
      "primary": "...",
      "secondary": "...",
      "proof_points": ["..."]
    }
  },

  "predictions": {
    "overall_score": 72,
    "section_scores": {
      "hook_attention": 12.5,
      "brand_visibility": 7.0,
      "social_proof_trust": 10.0,
      "product_clarity_benefits": 11.2,
      "funnel_alignment": 6.5,
      "cta": 8.0,
      "creative_diversity_readiness": 7.8,
      "measurement_compatibility": 6.0,
      "data_audience_leverage": 3.0
    },
    "section_maxes": {
      "hook_attention": 15,
      "brand_visibility": 10,
      "social_proof_trust": 15,
      "product_clarity_benefits": 15,
      "funnel_alignment": 10,
      "cta": 10,
      "creative_diversity_readiness": 10,
      "measurement_compatibility": 10,
      "data_audience_leverage": 5
    },
    "normalized": {
      "hook_attention": 0.8333,
      "brand_visibility": 0.7,
      "social_proof_trust": 0.6667,
      "product_clarity_benefits": 0.7467,
      "funnel_alignment": 0.65,
      "cta": 0.8,
      "creative_diversity_readiness": 0.78,
      "measurement_compatibility": 0.6,
      "data_audience_leverage": 0.6
    },
    "model_version": "deterministic-rules.v1",
    "indices": {
      "conversion_readiness_index": 0.612,
      "revenue_efficiency_index": 0.585,
      "refreshability_index": 0.650,
      "funnel_strength": {
        "tof": 0.720,
        "mof": 0.680,
        "bof": 0.710,
        "winner": "TOF",
        "hybrid": "TOF/BOF"
      }
    },
    "labels": {
      "predicted_cpa_risk": "Medium",
      "predicted_roas_tier": "Moderate",
      "creative_fatigue_risk": "Medium",
      "expected_funnel_strength": "TOF/BOF"
    },
    "flags": {
      "hook_within_3s": true,
      "brand_mentions_3x": false,
      "has_trackable_anchor": true,
      "has_testimonial_or_ugc": false,
      "product_demo_present": true,
      "end_card_present": true
    },
    "drivers": {
      "top_positive": [
        {"feature": "Hook & Attention", "score": 0.83},
        {"feature": "Call to Action", "score": 0.80}
      ],
      "top_negative": [
        {"feature": "Audience Leverage", "score": 0.40}
      ],
      "applied_adjustments": [
        {"type": "boost", "key": "has_trackable_anchor", "delta": 0.05},
        {"type": "penalty", "key": "has_testimonial_or_ugc", "delta": -0.05}
      ]
    }
  },

  "brand_intelligence": {
    "company_name": "Nike",
    "website": "nike.com",
    "founders_leadership": "Phil Knight, Bill Bowerman",
    "product_service": "Athletic footwear",
    "launched": "1964",
    "description": "Global athletic footwear and apparel brand...",
    "brand_positioning": "...",
    "core_value_proposition": "...",
    "mission": "Bring inspiration and innovation to every athlete",
    "taglines": "Just Do It",
    "social_proof_overview": "World's largest athletic brand...",
    "target_audience_primary": "Athletes and fitness enthusiasts 18-34",
    "target_audience_secondary": "Casual lifestyle consumers",
    "key_insight": "...",
    "secondary_insight": "...",
    "products_pricing": ["Air Max $150", "Dunk Low $110"],
    "tone": "Empowering, bold",
    "voice": "Motivational, direct",
    "what_it_is_not": "Discount athletic brand",
    "credibility_signals": ["Olympic sponsor", "#1 market share"],
    "paid_media_channels": ["YouTube", "Instagram", "TV"],
    "creative_formats": ["Hero video", "Athlete stories"],
    "messaging_themes": ["Personal achievement", "Innovation"],
    "offers_and_ctas": ["Shop now", "Find your nearest store"]
  },

  "video_metadata": {
    "duration": 30.0,
    "resolution": "1920x1080",
    "codec": "h264"
  },

  "emotional_coherence": {
    "score": 88.5,
    "flagged_shifts": [
      {
        "from_scene": 3,
        "to_scene": 4,
        "delta": 0.6,
        "from_emotion": "calm",
        "to_emotion": "urgency"
      }
    ]
  },

  "audio_analysis": {},

  "action_plan": [
    {
      "feature_name": "Dynamic Start",
      "detected": false,
      "recommendation": "Add a shot change within the first 3 seconds",
      "priority": "high"
    }
  ],

  "feature_timeline": {
    "video_duration_s": 30.0,
    "scene_boundaries": [
      {"start_s": 0, "end_s": 3, "scene_number": 1}
    ],
    "features": [
      {
        "id": "dynamic_start",
        "name": "Dynamic Start",
        "sub_category": "ATTRACT",
        "detected": true,
        "timestamps": [
          {"start_s": 0, "end_s": 2.5, "label": "First shot change"}
        ]
      }
    ]
  },

  "accessibility": {
    "score": 75.0,
    "passed": 3,
    "total": 4,
    "features": [],
    "speech_rate_wpm": 145.0,
    "speech_rate_flag": "ok"
  },

  "platform_fit": {
    "youtube": {
      "score": 85,
      "tips": ["Include a clear CTA (end card, overlay, or verbal) to drive action."]
    },
    "meta_feed": {
      "score": 60,
      "tips": [
        "Use square (1:1) or 4:5 vertical for Feed. Landscape loses real estate.",
        "Add captions — Feed autoplay is muted. Captions increase watch time by 12%."
      ]
    },
    "meta_reels": {
      "score": 55,
      "tips": ["Reels are 9:16 vertical. Crop to vertical for maximum screen coverage."]
    },
    "tiktok": {
      "score": 50,
      "tips": ["Re-crop to 9:16 vertical. TikTok is a vertical-first platform."]
    },
    "ctv": {
      "score": 90,
      "tips": []
    }
  },

  "benchmarks": {
    "abcd_percentile": 72.0,
    "persuasion_percentile": 65.0,
    "performance_percentile": 58.0,
    "sample_size": 150,
    "vertical": "Athletic footwear",
    "distribution": {
      "abcd": {"p10": 35.0, "p25": 50.0, "p50": 65.0, "p75": 78.0, "p90": 88.0, "mean": 63.5},
      "persuasion": {"p10": 20.0, "p25": 40.0, "p50": 55.0, "p75": 70.0, "p90": 82.0, "mean": 54.0},
      "performance": {"p10": 30.0, "p25": 45.0, "p50": 60.0, "p75": 72.0, "p90": 85.0, "mean": 58.0}
    }
  },

  "reference_ads": [
    {
      "title": "Nike — You Can't Stop Us",
      "vertical": "Athletic footwear",
      "overall_score": 88,
      "similarity": 0.945,
      "feature_vector": [0.9, 0.85, 0.7, 0.8, 0.75, 0.9, 0.6, 0.7, 0.5]
    }
  ]
}
```

### FeatureEvaluation

```json
{
  "id": "dynamic_start",
  "name": "Dynamic Start",
  "category": "LONG_FORM_ABCD",
  "sub_category": "ATTRACT",
  "detected": true,
  "confidence": 0.92,
  "rationale": "The video opens with a rapid cut within 2.1 seconds...",
  "evidence": "Shot change detected at 2.1s from close-up to wide angle",
  "strengths": "Strong visual hook that grabs attention immediately",
  "weaknesses": "",
  "timestamps": [
    {"start": "0:00", "end": "0:02", "label": "Opening shot change"}
  ],
  "recommendation": "Maintain this pattern — consider adding a secondary hook at the 5-second mark.",
  "recommendation_priority": "low"
}
```

Accessibility features include an additional `remediation` field with specific guidance:

```json
{
  "id": "acc_captions_present",
  "name": "Captions Present",
  "category": "CREATIVE_INTELLIGENCE",
  "sub_category": "ACCESSIBILITY",
  "detected": false,
  "confidence": 0.85,
  "remediation": "Add burned-in captions/subtitles to all spoken segments. Use a legible font (≥24px) with a semi-transparent background."
}
```

### Feature Categories

| Category | Description |
|---|---|
| `LONG_FORM_ABCD` | Core YouTube ABCD creative best practices (Attract, Brand, Connect, Direct) |
| `SHORTS` | YouTube Shorts-specific creative features |
| `CREATIVE_INTELLIGENCE` | Extended analysis: persuasion techniques, structural patterns, and accessibility |

### Feature Sub-Categories

| Sub-Category | Parent Categories | Description |
|---|---|---|
| `ATTRACT` | LONG_FORM_ABCD | Hook and attention-grabbing elements in the first seconds |
| `BRAND` | LONG_FORM_ABCD | Brand visibility, logo placement, and brand recall signals |
| `CONNECT` | LONG_FORM_ABCD | Emotional connection — people, product visuals, storytelling |
| `DIRECT` | LONG_FORM_ABCD | Call-to-action, offers, and conversion drivers |
| `PERSUASION` | CREATIVE_INTELLIGENCE | Persuasion techniques (social proof, urgency, scarcity, etc.) |
| `STRUCTURE` | CREATIVE_INTELLIGENCE | Narrative structure and archetype detection |
| `ACCESSIBILITY` | CREATIVE_INTELLIGENCE | Captions, text contrast, speech rate, audio independence |

### Render

```json
{
  "render_id": "abc123",
  "status": "succeeded",
  "progress_pct": 100,
  "created_at": "2026-02-23T10:00:00",
  "started_at": "2026-02-23T10:00:01",
  "finished_at": "2026-02-23T10:03:45",
  "user_id": "uuid",
  "user_email": "user@example.com",
  "user_name": null,
  "source_type": "upload",
  "source_ref": "my_ad.mp4",
  "input_assets": [],
  "prompt_text": "gs://bucket/my_ad.mp4",
  "brand_guide": null,
  "config": {"use_abcd": true, "use_shorts": false, "use_ci": true},
  "output_url": null,
  "thumbnail_url": null,
  "duration_seconds": 30.0,
  "file_size_mb": 12.4,
  "pipeline_version": "Gemini → FFmpeg → Encode v3",
  "model": "gemini-2.5-pro",
  "tokens_estimated": 600,
  "tokens_used": 300,
  "error_code": null,
  "error_message": null,
  "logs_url": null,
  "webhook_failures_count": 0
}
```

---

## 10. Error Codes

### HTTP Status Codes

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Created (registration) |
| `302` | Redirect (OAuth flow) |
| `400` | Bad request / validation error |
| `401` | Not authenticated |
| `402` | Insufficient credits |
| `403` | Forbidden (admin-only) |
| `404` | Resource not found |
| `413` | File too large |
| `415` | Unsupported Content-Type |
| `429` | Rate limited or concurrent job limit |
| `500` | Internal server error |
| `503` | Service degraded |

### Application Error Codes

Returned in the `error` field of JSON error responses:

| Error Code | Description |
|---|---|
| `file_too_large` | Upload exceeds 50 MB limit |
| `insufficient_credits` | Not enough credits to start evaluation |
| `concurrent_limit` | User already has an active evaluation job |
| `invalid_video` | Could not determine video duration |
| `video_too_long` | Video exceeds 60-second limit |
| `rate_limited` | Too many requests |

---

## 11. Rate Limits

| Endpoint | Limit |
|---|---|
| Global default | 200 requests/minute |
| `POST /api/upload` | 10 requests/minute |
| `POST /api/evaluate` | 5 requests/minute |
| `POST /api/evaluate_file` | 5 requests/minute |
| Auth endpoints (login, register, forgot/reset password) | 10 attempts / 5-minute window per IP |

---

## 12. CLI Interface

The tool can also be run from the command line via `main.py`:

```bash
python main.py \
  -pi PROJECT_ID \
  -bn BUCKET_NAME \
  -vu "gs://bucket/video.mp4" \
  -extvn -ull -rfa -rci -v \
  -kgak "$ABCD_KG_API_KEY" \
  -bd DATASET -bt TABLE
```

### CLI Flags

| Flag | Long Form | Description |
|---|---|---|
| `-pi` | `-project_id` | GCP Project ID |
| `-pz` | `-project_zone` | GCP zone (default: us-central1) |
| `-bn` | `-bucket_name` | GCS bucket name (not URI) |
| `-vu` | `-video_uris` | Comma-separated video URIs or folders |
| `-brn` | `-brand_name` | Brand name |
| `-brv` | `-brand_variations` | Comma-separated brand name variations |
| `-brprs` | `-branded_products` | Comma-separated product names |
| `-brprscts` | `-branded_products_categories` | Comma-separated product categories |
| `-brcallacts` | `-branded_call_to_actions` | Comma-separated CTAs |
| `-kgak` | `-knowledge_graph_api_key` | Knowledge Graph API key |
| `-bd` | `-bigquery_dataset` | BigQuery dataset name |
| `-bt` | `-bigquery_table` | BigQuery table name |
| `-af` | `-assessment_file` | Local file path for results output |
| `-extvn` | `-extract_brand_metadata` | Auto-extract brand info from video |
| `-uan` | `-use_annotations` | Enable annotation-based evaluation |
| `-ull` | `-use_llms` | Enable LLM-based evaluation |
| `-rfa` | `-run_long_form_abcd` | Run core ABCD features |
| `-rs` | `-run_shorts` | Run YouTube Shorts features |
| `-rci` | `-run_creative_intelligence` | Run Creative Intelligence features |
| `-llmn` | `-llm_name` | LLM model name (default: gemini-2.5-pro) |
| `-llml` | `-llm_location` | LLM region (default: us-central1) |
| `-mxotk` | `-max_output_tokens` | Max output tokens (default: 65535) |
| `-temp` | `-temperature` | Temperature (default: 1) |
| `-tpp` | `-top_p` | Top-P (default: 0.95) |
| `-fteval` | `-features_to_evaluate` | Comma-separated feature IDs to evaluate |
| `-crpt` | `-creative_provider_type` | Creative provider: `GCS` or `YOUTUBE` |
| `-v` | `-verbose` | Enable verbose output |
