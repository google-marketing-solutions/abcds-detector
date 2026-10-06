Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Disclaimer

ABCDs Detector is NOT an official Google product.

---

# ABCD Detector

The **ABCD Detector** solution automates the assessment of video advertising creatives against Google and YouTube's **ABCD framework** (Attract, Brand, Connect, Direct). Powered by Google's state-of-the-art **Multimodal Gemini AI**, this solution evaluates video and audio creatives with high precision, providing deep creative scoring, evidence timestamps, strengths, weaknesses, and actionable creative recommendations.

---

## What's New & Architecture Refresh

### 1. Multimodal Gemini & Custom Evaluation
* **Video Intelligence API Deprecation & Removal**: Following the deprecation of the Google Cloud Video Intelligence API, all legacy annotation pipelines (`annotations_evaluation`, `VideoIntelligenceAPIService`, etc.) have been completely retired.
* **Direct Multimodal Analysis**: Video and audio streams are now analyzed natively end-to-end by **Gemini Multimodal AI** (`google-genai` SDK) or extensible **Custom Evaluators**, eliminating multi-stage annotation latency and delivering richer contextual reasoning.
* **Unified 20-Column BigQuery Schema**: Both Universal and Shorts evaluations output to an identical, standardized BigQuery table schema.

### 2. Updated ABCD Feature Slices
* **12 Core Universal Features**: Covering fundamental ABCD storytelling, branding, pacing, and calls-to-action across all video formats.
* **18 YouTube Shorts Features**: Research-backed creative attributes specifically calibrated for short-form, mobile-first video performance.

---

## Supported ABCD Features

### 1. Universal Features (12)
Defined in [`features_repository/universal_features.py`](features_repository/universal_features.py):

| Feature ID | Name | Category | Description |
|---|---|---|---|
| `a_heartbeat_story_arc` | Heartbeat Story Arc | ATTRACT | Evaluates narrative pacing and dramatic tension curves (hook, conflict, peaks, resolution). |
| `a_tightly_framed_overall` | Tight Framing (Overall) | ATTRACT | Measures visual prominence and close framing of primary subjects. |
| `a_has_audio` | Audio Presence | ATTRACT | Evaluates intentional audio design (voiceover, dialogue, music, sound design). |
| `a_has_supers` | Supers (Text Overlays) | ATTRACT | Detects visible on-screen text overlays reinforcing the core message. |
| `a_supers_w_audio` | Supers with Audio | ATTRACT | Measures audio-visual synchronicity between on-screen text and spoken dialogue. |
| `b_brand_visualized_in_first_5_sec` | Brand Visualized (First 5s) | BRAND | Verifies clear visual brand presence (logo, product, package) in the opening 5 seconds. |
| `b_brand_mention` | Brand Mention | BRAND | Evaluates spoken or textual mentions of the brand name. |
| `b_brand_mention_speech_see_and_say_first_5s` | See & Say Brand Mention (First 5s) | BRAND | Evaluates concurrent visual and auditory brand cues within the first 5 seconds. |
| `b_brand_palette_multiple_brand_elements` | Brand Palette & Elements | BRAND | Evaluates consistent brand color palettes, visual cues, and distinctive brand assets. |
| `c_people_overall` | Presence of People | CONNECT | Quantifies human presence, face visibility, and emotional character connection. |
| `c_casual_language` | Casual Language | CONNECT | Evaluates script informality, conversational language, contractions, and natural dialogue. |
| `d_visual_cta` | Visual Call To Action | DIRECT | Detects prominent on-screen visual CTA prompts guiding the viewer to the next step. |

### 2. YouTube Shorts Features (18)
Defined in [`features_repository/shorts_features.py`](features_repository/shorts_features.py):

