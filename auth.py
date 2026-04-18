"""Authentication: Google SSO + email/password for external users."""

from __future__ import annotations

import collections
import datetime
import logging
import os
import re
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import jwt
import requests
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
import bcrypt as _bcrypt
from sqlalchemy.orm import Session

import email_service
import notification_service
from db import CreditTransaction, User, get_db
from credits import token_model_info

# Lazy import to avoid circular dependency at module level
_billing_mod = None
def _get_billing():
  global _billing_mod
  if _billing_mod is None:
    import billing
    _billing_mod = billing
  return _billing_mod

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "change-me-in-production")
SESSION_COOKIE = "session_token"
SESSION_TTL_HOURS = 24

SIGNUP_CREDITS = 3000

# One-time bonus grants for specific accounts (email → extra tokens)
_BONUS_GRANTS: dict[str, int] = {
    "kevin@kwangel.fund": 10000,
}

MIN_PASSWORD_LENGTH = 8
VERIFICATION_TOKEN_TTL = datetime.timedelta(hours=24)
RESET_TOKEN_TTL = datetime.timedelta(hours=1)

# Common passwords blocklist (top-20)
_BLOCKED_PASSWORDS = {
    "password", "12345678", "123456789", "1234567890", "qwerty123",
    "password1", "iloveyou", "abcdefgh", "abc12345", "password123",
    "qwertyui", "letmein1", "trustno1", "sunshine1", "princess1",
    "football1", "charlie1", "shadow12", "master12", "welcome1",
}

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Simple in-memory rate limiter: {ip: deque of timestamps}
_rate_limit_window = 300  # 5 minutes
_rate_limit_max = 10  # max attempts per window
_rate_buckets: dict[str, collections.deque] = {}

# Account lockout: {email: (consecutive_failures, last_failure_time)}
_LOCKOUT_MAX_FAILURES = 5
_LOCKOUT_DURATION = 900  # 15 minutes
_login_failures: dict[str, tuple[int, float]] = {}

