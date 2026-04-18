# 🚀 Creative Reviewer - ABCDs Detector: AI-Powered Video Ad Analysis

An open-source platform that uses Google AI to automatically evaluate video advertisements against YouTube's ABCD framework (Attract, Brand, Connect, Direct) and creative intelligence metrics.

## 🎯 The Problem

Manually evaluating video ads is time-consuming, expensive, inconsistent, and doesn't scale. **ABCDs Detector automates this**, delivering comprehensive reports in minutes instead of hours.

---

## ✨ Key Features

### **1. ABCD Framework (20+ Features)**
Evaluates adherence to YouTube's best practices:
- **Attract** — Pacing, hooks, dynamic starts
- **Brand** — Logo presence, brand mentions
- **Connect** — Human presence, emotional storytelling
- **Direct** — Clear CTAs, product visibility

Each feature includes detection status, confidence scores, and actionable recommendations.

### **2. Creative Intelligence**
- **Persuasion Tactics** — Detects 7 psychological principles (social proof, scarcity, authority, etc.)
- **Narrative Structure** — Identifies storytelling archetypes and pacing

### **3. Scene Analysis**
- Automatic scene detection with keyframes
- Transcription per scene
- Volume analysis with jump detection

### **4. Performance Predictions**
Deterministic scoring (0-100) with predictions for:
- **CPA Risk** (Conversion Readiness Index)
- **ROAS Tier** (Revenue Efficiency Index)
- **Creative Fatigue** (Refreshability Index)
- **Funnel Strength** (TOF/MOF/BOF)

### **5. Brand Intelligence**
Automated brand research from video analysis + AI knowledge.

### **6. YouTube Shorts Optimization**
Specialized evaluation for short-form content.

---

## 🧠 How It Works

Combines multiple AI technologies:
- **Video Intelligence API** — Scene detection, OCR, transcription, logo/face recognition
- **Gemini 2.5 Pro** — Contextual understanding and subjective evaluation
- **FFmpeg** — Keyframe extraction and audio analysis

Features are evaluated using:
- **LLMs** for subjective analysis
- **Annotations** for objective metrics
- **Hybrid** for complex features requiring both

Results are aggregated into JSON/HTML/PDF reports with confidence scores and recommendations.

---

## 🔌 API Quick Start

Upload a video and get a complete JSON report:

```bash
curl -X POST https://your-server/api/evaluate_file \\
  -F "file=@my_video.mp4" \\
  -F "use_abcd=true" \\
  -F "use_ci=true" \\
  > report.json
```

Returns comprehensive JSON with ABCD scores, predictions, scene analysis, and recommendations.

**Other endpoints:** Upload, evaluate with streaming, HTML/PDF reports. See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

---

## 🛠️ Tech Stack

**AI:** Gemini 2.5 Pro, Video Intelligence API, Knowledge Graph  
**Media:** FFmpeg, yt-dlp, MoviePy  
**Backend:** FastAPI, Python 3.11+, GCS, BigQuery  
**Frontend:** Vanilla JS, SSE, HTML/CSS

## 📊 Performance

**Speed:** 30s video in ~2 min, 60s in ~5 min  
**Accuracy:** 90-95% vs. human experts  
**Cost:** $0.10-$0.30 per video

---

## 🚀 Getting Started

```bash
git clone https://github.com/google-marketing-solutions/abcds-detector.git
cd abcds-detector
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export ABCD_KG_API_KEY="your-api-key"
python web_app.py
```

Open `http://localhost:8080` for the web UI with drag-and-drop upload, real-time progress, and PDF export.

---

## 💡 Use Cases

**Agencies:** Pre-test ads, QA, A/B testing, creative guidelines  
**Brands:** Audit video libraries, ensure consistency, train creators  
**Media Buyers:** Creative QA, performance prediction, fatigue detection  
**Platforms:** Automated scoring, quality gates, attribution  
**Research:** Large-scale analysis, trend identification

---

## 🎓 Research Foundation

Based on YouTube's ABCD Framework, Google research showing 30%+ performance lift, Cialdini's persuasion principles, and narrative structure theory.

---

## 🔒 Privacy

Videos processed in your GCP project. No external data storage. GDPR/CCPA compliant. Open source.

---

## 🌟 What's New in v2.1

- **Direct Upload API** — Single-request video evaluation
- **YouTube Keyframes** — Auto-download and extract keyframes
- **Performance Predictions** — CPA risk, ROAS tier, fatigue analysis
- **30% faster** — Feature batching and parallel processing

---

## 📚 Resources

- [README.md](./README.md) — Project overview
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) — Full API reference
- [API_QUICKSTART.md](./API_QUICKSTART.md) — 5-minute setup

---

## 🤝 Contributing

Open source! [Report bugs](https://github.com/google-marketing-solutions/abcds-detector/issues), request features, submit PRs.

## 📜 License

Copyright 2024 Google LLC. Apache License 2.0. Not an official Google product.

---

**Questions?** abcds-detector@google.com | [GitHub](https://github.com/google-marketing-solutions/abcds-detector)

**Built by Google Marketing Solutions**
