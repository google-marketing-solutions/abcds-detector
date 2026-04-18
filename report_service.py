#!/usr/bin/env python3

"""Service for generating shareable HTML reports, PDFs, and Slack notifications."""

import io
import json
import logging
import urllib.error
import urllib.request
import datetime
from html import escape

from fpdf import FPDF


def _volume_chart_html(scenes: list[dict]) -> str:
  """Build an inline SVG bar chart showing volume levels per scene."""
  vol_scenes = [s for s in scenes if "volume_pct" in s]
  if not vol_scenes:
    return ""

  n = len(vol_scenes)
  chart_w = min(800, max(400, n * 56))
  chart_h = 180
  pad_l, pad_r, pad_t, pad_b = 44, 16, 12, 36
  plot_w = chart_w - pad_l - pad_r
  plot_h = chart_h - pad_t - pad_b
  bar_gap = 4
  bar_w = max(12, (plot_w - bar_gap * (n - 1)) // n) if n > 0 else 40

  avg_vol = sum(s["volume_pct"] for s in vol_scenes) / n if n else 0
  avg_y = pad_t + plot_h - (avg_vol / 100 * plot_h)

  svg_parts = [
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart_w}" height="{chart_h}"'
      f' style="font-family:Inter,-apple-system,sans-serif;background:#f8f9fa;border-radius:12px">', 
  ]

  # Y-axis labels
  for pct in (0, 25, 50, 75, 100):
    y = pad_t + plot_h - (pct / 100 * plot_h)
    svg_parts.append(
        f'<text x="{pad_l - 6}" y="{y + 4}" text-anchor="end"'
        f' fill="#aaa" font-size="10">{pct}%</text>'
    )
    svg_parts.append(
        f'<line x1="{pad_l}" y1="{y}" x2="{pad_l + plot_w}" y2="{y}"'
        f' stroke="#e5e7eb" stroke-width="0.5"/>'
    )

  # Bars
  for i, sc in enumerate(vol_scenes):
    pct = sc["volume_pct"]
    flag = sc.get("volume_flag", False)
    x = pad_l + i * (bar_w + bar_gap)
    h = max(2, pct / 100 * plot_h)
    y = pad_t + plot_h - h
    fill = "#f87171" if flag else "#0A6D86"
    stroke = ' stroke="#dc2626" stroke-width="2"' if flag else ""

    svg_parts.append(
        f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}"'
        f' rx="3" fill="{fill}" opacity="0.85"{stroke}/>'
    )
    # Value label on bar
    svg_parts.append(
        f'<text x="{x + bar_w / 2}" y="{y - 4}" text-anchor="middle"'
        f' fill="{"#dc2626" if flag else "#555"}" font-size="9"'
        f' font-weight="{"700" if flag else "400"}">{pct:.0f}%</text>'
    )
    # Scene number label
    svg_parts.append(
        f'<text x="{x + bar_w / 2}" y="{pad_t + plot_h + 16}" text-anchor="middle"'
        f' fill="#888" font-size="10">S{sc.get("scene_number", i + 1)}</text>'
    )
    # Flag marker
    if flag:
      change = sc.get("volume_change_pct", 0)
      arrow = "\u2191" if change > 0 else "\u2193"
      svg_parts.append(
          f'<text x="{x + bar_w / 2}" y="{pad_t + plot_h + 28}" text-anchor="middle"'
          f' fill="#dc2626" font-size="9" font-weight="700">{arrow}{abs(change):.0f}%</text>'
      )

  # Average line
  svg_parts.append(
      f'<line x1="{pad_l}" y1="{avg_y}" x2="{pad_l + plot_w}" y2="{avg_y}"'
      f' stroke="#d97706" stroke-width="1.5" stroke-dasharray="6,4"/>'
  )
  svg_parts.append(
      f'<text x="{pad_l + plot_w + 2}" y="{avg_y + 4}"'
      f' fill="#d97706" font-size="9">avg</text>'
  )

  svg_parts.append("</svg>")
  return "\n".join(svg_parts)


def _emotional_arc_chart_html(scenes: list[dict]) -> str:
  """Build an inline SVG line chart showing emotional arc (sentiment) per scene."""
  emo_scenes = [s for s in scenes if "sentiment_score" in s]
  if not emo_scenes:
    return ""

  n = len(emo_scenes)
  chart_w = min(800, max(400, n * 56))
  chart_h = 200
  pad_l, pad_r, pad_t, pad_b = 44, 16, 20, 44
  plot_w = chart_w - pad_l - pad_r
  plot_h = chart_h - pad_t - pad_b

  # Emotion -> color mapping
  emo_colors = {
      "excitement": "#f59e0b", "trust": "#0A6D86", "humor": "#a855f7",
      "fear": "#dc2626", "urgency": "#ea580c", "inspiration": "#16a34a",
      "nostalgia": "#8b5cf6", "curiosity": "#0ea5e9", "calm": "#6ee7b7",
      "sadness": "#6b7280",
  }

  def _y(val: float) -> float:
    """Map sentiment -1..1 to pixel y."""
    normalized = (val + 1.0) / 2.0  # 0..1
    return pad_t + plot_h - (normalized * plot_h)

  svg_parts = [
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart_w}" height="{chart_h}"'
      f' style="font-family:Inter,-apple-system,sans-serif;background:#f8f9fa;border-radius:12px">',
  ]

  # Y-axis labels
  for val, label in [(-1.0, "-1.0"), (-0.5, "-0.5"), (0.0, "0.0"), (0.5, "+0.5"), (1.0, "+1.0")]:
    y = _y(val)
    svg_parts.append(
        f'<text x="{pad_l - 6}" y="{y + 4}" text-anchor="end"'
        f' fill="#aaa" font-size="9">{label}</text>'
    )
    dash = ' stroke-dasharray="4,4"' if val == 0.0 else ""
    svg_parts.append(
        f'<line x1="{pad_l}" y1="{y}" x2="{pad_l + plot_w}" y2="{y}"'
        f' stroke="{"#999" if val == 0.0 else "#e5e7eb"}" stroke-width="0.5"{dash}/>'
    )

  # Compute x positions
  spacing = plot_w / max(n - 1, 1)
  points = []
  for i, sc in enumerate(emo_scenes):
    x = pad_l + i * spacing
    y = _y(sc.get("sentiment_score", 0.0))
    points.append((x, y, sc))

  # Draw area fill
  if len(points) >= 2:
    zero_y = _y(0.0)
    area_path = f'M{points[0][0]},{zero_y}'
    for x, y, _ in points:
      area_path += f' L{x},{y}'
    area_path += f' L{points[-1][0]},{zero_y} Z'
    svg_parts.append(
        f'<path d="{area_path}" fill="#0A6D86" opacity="0.08"/>'
    )

  # Draw line
  if len(points) >= 2:
    line_path = f'M{points[0][0]},{points[0][1]}'
    for x, y, _ in points[1:]:
      line_path += f' L{x},{y}'
    svg_parts.append(
        f'<path d="{line_path}" fill="none" stroke="#0A6D86" stroke-width="2.5"'
        f' stroke-linejoin="round" stroke-linecap="round"/>'
    )

  # Draw dots, labels, and emotion pills
  for i, (x, y, sc) in enumerate(points):
    emo = sc.get("emotion", "")
    sent = sc.get("sentiment_score", 0.0)
    color = emo_colors.get(emo, "#0A6D86")
    # Check for abrupt shift
    is_shift = False
    if i > 0:
      prev_sent = emo_scenes[i - 1].get("sentiment_score", 0.0)
      if abs(sent - prev_sent) > 0.5:
        is_shift = True

    dot_r = 6 if is_shift else 4
    stroke = f' stroke="#dc2626" stroke-width="2"' if is_shift else ""
    svg_parts.append(
        f'<circle cx="{x}" cy="{y}" r="{dot_r}" fill="{color}"{stroke}/>'
    )
    # Score label
    svg_parts.append(
        f'<text x="{x}" y="{y - 10}" text-anchor="middle"'
        f' fill="{"#dc2626" if is_shift else "#555"}" font-size="9"'
        f' font-weight="{"700" if is_shift else "400"}">{sent:+.1f}</text>'
    )
    # Emotion label below
    svg_parts.append(
        f'<text x="{x}" y="{pad_t + plot_h + 14}" text-anchor="middle"'
        f' fill="{color}" font-size="8" font-weight="600">{emo[:6]}</text>'
    )
    # Scene number
    svg_parts.append(
        f'<text x="{x}" y="{pad_t + plot_h + 26}" text-anchor="middle"'
        f' fill="#888" font-size="9">S{sc.get("scene_number", i + 1)}</text>'
    )

  svg_parts.append("</svg>")
  return "\n".join(svg_parts)


def _feature_timeline_chart_html(timeline: dict) -> str:
  """Build an inline SVG swimlane chart showing when features are active.

  X-axis = video duration with scene boundaries.
  Y-axis = feature names as rows.
  Colored bars indicate when each feature is active.
  """
  features = timeline.get("features", [])
  boundaries = timeline.get("scene_boundaries", [])
  duration = timeline.get("video_duration_s", 0)
  if not features or duration <= 0:
    return ""

  # Filter to features with at least one timestamp
  active_features = [f for f in features if f.get("timestamps")]
  if not active_features:
    return ""

  row_h = 28
  label_w = 160
  pad_l, pad_r, pad_t, pad_b = label_w + 12, 16, 30, 20
  plot_w = max(400, min(700, int(duration * 12)))
  chart_w = pad_l + plot_w + pad_r
  chart_h = pad_t + len(active_features) * row_h + pad_b

  sub_cat_colors = {
      "ATTRACT": "#f59e0b", "BRAND": "#0A6D86", "CONNECT": "#a855f7",
      "DIRECT": "#16a34a", "PERSUASION": "#ea580c", "STRUCTURE": "#831F80",
  }

  def _x(seconds: float) -> float:
    return pad_l + (seconds / duration) * plot_w

  svg = [
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart_w}" height="{chart_h}"'
      f' style="font-family:Inter,-apple-system,sans-serif;background:#f8f9fa;border-radius:12px">',
  ]

  # Scene boundary columns (alternating subtle background)
  for i, b in enumerate(boundaries):
    bx = _x(b["start_s"])
    bw = _x(b["end_s"]) - bx
    if i % 2 == 0:
      svg.append(
          f'<rect x="{bx}" y="{pad_t}" width="{bw}"'
          f' height="{len(active_features) * row_h}" fill="#e5e7eb" opacity="0.3"/>'
      )
    # Scene label at top
    svg.append(
        f'<text x="{bx + bw / 2}" y="{pad_t - 8}" text-anchor="middle"'
        f' fill="#888" font-size="9">S{b["scene_number"]}</text>'
    )
    # Boundary line
    svg.append(
        f'<line x1="{bx}" y1="{pad_t - 2}" x2="{bx}"'
        f' y2="{pad_t + len(active_features) * row_h}" stroke="#d1d5db" stroke-width="0.5"/>'
    )

  # Time axis labels at bottom
  step = max(5, int(duration / 10))
  for t in range(0, int(duration) + 1, step):
    x = _x(t)
    m, s = divmod(t, 60)
    svg.append(
        f'<text x="{x}" y="{pad_t + len(active_features) * row_h + 14}"'
        f' text-anchor="middle" fill="#aaa" font-size="8">{m}:{s:02d}</text>'
    )

  # Feature rows
  for row_i, feat in enumerate(active_features):
    y_top = pad_t + row_i * row_h
    y_mid = y_top + row_h / 2
    color = sub_cat_colors.get(feat.get("sub_category", ""), "#0A6D86")
    detected = feat.get("detected", False)
    icon = "\u2713" if detected else "\u2717"
    icon_color = "#16a34a" if detected else "#dc2626"

    # Row separator
    svg.append(
        f'<line x1="0" y1="{y_top}" x2="{chart_w}" y2="{y_top}"'
        f' stroke="#e5e7eb" stroke-width="0.5"/>'
    )
    # Feature label (truncated)
    name = feat.get("name", "")[:24]
    svg.append(
        f'<text x="14" y="{y_mid + 4}" fill="{icon_color}" font-size="11"'
        f' font-weight="600">{icon}</text>'
    )
    svg.append(
        f'<text x="28" y="{y_mid + 4}" fill="#333" font-size="10">{name}</text>'
    )

    # Timestamp bars
    for ts in feat.get("timestamps", []):
      bx = _x(ts["start_s"])
      bw = max(4, _x(ts["end_s"]) - bx)
      bar_y = y_top + 4
      bar_h = row_h - 8
      opacity = "0.8" if detected else "0.35"
      lbl = ts.get("label", "")
      title_attr = f' title="{lbl}"' if lbl else ""
      # Make timestamps clickable for video seeking
      svg.append(
          f'<rect x="{bx}" y="{bar_y}" width="{bw}" height="{bar_h}"'
          f' rx="4" fill="{color}" opacity="{opacity}"'
          f' class="ts-bar" data-start="{ts["start_s"]}"'
          f' style="cursor:pointer"{title_attr}/>'
      )
      # Tooltip label (if bar wide enough)
      if bw > 40:
        svg.append(
            f'<text x="{bx + 4}" y="{bar_y + bar_h / 2 + 3}"'
            f' fill="#fff" font-size="8" pointer-events="none">{lbl[:int(bw / 5)]}</text>'
        )

  svg.append("</svg>")
  return "\n".join(svg)