# ---------- Startup guards ----------
if SESSION_SECRET == "change-me-in-production":
  if os.environ.get("K_SERVICE"):
    raise RuntimeError(
        "SESSION_SECRET must be set in production. "
        "Generate one with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    )
  logging.warning(
      "\n" + "=" * 60 + "\n"
      "  WARNING: SESSION_SECRET is set to the default value!\n"
      "  Generate a secure key: python3 -c \"import secrets; print(secrets.token_hex(32))\"\n"
      + "=" * 60
  )
if not email_service.is_configured():
  logging.warning(
      "SMTP not configured — verification and password reset emails "
      "will be logged to console instead of sent."
  )


def _check_rate_limit(request: Request) -> None:
  """Raise 429 if the IP has exceeded the auth attempt rate limit."""
  ip = request.client.host if request.client else "unknown"
  now = time.time()
  bucket = _rate_buckets.setdefault(ip, collections.deque())
  # Evict old entries
  while bucket and bucket[0] < now - _rate_limit_window:
    bucket.popleft()
  if len(bucket) >= _rate_limit_max:
    raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
  bucket.append(now)


def _require_json(request: Request) -> None:
  """CSRF protection: reject requests without a JSON content type.

  HTML forms can only send application/x-www-form-urlencoded or
  multipart/form-data, so requiring application/json blocks cross-site
  form submissions.
  """
  ct = (request.headers.get("content-type") or "").lower()
  if "application/json" not in ct:
    raise HTTPException(
        status_code=415,
        detail="Content-Type must be application/json",
    )


def _check_account_lockout(email: str) -> None:
  """Raise 429 if the account is locked due to repeated failures."""
  entry = _login_failures.get(email)
  if not entry:
    return
  failures, last_time = entry
  if failures >= _LOCKOUT_MAX_FAILURES:
    elapsed = time.time() - last_time
    if elapsed < _LOCKOUT_DURATION:
      remaining = int(_LOCKOUT_DURATION - elapsed)
      raise HTTPException(
          status_code=429,
          detail=f"Account temporarily locked. Try again in {remaining // 60 + 1} minute(s).",
      )
    # Lockout expired — reset
    _login_failures.pop(email, None)


def _record_login_failure(email: str) -> None:
  """Record a failed login attempt for account lockout."""
  entry = _login_failures.get(email)
  failures = (entry[0] + 1) if entry else 1
  _login_failures[email] = (failures, time.time())


def _clear_login_failures(email: str) -> None:
  """Clear failure counter on successful login."""
  _login_failures.pop(email, None)


def _validate_password(password: str) -> Optional[str]:
  """Validate password strength. Returns error message or None if valid."""
  if len(password) < MIN_PASSWORD_LENGTH:
    return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
  if not re.search(r"[a-zA-Z]", password):
    return "Password must contain at least one letter"
  if not re.search(r"[0-9]", password):
    return "Password must contain at least one number"
  if password.lower() in _BLOCKED_PASSWORDS:
    return "This password is too common. Please choose a stronger one."
  return None


def _build_base_url(request: Request) -> str:
  """Build the public base URL from the current request."""
  base = str(request.base_url).rstrip("/")
  if request.headers.get("x-forwarded-proto") == "https":
    base = base.replace("http://", "https://", 1)
  return base


def _build_redirect_uri(request: Request) -> str:
  """Build the OAuth callback URL from the current request.

  On Cloud Run / behind a reverse proxy, request.base_url may report
  http:// even though the public URL is https://. We check the
  X-Forwarded-Proto header and force https when appropriate.
  """
  return f"{_build_base_url(request)}/auth/callback"


def _create_session_token(user: User) -> str:
  """Create a signed JWT session token for the user."""
  payload = {
      "sub": user.id,
      "email": user.email,
      "exp": datetime.datetime.utcnow()
      + datetime.timedelta(hours=SESSION_TTL_HOURS),
  }
  return jwt.encode(payload, SESSION_SECRET, algorithm="HS256")


def _decode_session_token(token: str) -> Optional[dict]:
  """Decode and validate a session JWT. Returns payload or None."""
  try:
    return jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])
  except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
  """FastAPI dependency: extract and validate the session cookie.

  Returns the User object or raises 401.
  """
  token = request.cookies.get(SESSION_COOKIE)
  if not token:
    raise HTTPException(status_code=401, detail="Not authenticated")

  payload = _decode_session_token(token)
  if not payload:
    raise HTTPException(status_code=401, detail="Invalid or expired session")

  user = db.query(User).filter(User.id == payload["sub"]).first()
  if not user:
    raise HTTPException(status_code=401, detail="User not found")

  return user


# ---------- Endpoints ----------


@router.get("/config")
async def auth_config():
  """Return auth configuration so the frontend can adapt."""
  return JSONResponse({
      "google_enabled": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
  })


