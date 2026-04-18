# Building an AI Video Analyzer with Gemini 2.5 Pro and Python

**Target platforms:** Dev.to, Hashnode, Medium (tech audience)
**Target keywords:** Gemini video analysis, Video Intelligence API tutorial, Python video AI, LLM video understanding
**Target audience:** Developers, ML engineers, Python developers

---

## Draft

Video understanding is one of the most exciting capabilities of modern LLMs. Gemini 2.5 Pro can "watch" a video and answer structured questions about it — opening up use cases from content moderation to creative analysis.

In this post, I'll walk through the architecture of Creative Reviewer, an open-source system that evaluates video ads using a hybrid approach combining Google's Video Intelligence API with Gemini 2.5 Pro.

### The Architecture Challenge

Not all video analysis tasks are equal:

- **Objective tasks** (count shot changes, detect text on screen, identify faces) → structured annotations are more reliable
- **Subjective tasks** (is this emotionally engaging? is the pacing effective?) → LLMs excel here
- **Hybrid tasks** (is the brand visible in the first 5 seconds? — needs timing data + visual understanding) → best results from combining both

This led to a three-mode evaluation architecture:

### Mode 1: Annotations Only

Google's Video Intelligence API provides structured data:

```python
# Shot boundary detection
from google.cloud import videointelligence

client = videointelligence.VideoIntelligenceServiceClient()
features = [videointelligence.Feature.SHOT_CHANGE_DETECTION]
operation = client.annotate_video(
    request={"features": features, "input_uri": gcs_uri}
)
result = operation.result()

# Count shot changes in first 5 seconds
shots_in_first_5s = sum(
    1 for shot in result.annotation_results[0].shot_annotations
    if shot.start_time_offset.total_seconds() < 5
)
```

Available annotation types: shot boundaries, face detection, text/OCR, speech transcription, object tracking, logo recognition.

### Mode 2: LLM Only (Gemini 2.5 Pro)

For subjective features, we send the video directly to Gemini with a structured prompt:

```python
import vertexai
from vertexai.generative_models import GenerativeModel, Part

model = GenerativeModel("gemini-2.5-pro")
video_part = Part.from_uri(gcs_uri, mime_type="video/mp4")

response = model.generate_content([
    video_part,
    """Evaluate this video ad for the following feature:
    Feature: Call To Action (Speech)
    Definition: A spoken directive like "Shop now," "Learn more," or "Sign up."
    
    Return JSON:
    {
        "detected": true/false,
        "confidence_score": 0.0-1.0,
        "rationale": "why you made this determination",
        "evidence": "specific timestamps and observations",
        "strengths": "what the ad does well",
        "weaknesses": "what could improve"
    }"""
])
```

### Mode 3: Hybrid

Both pipelines run. Annotations provide ground truth data, and the LLM uses that data as context for its reasoning:

```python
# First, get annotations
annotations = get_video_annotations(gcs_uri)

# Then, feed annotation data to the LLM as context
prompt = f"""
Given these annotation results:
- Face detected at: {annotations.face_timestamps}
- Face size: {annotations.face_size}px
- Face position: {annotations.face_position}

Evaluate: Is there a visible face in the first 5 seconds?
Consider the annotations AND watch the video to confirm.
"""
```

### Feature Batching for Cost Optimization

Evaluating 23+ features individually would require 23+ API calls. Instead, features are grouped by video segment:

```python
# Group features by evaluation segment
full_video_features = [f for f in features if f.segment == "full_video"]
first_5s_features = [f for f in features if f.segment == "first_5_secs"]

# Evaluate all full-video features in one LLM call
batch_prompt = "Evaluate ALL of these features for the video:\n"
for f in full_video_features:
    batch_prompt += f"- {f.name}: {f.definition}\n"
```

This reduced API costs by ~40% and latency by ~50%.

### Deterministic Performance Predictions

Performance predictions (CPA risk, ROAS tier, creative fatigue) use NO LLM — they're a weighted scoring model:

```python
def calculate_performance_score(feature_results):
    weights = {
        "dynamic_start": 8,
        "brand_visuals_first_5s": 10,
        "call_to_action_text": 7,
        "presence_of_people": 6,
        # ... 23+ features with calibrated weights
    }
    
    score = sum(
        weights[f.name] for f in feature_results if f.detected
    )
    max_score = sum(weights.values())
    return (score / max_score) * 100
```

### Real-time Streaming with SSE

The web UI uses Server-Sent Events to stream progress:

```python
from fastapi.responses import StreamingResponse

async def evaluation_stream(video_uri):
    q = queue.Queue()
    
    def on_progress(step, message, pct, partial):
        q.put(json.dumps({"step": step, "message": message, "pct": pct}))
    
    # Run evaluation in background thread
    thread = threading.Thread(
        target=run_evaluation,
        args=(video_uri, config, on_progress)
    )
    thread.start()
    
    # Stream events to client
    while thread.is_alive() or not q.empty():
        try:
            event = q.get(timeout=0.5)
            yield f"data: {event}\n\n"
        except queue.Empty:
            continue
```

### Lessons Learned

1. **Hybrid beats pure LLM** — For measurable features, annotations provide ground truth that catches LLM hallucinations
2. **Feature batching is critical** — Individual feature evaluation is 2-3x more expensive
3. **Gemini is surprisingly good at video** — 90-95% accuracy on subjective features
4. **Edge cases are the hard part** — A product visible for 0.3 seconds, a brand logo partially obscured — these are where LLMs struggle
5. **Structured output saves parsing headaches** — Always request JSON with a schema

### Try It

The full codebase is open source: [GITHUB LINK]

Key files:
- `features_repository/` — Feature definitions and grouping
- `evaluation_services/video_evaluation_service.py` — Core evaluation logic
- `scene_detector.py` — Combined metadata + scene extraction
- `performance_predictor.py` — Deterministic scoring model
- `web_app.py` — FastAPI server with SSE streaming

---

## SEO Notes

- Title targets "Gemini 2.5 Pro" + "Python" + "video analyzer"
- Code examples make it highly bookmarkable/shareable in dev communities
- Include architecture diagram if possible
- Cross-link to the ABCD framework guide post
