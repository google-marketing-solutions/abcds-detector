#!/usr/bin/env python3
"""
Example client code for using the /api/evaluate_file endpoint.

This demonstrates how to:
1. Upload a video file
2. Get the complete JSON report response
3. Access specific data from the report
"""

import json
import requests
from pathlib import Path


def evaluate_video_file(
    video_path: str,
    api_url: str = "http://localhost:8080",
    use_abcd: bool = True,
    use_shorts: bool = False,
    use_ci: bool = True,
) -> dict:
    """
    Upload a video file and get the evaluation report.
    
    Args:
        video_path: Path to the local video file
        api_url: Base URL of the API server
        use_abcd: Evaluate ABCD framework features
        use_shorts: Evaluate YouTube Shorts features
        use_ci: Evaluate Creative Intelligence features
    
    Returns:
        Complete evaluation report as a dictionary
    """
    endpoint = f"{api_url}/api/evaluate_file"
    
    # Prepare the file
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    print(f"📹 Uploading video: {video_file.name}")
    print(f"   Size: {video_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Prepare the multipart form data
    files = {
        'file': (video_file.name, open(video_file, 'rb'), 'video/mp4')
    }
    
    data = {
        'use_abcd': str(use_abcd).lower(),
        'use_shorts': str(use_shorts).lower(),
        'use_ci': str(use_ci).lower(),
    }
    
    print(f"⚙️  Evaluation options:")
    print(f"   ABCD Framework: {use_abcd}")
    print(f"   YouTube Shorts: {use_shorts}")
    print(f"   Creative Intelligence: {use_ci}")
    print()
    print("⏳ Processing... (this may take several minutes)")
    
    # Make the request
    response = requests.post(endpoint, files=files, data=data, timeout=600)
    
    # Close the file
    files['file'][1].close()
    
    if response.status_code == 200:
        print("✅ Evaluation complete!")
        return response.json()
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()


def display_report_summary(report: dict):
    """Display a summary of the evaluation report."""
    print("\n" + "="*60)
    print("📊 EVALUATION REPORT SUMMARY")
    print("="*60)
    
    # Basic info
    print(f"\n🏢 Brand: {report.get('brand_name', 'Unknown')}")
    print(f"🎬 Video: {report.get('video_name', 'Unknown')}")
    print(f"📅 Timestamp: {report.get('timestamp', 'Unknown')}")
    print(f"🆔 Report ID: {report.get('report_id', 'Unknown')}")
    
    # ABCD Score
    abcd = report.get('abcd', {})
    if abcd.get('total', 0) > 0:
        print(f"\n📈 ABCD Score: {abcd['score']}%")
        print(f"   Result: {abcd['result']}")
        print(f"   Passed: {abcd['passed']}/{abcd['total']} features")
    
    # Persuasion
    persuasion = report.get('persuasion', {})
    if persuasion.get('total', 0) > 0:
        print(f"\n🎯 Persuasion Density: {persuasion['density']}%")
        print(f"   Detected: {persuasion['detected']}/{persuasion['total']} tactics")
    
    # Structure
    structure = report.get('structure', {})
    if structure.get('features'):
        archetypes = structure['features'][0].get('evidence', 'Unknown')
        print(f"\n🎨 Creative Structure: {archetypes}")
    
    # Scenes
    scenes = report.get('scenes', [])
    if scenes:
        print(f"\n🎞️  Scenes: {len(scenes)} detected")
        scenes_with_keyframes = sum(1 for s in scenes if s.get('keyframe'))
        print(f"   Keyframes extracted: {scenes_with_keyframes}/{len(scenes)}")
    
    print("\n" + "="*60)


def save_report_to_file(report: dict, output_path: str = "report.json"):
    """Save the full report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"💾 Full report saved to: {output_path}")


def extract_scene_keyframes(report: dict, output_dir: str = "keyframes"):
    """Extract and save keyframe images from the report."""
    import base64
    from pathlib import Path
    
    scenes = report.get('scenes', [])
    if not scenes:
        print("No scenes found in report")
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    saved_count = 0
    for scene in scenes:
        keyframe_b64 = scene.get('keyframe', '')
        if keyframe_b64:
            scene_num = scene.get('scene_number', 0)
            img_path = output_path / f"scene_{scene_num:03d}.jpg"
            
            # Decode and save
            img_data = base64.b64decode(keyframe_b64)
            with open(img_path, 'wb') as f:
                f.write(img_data)
            saved_count += 1
    
    print(f"🖼️  Saved {saved_count} keyframe images to: {output_dir}/")


# ===== USAGE EXAMPLES =====

def example_basic():
    """Basic usage example."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Video Evaluation")
    print("="*60 + "\n")
    
    # Evaluate a video file
    report = evaluate_video_file(
        video_path="path/to/your/video.mp4",
        api_url="http://localhost:8080",
    )
    
    # Display summary
    display_report_summary(report)
    
    # Save full report
    save_report_to_file(report, "my_report.json")


def example_with_options():
    """Example with custom evaluation options."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Custom Evaluation Options")
    print("="*60 + "\n")
    
    # Evaluate with Shorts features enabled
    report = evaluate_video_file(
        video_path="path/to/short_video.mp4",
        use_abcd=True,
        use_shorts=True,  # Enable Shorts evaluation
        use_ci=True,
    )
    
    display_report_summary(report)


def example_extract_data():
    """Example of extracting specific data from report."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Extract Specific Data")
    print("="*60 + "\n")
    
    report = evaluate_video_file("path/to/video.mp4")
    
    # Extract ABCD features that passed
    passed_features = [
        f['name'] for f in report['abcd']['features']
        if f['detected']
    ]
    print(f"\n✅ Passed ABCD Features ({len(passed_features)}):")
    for feature in passed_features:
        print(f"   • {feature}")
    
    # Extract failed features
    failed_features = [
        f['name'] for f in report['abcd']['features']
        if not f['detected']
    ]
    print(f"\n❌ Failed ABCD Features ({len(failed_features)}):")
    for feature in failed_features:
        print(f"   • {feature}")
    
    # Extract scenes with transcripts
    print(f"\n📝 Scene Transcripts:")
    for scene in report.get('scenes', []):
        if scene.get('transcript') and scene['transcript'] != '[No speech]':
            print(f"   Scene {scene['scene_number']}: \"{scene['transcript']}\"")
    
    # Save keyframes
    extract_scene_keyframes(report, "output_keyframes")


def example_curl():
    """Print equivalent curl command."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Using curl")
    print("="*60 + "\n")
    
    curl_cmd = """
# Upload and evaluate a video file using curl:

curl -X POST http://localhost:8080/api/evaluate_file \\
  -F "file=@path/to/video.mp4" \\
  -F "use_abcd=true" \\
  -F "use_shorts=false" \\
  -F "use_ci=true" \\
  > report.json

# Pretty print the report:
cat report.json | python -m json.tool
"""
    print(curl_cmd)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         ABCDs Detector - API Client Examples                ║
╚══════════════════════════════════════════════════════════════╝

This script demonstrates how to use the /api/evaluate_file endpoint.

NOTE: Update the video_path in each example before running!
""")
    
    # Uncomment the example you want to run:
    
    # example_basic()
    # example_with_options()
    # example_extract_data()
    example_curl()
    
    print("\n✨ Done!")
