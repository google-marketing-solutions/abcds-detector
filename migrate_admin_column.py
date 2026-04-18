#!/usr/bin/env python3
"""Add is_admin column to users table."""

import os
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/app.db")


def migrate():
    engine = create_engine(DATABASE_URL, echo=False)
    inspector = inspect(engine)
    
    columns = {c["name"] for c in inspector.get_columns("users")}
    
    if "is_admin" in columns:
        print("Column is_admin already exists")
        return
    
    is_sqlite = DATABASE_URL.startswith("sqlite")
    
    with engine.begin() as conn:
        if is_sqlite:
            sql = "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"
        else:
            sql = "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"
        
        conn.execute(text(sql))
        print("Added is_admin column")


if __name__ == "__main__":
    migrate()
