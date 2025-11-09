import aiohttp
import time
from datetime import datetime
import pandas as pd
import asyncio

class GeckoTerminalClient:
    def __init__(self):
        self.base_url = "https://api.geckoterminal.com/api/v2"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests

    async def _make_request(self, endpoint: str) -> dict:
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        url = f"{self.base_url}/{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Error fetching data: {response.status}")
                        return None
                    self.last_request_time = time.time()
                    return await response.json()
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    async def get_ohlcv(self, network: str, pool_address: str, interval: str = "minute", aggregate: int = 5, limit: int = 1000) -> pd.DataFrame:
        """
        Fetch OHLCV data for a specific pool
        
        Args:
            network: Network name (e.g., 'solana')
            pool_address: Pool contract address
            interval: Time interval ('minute')
            aggregate: Number of intervals to aggregate (e.g., 5 for 5-minute candles)
            limit: Number of candles to fetch
        """
        endpoint = f"networks/{network}/pools/{pool_address}/ohlcv/{interval}?aggregate={aggregate}&limit={limit}"
        data = await self._make_request(endpoint)
        
        if not data or 'data' not in data or 'attributes' not in data['data']:
            return None

        ohlcv_list = data['data']['attributes'].get('ohlcv_list', [])
        if not ohlcv_list:
            return None

        # Convert the data to a pandas DataFrame
        df = pd.DataFrame(ohlcv_list, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Ensure correct data types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Sort by timestamp to ensure correct order
        df = df.sort_values('timestamp')
        
        return df

    async def get_latest_candle(self, network: str, pool_address: str) -> dict:
        """Get the most recent candle data"""
        df = await self.get_ohlcv(network, pool_address, limit=1)
        if df is None or df.empty:
            return None
            
        latest = df.iloc[-1]
        return {
            'timestamp': latest['timestamp'],
            'open': float(latest['open']),
            'high': float(latest['high']),
            'low': float(latest['low']),
            'close': float(latest['close']),
            'volume': float(latest['volume'])
        }

# Test the client
if __name__ == "__main__":
    async def test():
        client = GeckoTerminalClient()
        # Test with a Solana pool
        df = await client.get_ohlcv('solana', 'DCTvr8KcsR3Da4fQXbPdhEH87rW7y2T34U8YAFww2sCp')
        if df is not None:
            print("Latest 5 candles:")
            print(df.tail())
            
            latest = await client.get_latest_candle('solana', 'DCTvr8KcsR3Da4fQXbPdhEH87rW7y2T34U8YAFww2sCp')
            print("\nLatest candle:")
            print(latest)

    asyncio.run(test())