def _video_web_url(uri: str) -> str:
  """Convert a video URI to a clickable web URL.

  GCS URIs (gs://bucket/path) become https://storage.googleapis.com/bucket/path.
  YouTube and other HTTP(S) URLs are returned as-is.
  """
  if uri.startswith("gs://"):
    return "https://storage.googleapis.com/" + uri[len("gs://"):]
  return uri


def _sanitize_pdf_text(text: str) -> str:
  """Remove or replace characters that Helvetica/latin-1 cannot render."""
  cleaned = text.encode("latin-1", errors="replace").decode("latin-1")
  return cleaned.strip()


def _score_color(score: float) -> str:
  """Return a hex color for a given score percentage."""
  if score >= 80:
    return "#16a34a"
  elif score >= 65:
    return "#d97706"
  return "#dc2626"


def _score_label(score: float) -> str:
  if score >= 80:
    return "Excellent"
  elif score >= 65:
    return "Might Improve"
  return "Needs Review"


def _feature_rows_html(features: list[dict]) -> str:
  """Build HTML table rows for a list of feature dicts."""
  rows = []
  for f in features:
    icon = "&#10003;" if f["detected"] else "&#10007;"
    icon_color = "#16a34a" if f["detected"] else "#dc2626"
    conf = f"{f['confidence'] * 100:.0f}%" if f.get("confidence") else ""
    # Reliability badge (from calibration data, if available)
    reliability = f.get("reliability_level", "")
    rel_badge = ""
    if reliability and reliability != "unknown":
      rel_colors = {"high": "#16a34a", "medium": "#ca8a04", "low": "#dc2626"}
      rel_icons = {"high": "\u25cf", "medium": "\u25cf", "low": "\u25cf"}
      rc = rel_colors.get(reliability, "#888")
      rel_badge = f' <span style="color:{rc};font-size:9px" title="Reliability: {reliability}">{rel_icons.get(reliability, "")} {reliability}</span>'
    detail_parts = []
    for key in ("rationale", "evidence", "strengths", "weaknesses"):
      val = f.get(key, "")
      if val:
        detail_parts.append(
            f'<span style="color:#831F80;font-weight:600;font-size:11px;'
            f'text-transform:uppercase;letter-spacing:0.5px">{key}</span><br>'
            f'<span style="color:#555">{escape(val)}</span>'
        )
    # Structured timestamps
    ts_list = f.get("timestamps", [])
    if ts_list:
      ts_pills = "".join(
          f'<span class="ts-pill" data-start-ts="{escape(ts.get("start", ""))}"'
          f' style="display:inline-block;background:#e0f2f6;color:#0A6D86;'
          f'padding:2px 8px;border-radius:10px;font-size:10px;margin:2px 3px;cursor:pointer"'
          f' title="{escape(ts.get("label", ""))}">{escape(ts.get("start", ""))}\u2013{escape(ts.get("end", ""))}</span>'
          for ts in ts_list
      )
      detail_parts.append(
          f'<span style="color:#0A6D86;font-weight:600;font-size:11px;'
          f'text-transform:uppercase;letter-spacing:0.5px">timestamps</span><br>'
          + ts_pills
      )
    # Recommendation callout
    rec = f.get("recommendation", "")
    rec_pri = f.get("recommendation_priority", "")
    rec_html = ""
    if rec:
      pri_colors = {"high": "#dc2626", "medium": "#ca8a04", "low": "#0A6D86"}
      pri_c = pri_colors.get(rec_pri, "#888")
      pri_badge = f'<span style="color:{pri_c};font-weight:700;font-size:10px;text-transform:uppercase">{escape(rec_pri)}</span> ' if rec_pri else ''
      rec_html = (
          f'<div style="margin-top:8px;padding:8px 12px;background:#f0fdf4;border-left:3px solid {pri_c};'
          f'border-radius:4px;font-size:12px;color:#333">{pri_badge}{escape(rec)}</div>'
      )
    details_html = "<br>".join(detail_parts) if detail_parts else ""
    rows.append(f"""
      <tr>
        <td style="padding:10px 12px;border-bottom:1px solid #eee;color:{icon_color};
            font-size:16px;text-align:center;width:30px">{icon}</td>
        <td style="padding:10px 12px;border-bottom:1px solid #eee;font-weight:500">
          {escape(f['name'])}
          {f'<div style="margin-top:6px;font-size:12px;line-height:1.5;font-weight:400">{details_html}</div>' if details_html else ''}
          {rec_html}
        </td>
        <td style="padding:10px 12px;border-bottom:1px solid #eee;color:#888;
            text-align:right;width:80px">{conf}{rel_badge}</td>
      </tr>""")
  return "\n".join(rows)


