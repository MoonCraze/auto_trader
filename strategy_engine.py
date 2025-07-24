import config

class StrategyEngine:
    def __init__(self, token_symbol, entry_price, initial_token_quantity):
        """
        Manages the trading strategy for a single token position.
        
        Args:
            token_symbol (str): The token being traded.
            entry_price (float): The average price at which the position was entered.
            initial_token_quantity (float): The initial number of tokens purchased.
        """
        self.token_symbol = token_symbol
        self.entry_price = entry_price
        self.initial_token_quantity = initial_token_quantity
        
        self.highest_price_seen = entry_price
        self.take_profit_levels_hit = [False] * len(config.TAKE_PROFIT_TIERS)
        self.is_breakeven_stop = False # Flag to check if stop is at breakeven

        # Calculate initial stop-loss price
        self.stop_loss_price = self.entry_price * (1 - config.INITIAL_STOP_LOSS_PERCENT)
        
        print(f"[{self.token_symbol}] Strategy Initialized. Entry: {self.entry_price:.6f}, "
              f"Stop-Loss: {self.stop_loss_price:.6f}")

    def check_for_trade_action(self, current_price):
        """
        Analyzes the current price and determines if a trade action is needed.
        
        Returns:
            tuple: (ACTION, amount_in_percent, reason)
                   e.g., ('SELL', 1.0, 'Stop-loss triggered')
                   e.g., ('SELL', 0.33, 'Take-profit 1 triggered')
                   e.g., ('HOLD', None, 'No condition met')
        """
        # --- 1. Priority Check: Stop-Loss ---
        if current_price <= self.stop_loss_price:
            reason = "Breakeven stop" if self.is_breakeven_stop else "Initial stop-loss"
            return ('SELL', 1.0, f"{reason} triggered at {current_price:.6f}")

        # --- 2. Check for Take-Profit Tiers ---
        for i, (profit_target, sell_portion) in enumerate(config.TAKE_PROFIT_TIERS):
            if not self.take_profit_levels_hit[i]:
                target_price = self.entry_price * (1 + profit_target)
                if current_price >= target_price:
                    self.take_profit_levels_hit[i] = True
                    # After first TP, move stop to breakeven
                    if not self.is_breakeven_stop:
                        self.stop_loss_price = self.entry_price
                        self.is_breakeven_stop = True
                        print(f"[{self.token_symbol}] Stop-loss moved to breakeven: {self.entry_price:.6f}")
                    
                    reason = f"Take-profit {i+1} ({profit_target*100}%) triggered at {current_price:.6f}"
                    return ('SELL', sell_portion, reason)

        # --- 3. Update Trailing Stop-Loss (if applicable) ---
        if current_price > self.highest_price_seen:
            self.highest_price_seen = current_price
            # Only trail the stop if we are in the "runner" phase (i.e., past breakeven)
            if self.is_breakeven_stop:
                new_trailing_stop = self.highest_price_seen * (1 - config.TRAILING_STOP_LOSS_PERCENT)
                # The stop-loss should only move up, never down.
                if new_trailing_stop > self.stop_loss_price:
                    self.stop_loss_price = new_trailing_stop
                    # print(f"[{self.token_symbol}] Trailing stop updated to {self.stop_loss_price:.6f}") # Can be noisy

        # --- 4. If no other action, hold ---
        return ('HOLD', None, None)

# --- Standalone Test ---
if __name__ == '__main__':
    print("--- Testing Strategy Engine Logic ---")
    
    # Setup a mock trade
    entry = 0.10
    quantity = 100
    strategy = StrategyEngine("TEST", entry, quantity)

    # Test 1: Price goes up slightly, no action
    action = strategy.check_for_trade_action(0.11)
    print(f"Price 0.11: -> Action: {action}") # Expected: HOLD

    # Test 2: Price hits first take-profit
    action = strategy.check_for_trade_action(0.13) # 30% profit
    print(f"Price 0.13: -> Action: {action}") # Expected: SELL, 0.33
    
    # Test 3: Price drops back to entry. Stop is at breakeven now.
    action = strategy.check_for_trade_action(0.10)
    print(f"Price 0.10: -> Action: {action}") # Expected: SELL, 1.0

    # Test 4: Reset and test trailing stop
    print("\n--- Testing Trailing Stop ---")
    strategy = StrategyEngine("TEST", entry, quantity)
    strategy.check_for_trade_action(0.13) # Hit TP1, stop moves to breakeven
    strategy.take_profit_levels_hit[0] = True
    strategy.is_breakeven_stop = True
    strategy.stop_loss_price = entry

    # Price moons to 0.50
    strategy.check_for_trade_action(0.50)
    print(f"Highest Price: {strategy.highest_price_seen:.2f}, New Stop: {strategy.stop_loss_price:.2f}") # Expected stop at 0.50 * 0.8 = 0.40

    # Price corrects to 0.45
    action = strategy.check_for_trade_action(0.45)
    print(f"Price 0.45: -> Action: {action}") # Expected: HOLD

    # Price crashes below trailing stop
    action = strategy.check_for_trade_action(0.39)
    print(f"Price 0.39: -> Action: {action}") # Expected: SELL, 1.0