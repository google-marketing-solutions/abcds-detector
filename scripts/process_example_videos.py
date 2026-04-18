#!/usr/bin/env python3
"""Process example YouTube videos through the ABCD evaluation pipeline.

Generates public report URLs and keyframes, then writes metadata to
static/examples.json for the website gallery.

Usage:
    python scripts/process_example_videos.py
    python scripts/process_example_videos.py --resume   # skip already-processed
    python scripts/process_example_videos.py --video-id VqB98tCClPQ  # single video
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import (
    build_config,
    run_evaluation,
    _save_results_to_gcs,
    results_store,
    PUBLIC_BASE_URL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# The 13 example YouTube videos
EXAMPLE_VIDEOS = [
    "VqB98tCClPQ",
    "kLdaIxDM-_Y",
    "7vKCq52wWUY",
    "rRo5spaBfbo",
    "1-mgrFS00B0",
    "xf64Okfdc6Y",
    "SRxEiXiMIXk",
    "sf2Ry_deVN0",
    "g-6nRs4BqXQ",
    "kQRu7DdTTVA",
    "84MCtvXCt9E",
    "Z1yGy9fELtE",
    "lMTcZb48aVU",
]

BASE_URL = PUBLIC_BASE_URL or "https://app.aicreativereview.com"
EXAMPLES_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
    "examples.json",
)


def make_report_id(video_id: str) -> str:
    """Deterministic 8-char report ID from YouTube video ID."""
    return hashlib.md5(f"example_{video_id}".encode()).hexdigest()[:8]


def youtube_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def load_existing() -> list[dict]:
    """Load existing examples.json if present."""
    if os.path.exists(EXAMPLES_JSON):
        with open(EXAMPLES_JSON) as f:
            data = json.load(f)
            return data.get("examples", [])
    return []


def save_examples(examples: list[dict]) -> None:
    """Write examples.json with full metadata."""
    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "count": len(examples),
        "examples": examples,
    }
    with open(EXAMPLES_JSON, "w") as f:
        json.dump(payload, f, indent=2)
    log.info("Wrote %d examples to %s", len(examples), EXAMPLES_JSON)


def process_video(video_id: str, existing: list[dict]) -> Optional[dict]:
    """Process a single YouTube video and return metadata dict."""
    report_id = make_report_id(video_id)
    url = youtube_url(video_id)

    # Check if already processed
    for ex in existing:
        if ex.get("report_id") == report_id and ex.get("processed"):
            log.info("Skipping %s (already processed as %s)", video_id, report_id)
            return ex

    log.info("Processing %s → report_id=%s", video_id, report_id)
    config = build_config(
        use_abcd=True,
        use_shorts=False,
        use_ci=True,
        provider_type="YOUTUBE",
    )

    def on_progress(step, message, pct=0, partial=None):
        log.info("  [%3d%%] %s: %s", pct, step, message)

    try:
        start = time.time()
        results = run_evaluation(url, config, on_progress=on_progress)
        elapsed = time.time() - start

        # Assign report ID and save to GCS
        results["report_id"] = report_id
        results["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        results_store[report_id] = results
        _save_results_to_gcs(report_id, results)

        # Wait briefly for GCS write to complete
        time.sleep(2)

        # Extract metadata for examples.json
        abcd = results.get("abcd", {})
        persuasion = results.get("persuasion", {})
        predictions = results.get("predictions", {})
        brand_intel = results.get("brand_intelligence", {})
        scenes = results.get("scenes", [])

        # Get first keyframe as base64 for thumbnail (first scene)
        first_keyframe = ""
        for sc in scenes:
            if sc.get("keyframe"):
                first_keyframe = sc["keyframe"][:200] + "..."  # truncated reference
                break

        report_url = f"{BASE_URL}/report/{report_id}"
        meta = {
            "video_id": video_id,
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
            "keyframe_count": sum(1 for s in scenes if s.get("keyframe")),
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "keyframe_urls": [
                f"{BASE_URL}/api/keyframe/{report_id}/{i}"
                for i in range(len(scenes))
                if i < len(scenes) and scenes[i].get("keyframe")
            ],
            "processed": True,
            "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "processing_time_s": round(elapsed, 1),
        }

        log.info(
            "  Done: %s | ABCD=%s%% | Perf=%s | %d scenes | %.1fs",
            meta["brand_name"],
            meta["abcd_score"],
            meta["performance_score"],
            meta["scene_count"],
            elapsed,
        )
        return meta

    except Exception as ex:
        log.error("Failed to process %s: %s", video_id, ex, exc_info=True)
        return {
            "video_id": video_id,
            "youtube_url": url,
            "report_id": report_id,
            "report_url": f"{BASE_URL}/report/{report_id}",
            "brand_name": "",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "processed": False,
            "error": str(ex),
        }


def main():
    parser = argparse.ArgumentParser(description="Process example YouTube videos")
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip videos that are already processed in examples.json",
    )
    parser.add_argument(
        "--video-id", type=str, default=None,
        help="Process a single video ID instead of the full list",
    )
    args = parser.parse_args()

    existing = load_existing() if args.resume else []
    video_ids = [args.video_id] if args.video_id else EXAMPLE_VIDEOS

    log.info("=" * 60)
    log.info("Processing %d example videos", len(video_ids))
    log.info("=" * 60)

    results_list = []
    # Preserve any existing entries not being re-processed
    existing_by_id = {ex["video_id"]: ex for ex in existing}

    for i, vid in enumerate(video_ids):
        log.info("\n[%d/%d] Video: %s", i + 1, len(video_ids), vid)
        meta = process_video(vid, existing)
        if meta:
            existing_by_id[vid] = meta

    # Build final list in original order
    for vid in EXAMPLE_VIDEOS:
        if vid in existing_by_id:
            results_list.append(existing_by_id[vid])

    save_examples(results_list)

    # Summary
    processed = sum(1 for r in results_list if r.get("processed"))
    failed = sum(1 for r in results_list if not r.get("processed"))
    log.info("\n" + "=" * 60)
    log.info("SUMMARY: %d processed, %d failed, %d total", processed, failed, len(results_list))
    log.info("=" * 60)

    if processed > 0:
        log.info("\nPublic Report URLs:")
        for r in results_list:
            if r.get("processed"):
                log.info("  %s → %s", r["video_id"], r["report_url"])
                if r.get("keyframe_urls"):
                    log.info("    Keyframes: %s", r["keyframe_urls"][0])


if __name__ == "__main__":
    main()
