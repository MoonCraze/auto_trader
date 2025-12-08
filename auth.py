"""
Authentication handler for synthetic wallet generation and user management.
Generates random wallet addresses and assigns initial SOL balance between 10-20 SOL.
"""

import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from database import User, SessionLocal
import config

def generate_synthetic_wallet_address() -> str:
    """Generate a synthetic Solana-like wallet address (base58 format simulation)"""
    # Solana addresses are 32-44 characters in base58 encoding
    # For synthetic purposes, we'll generate a 44-character alphanumeric string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(44))

def generate_initial_sol_balance() -> float:
    """Generate random SOL balance between MIN and MAX with decimal precision"""
    min_sol = config.MIN_SYNTHETIC_SOL
    max_sol = config.MAX_SYNTHETIC_SOL
    # Generate random value with 4 decimal places
    balance = random.uniform(min_sol, max_sol)
    return round(balance, 4)

def register_synthetic_wallet(db: Session) -> dict:
    """
    Register a new synthetic wallet with random address and SOL balance.
    Returns dict with wallet_address and initial_sol_balance.
    """
    wallet_address = generate_synthetic_wallet_address()
    initial_balance = generate_initial_sol_balance()
    
    # Check for collision (extremely unlikely but safe)
    existing = db.query(User).filter(User.wallet_address == wallet_address).first()
    if existing:
        # Try again recursively
        return register_synthetic_wallet(db)
    
    # Create new user
    user = User(
        wallet_address=wallet_address,
        created_at=datetime.utcnow(),
        initial_sol_balance=initial_balance
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✅ Registered new synthetic wallet: {wallet_address[:8]}... with {initial_balance} SOL")
    
    return {
        "wallet_address": wallet_address,
        "initial_sol_balance": initial_balance,
        "created_at": user.created_at.isoformat()
    }

def authenticate_wallet(wallet_address: str, db: Session) -> User | None:
    """
    Authenticate a wallet address (check if it exists in database).
    Returns User object if valid, None otherwise.
    """
    user = db.query(User).filter(User.wallet_address == wallet_address).first()
    return user

def get_or_create_user(wallet_address: str, db: Session) -> User:
    """
    Get existing user or create new one if doesn't exist.
    Used for login flow - creates account on first login attempt.
    """
    user = authenticate_wallet(wallet_address, db)
    if user:
        return user
    
    # Create new user with provided wallet address
    initial_balance = generate_initial_sol_balance()
    user = User(
        wallet_address=wallet_address,
        created_at=datetime.utcnow(),
        initial_sol_balance=initial_balance
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✅ Created new user for wallet: {wallet_address[:8]}... with {initial_balance} SOL")
    return user

def list_all_users(db: Session) -> list[User]:
    """Get all registered users (for admin/debugging)"""
    return db.query(User).all()

if __name__ == "__main__":
    # Test wallet generation
    db = SessionLocal()
    try:
        print("Testing synthetic wallet generation...")
        for i in range(5):
            result = register_synthetic_wallet(db)
            print(f"  {i+1}. Wallet: {result['wallet_address'][:12]}... | Balance: {result['initial_sol_balance']} SOL")
    finally:
        db.close()
