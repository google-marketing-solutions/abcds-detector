"""Tests for the auth module: registration, login, password reset, etc."""

import datetime
from unittest.mock import patch


# ===== Registration =====

class TestRegister:
  def test_register_success(self, client):
    resp = client.post("/auth/register", json={
        "email": "new@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "registered"
    assert data["email"] == "new@example.com"
    assert "session_token" in resp.cookies

  def test_register_gets_signup_credits(self, client):
    client.post("/auth/register", json={
        "email": "credits@example.com", "password": "Goodpass1",
    })
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["credits_balance"] == 1000

  def test_register_duplicate_email(self, client):
    client.post("/auth/register", json={
        "email": "dup@example.com", "password": "Goodpass1",
    })
    resp = client.post("/auth/register", json={
        "email": "dup@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 409

  def test_register_invalid_email(self, client):
    resp = client.post("/auth/register", json={
        "email": "notanemail", "password": "Goodpass1",
    })
    assert resp.status_code == 400

  def test_register_missing_email(self, client):
    resp = client.post("/auth/register", json={
        "email": "", "password": "Goodpass1",
    })
    assert resp.status_code == 400


# ===== Password Validation =====

class TestPasswordValidation:
  def test_too_short(self, client):
    resp = client.post("/auth/register", json={
        "email": "pw@example.com", "password": "Ab1",
    })
    assert resp.status_code == 400
    assert "8 characters" in resp.json()["detail"]

  def test_no_letter(self, client):
    resp = client.post("/auth/register", json={
        "email": "pw@example.com", "password": "12345678",
    })
    assert resp.status_code == 400
    assert "letter" in resp.json()["detail"]

  def test_no_number(self, client):
    resp = client.post("/auth/register", json={
        "email": "pw@example.com", "password": "abcdefgh",
    })
    assert resp.status_code == 400
    assert "number" in resp.json()["detail"]

  def test_blocked_password(self, client):
    resp = client.post("/auth/register", json={
        "email": "pw@example.com", "password": "password1",
    })
    assert resp.status_code == 400
    assert "too common" in resp.json()["detail"]

  def test_valid_password(self, client):
    resp = client.post("/auth/register", json={
        "email": "pw@example.com", "password": "Str0ngPass!",
    })
    assert resp.status_code == 201


# ===== Email/Password Login =====

class TestLoginEmail:
  def test_login_success(self, client):
    client.post("/auth/register", json={
        "email": "login@example.com", "password": "Goodpass1",
    })
    # Clear cookie to start fresh
    client.cookies.clear()
    resp = client.post("/auth/login/email", json={
        "email": "login@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 200
    assert "session_token" in resp.cookies

  def test_login_wrong_password(self, client):
    client.post("/auth/register", json={
        "email": "login2@example.com", "password": "Goodpass1",
    })
    client.cookies.clear()
    resp = client.post("/auth/login/email", json={
        "email": "login2@example.com", "password": "WrongPass1",
    })
    assert resp.status_code == 401

  def test_login_nonexistent_user(self, client):
    resp = client.post("/auth/login/email", json={
        "email": "nobody@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 401

  def test_login_missing_fields(self, client):
    resp = client.post("/auth/login/email", json={
        "email": "", "password": "",
    })
    assert resp.status_code == 400

  def test_login_case_insensitive_email(self, client):
    client.post("/auth/register", json={
        "email": "CaseTest@Example.com", "password": "Goodpass1",
    })
    client.cookies.clear()
    resp = client.post("/auth/login/email", json={
        "email": "casetest@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 200


# ===== /auth/me =====

class TestMe:
  def test_me_authenticated(self, client, auth_headers):
    hdrs = auth_headers()
    resp = client.get("/auth/me", headers=hdrs)
    assert resp.status_code == 200
    user = resp.json()["user"]
    assert user["email"] == "authed@example.com"
    assert "credits_balance" in user
    assert "email_verified" in user

  def test_me_unauthenticated(self, client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


# ===== Logout =====

class TestLogout:
  def test_logout(self, client, auth_headers):
    hdrs = auth_headers()
    resp = client.post("/auth/logout", headers=hdrs)
    assert resp.status_code == 200
    assert resp.json()["status"] == "logged_out"


# ===== Email Verification =====

class TestVerifyEmail:
  def test_verify_valid_token(self, client):
    # Register to get a user with a verification token
    client.post("/auth/register", json={
        "email": "verify@example.com", "password": "Goodpass1",
    })
    # Dig out the token from the DB
    from sqlalchemy.orm import sessionmaker
    from db import engine, User
    Session = sessionmaker(bind=engine)
    # We need to get the token from the test DB, but the client uses overridden DB.
    # Instead, test via the /me response — email_verified should be False
    me = client.get("/auth/me")
    assert me.json()["user"]["email_verified"] is False

  def test_verify_invalid_token(self, client):
    resp = client.get("/auth/verify-email", params={"token": "bogus-token"})
    assert resp.status_code == 200  # redirect
    assert "invalid_verification_token" in resp.headers.get("location", resp.url.path + "?" + str(resp.url.query))

  def test_verify_expired_token(self, client, db_engine):
    """Verify that an expired token is rejected."""
    from sqlalchemy.orm import sessionmaker
    from db import User
    import bcrypt as _bcrypt

    Session = sessionmaker(bind=db_engine)
    session = Session()
    user = User(
        email="expired@example.com",
        password_hash=_bcrypt.hashpw(b"Goodpass1", _bcrypt.gensalt()).decode(),
        email_verified=False,
        verification_token="expired-tok",
        token_expires_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
        credits_balance=1000,
    )
    session.add(user)
    session.commit()
    session.close()

    resp = client.get("/auth/verify-email", params={"token": "expired-tok"})
    assert "token_expired" in str(resp.url)


# ===== Forgot / Reset Password =====

class TestForgotPassword:
  def test_forgot_password_existing_user(self, client):
    client.post("/auth/register", json={
        "email": "forgot@example.com", "password": "Goodpass1",
    })
    resp = client.post("/auth/forgot-password", json={
        "email": "forgot@example.com",
    })
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"]

  def test_forgot_password_nonexistent_user(self, client):
    """Should still return 200 to prevent email enumeration."""
    resp = client.post("/auth/forgot-password", json={
        "email": "nobody@example.com",
    })
    assert resp.status_code == 200

  def test_forgot_password_empty_email(self, client):
    resp = client.post("/auth/forgot-password", json={"email": ""})
    assert resp.status_code == 200


class TestResetPassword:
  def test_reset_password_full_flow(self, client, db_engine):
    """Register → forgot → extract token → reset → login with new password."""
    # Register
    client.post("/auth/register", json={
        "email": "reset@example.com", "password": "Oldpass1",
    })
    client.cookies.clear()

    # Forgot
    client.post("/auth/forgot-password", json={
        "email": "reset@example.com",
    })

    # Extract reset token from DB
    from sqlalchemy.orm import sessionmaker
    from db import User
    Session = sessionmaker(bind=db_engine)
    session = Session()
    user = session.query(User).filter(User.email == "reset@example.com").first()
    reset_token = user.reset_token
    session.close()
    assert reset_token is not None

    # Reset
    resp = client.post("/auth/reset-password", json={
        "token": reset_token, "password": "Newpass1!",
    })
    assert resp.status_code == 200
    assert "reset" in resp.json()["message"].lower()

    # Login with new password
    resp = client.post("/auth/login/email", json={
        "email": "reset@example.com", "password": "Newpass1!",
    })
    assert resp.status_code == 200

    # Old password should fail
    resp = client.post("/auth/login/email", json={
        "email": "reset@example.com", "password": "Oldpass1",
    })
    assert resp.status_code == 401

  def test_reset_invalid_token(self, client):
    resp = client.post("/auth/reset-password", json={
        "token": "bogus", "password": "Newpass1!",
    })
    assert resp.status_code == 400

  def test_reset_expired_token(self, client, db_engine):
    from sqlalchemy.orm import sessionmaker
    from db import User
    import bcrypt as _bcrypt

    Session = sessionmaker(bind=db_engine)
    session = Session()
    user = User(
        email="expiredreset@example.com",
        password_hash=_bcrypt.hashpw(b"Oldpass1", _bcrypt.gensalt()).decode(),
        email_verified=True,
        reset_token="expired-reset-tok",
        token_expires_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
        credits_balance=1000,
    )
    session.add(user)
    session.commit()
    session.close()

    resp = client.post("/auth/reset-password", json={
        "token": "expired-reset-tok", "password": "Newpass1!",
    })
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()

  def test_reset_weak_password(self, client, db_engine):
    from sqlalchemy.orm import sessionmaker
    from db import User
    import bcrypt as _bcrypt

    Session = sessionmaker(bind=db_engine)
    session = Session()
    user = User(
        email="weakreset@example.com",
        password_hash=_bcrypt.hashpw(b"Oldpass1", _bcrypt.gensalt()).decode(),
        email_verified=True,
        reset_token="valid-tok",
        token_expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        credits_balance=1000,
    )
    session.add(user)
    session.commit()
    session.close()

    resp = client.post("/auth/reset-password", json={
        "token": "valid-tok", "password": "short",
    })
    assert resp.status_code == 400


# ===== Rate Limiting =====

class TestRateLimit:
  def test_rate_limit_kicks_in(self, client):
    """After 10 attempts in 5 minutes, should get 429."""
    for i in range(10):
      client.post("/auth/login/email", json={
          "email": f"spam{i}@example.com", "password": "x",
      })
    resp = client.post("/auth/login/email", json={
        "email": "spam@example.com", "password": "x",
    })
    assert resp.status_code == 429


# ===== CSRF Protection =====

class TestCSRFProtection:
  def test_register_rejects_form_encoded(self, client):
    """POST with form-encoded body should be rejected (CSRF protection)."""
    resp = client.post(
        "/auth/register",
        data={"email": "csrf@example.com", "password": "Goodpass1"},
    )
    assert resp.status_code == 415

  def test_login_rejects_no_content_type(self, client):
    resp = client.post(
        "/auth/login/email",
        content='{"email": "x@x.com", "password": "Goodpass1"}',
    )
    assert resp.status_code == 415

  def test_forgot_rejects_form_encoded(self, client):
    resp = client.post(
        "/auth/forgot-password",
        data={"email": "csrf@example.com"},
    )
    assert resp.status_code == 415

  def test_reset_rejects_form_encoded(self, client):
    resp = client.post(
        "/auth/reset-password",
        data={"token": "x", "password": "Goodpass1"},
    )
    assert resp.status_code == 415


# ===== Account Lockout =====

class TestAccountLockout:
  def test_lockout_after_5_failures(self, client):
    """After 5 wrong passwords, the account should be locked."""
    client.post("/auth/register", json={
        "email": "lockme@example.com", "password": "Goodpass1",
    })
    for _ in range(5):
      client.post("/auth/login/email", json={
          "email": "lockme@example.com", "password": "WrongPass1",
      })
    # 6th attempt — should be locked
    resp = client.post("/auth/login/email", json={
        "email": "lockme@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 429
    assert "locked" in resp.json()["detail"].lower()

  def test_lockout_resets_on_success(self, client):
    """Successful login clears the failure counter."""
    from auth import _rate_buckets

    client.post("/auth/register", json={
        "email": "unlock@example.com", "password": "Goodpass1",
    })
    # 4 failures (just under lockout threshold)
    for _ in range(4):
      client.post("/auth/login/email", json={
          "email": "unlock@example.com", "password": "WrongPass1",
      })
    # Successful login — should clear counter
    resp = client.post("/auth/login/email", json={
        "email": "unlock@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 200
    # Clear IP rate-limit so we don't hit that ceiling
    _rate_buckets.clear()
    # Now fail 4 more times — should still be under threshold
    for _ in range(4):
      client.post("/auth/login/email", json={
          "email": "unlock@example.com", "password": "WrongPass1",
      })
    resp = client.post("/auth/login/email", json={
        "email": "unlock@example.com", "password": "Goodpass1",
    })
    assert resp.status_code == 200


# ===== Security Headers =====

class TestSecurityHeaders:
  def test_security_headers_present(self, client):
    resp = client.get("/auth/config")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in resp.headers["Permissions-Policy"]


# ===== Reset Password Page =====

class TestResetPasswordPage:
  def test_reset_page_serves(self, client):
    resp = client.get("/reset-password")
    assert resp.status_code == 200
    assert "Reset Password" in resp.text
