"""Admin API router: render management endpoints."""

from __future__ import annotations

import csv
import datetime
import io
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import get_current_user
from db import CreditTransaction, Render, User, get_db

router = APIRouter(prefix="/admin/api", tags=["admin"])


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

ADMIN_EMAILS = {"kevin@kwangel.fund"}


def require_admin(
    user: User = Depends(get_current_user),
) -> User:
  """Dependency that ensures the current user has admin privileges."""
  if user.email not in ADMIN_EMAILS:
    raise HTTPException(status_code=403, detail="Admin access required")
  return user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_to_dict(r: Render) -> dict:
  """Serialise a Render row to a JSON-friendly dict."""
  return {
      "render_id": r.render_id,
      "status": r.status,
      "progress_pct": r.progress_pct,
      "created_at": r.created_at.isoformat() if r.created_at else None,
      "started_at": r.started_at.isoformat() if r.started_at else None,
      "finished_at": r.finished_at.isoformat() if r.finished_at else None,
      "user_id": r.user_id,
      "user_email": r.user_email,
      "user_name": r.user_name,
      "source_type": r.source_type,
      "source_ref": r.source_ref,
      "input_assets": json.loads(r.input_assets) if r.input_assets else [],
      "prompt_text": r.prompt_text,
      "asset_url": r.prompt_text or "",
      "brand_guide": r.brand_guide,
      "config": json.loads(r.config_json) if r.config_json else {},
      "output_url": r.output_url,
      "report_url": f"/report/{r.render_id}",
      "thumbnail_url": r.thumbnail_url,
      "duration_seconds": r.duration_seconds,
      "file_size_mb": r.file_size_mb,
      "pipeline_version": r.pipeline_version,
      "model": r.model,
      "tokens_estimated": r.tokens_estimated,
      "tokens_used": r.tokens_used,
      "error_code": r.error_code,
      "error_message": r.error_message,
      "logs_url": r.logs_url,
      "webhook_failures_count": r.webhook_failures_count,
      "slack_notified": r.slack_notified,
  }


def _apply_filters(query, params: dict):
  """Apply optional filter parameters to a SQLAlchemy query."""
  q = params.get("q")
  if q:
    like = f"%{q}%"
    query = query.filter(
        or_(
            Render.render_id.ilike(like),
            Render.user_email.ilike(like),
            Render.user_name.ilike(like),
            Render.prompt_text.ilike(like),
            Render.brand_guide.ilike(like),
            Render.source_ref.ilike(like),
        )
    )

  status = params.get("status")
  if status:
    statuses = [s.strip() for s in status.split(",") if s.strip()]
    if statuses:
      query = query.filter(Render.status.in_(statuses))

  source = params.get("source")
  if source:
    sources = [s.strip() for s in source.split(",") if s.strip()]
    if sources:
      query = query.filter(Render.source_type.in_(sources))

  user = params.get("user")
  if user:
    like = f"%{user}%"
    query = query.filter(
        or_(Render.user_email.ilike(like), Render.user_name.ilike(like))
    )

  time_range = params.get("time_range")
  if time_range:
    now = datetime.datetime.utcnow()
    mapping = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
    hours = mapping.get(time_range)
    if hours:
      cutoff = now - datetime.timedelta(hours=hours)
      query = query.filter(Render.created_at >= cutoff)

  for col, pmin, pmax in [
      (Render.duration_seconds, "min_duration", "max_duration"),
      (Render.file_size_mb, "min_size", "max_size"),
      (Render.tokens_used, "min_credits", "max_credits"),
  ]:
    v = params.get(pmin)
    if v is not None:
      try:
        query = query.filter(col >= float(v))
      except (ValueError, TypeError):
        pass
    v = params.get(pmax)
    if v is not None:
      try:
        query = query.filter(col <= float(v))
      except (ValueError, TypeError):
        pass

  if params.get("errors_only") in ("true", "1", True):
    query = query.filter(Render.error_code.isnot(None))

  if params.get("webhook_failures") in ("true", "1", True):
    query = query.filter(Render.webhook_failures_count > 0)

  return query


# ---------------------------------------------------------------------------
# List renders (paginated + filtered)
# ---------------------------------------------------------------------------

