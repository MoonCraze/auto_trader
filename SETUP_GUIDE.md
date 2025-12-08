# Auto Trader Bot - Multi-User Setup Guide

## 🎉 Implementation Complete!

The bot now supports:
- ✅ Synthetic wallet authentication (10-20 SOL initial balance)
- ✅ Multi-user support with per-user trading state
- ✅ Historical trade tracking with database persistence
- ✅ Profile/Wallet page with comprehensive analytics
- ✅ Per-token trading statistics
- ✅ Overall trading performance metrics

## 🚀 Quick Start

### 1. Install Python Dependencies

```powershell
cd D:\Academic\sem_8\FYP\auto-trader
pip install -r requirements.txt
```

### 2. Initialize Database

```powershell
python database.py
```

This creates the SQLite database with all necessary tables.

### 3. Install Frontend Dependencies

```powershell
cd bot-ui-ts
npm install
```

### 4. Start Backend Services

Open **3 separate terminals**:

**Terminal 1 - WebSocket Server (Multi-user trading bot):**
```powershell
python websocket_server.py
```

**Terminal 2 - REST API Server (Historical data & analytics):**
```powershell
python api_server.py
```

**Terminal 3 - SSE Token Feed (if using external token signals):**
```powershell
python sse.py
```

### 5. Start Frontend

```powershell
cd bot-ui-ts
npm run dev
```

Open http://localhost:5173 in your browser.

## 🔑 Authentication Flow

### Register New Wallet
1. Click "Create Wallet" on login screen
2. System generates synthetic wallet address
3. Random SOL balance assigned (10.00 - 20.00 SOL)
4. Automatically logged in

### Login with Existing Wallet
1. Click "Login with Existing Wallet"
2. Enter wallet address from previous session
3. System authenticates and loads user data

## 📊 Profile/Wallet Page Features

### Overview Tab
- Total P&L (Profit & Loss)
- Win Rate with W/L breakdown
- Total Trades (active + finished)
- Trading Volume & Average Trade Size
- Average P&L per Trade
- Largest Win/Loss
- Unique Tokens Traded

### Per-Token Stats Tab
Table showing for each token:
- Total trades
- Win rate
- Total invested
- Total returned
- Net P&L
- Average P&L percentage
- Best/worst trade

### Trade History Tab
Complete trade history with:
- Token symbol
- Status (active/finished/failed)
- Entry/exit prices
- SOL invested
- P&L in SOL and percentage
- Entry timestamp
- Exit reason (stop-loss, take-profit, etc.)

## 🗄️ Database Schema

### Users Table
- `wallet_address` (PK): Unique synthetic wallet ID
- `created_at`: Registration timestamp
- `initial_sol_balance`: Starting SOL amount

### Trades Table
- Full trade lifecycle tracking
- Entry/exit prices and timestamps
- P&L calculations
- Strategy parameters
- Sentiment scores
- Exit reasons

### Positions Table
- Current open positions per user
- Token holdings and cost basis
- Last updated timestamp

### Portfolio Snapshots Table
- Historical portfolio values
- Total value tracking over time
- P&L progression

## 🔧 Configuration

Edit `config.py` to adjust:

```python
# Database
DATABASE_URL = "sqlite:///./trading_bot.db"

# Synthetic Wallet Settings
MIN_SYNTHETIC_SOL = 10.0
MAX_SYNTHETIC_SOL = 20.0

# Trading Parameters
INITIAL_CAPITAL_SOL = 50.0  # Not used for multi-user (uses user's balance)
RISK_PER_TRADE_PERCENT = 0.02
TAKE_PROFIT_TIERS = [(0.30, 0.33), (0.75, 0.33)]
INITIAL_STOP_LOSS_PERCENT = 0.15
TRAILING_STOP_LOSS_PERCENT = 0.20
```

## 🌐 API Endpoints

### Authentication
- `POST /api/register` - Create new synthetic wallet
- `GET /api/user/{wallet_address}` - Get user info

### Trading History
- `GET /api/trades/{wallet_address}` - Get trade history (with filters)
- `GET /api/trades/{wallet_address}/{trade_id}` - Get specific trade
- `GET /api/positions/{wallet_address}` - Get current positions

### Analytics
- `GET /api/analytics/{wallet_address}/overall` - Overall trading stats
- `GET /api/analytics/{wallet_address}/by-token` - Per-token breakdown
- `GET /api/portfolio/history/{wallet_address}` - Portfolio value over time

## 🔌 WebSocket Protocol

### Client → Server

**Authentication:**
```json
{
  "type": "AUTH",
  "wallet_address": "your_wallet_address_here"
}
```

### Server → Client

**Auth Success:**
```json
{
  "type": "AUTH_SUCCESS",
  "data": {
    "wallet_address": "...",
    "initial_sol_balance": 15.2341,
    "created_at": "2025-12-07T..."
  }
}
```

**Auth Error:**
```json
{
  "type": "ERROR",
  "message": "Invalid wallet address"
}
```

All other message types remain the same (NEW_TRADE_STARTING, UPDATE, TRADE_SUMMARY_UPDATE).

## 📝 Notes

1. **Multi-User Trading**: All connected users see the same token signals but trade independently with their own portfolios
2. **Database Persistence**: All trades are saved to database for historical analysis
3. **Session Storage**: Wallet address saved in localStorage for auto-login
4. **Real-time Updates**: WebSocket maintains per-user state for live trading updates
5. **Analytics Refresh**: Profile page fetches latest data on load (can add auto-refresh if needed)

## 🐛 Troubleshooting

### "Module not found" errors
```powershell
pip install -r requirements.txt --upgrade
```

### Database errors
```powershell
# Reset database
rm trading_bot.db
python database.py
```

### WebSocket connection issues
- Ensure websocket_server.py is running on port 8765
- Check browser console for connection errors
- Verify wallet authentication is sent on connection

### Frontend build errors
```powershell
cd bot-ui-ts
rm -rf node_modules
npm install
```

## 🎯 Next Steps

1. Add portfolio value charts over time
2. Implement trade export (CSV/JSON)
3. Add filters by date range on profile page
4. Add real-time P&L updates for active trades on profile
5. Implement trade search functionality
6. Add performance comparison charts
7. Add email notifications for trade completions
8. Implement stop-loss/take-profit customization per user

---

**Happy Trading! 🚀📈**