| Feature ID | Name | Category | Description |
|---|---|---|---|
| `a_tight_framing` | Tight Framing & Visual Dominance | ATTRACT | Subject-to-Frame Ratio ≥60%, measuring visual dominance in 9:16 framing. |
| `a_human_voice` | Human Voice Presence | ATTRACT | Measures vocal density, speech clarity, and speech starting in the first 3 seconds. |
| `a_direct_camera` | Direct to Camera | ATTRACT | Evaluates eye-contact intensity, face-to-lens address, and immediate hook connection. |
| `b_product_closeup` | Product Close-Up | BRAND | Quantifies product presence occupying 30% to 59% of the frame. |
| `b_product_extreme_closeup` | Product Extreme Close-Up | BRAND | Quantifies macro product dominance occupying ≥60% of the frame area. |
| `c_people_using_product` | Product Context & Usage Quality | CONNECT | Evaluates "Show, Don't Tell" physical engagement, utility demonstration, and realism. |
| `c_humor` | Humor & Comedic Timing | CONNECT | Detects comedic setups, timing, deadpan delivery, physical humor, and edge factor. |
| `c_character_driven` | Character-Driven | CONNECT | Evaluates relatable protagonist prominence, narrative journey, and transformation. |
| `d_audio_cta` | Call to Action (Audio) | DIRECT | Detects verbal commands, urgency level, and spoken directives to act. |
| `d_special_offer_speech` | Special Offer (Speech) | DIRECT | Evaluates spoken announcements of promotions, discounts, deals, or incentives. |
| `shorts_production_style` | Production Style (UGC) | NONE | Evaluates authentic User Generated Content (UGC) markers vs. commercial polish. |
| `shorts_sfv_adaptation_high` | SFV Native Adaptation | NONE | Quantifies how convincingly the creative mimics organic short-form social video. |
| `shorts_emoji_usage` | Emoji Usage | NONE | Detects intentional creative use of emojis, animated stickers, and native overlays. |
| `shorts_personal_character_talk` | Direct to Camera Character Talk | NONE | Measures continuous conversational delivery and breaking the fourth wall. |
| `shorts_native_brand_context` | Brand Secondary Element | NONE | Evaluates natural narrative integration of the brand to avoid ad-blindness. |
| `shorts_personal_character_type` | Everyday Persona Validation | NONE | Validates if on-screen creator feels like an authentic everyday person vs. actor. |
| `shorts_product_context` | Secondary Product Context | NONE | Evaluates product in practical utility within realistic, lived-in environments. |
| `shorts_video_format` | Vertical Format (Mobile 9:16) | NONE | Verifies native 9:16 aspect ratio, mobile UI safe zones, and absence of letterboxing. |

---

## Evaluation Methods: Gemini vs. Custom

The ABCD Detector supports two complementary evaluation mechanisms via the `EvaluationMethod` enum:

```
                      ┌──────────────────────────────────────┐
                      │            Video Creative            │
                      └──────────────────┬───────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │  EvaluationMethod.GEMINI  │                   │  EvaluationMethod.CUSTOM  │
   │  (Multimodal AI Analysis) │                   │ (Programmatic / Heuristic)│
   └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                 │                                               │
                 │ Direct multimodal reasoning                   │ Custom Python function
                 │ over video frames + audio                     │ from registry
                 ▼                                               ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                   Standardized FeatureEvaluation Object                   │
   │  (detected, confidence_score, evidence, recommendations, metrics, etc.)   │
   └───────────────────────────────────────────────────────────────────────────┘
```

### 1. Multimodal Gemini (`EvaluationMethod.GEMINI`)
* **How it works**: Sends video URIs (GCS or YouTube) directly to Gemini models (`gemini-3.8-flash`, etc.) using structured JSON schemas.
* **Capabilities**: Evaluates visual context, audio cues, speech transcription, text overlays, and narrative flow in a single multimodal pass.
* **Modes**:
  * `BULK` (default): Evaluates all requested features in a single prompt for speed and cost efficiency.
  * `INDIVIDUAL`: Sends an isolated prompt per feature for granular debugging.

### 2. Custom Evaluators (`EvaluationMethod.CUSTOM`)
* **How it works**: Executes registered Python functions for specialized business rules, deterministic heuristic scripts, external API calls, or domain-specific computer vision models.
* **Interface**: Custom functions take `(gemini_config, feature_config, video_uri, brand_context)` and return a validated `FeatureEvaluation` object.

### Implementing a Custom Evaluator