def generate_report_html(data: dict, report_url: str = "") -> str:
  """Generate a self-contained, light-themed HTML report from evaluation data.

  Args:
    data: The formatted results dict (same shape as JSON API response, plus report_id/timestamp).
    report_url: The full permalink URL for this report (shown in header).
  Returns:
    Complete HTML string.
  """
  brand = escape(data.get("brand_name", "Unknown"))
  video = escape(data.get("video_name", ""))
  video_url = _video_web_url(data.get("video_uri", ""))
  timestamp = data.get("timestamp", datetime.datetime.now().isoformat(timespec="seconds"))
  report_id = data.get("report_id", "")

  # --- Video embed ---
  video_embed_html = ""
  raw_uri = data.get("video_uri", "")
  yt_id = ""
  if "youtube.com/watch" in raw_uri:
    from urllib.parse import urlparse, parse_qs
    yt_id = parse_qs(urlparse(raw_uri).query).get("v", [""])[0]
  elif "youtu.be/" in raw_uri:
    yt_id = raw_uri.split("youtu.be/")[1].split("?")[0].split("#")[0]
  if yt_id:
    video_embed_html = (
        f'<div style="position:relative;padding-bottom:56.25%;height:0;'
        f'border-radius:12px;overflow:hidden;margin-bottom:24px">'
        f'<iframe src="https://www.youtube.com/embed/{escape(yt_id)}" '
        f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:none" '
        f'allowfullscreen></iframe></div>'
    )
  elif raw_uri:
    video_src = f"/api/video/{report_id}" if report_id else escape(video_url)
    video_embed_html = (
        f'<video controls style="width:100%;border-radius:12px;background:#000;'
        f'max-height:480px;margin-bottom:24px" src="{video_src}"></video>'
    )

  # --- Score cards ---
  score_cards_html = ""
  benchmarks = data.get("benchmarks", {})
  bm_sample = benchmarks.get("sample_size", 0) if isinstance(benchmarks, dict) else 0

  def _percentile_badge(pct: float, sample: int) -> str:
    if sample < 5:
      return ""
    pct_r = round(pct)
    pc = "#16a34a" if pct_r >= 75 else "#ca8a04" if pct_r >= 50 else "#dc2626"
    return f'<div style="font-size:10px;color:{pc};margin-top:4px">{pct_r}th percentile (n={sample})</div>'

  predictions = data.get("predictions", {})
  if predictions.get("overall_score") is not None:
    perf_score = predictions["overall_score"]
    perf_color = _score_color(perf_score)
    perf_pct_badge = _percentile_badge(benchmarks.get("performance_percentile", 0), bm_sample) if isinstance(benchmarks, dict) else ""
    score_cards_html += f"""
      <div style="flex:1;min-width:200px;background:#f8f9fa;border-radius:12px;padding:24px;text-align:center">
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:6px">Performance Score</div>
        <div style="font-size:42px;font-weight:700;color:{perf_color}">{perf_score}</div>
        <div style="font-size:13px;color:#888">out of 100</div>
        {perf_pct_badge}
      </div>"""

  abcd = data.get("abcd", {})
  if abcd.get("total", 0) > 0:
    color = _score_color(abcd["score"])
    abcd_pct_badge = _percentile_badge(benchmarks.get("abcd_percentile", 0), bm_sample) if isinstance(benchmarks, dict) else ""
    score_cards_html += f"""
      <div style="flex:1;min-width:200px;background:#f8f9fa;border-radius:12px;padding:24px;text-align:center">
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:6px">ABCD Score</div>
        <div style="font-size:42px;font-weight:700;color:{color}">{abcd['score']}%</div>
        <div style="font-size:13px;color:#888">{abcd['passed']}/{abcd['total']} features &middot; {abcd['result']}</div>
        {abcd_pct_badge}
      </div>"""

  persuasion = data.get("persuasion", {})
  if persuasion.get("total", 0) > 0:
    p_color = _score_color(persuasion["density"])
    pers_pct_badge = _percentile_badge(benchmarks.get("persuasion_percentile", 0), bm_sample) if isinstance(benchmarks, dict) else ""
    score_cards_html += f"""
      <div style="flex:1;min-width:200px;background:#f8f9fa;border-radius:12px;padding:24px;text-align:center">
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:6px">Persuasion Density</div>
        <div style="font-size:42px;font-weight:700;color:{p_color}">{persuasion['density']}%</div>
        <div style="font-size:13px;color:#888">{persuasion['detected']}/{persuasion['total']} tactics</div>
        {pers_pct_badge}
      </div>"""

  emotional_coherence = data.get("emotional_coherence", {})
  ec_score = emotional_coherence.get("score") if isinstance(emotional_coherence, dict) else None
  if ec_score is not None:
    ec_color = _score_color(ec_score)
    score_cards_html += f"""
      <div style="flex:1;min-width:200px;background:#f8f9fa;border-radius:12px;padding:24px;text-align:center">
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:6px">Emotional Coherence</div>
        <div style="font-size:42px;font-weight:700;color:{ec_color}">{ec_score}</div>
        <div style="font-size:13px;color:#888">out of 100</div>
      </div>"""

  accessibility = data.get("accessibility", {})
  acc_score = accessibility.get("score") if isinstance(accessibility, dict) else None
  if acc_score is not None and accessibility.get("total", 0) > 0:
    acc_color = _score_color(acc_score)
    score_cards_html += f"""
      <div style="flex:1;min-width:200px;background:#f8f9fa;border-radius:12px;padding:24px;text-align:center">
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:6px">Accessibility</div>
        <div style="font-size:42px;font-weight:700;color:{acc_color}">{acc_score}%</div>
        <div style="font-size:13px;color:#888">{accessibility.get('passed', 0)}/{accessibility.get('total', 0)} checks passed</div>
      </div>"""

  score_cards_html += f"""
    <div style="flex:1;min-width:200px;background:#f8f9fa;border-radius:12px;padding:24px;text-align:center">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:6px">Brand</div>
      <div style="font-size:24px;font-weight:700;color:#0A6D86">{brand}</div>
      <div style="font-size:13px;color:#888"><a href="/api/video/{report_id}" download="{video}" style="color:#0A6D86;text-decoration:underline">download</a></div>
    </div>"""

  # --- Feature tables ---
  abcd_section = ""
  if abcd.get("features"):
    abcd_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        ABCD Feature Results</h2>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        {_feature_rows_html(abcd['features'])}
      </table>"""

  persuasion_section = ""
  if persuasion.get("features"):
    persuasion_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Persuasion Tactics</h2>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        {_feature_rows_html(persuasion['features'])}
      </table>"""

  structure_section = ""
  structure = data.get("structure", {})
  if structure.get("features"):
    s = structure["features"][0]
    archetypes = ", ".join(a.strip() for a in (s.get("evidence", "")).split(",") if a.strip())
    struct_details = ""
    for key in ("rationale", "strengths", "weaknesses"):
      val = s.get(key, "")
      if val:
        struct_details += (
            f'<p style="margin:6px 0"><span style="color:#831F80;font-weight:600;'
            f'font-size:11px;text-transform:uppercase;letter-spacing:0.5px">{key}</span>'
            f'<br><span style="color:#555">{escape(val)}</span></p>'
        )
    structure_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Creative Structure</h2>
      <div style="background:#f8f9fa;border-radius:12px;padding:20px">
        <div style="margin-bottom:8px">
          {''.join(f'<span style="display:inline-block;background:#e0f2f6;color:#0A6D86;padding:4px 14px;border-radius:20px;font-size:13px;margin:3px">{escape(a.strip())}</span>' for a in archetypes.split(',') if a.strip())}
        </div>
        {struct_details}
      </div>"""

  # --- Scenes timeline ---
  scenes_section = ""
  scenes = data.get("scenes", [])
  if scenes:
    scene_cards = ""
    for i, sc in enumerate(scenes):
      keyframe_img = ""
      if sc.get("keyframe"):
        keyframe_img = (
          f'<img src="data:image/jpeg;base64,{sc["keyframe"]}" '
          f'style="width:100%;aspect-ratio:16/9;border-radius:8px 8px 0 0;object-fit:contain;background:#000" '
          f'alt="Scene {sc.get("scene_number", i+1)} keyframe">'
        )
      ts = f"{sc.get('start_time', '?')} – {sc.get('end_time', '?')}"
      desc = escape(sc.get("description", ""))
      transcript = escape(sc.get("transcript", ""))
      emotion = sc.get("emotion", "")
      sentiment = sc.get("sentiment_score")
      emotion_pill = ""
      if emotion:
        emo_colors = {
            "excitement": "#f59e0b", "trust": "#0A6D86", "humor": "#a855f7",
            "fear": "#dc2626", "urgency": "#ea580c", "inspiration": "#16a34a",
            "nostalgia": "#8b5cf6", "curiosity": "#0ea5e9", "calm": "#6ee7b7",
            "sadness": "#6b7280",
        }
        emo_c = emo_colors.get(emotion, "#888")
        sent_str = f" ({sentiment:+.1f})" if sentiment is not None else ""
        emotion_pill = (
            f'<span style="display:inline-block;background:{emo_c}20;color:{emo_c};'
            f'padding:2px 10px;border-radius:12px;font-size:10px;font-weight:600;'
            f'margin-top:6px">{escape(emotion)}{sent_str}</span>'
        )
      # Music mood pill
      music_mood = sc.get("music_mood", "none")
      music_pill = ""
      if music_mood and music_mood != "none":
        mood_colors = {"energetic": "#f59e0b", "calm": "#6ee7b7", "dramatic": "#dc2626",
                       "playful": "#a855f7", "tense": "#ea580c"}
        mc = mood_colors.get(music_mood, "#888")
        music_pill = (
            f'<span style="display:inline-block;background:{mc}20;color:{mc};'
            f'padding:2px 10px;border-radius:12px;font-size:10px;font-weight:600;'
            f'margin-left:4px">&#9835; {escape(music_mood)}</span>'
        )
      scene_cards += f"""
        <div style="flex:1 1 260px;max-width:320px;background:#f8f9fa;border-radius:12px;overflow:hidden">
          {keyframe_img}
          <div style="padding:14px">
            <div style="font-size:11px;font-weight:700;color:#0A6D86;margin-bottom:6px">SCENE {sc.get('scene_number', i+1)} &middot; {ts}</div>
            <div style="font-size:13px;line-height:1.5;color:#333">{desc}</div>
            {emotion_pill}{music_pill}
            {f'<div style="margin-top:8px;font-size:12px;color:#888;font-style:italic">&ldquo;{transcript}&rdquo;</div>' if transcript else ''}
          </div>
        </div>"""
    scenes_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Scene Timeline</h2>
      <div style="display:flex;gap:16px;flex-wrap:wrap">
        {scene_cards}
      </div>"""

  # --- Performance Score detail ---
  performance_section = ""
  if predictions.get("overall_score") is not None:
    p_labels = predictions.get("labels", {})
    p_indices = predictions.get("indices", {})
    p_scores = predictions.get("section_scores", {})
    p_maxes = predictions.get("section_maxes", {})
    p_drivers = predictions.get("drivers", {})

    def _risk_color(val: str) -> str:
      if val == "Low":
        return "#16a34a"
      if val in ("Medium", "Moderate"):
        return "#ca8a04"
      return "#dc2626"

    funnel = p_indices.get("funnel_strength", {})
    pred_cards = f"""
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px">
        <div style="flex:1;min-width:140px;background:#f8f9fa;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">CPA Risk</div>
          <div style="font-size:22px;font-weight:700;color:{_risk_color(p_labels.get('predicted_cpa_risk', ''))}">{escape(p_labels.get('predicted_cpa_risk', '—'))}</div>
          <div style="font-size:11px;color:#aaa">CRI: {round((p_indices.get('conversion_readiness_index', 0)) * 100)}%</div>
        </div>
        <div style="flex:1;min-width:140px;background:#f8f9fa;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">ROAS Potential</div>
          <div style="font-size:22px;font-weight:700;color:{_risk_color(p_labels.get('predicted_roas_tier', ''))}">{escape(p_labels.get('predicted_roas_tier', '—'))}</div>
          <div style="font-size:11px;color:#aaa">REI: {round((p_indices.get('revenue_efficiency_index', 0)) * 100)}%</div>
        </div>
        <div style="flex:1;min-width:140px;background:#f8f9fa;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Fatigue Risk</div>
          <div style="font-size:22px;font-weight:700;color:{_risk_color(p_labels.get('creative_fatigue_risk', ''))}">{escape(p_labels.get('creative_fatigue_risk', '—'))}</div>
          <div style="font-size:11px;color:#aaa">RFI: {round((p_indices.get('refreshability_index', 0)) * 100)}%</div>
        </div>
        <div style="flex:1;min-width:140px;background:#f8f9fa;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Funnel Strength</div>
          <div style="font-size:22px;font-weight:700;color:#0A6D86">{escape(p_labels.get('expected_funnel_strength', '—'))}</div>
          <div style="font-size:11px;color:#aaa">TOF {round(funnel.get('tof', 0) * 100)} / MOF {round(funnel.get('mof', 0) * 100)} / BOF {round(funnel.get('bof', 0) * 100)}</div>
        </div>
      </div>"""

    section_labels = {
        "hook_attention": "Hook &amp; Attention",
        "brand_visibility": "Brand Visibility",
        "social_proof_trust": "Social Proof &amp; Trust",
        "product_clarity_benefits": "Product Clarity",
        "funnel_alignment": "Funnel Alignment",
        "cta": "Call to Action",
        "creative_diversity_readiness": "Creative Diversity",
        "measurement_compatibility": "Measurement Readiness",
        "data_audience_leverage": "Audience Leverage",
    }
    bars_html = ""
    for key, label in section_labels.items():
      score = p_scores.get(key, 0)
      mx = p_maxes.get(key, 1)
      pct = round(score / mx * 100) if mx else 0
      bar_color = "#16a34a" if pct >= 70 else "#ca8a04" if pct >= 50 else "#dc2626"
      bars_html += (
          f'<div style="display:flex;align-items:center;gap:10px;font-size:12px;margin-bottom:6px">'
          f'<span style="width:150px;color:#888;flex-shrink:0">{label}</span>'
          f'<div style="flex:1;height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden">'
          f'<div style="width:{pct}%;height:100%;background:{bar_color};border-radius:4px"></div></div>'
          f'<span style="width:55px;text-align:right;font-weight:600;font-size:12px">{score}/{mx}</span></div>'
      )

    drivers_html = ""
    pos = p_drivers.get("top_positive", [])
    neg = p_drivers.get("top_negative", [])
    if pos or neg:
      pos_spans = " &nbsp; ".join(
          f'<span style="color:#16a34a">+ {escape(d.get("feature", ""))}</span>' for d in pos
      )
      neg_spans = " &nbsp; ".join(
          f'<span style="color:#dc2626">- {escape(d.get("feature", ""))}</span>' for d in neg
      )
      drivers_html = f"""
        <div style="margin-top:14px;font-size:12px;color:#888">
          {f'<div style="margin-bottom:4px">{pos_spans}</div>' if pos_spans else ''}
          {f'<div>{neg_spans}</div>' if neg_spans else ''}
        </div>"""

    performance_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Performance Score</h2>
      {pred_cards}
      {bars_html}
      {drivers_html}"""

  # --- Creative Concept / Brief ---
  concept_section = ""
  concept = data.get("concept", {})
  has_brief = bool(concept.get("one_line_pitch"))
  if has_brief:
    # Structured creative brief
    pitch = escape(concept.get("one_line_pitch", ""))
    brief_fields = ""
    for lbl, key in [
        ("Key Message", "key_message"),
        ("Emotional Hook", "emotional_hook"),
        ("Narrative Technique", "narrative_technique"),
        ("Unique Selling Proposition", "unique_selling_proposition"),
        ("Target Emotion", "target_emotion"),
        ("Creative Territory", "creative_territory"),
    ]:
      val = concept.get(key, "")
      if val:
        brief_fields += (
            f'<div style="margin-bottom:10px">'
            f'<span style="color:#831F80;font-weight:600;font-size:11px;'
            f'text-transform:uppercase;letter-spacing:0.5px">{lbl}</span><br>'
            f'<span style="color:#333;font-size:13px;line-height:1.6">{escape(val)}</span></div>'
        )
    # Messaging hierarchy
    mh = concept.get("messaging_hierarchy", {})
    if isinstance(mh, dict) and (mh.get("primary") or mh.get("secondary")):
      proof_pts = mh.get("proof_points", [])
      proof_html = ""
      if proof_pts:
        proof_html = '<ul style="margin:4px 0 0 16px;padding:0;font-size:12px;color:#555">' + "".join(
            f"<li>{escape(p)}</li>" for p in proof_pts if p
        ) + "</ul>"
      brief_fields += (
          f'<div style="margin-top:14px;padding:12px 16px;background:#eef7f9;border-radius:8px">'
          f'<span style="color:#0A6D86;font-weight:600;font-size:11px;text-transform:uppercase;'
          f'letter-spacing:0.5px">Messaging Hierarchy</span>'
          f'<div style="margin-top:6px;font-size:13px;color:#333">'
          f'<strong>Primary:</strong> {escape(mh.get("primary", ""))}</div>'
          f'<div style="font-size:13px;color:#555"><strong>Secondary:</strong> {escape(mh.get("secondary", ""))}</div>'
          f'{proof_html}</div>'
      )
    concept_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Creative Brief</h2>
      <div style="background:#f8f9fa;border-radius:12px;padding:20px">
        <div style="font-size:20px;font-weight:700;color:#0A6D86;margin-bottom:16px;line-height:1.3">
          &ldquo;{pitch}&rdquo;</div>
        {brief_fields}
      </div>"""
  elif concept.get("name") or concept.get("description"):
    # Fallback: old-style name + description
    c_name = escape(concept.get("name", ""))
    c_desc = escape(concept.get("description", ""))
    concept_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Creative Concept</h2>
      <div style="background:#f8f9fa;border-radius:12px;padding:20px">
        {f'<div style="font-size:18px;font-weight:700;color:#0A6D86;margin-bottom:10px">{c_name}</div>' if c_name else ''}
        {f'<div style="font-size:13px;line-height:1.7;color:#555">{c_desc}</div>' if c_desc else ''}
      </div>"""

  # --- Executive Summary ---
  exec_summary_items = []
  if abcd.get("total", 0) > 0:
    label = _score_label(abcd["score"])
    exec_summary_items.append(
        f'ABCD Score of <strong>{abcd["score"]}%</strong> ({abcd["passed"]}/{abcd["total"]} features) — {label}.'
    )
  if persuasion.get("total", 0) > 0:
    exec_summary_items.append(
        f'Persuasion Density of <strong>{persuasion["density"]}%</strong> '
        f'with {persuasion["detected"]}/{persuasion["total"]} tactics detected.'
    )
  if structure.get("features"):
    archetypes_raw = structure["features"][0].get("evidence", "")
    if archetypes_raw:
      exec_summary_items.append(f'Creative structure identified as <strong>{escape(archetypes_raw)}</strong>.')
  if scenes:
    exec_summary_items.append(f'Video broken into <strong>{len(scenes)}</strong> scene{"s" if len(scenes) != 1 else ""}.')
    flagged_scenes = [s for s in scenes if s.get("volume_flag")]
    if flagged_scenes:
      exec_summary_items.append(
          f'<span style="color:#dc2626">&#9888; Volume jumps detected in '
          f'{len(flagged_scenes)} scene{"s" if len(flagged_scenes) != 1 else ""}.</span>'
      )
  # Emotional coherence in exec summary
  emotional_coherence = data.get("emotional_coherence", {})
  if isinstance(emotional_coherence, dict):
    ec_score = emotional_coherence.get("score")
    ec_shifts = emotional_coherence.get("flagged_shifts", [])
    if ec_score is not None:
      exec_summary_items.append(
          f'Emotional Coherence score of <strong>{ec_score}</strong>/100.'
      )
    if ec_shifts:
      shift_descs = ", ".join(
          f'Scene {s["from_scene"]}&rarr;{s["to_scene"]} ({s["from_emotion"]}&rarr;{s["to_emotion"]})'
          for s in ec_shifts[:3]
      )
      exec_summary_items.append(
          f'<span style="color:#dc2626">&#9888; Abrupt emotional shift{"s" if len(ec_shifts) != 1 else ""} '
          f'detected: {shift_descs}.</span>'
      )
  # Benchmark context in exec summary
  if isinstance(benchmarks, dict) and bm_sample >= 5:
    bm_parts = []
    for bm_label, bm_key in [("ABCD", "abcd_percentile"), ("Persuasion", "persuasion_percentile"), ("Performance", "performance_percentile")]:
      bm_val = benchmarks.get(bm_key)
      if bm_val is not None:
        bm_parts.append(f"{bm_label}: <strong>{round(bm_val)}th</strong>")
    if bm_parts:
      exec_summary_items.append(
          f'Percentile ranks (n={bm_sample}): {", ".join(bm_parts)}.'
      )
  # Accessibility in exec summary
  if isinstance(accessibility, dict) and accessibility.get("total", 0) > 0:
    acc_s = accessibility.get("score", 100)
    acc_passed = accessibility.get("passed", 0)
    acc_total = accessibility.get("total", 0)
    exec_summary_items.append(
        f'Accessibility score of <strong>{acc_s}%</strong> ({acc_passed}/{acc_total} checks passed).'
    )
    if acc_s < 60:
      failed_names = [f.get("name", "") for f in accessibility.get("features", []) if not f.get("detected")]
      if failed_names:
        exec_summary_items.append(
            f'<span style="color:#dc2626">&#9888; Accessibility issues: {escape(", ".join(failed_names))}.</span>'
        )
  # Audio analysis in exec summary
  audio_analysis = data.get("audio_analysis", {})
  if audio_analysis.get("summary"):
    exec_summary_items.append(f'Audio: {escape(audio_analysis["summary"])}')
    av_cong = audio_analysis.get("congruence_score")
    if av_cong is not None:
      exec_summary_items.append(f'Audio-Visual Congruence score of <strong>{av_cong}</strong>/100.')

  # --- Action Plan ---
  action_plan_section = ""
  action_plan = data.get("action_plan", [])
  if action_plan:
    ap_rows = ""
    pri_colors = {"high": "#dc2626", "medium": "#ca8a04", "low": "#0A6D86"}
    pri_icons = {"high": "\u26a0", "medium": "\u25cf", "low": "\u25cb"}
    for ap in action_plan:
      pri = ap.get("priority", "medium")
      pc = pri_colors.get(pri, "#888")
      icon = pri_icons.get(pri, "")
      det = ap.get("detected", False)
      label = "Optimize" if det else "Fix"
      ap_rows += (
          f'<div style="padding:10px 14px;border-bottom:1px solid #f0f0f0;display:flex;gap:12px;align-items:start">'
          f'<span style="color:{pc};font-size:14px;flex-shrink:0">{icon}</span>'
          f'<div style="flex:1">'
          f'<span style="font-weight:600;font-size:12px;color:#333">{escape(ap.get("feature_name", ""))}'
          f'</span> <span style="font-size:10px;color:{pc};font-weight:700;text-transform:uppercase">{escape(pri)} — {label}</span>'
          f'<div style="font-size:12px;color:#555;margin-top:4px;line-height:1.5">{escape(ap.get("recommendation", ""))}</div></div></div>'
      )
    action_plan_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Action Plan</h2>
      <div style="background:#f8f9fa;border-radius:12px;overflow:hidden">
        {ap_rows}
      </div>"""

  # --- Video filename tags ---
  raw_video_name = data.get("video_name", "")
  name_no_ext = raw_video_name.rsplit(".", 1)[0] if "." in raw_video_name else raw_video_name
  video_tags = [t.strip() for t in name_no_ext.split("_") if t.strip()]
  tags_html = ""
  if len(video_tags) > 1:
    tag_pills = "".join(
        f'<span style="display:inline-block;background:#e0f2f6;color:#0A6D86;'
        f'padding:3px 12px;border-radius:16px;font-size:11px;margin:3px">{escape(t)}</span>'
        for t in video_tags
    )
    tags_html = f'<div style="margin-bottom:12px">{tag_pills}</div>'

  exec_summary_section = ""
  if exec_summary_items or tags_html:
    bullets = "".join(f'<li style="margin-bottom:6px">{item}</li>' for item in exec_summary_items)
    exec_summary_section = f"""
      <div style="background:#eef7f9;border-left:4px solid #0A6D86;border-radius:8px;padding:20px 24px;margin-bottom:24px">
        <h2 style="font-size:15px;font-weight:700;color:#0A6D86;margin-bottom:10px">Executive Summary</h2>
        {tags_html}
        <ul style="list-style:none;padding:0;margin:0;font-size:13px;line-height:1.7;color:#333">
          {bullets}
        </ul>
      </div>"""

  # --- Brand Intelligence ---
  brand_intel_section = ""
  bi = data.get("brand_intelligence", {})
  if bi and bi.get("company_name"):
    def _bi_row(label: str, value: str) -> str:
      if not value or value == "Not available":
        return ""
      return (
          f'<tr><td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:600;'
          f'color:#831F80;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;'
          f'vertical-align:top;width:180px;white-space:nowrap">{escape(label)}</td>'
          f'<td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:13px;'
          f'line-height:1.6;color:#333">{escape(value)}</td></tr>'
      )

    def _bi_list_section(title: str, items: list) -> str:
      if not items:
        return ""
      bullets = "".join(
          f'<li style="margin-bottom:4px">{escape(item)}</li>' for item in items if item
      )
      if not bullets:
        return ""
      return (
          f'<h3 style="font-size:13px;font-weight:600;color:#0A6D86;margin:20px 0 8px">{escape(title)}</h3>'
          f'<ul style="padding-left:20px;font-size:13px;line-height:1.6;color:#333">{bullets}</ul>'
      )

    overview_rows = ""
    for lbl, key in [
        ("Company", "company_name"), ("Website", "website"),
        ("Founders / Leadership", "founders_leadership"),
        ("Product / Service", "product_service"), ("Launched", "launched"),
        ("Description", "description"), ("Brand Positioning", "brand_positioning"),
        ("Core Value Proposition", "core_value_proposition"),
        ("Mission", "mission"), ("Taglines", "taglines"),
        ("Social Proof", "social_proof_overview"),
    ]:
      overview_rows += _bi_row(lbl, bi.get(key, ""))

    audience_rows = ""
    for lbl, key in [
        ("Primary Audience", "target_audience_primary"),
        ("Secondary Audience", "target_audience_secondary"),
        ("Key Insight", "key_insight"),
        ("Secondary Insight", "secondary_insight"),
    ]:
      audience_rows += _bi_row(lbl, bi.get(key, ""))

    tone_rows = ""
    for lbl, key in [
        ("Tone", "tone"), ("Voice", "voice"), ("What It Is NOT", "what_it_is_not"),
    ]:
      tone_rows += _bi_row(lbl, bi.get(key, ""))

    brand_intel_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Brand Intelligence Brief</h2>

      <h3 style="font-size:13px;font-weight:600;color:#0A6D86;margin:16px 0 8px">Company Overview</h3>
      <table style="width:100%;border-collapse:collapse">{overview_rows}</table>

      <h3 style="font-size:13px;font-weight:600;color:#0A6D86;margin:20px 0 8px">Target Audience</h3>
      <table style="width:100%;border-collapse:collapse">{audience_rows}</table>

      {_bi_list_section("Products &amp; Pricing", bi.get("products_pricing", []))}

      <h3 style="font-size:13px;font-weight:600;color:#0A6D86;margin:20px 0 8px">Brand Tone &amp; Voice</h3>
      <table style="width:100%;border-collapse:collapse">{tone_rows}</table>

      {_bi_list_section("Social Proof &amp; Credibility", bi.get("credibility_signals", []))}
      {_bi_list_section("Paid Media Channels", bi.get("paid_media_channels", []))}
      {_bi_list_section("Creative Formats", bi.get("creative_formats", []))}
      {_bi_list_section("Messaging Themes", bi.get("messaging_themes", []))}
      {_bi_list_section("Offers &amp; CTA Patterns", bi.get("offers_and_ctas", []))}
    """

  # --- Creative Metadata ---
  metadata_section = ""
  vm = data.get("video_metadata", {})
  if vm:
    meta_items = [
        ("Duration", vm.get("duration", "")),
        ("Resolution", vm.get("resolution", "")),
        ("Aspect Ratio", vm.get("aspect_ratio", "")),
        ("Frame Rate", vm.get("frame_rate", "")),
        ("File Size", vm.get("file_size", "")),
        ("Codec", vm.get("codec", "")),
    ]
    meta_items = [(l, v) for l, v in meta_items if v and v != "Unknown"]
    if meta_items:
      meta_cards = "".join(
          f'<div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center">'
          f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:4px">{l}</div>'
          f'<div style="font-size:15px;font-weight:600;color:#021A20">{escape(v)}</div></div>'
          for l, v in meta_items
      )
      metadata_section = f"""
        <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
          Creative Metadata</h2>
        <div style="display:flex;gap:12px;flex-wrap:wrap">{meta_cards}</div>"""

  # --- Emotional Arc chart ---
  emotional_arc_section = ""
  if scenes and any(s.get("sentiment_score") is not None for s in scenes):
    emo_chart_svg = _emotional_arc_chart_html(scenes)
    if emo_chart_svg:
      ec_data = data.get("emotional_coherence", {})
      ec_note = ""
      if isinstance(ec_data, dict) and ec_data.get("flagged_shifts"):
        shifts = ec_data["flagged_shifts"]
        ec_note = (
            '<div style="margin-top:12px;padding:10px 14px;background:#fef2f2;'
            'border:1px solid #fecaca;border-radius:8px;font-size:12px;color:#b91c1c">'
            f'<strong>\u26a0 Abrupt emotional shift{"s" if len(shifts) != 1 else ""}</strong>: '
            + ", ".join(
                f'Scene {s["from_scene"]}\u2192{s["to_scene"]} '
                f'({s["from_emotion"]}\u2192{s["to_emotion"]}, \u0394{s["delta"]:.1f})'
                for s in shifts
            )
            + "</div>"
        )
      emotional_arc_section = f"""
        <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
          Emotional Arc</h2>
        <div style="overflow-x:auto">{emo_chart_svg}</div>
        {ec_note}"""

  # --- Audio Analysis (volume levels + richness) ---
  volume_section = ""
  if scenes and any(s.get("volume_pct") is not None for s in scenes):
    chart_svg = _volume_chart_html(scenes)
    flagged = [s for s in scenes if s.get("volume_flag")]
    flag_note = ""
    if flagged:
      flag_note = (
          '<div style="margin-top:12px;padding:10px 14px;background:#fef2f2;'
          'border:1px solid #fecaca;border-radius:8px;font-size:12px;color:#b91c1c">'
          f'<strong>\u26a0 Volume jump detected</strong> in '
          f'{len(flagged)} scene{"s" if len(flagged) != 1 else ""}: '
          + ", ".join(
              f'Scene {s.get("scene_number", "?")} ({s.get("volume_change_pct", 0):+.0f}%)'
              for s in flagged
          )
          + "</div>"
      )
    # Audio richness summary cards
    aa = data.get("audio_analysis", {})
    audio_cards = ""
    if aa:
      cong = aa.get("congruence_score", 0)
      cong_c = _score_color(cong)
      total_sil = aa.get("total_silence_s", 0)
      avg_sp = aa.get("avg_speech_ratio", 0)
      sil_gaps = aa.get("silence_gaps", [])
      audio_cards = f"""
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px">
          <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:4px">A/V Congruence</div>
            <div style="font-size:22px;font-weight:700;color:{cong_c}">{cong}/100</div></div>
          <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:4px">Silence Gaps</div>
            <div style="font-size:22px;font-weight:700;color:{"#dc2626" if sil_gaps else "#16a34a"}">{len(sil_gaps)}</div>
            <div style="font-size:10px;color:#aaa">{total_sil:.1f}s total</div></div>
          <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:4px">Avg Speech</div>
            <div style="font-size:22px;font-weight:700;color:#0A6D86">{avg_sp:.0%}</div></div>
        </div>"""
      if sil_gaps:
        gap_pills = "".join(
            f'<span style="display:inline-block;background:#fef2f2;color:#b91c1c;'
            f'padding:3px 10px;border-radius:12px;font-size:11px;margin:3px">'
            f'{g["start"]:.1f}s\u2013{g["end"]:.1f}s ({g["duration_s"]:.1f}s)</span>'
            for g in sil_gaps[:8]
        )
        audio_cards += f'<div style="margin-bottom:12px"><span style="font-size:11px;color:#888;text-transform:uppercase">Silence gaps:</span> {gap_pills}</div>'
    volume_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Audio Analysis</h2>
      {audio_cards}
      <div style="overflow-x:auto">{chart_svg}</div>
      {flag_note}"""

  # --- Reference Ads ---
  reference_ads_section = ""
  ref_ads = data.get("reference_ads", [])
  if ref_ads:
    ref_cards = ""
    for ra in ref_ads[:3]:
      yt_url = escape(ra.get("youtube_url", ""))
      ref_cards += (
          f'<div style="flex:1;min-width:240px;background:#f8f9fa;border-radius:12px;padding:16px">'
          f'<div style="font-size:14px;font-weight:700;color:#0A6D86;margin-bottom:4px">'
          f'<a href="{yt_url}" target="_blank" style="color:#0A6D86;text-decoration:none">{escape(ra.get("name", ""))}</a></div>'
          f'<div style="font-size:12px;color:#888;margin-bottom:8px">{escape(ra.get("brand", ""))} &middot; {escape(ra.get("vertical", ""))}'
          f' &middot; {escape(ra.get("structure_archetype", ""))}</div>'
          f'<div style="font-size:12px;color:#555;line-height:1.5;margin-bottom:8px">{escape(ra.get("why_effective", ""))}</div>'
          f'<div style="display:flex;gap:8px;font-size:11px">'
          f'<span style="background:#e0f2f6;color:#0A6D86;padding:2px 8px;border-radius:8px">ABCD {ra.get("abcd_score", 0)}%</span>'
          f'<span style="background:#f0fdf4;color:#16a34a;padding:2px 8px;border-radius:8px">Perf {ra.get("performance_score", 0)}</span>'
          f'<span style="background:#fef3c7;color:#ca8a04;padding:2px 8px;border-radius:8px">Sim {ra.get("similarity", 0):.0%}</span></div></div>'
      )
    reference_ads_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Reference Ads</h2>
      <p style="font-size:12px;color:#888;margin-bottom:12px">Top-performing ads with similar creative profiles</p>
      <div style="display:flex;gap:16px;flex-wrap:wrap">{ref_cards}</div>"""

  # --- Accessibility ---
  accessibility_section = ""
  if isinstance(accessibility, dict) and accessibility.get("total", 0) > 0:
    acc_feats = accessibility.get("features", [])
    acc_sc = accessibility.get("score", 100)
    acc_p = accessibility.get("passed", 0)
    acc_t = accessibility.get("total", 0)
    wpm = accessibility.get("speech_rate_wpm", 0)
    wpm_flag = accessibility.get("speech_rate_flag", "no_speech")
    acc_sc_color = _score_color(acc_sc)

    acc_feature_rows = ""
    for af in acc_feats:
      af_icon = "&#10003;" if af.get("detected") else "&#10007;"
      af_icon_c = "#16a34a" if af.get("detected") else "#dc2626"
      af_conf = f"{af.get('confidence', 0) * 100:.0f}%" if af.get("confidence") else ""
      af_name = escape(af.get("name", ""))
      af_rationale = escape(af.get("rationale", ""))
      af_evidence = escape(af.get("evidence", ""))
      af_remediation = escape(af.get("remediation", ""))
      detail_parts = []
      if af_rationale:
        detail_parts.append(
            f'<span style="color:#831F80;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.5px">rationale</span><br>'
            f'<span style="color:#555">{af_rationale}</span>'
        )
      if af_evidence:
        detail_parts.append(
            f'<span style="color:#831F80;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.5px">evidence</span><br>'
            f'<span style="color:#555">{af_evidence}</span>'
        )
      remediation_html = ""
      if af_remediation and not af.get("detected"):
        remediation_html = (
            f'<div style="margin-top:8px;padding:8px 12px;background:#fef3c7;border-left:3px solid #ca8a04;'
            f'border-radius:4px;font-size:12px;color:#333">'
            f'<span style="color:#ca8a04;font-weight:700;font-size:10px;text-transform:uppercase">FIX</span> {af_remediation}</div>'
        )
      details_html = "<br>".join(detail_parts) if detail_parts else ""
      acc_feature_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;color:{af_icon_c};font-size:16px;text-align:center;width:30px">{af_icon}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;font-weight:500">
            {af_name}
            {f'<div style="margin-top:6px;font-size:12px;line-height:1.5;font-weight:400">{details_html}</div>' if details_html else ''}
            {remediation_html}
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;color:#888;text-align:right;width:80px">{af_conf}</td>
        </tr>"""

    wpm_html = ""
    if wpm > 0:
      wpm_color = "#dc2626" if wpm_flag == "too_fast" else "#ca8a04" if wpm_flag == "too_slow" else "#16a34a"
      wpm_label = "Too fast" if wpm_flag == "too_fast" else "Too slow" if wpm_flag == "too_slow" else "OK"
      wpm_html = f"""
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px">
          <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:4px">Score</div>
            <div style="font-size:22px;font-weight:700;color:{acc_sc_color}">{acc_sc}%</div>
            <div style="font-size:10px;color:#aaa">{acc_p}/{acc_t} passed</div></div>
          <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:4px">Speech Rate</div>
            <div style="font-size:22px;font-weight:700;color:{wpm_color}">{wpm:.0f}</div>
            <div style="font-size:10px;color:#aaa">WPM &middot; {wpm_label}</div></div>
        </div>"""

    accessibility_section = f"""
      <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
        Accessibility</h2>
      {wpm_html}
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        {acc_feature_rows}
      </table>"""

  # --- Feature Timeline swimlane ---
  feature_timeline_section = ""
  ft = data.get("feature_timeline", {})
  if ft and ft.get("features"):
    timeline_svg = _feature_timeline_chart_html(ft)
    if timeline_svg:
      n_with_ts = sum(1 for f in ft["features"] if f.get("timestamps"))
      feature_timeline_section = f"""
        <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
          Feature Timeline</h2>
        <p style="font-size:12px;color:#888;margin-bottom:12px">
          {n_with_ts} feature{"s" if n_with_ts != 1 else ""} with structured timestamps.
          Click a bar to seek the video.</p>
        <div style="overflow-x:auto">{timeline_svg}</div>"""

  # --- Platform Compatibility ---
  platform_section = ""
  pf = data.get("platform_fit", {})
  if pf:
    platform_labels = {
        "youtube": "YouTube",
        "meta_feed": "Meta Feed",
        "meta_reels": "Meta Reels",
        "tiktok": "TikTok",
        "ctv": "CTV",
    }
    pf_cards = ""
    for pkey, plabel in platform_labels.items():
      pd = pf.get(pkey, {})
      if not pd:
        continue
      ps = pd.get("score", 0)
      ps_color = _score_color(ps)
      tips_html = "".join(
          f'<li style="margin-bottom:4px">{escape(t)}</li>' for t in pd.get("tips", [])[:3]
      )
      tips_list = f'<ul style="padding-left:16px;margin:8px 0 0;font-size:12px;line-height:1.6;color:#555">{tips_html}</ul>' if tips_html else ''
      pf_cards += (
          f'<div style="flex:1;min-width:160px;background:#f8f9fa;border-radius:12px;padding:16px;'
          f'border-top:3px solid {ps_color}">'
          f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:6px">{escape(plabel)}</div>'
          f'<div style="font-size:28px;font-weight:700;color:{ps_color};margin-bottom:4px">{ps}</div>'
          f'<div style="font-size:11px;color:#aaa">out of 100</div>'
          f'{tips_list}</div>'
      )
    if pf_cards:
      platform_section = f"""
        <h2 style="font-size:16px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e7eb">
          Platform Compatibility</h2>
        <div style="display:flex;gap:14px;flex-wrap:wrap">{pf_cards}</div>"""

  html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Creative Review — {brand} — {video}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #021A20; max-width: 900px; margin: 0 auto; padding: 32px 24px; }}
  @media print {{
    body {{ padding: 0; }}
    .no-print {{ display: none !important; }}
  }}
