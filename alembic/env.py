"""Alembic environment configuration.

Reads DATABASE_URL from the environment and uses the SQLAlchemy models
defined in db.py as the migration target metadata.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from db import Base, DATABASE_URL

config = context.config
if config.config_file_name is not None:
  fileConfig(config.config_file_name)

# Override sqlalchemy.url with our DATABASE_URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
  """Run migrations in 'offline' mode (emit SQL without a live connection)."""
  url = config.get_main_option("sqlalchemy.url")
  context.configure(
      url=url,
      target_metadata=target_metadata,
      literal_binds=True,
      dialect_opts={"paramstyle": "named"},
  )
  with context.begin_transaction():
    context.run_migrations()


def run_migrations_online() -> None:
  """Run migrations in 'online' mode (with a live database connection)."""
  connectable = engine_from_config(
      config.get_section(config.config_ini_section, {}),
      prefix="sqlalchemy.",
      poolclass=pool.NullPool,
  )
  with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
      context.run_migrations()


if context.is_offline_mode():
  run_migrations_offline()
else:
  run_migrations_online()
