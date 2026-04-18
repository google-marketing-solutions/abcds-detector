"""Integration tests for A/B comparison API endpoints.

Uses FastAPI TestClient with mocked evaluation to test:
- POST /api/evaluate_compare
- GET /report/compare/{comparison_id}
"""

import pytest
from unittest import mock


class TestEvaluateCompareEndpoint:
  """Tests for POST /api/evaluate_compare."""

  def _mock_eval_result(self, name="test_video.mp4"):
    """Build a mock evaluation result dict."""
    return {
        "brand_name": "TestBrand",
        "video_uri": f"gs://bucket/{name}",
        "video_name": name,
        "abcd": {"score": 75, "result": "Might Improve", "passed": 6, "total": 8, "features": []},
        "persuasion": {"density": 57, "detected": 4, "total": 7, "features": []},
        "structure": {"features": []},
        "shorts": {"features": []},
        "scenes": [],
        "concept": {"name": "Test Concept", "description": "A test ad"},
        "predictions": {"overall_score": 68, "section_scores": {}, "section_maxes": {},
                        "normalized": {}, "flags": {}, "labels": {}, "drivers": {"top_positive": [], "top_negative": []}},
        "reference_ads": [],
        "brand_intelligence": {},
        "video_metadata": {"duration": "0:30", "aspect_ratio": "16:9"},
        "emotional_coherence": {"score": 80, "flagged_shifts": []},
        "audio_analysis": {},
        "action_plan": [],
        "feature_timeline": {"video_duration_s": 30, "scene_boundaries": [], "features": []},
        "accessibility": {"score": 75, "passed": 3, "total": 4, "features": [], "speech_rate_wpm": 150, "speech_rate_flag": "ok"},
        "platform_fit": {"youtube": {"score": 85, "tips": []}, "meta_feed": {"score": 70, "tips": []},
                         "meta_reels": {"score": 55, "tips": []}, "tiktok": {"score": 50, "tips": []},
                         "ctv": {"score": 90, "tips": []}},
        "benchmarks": {"abcd_percentile": 50, "persuasion_percentile": 50, "performance_percentile": 50,
                       "sample_size": 0, "vertical": "all", "distribution": {}},
    }

  def test_requires_auth(self, client):
    """Unauthenticated request should be rejected."""
    resp = client.post("/api/evaluate_compare", json={
        "video_uris": ["gs://a/v1.mp4", "gs://a/v2.mp4"],
    })
    assert resp.status_code in (401, 403, 422)

  def test_minimum_two_uris_required(self, client, auth_headers):
    """Should reject with < 2 URIs."""
    headers = auth_headers()
    resp = client.post(
        "/api/evaluate_compare",
        json={"video_uris": ["gs://a/v1.mp4"]},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "at least 2" in resp.json().get("error", "").lower()

  def test_max_five_uris(self, client, auth_headers):
    """Should reject with > 5 URIs."""
    headers = auth_headers()
    resp = client.post(
        "/api/evaluate_compare",
        json={"video_uris": [f"gs://a/v{i}.mp4" for i in range(6)]},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "5" in resp.json().get("error", "")

  def test_successful_comparison(self, client, auth_headers, db_session, create_user):
    """Full comparison flow with mocked evaluation."""
    # Create a user with enough credits
    user = create_user(email="compare@test.com", password="Testpass1",
                       email_verified=True, credits_balance=100000)
    # Auth as that user
    resp = client.post("/auth/login/email", json={
        "email": "compare@test.com", "password": "Testpass1",
    })
    assert resp.status_code == 200
    headers = {"Cookie": f"session_token={resp.cookies.get('session_token')}"}

    # Mock run_evaluation to return predetermined results
    with mock.patch("web_app.run_evaluation") as mock_eval:
      mock_eval.side_effect = [
          self._mock_eval_result("variant_a.mp4"),
          self._mock_eval_result("variant_b.mp4"),
      ]
      resp = client.post(
          "/api/evaluate_compare",
          json={
              "video_uris": ["gs://bucket/variant_a.mp4", "gs://bucket/variant_b.mp4"],
              "use_abcd": True,
              "use_ci": True,
          },
          headers=headers,
      )

    assert resp.status_code == 200
    data = resp.json()
    assert "comparison_id" in data
    assert "comparison" in data
    assert data["comparison"]["variant_count"] == 2
    assert "recommended_winner" in data["comparison"]
    # Variants stored individually
    assert len(data["variants"]) == 2


class TestComparisonReportEndpoint:
  """Tests for GET /report/compare/{comparison_id}."""

  def test_not_found(self, client):
    resp = client.get("/report/compare/nonexistent")
    assert resp.status_code == 404

  def test_serves_html_after_comparison(self, client, auth_headers, create_user):
    """After a comparison, the report endpoint should serve HTML."""
    user = create_user(email="rptcmp@test.com", password="Testpass1",
                       email_verified=True, credits_balance=100000)
    resp = client.post("/auth/login/email", json={
        "email": "rptcmp@test.com", "password": "Testpass1",
    })
    headers = {"Cookie": f"session_token={resp.cookies.get('session_token')}"}

    mock_result = {
        "brand_name": "B", "video_uri": "gs://b/v.mp4", "video_name": "v.mp4",
        "abcd": {"score": 80, "result": "Excellent", "passed": 8, "total": 8, "features": []},
        "persuasion": {"density": 50, "detected": 3, "total": 7, "features": []},
        "structure": {"features": []}, "shorts": {"features": []}, "scenes": [],
        "concept": {}, "predictions": {"overall_score": 70, "section_scores": {},
        "section_maxes": {}, "normalized": {}, "flags": {}, "labels": {},
        "drivers": {"top_positive": [], "top_negative": []}},
        "reference_ads": [], "brand_intelligence": {},
        "video_metadata": {"duration": "0:30", "aspect_ratio": "16:9"},
        "emotional_coherence": {"score": 85, "flagged_shifts": []},
        "audio_analysis": {}, "action_plan": [],
        "feature_timeline": {"video_duration_s": 30, "scene_boundaries": [], "features": []},
        "accessibility": {"score": 80, "passed": 3, "total": 4, "features": [],
                          "speech_rate_wpm": 140, "speech_rate_flag": "ok"},
        "platform_fit": {"youtube": {"score": 80, "tips": []}, "meta_feed": {"score": 70, "tips": []},
                         "meta_reels": {"score": 60, "tips": []}, "tiktok": {"score": 55, "tips": []},
                         "ctv": {"score": 85, "tips": []}},
        "benchmarks": {"abcd_percentile": 50, "persuasion_percentile": 50,
                       "performance_percentile": 50, "sample_size": 0,
                       "vertical": "all", "distribution": {}},
    }

    with mock.patch("web_app.run_evaluation", return_value=mock_result):
      cmp_resp = client.post(
          "/api/evaluate_compare",
          json={"video_uris": ["gs://b/v1.mp4", "gs://b/v2.mp4"]},
          headers=headers,
      )

    assert cmp_resp.status_code == 200
    cmp_id = cmp_resp.json()["comparison_id"]

    # Now fetch the comparison report
    rpt_resp = client.get(f"/report/compare/{cmp_id}")
    assert rpt_resp.status_code == 200
    assert "text/html" in rpt_resp.headers["content-type"]
    assert "A/B Variant Comparison" in rpt_resp.text