</style>
</head>
<body>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid #e5e7eb">
    <div>
      <h1 style="font-size:22px;font-weight:700">AI Creative Review</h1>
      <p style="color:#888;font-size:13px;margin-top:4px">{timestamp}</p>
    </div>
    <div class="no-print" style="display:flex;gap:8px">
      <button onclick="window.print()" style="padding:8px 16px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer;font-size:13px">Print / PDF</button>
    </div>
  </div>

  {video_embed_html}

  <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px">
    {score_cards_html}
  </div>

  {exec_summary_section}
  {action_plan_section}
  {concept_section}
  {metadata_section}
  {scenes_section}
  {volume_section}
  {emotional_arc_section}
  {feature_timeline_section}
  {performance_section}
  {platform_section}
  {reference_ads_section}
  {accessibility_section}
  {abcd_section}
  {persuasion_section}
  {structure_section}
  {brand_intel_section}

  <div style="margin-top:48px;padding-top:16px;border-top:1px solid #e5e7eb;color:#aaa;font-size:11px;text-align:center">
    Generated by AI Creative Review &middot; {report_id}
  </div>
  <script>
  // Video seeking — click timestamp pills or timeline bars to seek the embedded video
  document.addEventListener('click', function(e) {{
    var el = e.target.closest('.ts-pill, .ts-bar');
    if (!el) return;
    var raw = el.getAttribute('data-start-ts') || el.getAttribute('data-start');
    if (!raw) return;
    var secs = 0;
    if (raw.includes(':')) {{
      var p = raw.split(':');
      secs = parseInt(p[0]||0)*60 + parseFloat(p[1]||0);
    }} else {{
      secs = parseFloat(raw);
    }}
    var vid = document.querySelector('video');
    if (vid) {{ vid.currentTime = secs; vid.play(); return; }}
    var iframe = document.querySelector('iframe[src*="youtube"]');
    if (iframe) {{
      var src = iframe.src.split('?')[0] + '?autoplay=1&start=' + Math.floor(secs);
      iframe.src = src;
    }}
  }});
  </script>
