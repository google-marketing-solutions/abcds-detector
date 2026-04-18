"""Tests for the migrate_auth.py migration script."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, inspect, text


def _create_legacy_db(db_path: str):
  """Create a DB with the old schema (no auth columns)."""
  engine = create_engine(f"sqlite:///{db_path}", echo=False)
  with engine.begin() as conn:
    conn.execute(text("""
      CREATE TABLE users (
        id TEXT PRIMARY KEY,
        google_sub TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        stripe_customer_id TEXT,
        is_admin BOOLEAN NOT NULL DEFAULT 0,
        credits_balance INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME,
        updated_at DATETIME,
        last_login DATETIME
      )
    """))
    conn.execute(text("""
      INSERT INTO users (id, google_sub, email, credits_balance)
      VALUES ('u1', 'gsub1', 'user@example.com', 500)
    """))
  engine.dispose()
  return f"sqlite:///{db_path}"


class TestMigration:
  def test_adds_missing_columns(self, tmp_path):
    db_path = str(tmp_path / "test.db")
    db_url = _create_legacy_db(db_path)

    # Patch DATABASE_URL and run migration
    import migrate_auth
    migrate_auth.DATABASE_URL = db_url
    migrate_auth.migrate()

    # Verify columns exist
    engine = create_engine(db_url)
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("users")}
    engine.dispose()

    assert "password_hash" in cols
    assert "email_verified" in cols
    assert "verification_token" in cols
    assert "reset_token" in cols
    assert "token_expires_at" in cols

  def test_idempotent(self, tmp_path):
    """Running migration twice should not fail."""
    db_path = str(tmp_path / "test2.db")
    db_url = _create_legacy_db(db_path)

    import migrate_auth
    migrate_auth.DATABASE_URL = db_url
    migrate_auth.migrate()
    migrate_auth.migrate()  # Second run should be a no-op

    engine = create_engine(db_url)
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("users")}
    engine.dispose()

    assert "password_hash" in cols

  def test_marks_existing_google_users_verified(self, tmp_path):
    db_path = str(tmp_path / "test3.db")
    db_url = _create_legacy_db(db_path)

    import migrate_auth
    migrate_auth.DATABASE_URL = db_url
    migrate_auth.migrate()

    engine = create_engine(db_url)
    with engine.begin() as conn:
      result = conn.execute(text(
          "SELECT email_verified FROM users WHERE id = 'u1'"
      ))
      row = result.fetchone()
    engine.dispose()

    assert row[0] == 1  # Should be marked as verified
