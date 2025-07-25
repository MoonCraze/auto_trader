import asyncio
import websockets
import json
import random
import config
import pandas as pd
from datetime import datetime, timezone

from portfolio_manager import PortfolioManager
from execution_engine import ExecutionEngine
from strategy_engine import StrategyEngine
from data_feeder import generate_synthetic_data
from entry_strategy import check_for_entry_signal

# This global dictionary is the single source of truth for the application's state.
APP_STATE = { "trade_summaries": [], "active_token_symbol": None, "initial_candles": [], "initial_volumes": [], "bot_trades": [], "strategy_state": None, "portfolio": None, }
CONNECTIONS = set()

async def register(websocket):
    CONNECTIONS.add(websocket)
    print(f"New UI client connected. Total clients: {len(CONNECTIONS)}")
    try:
        await websocket.send(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        if APP_STATE["active_token_symbol"]:
            start_package = { 'type': 'NEW_TRADE_STARTING', 'data': { 'token_symbol': APP_STATE["active_token_symbol"], 'candles': APP_STATE["initial_candles"], 'volumes': APP_STATE["initial_volumes"], 'bot_trades': APP_STATE["bot_trades"], 'strategy_state': APP_STATE["strategy_state"], } }
            await websocket.send(json.dumps(start_package))
            if APP_STATE["portfolio"]:
                 await websocket.send(json.dumps({'type': 'UPDATE', 'data': {'portfolio': APP_STATE["portfolio"]}}))
        await websocket.wait_closed()
    finally:
        print(f"Connection handler for a client finished.")
        CONNECTIONS.discard(websocket)

async def broadcast(message):
    if CONNECTIONS:
        for conn in list(CONNECTIONS):
            try:
                await conn.send(message)
            except websockets.exceptions.ConnectionClosed:
                CONNECTIONS.discard(conn)

def format_candle_and_volume(row):
    timestamp = int(row['timestamp'].timestamp())
    candle = {'time': timestamp, 'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close']}
    volume_color = '#26a69a80' if row['close'] >= row['open'] else '#ef535080'
    volume = {'time': timestamp, 'value': row['volume'], 'color': volume_color}
    return candle, volume

