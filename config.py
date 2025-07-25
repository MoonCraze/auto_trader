# Portfolio and Risk Management
INITIAL_CAPITAL_SOL = 50.0
RISK_PER_TRADE_PERCENT = 0.02  # 2% of total capital per trade

# Strategy Parameters: Tiered Take-Profits
# Format: (profit_percentage_target, portion_to_sell)
# e.g., (0.3, 0.33) means sell 33% of the position when profit hits 30%
TAKE_PROFIT_TIERS = [
    (0.30, 0.33),  # At +30% profit, sell 33%
    (0.75, 0.33)   # At +75% profit, sell another 33%
]

# Strategy Parameters: Stop-Loss
INITIAL_STOP_LOSS_PERCENT = 0.15   # 15% below entry price
TRAILING_STOP_LOSS_PERCENT = 0.20  # Trail 20% below the highest price reached

# Data Simulation Parameters
SIM_INITIAL_PRICE = 0.01
SIM_DRIFT = 0.001       # Positive drift to simulate a general uptrend
SIM_VOLATILITY = 0.02   # Volatility to create price fluctuations
SIM_TIME_STEPS = 1000    # Number of price updates in our simulation