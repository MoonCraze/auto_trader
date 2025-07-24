"""
Portfolio Manager Module

The system's memory - tracks all current positions, available capital,
transaction history, and calculates P&L.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Position:
    """Represents a trading position"""
    token_address: str
    entry_price: float
    quantity: float
    entry_time: datetime
    cost_basis: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class Transaction:
    """Represents a trading transaction"""
    token_address: str
    transaction_type: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    timestamp: datetime
    sol_amount: float


class PortfolioManager:
    """Manages portfolio state, positions, and transactions"""
    
    def __init__(self, initial_sol_balance: float = 100.0, db_path: str = "portfolio.db"):
        self.sol_balance = initial_sol_balance
        self.positions: Dict[str, Position] = {}
        self.transaction_history: List[Transaction] = []
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                token_address TEXT PRIMARY KEY,
                entry_price REAL,
                quantity REAL,
                entry_time TEXT,
                cost_basis REAL,
                current_price REAL,
                unrealized_pnl REAL,
                realized_pnl REAL
            )
        ''')
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_address TEXT,
                transaction_type TEXT,
                quantity REAL,
                price REAL,
                timestamp TEXT,
                sol_amount REAL
            )
        ''')
        
        # Create portfolio state table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_state (
                id INTEGER PRIMARY KEY,
                sol_balance REAL,
                total_value REAL,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_position_size(self, risk_percentage: float = 0.02) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            risk_percentage: Percentage of portfolio to risk (default 2%)
            
        Returns:
            Amount of SOL to allocate for the trade
        """
        return self.sol_balance * risk_percentage
    
    def add_position(
        self, 
        token_address: str, 
        quantity: float, 
        entry_price: float,
        sol_spent: float
    ) -> bool:
        """
        Add a new position to the portfolio
        
        Args:
            token_address: Token identifier
            quantity: Amount of tokens purchased
            entry_price: Price at which tokens were bought
            sol_spent: Amount of SOL spent
            
        Returns:
            True if position was added successfully
        """
        if self.sol_balance < sol_spent:
            return False
        
        # Update SOL balance
        self.sol_balance -= sol_spent
        
        # Create position
        position = Position(
            token_address=token_address,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            cost_basis=sol_spent,
            current_price=entry_price
        )
        
        self.positions[token_address] = position
        
        # Record transaction
        transaction = Transaction(
            token_address=token_address,
            transaction_type='BUY',
            quantity=quantity,
            price=entry_price,
            timestamp=datetime.now(),
            sol_amount=sol_spent
        )
        
        self.transaction_history.append(transaction)
        self._save_to_db()
        
        return True
    
    def partial_sell(
        self, 
        token_address: str, 
        percentage: float, 
        current_price: float
    ) -> Optional[float]:
        """
        Sell a percentage of a position
        
        Args:
            token_address: Token to sell
            percentage: Percentage of position to sell (0.0 to 1.0)
            current_price: Current market price
            
        Returns:
            SOL received from sale, or None if position doesn't exist
        """
        if token_address not in self.positions:
            return None
        
        position = self.positions[token_address]
        sell_quantity = position.quantity * percentage
        sol_received = sell_quantity * current_price
        
        # Update position
        position.quantity -= sell_quantity
        position.realized_pnl += sol_received - (position.cost_basis * percentage)
        
        # Update SOL balance
        self.sol_balance += sol_received
        
        # Remove position if fully sold
        if position.quantity <= 0:
            del self.positions[token_address]
        
        # Record transaction
        transaction = Transaction(
            token_address=token_address,
            transaction_type='SELL',
            quantity=sell_quantity,
            price=current_price,
            timestamp=datetime.now(),
            sol_amount=sol_received
        )
        
        self.transaction_history.append(transaction)
        self._save_to_db()
        
        return sol_received
    
    def update_position_price(self, token_address: str, current_price: float):
        """Update the current price and unrealized P&L for a position"""
        if token_address in self.positions:
            position = self.positions[token_address]
            position.current_price = current_price
            
            current_value = position.quantity * current_price
            position.unrealized_pnl = current_value - position.cost_basis + position.realized_pnl
    
    def get_position(self, token_address: str) -> Optional[Position]:
        """Get position details for a specific token"""
        return self.positions.get(token_address)
    
    def get_total_portfolio_value(self) -> float:
        """Calculate total portfolio value in SOL"""
        total_value = self.sol_balance
        
        for position in self.positions.values():
            total_value += position.quantity * position.current_price
        
        return total_value
    
    def get_portfolio_summary(self) -> Dict:
        """Get a summary of the current portfolio state"""
        total_value = self.get_total_portfolio_value()
        
        return {
            'sol_balance': self.sol_balance,
            'total_value': total_value,
            'positions_count': len(self.positions),
            'total_realized_pnl': sum(pos.realized_pnl for pos in self.positions.values()),
            'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values()),
            'positions': {addr: asdict(pos) for addr, pos in self.positions.items()}
        }
    
    def _save_to_db(self):
        """Save current state to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear and update positions
        cursor.execute('DELETE FROM positions')
        for position in self.positions.values():
            cursor.execute('''
                INSERT INTO positions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.token_address,
                position.entry_price,
                position.quantity,
                position.entry_time.isoformat(),
                position.cost_basis,
                position.current_price,
                position.unrealized_pnl,
                position.realized_pnl
            ))
        
        # Update portfolio state
        cursor.execute('DELETE FROM portfolio_state')
        cursor.execute('''
            INSERT INTO portfolio_state (id, sol_balance, total_value, last_updated) 
            VALUES (1, ?, ?, ?)
        ''', (self.sol_balance, self.get_total_portfolio_value(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()