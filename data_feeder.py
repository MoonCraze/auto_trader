import pandas as pd
import asyncio
from geckoterminal_client import GeckoTerminalClient

async def get_historical_data(pool_address: str, network: str = 'solana') -> pd.DataFrame:
    """
    Fetches historical OHLCV data from GeckoTerminal.
    
    Args:
        pool_address: The pool address to fetch data for
        network: The network (default: 'solana')
    
    Returns:
        DataFrame with OHLCV data
    """
    client = GeckoTerminalClient()
    df = await client.get_ohlcv(network, pool_address)
    if df is None:
        raise ValueError(f"Failed to fetch data for pool {pool_address}")
    return df

async def stream_data(pool_address: str, network: str = 'solana'):
    """
    An asynchronous generator that yields real-time data points from GeckoTerminal.
    
    Args:
        pool_address: The pool address to stream data for
        network: The network (default: 'solana')
    """
    client = GeckoTerminalClient()
    while True:
        try:
            latest = await client.get_latest_candle(network, pool_address)
            if latest:
                yield latest
            # Wait for 5 minutes before next update (GeckoTerminal data is in 5-min candles)
            await asyncio.sleep(300)
        except Exception as e:
            print(f"Error streaming data: {e}")
            await asyncio.sleep(5)  # Short delay on error before retry

# This part is for standalone testing of this file
if __name__ == '__main__':
    async def test():
        # Test historical data
        pool_address = 'DCTvr8KcsR3Da4fQXbPdhEH87rW7y2T34U8YAFww2sCp'
        print("Fetching historical data...")
        df = await get_historical_data(pool_address)
        print("\nHistorical Data Head:")
        print(df.head())
        
        print("\n--- Starting Live Stream ---")
        async for candle in stream_data(pool_address):
            print(f"Time: {candle['timestamp']}, Close: {candle['close']:.6f}, Volume: {candle['volume']:.2f}")

    asyncio.run(test())