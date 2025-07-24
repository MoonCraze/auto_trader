import config
from collections import defaultdict

class PortfolioManager:
    def __init__(self, initial_capital):
        self.sol_balance = initial_capital
        self.positions = defaultdict(lambda: {'tokens': 0, 'cost_basis': 0.0})
        self.trade_log = []

    def record_buy(self, token_symbol, sol_spent, tokens_received, price):
        """Records a purchase transaction."""
        if self.sol_balance < sol_spent:
            print("Error: Insufficient SOL balance to perform buy.")
            return False
        
        self.sol_balance -= sol_spent
        
        # Update position
        current_tokens = self.positions[token_symbol]['tokens']
        current_cost = self.positions[token_symbol]['cost_basis'] * current_tokens
        
        new_total_tokens = current_tokens + tokens_received
        new_total_cost = current_cost + sol_spent
        
        self.positions[token_symbol]['tokens'] = new_total_tokens
        self.positions[token_symbol]['cost_basis'] = new_total_cost / new_total_tokens if new_total_tokens > 0 else 0
        
        log_entry = f"BUY: {tokens_received:.2f} {token_symbol} at {price:.6f} for {sol_spent:.4f} SOL"
        self.trade_log.append(log_entry)
        print(log_entry)
        return True

    def record_sell(self, token_symbol, tokens_sold, sol_received, price):
        """Records a sale transaction."""
        if self.positions[token_symbol]['tokens'] < tokens_sold:
            print("Error: Not enough tokens to sell.")
            return False
            
        self.sol_balance += sol_received
        self.positions[token_symbol]['tokens'] -= tokens_sold
        
        # If all tokens are sold, remove the position to keep things clean
        if self.positions[token_symbol]['tokens'] < 1e-9: # Use a small threshold for float comparison
            del self.positions[token_symbol]

        log_entry = f"SELL: {tokens_sold:.2f} {token_symbol} at {price:.6f} for {sol_received:.4f} SOL"
        self.trade_log.append(log_entry)
        print(log_entry)
        return True

    def get_position_value(self, token_symbol, current_price):
        """Calculates the current SOL value of a token holding."""
        if token_symbol in self.positions:
            return self.positions[token_symbol]['tokens'] * current_price
        return 0.0

    def get_total_value(self, current_prices_dict):
        """Calculates the total portfolio value (SOL + all token holdings)."""
        total_value = self.sol_balance
        for token_symbol, position_data in self.positions.items():
            current_price = current_prices_dict.get(token_symbol, 0)
            total_value += position_data['tokens'] * current_price
        return total_value

    def display_status(self, current_prices_dict):
        """Prints a summary of the current portfolio status."""
        print("\n--- PORTFOLIO STATUS ---")
        print(f"SOL Balance: {self.sol_balance:.4f} SOL")
        print("Holdings:")
        if not self.positions:
            print("  None")
        for token, pos in self.positions.items():
            current_value = self.get_position_value(token, current_prices_dict.get(token, 0))
            pnl = (current_value - (pos['tokens'] * pos['cost_basis']))
            pnl_percent = (current_prices_dict.get(token, 0) / pos['cost_basis'] - 1) * 100 if pos['cost_basis'] > 0 else 0
            print(f"  - {token}: {pos['tokens']:.2f} tokens | Avg Cost: {pos['cost_basis']:.6f} | "
                  f"Current Value: {current_value:.4f} SOL | P&L: {pnl:+.4f} SOL ({pnl_percent:+.2f}%)")
        
        total_value = self.get_total_value(current_prices_dict)
        initial_capital = config.INITIAL_CAPITAL_SOL
        total_pnl = total_value - initial_capital
        total_pnl_percent = (total_value / initial_capital - 1) * 100
        print(f"Total Portfolio Value: {total_value:.4f} SOL")
        print(f"Total P&L: {total_pnl:+.4f} SOL ({total_pnl_percent:+.2f}%)")
        print("------------------------\n")

# This part is for standalone testing of this file
if __name__ == '__main__':
    # Initialize Portfolio Manager
    pm = PortfolioManager(initial_capital=config.INITIAL_CAPITAL_SOL)
    pm.display_status({})

    # Simulate a buy
    print("\n--- Simulating a BUY ---")
    token_a = "TESTCOIN"
    buy_price = 0.01
    sol_to_spend = 1.0 # As per 2% risk on 50 SOL
    tokens_bought = sol_to_spend / buy_price
    pm.record_buy(token_a, sol_to_spend, tokens_bought, buy_price)
    pm.display_status({token_a: 0.012}) # Price went up a bit

    # Simulate a sell
    print("\n--- Simulating a SELL ---")
    sell_price = 0.013
    tokens_to_sell = 50.0
    sol_gained = tokens_to_sell * sell_price
    pm.record_sell(token_a, tokens_to_sell, sol_gained, sell_price)
    pm.display_status({token_a: 0.013})