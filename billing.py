"""Stripe billing: checkout sessions and webhook fulfillment."""

import logging
import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from credits import TOKEN_PACKS
from db import CreditTransaction, ProcessedStripeEvent, User, get_db

router = APIRouter(tags=["billing"])

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

stripe.api_key = STRIPE_SECRET_KEY


def create_stripe_customer(user: User, db: Session) -> str:
  """Create a Stripe customer for a user (idempotent).

  Returns the stripe_customer_id.
  """
  if user.stripe_customer_id:
    return user.stripe_customer_id

  if not STRIPE_SECRET_KEY:
    logging.warning("STRIPE_SECRET_KEY not configured — skipping Stripe customer creation")
    return ""

  customer = stripe.Customer.create(
      email=user.email,
      metadata={"user_id": user.id},
  )
  user.stripe_customer_id = customer.id
  db.commit()
  logging.info("Created Stripe customer %s for user %s", customer.id, user.email)
  return customer.id


# ---------- Endpoints ----------


@router.get("/billing/packs")
async def list_packs(user: User = Depends(get_current_user)):
  """Return available token packs and current balance."""
  return JSONResponse({
      "credits_balance": user.credits_balance,
      "packs": [
          {
              "key": k,
              "usd": v["usd"],
              "tokens": v["tokens"],
              "available": bool(v["stripe_price_id"] and STRIPE_SECRET_KEY),
          }
          for k, v in TOKEN_PACKS.items()
      ],
  })


@router.get("/billing/history")
async def billing_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Return the user's credit transaction history."""
  txns = (
      db.query(CreditTransaction)
      .filter(CreditTransaction.user_id == user.id)
      .order_by(CreditTransaction.created_at.desc())
      .limit(100)
      .all()
  )
  return JSONResponse({
      "credits_balance": user.credits_balance,
      "transactions": [
          {
              "id": tx.id,
              "type": tx.type,
              "amount": tx.amount,
              "reason": tx.reason,
              "job_id": tx.job_id,
              "created_at": tx.created_at.isoformat() if tx.created_at else None,
          }
          for tx in txns
      ],
  })


@router.post("/billing/checkout-session")
async def create_checkout_session(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Create a Stripe Checkout Session for a token pack purchase."""
  if not STRIPE_SECRET_KEY:
    raise HTTPException(status_code=500, detail="Stripe not configured")

  body = await request.json()
  pack_key = body.get("pack", "")

  if pack_key not in TOKEN_PACKS:
    raise HTTPException(status_code=400, detail=f"Invalid pack: {pack_key}")

  pack = TOKEN_PACKS[pack_key]
  if not pack["stripe_price_id"]:
    raise HTTPException(
        status_code=500,
        detail=f"Stripe Price ID not configured for {pack_key}",
    )

  # Ensure Stripe customer exists
  customer_id = create_stripe_customer(user, db)
  if not customer_id:
    raise HTTPException(status_code=500, detail="Could not create Stripe customer")

  public_base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
  if not public_base:
    # Fall back to request URL, correcting for reverse proxy
    public_base = str(request.base_url).rstrip("/")
    if request.headers.get("x-forwarded-proto") == "https":
      public_base = public_base.replace("http://", "https://", 1)

  session = stripe.checkout.Session.create(
      customer=customer_id,
      line_items=[{
          "price": pack["stripe_price_id"],
          "quantity": 1,
      }],
      mode="payment",
      metadata={
          "user_id": user.id,
          "token_amount": str(pack["tokens"]),
          "pack": pack_key,
      },
      success_url=f"{public_base}/billing?billing=success",
      cancel_url=f"{public_base}/billing?billing=cancel",
  )

  return JSONResponse({"checkout_url": session.url})


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
  """Handle Stripe webhook events (no auth — signature verified)."""
  payload = await request.body()
  sig_header = request.headers.get("stripe-signature", "")

  if not STRIPE_WEBHOOK_SECRET:
    raise HTTPException(status_code=500, detail="Webhook secret not configured")

  # Verify signature
  try:
    event = stripe.Webhook.construct_event(
        payload, sig_header, STRIPE_WEBHOOK_SECRET,
    )
  except (stripe.error.SignatureVerificationError, stripe.SignatureVerificationError):
    logging.error("Stripe webhook signature verification failed")
    raise HTTPException(status_code=400, detail="Invalid signature")
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid payload")

  # Handle checkout.session.completed
  if event["type"] == "checkout.session.completed":
    session = event["data"]["object"]
    event_id = event["id"]
    session_id = session["id"]

    # Idempotency check
    existing = db.query(ProcessedStripeEvent).filter(
        ProcessedStripeEvent.stripe_event_id == event_id,
    ).first()
    if existing:
      logging.info("Stripe event %s already processed — skipping", event_id)
      return JSONResponse({"status": "already_processed"})

    # Extract metadata
    metadata = session.get("metadata", {})
    user_id = metadata.get("user_id")
    token_amount = int(metadata.get("token_amount", 0))
    pack_key = metadata.get("pack", "unknown")

    if not user_id or token_amount <= 0:
      logging.error(
          "Stripe webhook missing metadata: user_id=%s token_amount=%s",
          user_id, token_amount,
      )
      return JSONResponse({"status": "error", "detail": "missing metadata"}, status_code=400)

    # Credit the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
      logging.error("Stripe webhook: user %s not found", user_id)
      return JSONResponse({"status": "error", "detail": "user not found"}, status_code=400)

    user.credits_balance += token_amount

    # Log transaction
    tx = CreditTransaction(
        user_id=user.id,
        type="grant",
        amount=token_amount,
        reason=f"purchase_{pack_key}",
        job_id=session_id,
    )
    db.add(tx)

    # Record processed event
    processed = ProcessedStripeEvent(
        stripe_event_id=event_id,
        stripe_session_id=session_id,
    )
    db.add(processed)

    db.commit()
    logging.info(
        "Stripe webhook: credited %d tokens to user %s (balance: %d)",
        token_amount, user.email, user.credits_balance,
    )

  return JSONResponse({"status": "ok"})
