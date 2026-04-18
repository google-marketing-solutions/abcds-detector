"""Tests for benchmarking module."""

import json
import pytest
from unittest import mock
from pathlib import Path

import benchmarking


class TestPercentileRank:
  def test_empty_list_returns_50(self):
    assert benchmarking._percentile_rank([], 50) == 50.0

  def test_value_at_bottom(self):
    vals = [10, 20, 30, 40, 50]
    assert benchmarking._percentile_rank(vals, 5) == 0.0

  def test_value_at_top(self):
    vals = [10, 20, 30, 40, 50]
    assert benchmarking._percentile_rank(vals, 60) == 100.0

  def test_value_in_middle(self):
    vals = [10, 20, 30, 40, 50]
    result = benchmarking._percentile_rank(vals, 30)
    assert 30 <= result <= 60

  def test_all_same_values(self):
    vals = [50, 50, 50, 50]
    result = benchmarking._percentile_rank(vals, 50)
    assert 0 <= result <= 100


class TestDistributionStats:
  def test_empty_returns_empty(self):
    assert benchmarking._distribution_stats([]) == {}

  def test_single_value(self):
    result = benchmarking._distribution_stats([75.0])
    assert result["p50"] == 75.0
    assert result["mean"] == 75.0

  def test_normal_distribution(self):
    vals = list(range(0, 101, 10))  # 0,10,20,...,100
    result = benchmarking._distribution_stats(vals)
    assert "p10" in result
    assert "p25" in result
    assert "p50" in result
    assert "p75" in result
    assert "p90" in result
    assert "mean" in result
    assert result["p50"] == 50.0
    assert result["mean"] == 50.0


class TestComputeBenchmarks:
  def test_no_history(self):
    """When no history exists, percentiles should default to 50."""
    with mock.patch.object(benchmarking, "_load_history", return_value=[]):
      result = benchmarking.compute_benchmarks(80, 60, 70)
    assert result["abcd_percentile"] == 50.0
    assert result["persuasion_percentile"] == 50.0
    assert result["performance_percentile"] == 50.0
    assert result["sample_size"] == 0

  def test_with_history(self):
    history = [
        {"abcd_score": s, "persuasion_density": s, "performance_score": s, "vertical": ""}
        for s in range(10, 100, 10)
    ]
    with mock.patch.object(benchmarking, "_load_history", return_value=history):
      result = benchmarking.compute_benchmarks(50, 50, 50)
    assert result["sample_size"] == len(history)
    assert 30 <= result["abcd_percentile"] <= 70
    assert "distribution" in result

  def test_vertical_filter(self):
    history = [
        {"abcd_score": 30, "persuasion_density": 30, "performance_score": 30, "vertical": "ecommerce"},
    ] * 15 + [
        {"abcd_score": 90, "persuasion_density": 90, "performance_score": 90, "vertical": "saas"},
    ] * 15
    with mock.patch.object(benchmarking, "_load_history", return_value=history):
      result = benchmarking.compute_benchmarks(80, 80, 80, vertical="ecommerce")
    # Within ecommerce subset (all 30), 80 should be 100th percentile
    assert result["abcd_percentile"] == 100.0


class TestLogEvaluation:
  def test_log_appends_entry(self, tmp_path):
    hist_file = tmp_path / "benchmark_history.json"
    hist_file.write_text("[]")
    with mock.patch.object(benchmarking, "HISTORY_FILE", hist_file):
      # Reset cache
      benchmarking._cache = None
      benchmarking._cache_ts = 0.0
      benchmarking.log_evaluation("rpt-1", 85, 60, 72)
    data = json.loads(hist_file.read_text())
    assert len(data) == 1
    assert data[0]["report_id"] == "rpt-1"
    assert data[0]["abcd_score"] == 85
