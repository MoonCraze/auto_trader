"""
Test script to verify database setup and create demo users.
"""

from database import SessionLocal, init_db
from auth import register_synthetic_wallet

def main():
    print("=" * 60)
    print("Auto Trader Bot - Database Test & Demo Setup")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    
    # Create demo users
    print("\n2. Creating demo users...")
    db = SessionLocal()
    try:
        for i in range(3):
            result = register_synthetic_wallet(db)
            print(f"\n   Demo User #{i+1}:")
            print(f"   Wallet: {result['wallet_address']}")
            print(f"   Balance: {result['initial_sol_balance']} SOL")
            print(f"   Created: {result['created_at']}")
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete! You can now:")
    print("   1. Start the WebSocket server: python websocket_server.py")
    print("   2. Start the API server: python api_server.py")
    print("   3. Start the frontend: cd bot-ui-ts && npm run dev")
    print("\n   Or use any of the demo wallet addresses above to login!")
    print("=" * 60)

if __name__ == "__main__":
    main()
