#!/usr/bin/env python3
"""
Simple demo script to showcase the auto trader system
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orchestrator import Orchestrator


async def run_simple_demo():
    """Run a simple demonstration of the trading system"""
    
    print("""
🎯 AUTO TRADER SIMPLE DEMO
=========================
This demo shows the complete trading lifecycle:
1. Signal processing from queue
2. Position sizing and entry
3. Tiered take-profits (30%, 75%)
4. Trailing stop-loss management
5. Portfolio tracking and P&L calculation
""")
    
    # Create orchestrator with demo settings
    orchestrator = Orchestrator(
        initial_sol_balance=50.0,  # Start with 50 SOL
        max_concurrent_positions=3,
        price_update_interval=0.5  # Update prices every 0.5 seconds
    )
    
    # Add some demo signals manually
    await orchestrator.add_signal("MOONSHOT_TOKEN", "GREEN_FLAG", priority=3)
    await orchestrator.add_signal("DEGEN_COIN", "BULLISH", priority=2)
    await orchestrator.add_signal("ROCKET_TOKEN", "GREEN_FLAG", priority=1)
    
    print("🔥 Added demo signals to queue...")
    print("⏱️  Running trading simulation for 30 seconds...\n")
    
    # Run the demo
    await orchestrator.run_demo(30)


if __name__ == "__main__":
    asyncio.run(run_simple_demo())