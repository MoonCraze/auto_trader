class ExecutionEngine:
    def __init__(self, portfolio_manager):
        """
        Initializes the ExecutionEngine with a reference to the portfolio manager.
        
        Args:
            portfolio_manager (PortfolioManager): The portfolio manager instance.
        """
        self.portfolio_manager = portfolio_manager

    def execute_buy(self, token_symbol, sol_to_invest, current_price):
        """
        Executes a buy order in the simulation.

        Args:
            token_symbol (str): The symbol of the token to buy.
            sol_to_invest (float): The amount of SOL to spend.
            current_price (float): The current price of the token.

        Returns:
            float: The number of tokens successfully purchased, or 0 if failed.
        """
        # In a real system, this is where you'd add a slippage tolerance.
        # For our simulation, we assume perfect execution at the current price.
        if current_price <= 0:
            print("Error: Invalid price for buy.")
            return 0
            
        tokens_received = sol_to_invest / current_price
        
        success = self.portfolio_manager.record_buy(
            token_symbol=token_symbol,
            sol_spent=sol_to_invest,
            tokens_received=tokens_received,
            price=current_price
        )
        
        return tokens_received if success else 0

    def execute_sell(self, token_symbol, tokens_to_sell, current_price):
        """
        Executes a sell order in the simulation.

        Args:
            token_symbol (str): The symbol of the token to sell.
            tokens_to_sell (float): The number of tokens to sell.
            current_price (float): The current price of the token.

        Returns:
            float: The amount of SOL received from the sale, or 0 if failed.
        """
        if current_price <= 0:
            print("Error: Invalid price for sell.")
            return 0

        # Again, assuming perfect execution for the simulation.
        sol_received = tokens_to_sell * current_price
        
        success = self.portfolio_manager.record_sell(
            token_symbol=token_symbol,
            tokens_sold=tokens_to_sell,
            sol_received=sol_received,
            price=current_price
        )
        
        return sol_received if success else 0

# --- Standalone Test ---
if __name__ == '__main__':
    import config
    from portfolio_manager import PortfolioManager

    # Setup
    pm = PortfolioManager(initial_capital=config.INITIAL_CAPITAL_SOL)
    executor = ExecutionEngine(pm)
    
    token_b = "BRAINCOIN"
    
    # Test Buy
    print("--- Testing BUY execution ---")
    executor.execute_buy(token_symbol=token_b, sol_to_invest=1.0, current_price=0.05)
    pm.display_status({token_b: 0.05})

    # Test Sell
    print("\n--- Testing SELL execution ---")
    # We should have 1.0 / 0.05 = 20 tokens. Let's sell 5 of them.
    executor.execute_sell(token_symbol=token_b, tokens_to_sell=5.0, current_price=0.06)
    pm.display_status({token_b: 0.06})