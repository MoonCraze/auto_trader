import asyncio
import config
from portfolio_manager import PortfolioManager
from execution_engine import ExecutionEngine
from strategy_engine import StrategyEngine
from data_feeder import generate_synthetic_data, stream_data

class Orchestrator:
    def __init__(self):
        self.portfolio_manager = PortfolioManager(config.INITIAL_CAPITAL_SOL)
        self.execution_engine = ExecutionEngine(self.portfolio_manager)
        self.token_queue = asyncio.Queue()
        self.active_strategies = {}  # Maps token_symbol -> StrategyEngine instance
        self.active_trades = {}      # Maps token_symbol -> original purchase quantity

    def add_token_to_queue(self, token_symbol):
        """Adds a new 'green-flagged' token to the processing queue."""
        print(f"\n[ORCHESTRATOR] New token signal received: {token_symbol}. Added to queue.")
        self.token_queue.put_nowait(token_symbol)

    async def _monitor_trade(self, token_symbol, data_df):
        """Monitors price updates for a single token and executes strategy decisions."""
        strategy = self.active_strategies[token_symbol]
        initial_quantity = self.active_trades[token_symbol]

        print(f"[{token_symbol}] Starting trade monitoring...")

        async for price_update in stream_data(data_df):
            current_price = price_update['price']
            
            # If position is closed, stop monitoring
            if token_symbol not in self.portfolio_manager.positions:
                break
                
            action, sell_portion, reason = strategy.check_for_trade_action(current_price)
            
            if action == 'SELL':
                print(f"[{token_symbol}] Strategy action: {action} {sell_portion*100}% - Reason: {reason}")
                
                remaining_tokens = self.portfolio_manager.positions[token_symbol]['tokens']
                
                # If it's a stop-loss (sell_portion=1.0), sell all remaining tokens.
                # Otherwise, sell a portion of the *original* quantity.
                tokens_to_sell = remaining_tokens if sell_portion == 1.0 else initial_quantity * sell_portion
                
                # Ensure we don't try to sell more than we have
                tokens_to_sell = min(tokens_to_sell, remaining_tokens)

                self.execution_engine.execute_sell(token_symbol, tokens_to_sell, current_price)
                
                # Display status after the trade
                self.portfolio_manager.display_status({token_symbol: current_price})

        # --- Cleanup after the trade is fully closed ---
        print(f"[{token_symbol}] Trade monitoring finished. Position closed.")
        del self.active_strategies[token_symbol]
        del self.active_trades[token_symbol]

    async def run(self):
        """The main loop of the orchestrator."""
        print("[ORCHESTRATOR] System started. Waiting for token signals...")
        self.portfolio_manager.display_status({})
        
        active_monitoring_tasks = []

        while True:
            # --- Start new trades for tokens in the queue ---
            if not self.token_queue.empty():
                token_symbol = await self.token_queue.get()
                
                print(f"[ORCHESTRATOR] Processing signal for {token_symbol} from queue.")

                # 1. Calculate investment size
                sol_to_invest = self.portfolio_manager.sol_balance * config.RISK_PER_TRADE_PERCENT
                
                if self.portfolio_manager.sol_balance < sol_to_invest or sol_to_invest < 0.01:
                    print(f"[{token_symbol}] Skipping trade: Insufficient capital to meet risk profile.")
                    continue

                # 2. Get data and execute initial buy
                data_df = generate_synthetic_data(
                    initial_price=config.SIM_INITIAL_PRICE, 
                    drift=config.SIM_DRIFT, 
                    volatility=config.SIM_VOLATILITY, 
                    time_steps=config.SIM_TIME_STEPS
                )
                entry_price = data_df['price'].iloc[0]
                
                print(f"[{token_symbol}] Attempting initial buy with {sol_to_invest:.4f} SOL at price {entry_price:.6f}")
                tokens_bought = self.execution_engine.execute_buy(token_symbol, sol_to_invest, entry_price)

                # 3. If buy successful, create strategy and start monitoring
                if tokens_bought > 0:
                    strategy = StrategyEngine(token_symbol, entry_price, tokens_bought)
                    self.active_strategies[token_symbol] = strategy
                    self.active_trades[token_symbol] = tokens_bought
                    
                    # Create and start the monitoring task
                    task = asyncio.create_task(self._monitor_trade(token_symbol, data_df))
                    active_monitoring_tasks.append(task)
                    self.portfolio_manager.display_status({token_symbol: entry_price})
                else:
                    print(f"[{token_symbol}] Initial buy failed. Aborting trade.")
            
            # --- Check for completion ---
            if self.token_queue.empty() and not self.active_strategies:
                print("\n[ORCHESTRATOR] All trades are complete and queue is empty. Shutting down.")
                break

            await asyncio.sleep(1) # Check the queue every second

        # Wait for any lingering tasks to finish (good practice)
        await asyncio.gather(*active_monitoring_tasks)