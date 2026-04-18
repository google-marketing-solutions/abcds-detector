#!/usr/bin/env python3

from __future__ import annotations

"""Service for detecting scenes in videos using Gemini and extracting keyframes with ffmpeg."""

import base64
import logging
import os
import re
import subprocess
import sys
import tempfile

from configuration import Configuration
from gcp_api_services.gemini_api_service import get_gemini_api_service
from gcp_api_services import gcs_api_service
from models import LLMParameters, PromptConfig, SCENE_RESPONSE_SCHEMA, BRAND_INTELLIGENCE_RESPONSE_SCHEMA, METADATA_AND_SCENES_RESPONSE_SCHEMA, VIDEO_METADATA_RESPONSE_SCHEMA, CONCEPT_RESPONSE_SCHEMA

FLASH_MODEL = "gemini-2.5-flash"


def detect_scenes(config: Configuration, video_uri: str) -> list[dict]:
  """Send a video to Gemini and get back a list of detected scenes.

  Each scene has: scene_number, start_time, end_time, description, transcript.

  Args:
    config: Project configuration.
    video_uri: GCS URI or YouTube URL of the video.
  Returns:
    List of scene dicts from the LLM.
  """
  system_instructions = """
      You are a professional video editor and scene analyst. Your job is to watch a video
      and break it down into its distinct scenes or shots.

      A "scene" is a continuous segment of video that shares a single visual setting,
      camera angle, or narrative beat. A new scene starts when there is a clear visual
      transition: a cut, dissolve, wipe, significant camera movement to a new subject,
      or a major change in on-screen content.

      For each scene you must provide:
      - scene_number: sequential integer starting at 1
      - start_time: timestamp in "M:SS" or "H:MM:SS" format (e.g. "0:00", "0:15", "1:02")
      - end_time: timestamp in the same format
      - description: 1-2 sentence description of what is visually happening in this scene.
        Include key subjects, actions, text overlays, and dominant colors/mood.
      - transcript: the exact spoken words or narration heard during this scene.
        If there is no speech, write "[No speech]". Include only what is actually said,
        not descriptions of music or sound effects.

      Be thorough — capture every distinct scene, even short ones (1-2 seconds).
      Use precise timestamps based on what you observe.
  """

  prompt = """
      Analyze the provided video and identify every distinct scene or shot.
      Return a complete list of scenes in chronological order.
  """

  prompt_config = PromptConfig(
      prompt=prompt,
      system_instructions=system_instructions,
  )

  # Build LLM params with video modality
  llm_params = LLMParameters()
  llm_params.model_name = config.llm_params.model_name
  llm_params.location = config.llm_params.location
  llm_params.generation_config = {
      "max_output_tokens": config.llm_params.generation_config.get("max_output_tokens", 65535),
      "temperature": 0.5,  # Lower temp for more consistent scene boundaries
      "top_p": 0.95,
      "response_schema": SCENE_RESPONSE_SCHEMA,
  }
  llm_params.set_modality({"type": "video", "video_uri": video_uri})

  try:
    gemini_service = get_gemini_api_service(config)
    scenes = gemini_service.execute_gemini_with_genai(prompt_config, llm_params)
    if scenes and isinstance(scenes, list):
      logging.info("Detected %d scenes in %s", len(scenes), video_uri)
      return scenes
    logging.warning("Scene detection returned empty or invalid result for %s", video_uri)
    return []
  except Exception as ex:
    logging.error("Scene detection failed for %s: %s", video_uri, ex)
    return []