</body>
</html>"""
  return html


def generate_report_pdf(data: dict) -> bytes:
  """Generate a PDF report from evaluation data using fpdf2.

  Args:
    data: The formatted evaluation results dict.
  Returns:
    PDF file content as bytes.
  """
  pdf = FPDF()
  pdf.set_auto_page_break(auto=True, margin=20)
  pdf.add_page()

  # --- Header ---
  pdf.set_font("Helvetica", "B", 20)
  pdf.cell(0, 12, "AI Creative Review", new_x="LMARGIN", new_y="NEXT")
  pdf.set_font("Helvetica", "", 10)
  pdf.set_text_color(120, 120, 120)
  timestamp = data.get("timestamp", datetime.datetime.now().isoformat(timespec="seconds"))
  pdf.cell(0, 6, timestamp, new_x="LMARGIN", new_y="NEXT")
  pdf.ln(4)
  pdf.set_draw_color(200, 200, 200)
  pdf.line(10, pdf.get_y(), 200, pdf.get_y())
  pdf.ln(8)

  # --- Score summary ---
  pdf.set_text_color(0, 0, 0)
  brand = data.get("brand_name", "Unknown")
  video = data.get("video_name", "")
  video_url = _video_web_url(data.get("video_uri", ""))
  pdf.set_font("Helvetica", "B", 12)
  safe_brand = _sanitize_pdf_text(brand)
  safe_video = _sanitize_pdf_text(video)
  pdf.cell(pdf.get_string_width("Brand: " + safe_brand + "    |    Video: ") + 2, 8, f"Brand: {safe_brand}    |    Video: ")
  pdf.set_text_color(10, 109, 134)
  pdf.cell(0, 8, safe_video, new_x="LMARGIN", new_y="NEXT", link=video_url)
  pdf.set_text_color(0, 0, 0)
  pdf.ln(4)

  abcd = data.get("abcd", {})
  if abcd.get("total", 0) > 0:
    _pdf_score_box(pdf, "ABCD Score", f"{abcd['score']}%",
                   f"{abcd['passed']}/{abcd['total']} features - {abcd['result']}",
                   _score_color_rgb(abcd["score"]))

  persuasion = data.get("persuasion", {})
  if persuasion.get("total", 0) > 0:
    _pdf_score_box(pdf, "Persuasion Density", f"{persuasion['density']}%",
                   f"{persuasion['detected']}/{persuasion['total']} tactics detected",
                   _score_color_rgb(persuasion["density"]))

  emotional_coherence = data.get("emotional_coherence", {})
  if isinstance(emotional_coherence, dict) and emotional_coherence.get("score") is not None:
    ec_s = emotional_coherence["score"]
    _pdf_score_box(pdf, "Emotional Coherence", f"{ec_s}/100",
                   "sentiment consistency across scenes",
                   _score_color_rgb(ec_s))

  acc_pdf = data.get("accessibility", {})
  if isinstance(acc_pdf, dict) and acc_pdf.get("total", 0) > 0:
    acc_s = acc_pdf["score"]
    _pdf_score_box(pdf, "Accessibility", f"{acc_s}%",
                   f"{acc_pdf.get('passed', 0)}/{acc_pdf.get('total', 0)} checks passed",
                   _score_color_rgb(acc_s))
  pdf.ln(6)

  # --- Executive Summary ---
  structure = data.get("structure", {})
  scenes = data.get("scenes", [])
  exec_lines = []
  if abcd.get("total", 0) > 0:
    label = _score_label(abcd["score"])
    exec_lines.append(f"ABCD Score: {abcd['score']}% ({abcd['passed']}/{abcd['total']} features) - {label}")
  if persuasion.get("total", 0) > 0:
    exec_lines.append(f"Persuasion Density: {persuasion['density']}% ({persuasion['detected']}/{persuasion['total']} tactics)")
  if structure.get("features"):
    arch = structure["features"][0].get("evidence", "")
    if arch:
      exec_lines.append(f"Creative Structure: {arch}")
  if scenes:
    exec_lines.append(f"Scenes: {len(scenes)}")
    flagged_pdf = [s for s in scenes if s.get("volume_flag")]
    if flagged_pdf:
      exec_lines.append(f"Volume jumps detected in {len(flagged_pdf)} scene{'s' if len(flagged_pdf) != 1 else ''}")
  ec_pdf = data.get("emotional_coherence", {})
  if isinstance(ec_pdf, dict):
    ec_sc = ec_pdf.get("score")
    if ec_sc is not None:
      exec_lines.append(f"Emotional Coherence: {ec_sc}/100")
    ec_sh = ec_pdf.get("flagged_shifts", [])
    if ec_sh:
      exec_lines.append(
          f"Abrupt emotional shifts in {len(ec_sh)} transition{'s' if len(ec_sh) != 1 else ''}: "
          + ", ".join(f"S{s['from_scene']}->S{s['to_scene']}" for s in ec_sh[:3])
      )

  if exec_lines:
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    for line in exec_lines:
      pdf.cell(0, 6, _sanitize_pdf_text(f"  {line}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

  # --- Creative Concept / Brief ---
  concept = data.get("concept", {})
  has_brief = bool(concept.get("one_line_pitch"))
  if has_brief or concept.get("name") or concept.get("description"):
    title = "Creative Brief" if has_brief else "Creative Concept"
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    if has_brief:
      # One-line pitch
      pdf.set_font("Helvetica", "B", 12)
      pdf.set_text_color(10, 109, 134)
      pdf.multi_cell(0, 7, _sanitize_pdf_text(concept.get("one_line_pitch", "")))
      pdf.ln(3)
      for lbl, key in [
          ("KEY MESSAGE", "key_message"),
          ("EMOTIONAL HOOK", "emotional_hook"),
          ("NARRATIVE TECHNIQUE", "narrative_technique"),
          ("USP", "unique_selling_proposition"),
          ("TARGET EMOTION", "target_emotion"),
          ("CREATIVE TERRITORY", "creative_territory"),
      ]:
        val = concept.get(key, "")
        if val:
          if pdf.get_y() > 260:
            pdf.add_page()
          pdf.set_font("Helvetica", "B", 8)
          pdf.set_text_color(131, 31, 128)
          pdf.cell(0, 5, f"  {lbl}", new_x="LMARGIN", new_y="NEXT")
          pdf.set_x(pdf.l_margin)
          pdf.set_font("Helvetica", "", 9)
          pdf.set_text_color(60, 60, 60)
          pdf.multi_cell(0, 5, _sanitize_pdf_text(f"  {val}"))
      mh = concept.get("messaging_hierarchy", {})
      if isinstance(mh, dict) and mh.get("primary"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(10, 109, 134)
        pdf.cell(0, 5, "  MESSAGING HIERARCHY", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 5, _sanitize_pdf_text(f"  Primary: {mh.get('primary', '')}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, _sanitize_pdf_text(f"  Secondary: {mh.get('secondary', '')}"), new_x="LMARGIN", new_y="NEXT")
        for pp in mh.get("proof_points", [])[:4]:
          if pp:
            pdf.cell(0, 4, _sanitize_pdf_text(f"    - {pp}"), new_x="LMARGIN", new_y="NEXT")
    else:
      c_name = concept.get("name", "")
      if c_name:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(10, 109, 134)
        pdf.cell(0, 7, _sanitize_pdf_text(c_name), new_x="LMARGIN", new_y="NEXT")
      c_desc = concept.get("description", "")
      if c_desc:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, _sanitize_pdf_text(c_desc[:500]))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

  # --- Scenes ---
  if scenes:
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Scene Timeline", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    for i, sc in enumerate(scenes):
      if pdf.get_y() > 255:
        pdf.add_page()
      num = sc.get("scene_number", i + 1)
      ts = f"{sc.get('start_time', '?')} - {sc.get('end_time', '?')}"
      pdf.set_font("Helvetica", "B", 10)
      pdf.set_text_color(10, 109, 134)
      pdf.cell(0, 6, _sanitize_pdf_text(f"Scene {num}  |  {ts}"), new_x="LMARGIN", new_y="NEXT")
      desc = sc.get("description", "")
      if desc:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, _sanitize_pdf_text(desc))
      transcript = sc.get("transcript", "")
      if transcript:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 4, _sanitize_pdf_text(f'"{transcript}"'))
      emo = sc.get("emotion", "")
      sent = sc.get("sentiment_score")
      if emo:
        emo_label = f"{emo}"
        if sent is not None:
          emo_label += f" ({sent:+.1f})"
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(10, 109, 134)
        pdf.cell(0, 4, _sanitize_pdf_text(f"  Emotion: {emo_label}"), new_x="LMARGIN", new_y="NEXT")
      pdf.ln(3)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

  # --- Emotional Arc (text-based, after scenes) ---
  emo_scenes_pdf = [s for s in scenes if s.get("sentiment_score") is not None] if scenes else []
  if emo_scenes_pdf:
    if pdf.get_y() > 220:
      pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Emotional Arc", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    bar_x_start = 30
    bar_max_w = 130
    for i, sc in enumerate(emo_scenes_pdf):
      if pdf.get_y() > 265:
        pdf.add_page()
      num = sc.get("scene_number", i + 1)
      sent_val = sc.get("sentiment_score", 0.0)
      emo_name = sc.get("emotion", "")
      # Check for shift
      is_shift = False
      if i > 0:
        prev = emo_scenes_pdf[i - 1].get("sentiment_score", 0.0)
        if abs(sent_val - prev) > 0.5:
          is_shift = True
      pdf.set_font("Helvetica", "B" if is_shift else "", 9)
      pdf.set_text_color(220, 38, 38) if is_shift else pdf.set_text_color(80, 80, 80)
      pdf.cell(20, 5, f"S{num}")
      y = pdf.get_y()
      # Bar: map -1..1 to 0..bar_max_w
      norm = (sent_val + 1.0) / 2.0
      w = max(2, norm * bar_max_w)
      if is_shift:
        pdf.set_fill_color(248, 113, 113)
      elif sent_val >= 0:
        pdf.set_fill_color(10, 109, 134)
      else:
        pdf.set_fill_color(156, 163, 175)
      pdf.rect(bar_x_start, y, w, 4, style="F")
      pdf.set_x(bar_x_start + bar_max_w + 4)
      pdf.set_font("Helvetica", "B" if is_shift else "", 8)
      label = f"{sent_val:+.1f}  {emo_name}"
      if is_shift:
        label += "  ! shift"
      pdf.cell(0, 5, _sanitize_pdf_text(label), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

  # --- Audio Analysis (volume + richness) ---
  vol_scenes = [s for s in scenes if "volume_pct" in s] if scenes else []
  if vol_scenes:
    if pdf.get_y() > 220:
      pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Audio Analysis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    bar_x_start = 30
    bar_max_w = 130
    for i, sc in enumerate(vol_scenes):
      if pdf.get_y() > 265:
        pdf.add_page()
      num = sc.get("scene_number", i + 1)
      pct = sc.get("volume_pct", 0)
      db = sc.get("volume_db", -60)
      flag = sc.get("volume_flag", False)
      change = sc.get("volume_change_pct", 0)
      pdf.set_font("Helvetica", "B" if flag else "", 9)
      pdf.set_text_color(220, 38, 38) if flag else pdf.set_text_color(80, 80, 80)
      pdf.cell(20, 5, f"S{num}")
      y = pdf.get_y()
      w = max(2, pct / 100 * bar_max_w)
      r, g, b = (248, 113, 113) if flag else (10, 109, 134)
      pdf.set_fill_color(r, g, b)
      pdf.rect(bar_x_start, y, w, 4, style="F")
      pdf.set_x(bar_x_start + bar_max_w + 4)
      pdf.set_font("Helvetica", "B" if flag else "", 8)
      vol_label = f"{pct:.0f}% ({db:.1f} dB)"
      if flag:
        arrow = "^" if change > 0 else "v"
        vol_label += f"  {arrow}{abs(change):.0f}%"
      pdf.cell(0, 5, _sanitize_pdf_text(vol_label), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    # Audio richness summary in PDF
    aa_pdf = data.get("audio_analysis", {})
    if aa_pdf:
      cong = aa_pdf.get("congruence_score", 0)
      sil_ct = len(aa_pdf.get("silence_gaps", []))
      avg_sp = aa_pdf.get("avg_speech_ratio", 0)
      pdf.set_font("Helvetica", "", 9)
      pdf.set_text_color(60, 60, 60)
      pdf.cell(0, 5, _sanitize_pdf_text(f"  A/V Congruence: {cong}/100  |  Silence gaps: {sil_ct}  |  Avg speech: {avg_sp:.0%}"),
               new_x="LMARGIN", new_y="NEXT")
      summary = aa_pdf.get("summary", "")
      if summary:
        pdf.multi_cell(0, 4, _sanitize_pdf_text(f"  {summary}"))
      pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

  # --- Feature Timeline (text-based, after volume) ---
  ft_pdf = data.get("feature_timeline", {})
  ft_features = ft_pdf.get("features", []) if ft_pdf else []
  ts_features = [f for f in ft_features if f.get("timestamps")]
  if ts_features:
    if pdf.get_y() > 220:
      pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Feature Timeline", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    for feat in ts_features:
      if pdf.get_y() > 265:
        pdf.add_page()
      detected = feat.get("detected", False)
      icon = "PASS" if detected else "FAIL"
      icon_color = (22, 163, 74) if detected else (220, 38, 38)
      pdf.set_font("Helvetica", "B", 9)
      pdf.set_text_color(*icon_color)
      pdf.cell(12, 5, icon)
      pdf.set_text_color(0, 0, 0)
      pdf.set_font("Helvetica", "B", 9)
      pdf.cell(70, 5, _sanitize_pdf_text(feat.get("name", "")[:40]))
      ts_strs = [f"{ts['start_s']:.0f}s-{ts['end_s']:.0f}s" for ts in feat["timestamps"][:4]]
      pdf.set_font("Helvetica", "", 8)
      pdf.set_text_color(10, 109, 134)
      pdf.cell(0, 5, "  ".join(ts_strs), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

  # --- Video Metadata ---
  vm = data.get("video_metadata", {})
  if vm:
    vm_items = [
        ("Duration", vm.get("duration", "")),
        ("Resolution", vm.get("resolution", "")),
        ("Aspect Ratio", vm.get("aspect_ratio", "")),
        ("Frame Rate", vm.get("frame_rate", "")),
        ("File Size", vm.get("file_size", "")),
        ("Codec", vm.get("codec", "")),
    ]
    vm_items = [(l, v) for l, v in vm_items if v and v != "Unknown"]
    if vm_items:
      pdf.set_font("Helvetica", "B", 14)
      pdf.cell(0, 10, "Creative Metadata", new_x="LMARGIN", new_y="NEXT")
      pdf.set_draw_color(200, 200, 200)
      pdf.line(10, pdf.get_y(), 200, pdf.get_y())
      pdf.ln(4)
      for lbl, val in vm_items:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(10, 109, 134)
        pdf.cell(50, 6, lbl)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, _sanitize_pdf_text(str(val)), new_x="LMARGIN", new_y="NEXT")
      pdf.ln(4)

  # --- Platform Compatibility ---
  pf_pdf = data.get("platform_fit", {})
  if pf_pdf:
    if pdf.get_y() > 220:
      pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Platform Compatibility", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    plat_labels = {"youtube": "YouTube", "meta_feed": "Meta Feed", "meta_reels": "Meta Reels", "tiktok": "TikTok", "ctv": "CTV"}
    for pk, pl in plat_labels.items():
      pd = pf_pdf.get(pk, {})
      if not pd:
        continue
      if pdf.get_y() > 260:
        pdf.add_page()
      ps = pd.get("score", 0)
      ps_rgb = _score_color_rgb(ps)
      pdf.set_font("Helvetica", "B", 10)
      pdf.set_text_color(*ps_rgb)
      pdf.cell(20, 6, f"{ps}")
      pdf.set_text_color(0, 0, 0)
      pdf.cell(0, 6, pl, new_x="LMARGIN", new_y="NEXT")
      for tip in pd.get("tips", [])[:2]:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 4, _sanitize_pdf_text(f"    - {tip}"), new_x="LMARGIN", new_y="NEXT")
      pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

  # --- Accessibility ---
  if isinstance(acc_pdf, dict) and acc_pdf.get("total", 0) > 0:
    if pdf.get_y() > 220:
      pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Accessibility", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    wpm_pdf = acc_pdf.get("speech_rate_wpm", 0)
    wpm_flag_pdf = acc_pdf.get("speech_rate_flag", "no_speech")
    if wpm_pdf > 0:
      pdf.set_font("Helvetica", "", 9)
      pdf.set_text_color(60, 60, 60)
      wpm_lbl = "OK" if wpm_flag_pdf == "ok" else "Too fast" if wpm_flag_pdf == "too_fast" else "Too slow"
      pdf.cell(0, 5, f"  Speech Rate: {wpm_pdf:.0f} WPM ({wpm_lbl})", new_x="LMARGIN", new_y="NEXT")
      pdf.ln(2)
    for af in acc_pdf.get("features", []):
      if pdf.get_y() > 260:
        pdf.add_page()
      icon = "PASS" if af.get("detected") else "FAIL"
      color = (22, 163, 74) if af.get("detected") else (220, 38, 38)
      pdf.set_font("Helvetica", "B", 10)
      pdf.set_text_color(*color)
      pdf.cell(12, 6, icon)
      pdf.set_text_color(0, 0, 0)
      pdf.cell(0, 6, _sanitize_pdf_text(af.get("name", "")), new_x="LMARGIN", new_y="NEXT")
      for key in ("rationale", "evidence"):
        val = af.get(key, "")
        if val:
          pdf.set_font("Helvetica", "B", 8)
          pdf.set_text_color(131, 31, 128)
          pdf.cell(0, 5, f"    {key.upper()}", new_x="LMARGIN", new_y="NEXT")
          pdf.set_x(pdf.l_margin)
          pdf.set_font("Helvetica", "", 8)
          pdf.set_text_color(80, 80, 80)
          pdf.multi_cell(0, 4, _sanitize_pdf_text(f"    {val}"))
      if not af.get("detected") and af.get("remediation"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(202, 138, 4)
        pdf.cell(0, 5, "    FIX", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 4, _sanitize_pdf_text(f"    {af.get('remediation', '')}"))
      pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

  # --- ABCD Features ---
  if abcd.get("features"):
    _pdf_feature_section(pdf, "ABCD Feature Results", abcd["features"])

  # --- Persuasion ---
  if persuasion.get("features"):
    _pdf_feature_section(pdf, "Persuasion Tactics", persuasion["features"])

  # --- Structure ---
  if structure.get("features"):
    s = structure["features"][0]
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Creative Structure", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    if s.get("evidence"):
      pdf.set_font("Helvetica", "B", 10)
      pdf.cell(0, 7, _sanitize_pdf_text(f"Archetype(s): {s['evidence']}"), new_x="LMARGIN", new_y="NEXT")
    for key in ("rationale", "strengths", "weaknesses"):
      val = s.get(key, "")
      if val:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(131, 31, 128)
        pdf.cell(0, 6, key.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 5, _sanitize_pdf_text(val))
        pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

  # --- Brand Intelligence ---
  bi = data.get("brand_intelligence", {})
  if bi and bi.get("company_name"):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Brand Intelligence Brief", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    bi_text_fields = [
        ("Company Overview", [
            ("Company", "company_name"), ("Website", "website"),
            ("Founders / Leadership", "founders_leadership"),
            ("Product / Service", "product_service"), ("Launched", "launched"),
            ("Description", "description"), ("Brand Positioning", "brand_positioning"),
            ("Core Value Proposition", "core_value_proposition"),
            ("Mission", "mission"), ("Taglines", "taglines"),
            ("Social Proof", "social_proof_overview"),
        ]),
        ("Target Audience", [
            ("Primary", "target_audience_primary"),
            ("Secondary", "target_audience_secondary"),
            ("Key Insight", "key_insight"),
            ("Secondary Insight", "secondary_insight"),
        ]),
        ("Brand Tone & Voice", [
            ("Tone", "tone"), ("Voice", "voice"), ("What It Is NOT", "what_it_is_not"),
        ]),
    ]

    for section_title, fields in bi_text_fields:
      if pdf.get_y() > 250:
        pdf.add_page()
      pdf.set_font("Helvetica", "B", 11)
      pdf.set_text_color(10, 109, 134)
      pdf.cell(0, 8, section_title, new_x="LMARGIN", new_y="NEXT")
      pdf.ln(2)
      for label, key in fields:
        val = bi.get(key, "")
        if not val or val == "Not available":
          continue
        if pdf.get_y() > 260:
          pdf.add_page()
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(131, 31, 128)
        pdf.cell(0, 5, f"  {label.upper()}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, _sanitize_pdf_text(f"  {val}"))
        pdf.ln(1)
      pdf.ln(3)

    bi_list_fields = [
        ("Products & Pricing", "products_pricing"),
        ("Social Proof & Credibility", "credibility_signals"),
        ("Paid Media Channels", "paid_media_channels"),
        ("Creative Formats", "creative_formats"),
        ("Messaging Themes", "messaging_themes"),
        ("Offers & CTA Patterns", "offers_and_ctas"),
    ]

    for section_title, key in bi_list_fields:
      items = bi.get(key, [])
      if not items:
        continue
      if pdf.get_y() > 250:
        pdf.add_page()
      pdf.set_font("Helvetica", "B", 11)
      pdf.set_text_color(10, 109, 134)
      pdf.cell(0, 8, section_title, new_x="LMARGIN", new_y="NEXT")
      pdf.ln(2)
      for item in items:
        if not item:
          continue
        if pdf.get_y() > 265:
          pdf.add_page()
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, _sanitize_pdf_text(f"  - {item}"))
      pdf.ln(3)

    pdf.set_text_color(0, 0, 0)

  # --- Footer ---
  pdf.set_font("Helvetica", "", 8)
  pdf.set_text_color(170, 170, 170)
  report_id = data.get("report_id", "")
  pdf.cell(0, 6, f"Generated by AI Creative Review  |  {report_id}",
           new_x="LMARGIN", new_y="NEXT", align="C")

  return bytes(pdf.output())


def _score_color_rgb(score: float) -> tuple[int, int, int]:
  """Return RGB tuple for a score percentage."""
  if score >= 80:
    return (22, 163, 74)
  elif score >= 65:
    return (217, 119, 6)
  return (220, 38, 38)


def _pdf_score_box(pdf: FPDF, label: str, value: str, subtitle: str,
                   color: tuple[int, int, int]) -> None:
  """Draw a score summary line in the PDF."""
  pdf.set_font("Helvetica", "", 9)
  pdf.set_text_color(120, 120, 120)
  pdf.cell(50, 7, label)
  pdf.set_font("Helvetica", "B", 16)
  pdf.set_text_color(*color)
  pdf.cell(30, 7, value)
  pdf.set_font("Helvetica", "", 9)
  pdf.set_text_color(120, 120, 120)
  pdf.cell(0, 7, _sanitize_pdf_text(subtitle), new_x="LMARGIN", new_y="NEXT")
  pdf.set_text_color(0, 0, 0)


def _pdf_feature_section(pdf: FPDF, title: str, features: list[dict]) -> None:
  """Render a feature section (heading + feature rows) in the PDF."""
  pdf.set_font("Helvetica", "B", 14)
  pdf.set_text_color(0, 0, 0)
  pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
  pdf.set_draw_color(200, 200, 200)
  pdf.line(10, pdf.get_y(), 200, pdf.get_y())
  pdf.ln(4)

  for f in features:
    # Check if we need a new page (leave room for details)
    if pdf.get_y() > 260:
      pdf.add_page()

    icon = "PASS" if f["detected"] else "FAIL"
    color = (22, 163, 74) if f["detected"] else (220, 38, 38)
    conf = f"{f['confidence'] * 100:.0f}%" if f.get("confidence") else ""

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*color)
    pdf.cell(8, 6, icon)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, _sanitize_pdf_text(f"{f['name']}  {conf}"), new_x="LMARGIN", new_y="NEXT")

    for key in ("rationale", "evidence", "strengths", "weaknesses"):
      val = f.get(key, "")
      if val:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(131, 31, 128)
        pdf.cell(0, 5, f"    {key.upper()}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 4, _sanitize_pdf_text(f"    {val}"))
    # Timestamps
    ts_list = f.get("timestamps", [])
    if ts_list:
      pdf.set_font("Helvetica", "B", 8)
      pdf.set_text_color(10, 109, 134)
      pdf.cell(0, 5, "    TIMESTAMPS", new_x="LMARGIN", new_y="NEXT")
      pdf.set_font("Helvetica", "", 8)
      pdf.set_text_color(80, 80, 80)
      ts_str = ", ".join(f"{ts.get('start','?')}-{ts.get('end','?')}" for ts in ts_list[:5])
      pdf.cell(0, 4, _sanitize_pdf_text(f"    {ts_str}"), new_x="LMARGIN", new_y="NEXT")
    # Recommendation
    rec = f.get("recommendation", "")
    if rec:
      rec_pri = f.get("recommendation_priority", "")
      pdf.set_font("Helvetica", "B", 8)
      pdf.set_text_color(10, 109, 134)
      pri_label = f" [{rec_pri.upper()}]" if rec_pri else ""
      pdf.cell(0, 5, f"    RECOMMENDATION{pri_label}", new_x="LMARGIN", new_y="NEXT")
      pdf.set_x(pdf.l_margin)
      pdf.set_font("Helvetica", "", 8)
      pdf.set_text_color(80, 80, 80)
      pdf.multi_cell(0, 4, _sanitize_pdf_text(f"    {rec}"))
    pdf.ln(2)


def _slack_trunc(text: str, limit: int = 2900) -> str:
  """Truncate text to stay within Slack's 3000-char section limit."""
  if len(text) <= limit:
    return text
  return text[:limit] + "\u2026"


