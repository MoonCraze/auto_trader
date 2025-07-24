import pandas as pd

# --- Strategy A: Buy the Dip using SMA Crossover ---
def find_sma_buy_signal(price_history: list[float], short_window: int = 10, long_window: int = 20) -> bool:
    """
    Returns True if the short-term SMA has just crossed above the long-term SMA.
    
    Args:
        price_history: A list of recent prices.
        short_window: The lookback period for the short SMA.
        long_window: The lookback period for the long SMA.
    """
    if len(price_history) < long_window + 1:
        # Not enough data to compute both SMAs and check for a crossover
        return False
    
    # Use pandas to easily calculate SMAs
    series = pd.Series(price_history)
    short_sma = series.rolling(window=short_window).mean()
    long_sma = series.rolling(window=long_window).mean()
    
    # The signal is a crossover:
    # 1. The short SMA was below the long SMA in the previous period.
    # 2. The short SMA is now above the long SMA in the current period.
    prev_short = short_sma.iloc[-2]
    prev_long = long_sma.iloc[-2]
    curr_short = short_sma.iloc[-1]
    curr_long = long_sma.iloc[-1]
    
    if prev_short < prev_long and curr_short > curr_long:
        print(f"[ENTRY SIGNAL] SMA Crossover detected! Short SMA ({curr_short:.6f}) crossed above Long SMA ({curr_long:.6f}).")
        return True
        
    return False

# --- Strategy B: Buy the Breakout ---
def find_breakout_buy_signal(price_history: list[float], lookback_period: int = 50) -> bool:
    """
    Returns True if the current price is the highest in the lookback period.

    Args:
        price_history: A list of recent prices.
        lookback_period: The number of recent periods to check for a high.
    """
    if len(price_history) < lookback_period:
        # Not enough data to determine a breakout
        return False

    recent_prices = price_history[-lookback_period:]
    current_price = recent_prices[-1]
    highest_in_lookback = max(recent_prices[:-1]) # Check against all but the current price

    if current_price > highest_in_lookback:
        print(f"[ENTRY SIGNAL] Breakout detected! Current price ({current_price:.6f}) surpassed recent high ({highest_in_lookback:.6f}).")
        return True
        
    return False

# --- Strategy Chooser ---
def check_for_entry_signal(price_history: list[float], strategy_type: str = 'sma') -> bool:
    """
    Checks for a buy signal using the specified strategy.
    
    Args:
        price_history: A list of recent prices.
        strategy_type: The strategy to use ('sma' or 'breakout').
    """
    if strategy_type == 'sma':
        return find_sma_buy_signal(price_history)
    elif strategy_type == 'breakout':
        return find_breakout_buy_signal(price_history)
    else:
        return False