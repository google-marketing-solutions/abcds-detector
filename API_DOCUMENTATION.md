# ABCDs Detector API Documentation

## Overview

The ABCDs Detector provides a REST API for evaluating video advertisements against YouTube's ABCD framework and other creative intelligence metrics.

Base URL: `http://localhost:8080` (or your deployed server URL)

---

## Endpoints

### 1. POST `/api/evaluate_file`

Upload a video file and receive a complete evaluation report as JSON.

**This is a synchronous endpoint** - it uploads the video, runs the full evaluation pipeline, and returns the complete report. Processing time depends on video length and evaluation options selected (typically 2-10 minutes).

#### Request

**Method:** `POST`

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | File | Yes | - | Video file to evaluate (MP4 recommended, max 500MB) |
| `use_abcd` | Boolean | No | `true` | Evaluate ABCD framework features |
| `use_shorts` | No | `false` | Evaluate YouTube Shorts-specific features |
| `use_ci` | Boolean | No | `true` | Evaluate Creative Intelligence features (persuasion, structure) |

#### Response

**Status Code:** `200 OK` (on success)

**Content-Type:** `application/json`

**Response Body:**

```json
{
  "brand_name": "Example Brand",
  "video_name": "ad_video.mp4",
  "video_uri": "gs://bucket-name/ad_video.mp4",
  "report_id": "a1b2c3d4",
  "timestamp": "2026-02-21T05:30:00",
  "file_size_mb": 12.45,
  
  "abcd": {
    "score": 85.7,
    "result": "Excellent",
    "passed": 18,
    "total": 21,
    "features": [
      {
        "id": "quick_pacing",
        "name": "Quick Pacing",
        "category": "LONG_FORM_ABCD",
        "sub_category": "ATTRACT",
        "detected": true,
        "confidence": 0.92,
        "rationale": "Video demonstrates rapid shot changes...",
        "evidence": "Average shot duration: 1.8 seconds",
        "strengths": "Maintains viewer attention effectively",
        "weaknesses": ""
      }
      // ... more features
    ]
  },
  
  "persuasion": {
    "density": 71.4,
    "detected": 5,
    "total": 7,
    "features": [
      {
        "id": "social_proof",
        "name": "Social Proof",
        "detected": true,
        "confidence": 0.88,
        "rationale": "Customer testimonials present...",
        "evidence": "\"10,000+ satisfied customers\"",
        "strengths": "Strong credibility indicators",
        "weaknesses": ""
      }
      // ... more tactics
    ]
  },
  
  "structure": {
    "features": [
      {
        "id": "creative_structure",
        "name": "Creative Structure",
        "detected": true,
        "confidence": 1.0,
        "rationale": "Follows problem-solution narrative arc",
        "evidence": "Hero's Journey, Problem-Solution",
        "strengths": "Clear narrative progression",
        "weaknesses": ""
      }
    ]
  },
  
  "scenes": [
    {
      "scene_number": 1,
      "start_time": "0:00",
      "end_time": "0:05",
      "description": "Opening shot showing product...",
      "transcript": "Introducing the all-new...",
      "keyframe": "/9j/4AAQSkZJRg...",  // base64-encoded JPEG
      "volume_db": -18.5,
      "volume_pct": 69.2,
      "volume_change_pct": 0.0,
      "volume_flag": false
    }
    // ... more scenes
  ],
  
  "brand_intelligence": {
    "company_name": "Example Brand Inc.",
    "website": "https://example.com",
    "product_service": "Premium consumer electronics",
    "brand_positioning": "Innovative, accessible technology",
    "target_audience_primary": "Tech-savvy millennials...",
    "tone": "Friendly, innovative, aspirational",
    "products_pricing": ["Product A - $99", "Product B - $199"],
    // ... more fields
  },
  
  "shorts": {
    "features": []  // Only populated if use_shorts=true
  }
}
```

#### Error Response

**Status Code:** `500 Internal Server Error` (on failure)

```json
{
  "error": "Evaluation failed: <error message>"
}
```

---

## Usage Examples

### Python (using requests)