1. **Define and Register Your Function**:
   Create a detector file inside `custom_evaluation/evaluations/` (for example, `custom_evaluation/evaluations/has_audio_detector.py` or `<feature_name>_detector.py`) and decorate your function with `@register_evaluator("evaluator_name")`. 
   
   > **Note:** All `.py` files inside `custom_evaluation/evaluations/` are **automatically discovered and imported** by `CustomDetector`. If your function is defined in an external module, simply import that module in your application so the decorator executes.

   ```python
   # custom_evaluation/evaluations/has_audio_detector.py
   from configuration import BrandContext, GeminiConfig
   from custom_evaluation.custom_detector import register_evaluator
   from models import FeatureEvaluation, VideoFeature

   @register_evaluator("detect_custom_audio_cue")
   def detect_custom_audio_cue(
       gemini_config: GeminiConfig,
       feature_config: VideoFeature,
       video_uri: str,
       brand_context: BrandContext | None = None,
   ) -> FeatureEvaluation:
       # Implement your custom logic (e.g. audio processing, heuristics, or external APIs)
       is_cue_present = True
       confidence = 0.92

       return FeatureEvaluation(
           feature_id=feature_config.id,
           feature_name=feature_config.name,
           feature_category=feature_config.category.value,
           feature_sub_category=feature_config.sub_category.value,
           video_segment=feature_config.video_segment.value,
           detected=is_cue_present,
           confidence_score=confidence,
           detected_evidence="Detected target sound signature between 00:01 and 00:03.",
           rationale="Sound signature matches brand audio benchmark.",
           strengths_to_keep="Clear audio cue in the opening seconds.",
           weaknesses_to_improve="",
           recommended_actions="Great job! This feature is fully optimized.",
       )
   ```

2. **Configure the Feature**:
   In your feature repository (`universal_features.py` or `shorts_features.py`), instantiate `VideoFeature` pointing to your registered evaluator name:

   ```python
   VideoFeature(
       id="custom_audio_cue",
       name="Custom Audio Signature",
       category=VideoFeatureCategory.UNIVERSAL,
       sub_category=VideoFeatureSubCategory.ATTRACT,
       video_segment=VideoSegment.FULL_VIDEO,
       evaluation_criteria="Detects custom sonic branding cues in the opening seconds.",
       prompt_template="",
       evaluation_method=EvaluationMethod.CUSTOM,
       evaluation_function="detect_custom_audio_cue",
   )
   ```

---

## Creative Sourcing: GCS & YouTube

Videos can be sourced from Google Cloud Storage or YouTube via the **Creative Provider** architecture:

1. **Google Cloud Storage (`gcs`)**:
   * Direct video file: `gs://my-bucket/videos/ad_01.mp4`
   * Bucket directory / prefix: `gs://my-bucket/campaign_q2/` (automatically discovers all `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm` videos in the path).
2. **YouTube (`youtube`)**:
   * Public or channel-owned YouTube URLs: `https://www.youtube.com/watch?v=VIDEO_ID` or short URLs `https://youtu.be/VIDEO_ID`.

### Registering a New Creative Provider

To add support for a new video source (e.g. Amazon S3, Azure Blob Storage, or an internal DAM/MAM):

1. **Implement `CreativeProviderProto`**:
   ```python
   # creative_providers/my_custom_provider.py
   from configuration import EvaluationRequest

   class MyCustomCreativeProvider:
       def get_creative_uris(self, request: EvaluationRequest) -> list[str]:
           # Logic to resolve custom source paths into downloadable or streamable URIs
           return ["https://my-dam.internal/assets/video1.mp4"]
   ```

2. **Register in Factory**:
   Add the provider to `creative_providers/creative_provider_registry.py`:
   ```python
   from creative_providers.my_custom_provider import MyCustomCreativeProvider

   provider_factory.register_provider("my_dam", MyCustomCreativeProvider)
   ```

3. **Use in Configuration**:
   Pass `--source_type "my_dam"` via CLI or configure `CreativeProviderConfig(source_type="my_dam", creative_paths=[...])`.

---

## How to Run: CLI Script vs. API / Programmatic Call

### Option A: Standard CLI Script Execution (`main.py`)

Run `main.py` directly from your terminal or automated pipeline:

```bash
python main.py \
  --project_id "your-gcp-project-id" \
  --api_key "your-gemini-api-key" \
  --video_uris "gs://my-bucket/ads/summer_sale.mp4,https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --slices "universal,shorts" \
  --mode "BULK" \
  --brand_name "Acme" \
  --branded_products "Acme Cloud,Acme Runner" \
  --bigquery_dataset "abcd_evaluations" \
  --bigquery_table "video_results"
```

#### Key Command-Line Parameters:

| Group | Flag / Alias | Description | Default |
|---|---|---|---|
| **GCP** | `--project_id`, `-pi` | Google Cloud Project ID (or set `PROJECT_ID` env var). | *Required* |
| **GCP** | `--location` | Google Cloud region/location. | `us-central1` |
| **Gemini** | `--api_key`, `-k` | Gemini API Key (or set `GEMINI_API_KEY` env var). | *Required* |
| **Gemini** | `--model_name`, `-m` | Model identifier (e.g., `gemini-3.8-flash`, `gemini-2.5-flash`). | `gemini-3.8-flash` |
| **Execution** | `--video_uris`, `-vu` | Comma-delimited list of GCS paths or YouTube URLs. | *Required* |
| **Execution** | `--slices`, `-s` | Comma-delimited ABCD slices to evaluate (`universal,shorts`). | `universal,shorts` |
| **Execution** | `--features_to_evaluate` | JSON filter mapping slices to feature ID lists. | All in slice |
| **Execution** | `--mode` | Execution mode: `BULK` (single combined prompt) or `INDIVIDUAL`. | `BULK` |
| **Brand** | `--brand_name`, `-brn` | Brand name (required if `--no_extract_brand_metadata` is set). | None |
| **Brand** | `--branded_products` | Comma-delimited list of brand products. | None |
| **BigQuery** | `--bigquery_dataset`, `-bd` | BigQuery dataset for storing results (or `BQ_DATASET` env var). | None |
| **BigQuery** | `--bigquery_table`, `-bt` | BigQuery table name for results (or `BQ_TABLE` env var). | None |

### Option B: Programmatic API / Python Service Call

Integrate ABCD evaluation directly into your Python backend, Cloud Run service, or Celery task:

```python
from configuration import (
    EvaluationRequest,
    GCPConfig,
    GeminiConfig,
    BrandContext,
    BigQuerySettings,
    ExecutionMode,
)
from evaluation_services.video_evaluation_service import VideoEvaluationService
from gcp_api_services.gemini_api_service import GeminiAPIService

# 1. Build the validated configuration request
request = EvaluationRequest(
    gcp_config=GCPConfig(project_id="your-gcp-project-id", location="us-central1"),
    gemini_config=GeminiConfig(
        api_key="your-gemini-api-key",
        model_name="gemini-3.8-flash",
    ),
    video_uris=[
        "gs://my-ad-bucket/video_ad_01.mp4",
        "https://www.youtube.com/watch?v=EXAMPLE_ID",
    ],
    slices=["universal", "shorts"],
    execution_mode=ExecutionMode.BULK,
    brand_context=BrandContext(
        brand_name="Acme",
        branded_products=["Acme Phone", "Acme Buds"],
    ),
    # Optional BigQuery persistence:
    bigquery_settings=BigQuerySettings(
        project_id="your-gcp-project-id",
        dataset_name="abcd_evaluations",
        table_name="video_results",
    ),
)

# 2. Execute evaluation
gemini_service = GeminiAPIService(request.gcp_config, request.gemini_config)
evaluation_service = VideoEvaluationService()

for video_uri in request.video_uris:
    assessment = evaluation_service.evaluate_video(
        request=request,
        video_uri=video_uri,
        gemini_service=gemini_service,
    )
    print(f"Video: {assessment.video_name} | Brand: {assessment.brand_name}")
    for slice_name, evals in assessment.slice_evaluations.items():
        print(f"  Slice {slice_name}: {len(evals)} features evaluated.")
```

---

## BigQuery Output Schema

Results are written to BigQuery using a consolidated schema across both Universal and Shorts evaluations:

