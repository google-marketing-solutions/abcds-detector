#!/usr/bin/env python3
"""Test script to verify keyframe extraction for YouTube videos."""

import sys
import logging
from scene_detector import download_video_locally, extract_keyframes, cleanup_temp_dir
from configuration import Configuration

logging.basicConfig(level=logging.INFO)

def test_youtube_keyframe_extraction():
    """Test downloading a YouTube video and extracting keyframes."""
    
    # Use a short, public YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up (for testing)
    
    # Create a minimal config
    config = Configuration()
    config.set_parameters(
        project_id="test-project",
        project_zone="us-central1",
        bucket_name="test-bucket",
        knowledge_graph_api_key="",
        bigquery_dataset="",
        bigquery_table="",
        assessment_file="",
        extract_brand_metadata=False,
        use_annotations=False,
        use_llms=False,
        run_long_form_abcd=False,
        run_shorts=False,
        run_creative_intelligence=False,
        features_to_evaluate=[],
        creative_provider_type="YOUTUBE",
        verbose=True,
    )
    
    print(f"\n{'='*60}")
    print(f"Testing YouTube video download and keyframe extraction")
    print(f"URL: {test_url}")
    print(f"{'='*60}\n")
    
    # Download video
    print("Step 1: Downloading YouTube video...")
    tmp_dir, video_path = download_video_locally(config, test_url)
    
    if not video_path:
        print("❌ FAILED: Could not download video")
        print("\nMake sure yt-dlp is installed:")
        print("  pip install yt-dlp")
        return False
    
    print(f"✓ Video downloaded to: {video_path}")
    
    # Create test scenes
    test_scenes = [
        {"scene_number": 1, "start_time": "0:05", "end_time": "0:10"},
        {"scene_number": 2, "start_time": "0:15", "end_time": "0:20"},
    ]
    
    # Extract keyframes
    print("\nStep 2: Extracting keyframes...")
    keyframes = extract_keyframes(test_scenes, video_path)
    
    if not keyframes or all(not k for k in keyframes):
        print("❌ FAILED: No keyframes extracted")
        cleanup_temp_dir(tmp_dir)
        return False
    
    print(f"✓ Extracted {len([k for k in keyframes if k])} keyframes")
    for i, kf in enumerate(keyframes):
        if kf:
            print(f"  Scene {i+1}: {len(kf)} bytes (base64)")
        else:
            print(f"  Scene {i+1}: [empty]")
    
    # Cleanup
    print("\nStep 3: Cleaning up...")
    cleanup_temp_dir(tmp_dir)
    print("✓ Cleanup complete")
    
    print(f"\n{'='*60}")
    print("✅ TEST PASSED: YouTube keyframe extraction working!")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    try:
        success = test_youtube_keyframe_extraction()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
