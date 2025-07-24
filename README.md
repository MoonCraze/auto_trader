# Auto Trader - Autonomous Crypto Trading Execution Engine

An intelligent, modular crypto trading system that autonomously manages the complete lifecycle of trades for "green-flagged" tokens to maximize profit through systematic risk management and dynamic position management.

## 🚀 System Overview

This system implements a robust, event-driven architecture for autonomous crypto trading with the following key features:

- **Risk-Based Position Sizing**: Automatically calculates position sizes based on portfolio risk (default 2%)
- **Tiered Take-Profits**: Systematically locks in profits at 30% and 75% gain levels
- **Trailing Stop-Loss**: Dynamic stop-loss that moves up with profits to protect gains
- **Multi-Token Management**: Handles multiple positions concurrently with proper risk controls
- **Complete Simulation Mode**: Full backtesting capabilities with realistic market simulation

## 🏗️ Architecture

### Core Components

- **Signal Queue**: Entry point for trading signals with priority-based processing
- **Orchestrator**: Central coordinator managing the complete trading lifecycle
- **Data Feeder**: Provides real-time and historical price data (simulated for demo)
- **Portfolio Manager**: Tracks positions, balances, and P&L with database persistence
- **Strategy Engine**: Core trading logic implementing the systematic methodology
- **Execution Engine**: Handles order execution with slippage and fee simulation

### Trading Methodology

#### Stage 1: Position Sizing & Entry
- **Risk Management**: Fixed 2% of portfolio allocated per trade
- **Entry Logic**: Immediate purchase when signal is received
- **Stop-Loss**: Initial -15% stop-loss set at entry

#### Stage 2: Active Position Management
- **Take Profit 1**: At +30% gain, sell 33% of position, move stop to breakeven
- **Take Profit 2**: At +75% gain, sell another 33% of position
- **Runner Position**: Remaining ~34% continues with trailing stop-loss
- **Trailing Stop**: 20% below highest price reached after breakeven

#### Stage 3: Advanced Features
- **Scale-In**: Add to winning positions at +50% profit (1% of portfolio)
- **Position Limits**: Maximum 5 concurrent positions
- **Dynamic Management**: Continuous price monitoring and decision making

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/MoonCraze/auto_trader.git
cd auto_trader

# Install dependencies
pip install -r requirements.txt
```

## 🎮 Usage

### Quick Demo
```bash
# Run a 30-second demo with simulated trading
python demo.py
```

### Full System
```bash
# Run demo mode with custom settings
python main.py --demo --duration 60 --balance 100

# Run with verbose logging
python main.py --demo --verbose

# Get help
python main.py --help
```

### Example Output
```
🎯 DEMO TRADING RESULTS
============================================================
💰 Final SOL Balance: 49.5063
📊 Total Portfolio Value: 52.9030
💹 Total Realized P&L: 0.5060
📈 Total Unrealized P&L: 0.9623
🎪 Completed Sessions: 3
⚡ Active Positions: 3
```

## 🔧 Configuration

The system is highly configurable through `src/config.py`:

```python
STRATEGY_CONFIG = {
    'risk_percentage': 0.02,        # 2% of portfolio per trade
    'take_profit_1': 0.30,          # 30% gain for first take profit
    'take_profit_2': 0.75,          # 75% gain for second take profit  
    'initial_stop_loss': -0.15,     # -15% initial stop loss
    'trailing_stop_percentage': 0.20, # 20% trailing stop
    'scale_in_threshold': 0.50,     # Scale in at 50% profit
}
```

## 📊 Features

### Risk Management
- **Portfolio-Based Sizing**: Never risk more than 2% on any single trade
- **Position Limits**: Maximum concurrent positions to prevent overexposure
- **Stop-Loss Protection**: Automatic loss limitation with trailing functionality

### Profit Optimization
- **Systematic Profit Taking**: Lock in gains at predetermined levels
- **Runner Strategy**: Let a portion of profitable trades run for maximum upside
- **Dynamic Scaling**: Add to winning positions when momentum is strong

### Monitoring & Logging
- **Real-Time Portfolio Tracking**: Continuous P&L monitoring
- **Detailed Transaction History**: Complete audit trail of all trades
- **Performance Analytics**: Comprehensive trading statistics

## 🧪 Testing & Simulation

The system includes a sophisticated simulation engine that:

- Uses Geometric Brownian Motion for realistic price generation
- Simulates market slippage and transaction fees
- Provides realistic trading conditions for strategy validation
- Enables safe backtesting before live deployment

## 🛠️ Development

### Project Structure
```
auto_trader/
├── src/
│   ├── __init__.py
│   ├── orchestrator.py      # Central coordinator
│   ├── signal_queue.py      # Signal processing
│   ├── data_feeder.py       # Price data simulation
│   ├── portfolio_manager.py # Position tracking
│   ├── strategy_engine.py   # Trading logic
│   ├── execution_engine.py  # Order execution
│   └── config.py           # Configuration settings
├── main.py                  # Main entry point
├── demo.py                 # Quick demo script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Key Dependencies
- **pandas**: Time-series data handling
- **numpy**: Numerical calculations
- **asyncio**: Concurrent operations
- **sqlite3**: Database persistence

## 🔮 Future Enhancements

### Production Features
- **Jupiter Integration**: Real DEX execution via Jupiter aggregator
- **Live Data Feeds**: Integration with Birdeye, DexScreener APIs
- **Advanced Analytics**: ML-based signal generation
- **Multi-Chain Support**: Ethereum, BSC, and other chains

### Strategy Improvements
- **Dynamic Risk Adjustment**: Portfolio-based risk scaling
- **Market Regime Detection**: Adapt strategy to market conditions
- **Advanced Indicators**: Technical analysis integration
- **Portfolio Optimization**: Modern portfolio theory application

## ⚠️ Disclaimer

This system is provided for educational and research purposes. Cryptocurrency trading involves significant risk and can result in substantial losses. The authors are not responsible for any financial losses incurred through the use of this software.

**Important Notes:**
- Always test thoroughly in simulation mode before live trading
- Never risk more than you can afford to lose
- Past performance does not guarantee future results
- Consider consulting with financial professionals before trading

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

*Built with ❤️ for the crypto trading community*