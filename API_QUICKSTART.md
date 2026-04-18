# API Quick Start Guide

## New Feature: Direct Video Upload & JSON Response

The ABCDs Detector now includes a **synchronous API endpoint** that allows you to:
1. Upload a video file directly
2. Get the complete evaluation report as JSON in a single request

---

## Quick Start

### 1. Start the Server

```bash
python web_app.py
```

The API will be available at `http://localhost:8080`

### 2. Upload a Video and Get Results

#### Using curl:

```bash
curl -X POST http://localhost:8080/api/evaluate_file \
  -F "file=@your_video.mp4" \
  -F "use_abcd=true" \
  -F "use_shorts=false" \
  -F "use_ci=true" \
  > report.json
```

#### Using Python:

```python
import requests

files = {'file': open('your_video.mp4', 'rb')}
data = {'use_abcd': 'true', 'use_ci': 'true'}

response = requests.post(
    'http://localhost:8080/api/evaluate_file',
    files=files,
    data=data,
    timeout=600
)

report = response.json()
print(f"ABCD Score: {report['abcd']['score']}%")
```

#### Using the Test Script:

```bash
./test_api_endpoint.sh your_video.mp4
```

---

## Response Structure

The endpoint returns a complete JSON report:

```json
{
  "brand_name": "Example Brand",
  "video_name": "video.mp4",
  "report_id": "abc12345",
  "timestamp": "2026-02-21T12:00:00",
  
  "abcd": {
    "score": 85.7,
    "result": "Excellent",
    "passed": 18,
    "total": 21,
    "features": [...]
  },
  
  "persuasion": {
    "density": 71.4,
    "detected": 5,
    "total": 7,
    "features": [...]
  },
  
  "structure": {
    "features": [...]
  },
  
  "scenes": [
    {
      "scene_number": 1,
      "start_time": "0:00",
      "end_time": "0:05",
      "description": "...",
      "transcript": "...",
      "keyframe": "base64-encoded-image",
      "volume_db": -18.5,
      "volume_pct": 69.2
    }
  ],
  
  "brand_intelligence": {...}
}
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | *required* | Video file (MP4, max 500MB) |
| `use_abcd` | Boolean | `true` | Evaluate ABCD features |
| `use_shorts` | Boolean | `false` | Evaluate YouTube Shorts features |
| `use_ci` | Boolean | `true` | Evaluate Creative Intelligence |

---

## Processing Time

- **Short videos (<1 min)**: 2-3 minutes
- **Medium videos (1-3 min)**: 5-7 minutes  
- **Longer videos (3-5 min)**: 10+ minutes

Set appropriate timeouts in your client!

---

## Complete Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for:
- Full response schema
- All endpoints
- Error handling
- Best practices

---

## Examples

Ready-to-use examples are in [examples/api_client_example.py](./examples/api_client_example.py):

```bash
# View examples
python examples/api_client_example.py

# Run specific example
python examples/api_client_example.py
# (then uncomment the example you want to run)
```

---

## What's Included in Reports

✅ **ABCD Framework** - 20+ YouTube best practice features  
✅ **Persuasion Tactics** - Psychological influence techniques  
✅ **Creative Structure** - Narrative arc analysis  
✅ **Scene-by-Scene** - Breakdown with keyframes & transcripts  
✅ **Volume Analysis** - Audio level detection & warnings  
✅ **Brand Intelligence** - Automated brand research brief  

---

## Tips

1. **Use MP4 format** for best compatibility
2. **Set generous timeouts** (10 minutes recommended)
3. **Process during off-peak hours** if doing batch processing
4. **Cache results** using the returned `report_id`
5. **Extract keyframes** from the base64 data in scenes

---

## Troubleshooting

**"Evaluation failed: yt-dlp not found"**
```bash
pip install yt-dlp
```

**"Timeout"**
- Increase your client timeout
- Try with a shorter video first
- Check server logs for the actual error

**"No keyframes in scenes"**
- Only GCS and YouTube videos support keyframes
- Ensure ffmpeg is installed: `brew install ffmpeg`

---

## Next Steps

- 📖 Read [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for full details
- 🔧 Try [examples/api_client_example.py](./examples/api_client_example.py)
- 🧪 Run `./test_api_endpoint.sh your_video.mp4`
- 📊 View reports at `/report/{report_id}` in your browser

---

**Need help?** Open an issue or email abcds-detector@google.com
