#!/usr/bin/env python3
"""
Autonomous Crypto Trading Execution Engine

Main entry point for the auto trader system.
This demonstrates the complete trading lifecycle from signal to execution.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orchestrator import Orchestrator


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Autonomous Crypto Trading System')
    parser.add_argument('--demo', action='store_true', 
                       help='Run demo mode with simulated data')
    parser.add_argument('--duration', type=int, default=60,
                       help='Demo duration in seconds (default: 60)')
    parser.add_argument('--balance', type=float, default=100.0,
                       help='Initial SOL balance (default: 100)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Create orchestrator
    orchestrator = Orchestrator(initial_sol_balance=args.balance)
    
    if args.demo:
        print(f"""
🚀 AUTO TRADER DEMO MODE
========================
Initial Balance: {args.balance} SOL
Duration: {args.duration} seconds
        """)
        
        await orchestrator.run_demo(args.duration)
    else:
        print("""
🚀 AUTO TRADER SYSTEM
====================
Running in live mode...
Press Ctrl+C to stop gracefully
        """)
        
        try:
            await orchestrator.start()
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
            await orchestrator.stop()
            print("✅ System stopped gracefully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)