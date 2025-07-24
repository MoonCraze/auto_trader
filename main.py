import asyncio
from orchestrator import Orchestrator
import config

async def main():
    """
    The main entry point for the autonomous trading system simulation.
    """
    print("--- Autonomous Trading System Simulation ---")
    print("Initializing Orchestrator...")
    
    # 1. Create the orchestrator instance
    orchestrator = Orchestrator()

    # 2. Add "green-flagged" tokens to the queue. 
    #    The orchestrator will process these one by one.
    orchestrator.add_token_to_queue("MOGCOIN")
    # You could add more here to see them queued up:
    # orchestrator.add_token_to_queue("PEPECOIN") 
    
    # 3. Start the orchestrator's main loop and wait for it to complete.
    await orchestrator.run()

    # 4. Display the final state of the portfolio.
    print("\n--- SIMULATION COMPLETE ---")
    print("Final Portfolio State:")
    orchestrator.portfolio_manager.display_status({}) # Pass empty dict as no prices are streaming
    print("\nTrade Log:")
    for log in orchestrator.portfolio_manager.trade_log:
        print(log)

if __name__ == "__main__":
    # Ensure you have the necessary libraries: pip install numpy pandas
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user. Exiting.")