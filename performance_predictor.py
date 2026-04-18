#!/usr/bin/env python3

"""Deterministic performance prediction engine.

Computes predicted CPA Risk, ROAS Tier, Creative Fatigue Risk,
and Funnel Strength from ABCD feature evaluations.

Model version: deterministic-rules.v1
Same inputs → same outputs. No LLM required.
"""

# Section score maximums
SECTION_MAXES = {
    "hook_attention": 15,
    "brand_visibility": 10,
    "social_proof_trust": 15,
    "product_clarity_benefits": 15,
    "funnel_alignment": 10,
    "cta": 10,
    "creative_diversity_readiness": 10,
    "measurement_compatibility": 10,
    "data_audience_leverage": 5,
}

SECTION_LABELS = {
    "hook_attention": "Hook & Attention",
    "brand_visibility": "Brand Visibility",
    "social_proof_trust": "Social Proof & Trust",
    "product_clarity_benefits": "Product Clarity",
    "funnel_alignment": "Funnel Alignment",
    "cta": "Call to Action",
    "creative_diversity_readiness": "Creative Diversity",
    "measurement_compatibility": "Measurement Readiness",
    "data_audience_leverage": "Audience Leverage",
}


def _section_score(features: list[dict], max_score: float) -> float:
  """Compute a section score from feature evaluations.

  Each detected feature contributes (confidence * max_score / n_features).
  """
  if not features:
    return 0.0
  per_feature = max_score / len(features)
  total = 0.0
  for f in features:
    if f.get("detected"):
      conf = f.get("confidence") or 0.5
      total += conf * per_feature
  return round(min(total, max_score), 2)


def _has_keyword_detected(
    features: list[dict],
    keywords: list[str],
    field: str = "name",
) -> bool:
  """True if any detected feature's field contains one of the keywords."""
  for f in features:
    if not f.get("detected"):
      continue
    text = (f.get(field, "") or "").lower()
    if any(k in text for k in keywords):
      return True
  return False


def _by_sub(features: list[dict], sub: str) -> list[dict]:
  """Filter features by sub_category (case-insensitive)."""
  return [
      f for f in features
      if str(f.get("sub_category", "")).upper() == sub.upper()
  ]