@router.get("/login")
async def login(request: Request):
  """Redirect to Google OAuth consent screen."""
  if not GOOGLE_CLIENT_ID:
    return RedirectResponse("/?auth_error=google_not_configured")

  params = {
      "client_id": GOOGLE_CLIENT_ID,
      "redirect_uri": _build_redirect_uri(request),
      "response_type": "code",
      "scope": "openid email profile",
      "access_type": "offline",
      "prompt": "select_account",
  }
  return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
  """Handle Google OAuth callback — exchange code, validate, upsert user."""
  if error:
    return RedirectResponse(f"/?auth_error={error}")
  if not code:
    return RedirectResponse("/?auth_error=missing_code")

  # 1) Exchange authorization code for tokens
  redirect_uri = _build_redirect_uri(request)
  token_resp = requests.post(
      GOOGLE_TOKEN_URL,
      data={
          "code": code,
          "client_id": GOOGLE_CLIENT_ID,
          "client_secret": GOOGLE_CLIENT_SECRET,
          "redirect_uri": redirect_uri,
          "grant_type": "authorization_code",
      },
      timeout=10,
  )
  if token_resp.status_code != 200:
    logging.error("Token exchange failed: %s", token_resp.text)
    return RedirectResponse("/?auth_error=token_exchange_failed")

  tokens = token_resp.json()
  raw_id_token = tokens.get("id_token")
  if not raw_id_token:
    return RedirectResponse("/?auth_error=no_id_token")

  # 2) Validate the ID token
  try:
    id_info = google_id_token.verify_oauth2_token(
        raw_id_token, GoogleRequest(), GOOGLE_CLIENT_ID
    )
  except ValueError as ex:
    logging.error("ID token validation failed: %s", ex)
    return RedirectResponse("/?auth_error=invalid_token")

  # Verify issuer
  if id_info.get("iss") not in (
      "accounts.google.com",
      "https://accounts.google.com",
  ):
    return RedirectResponse("/?auth_error=invalid_issuer")

  # Verify email_verified
  if not id_info.get("email_verified"):
    return RedirectResponse("/?auth_error=email_not_verified")

  email = id_info.get("email", "")
  google_sub = id_info.get("sub", "")

  # 3) Upsert user — check by google_sub first, then by email (account linking)
  user = db.query(User).filter(User.google_sub == google_sub).first()
  now = datetime.datetime.utcnow()

  if user:
    # Returning Google user — update last_login
    user.email_verified = True
    user.last_login = now
    db.commit()
  else:
    # Check if an email/password user already exists with this email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
      # Link Google identity to existing account
      existing.google_sub = google_sub
      existing.email_verified = True
      existing.last_login = now
      db.commit()
      user = existing
      logging.info("Linked Google account to existing user: %s", email)
    else:
      # Brand-new user — create with signup credits
      user = User(
          google_sub=google_sub,
          email=email,
          email_verified=True,
          credits_balance=SIGNUP_CREDITS,
          created_at=now,
          updated_at=now,
          last_login=now,
      )
      db.add(user)
      db.flush()  # get user.id

      # Log signup bonus
      tx = CreditTransaction(
          user_id=user.id,
          type="grant",
          amount=SIGNUP_CREDITS,
          reason="signup_bonus",
      )
      db.add(tx)

      # One-time bonus for specific accounts
      bonus = _BONUS_GRANTS.pop(email, 0)
      if bonus:
        user.credits_balance += bonus
        bonus_tx = CreditTransaction(
            user_id=user.id,
            type="grant",
            amount=bonus,
            reason="admin_manual_grant",
        )
        db.add(bonus_tx)
        logging.info("Granted %d bonus credits to %s", bonus, email)

      db.commit()
      logging.info("New user created: %s (%s)", email, user.id)

      # Create Stripe customer (best-effort, non-blocking)
      try:
        _get_billing().create_stripe_customer(user, db)
      except Exception as ex:
        logging.warning("Stripe customer creation failed (non-fatal): %s", ex)

      # Notify admin of new signup (Slack + email, non-blocking)
      notification_service.notify_new_signup(email, method="google")

  # 5) Issue session cookie and redirect to app
  session_token = _create_session_token(user)
  response = RedirectResponse("/", status_code=302)
  response.set_cookie(
      key=SESSION_COOKIE,
      value=session_token,
      httponly=True,
      secure=True,
      samesite="lax",
      max_age=SESSION_TTL_HOURS * 3600,
  )
  return response


@router.post("/logout")
async def logout():
  """Clear the session cookie."""
  response = JSONResponse({"status": "logged_out"})
  response.delete_cookie(SESSION_COOKIE)
  return response


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
  """Return current authenticated user data."""
  return JSONResponse({
      "user": {
          "id": user.id,
          "email": user.email,
          "email_verified": user.email_verified,
          "has_google": user.google_sub is not None,
          "credits_balance": user.credits_balance,
          "created_at": user.created_at.isoformat() if user.created_at else None,
          "token_model": token_model_info(),
      }
  })


