import asyncio
import websockets
import json
import random
import config
import pandas as pd
from datetime import datetime, timezone

# Import all our existing bot modules
from portfolio_manager import PortfolioManager
from execution_engine import ExecutionEngine
from strategy_engine import StrategyEngine
from data_feeder import generate_synthetic_data
from entry_strategy import check_for_entry_signal

# --- WebSocket Server Setup (No changes here) ---
CONNECTIONS = set()
# ... (register and broadcast functions are correct from the previous version) ...
async def register(websocket):
    """Registers a new UI connection."""
    CONNECTIONS.add(websocket)
    print(f"New UI client connected. Total clients: {len(CONNECTIONS)}")
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)
        print(f"UI client disconnected. Total clients: {len(CONNECTIONS)}")

async def broadcast(message):
    """Sends a message to all connected UI clients, handling disconnections gracefully."""
    if CONNECTIONS:
        disconnected_clients = set()
        for conn in CONNECTIONS:
            try:
                await conn.send(message)
            except websockets.exceptions.ConnectionClosed:
                print("A client disconnected, will remove.")
                disconnected_clients.add(conn)
        for conn in disconnected_clients:
            CONNECTIONS.remove(conn)

def format_candle_and_volume(row):
    """Converts a DataFrame row to chart-compatible candle and volume objects."""
    timestamp = int(row['timestamp'].timestamp())
    
    candle = {
        'time': timestamp,
        'open': row['open'],
        'high': row['high'],
        'low': row['low'],
        'close': row['close']
    }
    
    volume_color = '#26a69a80' if row['close'] >= row['open'] else '#ef535080'

    volume = {
        'time': timestamp,
        'value': row['volume'],
        'color': volume_color
    }
    return candle, volume