def _slack_score_emoji(score: float) -> str:
  """Return a Slack emoji string for a score value."""
  if score >= 80:
    return ":large_green_circle:"
  if score >= 65:
    return ":large_yellow_circle:"
  return ":red_circle:"


def _slack_section(blocks: list[dict], text: str) -> None:
  """Append a divider + mrkdwn section block, auto-truncating text."""
  blocks.append({"type": "divider"})
  blocks.append({
      "type": "section",
      "text": {"type": "mrkdwn", "text": _slack_trunc(text)},
  })


def _build_slack_blocks(data: dict, report_url: str) -> list[dict]:
  """Build a compact Slack Block Kit message (~2000 chars max).

  Shows: header, key scores, top action items, and a report link.
  All detail is available in the full HTML report.
  """
  brand = data.get("brand_name", "Unknown")
  video = data.get("video_name", "")
  video_uri = data.get("video_uri", "")
  abcd = data.get("abcd", {})
  persuasion = data.get("persuasion", {})
  predictions = data.get("predictions", {})
  emotional_coherence = data.get("emotional_coherence", {})
  accessibility = data.get("accessibility", {})
  scenes = data.get("scenes", [])

  blocks: list[dict] = []

  # Header
  blocks.append({
      "type": "header",
      "text": {"type": "plain_text", "text": "AI Creative Review Complete"},
  })
  # Make video name clickable if we have a YouTube URL; otherwise link to report
  is_yt = video_uri and ("youtube.com" in video_uri or "youtu.be" in video_uri)
  video_link_url = video_uri if is_yt else report_url
  video_display = f"<{video_link_url}|{video}>" if video_link_url and video else f"`{video}`"
  user_email = data.get("user_email", "")
  user_line = f"\n*Submitted by:* {user_email}" if user_email else ""
  blocks.append({
      "type": "section",
      "text": {"type": "mrkdwn", "text": f"*Video:* {video_display}  \u2014  *Brand:* {brand}{user_line}"},
  })

  # --- Scores (single compact block) ---
  score_lines = []
  if predictions.get("overall_score") is not None:
    score_lines.append(f":bar_chart: Performance: *{predictions['overall_score']}/100*")
  if abcd.get("total", 0) > 0:
    score_lines.append(
        f"{_slack_score_emoji(abcd['score'])} ABCD: *{abcd['score']}%* "
        f"({abcd['passed']}/{abcd['total']}) {abcd['result']}")
  if persuasion.get("total", 0) > 0:
    score_lines.append(
        f":dart: Persuasion: *{persuasion['density']}%* "
        f"({persuasion['detected']}/{persuasion['total']})")
  if isinstance(emotional_coherence, dict) and emotional_coherence.get("score") is not None:
    score_lines.append(f"{_slack_score_emoji(emotional_coherence['score'])} Emotional Coherence: *{emotional_coherence['score']}/100*")
  if isinstance(accessibility, dict) and accessibility.get("total", 0) > 0:
    acc_s = accessibility.get("score", 100)
    score_lines.append(f"{_slack_score_emoji(acc_s)} Accessibility: *{acc_s}%*")
  if scenes:
    n_flagged = sum(1 for s in scenes if s.get("volume_flag"))
    scene_note = f" \u2014 :warning: {n_flagged} volume jump{'s' if n_flagged != 1 else ''}" if n_flagged else ""
    score_lines.append(f":clapper: {len(scenes)} scene{'s' if len(scenes) != 1 else ''}{scene_note}")
  if score_lines:
    _slack_section(blocks, "\n".join(score_lines))

  # --- Top action items (max 2, high-priority only) ---
  action_items = [ap for ap in data.get("action_plan", []) if ap.get("priority") == "high"][:2]
  if action_items:
    lines = [":clipboard: *Top Actions*"]
    for ap in action_items:
      lines.append(f":red_circle: *{ap.get('feature_name', '')}:* {ap.get('recommendation', '')}")
    _slack_section(blocks, _slack_trunc("\n".join(lines), 600))

  # --- Report link (show clickable URL) ---
  if report_url:
    _slack_section(blocks, f":page_facing_up: *Report:* <{report_url}|{report_url}>")

  return blocks


