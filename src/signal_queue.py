"""
Signal Queue Module

Entry point for the trading system. Manages the queue of "green-flagged" tokens
that are ready for trading consideration.
"""

import asyncio
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import deque


@dataclass
class TradingSignal:
    """Represents a trading signal for a token"""
    token_address: str
    signal_type: str  # 'GREEN_FLAG', 'BULLISH', etc.
    timestamp: datetime
    metadata: dict = None
    priority: int = 1  # Higher numbers = higher priority


class SignalQueue:
    """Manages the queue of trading signals"""
    
    def __init__(self, max_size: int = 100):
        self.queue = deque(maxlen=max_size)
        self.processed_signals = []
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def add_signal(self, signal: TradingSignal) -> bool:
        """
        Add a new trading signal to the queue
        
        Args:
            signal: TradingSignal to add
            
        Returns:
            True if signal was added successfully
        """
        async with self._lock:
            try:
                # Check for duplicates
                if self._is_duplicate(signal):
                    self.logger.warning(f"Duplicate signal ignored for {signal.token_address}")
                    return False
                
                # Add to queue (sorted by priority)
                self._insert_by_priority(signal)
                
                self.logger.info(f"Added signal: {signal.token_address} "
                               f"({signal.signal_type}) with priority {signal.priority}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add signal: {str(e)}")
                return False
    
    async def get_next_signal(self) -> Optional[TradingSignal]:
        """
        Get the next signal from the queue
        
        Returns:
            Next TradingSignal or None if queue is empty
        """
        async with self._lock:
            if not self.queue:
                return None
            
            signal = self.queue.popleft()
            self.processed_signals.append(signal)
            
            self.logger.info(f"Processing signal: {signal.token_address}")
            return signal
    
    async def peek_next_signal(self) -> Optional[TradingSignal]:
        """
        Peek at the next signal without removing it from queue
        
        Returns:
            Next TradingSignal or None if queue is empty
        """
        async with self._lock:
            return self.queue[0] if self.queue else None
    
    def _is_duplicate(self, signal: TradingSignal) -> bool:
        """Check if a signal already exists in the queue"""
        for existing_signal in self.queue:
            if (existing_signal.token_address == signal.token_address and 
                existing_signal.signal_type == signal.signal_type):
                return True
        return False
    
    def _insert_by_priority(self, signal: TradingSignal):
        """Insert signal in queue based on priority (higher priority first)"""
        inserted = False
        for i, existing_signal in enumerate(self.queue):
            if signal.priority > existing_signal.priority:
                self.queue.insert(i, signal)
                inserted = True
                break
        
        if not inserted:
            self.queue.append(signal)
    
    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            'queue_size': len(self.queue),
            'processed_count': len(self.processed_signals),
            'max_size': self.max_size,
            'pending_signals': [
                {
                    'token_address': signal.token_address,
                    'signal_type': signal.signal_type,
                    'priority': signal.priority,
                    'timestamp': signal.timestamp.isoformat()
                }
                for signal in list(self.queue)
            ]
        }
    
    async def clear_queue(self):
        """Clear all signals from the queue"""
        async with self._lock:
            self.queue.clear()
            self.logger.info("Signal queue cleared")
    
    async def add_demo_signals(self):
        """Add some demo signals for testing"""
        demo_signals = [
            TradingSignal(
                token_address="DEMO_TOKEN_1",
                signal_type="GREEN_FLAG",
                timestamp=datetime.now(),
                metadata={"source": "demo", "confidence": 0.85},
                priority=2
            ),
            TradingSignal(
                token_address="DEMO_TOKEN_2", 
                signal_type="BULLISH",
                timestamp=datetime.now(),
                metadata={"source": "demo", "confidence": 0.75},
                priority=1
            ),
            TradingSignal(
                token_address="DEMO_TOKEN_3",
                signal_type="GREEN_FLAG",
                timestamp=datetime.now(),
                metadata={"source": "demo", "confidence": 0.90},
                priority=3
            )
        ]
        
        for signal in demo_signals:
            await self.add_signal(signal)
        
        self.logger.info(f"Added {len(demo_signals)} demo signals to queue")