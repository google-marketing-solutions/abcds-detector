"""Add slack_notified column to renders table.

Revision ID: 002
Revises: 001
Create Date: 2026-02-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.add_column(
      "renders",
      sa.Column(
          "slack_notified",
          sa.Boolean(),
          nullable=False,
          server_default=sa.text("0"),
      ),
  )


def downgrade() -> None:
  op.drop_column("renders", "slack_notified")
