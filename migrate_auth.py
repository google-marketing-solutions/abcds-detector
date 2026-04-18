#!/usr/bin/env python3
"""Idempotent database migration: add external auth columns to users table.

Adds the following columns if they don't already exist:
  - password_hash (TEXT, nullable)
  - email_verified (BOOLEAN, default 0)
  - verification_token (TEXT, nullable)
  - reset_token (TEXT, nullable)
  - token_expires_at (DATETIME, nullable)

Also makes google_sub nullable for email/password-only users.

Safe to run multiple times. Supports SQLite and PostgreSQL.

Usage:
  python migrate_auth.py
  DATABASE_URL=postgresql://... python migrate_auth.py
"""

import os
import sys

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/app.db")


def _column_exists(inspector, table: str, column: str) -> bool:
  """Check if a column exists in a table."""
  columns = {c["name"] for c in inspector.get_columns(table)}
  return column in columns


def migrate():
  engine = create_engine(DATABASE_URL, echo=False)
  inspector = inspect(engine)

  if "users" not in inspector.get_table_names():
    print("Table 'users' does not exist yet — skipping auth migration.")
    return

  is_sqlite = DATABASE_URL.startswith("sqlite")

  migrations = [
      # (column_name, SQL for SQLite, SQL for PostgreSQL)
      (
          "password_hash",
          "ALTER TABLE users ADD COLUMN password_hash TEXT",
          "ALTER TABLE users ADD COLUMN password_hash TEXT",
      ),
      (
          "email_verified",
          "ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0",
          "ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE",
      ),
      (
          "verification_token",
          "ALTER TABLE users ADD COLUMN verification_token TEXT",
          "ALTER TABLE users ADD COLUMN verification_token TEXT",
      ),
      (
          "reset_token",
          "ALTER TABLE users ADD COLUMN reset_token TEXT",
          "ALTER TABLE users ADD COLUMN reset_token TEXT",
      ),
      (
          "token_expires_at",
          "ALTER TABLE users ADD COLUMN token_expires_at DATETIME",
          "ALTER TABLE users ADD COLUMN token_expires_at TIMESTAMP",
      ),
  ]

  applied = 0
  skipped = 0

  with engine.begin() as conn:
    for col_name, sqlite_sql, pg_sql in migrations:
      # Re-inspect after each change (SQLite needs this)
      inspector = inspect(engine)
      if _column_exists(inspector, "users", col_name):
        print(f"  [skip] {col_name} already exists")
        skipped += 1
        continue

      sql = sqlite_sql if is_sqlite else pg_sql
      conn.execute(text(sql))
      print(f"  [add]  {col_name}")
      applied += 1

    # Make google_sub nullable (SQLite doesn't support ALTER COLUMN,
    # but the column was already created as nullable in the latest schema).
    # For PostgreSQL:
    if not is_sqlite:
      try:
        conn.execute(text(
            "ALTER TABLE users ALTER COLUMN google_sub DROP NOT NULL"
        ))
        print("  [fix]  google_sub made nullable")
      except Exception:
        pass  # Already nullable

  # Mark existing Google users as email_verified
  with engine.begin() as conn:
    result = conn.execute(text(
        "UPDATE users SET email_verified = 1 "
        "WHERE google_sub IS NOT NULL AND email_verified = 0"
    ))
    if result.rowcount:
      print(f"  [fix]  Marked {result.rowcount} existing Google user(s) as email_verified")

  print(f"\nDone: {applied} column(s) added, {skipped} skipped.")


if __name__ == "__main__":
  print(f"Migrating database: {DATABASE_URL}")
  print()
  migrate()