def send_slack_notification(
    data: dict,
    report_url: str,
    webhook_url: str,
) -> bool:
  """Post an evaluation summary to a Slack incoming webhook.

  Args:
    data: The formatted evaluation results dict.
    report_url: Public URL to the full HTML report.
    webhook_url: Slack incoming webhook URL.
  Returns:
    True if the notification was sent successfully.
  """
  if not webhook_url:
    logging.info("No Slack webhook URL configured — skipping notification.")
    return False

  video = data.get("video_name", "")
  brand = data.get("brand_name", "Unknown")
  blocks = _build_slack_blocks(data, report_url)

  # Build compact fallback text for push notifications
  fallback_parts = [f"AI Creative Review Complete \u2014 {video} (Brand: {brand})"]
  abcd = data.get("abcd", {})
  if abcd.get("total", 0) > 0:
    fallback_parts.append(f"ABCD: {abcd['score']}%")
  persuasion = data.get("persuasion", {})
  if persuasion.get("total", 0) > 0:
    fallback_parts.append(f"Persuasion: {persuasion['density']}%")
  ec = data.get("emotional_coherence", {})
  if isinstance(ec, dict) and ec.get("score") is not None:
    fallback_parts.append(f"Emotional Coherence: {ec['score']}/100")
  acc = data.get("accessibility", {})
  if isinstance(acc, dict) and acc.get("total", 0) > 0:
    fallback_parts.append(f"Accessibility: {acc.get('score', 100)}%")

  payload = {
      "text": " | ".join(fallback_parts),
      "blocks": blocks,
      "unfurl_links": False,
  }

  try:
    body = json.dumps(payload).encode("utf-8")
    logging.info("Sending Slack notification for %s (%d blocks, %d bytes)",
                 video, len(blocks), len(body))
    req = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
      resp_body = resp.read().decode("utf-8", errors="replace")
      if resp.status == 200:
        logging.info("Slack notification sent for %s", video)
        return True
      else:
        logging.warning("Slack webhook returned status %d: %s", resp.status, resp_body)
        return False
  except urllib.error.HTTPError as ex:
    err_body = ex.read().decode("utf-8", errors="replace") if ex.fp else ""
    logging.error("Slack webhook HTTP %d: %s", ex.code, err_body)
    return False
  except Exception as ex:
    logging.error("Failed to send Slack notification: %s", ex)
    return False