@router.get("/renders")
async def list_renders(
    request: Request,
    q: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    user: Optional[str] = None,
    time_range: Optional[str] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    min_size: Optional[float] = None,
    max_size: Optional[float] = None,
    min_credits: Optional[int] = None,
    max_credits: Optional[int] = None,
    errors_only: bool = False,
    webhook_failures: bool = False,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(0, ge=0, le=10000),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Return paginated, filtered list of renders."""
  params = {
      "q": q, "status": status, "source": source, "user": user,
      "time_range": time_range,
      "min_duration": min_duration, "max_duration": max_duration,
      "min_size": min_size, "max_size": max_size,
      "min_credits": min_credits, "max_credits": max_credits,
      "errors_only": errors_only, "webhook_failures": webhook_failures,
  }

  base = db.query(Render)
  base = _apply_filters(base, params)

  # Sorting
  allowed_sort = {
      "created_at": Render.created_at,
      "status": Render.status,
      "duration_seconds": Render.duration_seconds,
      "file_size_mb": Render.file_size_mb,
      "tokens_used": Render.tokens_used,
      "user_email": Render.user_email,
  }
  sort_col = allowed_sort.get(sort_by, Render.created_at)
  if sort_dir == "asc":
    base = base.order_by(sort_col.asc())
  else:
    base = base.order_by(sort_col.desc())

  total = base.count()

  if page_size == 0:
    # Return all renders (no pagination)
    renders = base.all()
  else:
    renders = base.offset((page - 1) * page_size).limit(page_size).all()

  return JSONResponse({
      "renders": [_render_to_dict(r) for r in renders],
      "total": total,
      "page": page,
      "page_size": page_size if page_size > 0 else total,
  })


# ---------------------------------------------------------------------------
# Render detail
# ---------------------------------------------------------------------------

@router.get("/renders/{render_id}")
async def get_render(
    render_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Return full detail for a single render."""
  render = db.query(Render).filter(Render.render_id == render_id).first()
  if not render:
    raise HTTPException(status_code=404, detail="Render not found")
  return JSONResponse(_render_to_dict(render))


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

@router.post("/renders/{render_id}/rerun")
async def rerun_render(
    render_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Re-queue a render with the same inputs."""
  original = db.query(Render).filter(Render.render_id == render_id).first()
  if not original:
    raise HTTPException(status_code=404, detail="Render not found")

  import uuid
  new_render = Render(
      render_id=str(uuid.uuid4())[:8],
      status="queued",
      progress_pct=0,
      user_id=original.user_id,
      user_email=original.user_email,
      user_name=original.user_name,
      source_type=original.source_type,
      source_ref=original.source_ref,
      input_assets=original.input_assets,
      prompt_text=original.prompt_text,
      brand_guide=original.brand_guide,
      config_json=original.config_json,
      duration_seconds=original.duration_seconds,
      file_size_mb=original.file_size_mb,
      pipeline_version=original.pipeline_version,
      model=original.model,
      tokens_estimated=original.tokens_estimated,
  )
  db.add(new_render)
  db.commit()
  return JSONResponse({
      "status": "queued",
      "render_id": new_render.render_id,
      "message": f"Re-queued from {render_id}",
  })


@router.post("/renders/{render_id}/cancel")
async def cancel_render(
    render_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Cancel a render in progress."""
  render = db.query(Render).filter(Render.render_id == render_id).first()
  if not render:
    raise HTTPException(status_code=404, detail="Render not found")
  if render.status not in ("queued", "rendering"):
    raise HTTPException(
        status_code=400,
        detail=f"Cannot cancel render with status '{render.status}'",
    )
  render.status = "canceled"
  render.finished_at = datetime.datetime.utcnow()
  db.commit()
  return JSONResponse({"status": "canceled", "render_id": render_id})


@router.post("/renders/{render_id}/refund")
async def refund_render(
    render_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Refund credits for a render."""
  render = db.query(Render).filter(Render.render_id == render_id).first()
  if not render:
    raise HTTPException(status_code=404, detail="Render not found")
  if not render.tokens_used or render.tokens_used <= 0:
    raise HTTPException(status_code=400, detail="No credits to refund")

  user = db.query(User).filter(User.id == render.user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="User not found")

  user.credits_balance += render.tokens_used
  tx = CreditTransaction(
      user_id=user.id,
      type="grant",
      amount=render.tokens_used,
      reason=f"admin_refund_{render_id}",
      job_id=render_id,
  )
  db.add(tx)

  refunded = render.tokens_used
  render.tokens_used = 0
  db.commit()

  logging.info(
      "Admin refunded %d credits to %s for render %s",
      refunded, user.email, render_id,
  )
  return JSONResponse({
      "status": "refunded",
      "credits_refunded": refunded,
      "new_balance": user.credits_balance,
  })


@router.delete("/renders/{render_id}/output")
async def delete_output(
    render_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Delete output artifacts for a render."""
  render = db.query(Render).filter(Render.render_id == render_id).first()
  if not render:
    raise HTTPException(status_code=404, detail="Render not found")

  render.output_url = None
  render.thumbnail_url = None
  db.commit()

  logging.info("Admin deleted output for render %s", render_id)
  return JSONResponse({"status": "deleted", "render_id": render_id})


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------

@router.get("/renders/export")
async def export_renders(
    request: Request,
    q: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    user: Optional[str] = None,
    time_range: Optional[str] = None,
    errors_only: bool = False,
    webhook_failures: bool = False,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Export filtered renders as CSV."""
  params = {
      "q": q, "status": status, "source": source, "user": user,
      "time_range": time_range,
      "errors_only": errors_only, "webhook_failures": webhook_failures,
  }
  base = db.query(Render).order_by(Render.created_at.desc())
  base = _apply_filters(base, params)
  renders = base.all()

  output = io.StringIO()
  writer = csv.writer(output)
  header = [
      "render_id", "status", "created_at", "user_email",
      "source_type", "source_ref", "duration_seconds", "file_size_mb",
      "pipeline_version", "model", "tokens_estimated", "tokens_used",
      "error_code", "error_message",
  ]
  writer.writerow(header)
  for r in renders:
    writer.writerow([
        r.render_id, r.status,
        r.created_at.isoformat() if r.created_at else "",
        r.user_email, r.source_type, r.source_ref,
        r.duration_seconds, r.file_size_mb,
        r.pipeline_version, r.model,
        r.tokens_estimated, r.tokens_used,
        r.error_code or "", r.error_message or "",
    ])

  output.seek(0)
  return StreamingResponse(
      output,
      media_type="text/csv",
      headers={
          "Content-Disposition": "attachment; filename=renders_export.csv",
      },
  )


# ---------------------------------------------------------------------------
# Bulk actions
# ---------------------------------------------------------------------------

@router.post("/renders/bulk")
async def bulk_action(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Perform bulk actions on multiple renders.

  Body: {"action": "rerun"|"refund"|"delete_output", "render_ids": [...]}
  """
  body = await request.json()
  action = body.get("action")
  render_ids = body.get("render_ids", [])

  if not render_ids:
    raise HTTPException(status_code=400, detail="No render_ids provided")
  if action not in ("rerun", "refund", "delete_output"):
    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

  results = []
  for rid in render_ids:
    render = db.query(Render).filter(Render.render_id == rid).first()
    if not render:
      results.append({"render_id": rid, "status": "not_found"})
      continue

    if action == "rerun":
      import uuid
      new = Render(
          render_id=str(uuid.uuid4())[:8],
          status="queued",
          user_id=render.user_id,
          user_email=render.user_email,
          user_name=render.user_name,
          source_type=render.source_type,
          source_ref=render.source_ref,
          input_assets=render.input_assets,
          prompt_text=render.prompt_text,
          brand_guide=render.brand_guide,
          config_json=render.config_json,
          pipeline_version=render.pipeline_version,
          model=render.model,
          tokens_estimated=render.tokens_estimated,
      )
      db.add(new)
      results.append({
          "render_id": rid, "status": "requeued",
          "new_render_id": new.render_id,
      })

    elif action == "refund":
      if render.tokens_used and render.tokens_used > 0:
        user_obj = db.query(User).filter(User.id == render.user_id).first()
        if user_obj:
          user_obj.credits_balance += render.tokens_used
          tx = CreditTransaction(
              user_id=user_obj.id,
              type="grant",
              amount=render.tokens_used,
              reason=f"admin_bulk_refund_{rid}",
              job_id=rid,
          )
          db.add(tx)
          refunded = render.tokens_used
          render.tokens_used = 0
          results.append({
              "render_id": rid, "status": "refunded",
              "credits": refunded,
          })
        else:
          results.append({"render_id": rid, "status": "user_not_found"})
      else:
        results.append({"render_id": rid, "status": "nothing_to_refund"})

    elif action == "delete_output":
      render.output_url = None
      render.thumbnail_url = None
      results.append({"render_id": rid, "status": "deleted"})

  db.commit()
  return JSONResponse({"action": action, "results": results})


# ---------------------------------------------------------------------------
# Grant tokens to a user
# ---------------------------------------------------------------------------

@router.post("/users/grant")
async def grant_tokens(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
  """Grant tokens to a user by email.

  Body: {"email": "...", "amount": 10000, "reason": "..."}
  """
  body = await request.json()
  email = body.get("email", "").strip()
  amount = body.get("amount", 0)
  reason = body.get("reason", "admin_grant")

  if not email:
    raise HTTPException(status_code=400, detail="Email is required")
  if not isinstance(amount, int) or amount <= 0:
    raise HTTPException(status_code=400, detail="Amount must be a positive integer")

  user = db.query(User).filter(User.email == email).first()
  if not user:
    raise HTTPException(status_code=404, detail=f"User {email} not found")

  user.credits_balance += amount
  tx = CreditTransaction(
      user_id=user.id,
      type="grant",
      amount=amount,
      reason=reason,
  )
  db.add(tx)
  db.commit()
  db.refresh(user)

  logging.info(
      "Admin granted %d credits to %s (new balance: %d)",
      amount, email, user.credits_balance,
  )
  return JSONResponse({
      "status": "granted",
      "email": email,
      "amount": amount,
      "new_balance": user.credits_balance,
  })
