#!/usr/bin/env python3
"""
Basic tests for the auto trader system
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.portfolio_manager import PortfolioManager
from src.strategy_engine import StrategyEngine
from src.signal_queue import SignalQueue, TradingSignal
from datetime import datetime


async def test_portfolio_manager():
    """Test portfolio manager functionality"""
    print("🧪 Testing Portfolio Manager...")
    
    pm = PortfolioManager(initial_sol_balance=100.0, db_path="test_portfolio.db")
    
    # Test position sizing
    position_size = pm.calculate_position_size(0.02)
    assert position_size == 2.0, f"Expected 2.0, got {position_size}"
    
    # Test adding position
    success = pm.add_position("TEST_TOKEN", 1000, 0.001, 2.0)
    assert success, "Failed to add position"
    assert pm.sol_balance == 98.0, f"Expected 98.0 SOL, got {pm.sol_balance}"
    
    # Test partial sell
    sol_received = pm.partial_sell("TEST_TOKEN", 0.5, 0.002)
    assert sol_received is not None, "Failed to sell position"
    
    print("✅ Portfolio Manager tests passed")


async def test_strategy_engine():
    """Test strategy engine functionality"""
    print("🧪 Testing Strategy Engine...")
    
    pm = PortfolioManager(initial_sol_balance=100.0, db_path="test_strategy.db")
    se = StrategyEngine(pm)
    
    # Test entry signal
    action = se.analyze_token("TEST_TOKEN", 1.0)
    assert action.action.value == "BUY", f"Expected BUY action, got {action.action}"
    
    print("✅ Strategy Engine tests passed")


async def test_signal_queue():
    """Test signal queue functionality"""
    print("🧪 Testing Signal Queue...")
    
    sq = SignalQueue()
    
    # Test adding signal
    signal = TradingSignal(
        token_address="TEST_TOKEN",
        signal_type="GREEN_FLAG",
        timestamp=datetime.now(),
        priority=1
    )
    
    success = await sq.add_signal(signal)
    assert success, "Failed to add signal"
    
    # Test retrieving signal
    retrieved_signal = await sq.get_next_signal()
    assert retrieved_signal is not None, "Failed to retrieve signal"
    assert retrieved_signal.token_address == "TEST_TOKEN", "Wrong token retrieved"
    
    print("✅ Signal Queue tests passed")


async def main():
    """Run all tests"""
    print("🚀 Running Auto Trader System Tests")
    print("=" * 40)
    
    try:
        await test_portfolio_manager()
        await test_strategy_engine()
        await test_signal_queue()
        
        print("\n🎉 All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
    
    # Cleanup test databases
    import os
    for db in ["test_portfolio.db", "test_strategy.db"]:
        if os.path.exists(db):
            os.remove(db)
    
    print("🧹 Test cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())