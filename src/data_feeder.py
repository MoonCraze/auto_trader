"""
Data Feeder Module

Responsible for providing real-time and historical price/volume data for tokens.
Uses Geometric Brownian Motion to generate simulated market data.
"""

import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta
from typing import Generator, Optional


class DataFeeder:
    """Generates and streams simulated market data for tokens"""
    
    def __init__(self):
        self.active_feeds = {}
    
    def generate_synthetic_data(
        self, 
        initial_price: float = 1.0,
        drift: float = 0.05,
        volatility: float = 0.3,
        time_steps: int = 1000,
        dt: float = 1/24/60  # 1 minute intervals
    ) -> pd.DataFrame:
        """
        Generate synthetic price data using Geometric Brownian Motion
        
        Args:
            initial_price: Starting price of the token
            drift: Expected return (annual)
            volatility: Annual volatility
            time_steps: Number of data points to generate
            dt: Time step in years (1/24/60 = 1 minute)
        
        Returns:
            DataFrame with timestamp and price columns
        """
        # Generate random shocks
        np.random.seed(42)  # For reproducible results
        shocks = np.random.normal(0, 1, time_steps)
        
        # Calculate price changes using GBM formula
        drift_term = (drift - 0.5 * volatility**2) * dt
        diffusion_term = volatility * np.sqrt(dt) * shocks
        
        # Calculate log returns
        log_returns = drift_term + diffusion_term
        
        # Convert to price levels
        prices = initial_price * np.exp(np.cumsum(log_returns))
        
        # Create timestamps
        start_time = datetime.now()
        timestamps = [start_time + timedelta(minutes=i) for i in range(time_steps)]
        
        # Create DataFrame
        data = pd.DataFrame({
            'timestamp': timestamps,
            'price': prices,
            'volume': np.random.exponential(1000, time_steps)  # Simulated volume
        })
        
        return data
    
    async def start_price_feed(
        self, 
        token_address: str, 
        initial_price: float = 1.0,
        drift: float = 0.05,
        volatility: float = 0.3
    ) -> Generator[dict, None, None]:
        """
        Start streaming price data for a token
        
        Args:
            token_address: Unique identifier for the token
            initial_price: Starting price
            drift: Expected return
            volatility: Price volatility
            
        Yields:
            Dict with timestamp, price, and volume data
        """
        data = self.generate_synthetic_data(initial_price, drift, volatility)
        
        for _, row in data.iterrows():
            yield {
                'token_address': token_address,
                'timestamp': row['timestamp'],
                'price': row['price'],
                'volume': row['volume']
            }
            await asyncio.sleep(0.1)  # Simulate real-time delay
    
    async def get_current_price(self, token_address: str) -> Optional[float]:
        """Get the current price of a token"""
        # In a real implementation, this would fetch from an API
        # For simulation, return a random price around 1.0
        return np.random.normal(1.0, 0.1)