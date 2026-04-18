#!/usr/bin/env python3
"""Script to create a new user with password and credits."""

import sys
import datetime
import bcrypt as _bcrypt
from db import SessionLocal, User, CreditTransaction
import notification_service


def create_user(email: str, password: str, credits: int):
    """Create a new user with email, password, and initial credits."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ Error: User with email '{email}' already exists")
            return False
        
        now = datetime.datetime.utcnow()
        
        # Create user
        user = User(
            email=email,
            password_hash=_bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode(),
            email_verified=True,  # Auto-verify admin-created accounts
            credits_balance=credits,
            created_at=now,
            updated_at=now,
            last_login=now,
        )
        db.add(user)
        db.flush()  # Get user ID
        
        # Create transaction record
        tx = CreditTransaction(
            user_id=user.id,
            type="grant",
            amount=credits,
            reason="initial_grant",
        )
        db.add(tx)
        
        # Commit changes
        db.commit()
        
        print(f"✅ Successfully created user: {email}")
        print(f"   User ID: {user.id}")
        print(f"   Credits: {credits:,}")
        print(f"   Verified: Yes")

        # Notify admin of new signup (Slack + email)
        notification_service.notify_new_signup(email, method="admin_script")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating user: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_user.py <email> <password> <credits>")
        print("Example: python create_user.py kevin@upscale.ai Upscale1! 100000")
        sys.exit(1)
    
    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    
    try:
        credits = int(sys.argv[3])
    except ValueError:
        print("❌ Error: Credits must be a number")
        sys.exit(1)
    
    if credits < 0:
        print("❌ Error: Credits cannot be negative")
        sys.exit(1)
    
    success = create_user(email, password, credits)
    sys.exit(0 if success else 1)