# ---------- Email/Password Endpoints ----------


@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
  """Register a new user with email and password."""
  _require_json(request)
  _check_rate_limit(request)

  body = await request.json()
  email = (body.get("email") or "").strip().lower()
  password = body.get("password") or ""

  if not email or "@" not in email or "." not in email.split("@")[-1]:
    raise HTTPException(status_code=400, detail="Valid email is required")
  pw_error = _validate_password(password)
  if pw_error:
    raise HTTPException(status_code=400, detail=pw_error)

  # Check for existing user
  existing = db.query(User).filter(User.email == email).first()
  if existing:
    raise HTTPException(status_code=409, detail="An account with this email already exists")

  now = datetime.datetime.utcnow()
  verification_token = secrets.token_urlsafe(32)

  user = User(
      email=email,
      password_hash=_bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode(),
      email_verified=False,
      verification_token=verification_token,
      token_expires_at=now + VERIFICATION_TOKEN_TTL,
      credits_balance=SIGNUP_CREDITS,
      created_at=now,
      updated_at=now,
      last_login=now,
  )
  db.add(user)
  db.flush()

  # Log signup bonus
  tx = CreditTransaction(
      user_id=user.id,
      type="grant",
      amount=SIGNUP_CREDITS,
      reason="signup_bonus",
  )
  db.add(tx)

  # One-time bonus for specific accounts
  bonus = _BONUS_GRANTS.pop(email, 0)
  if bonus:
    user.credits_balance += bonus
    bonus_tx = CreditTransaction(
        user_id=user.id,
        type="grant",
        amount=bonus,
        reason="admin_manual_grant",
    )
    db.add(bonus_tx)

  db.commit()
  logging.info("New email/password user registered: %s (%s)", email, user.id)

  # Create Stripe customer (best-effort)
  try:
    _get_billing().create_stripe_customer(user, db)
  except Exception as ex:
    logging.warning("Stripe customer creation failed (non-fatal): %s", ex)

  # Notify admin of new signup (Slack + email, non-blocking)
  notification_service.notify_new_signup(email, method="email")

  # Send verification email (best-effort)
  verify_url = f"{_build_base_url(request)}/auth/verify-email?token={verification_token}"
  email_service.send_verification_email(email, verify_url)

  # Issue session cookie immediately
  session_token = _create_session_token(user)
  response = JSONResponse(
      {"status": "registered", "email": email},
      status_code=201,
  )
  response.set_cookie(
      key=SESSION_COOKIE,
      value=session_token,
      httponly=True,
      secure=True,
      samesite="lax",
      max_age=SESSION_TTL_HOURS * 3600,
  )
  return response


@router.post("/login/email")
async def login_email(request: Request, db: Session = Depends(get_db)):
  """Authenticate with email and password."""
  _require_json(request)
  _check_rate_limit(request)

  body = await request.json()
  email = (body.get("email") or "").strip().lower()
  password = body.get("password") or ""

  if not email or not password:
    raise HTTPException(status_code=400, detail="Email and password are required")

  _check_account_lockout(email)

  user = db.query(User).filter(User.email == email).first()
  if not user or not user.password_hash:
    _record_login_failure(email)
    raise HTTPException(status_code=401, detail="Invalid email or password")

  if not _bcrypt.checkpw(password.encode(), user.password_hash.encode()):
    _record_login_failure(email)
    raise HTTPException(status_code=401, detail="Invalid email or password")

  _clear_login_failures(email)
  user.last_login = datetime.datetime.utcnow()
  db.commit()

  session_token = _create_session_token(user)
  response = JSONResponse({"status": "ok"})
  response.set_cookie(
      key=SESSION_COOKIE,
      value=session_token,
      httponly=True,
      secure=True,
      samesite="lax",
      max_age=SESSION_TTL_HOURS * 3600,
  )
  return response


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
  """Verify a user's email address via token."""
  if not token:
    return RedirectResponse("/?auth_error=missing_token")

  user = db.query(User).filter(User.verification_token == token).first()
  if not user:
    return RedirectResponse("/?auth_error=invalid_verification_token")

  # Check expiry
  now = datetime.datetime.utcnow()
  if user.token_expires_at and now > user.token_expires_at:
    return RedirectResponse("/?auth_error=token_expired")

  user.email_verified = True
  user.verification_token = None
  user.token_expires_at = None
  db.commit()

  logging.info("Email verified for user: %s", user.email)
  return RedirectResponse("/?email_verified=true")


