# Keyframe Extraction Fix for YouTube Videos

## Problem
Scene keyframe images were not appearing in reports when evaluating YouTube videos. The keyframe extraction functionality only worked for GCS (Google Cloud Storage) videos.

## Root Cause
The `download_video_locally()` function in `scene_detector.py` was returning empty paths for non-GCS URIs, which meant:
1. YouTube videos were never downloaded locally
2. Keyframe extraction was skipped (no local video file)
3. Reports showed scenes without thumbnail images

## Solution
Enhanced `scene_detector.py` to support YouTube video downloads using `yt-dlp`:

### Changes Made

1. **Updated `download_video_locally()` function** (`scene_detector.py:98-159`)
   - Now handles both GCS URIs and YouTube URLs
   - Uses `yt-dlp` to download YouTube videos in MP4 format
   - Maintains backward compatibility with existing GCS downloads
   - Provides clear error messages if `yt-dlp` is not installed

2. **Added `yt-dlp` dependency** (`requirements.txt`)
   - Added `yt-dlp>=2026.2.4` to the project requirements

3. **Created test script** (`test_keyframe_extraction.py`)
   - Verifies YouTube download and keyframe extraction works end-to-end
   - Can be run with: `python test_keyframe_extraction.py`

## How It Works

### For GCS Videos (Existing Flow - Unchanged)
1. Video URI starts with `gs://`
2. Downloads from GCS using Cloud Storage API
3. Extracts keyframes with ffmpeg
4. Displays in scene cards

### For YouTube Videos (New Flow)
1. Video URL contains `youtube.com` or `youtu.be`
2. Downloads video using `yt-dlp` (best quality MP4)
3. Extracts keyframes with ffmpeg (same as GCS)
4. Displays in scene cards (same as GCS)

## Installation

Make sure `yt-dlp` is installed:

```bash
pip install yt-dlp
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

## Testing

Run the test script to verify everything works:

```bash
python test_keyframe_extraction.py
```

This will:
- Download a short YouTube video
- Extract keyframes from test scenes
- Verify the base64-encoded images are generated
- Clean up temporary files

## Example Output

With this fix, scene sections in reports now show:

```
┌─────────────────────────┐
│   [Keyframe Image]      │  ← Now appears for YouTube videos!
├─────────────────────────┤
│ SCENE 1 • 0:00 - 0:05   │
│ Description text...     │
│ "Transcript text..."    │
└─────────────────────────┘
```

## Technical Details

### Video Download Logic

```python
if video_uri.startswith("gs://"):
    # Download from GCS
    blob = gcs_api_service.get_blob(video_uri)
    blob.download_to_file(video_path)
elif "youtube.com" in video_uri or "youtu.be" in video_uri:
    # Download from YouTube
    subprocess.run([
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", video_path,
        video_uri
    ])
```

### Keyframe Extraction (Same for Both)

```python
ffmpeg -ss {timestamp} -i {video_path} -vframes 1 -q:v 2 \
  -vf "scale=640:360:force_original_aspect_ratio=decrease,\
       pad=640:360:(ow-iw)/2:(oh-ih)/2:black" \
  {output_frame.jpg}
```

## Files Modified

1. `scene_detector.py` - Enhanced video download to support YouTube
2. `requirements.txt` - Added yt-dlp dependency
3. `test_keyframe_extraction.py` - New test script (optional)

## Files NOT Modified

- `report_service.py` - Already displays keyframes correctly
- `static/index.html` - Already renders keyframes correctly
- `web_app.py` - Already passes keyframes through correctly

The display logic was already working; it just needed the keyframe data to be populated!

## Compatibility

- ✅ GCS videos - Still works as before
- ✅ YouTube videos - Now works with keyframes
- ✅ Reports - Both HTML and PDF show keyframes
- ✅ Web UI - Displays keyframes in scene cards

## Future Enhancements

Potential improvements for later:
- Cache downloaded YouTube videos to avoid re-downloading
- Support other video platforms (Vimeo, etc.)
- Parallel keyframe extraction for faster processing
- Adjustable keyframe quality/size settings
