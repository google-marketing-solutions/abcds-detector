"""Initial schema — matches existing SQLite tables.

Revision ID: 001
Revises: None
Create Date: 2026-02-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.create_table(
      "users",
      sa.Column("id", sa.String(), primary_key=True),
      sa.Column("google_sub", sa.String(), unique=True, index=True, nullable=True),
      sa.Column("email", sa.String(), unique=True, nullable=False),
      sa.Column("password_hash", sa.String(), nullable=True),
      sa.Column("email_verified", sa.Boolean(), default=False, nullable=False),
      sa.Column("verification_token", sa.String(), nullable=True),
      sa.Column("reset_token", sa.String(), nullable=True),
      sa.Column("token_expires_at", sa.DateTime(), nullable=True),
      sa.Column("stripe_customer_id", sa.String(), nullable=True),
      sa.Column("is_admin", sa.Boolean(), default=False, nullable=False),
      sa.Column("credits_balance", sa.Integer(), default=0, nullable=False),
      sa.Column("created_at", sa.DateTime()),
      sa.Column("updated_at", sa.DateTime()),
      sa.Column("last_login", sa.DateTime()),
  )

  op.create_table(
      "credit_transactions",
      sa.Column("id", sa.String(), primary_key=True),
      sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, index=True),
      sa.Column("type", sa.String(), nullable=False),
      sa.Column("amount", sa.Integer(), nullable=False),
      sa.Column("reason", sa.String(), nullable=False),
      sa.Column("job_id", sa.String(), nullable=True),
      sa.Column("created_at", sa.DateTime()),
  )

  op.create_table(
      "renders",
      sa.Column("render_id", sa.String(), primary_key=True),
      sa.Column("status", sa.String(), nullable=False, default="queued", index=True),
      sa.Column("progress_pct", sa.Integer(), nullable=True),
      sa.Column("created_at", sa.DateTime()),
      sa.Column("started_at", sa.DateTime(), nullable=True),
      sa.Column("finished_at", sa.DateTime(), nullable=True),
      sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, index=True),
      sa.Column("user_email", sa.String(), nullable=True),
      sa.Column("user_name", sa.String(), nullable=True),
      sa.Column("source_type", sa.String(), nullable=True),
      sa.Column("source_ref", sa.String(), nullable=True),
      sa.Column("input_assets", sa.Text(), nullable=True),
      sa.Column("prompt_text", sa.Text(), nullable=True),
      sa.Column("brand_guide", sa.Text(), nullable=True),
      sa.Column("config_json", sa.Text(), nullable=True),
      sa.Column("output_url", sa.String(), nullable=True),
      sa.Column("thumbnail_url", sa.String(), nullable=True),
      sa.Column("duration_seconds", sa.Float(), nullable=True),
      sa.Column("file_size_mb", sa.Float(), nullable=True),
      sa.Column("pipeline_version", sa.String(), nullable=True),
      sa.Column("model", sa.String(), nullable=True),
      sa.Column("tokens_estimated", sa.Integer(), nullable=True),
      sa.Column("tokens_used", sa.Integer(), nullable=True),
      sa.Column("error_code", sa.String(), nullable=True),
      sa.Column("error_message", sa.Text(), nullable=True),
      sa.Column("logs_url", sa.String(), nullable=True),
      sa.Column("webhook_failures_count", sa.Integer(), default=0, nullable=False),
  )

  op.create_table(
      "feature_feedback",
      sa.Column("id", sa.String(), primary_key=True),
      sa.Column("report_id", sa.String(), nullable=False, index=True),
      sa.Column("feature_id", sa.String(), nullable=False, index=True),
      sa.Column("verdict", sa.String(), nullable=False),
      sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
      sa.Column("created_at", sa.DateTime()),
  )

  op.create_table(
      "processed_stripe_events",
      sa.Column("stripe_event_id", sa.String(), primary_key=True),
      sa.Column("stripe_session_id", sa.String(), nullable=False),
      sa.Column("processed_at", sa.DateTime()),
  )


def downgrade() -> None:
  op.drop_table("processed_stripe_events")
  op.drop_table("feature_feedback")
  op.drop_table("renders")
  op.drop_table("credit_transactions")
  op.drop_table("users")