def transcode_to_720p(input_path: str) -> str:
  """Transcode a video to 720p using ffmpeg for faster upload/processing.

  Args:
    input_path: Local path to the source video.
  Returns:
    Path to the transcoded file, or the original path if transcoding fails.
  """
  ffmpeg = _find_ffmpeg()
  output_path = input_path.rsplit(".", 1)[0] + "_720p.mp4"
  try:
    result = subprocess.run(
        [
            ffmpeg, "-y",
            "-i", input_path,
            "-vf", "scale=-2:720",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output_path,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0 and os.path.exists(output_path):
      logging.info("Transcoded to 720p: %s -> %s", input_path, output_path)
      return output_path
    logging.warning("Transcode failed (rc=%d): %s", result.returncode, result.stderr[:200])
    return input_path
  except Exception as ex:
    logging.warning("Transcode to 720p failed, using original: %s", ex)
    return input_path


def extract_metadata_and_scenes(
    config: Configuration,
    video_uri: str,
) -> tuple[dict, list[dict]]:
  """Extract brand metadata and detect scenes in a single Gemini Flash call.

  Combines what were previously two separate LLM calls into one to reduce
  latency. Uses Flash model for speed.

  Args:
    config: Project configuration.
    video_uri: GCS URI or YouTube URL of the video.
  Returns:
    Tuple of (metadata_dict, scenes_list).
  """
  system_instructions = """
      You are an expert video analyst. You will perform TWO tasks on the provided video:

      TASK 1 — BRAND METADATA: Identify the brand being advertised and extract:
      - brand_name: The main brand name
      - brand_variations: Alternative names, abbreviations, or sub-brands
      - branded_products: Specific products shown or mentioned
      - branded_products_categories: Product categories
      - branded_call_to_actions: CTAs like "Shop now", "Visit site", etc.

      TASK 2 — SCENE DETECTION: Break the video into distinct scenes/shots.
      A "scene" is a continuous segment sharing a single visual setting or camera angle.
      For each scene provide: scene_number, start_time (M:SS), end_time (M:SS),
      description (1-2 sentences), and transcript (exact spoken words or "[No speech]").
      Be thorough — capture every scene, even short 1-2 second ones.

      TASK 3 — EMOTIONAL ANALYSIS: For each scene, also provide:
      - emotion: The single dominant emotion from this fixed list:
        excitement, trust, humor, fear, urgency, inspiration, nostalgia, curiosity, calm, sadness.
        Choose the one that best describes the overall emotional tone of the scene.
      - sentiment_score: A float from -1.0 (very negative) to 1.0 (very positive)
        representing the emotional valence of the scene. 0.0 is neutral.

      TASK 4 — AUDIO ANALYSIS: For each scene, also provide:
      - music_mood: The mood of any background music from this list:
        energetic, calm, dramatic, playful, tense, none.
        Use "none" if there is no music in the scene.
      - has_music: Boolean — true if background music is present in the scene.
      - speech_ratio: A float from 0.0 to 1.0 representing the proportion of the
        scene's duration that contains speech or narration. 1.0 means speech
        throughout, 0.0 means no speech at all.
  """

  prompt = """
      Analyze the provided video. Return a JSON object with two keys:
      1. "metadata" — brand information extracted from the video
      2. "scenes" — chronological list of every distinct scene
  """

  prompt_config = PromptConfig(
      prompt=prompt,
      system_instructions=system_instructions,
  )

  llm_params = LLMParameters()
  llm_params.model_name = FLASH_MODEL
  llm_params.location = config.llm_params.location
  llm_params.generation_config = {
      "max_output_tokens": 8192,
      "temperature": 0.5,
      "top_p": 0.95,
      "response_schema": METADATA_AND_SCENES_RESPONSE_SCHEMA,
  }
  llm_params.set_modality({"type": "video", "video_uri": video_uri})

  try:
    gemini_service = get_gemini_api_service(config)
    result = gemini_service.execute_gemini_with_genai(prompt_config, llm_params)
    if result and isinstance(result, dict):
      metadata = result.get("metadata", {})
      scenes = result.get("scenes", [])
      logging.info(
          "Combined extraction: brand=%s, %d scenes",
          metadata.get("brand_name", "?"), len(scenes),
      )
      return metadata, scenes
    logging.warning("Combined metadata+scenes returned empty for %s", video_uri)
    return {}, []
  except Exception as ex:
    logging.error("Combined metadata+scenes failed: %s", ex)
    return {}, []


def _parse_timestamp_seconds(ts: str) -> float:
  """Convert a timestamp string like '0:15' or '1:02:30' to seconds."""
  parts = ts.strip().split(":")
  parts = [float(p) for p in parts]
  if len(parts) == 3:
    return parts[0] * 3600 + parts[1] * 60 + parts[2]
  elif len(parts) == 2:
    return parts[0] * 60 + parts[1]
  return parts[0]


def download_video_locally(
    config: Configuration,
    video_uri: str,
) -> tuple[str, str]:
  """Download a GCS or YouTube video to a local temp directory.

  Args:
    config: Project configuration.
    video_uri: GCS URI or YouTube URL of the video.
  Returns:
    Tuple of (tmp_dir_path, video_file_path). Caller must clean up tmp_dir.
    Returns ("", "") if download fails.
  """
  tmp_dir = tempfile.mkdtemp(prefix="abcd_video_")
  video_path = os.path.join(tmp_dir, "source.mp4")

  # Handle GCS URIs
  if video_uri.startswith("gs://"):
    try:
      blob = gcs_api_service.gcs_api_service.get_blob(video_uri)
      if not blob:
        logging.error("Could not download video %s", video_uri)
        return ("", "")
      with open(video_path, "wb") as f:
        f.write(blob.download_as_string(client=None))
      return (tmp_dir, video_path)
    except Exception as ex:
      logging.error("Failed to download GCS video %s: %s", video_uri, ex)
      return ("", "")

  # Handle YouTube URLs
  if "youtube.com" in video_uri or "youtu.be" in video_uri:
    try:
      logging.info("Downloading YouTube video: %s", video_uri)
      # Use yt-dlp to download the video (try binary, fall back to python -m)
      import shutil
      yt_dlp_cmd = shutil.which("yt-dlp")
      if yt_dlp_cmd:
        cmd = [yt_dlp_cmd]
      else:
        cmd = [sys.executable, "-m", "yt_dlp"]
      cmd += [
          "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
          "--merge-output-format", "mp4",
          "-o", video_path,
          video_uri,
      ]
      result = subprocess.run(
          cmd,
          capture_output=True,
          text=True,
          timeout=300,
      )
      if result.returncode == 0 and os.path.exists(video_path):
        logging.info("Successfully downloaded YouTube video to %s", video_path)
        return (tmp_dir, video_path)
      else:
        logging.error("yt-dlp failed: %s", result.stderr)
        return ("", "")
    except FileNotFoundError:
      logging.error("yt-dlp not found. Install with: pip install yt-dlp")
      return ("", "")
    except Exception as ex:
      logging.error("Failed to download YouTube video %s: %s", video_uri, ex)
      return ("", "")

  logging.warning("Unsupported video URI format: %s", video_uri)
  return ("", "")


def cleanup_temp_dir(tmp_dir: str) -> None:
  """Remove a temporary directory and all its contents."""
  if not tmp_dir or not os.path.isdir(tmp_dir):
    return
  for f in os.listdir(tmp_dir):
    try:
      os.remove(os.path.join(tmp_dir, f))
    except OSError:
      pass
  try:
    os.rmdir(tmp_dir)
  except OSError:
    pass


def _find_ffmpeg() -> str:
  """Find ffmpeg binary in common locations."""
  import shutil
  # Try to find ffmpeg in PATH
  ffmpeg = shutil.which("ffmpeg")
  if ffmpeg:
    return ffmpeg
  # Try common installation paths
  common_paths = [
      "/opt/homebrew/bin/ffmpeg",  # Homebrew on Apple Silicon
      "/usr/local/bin/ffmpeg",      # Homebrew on Intel Mac / Linux
      "/usr/bin/ffmpeg",             # System install on Linux
  ]
  for path in common_paths:
    if os.path.exists(path):
      return path
  logging.warning("ffmpeg not found in PATH or common locations")
  return "ffmpeg"  # Fall back to hoping it's in PATH


def extract_keyframes(
    scenes: list[dict],
    video_path: str,
    ffmpeg_path: str | None = None,
) -> list[str]:
  """Extract a keyframe image for each scene using ffmpeg.

  Args:
    scenes: List of scene dicts with 'start_time' keys.
    video_path: Local path to the video file.
    ffmpeg_path: Optional path to ffmpeg binary. Auto-detected if not provided.
  Returns:
    List of base64-encoded JPEG strings, parallel to scenes list.
    Empty string for any scene where extraction fails.
  """
  if not scenes or not video_path:
    return [""] * max(len(scenes), 0)

  if not ffmpeg_path:
    ffmpeg_path = _find_ffmpeg()

  keyframes: list[str] = []
  tmp_dir = os.path.dirname(video_path)

  for i, scene in enumerate(scenes):
    frame_path = os.path.join(tmp_dir, f"scene_{i:03d}.jpg")
    ts = scene.get("start_time", "0:00")
    seconds = _parse_timestamp_seconds(ts)

    try:
      subprocess.run(
          [
              ffmpeg_path, "-y",
              "-ss", str(seconds),
              "-i", video_path,
              "-vframes", "1",
              "-q:v", "2",
              "-vf", "scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2:black",
              frame_path,
          ],
          capture_output=True,
          timeout=30,
      )
      if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
        with open(frame_path, "rb") as img:
          keyframes.append(base64.b64encode(img.read()).decode("ascii"))
      else:
        keyframes.append("")
    except Exception as ex:
      logging.warning("Failed to extract keyframe for scene %d: %s", i + 1, ex)
      keyframes.append("")

  return keyframes


def analyze_volume_levels(
    scenes: list[dict],
    video_path: str,
    ffmpeg_path: str | None = None,
) -> list[dict]:
  """Measure mean audio volume for each scene using ffmpeg volumedetect.

  Args:
    scenes: List of scene dicts with 'start_time' and 'end_time' keys.
    video_path: Local path to the video file.
    ffmpeg_path: Optional path to ffmpeg binary. Auto-detected if not provided.
  Returns:
    List of dicts with volume_db, volume_pct, volume_change_pct, volume_flag.
  """
  if not scenes or not video_path:
    return []

  if not ffmpeg_path:
    ffmpeg_path = _find_ffmpeg()

  volumes: list[dict] = []
  raw_pcts: list[float] = []

  for i, scene in enumerate(scenes):
    start_sec = _parse_timestamp_seconds(scene.get("start_time", "0:00"))
    end_sec = _parse_timestamp_seconds(scene.get("end_time", "0:01"))
    # Ensure at least a small window
    if end_sec <= start_sec:
      end_sec = start_sec + 0.5

    mean_db = -60.0  # default silence
    try:
      result = subprocess.run(
          [
              ffmpeg_path, "-y",
              "-ss", str(start_sec),
              "-to", str(end_sec),
              "-i", video_path,
              "-af", "volumedetect",
              "-f", "null", "-",
          ],
          capture_output=True,
          text=True,
          timeout=30,
      )
      # volumedetect output is on stderr
      match = re.search(r"mean_volume:\s*([\-\d.]+)\s*dB", result.stderr)
      if match:
        mean_db = float(match.group(1))
    except Exception as ex:
      logging.warning("Volume analysis failed for scene %d: %s", i + 1, ex)

    # Normalise dB to 0-100 scale (-60 dB = 0%, 0 dB = 100%)
    volume_pct = round(max(0.0, min(100.0, (mean_db + 60.0) / 60.0 * 100.0)), 1)
    raw_pcts.append(volume_pct)

    volumes.append({
        "volume_db": round(mean_db, 1),
        "volume_pct": volume_pct,
        "volume_change_pct": 0.0,
        "volume_flag": False,
    })

  # Compute inter-scene changes
  for i in range(1, len(volumes)):
    change = round(raw_pcts[i] - raw_pcts[i - 1], 1)
    volumes[i]["volume_change_pct"] = change
    if abs(change) > 10.0:
      volumes[i]["volume_flag"] = True

  return volumes


def extract_video_metadata(
    video_path: str,
    ffprobe_path: str | None = None,
) -> dict:
  """Extract technical metadata from a video file using ffprobe.

  Args:
    video_path: Local path to the video file.
    ffprobe_path: Optional path to ffprobe binary. Auto-detected if not provided.
  Returns:
    Dict with duration, resolution, aspect_ratio, frame_rate, file_size, codec.
    Empty dict on failure.
  """
  if not video_path or not os.path.exists(video_path):
    return {}

  if not ffprobe_path:
    import shutil
    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
      # Try alongside ffmpeg
      ffmpeg = _find_ffmpeg()
      candidate = ffmpeg.replace("ffmpeg", "ffprobe")
      if os.path.exists(candidate):
        ffprobe_path = candidate
      else:
        ffprobe_path = "ffprobe"

  try:
    result = subprocess.run(
        [
            ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
      logging.warning("ffprobe failed: %s", result.stderr)
      return {}

    import json
    probe = json.loads(result.stdout)

    # Find video stream
    video_stream = None
    for stream in probe.get("streams", []):
      if stream.get("codec_type") == "video":
        video_stream = stream
        break

    fmt = probe.get("format", {})

    # Duration
    duration_secs = float(fmt.get("duration", 0))
    mins = int(duration_secs // 60)
    secs = duration_secs % 60
    duration_str = f"{mins}:{secs:05.2f}" if mins > 0 else f"{secs:.2f}s"

    # File size
    file_size_bytes = int(fmt.get("size", 0)) or os.path.getsize(video_path)
    if file_size_bytes >= 1024 * 1024:
      file_size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"
    else:
      file_size_str = f"{file_size_bytes / 1024:.0f} KB"

    metadata = {
        "duration": duration_str,
        "duration_seconds": round(duration_secs, 2),
        "file_size": file_size_str,
        "file_size_bytes": file_size_bytes,
    }

    if video_stream:
      width = int(video_stream.get("width", 0))
      height = int(video_stream.get("height", 0))
      metadata["resolution"] = f"{width}x{height}" if width and height else "Unknown"

      # Aspect ratio
      dar = video_stream.get("display_aspect_ratio", "")
      if dar and dar != "0:1":
        metadata["aspect_ratio"] = dar
      elif width and height:
        from math import gcd
        g = gcd(width, height)
        metadata["aspect_ratio"] = f"{width // g}:{height // g}"
      else:
        metadata["aspect_ratio"] = "Unknown"

      # Frame rate
      r_frame = video_stream.get("r_frame_rate", "")
      if r_frame and "/" in r_frame:
        num, den = r_frame.split("/")
        fps = float(num) / float(den) if float(den) else 0
        metadata["frame_rate"] = f"{fps:.2f} fps"
      elif r_frame:
        metadata["frame_rate"] = f"{r_frame} fps"
      else:
        metadata["frame_rate"] = "Unknown"

      # Codec
      codec = video_stream.get("codec_name", "")
      codec_long = video_stream.get("codec_long_name", "")
      metadata["codec"] = codec_long if codec_long else codec if codec else "Unknown"

    return metadata

  except Exception as ex:
    logging.error("Video metadata extraction failed: %s", ex)
    return {}


def generate_brand_intelligence(
    config: Configuration,
    video_uri: str,
    brand_name: str = "",
) -> dict:
  """Generate a Brand Intelligence Brief by sending the video to Gemini.

  Gemini watches the video and combines what it observes with its knowledge
  of the brand to produce a comprehensive brand profile.

  Args:
    config: Project configuration.
    video_uri: GCS URI or YouTube URL of the video.
    brand_name: The brand name (already extracted earlier in the pipeline).
  Returns:
    Dict with brand intelligence fields, or empty dict on failure.
  """
  system_instructions = """
      You are a brand research analyst and creative strategist. Your task is
      to produce a fully populated Brand Intelligence Brief based on the
      provided video advertisement and everything you know about the brand.

      Watch the video carefully to extract brand signals — tone, messaging,
      products shown, calls to action, target audience cues, and creative
      approach. Then augment those observations with your broader knowledge
      of the brand to fill in every field with specificity. Vague or generic
      entries are not acceptable.

      If you truly cannot determine a value, write "Not available" rather
      than leaving it blank or guessing wildly.
  """

  brand_hint = f"The brand in this video is: {brand_name}." if brand_name else ""

  prompt = f"""
      {brand_hint}

      Watch the provided video and produce a Brand Intelligence Brief with
      the following fields. Be exhaustive and specific for every field.

      COMPANY OVERVIEW
      - company_name: Official company / brand name
      - website: Brand website URL
      - founders_leadership: Founders, key leaders, founding story
      - product_service: One sentence — what they sell
      - launched: Year and location
      - description: 3-4 sentences — what the brand is, what it does, differentiation
      - brand_positioning: Specific market position, competitive advantage
      - core_value_proposition: Single most compelling reason to buy, in the customer's voice
      - mission: Official or inferred brand mission
      - taglines: All known taglines / slogans / campaign lines separated by " / "
      - social_proof_overview: Ratings, reviews, customers served, press, awards

      TARGET AUDIENCE
      - target_audience_primary: Demographics + psychographics — age, gender, location, motivations
      - target_audience_secondary: Second audience segment
      - key_insight: The sharpest strategic truth about why this audience buys
      - secondary_insight: A second behavioral or emotional truth

      PRODUCTS & PRICING
      - products_pricing: List every product/SKU/tier with name, description, price, key specs

      BRAND TONE & VOICE
      - tone: 3-5 adjectives with explanation
      - voice: How the brand writes and speaks — vocabulary, energy, humor
      - what_it_is_not: 3-4 things this brand would never sound like

      SOCIAL PROOF & CREDIBILITY
      - credibility_signals: Every credibility signal — ratings, press, awards, certifications, partnerships

      PAID MEDIA CHANNELS (ranked by importance)
      - paid_media_channels: Each channel with why it matters and what format performs

      CREATIVE FORMATS IN USE
      - creative_formats: Every ad format / content type with why it works for them

      MESSAGING THEMES (in priority order)
      - messaging_themes: The 5-7 core messages ranked by strategic importance

      CURRENT OFFERS & CTA PATTERNS
      - offers_and_ctas: Every offer, promotion, guarantee, trial, or CTA with exact phrasing where known
  """

  prompt_config = PromptConfig(
      prompt=prompt,
      system_instructions=system_instructions,
  )

  llm_params = LLMParameters()
  llm_params.model_name = config.llm_params.model_name
  llm_params.location = config.llm_params.location
  llm_params.generation_config = {
      "max_output_tokens": config.llm_params.generation_config.get("max_output_tokens", 65535),
      "temperature": 0.7,
      "top_p": 0.95,
      "response_schema": BRAND_INTELLIGENCE_RESPONSE_SCHEMA,
  }
  llm_params.set_modality({"type": "video", "video_uri": video_uri})

  try:
    gemini_service = get_gemini_api_service(config)
    result = gemini_service.execute_gemini_with_genai(prompt_config, llm_params)
    if result and isinstance(result, dict):
      logging.info("Brand intelligence generated for %s", brand_name or video_uri)
      return result
    logging.warning("Brand intelligence returned empty for %s", video_uri)
    return {}
  except Exception as ex:
    logging.error("Brand intelligence generation failed: %s", ex)
    return {}


def analyze_audio_richness(
    scenes: list[dict],
    video_path: str,
    ffmpeg_path: str | None = None,
) -> dict:
  """Analyze audio richness: detect silence gaps using FFmpeg silencedetect.

  Args:
    scenes: List of scene dicts (with music_mood, has_music, speech_ratio).
    video_path: Local path to the video file.
    ffmpeg_path: Optional path to ffmpeg binary.
  Returns:
    Dict with congruence_score, total_silence_s, avg_speech_ratio,
    silence_gaps list, and summary string.
  """
  if not video_path or not os.path.exists(video_path):
    return {}

  if not ffmpeg_path:
    ffmpeg_path = _find_ffmpeg()

  # Detect silence gaps > 1.5s
  silence_gaps = []
  try:
    result = subprocess.run(
        [
            ffmpeg_path, "-y",
            "-i", video_path,
            "-af", "silencedetect=noise=-40dB:d=1.5",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Parse silencedetect output from stderr
    starts = re.findall(r"silence_start:\s*([\d.]+)", result.stderr)
    ends = re.findall(r"silence_end:\s*([\d.]+).*silence_duration:\s*([\d.]+)", result.stderr)
    for i, s_start in enumerate(starts):
      s_start_f = float(s_start)
      if i < len(ends):
        s_end_f = float(ends[i][0])
        s_dur_f = float(ends[i][1])
      else:
        s_end_f = s_start_f + 1.5
        s_dur_f = 1.5
      silence_gaps.append({
          "start": round(s_start_f, 2),
          "end": round(s_end_f, 2),
          "duration_s": round(s_dur_f, 2),
      })
  except Exception as ex:
    logging.warning("Silence detection failed: %s", ex)

  total_silence = round(sum(g["duration_s"] for g in silence_gaps), 2)

  # Compute avg speech ratio from scene data
  speech_ratios = [s.get("speech_ratio", 0.0) for s in scenes if isinstance(s.get("speech_ratio"), (int, float))]
  avg_speech = round(sum(speech_ratios) / len(speech_ratios), 2) if speech_ratios else 0.0

  # Compute audio-visual congruence heuristic:
  # High when music mood aligns with scene emotion, speech ratio is balanced
  congruence_points = 0
  congruence_total = 0
  mood_emotion_map = {
      "energetic": {"excitement", "humor", "urgency", "inspiration"},
      "calm": {"calm", "trust", "nostalgia"},
      "dramatic": {"fear", "urgency", "inspiration", "sadness"},
      "playful": {"humor", "curiosity", "excitement"},
      "tense": {"fear", "urgency"},
  }
  for s in scenes:
    mood = s.get("music_mood", "none")
    emo = s.get("emotion", "")
    if mood and mood != "none" and emo:
      congruence_total += 1
      if emo in mood_emotion_map.get(mood, set()):
        congruence_points += 1
    elif mood == "none":
      # No music — neutral
      congruence_total += 1
      congruence_points += 0.5

  congruence_score = round((congruence_points / congruence_total * 100) if congruence_total else 70, 1)

  # Build summary
  music_scenes = [s for s in scenes if s.get("has_music")]
  moods = list(set(s.get("music_mood", "") for s in music_scenes if s.get("music_mood", "none") != "none"))
  parts = []
  if music_scenes:
    mood_str = " and ".join(moods[:3]) if moods else "present"
    parts.append(f"Music is {mood_str} in {len(music_scenes)}/{len(scenes)} scenes.")
  else:
    parts.append("No background music detected.")
  if silence_gaps:
    parts.append(f"{len(silence_gaps)} silence gap{'s' if len(silence_gaps) != 1 else ''} detected ({total_silence:.1f}s total).")
  else:
    parts.append("No significant silence gaps.")
  parts.append(f"Average speech ratio: {avg_speech:.0%}.")

  return {
      "congruence_score": congruence_score,
      "total_silence_s": total_silence,
      "avg_speech_ratio": avg_speech,
      "silence_gaps": silence_gaps,
      "summary": " ".join(parts),
  }


def generate_creative_brief(
    config: Configuration,
    video_uri: str,
    brand_name: str = "",
) -> dict:
  """Generate a structured creative brief using Gemini.

  Produces a strategist-quality creative brief with one-line pitch,
  key message, emotional hook, narrative technique, USP, target emotion,
  messaging hierarchy, and creative territory.

  Args:
    config: Project configuration.
    video_uri: GCS URI or YouTube URL of the video.
    brand_name: The brand name for context.
  Returns:
    Dict with creative brief fields, or empty dict on failure.
  """
  system_instructions = """
      You are a senior creative strategist at a top advertising agency with
      20+ years of experience writing creative briefs for global brands.

      Your task is to watch a video advertisement and produce a structured
      creative brief that captures the strategic intent behind the ad.

      Be specific and insightful — a great brief is concise, precise, and
      reveals the strategic logic behind the creative choices. Avoid generic
      observations. Every field should demonstrate deep strategic thinking.

      Guidelines:
      - one_line_pitch: Maximum 15 words. Capture the ad's essence in a
        single punchy sentence a creative director would use in a review.
      - key_message: The core takeaway the viewer should remember.
      - emotional_hook: How the ad creates emotional engagement. Name the
        specific emotional mechanism (not just the emotion).
      - narrative_technique: The storytelling structure used (e.g., problem-
        solution, testimonial, day-in-the-life, before/after, metaphor,
        montage, etc.).
      - unique_selling_proposition: The specific competitive advantage or
        benefit being communicated. Be concrete.
      - target_emotion: The single primary emotion the ad is designed to
        evoke in the viewer.
      - creative_territory: The broader creative territory (e.g., humor,
        aspiration, fear, empathy, excitement, trust, nostalgia, etc.).
      - messaging_hierarchy:
        - primary: The #1 message the viewer should take away.
        - secondary: The supporting message that reinforces the primary.
        - proof_points: 2-4 specific evidence points from the ad that
          support the messages.
  """

  brand_hint = f"The brand in this video is: {brand_name}." if brand_name else ""

  prompt = f"""
      {brand_hint}

      Watch the provided video advertisement and produce a comprehensive
      creative brief. Be specific and strategically insightful.
  """

  prompt_config = PromptConfig(
      prompt=prompt,
      system_instructions=system_instructions,
  )

  llm_params = LLMParameters()
  llm_params.model_name = config.llm_params.model_name
  llm_params.location = config.llm_params.location
  llm_params.generation_config = {
      "max_output_tokens": 4096,
      "temperature": 0.7,
      "top_p": 0.95,
      "response_schema": CONCEPT_RESPONSE_SCHEMA,
  }
  llm_params.set_modality({"type": "video", "video_uri": video_uri})

  try:
    gemini_service = get_gemini_api_service(config)
    result = gemini_service.execute_gemini_with_genai(prompt_config, llm_params)
    if result and isinstance(result, dict):
      logging.info("Creative brief generated for %s", brand_name or video_uri)
      return result
    logging.warning("Creative brief returned empty for %s", video_uri)
    return {}
  except Exception as ex:
    logging.error("Creative brief generation failed: %s", ex)
    return {}