| # | Column Name | Type | Description |
|---|---|---|---|
| 1 | `execution_timestamp` | TIMESTAMP | Timestamp when the evaluation pipeline ran. |
| 2 | `brand_name` | STRING | Target brand name evaluated. |
| 3 | `video_uri` | STRING | Source URI (`gs://...` or `https://...`). |
| 4 | `feature_id` | STRING | Unique feature ID (e.g., `a_tight_framing`, `b_brand_mention`). |
| 5 | `feature_name` | STRING | Human-readable name of the evaluated feature. |
| 6 | `feature_category` | STRING | ABCD Category (`ATTRACT`, `BRAND`, `CONNECT`, `DIRECT`). |
| 7 | `feature_sub_category` | STRING | ABCD Subcategory or `NONE`. |
| 8 | `feature_evaluation_criteria` | STRING | Creative rubric definition used by the model. |
| 9 | `is_detected` | BOOLEAN | `True` if the video adheres to the rubric, `False` otherwise. |
| 10 | `confidence_score` | FLOAT | Model confidence score between `0.0` and `1.0`. |
| 11 | `rationale` | STRING | Model reasoning explaining the evaluation verdict. |
| 12 | `evidence` | STRING | Verbatim cues, actions, and exact timestamps supporting the decision. |
| 13 | `strengths` | STRING | Creative elements executed well that should be retained. |
| 14 | `weaknesses` | STRING | Creative gaps or missed opportunities detected. |
| 15 | `recommended_actions` | STRING | Actionable creative optimization recommendation. |
| 16 | `first_appearance_timestamp` | STRING | First timestamp where the feature appeared (`MM:SS` or seconds). |
| 17 | `feature_density_score` | FLOAT | Ratio of video duration where feature is active (`0.0` to `1.0`). |
| 18 | `feature_quality_score` | FLOAT | Creative quality execution score (`0.0` to `1.0`). |
| 19 | `feature_specifics` | STRING (JSON) | Detailed rubric metrics, scores, and temporal markers. |
| 20 | `brand_context` | STRING (JSON) | Full brand context (brand name, branded products, and CTAs). |

---

## Requirements & Prerequisites

Please ensure access to the following before starting:

* [Google Cloud Project](https://cloud.google.com) with enabled APIs:
  * [Vertex AI API / Gemini API](https://console.cloud.google.com/marketplace/product/google/aiplatform.googleapis.com)
  * [Cloud Storage API](https://console.cloud.google.com/marketplace/product/google/storage.googleapis.com)
  * [BigQuery API](https://console.cloud.google.com/marketplace/product/google/bigquery.googleapis.com) (Optional, for storing assessment results)
* [Gemini API Key](https://aistudio.google.com/app/apikey) from Google AI Studio or Vertex AI service credentials.
* [Google Cloud Project Billing](https://cloud.google.com/billing/) enabled.
* Python 3.11+ runtime.

### Python Dependencies

Install the required packages using **uv** (recommended) or **pip**:

```bash
# Using uv (recommended)
uv sync

# Or using uv pip
uv pip install -r requirements.txt

# Or using standard pip
pip install -r requirements.txt
```

You can execute CLI commands directly within the managed environment using `uv run`:
```bash
uv run python main.py [ARGS]
```

Core dependencies in `requirements.txt`:
* `google-genai` (Official Google Gemini SDK)
* `google-cloud-storage` (GCS client library)
* `google-cloud-bigquery` (BigQuery client library)
* `google-api-python-client` (YouTube Data API support)
* `pandas` & `pyarrow` (Data processing & BQ transport)
* `pyopenssl` (Secure TLS)

---

## Where to Start: Google Colab Quickstart

The easiest way to get started with interactive evaluations:

1. Navigate to [colab.research.google.com](http://colab.research.google.com).
2. In the dialog, select **GitHub**.
3. Enter the URL of this repository (`https://github.com/google-marketing-solutions/abcds-detector`).
4. Open the `[GitHub]_ABCDs_Detector.ipynb` notebook.
5. Follow the step-by-step cells to configure your API key, video paths, and run the ABCD assessment.

---

## Instructions & Video Bucket Setup

1. **Prepare Video Sources**:
   * **Cloud Storage**: Upload video files to a Google Cloud Storage bucket (e.g. `gs://[BUCKET_NAME]/ad.mp4` or folder `gs://[BUCKET_NAME]/campaign/`). Ensure the service account or authenticated user has `Storage Object Viewer` permissions on the bucket.
   * **YouTube**: Prepare public or channel-owned YouTube URLs.

2. **Configure Parameters**:
   * Set your GCP `project_id` and `api_key`.
   * Provide `brand_name` and `branded_products` (or enable dynamic brand extraction).
   * Specify ABCD slices (`universal`, `shorts`, or both).

3. **Run the Assessment**:
   * In Colab: run cells sequentially through the **Execute Bulk ABCD Assessment** step.
   * In CLI: run `python main.py` with your arguments.

---

## Additional Resources

* [Think with Google: YouTube ABCD Framework Best Practices](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)
* [Google Gemini API Documentation](https://ai.google.dev/docs)
* [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai)
* [Vertex AI Generative AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