def compute_predictions(
    abcd_features: list[dict],
    persuasion_features: list[dict],
    structure_features: list[dict],
) -> dict:
  """Compute deterministic performance predictions.

  Args:
    abcd_features: Formatted ABCD feature dicts with detected/confidence/name/sub_category.
    persuasion_features: Formatted persuasion feature dicts.
    structure_features: Formatted structure feature dicts.

  Returns:
    Full prediction dict with overall_score, indices, labels, flags, drivers.
  """
  # --- Group ABCD features by sub_category ---
  attract = _by_sub(abcd_features, "ATTRACT")
  brand = _by_sub(abcd_features, "BRAND")
  connect = _by_sub(abcd_features, "CONNECT")
  direct = _by_sub(abcd_features, "DIRECT")

  # Split CONNECT into product vs people
  product_kw = ["product"]
  people_kw = ["people", "face", "person", "presence"]
  product_feats = [
      f for f in connect
      if any(k in f.get("name", "").lower() for k in product_kw)
  ]
  people_feats = [
      f for f in connect
      if any(k in f.get("name", "").lower() for k in people_kw)
  ]

  # --- Compute section scores ---
  scores = {
      "hook_attention": _section_score(attract, 15),
      "brand_visibility": _section_score(brand, 10),
      "social_proof_trust": _section_score(
          people_feats + persuasion_features, 15
      ),
      "product_clarity_benefits": _section_score(product_feats, 15),
      "funnel_alignment": _section_score(structure_features, 10),
      "cta": _section_score(direct, 10),
  }

  # Creative diversity: blend of structure variety + overall feature coverage
  all_abcd = abcd_features or []
  coverage = len([f for f in all_abcd if f.get("detected")]) / max(len(all_abcd), 1)
  scores["creative_diversity_readiness"] = round(
      min(
          _section_score(structure_features + persuasion_features, 10) * 0.6
          + coverage * 4.0,
          10,
      ),
      2,
  )

  # Measurement: proxy from CTA + trackable signals
  scores["measurement_compatibility"] = round(
      min(
          _section_score(direct, 7)
          + (3.0 if _has_keyword_detected(
              direct + all_abcd,
              ["url", "qr", "link", "code", "shop", "visit"],
              field="evidence",
          ) else 0.0),
          10,
      ),
      2,
  )

  # Audience leverage: proxy from brand signals
  scores["data_audience_leverage"] = round(
      min(_section_score(brand, 5), 5), 2
  )

  # --- Normalize to 0–1 ---
  norm = {
      k: round(scores[k] / SECTION_MAXES[k], 4)
      for k in scores
  }

  # --- Boolean flags ---
  flags = {
      "hook_within_3s": _has_keyword_detected(attract, ["dynamic start"]),
      "brand_mentions_3x": (
          len([f for f in brand if f.get("detected")]) >= 3
      ),
      "has_trackable_anchor": (
          _has_keyword_detected(
              direct + all_abcd,
              ["url", "qr", "link", "code", "shop", "offer"],
              field="evidence",
          )
          or _has_keyword_detected(
              direct,
              ["url", "qr", "link", "code", "shop", "offer"],
              field="rationale",
          )
      ),
      "has_testimonial_or_ugc": _has_keyword_detected(
          persuasion_features + people_feats,
          ["testimonial", "ugc", "user-generated", "review", "creator"],
      ),
      "product_demo_present": _has_keyword_detected(
          product_feats, ["product visuals"],
      ),
      "end_card_present": _has_keyword_detected(
          direct, ["text", "call to action"],
      ),
  }

  # ============================================================
  # A) Predicted CPA Risk — Conversion Readiness Index (CRI)
  # ============================================================
  cri = (
      0.22 * norm["hook_attention"]
      + 0.18 * norm["product_clarity_benefits"]
      + 0.18 * norm["cta"]
      + 0.14 * norm["social_proof_trust"]
      + 0.12 * norm["brand_visibility"]
      + 0.10 * norm["funnel_alignment"]
      + 0.06 * norm["measurement_compatibility"]
  )

  cri_penalty = 0.0
  if not flags["hook_within_3s"]:
    cri_penalty += 0.10
  if not flags["has_trackable_anchor"]:
    cri_penalty += 0.10
  if not flags["product_demo_present"]:
    cri_penalty += 0.07
  if not flags["has_testimonial_or_ugc"]:
    cri_penalty += 0.05

  cri_adj = max(0.0, min(1.0, cri - cri_penalty))
  cpa_risk = (
      "Low" if cri_adj >= 0.72
      else "Medium" if cri_adj >= 0.52
      else "High"
  )

  # ============================================================
  # B) Predicted ROAS Tier — Revenue Efficiency Index (REI)
  # ============================================================
  rei = (
      0.24 * norm["product_clarity_benefits"]
      + 0.18 * norm["social_proof_trust"]
      + 0.14 * norm["brand_visibility"]
      + 0.12 * norm["funnel_alignment"]
      + 0.12 * norm["hook_attention"]
      + 0.10 * norm["cta"]
      + 0.10 * norm["creative_diversity_readiness"]
  )

  rei_boost = 0.0
  if flags["has_trackable_anchor"]:
    rei_boost += 0.05
  if flags["brand_mentions_3x"]:
    rei_boost += 0.03
  if flags["end_card_present"]:
    rei_boost += 0.02

  rei_penalty = 0.0
  if norm["product_clarity_benefits"] < 0.45:
    rei_penalty += 0.07
  if norm["social_proof_trust"] < 0.40:
    rei_penalty += 0.05

  rei_adj = max(0.0, min(1.0, rei + rei_boost - rei_penalty))
  roas_tier = (
      "High" if rei_adj >= 0.70
      else "Moderate" if rei_adj >= 0.50
      else "Low"
  )

  # ============================================================
  # C) Creative Fatigue Risk — Refreshability Index (RFI)
  # ============================================================
  rfi = (
      0.55 * norm["creative_diversity_readiness"]
      + 0.25 * norm["hook_attention"]
      + 0.20 * norm["measurement_compatibility"]
  )

  fatigue_risk = (
      "Low" if rfi >= 0.70
      else "Medium" if rfi >= 0.50
      else "High"
  )

  # ============================================================
  # D) Expected Funnel Strength (TOF / MOF / BOF)
  # ============================================================
  story_proxy = (norm["funnel_alignment"] + norm["product_clarity_benefits"]) / 2

  tof = (
      0.35 * norm["hook_attention"]
      + 0.25 * norm["brand_visibility"]
      + 0.20 * norm["social_proof_trust"]
      + 0.20 * story_proxy
  )
  mof = (
      0.25 * norm["social_proof_trust"]
      + 0.25 * norm["product_clarity_benefits"]
      + 0.20 * norm["brand_visibility"]
      + 0.15 * norm["hook_attention"]
      + 0.15 * norm["cta"]
  )
  bof = (
      0.30 * norm["cta"]
      + 0.25 * norm["product_clarity_benefits"]
      + 0.20 * norm["social_proof_trust"]
      + 0.15 * norm["measurement_compatibility"]
      + 0.10 * norm["funnel_alignment"]
  )

  funnel_map = {"TOF": tof, "MOF": mof, "BOF": bof}
  sorted_funnel = sorted(funnel_map.items(), key=lambda x: x[1], reverse=True)
  winner = sorted_funnel[0][0]
  hybrid = None
  if (
      len(sorted_funnel) > 1
      and abs(sorted_funnel[0][1] - sorted_funnel[1][1]) < 0.05
  ):
    hybrid = f"{sorted_funnel[0][0]}/{sorted_funnel[1][0]}"

  funnel_label = hybrid or winner

  # ============================================================
  # Drivers (explainability)
  # ============================================================
  sorted_sections = sorted(norm.items(), key=lambda x: x[1], reverse=True)
  top_positive = [
      {"feature": SECTION_LABELS.get(k, k), "score": round(v, 2)}
      for k, v in sorted_sections[:3]
      if v > 0.5
  ]
  top_negative = [
      {"feature": SECTION_LABELS.get(k, k), "score": round(v, 2)}
      for k, v in sorted_sections
      if v < 0.5
  ][:3]

  adjustments = []
  if flags["has_trackable_anchor"]:
    adjustments.append({"type": "boost", "key": "has_trackable_anchor", "delta": 0.05})
  if flags["brand_mentions_3x"]:
    adjustments.append({"type": "boost", "key": "brand_mentions_3x", "delta": 0.03})
  if flags["end_card_present"]:
    adjustments.append({"type": "boost", "key": "end_card_present", "delta": 0.02})
  if not flags["hook_within_3s"]:
    adjustments.append({"type": "penalty", "key": "hook_within_3s", "delta": -0.10})
  if not flags["has_trackable_anchor"]:
    adjustments.append({"type": "penalty", "key": "has_trackable_anchor", "delta": -0.10})
  if not flags["product_demo_present"]:
    adjustments.append({"type": "penalty", "key": "product_demo_present", "delta": -0.07})
  if not flags["has_testimonial_or_ugc"]:
    adjustments.append({"type": "penalty", "key": "has_testimonial_or_ugc", "delta": -0.05})

  # --- Overall performance score (0–100) ---
  overall = round(sum(scores.values()), 1)

  return {
      "overall_score": overall,
      "section_scores": scores,
      "section_maxes": SECTION_MAXES,
      "normalized": norm,
      "model_version": "deterministic-rules.v1",
      "indices": {
          "conversion_readiness_index": round(cri_adj, 3),
          "revenue_efficiency_index": round(rei_adj, 3),
          "refreshability_index": round(rfi, 3),
          "funnel_strength": {
              "tof": round(tof, 3),
              "mof": round(mof, 3),
              "bof": round(bof, 3),
              "winner": winner,
              "hybrid": hybrid,
          },
      },
      "labels": {
          "predicted_cpa_risk": cpa_risk,
          "predicted_roas_tier": roas_tier,
          "creative_fatigue_risk": fatigue_risk,
          "expected_funnel_strength": funnel_label,
      },
      "flags": flags,
      "drivers": {
          "top_positive": top_positive,
          "top_negative": top_negative,
          "applied_adjustments": adjustments,
      },
  }
