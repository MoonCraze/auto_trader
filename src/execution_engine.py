"""
Execution Engine Module

The system's hands - executes trading orders from the Strategy Engine.
In simulation mode, it updates the Portfolio Manager directly.
In production, it would interact with DEX aggregators like Jupiter.
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime

from .portfolio_manager import PortfolioManager
from .strategy_engine import TradingAction, ActionType


class ExecutionEngine:
    """Executes trading orders and updates portfolio state"""
    
    def __init__(self, portfolio_manager: PortfolioManager, simulation_mode: bool = True):
        self.portfolio = portfolio_manager
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(__name__)
        
        # Simulation parameters
        self.slippage = 0.005  # 0.5% slippage
        self.transaction_fee = 0.003  # 0.3% transaction fee
    
    async def execute_action(self, action: TradingAction, current_price: float) -> bool:
        """
        Execute a trading action
        
        Args:
            action: TradingAction to execute
            current_price: Current market price
            
        Returns:
            True if execution was successful
        """
        try:
            if action.action == ActionType.BUY or action.action == ActionType.SCALE_IN:
                return await self._execute_buy(action, current_price)
            elif action.action == ActionType.SELL:
                return await self._execute_sell(action, current_price)
            elif action.action == ActionType.HOLD:
                self.logger.debug(f"Holding position for {action.token_address}: {action.reason}")
                return True
            else:
                self.logger.warning(f"Unknown action type: {action.action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Execution failed for {action.token_address}: {str(e)}")
            return False
    
    async def _execute_buy(self, action: TradingAction, current_price: float) -> bool:
        """Execute a buy order"""
        if self.simulation_mode:
            return await self._simulate_buy(action, current_price)
        else:
            # In production, this would call Jupiter API or similar
            return await self._real_buy(action, current_price)
    
    async def _execute_sell(self, action: TradingAction, current_price: float) -> bool:
        """Execute a sell order"""
        if self.simulation_mode:
            return await self._simulate_sell(action, current_price)
        else:
            # In production, this would call Jupiter API or similar
            return await self._real_sell(action, current_price)
    
    async def _simulate_buy(self, action: TradingAction, current_price: float) -> bool:
        """Simulate a buy order execution"""
        # Apply slippage (price moves against us)
        execution_price = current_price * (1 + self.slippage)
        
        # Calculate quantity after fees
        sol_after_fees = action.sol_amount * (1 - self.transaction_fee)
        quantity = sol_after_fees / execution_price
        
        # Add position to portfolio
        success = self.portfolio.add_position(
            token_address=action.token_address,
            quantity=quantity,
            entry_price=execution_price,
            sol_spent=action.sol_amount
        )
        
        if success:
            self.logger.info(
                f"BUY executed: {quantity:.6f} tokens of {action.token_address} "
                f"at ${execution_price:.6f} for {action.sol_amount:.4f} SOL"
            )
        else:
            self.logger.error(f"BUY failed: Insufficient SOL balance")
        
        # Simulate network delay
        await asyncio.sleep(0.1)
        return success
    
    async def _simulate_sell(self, action: TradingAction, current_price: float) -> bool:
        """Simulate a sell order execution"""
        position = self.portfolio.get_position(action.token_address)
        if not position:
            self.logger.error(f"SELL failed: No position found for {action.token_address}")
            return False
        
        # Apply slippage (price moves against us)
        execution_price = current_price * (1 - self.slippage)
        
        # Execute partial sell
        sol_received = self.portfolio.partial_sell(
            token_address=action.token_address,
            percentage=action.percentage,
            current_price=execution_price
        )
        
        if sol_received is not None:
            # Apply transaction fees
            sol_after_fees = sol_received * (1 - self.transaction_fee)
            
            self.logger.info(
                f"SELL executed: {action.percentage*100:.1f}% of {action.token_address} "
                f"at ${execution_price:.6f} for {sol_after_fees:.4f} SOL (after fees)"
            )
            
            # Simulate network delay
            await asyncio.sleep(0.1)
            return True
        else:
            self.logger.error(f"SELL failed for {action.token_address}")
            return False
    
    async def _real_buy(self, action: TradingAction, current_price: float) -> bool:
        """Execute a real buy order via Jupiter API (placeholder)"""
        # This would be implemented with actual Jupiter API calls
        self.logger.info("Real trading not implemented - use simulation mode")
        return False
    
    async def _real_sell(self, action: TradingAction, current_price: float) -> bool:
        """Execute a real sell order via Jupiter API (placeholder)"""
        # This would be implemented with actual Jupiter API calls
        self.logger.info("Real trading not implemented - use simulation mode")
        return False
    
    def get_execution_stats(self) -> dict:
        """Get execution statistics"""
        return {
            'simulation_mode': self.simulation_mode,
            'slippage': self.slippage,
            'transaction_fee': self.transaction_fee,
            'total_transactions': len(self.portfolio.transaction_history)
        }