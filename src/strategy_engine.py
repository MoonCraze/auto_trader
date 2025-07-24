"""
Strategy Engine Module

The "Brain" of the trading system. Implements the core trading logic:
- Risk-based position sizing
- Tiered take-profits (30%, 75% levels)
- Trailing stop-loss mechanism
- Position re-evaluation for scaling in
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

from .portfolio_manager import PortfolioManager, Position


class ActionType(Enum):
    """Types of trading actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SCALE_IN = "SCALE_IN"


@dataclass
class TradingAction:
    """Represents a trading decision"""
    action: ActionType
    token_address: str
    percentage: float = 0.0  # For sells, percentage of position
    sol_amount: float = 0.0  # For buys, amount of SOL to spend
    reason: str = ""
    stop_loss_price: float = 0.0
    take_profit_levels: Dict[str, float] = None


@dataclass
class PositionState:
    """Tracks the state of position management"""
    entry_price: float
    highest_price: float
    stop_loss_price: float
    take_profit_1_hit: bool = False  # 30% level
    take_profit_2_hit: bool = False  # 75% level
    breakeven_reached: bool = False


class StrategyEngine:
    """Core trading logic and decision engine"""
    
    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio = portfolio_manager
        self.position_states: Dict[str, PositionState] = {}
        
        # Strategy parameters
        self.risk_percentage = 0.02  # 2% of portfolio per trade
        self.take_profit_1 = 0.30    # 30% gain
        self.take_profit_2 = 0.75    # 75% gain
        self.initial_stop_loss = -0.15   # -15% stop loss
        self.trailing_stop_percentage = 0.20  # 20% trailing stop
        self.scale_in_threshold = 0.50   # Scale in at 50% profit
        self.scale_in_percentage = 0.01  # 1% of portfolio for scaling in
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def analyze_token(self, token_address: str, current_price: float) -> TradingAction:
        """
        Analyze a token and determine the appropriate trading action
        
        Args:
            token_address: Token to analyze
            current_price: Current market price
            
        Returns:
            TradingAction with the recommended action
        """
        position = self.portfolio.get_position(token_address)
        
        if position is None:
            # No existing position - consider opening one
            return self._evaluate_entry(token_address, current_price)
        else:
            # Existing position - manage it
            return self._manage_position(token_address, current_price, position)
    
    def _evaluate_entry(self, token_address: str, current_price: float) -> TradingAction:
        """Evaluate whether to enter a new position"""
        # Calculate position size based on risk management
        sol_amount = self.portfolio.calculate_position_size(self.risk_percentage)
        
        if sol_amount < 0.01:  # Minimum trade size
            return TradingAction(
                action=ActionType.HOLD,
                token_address=token_address,
                reason="Insufficient capital for minimum trade size"
            )
        
        # Calculate stop loss price
        stop_loss_price = current_price * (1 + self.initial_stop_loss)
        
        self.logger.info(f"Entry signal for {token_address} at ${current_price:.6f}, "
                        f"allocating {sol_amount:.4f} SOL")
        
        return TradingAction(
            action=ActionType.BUY,
            token_address=token_address,
            sol_amount=sol_amount,
            stop_loss_price=stop_loss_price,
            reason=f"Initial entry with {self.risk_percentage*100}% portfolio allocation",
            take_profit_levels={
                "tp1": current_price * (1 + self.take_profit_1),
                "tp2": current_price * (1 + self.take_profit_2)
            }
        )
    
    def _manage_position(
        self, 
        token_address: str, 
        current_price: float, 
        position: Position
    ) -> TradingAction:
        """Manage an existing position"""
        
        # Initialize position state if it doesn't exist
        if token_address not in self.position_states:
            self.position_states[token_address] = PositionState(
                entry_price=position.entry_price,
                highest_price=position.entry_price,
                stop_loss_price=position.entry_price * (1 + self.initial_stop_loss)
            )
        
        state = self.position_states[token_address]
        
        # Update highest price reached
        if current_price > state.highest_price:
            state.highest_price = current_price
        
        # Calculate percentage change from entry
        pct_change = (current_price - state.entry_price) / state.entry_price
        
        # Check for stop loss trigger
        if current_price <= state.stop_loss_price:
            return self._create_stop_loss_action(token_address, current_price, pct_change)
        
        # Check for take profit levels
        if not state.take_profit_1_hit and pct_change >= self.take_profit_1:
            return self._create_take_profit_1_action(token_address, current_price, state)
        
        if not state.take_profit_2_hit and pct_change >= self.take_profit_2:
            return self._create_take_profit_2_action(token_address, current_price, state)
        
        # Update trailing stop loss
        self._update_trailing_stop(state, current_price)
        
        # Check for scale-in opportunity
        if (pct_change >= self.scale_in_threshold and 
            not state.take_profit_1_hit and 
            self.portfolio.sol_balance > self.portfolio.calculate_position_size(self.scale_in_percentage)):
            
            return self._create_scale_in_action(token_address, current_price)
        
        # Default action is to hold
        return TradingAction(
            action=ActionType.HOLD,
            token_address=token_address,
            reason=f"Holding position, P&L: {pct_change*100:.2f}%, "
                   f"Stop: ${state.stop_loss_price:.6f}"
        )
    
    def _create_stop_loss_action(
        self, 
        token_address: str, 
        current_price: float, 
        pct_change: float
    ) -> TradingAction:
        """Create a stop loss sell action"""
        self.logger.warning(f"Stop loss triggered for {token_address} at ${current_price:.6f}, "
                           f"Loss: {pct_change*100:.2f}%")
        
        # Clean up position state
        if token_address in self.position_states:
            del self.position_states[token_address]
        
        return TradingAction(
            action=ActionType.SELL,
            token_address=token_address,
            percentage=1.0,  # Sell entire position
            reason=f"Stop loss triggered at {pct_change*100:.2f}% loss"
        )
    
    def _create_take_profit_1_action(
        self, 
        token_address: str, 
        current_price: float, 
        state: PositionState
    ) -> TradingAction:
        """Create first take profit action (30% gain, sell 33%)"""
        state.take_profit_1_hit = True
        state.breakeven_reached = True
        state.stop_loss_price = state.entry_price  # Move stop to breakeven
        
        self.logger.info(f"Take Profit 1 hit for {token_address} at ${current_price:.6f}, "
                        f"selling 33% of position")
        
        return TradingAction(
            action=ActionType.SELL,
            token_address=token_address,
            percentage=0.33,
            reason=f"Take profit 1 at +{self.take_profit_1*100}% gain, stop moved to breakeven"
        )
    
    def _create_take_profit_2_action(
        self, 
        token_address: str, 
        current_price: float, 
        state: PositionState
    ) -> TradingAction:
        """Create second take profit action (75% gain, sell another 33%)"""
        state.take_profit_2_hit = True
        
        self.logger.info(f"Take Profit 2 hit for {token_address} at ${current_price:.6f}, "
                        f"selling another 33% of position")
        
        return TradingAction(
            action=ActionType.SELL,
            token_address=token_address,
            percentage=0.33,
            reason=f"Take profit 2 at +{self.take_profit_2*100}% gain, letting runner continue"
        )
    
    def _create_scale_in_action(self, token_address: str, current_price: float) -> TradingAction:
        """Create a scale-in buy action"""
        sol_amount = self.portfolio.calculate_position_size(self.scale_in_percentage)
        
        self.logger.info(f"Scaling into {token_address} at ${current_price:.6f}, "
                        f"adding {sol_amount:.4f} SOL")
        
        return TradingAction(
            action=ActionType.SCALE_IN,
            token_address=token_address,
            sol_amount=sol_amount,
            reason=f"Scaling in at +{self.scale_in_threshold*100}% profit"
        )
    
    def _update_trailing_stop(self, state: PositionState, current_price: float):
        """Update the trailing stop loss based on highest price reached"""
        if state.breakeven_reached:
            # Calculate trailing stop from highest price
            trailing_stop = state.highest_price * (1 - self.trailing_stop_percentage)
            
            # Only move stop loss up, never down
            if trailing_stop > state.stop_loss_price:
                state.stop_loss_price = trailing_stop
                self.logger.debug(f"Trailing stop updated to ${state.stop_loss_price:.6f}")
    
    def get_position_summary(self, token_address: str) -> Dict:
        """Get a summary of position management state"""
        position = self.portfolio.get_position(token_address)
        state = self.position_states.get(token_address)
        
        if not position or not state:
            return {}
        
        current_pct = (position.current_price - state.entry_price) / state.entry_price
        
        return {
            'token_address': token_address,
            'entry_price': state.entry_price,
            'current_price': position.current_price,
            'highest_price': state.highest_price,
            'stop_loss_price': state.stop_loss_price,
            'current_pnl_pct': current_pct * 100,
            'unrealized_pnl': position.unrealized_pnl,
            'realized_pnl': position.realized_pnl,
            'take_profit_1_hit': state.take_profit_1_hit,
            'take_profit_2_hit': state.take_profit_2_hit,
            'breakeven_reached': state.breakeven_reached,
            'quantity': position.quantity,
            'cost_basis': position.cost_basis
        }