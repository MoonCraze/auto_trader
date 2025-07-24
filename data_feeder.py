import numpy as np
import pandas as pd
import asyncio
import random 

def generate_synthetic_data(initial_price, drift, volatility, time_steps):
    """
    Generates synthetic cryptocurrency price data using Geometric Brownian Motion.

    Args:
        initial_price (float): The starting price of the token.
        drift (float): The long-term trend (e.g., 0.001 for a slight uptrend).
        volatility (float): The randomness or daily price fluctuation (e.g., 0.02).
        time_steps (int): The number of price points to generate.

    Returns:
        pandas.DataFrame: A DataFrame with 'timestamp' and 'price' columns.
    """
    shocks = np.random.normal(loc=drift, scale=volatility, size=time_steps)
    prices = initial_price * np.exp(np.cumsum(shocks))
    timestamps = pd.to_datetime(pd.date_range(start='2023-01-01', periods=time_steps, freq='1min'))
    
    transactions = []
    for price in prices:
        if random.random() > 0.7: # 30% chance of a transaction at each price tick
            tx = {
                'type': 'BUY' if random.random() > 0.5 else 'SELL',
                'sol_amount': round(random.uniform(0.1, 2.0), 4),
                'price': round(price, 6)
            }
            transactions.append(tx)
        else:
            transactions.append(None)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'price': prices,
        'transaction': transactions # Add new column
    })
    
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
        time_steps=100
    )
    
    print("Generated Data Head:")
    print(test_data.head())
    print("\n--- Simulating Stream ---")

    async def run_test_stream():
        async for price_update in stream_data(test_data):
            print(f"Time: {price_update['timestamp'].time()}, Price: {price_update['price']:.6f}")
    
    asyncio.run(run_test_stream())