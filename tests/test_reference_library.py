"""Tests for reference_library module."""

import math
import pytest
from unittest import mock

from reference_library import (
    _cosine_similarity,
    _build_feature_vector,
    find_similar_ads,
)


class TestCosineSimilarity:
  def test_identical_vectors(self):
    v = [1.0, 2.0, 3.0]
    assert _cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-6)

  def test_orthogonal_vectors(self):
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert _cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)

  def test_opposite_vectors(self):
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert _cosine_similarity(a, b) == pytest.approx(-1.0, abs=1e-6)

  def test_zero_vector(self):
    assert _cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0

  def test_different_lengths(self):
    assert _cosine_similarity([1, 2], [1, 2, 3]) == 0.0

  def test_empty_vectors(self):
    assert _cosine_similarity([], []) == 0.0


class TestBuildFeatureVector:
  def test_extracts_normalized_scores(self):
    predictions = {
        "normalized": {
            "hook_attention": 0.8,
            "brand_visibility": 0.6,
            "social_proof_trust": 0.7,
            "product_clarity_benefits": 0.5,
            "funnel_alignment": 0.4,
            "cta": 0.9,
            "creative_diversity_readiness": 0.3,
            "measurement_compatibility": 0.2,
            "data_audience_leverage": 0.1,
        }
    }
    vec = _build_feature_vector(predictions)
    assert len(vec) == 9
    assert vec[0] == 0.8  # hook_attention
    assert vec[5] == 0.9  # cta

  def test_missing_keys_default_zero(self):
    vec = _build_feature_vector({"normalized": {}})
    assert all(v == 0.0 for v in vec)

  def test_empty_predictions(self):
    vec = _build_feature_vector({})
    assert len(vec) == 9
    assert all(v == 0.0 for v in vec)


class TestFindSimilarAds:
  def test_empty_library_returns_empty(self):
    with mock.patch("reference_library.load_library", return_value=[]):
      result = find_similar_ads({"normalized": {"hook_attention": 0.5}})
    assert result == []

  def test_returns_top_k(self):
    library = [
        {"name": f"Ad {i}", "feature_vector": [float(i) / 10] * 9, "vertical": ""}
        for i in range(1, 8)
    ]
    with mock.patch("reference_library.load_library", return_value=library):
      predictions = {"normalized": {
          "hook_attention": 0.7, "brand_visibility": 0.7,
          "social_proof_trust": 0.7, "product_clarity_benefits": 0.7,
          "funnel_alignment": 0.7, "cta": 0.7,
          "creative_diversity_readiness": 0.7,
          "measurement_compatibility": 0.7,
          "data_audience_leverage": 0.7,
      }}
      result = find_similar_ads(predictions, top_k=3)
    assert len(result) == 3
    assert all("similarity" in ad for ad in result)
    # Should be sorted by similarity descending
    assert result[0]["similarity"] >= result[1]["similarity"]

  def test_vertical_filter(self):
    library = [
        {"name": "Ecom Ad", "feature_vector": [0.5] * 9, "vertical": "ecommerce"},
        {"name": "SaaS Ad", "feature_vector": [0.5] * 9, "vertical": "saas"},
    ]
    with mock.patch("reference_library.load_library", return_value=library):
      predictions = {"normalized": {k: 0.5 for k in [
          "hook_attention", "brand_visibility", "social_proof_trust",
          "product_clarity_benefits", "funnel_alignment", "cta",
          "creative_diversity_readiness", "measurement_compatibility",
          "data_audience_leverage",
      ]}}
      result = find_similar_ads(predictions, vertical="ecommerce", top_k=5)
    assert len(result) >= 1
    # When filtering by ecommerce, the ecom ad should be in results
    names = [ad["name"] for ad in result]
    assert "Ecom Ad" in names

  def test_zero_vector_predictions_returns_empty(self):
    with mock.patch("reference_library.load_library", return_value=[
        {"name": "Ad", "feature_vector": [0.5] * 9, "vertical": ""},
    ]):
      result = find_similar_ads({"normalized": {}})
    assert result == []
