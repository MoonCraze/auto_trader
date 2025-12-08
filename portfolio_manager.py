import config
from collections import defaultdict
from datetime import datetime
from sqlalchemy.orm import Session
from database import Trade, Position, PortfolioSnapshot, SessionLocal
import json

class PortfolioManager:
    def __init__(self, initial_capital, wallet_address=None, db_session=None):
        self.sol_balance = initial_capital
        self.positions = defaultdict(lambda: {'tokens': 0, 'cost_basis': 0.0})
        self.trade_log = []
        self.wallet_address = wallet_address
        self.db_session = db_session or SessionLocal()
        self.initial_capital = initial_capital
        
        # Load existing positions from database if wallet_address provided
        if wallet_address and db_session:
            self._load_positions_from_db()

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
        
        # Persist to database if wallet_address provided
        if self.wallet_address and self.db_session:
            self._update_position_in_db(token_symbol)
        
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
        
        # Persist to database if wallet_address provided
        if self.wallet_address and self.db_session:
            self._update_position_in_db(token_symbol)
        
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

    def _load_positions_from_db(self):
        """Load existing positions from database for this wallet"""
        if not self.wallet_address or not self.db_session:
            return
            
        db_positions = self.db_session.query(Position).filter(
            Position.wallet_address == self.wallet_address
        ).all()
        
        for pos in db_positions:
            self.positions[pos.token_symbol] = {
                'tokens': pos.tokens,
                'cost_basis': pos.cost_basis
            }
        
        print(f"Loaded {len(db_positions)} positions from database for {self.wallet_address[:8]}...")

    def _update_position_in_db(self, token_symbol):
        """Update or create position in database"""
        if not self.wallet_address or not self.db_session:
            return
            
        # Find existing position or create new
        db_position = self.db_session.query(Position).filter(
            Position.wallet_address == self.wallet_address,
            Position.token_symbol == token_symbol
        ).first()
        
        if token_symbol in self.positions and self.positions[token_symbol]['tokens'] > 1e-9:
            # Update or create position
            if db_position:
                db_position.tokens = self.positions[token_symbol]['tokens']
                db_position.cost_basis = self.positions[token_symbol]['cost_basis']
                db_position.last_updated = datetime.utcnow()
            else:
                db_position = Position(
                    wallet_address=self.wallet_address,
                    token_address=f"unknown_{token_symbol}",  # Token address would need to be passed
                    token_symbol=token_symbol,
                    tokens=self.positions[token_symbol]['tokens'],
                    cost_basis=self.positions[token_symbol]['cost_basis']
                )
                self.db_session.add(db_position)
        elif db_position:
            # Position closed, remove from database
            self.db_session.delete(db_position)
        
        self.db_session.commit()

    def save_portfolio_snapshot(self, current_prices_dict):
        """Save current portfolio state as snapshot for historical tracking"""
        if not self.wallet_address or not self.db_session:
            return
            
        total_value = self.get_total_value(current_prices_dict)
        overall_pnl = total_value - self.initial_capital
        
        snapshot = PortfolioSnapshot(
            wallet_address=self.wallet_address,
            timestamp=datetime.utcnow(),
            sol_balance=self.sol_balance,
            total_value=total_value,
            overall_pnl=overall_pnl
        )
        self.db_session.add(snapshot)
        self.db_session.commit()

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