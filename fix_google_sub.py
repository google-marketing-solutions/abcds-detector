#!/usr/bin/env python3
"""Make google_sub column nullable for SQLite."""

import os
import sqlite3

DATABASE_PATH = "data/app.db"


def fix_google_sub():
    """Recreate users table with google_sub as nullable."""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        
        # 1. Create new table with correct schema
        cursor.execute("""
            CREATE TABLE users_new (
                id TEXT PRIMARY KEY,
                google_sub TEXT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                email_verified BOOLEAN NOT NULL DEFAULT 0,
                verification_token TEXT,
                reset_token TEXT,
                token_expires_at DATETIME,
                stripe_customer_id TEXT,
                is_admin BOOLEAN NOT NULL DEFAULT 0,
                credits_balance INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME,
                last_login DATETIME
            )
        """)
        
        # 2. Copy data from old table if it exists and has data
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("""
                INSERT INTO users_new 
                SELECT * FROM users
            """)
        
        # 3. Drop old table
        cursor.execute("DROP TABLE users")
        
        # 4. Rename new table
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        # 5. Recreate indexes
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        
        conn.commit()
        print("✅ Successfully made google_sub nullable")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at {DATABASE_PATH}")
        exit(1)
    
    fix_google_sub()