async def process_single_token(token_symbol, pm, index):
    """Handles the entire lifecycle for one token with correct data flow."""
    global APP_STATE
    executor = ExecutionEngine(pm)
    initial_sol_balance = pm.sol_balance
    
    print(f"[{token_symbol}] Preparing data for new trade...")
    
    # 1. Generate the full historical dataset for the simulation.
    data_df = generate_synthetic_data(config.SIM_INITIAL_PRICE, config.SIM_DRIFT, config.SIM_VOLATILITY, config.SIM_TIME_STEPS)
    
    # <<< FIX 1: Split the data into historical (for monitoring) and live (for active trading)
    # The "live" part starts after the minimum period needed for the entry strategy.
    monitoring_period = 50 
    historical_df = data_df.iloc[:monitoring_period]
    live_df = data_df.iloc[monitoring_period:]

    initial_candles, initial_volumes = [], []
    for _, row in historical_df.iterrows():
        candle, volume = format_candle_and_volume(row)
        initial_candles.append(candle)
        initial_volumes.append(volume)

    # 2. Atomically update the global state with the initial historical data.
    APP_STATE.update({
        "active_token_symbol": token_symbol,
        "initial_candles": initial_candles, "initial_volumes": initial_volumes,
        "bot_trades": [], "strategy_state": None, "portfolio": None,
    })
    
    # 3. Notify the UI about the new trade. It will draw the initial historical chart.
    APP_STATE["trade_summaries"][index]['status'] = 'Monitoring'
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
    new_trade_package = { 'type': 'NEW_TRADE_STARTING', 'data': { 'token_symbol': token_symbol, 'candles': initial_candles, 'volumes': initial_volumes, } }
    await broadcast(json.dumps(new_trade_package))
    await asyncio.sleep(2)

    # <<< FIX 2: The monitoring phase is now a "live" simulation.
    # We find the entry point by processing the "live" part of the data.
    print(f"[{token_symbol}] Entering Phase 1: Monitoring live data...")
    price_history = historical_df['close'].tolist()
    entry_price, entry_index = 0.0, -1

    for i, row in live_df.iterrows():
        await asyncio.sleep(0.02)
        current_price = row['close']
        price_history.append(current_price)
        
        # Broadcast this new tick as an UPDATE
        candle, volume = format_candle_and_volume(row)
        market_trade = {'side': 'BUY' if random.random() > 0.5 else 'SELL', 'sol_amount': round(random.uniform(0.05, 1.5), 4), 'price': round(current_price, 6), 'timestamp': datetime.now(timezone.utc).isoformat()} if random.random() > 0.6 else None
        await broadcast(json.dumps({'type': 'UPDATE', 'data': {'candle': candle, 'volume': volume, 'market_trade': market_trade}}))
        
        if check_for_entry_signal(price_history, 'sma'):
            entry_price, entry_index = current_price, i
            break
    
    if not entry_price:
        print(f"[{token_symbol}] No entry signal found. Skipping.")
        APP_STATE["trade_summaries"][index]['status'] = 'Finished'; APP_STATE["trade_summaries"][index]['pnl'] = 0.0
        await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        return

    # Phase 2: Position Management
    print(f"[{token_symbol}] Entering Phase 2: Active Trade.")
    APP_STATE["trade_summaries"][index]['status'] = 'Active'
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))

    sol_to_invest = pm.sol_balance * config.RISK_PER_TRADE_PERCENT
    tokens_bought = executor.execute_buy(token_symbol, sol_to_invest, entry_price)
    strategy = StrategyEngine(token_symbol, entry_price, tokens_bought)
    
    APP_STATE["bot_trades"].append({'time': int(data_df.iloc[entry_index]['timestamp'].timestamp()), 'side': 'BUY', 'price': entry_price, 'sol_amount': sol_to_invest, 'token_amount': tokens_bought})
    APP_STATE["strategy_state"] = {'entry_price': strategy.entry_price, 'stop_loss_price': strategy.stop_loss_price, 'take_profit_tiers': config.TAKE_PROFIT_TIERS}
    APP_STATE["portfolio"] = {'sol_balance': pm.sol_balance, 'positions': {k: v for k, v in pm.positions.items()}, 'total_value': pm.get_total_value({token_symbol: entry_price}), 'pnl': pm.get_total_value({token_symbol: entry_price}) - initial_sol_balance}
    APP_STATE["trade_summaries"][index]['status'] = 'Active'

    first_update = {'type': 'UPDATE', 'data': {'bot_trade': APP_STATE["bot_trades"][-1], 'strategy_state': APP_STATE["strategy_state"], 'portfolio': APP_STATE["portfolio"]}}
    await broadcast(json.dumps(first_update))

    for i, row in data_df.iloc[entry_index + 1:].iterrows():
        await asyncio.sleep(0.02)
        current_price = row['close']
        bot_trade_event = None

        if token_symbol in pm.positions:
            action, sell_portion, reason = strategy.check_for_trade_action(current_price)
            if action == 'SELL':
                remaining_tokens = pm.positions[token_symbol]['tokens']
                tokens_to_sell = remaining_tokens if sell_portion == 1.0 else strategy.initial_token_quantity * sell_portion
                tokens_to_sell = min(tokens_to_sell, remaining_tokens)
                sol_received = executor.execute_sell(token_symbol, tokens_to_sell, current_price)
                if sol_received > 0:
                    bot_trade_event = {'time': int(row['timestamp'].timestamp()), 'side': 'SELL', 'price': current_price, 'sol_amount': sol_received, 'token_amount': tokens_to_sell}
                    APP_STATE["bot_trades"].append(bot_trade_event)
        
        APP_STATE["strategy_state"]['stop_loss_price'] = strategy.stop_loss_price
        APP_STATE["portfolio"] = {'sol_balance': pm.sol_balance, 'positions': {k: v for k, v in pm.positions.items()}, 'total_value': pm.get_total_value({token_symbol: current_price}), 'pnl': pm.get_total_value({token_symbol: current_price}) - initial_sol_balance}
        
        market_trade = {'side': 'BUY' if random.random() > 0.5 else 'SELL', 'sol_amount': round(random.uniform(0.05, 1.5), 4), 'price': round(current_price, 6), 'timestamp': datetime.now(timezone.utc).isoformat()} if random.random() > 0.6 else None
        candle, volume = format_candle_and_volume(row)
        update_message = {'type': 'UPDATE', 'data': {'candle': candle, 'volume': volume, 'portfolio': APP_STATE["portfolio"], 'strategy_state': APP_STATE["strategy_state"], 'bot_trade': bot_trade_event, 'market_trade': market_trade}}
        await broadcast(json.dumps(update_message))
        
        if token_symbol not in pm.positions: break

    print(f"[{token_symbol}] Trade finished.")
    APP_STATE["trade_summaries"][index]['status'] = 'Finished'
    APP_STATE["trade_summaries"][index]['pnl'] = pm.sol_balance - initial_sol_balance
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))

async def run_bot_queue():
    """Manages the queue of tokens to trade and updates the global APP_STATE."""
    global APP_STATE
    token_queue = ["MOGCOIN", "PEPECOIN", "WIFCOIN", "BONKCOIN"]
    
    APP_STATE["trade_summaries"] = [{'token': t, 'status': 'Pending', 'pnl': 0.0} for t in token_queue]
    pm = PortfolioManager(config.INITIAL_CAPITAL_SOL)

    print("--- Autonomous Trading System Started ---")
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))

    for i, token_symbol in enumerate(token_queue):
        await process_single_token(token_symbol, pm, i)
        await asyncio.sleep(5)

    print("--- All trades in queue are complete. ---")
    APP_STATE["active_token_symbol"] = None # Clear active token at the end

async def main():
    """Starts the WebSocket server and the bot queue concurrently."""
    server = websockets.serve(register, "localhost", 8765)
    
    await asyncio.gather(
        server,
        run_bot_queue()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")