```python
import requests

# Prepare the request
files = {'file': open('my_video.mp4', 'rb')}
data = {
    'use_abcd': 'true',
    'use_shorts': 'false',
    'use_ci': 'true'
}

# Make the request
response = requests.post(
    'http://localhost:8080/api/evaluate_file',
    files=files,
    data=data,
    timeout=600  # 10 minutes
)

# Get the report
if response.status_code == 200:
    report = response.json()
    print(f"ABCD Score: {report['abcd']['score']}%")
    print(f"Report ID: {report['report_id']}")
else:
    print(f"Error: {response.text}")
```

### JavaScript (using fetch)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('use_abcd', 'true');
formData.append('use_shorts', 'false');
formData.append('use_ci', 'true');

fetch('http://localhost:8080/api/evaluate_file', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(report => {
    console.log('ABCD Score:', report.abcd.score);
    console.log('Report ID:', report.report_id);
})
.catch(error => console.error('Error:', error));
```

### curl

```bash
curl -X POST http://localhost:8080/api/evaluate_file \
  -F "file=@my_video.mp4" \
  -F "use_abcd=true" \
  -F "use_shorts=false" \
  -F "use_ci=true" \
  -o report.json

# Pretty-print the result
cat report.json | python -m json.tool
```

---

## Response Schema

### ABCD Features Object

```typescript
{
  score: number,        // 0-100 percentage
  result: string,       // "Excellent" | "Might Improve" | "Needs Review"
  passed: number,       // Number of features passed
  total: number,        // Total features evaluated
  features: Feature[]   // Detailed feature results
}
```

### Feature Object

```typescript
{
  id: string,           // Unique feature identifier
  name: string,         // Human-readable feature name
  category: string,     // "LONG_FORM_ABCD" | "SHORTS" | "CREATIVE_INTELLIGENCE"
  sub_category: string, // "ATTRACT" | "BRAND" | "CONNECT" | "DIRECT" | "PERSUASION" | "STRUCTURE"
  detected: boolean,    // Whether feature was detected
  confidence: number,   // 0.0-1.0 confidence score
  rationale: string,    // Why this determination was made
  evidence: string,     // Specific evidence from the video
  strengths: string,    // What was done well
  weaknesses: string    // Areas for improvement
}
```

### Scene Object

```typescript
{
  scene_number: number,      // Sequential scene number
  start_time: string,        // "M:SS" or "H:MM:SS" format
  end_time: string,          // "M:SS" or "H:MM:SS" format
  description: string,       // What's happening in the scene
  transcript: string,        // Spoken words or "[No speech]"
  keyframe: string,          // Base64-encoded JPEG image
  volume_db: number,         // Audio level in dB
  volume_pct: number,        // Audio level as 0-100%
  volume_change_pct: number, // Change from previous scene
  volume_flag: boolean       // True if volume jump detected
}
```

---

## Related Endpoints

### GET `/api/results/{report_id}`

Retrieve a previously generated report by its ID.

**Response:** Same JSON structure as `/api/evaluate_file`

### GET `/report/{report_id}`

View the HTML report in a browser.

**Response:** HTML page with full report visualization

### GET `/api/report/{report_id}/pdf`

Download the report as a PDF.

**Response:** PDF file (application/pdf)

---

## Best Practices

1. **Timeout:** Set adequate timeout values (5-10 minutes) as evaluation takes time
2. **File Size:** Keep videos under 500MB for best performance
3. **Format:** MP4 format with H.264 codec is recommended
4. **Keyframes:** To receive scene keyframes, ensure videos are GCS URIs or publicly accessible YouTube URLs
5. **Error Handling:** Implement retry logic with exponential backoff for production use
6. **Caching:** Reports are cached in-memory by report_id for subsequent retrieval

---

## Rate Limits & Quotas

API usage is subject to:
- Google Cloud API quotas (Video Intelligence, Vertex AI)
- Storage limits in your GCS bucket
- Server memory for in-memory report storage

Refer to [Google Cloud pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) for cost details.

---

## Support

For issues or questions:
- GitHub Issues: [abcds-detector repository](https://github.com/google-marketing-solutions/abcds-detector)
- Email: abcds-detector@google.com

---

## Changelog

### Version 2.1 (February 2026)
- ✨ NEW: `/api/evaluate_file` endpoint for direct file upload and JSON response
- 🖼️ Enhanced: YouTube video keyframe extraction support
- 🔧 Improved: Automatic ffmpeg path detection across platforms
