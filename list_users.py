#!/usr/bin/env python3
"""List all users in the database."""

from db import SessionLocal, User


def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("No users found in database")
            return
        
        print(f"Found {len(users)} user(s):\n")
        for user in users:
            print(f"  Email: {user.email}")
            print(f"  ID: {user.id}")
            print(f"  Credits: {user.credits_balance:,}")
            print(f"  Verified: {user.email_verified}")
            print(f"  Created: {user.created_at}")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    list_users()
