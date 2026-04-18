"""Tests for gcp_api_services/gemini_api_service.py."""

import pytest
from gcp_api_services.gemini_api_service import GeminiAPIService


class TestResolveMimeType:
    """_resolve_video_mime_type must produce valid MIME types for all URI shapes."""

    # YouTube URLs
    @pytest.mark.parametrize("url", [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=abc123",
        "https://www.youtube.com/embed/abc123",
        "https://www.youtube.com/watch?v=abc&t=30s&list=PL123",
    ])
    def test_youtube_urls_resolve_to_mp4(self, url):
        assert GeminiAPIService._resolve_video_mime_type(url) == "video/mp4"

    @pytest.mark.parametrize("url", [
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtu.be/abc123?t=10",
    ])
    def test_youtu_be_urls_resolve_to_mp4(self, url):
        assert GeminiAPIService._resolve_video_mime_type(url) == "video/mp4"

    # GCS URIs
    def test_gcs_mp4(self):
        assert GeminiAPIService._resolve_video_mime_type("gs://bucket/video.mp4") == "video/mp4"

    def test_gcs_mov(self):
        assert GeminiAPIService._resolve_video_mime_type("gs://bucket/video.mov") == "video/quicktime"

    def test_gcs_webm(self):
        assert GeminiAPIService._resolve_video_mime_type("gs://bucket/video.webm") == "video/webm"

    def test_gcs_avi(self):
        assert GeminiAPIService._resolve_video_mime_type("gs://bucket/video.avi") == "video/x-msvideo"

    def test_gcs_mkv(self):
        assert GeminiAPIService._resolve_video_mime_type("gs://bucket/video.mkv") == "video/x-matroska"

    def test_query_string_stripped(self):
        uri = "gs://bucket/video.mp4?generation=123456"
        assert GeminiAPIService._resolve_video_mime_type(uri) == "video/mp4"

    def test_uppercase_extension(self):
        uri = "gs://bucket/video.MP4"
        assert GeminiAPIService._resolve_video_mime_type(uri) == "video/mp4"

    def test_unknown_extension_falls_back(self):
        uri = "gs://bucket/video.flv"
        assert GeminiAPIService._resolve_video_mime_type(uri) == "video/flv"

    # Regression: the old code produced invalid MIME for YouTube URLs
    def test_old_behavior_was_broken(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        old_mime = f"video/{url.rsplit('.', 1)[-1]}"
        # Old result contained slashes in the type → invalid
        assert "/" in old_mime.split("video/", 1)[1]
        # New result is clean
        new_mime = GeminiAPIService._resolve_video_mime_type(url)
        assert "/" not in new_mime.split("video/", 1)[1]
