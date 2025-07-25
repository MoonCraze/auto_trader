import numpy as np
import pandas as pd
import asyncio
import random 

def generate_synthetic_data(initial_price, drift, volatility, time_steps):
    """
    Generates realistic synthetic OHLCV data for candlestick charts.
    """
    # 1. Generate a series of close prices using Geometric Brownian Motion
    shocks = np.random.normal(loc=drift, scale=volatility, size=time_steps)
    close_prices = initial_price * np.exp(np.cumsum(shocks))
    
    # 2. Build OHLCV data from the close prices
    ohlcv = []
    for i in range(len(close_prices)):
        if i == 0:
            open_price = initial_price
        else:
            # The open of this candle is the close of the last one
            open_price = ohlcv[i-1]['close']

        close_price = close_prices[i]

        # Create realistic wicks
        high_price = max(open_price, close_price) * random.uniform(1, 1.015)
        low_price = min(open_price, close_price) * random.uniform(0.985, 1)
        
        # Ensure open/close are within high/low
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        # Generate some volume
        volume = random.randint(1000, 20000)

        ohlcv.append({
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })

    # 3. Create the final DataFrame
    timestamps = pd.to_datetime(pd.date_range(start='2023-01-01', periods=time_steps, freq='5min'))
    df = pd.DataFrame(ohlcv)
    df['timestamp'] = timestamps
    
    return df

async def stream_data(data_df):
    """
    An asynchronous generator that yields data points one by one,
    simulating a real-time data feed.
    """
    for index, row in data_df.iterrows():
        yield row
        await asyncio.sleep(0.05) # This will now work correctly

# This part is for standalone testing of this file
if __name__ == '__main__':
    # Generate some sample data
    test_data = generate_synthetic_data(
        initial_price=0.01, 
        drift=0.001, 
        volatility=0.02, 
        time_steps=200
    )
    
    print("Generated Data Head:")
    print(test_data.head())
    print("\n--- Simulating Stream ---")

    async def run_test_stream():
        async for price_update in stream_data(test_data):
            print(f"Time: {price_update['timestamp'].time()}, Price: {price_update['price']:.6f}")
    
    asyncio.run(run_test_stream())