async def run_bot_simulation():
    """Runs the entire bot simulation and broadcasts events to the UI."""
    pm = PortfolioManager(config.INITIAL_CAPITAL_SOL)
    executor = ExecutionEngine(pm)
    token_symbol = "MOGCOIN"
    
    data_df = generate_synthetic_data(
        config.SIM_INITIAL_PRICE, config.SIM_DRIFT, config.SIM_VOLATILITY, config.SIM_TIME_STEPS
    )

    # --- Phase 1: Monitoring ---
    print(f"[{token_symbol}] Entering Phase 1: Monitoring for entry signal...")
    price_history = []
    entry_price = 0.0
    
    # <<< FIX 1: Correctly prepare the INITIAL_STATE data BEFORE the loop ---
    initial_candles = []
    initial_volumes = []
    for _, row in data_df.iterrows():
        candle_data, volume_data = format_candle_and_volume(row)
        initial_candles.append(candle_data)
        initial_volumes.append(volume_data)

    await broadcast(json.dumps({
        'type': 'INITIAL_STATE', 
        'data': {
            'candles': initial_candles, 
            'volumes': initial_volumes, # Send volumes as well
            'bot_trades': []
        }
    }))
    await asyncio.sleep(2)

    entry_index = -1
    for index, row in data_df.iterrows():
        await asyncio.sleep(0.05)
        
        # <<< FIX 2: Use `row['close']` as the representative price ---
        current_price = row['close'] 
        price_history.append(current_price)
        
        market_trade_event = None
        if random.random() > 0.6:
            market_trade_event = {
                'side': 'BUY' if random.random() > 0.5 else 'SELL',
                'sol_amount': round(random.uniform(0.05, 1.5), 4),
                'price': round(current_price, 6),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        portfolio_status = { 'sol_balance': pm.sol_balance, 'positions': {}, 'total_value': pm.sol_balance, 'pnl': 0 }
        
        candle_data, volume_data = format_candle_and_volume(row)
        update_package = { 'type': 'UPDATE', 'data': {'candle': candle_data, 'volume': volume_data, 'portfolio': portfolio_status, 'market_trade': market_trade_event}}
        await broadcast(json.dumps(update_package))
        
        if check_for_entry_signal(price_history, strategy_type='sma'):
            entry_price = current_price
            entry_index = index
            break

    if not entry_price:
        print(f"[{token_symbol}] Simulation finished without finding an entry signal.")
        await broadcast(json.dumps({'type': 'FINAL_STATE'}))
        return

    # --- Phase 2: Position Management ---
    print(f"[{token_symbol}] Entering Phase 2: Executing trade and managing position.")

    sol_to_invest = pm.sol_balance * config.RISK_PER_TRADE_PERCENT
    tokens_bought = executor.execute_buy(token_symbol, sol_to_invest, entry_price)

    if not tokens_bought: return
    
    strategy = StrategyEngine(token_symbol, entry_price, tokens_bought)
    
    strategy_state = { 'entry_price': strategy.entry_price, 'stop_loss_price': strategy.stop_loss_price, 'take_profit_tiers': config.TAKE_PROFIT_TIERS }
    bot_trade_event = { 'time': int(data_df.iloc[entry_index]['timestamp'].timestamp()), 'side': 'BUY', 'price': entry_price, 'sol_amount': sol_to_invest }
    serializable_positions = {k: v for k, v in pm.positions.items()}
    portfolio_status = {
        'sol_balance': pm.sol_balance,
        'positions': serializable_positions,
        'total_value': pm.get_total_value({token_symbol: entry_price}),
        'pnl': pm.get_total_value({token_symbol: entry_price}) - config.INITIAL_CAPITAL_SOL
    }
    
    first_trade_update = { 
        'type': 'UPDATE', 
        'data': {
            'bot_trade': bot_trade_event, 
            'strategy_state': strategy_state,
            'portfolio': portfolio_status
        } 
    }
    await broadcast(json.dumps(first_trade_update))

    for index, row in data_df.iloc[entry_index + 1:].iterrows():
        await asyncio.sleep(0.05)
        current_price = row['close'] # <<< FIX 2 (Again): Use `row['close']`
        bot_trade_event = None
        if token_symbol in pm.positions:
            action, sell_portion, reason = strategy.check_for_trade_action(current_price)
            if action == 'SELL':
                remaining_tokens = pm.positions[token_symbol]['tokens']
                tokens_to_sell = remaining_tokens if sell_portion == 1.0 else strategy.initial_token_quantity * sell_portion
                tokens_to_sell = min(tokens_to_sell, remaining_tokens)
                sol_received = executor.execute_sell(token_symbol, tokens_to_sell, current_price)
                if sol_received > 0:
                    bot_trade_event = { 'time': int(row['timestamp'].timestamp()), 'side': 'SELL', 'price': current_price, 'sol_amount': sol_received }
        
        market_trade_event = None
        if random.random() > 0.6:
            market_trade_event = { 'side': 'BUY' if random.random() > 0.5 else 'SELL', 'sol_amount': round(random.uniform(0.05, 1.5), 4), 'price': round(current_price, 6), 'timestamp': datetime.now(timezone.utc).isoformat() }
        
        serializable_positions = {k: v for k, v in pm.positions.items()}
        portfolio_status = {
            'sol_balance': pm.sol_balance,
            'positions': serializable_positions,
            'total_value': pm.get_total_value({token_symbol: current_price}),
            'pnl': pm.get_total_value({token_symbol: current_price}) - config.INITIAL_CAPITAL_SOL
        }
        
        current_strategy_state = { 'entry_price': strategy.entry_price, 'stop_loss_price': strategy.stop_loss_price, 'take_profit_tiers': config.TAKE_PROFIT_TIERS }
        
        candle_data, volume_data = format_candle_and_volume(row)
        update_message = { 'type': 'UPDATE', 'data': { 'candle': candle_data, 'volume': volume_data, 'portfolio': portfolio_status, 'strategy_state': current_strategy_state, 'bot_trade': bot_trade_event, 'market_trade': market_trade_event } }
        await broadcast(json.dumps(update_message))
        
        if token_symbol not in pm.positions:
            print(f"[{token_symbol}] Position closed. Ending management.")
            break

    print(f"[{token_symbol}] Trade management complete.")
    await broadcast(json.dumps({'type': 'FINAL_STATE'}))

async def main():
    print("Starting WebSocket Server on ws://localhost:8765")
    async with websockets.serve(register, "localhost", 8765):
        await run_bot_simulation()
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")