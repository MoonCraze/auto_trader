"""
Orchestrator Module

The central coordinator that ties everything together. It manages the lifecycle
of trades from signal to completion, coordinating between all system components.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .signal_queue import SignalQueue, TradingSignal
from .data_feeder import DataFeeder
from .portfolio_manager import PortfolioManager
from .strategy_engine import StrategyEngine, ActionType
from .execution_engine import ExecutionEngine


class TradingSession:
    """Represents an active trading session for a token"""
    
    def __init__(self, token_address: str, signal: TradingSignal):
        self.token_address = token_address
        self.signal = signal
        self.start_time = datetime.now()
        self.last_price_update = None
        self.current_price = None
        self.price_history = []
        self.actions_taken = []
        self.is_active = True
        self.completion_reason = None


class Orchestrator:
    """Central coordinator for the autonomous trading system"""
    
    def __init__(
        self,
        initial_sol_balance: float = 100.0,
        max_concurrent_positions: int = 5,
        price_update_interval: float = 1.0  # seconds
    ):
        # Initialize core components
        self.signal_queue = SignalQueue()
        self.data_feeder = DataFeeder()
        self.portfolio_manager = PortfolioManager(initial_sol_balance)
        self.strategy_engine = StrategyEngine(self.portfolio_manager)
        self.execution_engine = ExecutionEngine(self.portfolio_manager)
        
        # Configuration
        self.max_concurrent_positions = max_concurrent_positions
        self.price_update_interval = price_update_interval
        
        # State tracking
        self.active_sessions: Dict[str, TradingSession] = {}
        self.completed_sessions: List[TradingSession] = []
        self.is_running = False
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the autonomous trading system"""
        self.is_running = True
        self.logger.info("🚀 Auto Trader System Starting...")
        
        # Start main orchestration loop
        await asyncio.gather(
            self._signal_processing_loop(),
            self._price_monitoring_loop(),
            self._portfolio_monitoring_loop()
        )
    
    async def stop(self):
        """Stop the trading system gracefully"""
        self.is_running = False
        self.logger.info("🛑 Auto Trader System Stopping...")
        
        # Close all active sessions
        for session in self.active_sessions.values():
            session.is_active = False
            session.completion_reason = "System shutdown"
            self.completed_sessions.append(session)
        
        self.active_sessions.clear()
    
    async def _signal_processing_loop(self):
        """Main loop for processing trading signals"""
        while self.is_running:
            try:
                # Get next signal from queue
                signal = await self.signal_queue.get_next_signal()
                
                if signal:
                    await self._process_new_signal(signal)
                
                await asyncio.sleep(0.5)  # Small delay between signal checks
                
            except Exception as e:
                self.logger.error(f"Error in signal processing loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _price_monitoring_loop(self):
        """Monitor prices for all active trading sessions"""
        while self.is_running:
            try:
                tasks = []
                for token_address in list(self.active_sessions.keys()):
                    tasks.append(self._update_token_price(token_address))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(self.price_update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in price monitoring loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _portfolio_monitoring_loop(self):
        """Monitor portfolio status and log periodic updates"""
        while self.is_running:
            try:
                # Log portfolio summary every 30 seconds
                summary = self.portfolio_manager.get_portfolio_summary()
                
                self.logger.info(
                    f"💰 Portfolio: {summary['sol_balance']:.4f} SOL, "
                    f"Total Value: {summary['total_value']:.4f} SOL, "
                    f"Positions: {summary['positions_count']}, "
                    f"Unrealized P&L: {summary['total_unrealized_pnl']:.4f} SOL"
                )
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in portfolio monitoring loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def _process_new_signal(self, signal: TradingSignal):
        """Process a new trading signal"""
        token_address = signal.token_address
        
        # Check if we already have a position or active session
        if token_address in self.active_sessions:
            self.logger.warning(f"Signal ignored: Already trading {token_address}")
            return
        
        # Check position limits
        if len(self.active_sessions) >= self.max_concurrent_positions:
            self.logger.warning(f"Signal ignored: Max concurrent positions reached ({self.max_concurrent_positions})")
            return
        
        # Create new trading session
        session = TradingSession(token_address, signal)
        self.active_sessions[token_address] = session
        
        self.logger.info(f"🎯 Starting new trading session for {token_address}")
        
        # Initialize with starting price
        await self._update_token_price(token_address)
    
    async def _update_token_price(self, token_address: str):
        """Update price for a token and trigger strategy analysis"""
        if token_address not in self.active_sessions:
            return
            
        session = self.active_sessions[token_address]
        
        try:
            # Get current price (in real system, this would be from live feed)
            if not session.current_price:
                # Initialize with random price for demo
                session.current_price = 1.0 + (len(session.price_history) * 0.001)
            else:
                # Simulate price movement
                import random
                change = random.uniform(-0.05, 0.08)  # Slight upward bias
                session.current_price *= (1 + change)
            
            current_price = session.current_price
            session.last_price_update = datetime.now()
            session.price_history.append({
                'timestamp': session.last_price_update,
                'price': current_price
            })
            
            # Update portfolio with current price
            self.portfolio_manager.update_position_price(token_address, current_price)
            
            # Get strategy recommendation
            action = self.strategy_engine.analyze_token(token_address, current_price)
            
            # Execute action if needed
            if action.action != ActionType.HOLD:
                success = await self.execution_engine.execute_action(action, current_price)
                
                session.actions_taken.append({
                    'timestamp': datetime.now(),
                    'action': action.action.value,
                    'price': current_price,
                    'reason': action.reason,
                    'success': success
                })
                
                # Check if position is fully closed
                position = self.portfolio_manager.get_position(token_address)
                if not position:
                    await self._close_session(token_address, "Position fully closed")
            
        except Exception as e:
            self.logger.error(f"Error updating price for {token_address}: {str(e)}")
    
    async def _close_session(self, token_address: str, reason: str):
        """Close an active trading session"""
        if token_address not in self.active_sessions:
            return
        
        session = self.active_sessions[token_address]
        session.is_active = False
        session.completion_reason = reason
        
        # Move to completed sessions
        self.completed_sessions.append(session)
        del self.active_sessions[token_address]
        
        # Calculate session P&L
        total_pnl = 0
        for transaction in self.portfolio_manager.transaction_history:
            if transaction.token_address == token_address:
                if transaction.transaction_type == 'SELL':
                    total_pnl += transaction.sol_amount
                else:
                    total_pnl -= transaction.sol_amount
        
        duration = datetime.now() - session.start_time
        
        self.logger.info(
            f"✅ Session completed for {token_address}: {reason}. "
            f"Duration: {duration.total_seconds():.1f}s, "
            f"P&L: {total_pnl:.4f} SOL, "
            f"Actions taken: {len(session.actions_taken)}"
        )
    
    async def add_signal(self, token_address: str, signal_type: str = "GREEN_FLAG", priority: int = 1):
        """Convenience method to add a trading signal"""
        signal = TradingSignal(
            token_address=token_address,
            signal_type=signal_type,
            timestamp=datetime.now(),
            priority=priority
        )
        
        return await self.signal_queue.add_signal(signal)
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        return {
            'is_running': self.is_running,
            'active_sessions': len(self.active_sessions),
            'completed_sessions': len(self.completed_sessions),
            'queue_status': self.signal_queue.get_queue_status(),
            'portfolio_summary': self.portfolio_manager.get_portfolio_summary(),
            'active_tokens': list(self.active_sessions.keys()),
            'system_uptime': datetime.now().isoformat()
        }
    
    async def run_demo(self, duration_seconds: int = 60):
        """Run a demo trading session"""
        self.logger.info(f"🎮 Starting demo trading session for {duration_seconds} seconds")
        
        # Add demo signals
        await self.signal_queue.add_demo_signals()
        
        # Run for specified duration
        try:
            await asyncio.wait_for(self.start(), timeout=duration_seconds)
        except asyncio.TimeoutError:
            await self.stop()
            
        # Print final results
        self._print_demo_results()
    
    def _print_demo_results(self):
        """Print demo trading results"""
        print("\n" + "="*60)
        print("🎯 DEMO TRADING RESULTS")
        print("="*60)
        
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        
        print(f"💰 Final SOL Balance: {portfolio_summary['sol_balance']:.4f}")
        print(f"📊 Total Portfolio Value: {portfolio_summary['total_value']:.4f}")
        print(f"💹 Total Realized P&L: {portfolio_summary['total_realized_pnl']:.4f}")
        print(f"📈 Total Unrealized P&L: {portfolio_summary['total_unrealized_pnl']:.4f}")
        print(f"🎪 Completed Sessions: {len(self.completed_sessions)}")
        print(f"⚡ Active Positions: {portfolio_summary['positions_count']}")
        
        print("\n📋 Transaction History:")
        for i, tx in enumerate(self.portfolio_manager.transaction_history[-10:], 1):
            print(f"  {i}. {tx.transaction_type} {tx.quantity:.6f} {tx.token_address} "
                  f"at ${tx.price:.6f} for {tx.sol_amount:.4f} SOL")
        
        print("\n" + "="*60)