"""Tests for report_service module."""

import pytest
from report_service import generate_comparison_report_html


class TestGenerateComparisonReportHtml:
  def _make_comparison_data(self):
    return {
        "comparison_id": "cmp-test-01",
        "timestamp": "2026-02-22T19:00:00",
        "comparison": {
            "variant_count": 2,
            "variants": [
                {
                    "index": 0,
                    "video_name": "Ad_Alpha.mp4",
                    "brand_name": "BrandA",
                    "abcd_score": 75,
                    "persuasion_density": 57,
                    "performance_score": 68,
                    "accessibility_score": 80,
                    "emotional_coherence": 72,
                    "report_id": "rpt-alpha",
                },
                {
                    "index": 1,
                    "video_name": "Ad_Beta.mp4",
                    "brand_name": "BrandA",
                    "abcd_score": 90,
                    "persuasion_density": 43,
                    "performance_score": 82,
                    "accessibility_score": 85,
                    "emotional_coherence": 88,
                    "report_id": "rpt-beta",
                },
            ],
            "deltas": [
                {
                    "vs": "Ad_Beta.mp4 vs Ad_Alpha.mp4",
                    "abcd_delta": 15.0,
                    "persuasion_delta": -14.0,
                    "performance_delta": 14.0,
                },
            ],
            "feature_diffs": [
                {
                    "feature_id": "attract_hook",
                    "feature_name": "Hook / Dynamic Start",
                    "results": [True, False],
                },
            ],
            "recommended_winner": {
                "index": 1,
                "video_name": "Ad_Beta.mp4",
                "justification": "Ad_Beta leads with higher performance and ABCD scores.",
            },
        },
        "variants": [],
        "errors": [],
    }

  def test_returns_html_string(self):
    html = generate_comparison_report_html(self._make_comparison_data())
    assert isinstance(html, str)
    assert html.startswith("<!DOCTYPE html>")

  def test_contains_variant_names(self):
    html = generate_comparison_report_html(self._make_comparison_data())
    assert "Ad_Alpha.mp4" in html
    assert "Ad_Beta.mp4" in html

  def test_contains_winner_banner(self):
    html = generate_comparison_report_html(self._make_comparison_data())
    assert "Recommended Winner" in html
    assert "Ad_Beta.mp4" in html

  def test_contains_scores(self):
    html = generate_comparison_report_html(self._make_comparison_data())
    assert "75%" in html  # Alpha ABCD
    assert "90%" in html  # Beta ABCD
    assert "68" in html   # Alpha performance
    assert "82" in html   # Beta performance

  def test_contains_deltas(self):
    html = generate_comparison_report_html(self._make_comparison_data())
    assert "Score Deltas" in html

  def test_contains_feature_diffs(self):
    html = generate_comparison_report_html(self._make_comparison_data())
    assert "Feature Differences" in html
    assert "Hook / Dynamic Start" in html

  def test_contains_report_links(self):
    html = generate_comparison_report_html(self._make_comparison_data())
    assert "/report/rpt-alpha" in html
    assert "/report/rpt-beta" in html

  def test_empty_comparison(self):
    data = {
        "comparison_id": "empty",
        "timestamp": "",
        "comparison": {
            "variant_count": 0,
            "variants": [],
            "deltas": [],
            "feature_diffs": [],
            "recommended_winner": {},
        },
        "variants": [],
        "errors": [],
    }
    html = generate_comparison_report_html(data)
    assert "<!DOCTYPE html>" in html