@router.post("/forgot-password")
async def forgot_password(request: Request, db: Session = Depends(get_db)):
  """Send a password reset email.

  Always returns 200 to prevent email enumeration.
  """
  _require_json(request)
  _check_rate_limit(request)

  body = await request.json()
  email = (body.get("email") or "").strip().lower()

  # Always return success to prevent email enumeration
  success_msg = {"status": "ok", "message": "If that email exists, a reset link has been sent."}

  if not email or "@" not in email:
    return JSONResponse(success_msg)

  user = db.query(User).filter(User.email == email).first()
  if not user or not user.password_hash:
    # No user or Google-only user — silently do nothing
    return JSONResponse(success_msg)

  now = datetime.datetime.utcnow()
  reset_token = secrets.token_urlsafe(32)
  user.reset_token = reset_token
  user.token_expires_at = now + RESET_TOKEN_TTL
  db.commit()

  reset_url = f"{_build_base_url(request)}/reset-password?token={reset_token}"
  email_service.send_password_reset_email(email, reset_url)

  logging.info("Password reset requested for: %s", email)
  return JSONResponse(success_msg)


@router.post("/reset-password")
async def reset_password(request: Request, db: Session = Depends(get_db)):
  """Reset password using a valid reset token."""
  _require_json(request)
  _check_rate_limit(request)

  body = await request.json()
  token = (body.get("token") or "").strip()
  password = body.get("password") or ""

  if not token:
    raise HTTPException(status_code=400, detail="Reset token is required")

  pw_error = _validate_password(password)
  if pw_error:
    raise HTTPException(status_code=400, detail=pw_error)

  user = db.query(User).filter(User.reset_token == token).first()
  if not user:
    raise HTTPException(status_code=400, detail="Invalid or expired reset link")

  # Check expiry
  now = datetime.datetime.utcnow()
  if user.token_expires_at and now > user.token_expires_at:
    user.reset_token = None
    user.token_expires_at = None
    db.commit()
    raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")

  user.password_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
  user.reset_token = None
  user.token_expires_at = None
  db.commit()

  logging.info("Password reset completed for: %s", user.email)
  return JSONResponse({"status": "ok", "message": "Password has been reset. You can now sign in."})


@router.get("/transactions")
async def transactions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
  """Return paginated credit transaction history for the current user."""
  limit = min(limit, 100)  # cap at 100
  offset = max(offset, 0)

  txs = (
      db.query(CreditTransaction)
      .filter(CreditTransaction.user_id == user.id)
      .order_by(CreditTransaction.created_at.desc())
      .offset(offset)
      .limit(limit)
      .all()
  )

  total = (
      db.query(CreditTransaction)
      .filter(CreditTransaction.user_id == user.id)
      .count()
  )

  return JSONResponse({
      "transactions": [
          {
              "id": tx.id,
              "type": tx.type,
              "amount": tx.amount,
              "reason": tx.reason,
              "job_id": tx.job_id,
              "created_at": tx.created_at.isoformat() if tx.created_at else None,
          }
          for tx in txs
      ],
      "total": total,
      "limit": limit,
      "offset": offset,
  })
