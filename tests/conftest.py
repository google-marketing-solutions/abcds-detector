"""Shared test fixtures for auth test suite."""

import datetime
import os
import sys

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override env vars BEFORE importing app modules so startup guards don't fire
os.environ["SESSION_SECRET"] = "test-secret-key-not-for-production"
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""
os.environ["STRIPE_SECRET_KEY"] = ""

from db import Base, User, CreditTransaction  # noqa: E402
import bcrypt as _bcrypt  # noqa: E402


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_engine():
  """Create an in-memory SQLite engine with all tables.

  Uses StaticPool so every connection shares the same in-memory DB,
  and check_same_thread=False for FastAPI TestClient threading.
  """
  engine = create_engine(
      "sqlite://",
      echo=False,
      connect_args={"check_same_thread": False},
      poolclass=StaticPool,
  )
  Base.metadata.create_all(bind=engine)
  yield engine
  engine.dispose()


@pytest.fixture()
def db_session(db_engine):
  """Yield a fresh DB session per test, rolled back after."""
  Session = sessionmaker(bind=db_engine)
  session = Session()
  yield session
  session.close()


@pytest.fixture()
def client(db_engine):
  """FastAPI TestClient wired to the in-memory DB."""
  from fastapi.testclient import TestClient

  SessionLocal = sessionmaker(bind=db_engine)

  # Must import app AFTER env vars are set
  from web_app import app
  from db import get_db

  def _override_get_db():
    db = SessionLocal()
    try:
      yield db
    finally:
      db.close()

  app.dependency_overrides[get_db] = _override_get_db

  # Clear rate-limit and lockout buckets between tests
  from auth import _rate_buckets, _login_failures
  _rate_buckets.clear()
  _login_failures.clear()

  with TestClient(app, base_url="https://testserver") as c:
    yield c

  app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def create_user(db_session):
  """Factory to insert a user directly into the DB."""

  def _create(
      email="test@example.com",
      password="Testpass1",
      email_verified=False,
      google_sub=None,
      credits_balance=1000,
      verification_token=None,
      reset_token=None,
      token_expires_at=None,
  ):
    now = datetime.datetime.utcnow()
    user = User(
        email=email,
        password_hash=_bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode() if password else None,
        email_verified=email_verified,
        google_sub=google_sub,
        credits_balance=credits_balance,
        verification_token=verification_token,
        reset_token=reset_token,
        token_expires_at=token_expires_at,
        created_at=now,
        updated_at=now,
        last_login=now,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

  return _create


@pytest.fixture()
def auth_headers(client):
  """Helper: register a user and return headers with the session cookie."""

  def _auth(email="authed@example.com", password="Testpass1"):
    resp = client.post("/auth/register", json={
        "email": email, "password": password,
    })
    assert resp.status_code == 201
    return {"Cookie": f"session_token={resp.cookies.get('session_token')}"}

  return _auth


# ---------------------------------------------------------------------------
# Feature / scene / metadata fixtures (used by unit tests)
# ---------------------------------------------------------------------------

def _make_feature(
    fid, name, sub_category="ATTRACT", detected=True,
    confidence=0.9, evidence="", recommendation="",
    recommendation_priority="", timestamps=None,
):
  """Build a formatted feature dict (same shape as web_app.format_feature)."""
  return {
      "id": fid,
      "name": name,
      "category": "LONG_FORM_ABCD",
      "sub_category": sub_category,
      "detected": detected,
      "confidence": confidence,
      "rationale": f"Rationale for {name}",
      "evidence": evidence or f"Evidence for {name}",
      "strengths": "Good" if detected else "",
      "weaknesses": "" if detected else "Missing",
      "timestamps": timestamps or [],
      "recommendation": recommendation,
      "recommendation_priority": recommendation_priority,
  }


@pytest.fixture()
def abcd_features():
  return [
      _make_feature("attract_dynamic_start", "Dynamic Start", "ATTRACT", True, 0.95, "dynamic start in first 2s"),
      _make_feature("attract_supers", "Supers / Text Overlays", "ATTRACT", True, 0.8),
      _make_feature("brand_logo_early", "Brand Logo Early", "BRAND", True, 0.85, "logo visible at 0:02"),
      _make_feature("brand_mention", "Brand Mention", "BRAND", False, 0.3),
      _make_feature("connect_product_visuals", "Product Visuals", "CONNECT", True, 0.9, "product demo"),
      _make_feature("connect_people", "People Presence", "CONNECT", True, 0.88),
      _make_feature("direct_cta", "Call to Action", "DIRECT", True, 0.92, "Shop now text at end"),
      _make_feature("direct_offer", "Offer / Promotion", "DIRECT", False, 0.2, "url in end card"),
  ]


@pytest.fixture()
def persuasion_features():
  return [
      _make_feature("ci_social_proof", "Social Proof", "PERSUASION", True, 0.85),
      _make_feature("ci_scarcity", "Scarcity / Urgency", "PERSUASION", True, 0.7),
      _make_feature("ci_authority", "Authority / Expertise", "PERSUASION", False, 0.4),
      _make_feature("ci_emotional_appeal", "Emotional Appeal", "PERSUASION", True, 0.9),
      _make_feature("ci_reciprocity", "Reciprocity", "PERSUASION", False, 0.3),
      _make_feature("ci_storytelling", "Storytelling", "PERSUASION", True, 0.88),
      _make_feature("ci_humor", "Humor / Entertainment", "PERSUASION", False, 0.2),
  ]


@pytest.fixture()
def structure_features():
  return [
      _make_feature(
          "ci_structure", "Creative Structure", "STRUCTURE",
          True, 0.82, evidence="Problem-Solution, Demo",
      ),
  ]


@pytest.fixture()
def accessibility_features():
  return [
      _make_feature("acc_captions_present", "Captions Present", "ACCESSIBILITY", True, 0.9),
      _make_feature("acc_text_contrast", "Text Contrast", "ACCESSIBILITY", True, 0.8),
      _make_feature("acc_speech_rate", "Comfortable Speech Rate", "ACCESSIBILITY", True, 0.7),
      _make_feature("acc_audio_dependence", "Audio Independence", "ACCESSIBILITY", False, 0.4),
  ]


@pytest.fixture()
def sample_scenes():
  return [
      {
          "scene_number": 1, "start_time": "0:00", "end_time": "0:05",
          "description": "Opening shot of person with product",
          "transcript": "Hey check out this amazing new gadget it really works",
          "emotion": "excitement", "sentiment_score": 0.7,
          "speech_ratio": 0.8, "volume_pct": 65, "volume_flag": False,
      },
      {
          "scene_number": 2, "start_time": "0:05", "end_time": "0:12",
          "description": "Product demo close-up",
          "transcript": "Look at the premium build quality and sleek design",
          "emotion": "trust", "sentiment_score": 0.5,
          "speech_ratio": 0.7, "volume_pct": 70, "volume_flag": False,
      },
      {
          "scene_number": 3, "start_time": "0:12", "end_time": "0:20",
          "description": "Customer testimonial",
          "transcript": "I have been using this for a month and honestly it changed my routine",
          "emotion": "trust", "sentiment_score": 0.6,
          "speech_ratio": 0.9, "volume_pct": 60, "volume_flag": False,
      },
      {
          "scene_number": 4, "start_time": "0:20", "end_time": "0:30",
          "description": "CTA end card with brand logo",
          "transcript": "Get yours today visit our website",
          "emotion": "urgency", "sentiment_score": 0.3,
          "speech_ratio": 0.5, "volume_pct": 75, "volume_flag": False,
      },
  ]


@pytest.fixture()
def video_metadata():
  return {
      "duration": "0:30", "resolution": "1920x1080",
      "aspect_ratio": "16:9", "frame_rate": "30fps",
      "file_size": "12.5 MB", "codec": "H.264",
  }


@pytest.fixture()
def sample_predictions(abcd_features, persuasion_features, structure_features):
  import performance_predictor
  return performance_predictor.compute_predictions(
      abcd_features, persuasion_features, structure_features,
  )
