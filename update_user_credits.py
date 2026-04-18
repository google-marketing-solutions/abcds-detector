#!/usr/bin/env python3
"""Script to update user credits."""

import sys
import datetime
from sqlalchemy.orm import Session
from db import SessionLocal, User, CreditTransaction


def update_user_credits(email: str, credits: int):
    """Add credits to a user account."""
    db: Session = SessionLocal()
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ Error: User with email '{email}' not found")
            return False
        
        # Store old balance
        old_balance = user.credits_balance
        
        # Update balance
        user.credits_balance += credits
        user.updated_at = datetime.datetime.utcnow()
        
        # Create transaction record
        tx = CreditTransaction(
            user_id=user.id,
            type="grant",
            amount=credits,
            reason="admin_manual_grant",
        )
        db.add(tx)
        
        # Commit changes
        db.commit()
        
        print(f"✅ Successfully updated user: {email}")
        print(f"   Previous balance: {old_balance:,} credits")
        print(f"   Added: {credits:,} credits")
        print(f"   New balance: {user.credits_balance:,} credits")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating user: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_user_credits.py <email> <credits>")
        print("Example: python update_user_credits.py kevin@upscale.ai 100000")
        sys.exit(1)
    
    email = sys.argv[1].strip().lower()
    try:
        credits = int(sys.argv[2])
    except ValueError:
        print("❌ Error: Credits must be a number")
        sys.exit(1)
    
    if credits <= 0:
        print("❌ Error: Credits must be positive")
        sys.exit(1)
    
    success = update_user_credits(email, credits)
    sys.exit(0 if success else 1)
