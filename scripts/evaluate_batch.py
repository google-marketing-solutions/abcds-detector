#!/usr/bin/env python3
"""Batch evaluate YouTube videos via download → GCS upload → evaluation.

Vertex AI Gemini does not support YouTube URLs directly (requires video
ownership). This script downloads each video with pytubefix, uploads to GCS,
and then runs the full evaluation pipeline against the GCS URI.

Usage:
    python scripts/evaluate_batch.py
    python scripts/evaluate_batch.py --video-index 0   # single video
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
import os
import re
import sys
import time
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pytubefix import YouTube
from google.cloud import storage

from web_app import (
    build_config,
    run_evaluation,
    upload_to_gcs,
    _save_results_to_gcs,
    results_store,
    PUBLIC_BASE_URL,
    PROJECT_ID,
    BUCKET_NAME,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# Videos to evaluate
VIDEOS = [
    {"label": "JonesRoad - DustyRose", "url": "https://www.youtube.com/watch?v=vtELqF9LYds"},
    {"label": "StateBags", "url": "https://www.youtube.com/watch?v=sz-jDaNB46Q"},
    {"label": "Laundry Sauce", "url": "https://www.youtube.com/watch?v=_clSytDt_JA"},
    {"label": "Newton Baby", "url": "https://www.youtube.com/watch?v=cSGLoY8vJXo"},
    {"label": "Latico Leather Bags", "url": "https://www.youtube.com/watch?v=9eI9LuovG1g"},
    {"label": "Fatty15", "url": "https://www.youtube.com/watch?v=gC3pRK6ygRM"},
    {"label": "Elevated Landscape - Jones Road", "url": "https://www.youtube.com/watch?v=jzR4BSQgf9Y"},
    {"label": "Image Slideshow - Momofuku Noodles", "url": "https://www.youtube.com/watch?v=_q8NYTE8Qgk"},
    {"label": "UGC Talking Heads", "url": "https://www.youtube.com/watch?v=YbbieOp34Ac"},
]

BASE_URL = PUBLIC_BASE_URL or "https://app.aicreativereview.com"
TMP_DIR = "/tmp/batch_eval"


def make_report_id(url: str) -> str:
    """Deterministic 8-char report ID from URL."""
    return hashlib.md5(f"batch_{url}".encode()).hexdigest()[:8]


def download_youtube_video(url: str, label: str) -> Optional[str]:
    """Download a YouTube video to a local temp file. Returns local path or None."""
    try:
        yt = YouTube(url)
        log.info("  Downloading: %s (%ds)", yt.title, yt.length)

        # Try progressive (audio+video combined) MP4 first
        stream = (
            yt.streams.filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
        )
        if not stream:
            stream = yt.streams.filter(file_extension="mp4").first()
        if not stream:
            stream = yt.streams.first()

        if not stream:
            log.error("  No downloadable stream for %s", label)
            return None

        os.makedirs(TMP_DIR, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", label) + ".mp4"
        path = stream.download(output_path=TMP_DIR, filename=safe_name)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        log.info("  Downloaded: %s (%.1f MB, %s)", safe_name, size_mb, stream.resolution)
        return path

    except Exception as ex:
        log.error("  Download failed for %s: %s", label, ex)
        return None


def process_video(video: dict) -> Optional[dict]:
    """Download, upload, evaluate a single YouTube video."""
    url = video["url"]
    label = video["label"]
    report_id = make_report_id(url)

    log.info("Processing: %s → %s (report_id=%s)", label, url, report_id)

    # Step 1: Download from YouTube
    local_path = download_youtube_video(url, label)
    if not local_path:
        return {
            "label": label,
            "youtube_url": url,
            "report_id": report_id,
            "report_url": f"{BASE_URL}/report/{report_id}",
            "processed": False,
            "error": "Download failed",
        }

    try:
        # Step 2: Upload to GCS
        safe_name = os.path.basename(local_path)
        gcs_dest = f"batch_eval/{safe_name}"
        log.info("  Uploading to GCS: gs://%s/%s", BUCKET_NAME, gcs_dest)
        gcs_uri = upload_to_gcs(local_path, gcs_dest)
        log.info("  Uploaded: %s", gcs_uri)

        # Clean up local file
        os.unlink(local_path)

        # Step 3: Run evaluation with GCS URI
        log.info("  Running evaluation...")
        config = build_config(
            use_abcd=True,
            use_shorts=False,
            use_ci=True,
            provider_type="GCS",
        )

        def on_progress(step, message, pct=0, partial=None):
            log.info("  [%3d%%] %s: %s", pct, step, message)

        start = time.time()
        results = run_evaluation(gcs_uri, config, on_progress=on_progress)
        elapsed = time.time() - start

        # Step 4: Save results
        results["report_id"] = report_id
        results["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        results["youtube_url"] = url
        results_store[report_id] = results
        _save_results_to_gcs(report_id, results)

        time.sleep(2)

        abcd = results.get("abcd", {})
        persuasion = results.get("persuasion", {})
        predictions = results.get("predictions", {})
        scenes = results.get("scenes", [])

        report_url = f"{BASE_URL}/report/{report_id}"
        meta = {
            "label": label,
            "youtube_url": url,
            "report_id": report_id,
            "report_url": report_url,
            "brand_name": results.get("brand_name", ""),
            "video_name": results.get("video_name", ""),
            "abcd_score": abcd.get("score", 0),
            "abcd_result": abcd.get("result", ""),
            "persuasion_density": persuasion.get("density", 0),
            "performance_score": predictions.get("overall_score", 0),
            "scene_count": len(scenes),
            "processing_time_s": round(elapsed, 1),
            "processed": True,
        }

        log.info(
            "  Done: %s | ABCD=%s%% | Persuasion=%s%% | Perf=%s | %d scenes | %.1fs",
            meta["brand_name"],
            meta["abcd_score"],
            meta["persuasion_density"],
            meta["performance_score"],
            meta["scene_count"],
            elapsed,
        )
        return meta

    except Exception as ex:
        log.error("Failed to process %s: %s", label, ex, exc_info=True)
        if local_path and os.path.exists(local_path):
            os.unlink(local_path)
        return {
            "label": label,
            "youtube_url": url,
            "report_id": report_id,
            "report_url": f"{BASE_URL}/report/{report_id}",
            "processed": False,
            "error": str(ex),
        }


def main():
    parser = argparse.ArgumentParser(description="Batch evaluate YouTube videos")
    parser.add_argument(
        "--video-index", type=int, default=None,
        help="Process a single video by index (0-based)",
    )
    args = parser.parse_args()

    videos = [VIDEOS[args.video_index]] if args.video_index is not None else VIDEOS

    log.info("=" * 60)
    log.info("Batch Creative Evaluation — %d videos", len(videos))
    log.info("Pipeline: YouTube → pytubefix → GCS → Gemini Pro")
    log.info("=" * 60)

    results_list = []
    for i, video in enumerate(videos):
        log.info("\n[%d/%d] %s", i + 1, len(videos), video["label"])
        meta = process_video(video)
        if meta:
            results_list.append(meta)

    # Summary
    log.info("\n" + "=" * 60)
    log.info("BATCH EVALUATION COMPLETE")
    log.info("=" * 60)

    processed = [r for r in results_list if r.get("processed")]
    failed = [r for r in results_list if not r.get("processed")]

    log.info("%d processed, %d failed\n", len(processed), len(failed))

    if processed:
        log.info("Report URLs:")
        for r in processed:
            log.info(
                "  %-40s ABCD=%3s%%  Persuasion=%3s%%  Perf=%3s  %s",
                r["label"],
                r["abcd_score"],
                r["persuasion_density"],
                r["performance_score"],
                r["report_url"],
            )

    if failed:
        log.info("\nFailed:")
        for r in failed:
            log.info("  %s — %s", r["label"], r.get("error", "unknown"))

    # Save summary JSON
    summary_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "batch_evaluation_results.json",
    )
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump({
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "count": len(results_list),
            "results": results_list,
        }, f, indent=2)
    log.info("\nResults saved to: %s", summary_path)


if __name__ == "__main__":
    main()
