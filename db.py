"""Database models and session management using SQLAlchemy."""

import logging
import os
import uuid
import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
    relationship,
)


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/app.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

# Configure engine with appropriate pooling per backend
if _is_sqlite:
  engine = create_engine(
      DATABASE_URL,
      echo=False,
      connect_args={"check_same_thread": False},
  )

  @event.listens_for(engine, "connect")
  def _set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
else:
  # PostgreSQL: use connection pooling suitable for Cloud Run
  engine = create_engine(
      DATABASE_URL,
      echo=False,
      pool_size=5,
      max_overflow=10,
      pool_timeout=30,
      pool_recycle=1800,  # recycle connections every 30 min
      pool_pre_ping=True,  # verify connections are alive before use
  )

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
  pass


def _uuid() -> str:
  return str(uuid.uuid4())


class User(Base):
  __tablename__ = "users"

  id = Column(String, primary_key=True, default=_uuid)
  google_sub = Column(String, unique=True, index=True, nullable=True)
  email = Column(String, unique=True, nullable=False)
  password_hash = Column(String, nullable=True)
  email_verified = Column(Boolean, default=False, nullable=False)
  verification_token = Column(String, nullable=True)
  reset_token = Column(String, nullable=True)
  token_expires_at = Column(DateTime, nullable=True)
  stripe_customer_id = Column(String, nullable=True)
  is_admin = Column(Boolean, default=False, nullable=False)
  credits_balance = Column(Integer, default=0, nullable=False)
  created_at = Column(DateTime, default=datetime.datetime.utcnow)
  updated_at = Column(
      DateTime,
      default=datetime.datetime.utcnow,
      onupdate=datetime.datetime.utcnow,
  )
  last_login = Column(DateTime, default=datetime.datetime.utcnow)

  transactions = relationship(
      "CreditTransaction", back_populates="user", lazy="dynamic",
  )
  renders = relationship(
      "Render", back_populates="user", lazy="dynamic",
  )


class CreditTransaction(Base):
  __tablename__ = "credit_transactions"

  id = Column(String, primary_key=True, default=_uuid)
  user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
  type = Column(String, nullable=False)  # "grant" | "debit"
  amount = Column(Integer, nullable=False)
  reason = Column(String, nullable=False)
  job_id = Column(String, nullable=True)
  created_at = Column(DateTime, default=datetime.datetime.utcnow)

  user = relationship("User", back_populates="transactions")


class Render(Base):
  __tablename__ = "renders"

  render_id = Column(String, primary_key=True, default=_uuid)
  status = Column(
      String, nullable=False, default="queued", index=True,
  )  # queued / rendering / succeeded / failed / canceled
  progress_pct = Column(Integer, nullable=True)

  created_at = Column(DateTime, default=datetime.datetime.utcnow)
  started_at = Column(DateTime, nullable=True)
  finished_at = Column(DateTime, nullable=True)

  user_id = Column(
      String, ForeignKey("users.id"), nullable=False, index=True,
  )
  user_email = Column(String, nullable=True)
  user_name = Column(String, nullable=True)

  source_type = Column(String, nullable=True)  # upload / url / api
  source_ref = Column(String, nullable=True)    # filename / domain / api_key_id

  input_assets = Column(Text, nullable=True)    # JSON array
  prompt_text = Column(Text, nullable=True)
  brand_guide = Column(Text, nullable=True)
  config_json = Column(Text, nullable=True)     # JSON object

  output_url = Column(String, nullable=True)
  thumbnail_url = Column(String, nullable=True)

  duration_seconds = Column(Float, nullable=True)
  file_size_mb = Column(Float, nullable=True)

  pipeline_version = Column(String, nullable=True)
  model = Column(String, nullable=True)

  tokens_estimated = Column(Integer, nullable=True)
  tokens_used = Column(Integer, nullable=True)

  error_code = Column(String, nullable=True)
  error_message = Column(Text, nullable=True)

  logs_url = Column(String, nullable=True)
  webhook_failures_count = Column(Integer, default=0, nullable=False)
  slack_notified = Column(Boolean, default=False, nullable=False)

  user = relationship("User", back_populates="renders")


class FeatureFeedback(Base):
  """Human feedback on feature detection accuracy."""
  __tablename__ = "feature_feedback"

  id = Column(String, primary_key=True, default=_uuid)
  report_id = Column(String, nullable=False, index=True)
  feature_id = Column(String, nullable=False, index=True)
  verdict = Column(String, nullable=False)  # "correct" | "incorrect"
  user_id = Column(String, ForeignKey("users.id"), nullable=True)
  created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ProcessedStripeEvent(Base):
  __tablename__ = "processed_stripe_events"

  stripe_event_id = Column(String, primary_key=True)
  stripe_session_id = Column(String, nullable=False)
  processed_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
  """Create all tables. Safe to call multiple times."""
  if _is_sqlite:
    os.makedirs("data", exist_ok=True)
  Base.metadata.create_all(bind=engine)
  logging.info("Database initialized (%s)", "SQLite" if _is_sqlite else "PostgreSQL")


def get_db():
  """Yield a database session, closing it after use."""
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
