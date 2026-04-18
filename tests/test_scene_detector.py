"""Tests for scene_detector.py — pure-function and edge-case tests."""

import os
import tempfile

import pytest
from scene_detector import (
    _parse_timestamp_seconds,
    cleanup_temp_dir,
    extract_keyframes,
    extract_video_metadata,
)


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

class TestParseTimestamp:
    def test_mm_ss(self):
        assert _parse_timestamp_seconds("0:15") == 15.0

    def test_mm_ss_with_minutes(self):
        assert _parse_timestamp_seconds("1:30") == 90.0

    def test_hh_mm_ss(self):
        assert _parse_timestamp_seconds("1:02:30") == 3750.0

    def test_seconds_only(self):
        assert _parse_timestamp_seconds("45") == 45.0

    def test_fractional_seconds(self):
        assert _parse_timestamp_seconds("0:15.5") == 15.5

    def test_whitespace_stripped(self):
        assert _parse_timestamp_seconds("  0:10  ") == 10.0

    def test_zero(self):
        assert _parse_timestamp_seconds("0:00") == 0.0


# ---------------------------------------------------------------------------
# cleanup_temp_dir
# ---------------------------------------------------------------------------

class TestCleanupTempDir:
    def test_removes_files_and_dir(self):
        d = tempfile.mkdtemp(prefix="abcd_test_")
        # Create a file inside
        with open(os.path.join(d, "test.txt"), "w") as f:
            f.write("hello")
        cleanup_temp_dir(d)
        assert not os.path.exists(d)

    def test_empty_string_noop(self):
        cleanup_temp_dir("")  # should not raise

    def test_nonexistent_dir_noop(self):
        cleanup_temp_dir("/tmp/does_not_exist_abcd_test_xyz")


# ---------------------------------------------------------------------------
# extract_keyframes edge cases
# ---------------------------------------------------------------------------

class TestExtractKeyframes:
    def test_empty_scenes(self):
        result = extract_keyframes([], "/some/video.mp4")
        assert result == []

    def test_no_video_path(self):
        scenes = [{"scene_number": 1, "start_time": "0:00"}]
        result = extract_keyframes(scenes, "")
        assert result == [""]

    def test_none_video_path(self):
        scenes = [{"scene_number": 1, "start_time": "0:00"}]
        result = extract_keyframes(scenes, None)
        assert result == [""]


# ---------------------------------------------------------------------------
# extract_video_metadata edge cases
# ---------------------------------------------------------------------------

class TestExtractVideoMetadata:
    def test_empty_path(self):
        assert extract_video_metadata("") == {}

    def test_nonexistent_path(self):
        assert extract_video_metadata("/tmp/nope_abcd_xyz.mp4") == {}
