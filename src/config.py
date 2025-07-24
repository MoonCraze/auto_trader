"""
Configuration settings for the Auto Trader system
"""

# Trading Strategy Parameters
STRATEGY_CONFIG = {
    'risk_percentage': 0.02,        # 2% of portfolio per trade
    'take_profit_1': 0.30,          # 30% gain for first take profit
    'take_profit_2': 0.75,          # 75% gain for second take profit  
    'initial_stop_loss': -0.15,     # -15% initial stop loss
    'trailing_stop_percentage': 0.20, # 20% trailing stop
    'scale_in_threshold': 0.50,     # Scale in at 50% profit
    'scale_in_percentage': 0.01,    # 1% of portfolio for scaling in
}

# System Configuration  
SYSTEM_CONFIG = {
    'max_concurrent_positions': 5,
    'price_update_interval': 1.0,   # seconds
    'signal_queue_max_size': 100,
    'default_sol_balance': 100.0,
}

# Simulation Parameters
SIMULATION_CONFIG = {
    'slippage': 0.005,              # 0.5% slippage
    'transaction_fee': 0.003,       # 0.3% transaction fee
    'initial_price': 1.0,
    'price_volatility': 0.3,
    'price_drift': 0.05,
}

# Database Configuration
DATABASE_CONFIG = {
    'db_path': 'portfolio.db',
    'backup_interval': 300,         # 5 minutes
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%H:%M:%S'
}