def generate_comparison_report_html(data: dict) -> str:
  """Generate a side-by-side comparison report for 2+ evaluated variants."""
  comparison = data.get("comparison", {})
  variants_data = data.get("variants", [])
  variant_summaries = comparison.get("variants", [])
  deltas = comparison.get("deltas", [])
  feature_diffs = comparison.get("feature_diffs", [])
  winner = comparison.get("recommended_winner", {})
  timestamp = data.get("timestamp", "")
  comparison_id = data.get("comparison_id", "")

  n = len(variant_summaries)
  col_w = max(20, 90 // n) if n else 45

  # Build variant score cards side-by-side
  cards_html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:32px">'
  for i, vs in enumerate(variant_summaries):
    is_winner = (i == winner.get("index", -1))
    border = "2px solid #16a34a" if is_winner else "1px solid #e5e7eb"
    badge = '<span style="background:#16a34a;color:#fff;font-size:11px;font-weight:700;padding:3px 10px;border-radius:12px;margin-left:8px">WINNER</span>' if is_winner else ""
    abcd_cls = "#16a34a" if vs.get("abcd_score", 0) >= 80 else "#f59e0b" if vs.get("abcd_score", 0) >= 65 else "#dc2626"
    perf_cls = "#16a34a" if vs.get("performance_score", 0) >= 70 else "#f59e0b" if vs.get("performance_score", 0) >= 50 else "#dc2626"
    acc_cls = "#16a34a" if vs.get("accessibility_score", 0) >= 80 else "#f59e0b" if vs.get("accessibility_score", 0) >= 60 else "#dc2626"
    name = escape(vs.get("video_name", f"Variant {i + 1}"))
    brand = escape(vs.get("brand_name", ""))
    report_id = vs.get("report_id", "")
    report_link = f'<a href="/report/{report_id}" style="color:#0A6D86;font-size:12px">Full Report &rarr;</a>' if report_id else ""

    cards_html += f'''
    <div style="background:#fff;border:{border};border-radius:16px;padding:24px;position:relative">
      <div style="font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:4px">{name}{badge}</div>
      <div style="font-size:13px;color:#666;margin-bottom:16px">{brand}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div style="text-align:center;padding:12px;background:#f8f9fa;border-radius:10px">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">ABCD</div>
          <div style="font-size:28px;font-weight:700;color:{abcd_cls}">{vs.get("abcd_score", 0)}%</div>
        </div>
        <div style="text-align:center;padding:12px;background:#f8f9fa;border-radius:10px">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">Performance</div>
          <div style="font-size:28px;font-weight:700;color:{perf_cls}">{vs.get("performance_score", 0)}</div>
        </div>
        <div style="text-align:center;padding:12px;background:#f8f9fa;border-radius:10px">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">Persuasion</div>
          <div style="font-size:28px;font-weight:700;color:#0A6D86">{vs.get("persuasion_density", 0)}%</div>
        </div>
        <div style="text-align:center;padding:12px;background:#f8f9fa;border-radius:10px">
          <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">Accessibility</div>
          <div style="font-size:28px;font-weight:700;color:{acc_cls}">{vs.get("accessibility_score", 0)}%</div>
        </div>
      </div>
      <div style="margin-top:12px;text-align:right">{report_link}</div>
    </div>'''
  cards_html += '</div>'

  # Deltas section
  deltas_html = ''
  if deltas:
    deltas_html = '<div style="margin-bottom:32px"><h2 style="font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:12px">Score Deltas</h2>'
    for d in deltas:
      deltas_html += f'<div style="background:#f8f9fa;border-radius:12px;padding:16px;margin-bottom:8px"><strong>{escape(d.get("vs", ""))}</strong><div style="display:flex;gap:20px;margin-top:8px">'
      for key, label in [("abcd_delta", "ABCD"), ("persuasion_delta", "Persuasion"), ("performance_delta", "Performance")]:
        val = d.get(key, 0)
        color = "#16a34a" if val > 0 else "#dc2626" if val < 0 else "#888"
        arrow = "&#9650;" if val > 0 else "&#9660;" if val < 0 else "&#8212;"
        deltas_html += f'<span style="color:{color};font-weight:600">{label}: {arrow} {abs(val):.1f}</span>'
      deltas_html += '</div></div>'
    deltas_html += '</div>'

  # Feature diffs
  fdiffs_html = ''
  if feature_diffs:
    fdiffs_html = '<div style="margin-bottom:32px"><h2 style="font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:12px">Feature Differences</h2>'
    fdiffs_html += '<p style="font-size:13px;color:#666;margin-bottom:12px">Features where variants disagree:</p>'
    for fd in feature_diffs:
      fdiffs_html += f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #e5e7eb">'
      fdiffs_html += f'<span style="width:200px;font-weight:600;font-size:13px">{escape(fd.get("feature_name", ""))}</span>'
      for ri, r in enumerate(fd.get("results", [])):
        if r is True:
          fdiffs_html += '<span style="color:#16a34a;font-weight:700;width:80px;text-align:center">&#10003;</span>'
        elif r is False:
          fdiffs_html += '<span style="color:#dc2626;font-weight:700;width:80px;text-align:center">&#10007;</span>'
        else:
          fdiffs_html += '<span style="color:#888;width:80px;text-align:center">N/A</span>'
      fdiffs_html += '</div>'
    fdiffs_html += '</div>'

  # Winner recommendation
  winner_html = ''
  if winner:
    winner_html = f'''
    <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #16a34a;border-radius:16px;padding:24px;margin-bottom:32px">
      <h2 style="font-size:18px;font-weight:700;color:#16a34a;margin:0 0 8px">&#127942; Recommended Winner: {escape(winner.get("video_name", ""))}</h2>
      <p style="font-size:14px;color:#333;margin:0;line-height:1.6">{escape(winner.get("justification", ""))}</p>
    </div>'''

  html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A/B Comparison Report \u2014 AI Creative Review</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif; background:#f3f4f6; color:#1a1a2e; }}
  .header {{ background:linear-gradient(135deg,#0A6D86,#084c5e); color:#fff; padding:32px 40px; }}
  .header h1 {{ font-size:28px; font-weight:800; margin-bottom:4px; }}
  .header .sub {{ font-size:14px; opacity:0.8; }}
  .container {{ max-width:1100px; margin:0 auto; padding:32px 24px; }}
</style>
</head>
<body>
<div class="header">
  <h1>A/B Variant Comparison</h1>
  <div class="sub">{n} variants compared &middot; {escape(timestamp)} &middot; ID: {escape(comparison_id)}</div>
</div>
<div class="container">
  {winner_html}
  {cards_html}
  {deltas_html}
  {fdiffs_html}
  <div style="text-align:center;color:#aaa;font-size:12px;padding:24px 0">Generated by AI Creative Review</div>
</div>
</body>
</html>'''
  return html
