import asyncio
import websockets
import json
import random
import config
import aiohttp
from datetime import datetime, timezone

from portfolio_manager import PortfolioManager
from execution_engine import ExecutionEngine
from strategy_engine import StrategyEngine
from data_feeder import generate_synthetic_data
from entry_strategy import check_for_entry_signal
from token_metadata import TokenMetadata

SSE_ENDPOINT = "https://helius.wonderswhisper.com/stream/coordinated"

APP_STATE = { "trade_summaries": [], "active_token_info": None, "initial_candles": [], "initial_volumes": [], "bot_trades": [], "strategy_state": None, "portfolio": None, "market_index_history": [] }
CONNECTIONS = set()

async def register(websocket):
    CONNECTIONS.add(websocket)
    print(f"New UI client connected. Total clients: {len(CONNECTIONS)}")
    try:
        await websocket.send(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        if APP_STATE["active_token_info"]:
            start_package = { 'type': 'NEW_TRADE_STARTING', 'data': { 'token_info': APP_STATE["active_token_info"], 'candles': APP_STATE["initial_candles"], 'volumes': APP_STATE["initial_volumes"], 'bot_trades': APP_STATE["bot_trades"], 'strategy_state': APP_STATE["strategy_state"], 'portfolio': APP_STATE["portfolio"] } }
            await websocket.send(json.dumps(start_package))
        else:
            market_index_package = { 'type': 'NEW_TRADE_STARTING', 'data': { 'token_info': {'symbol': 'SOL/USDC', 'address': 'MARKET_INDEX'}, 'candles': APP_STATE["market_index_history"], 'volumes': [], 'bot_trades': [], 'strategy_state': None, } }
            await websocket.send(json.dumps(market_index_package))
        await websocket.wait_closed()
    finally:
        print(f"Connection handler for a client finished.")
        CONNECTIONS.discard(websocket)

async def broadcast(message):
    if CONNECTIONS:
        for conn in list(CONNECTIONS):
            try: await conn.send(message)
            except websockets.exceptions.ConnectionClosed: CONNECTIONS.discard(conn)

def format_candle_and_volume(row):
    timestamp = int(row['timestamp'].timestamp())
    candle = {'time': timestamp, 'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close']}
    volume_color = '#26a69a80' if row['close'] >= row['open'] else '#ef535080'
    volume = {'time': timestamp, 'value': row['volume'], 'color': volume_color}
    return candle, volume

async def process_single_token(token_info, pm, index):
    global APP_STATE
    executor = ExecutionEngine(pm)
    initial_sol_balance = pm.sol_balance
    
    print(f"[{token_info['symbol']}] Preparing data and finding entry signal...")

    data_df = generate_synthetic_data(config.SIM_INITIAL_PRICE, config.SIM_DRIFT, config.SIM_VOLATILITY, config.SIM_TIME_STEPS)
    
    # --- Phase 1: Silent, Internal Monitoring ---
    price_history, entry_price, entry_index = [], 0.0, -1
    for i, row in data_df.iterrows():
        price_history.append(row['close'])
        if check_for_entry_signal(price_history, 'sma'):
            entry_price, entry_index = row['close'], i
            break
    
    if not entry_price:
        print(f"[{token_info['symbol']}] No entry signal found in dataset. Skipping.")
        APP_STATE["trade_summaries"][index].update({'status': 'Finished', 'pnl': 0.0})
        await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        return

    # --- Prepare the Atomic "Go Live" Package ---
    print(f"[{token_info['symbol']}] Entry signal found at index {entry_index}. Going live.")
    
    historical_df = data_df.iloc[:entry_index + 1]
    initial_candles, initial_volumes = [], []
    for _, row in historical_df.iterrows():
        candle, volume = format_candle_and_volume(row)
        initial_candles.append(candle)
        initial_volumes.append(volume)

    sol_to_invest = pm.sol_balance * config.RISK_PER_TRADE_PERCENT
    tokens_bought = executor.execute_buy(token_info, sol_to_invest, entry_price)
    strategy = StrategyEngine(token_info, entry_price, tokens_bought)

    bot_trade = {'time': int(data_df.iloc[entry_index]['timestamp'].timestamp()), 'side': 'BUY', 'price': entry_price, 'sol_amount': sol_to_invest, 'token_amount': tokens_bought}
    strategy_state = {'entry_price': strategy.entry_price, 'stop_loss_price': strategy.stop_loss_price, 'take_profit_tiers': config.TAKE_PROFIT_TIERS}
    portfolio_status = {'sol_balance': pm.sol_balance, 'positions': {k: v for k, v in pm.positions.items()}, 'total_value': pm.get_total_value({token_info['address']: entry_price}), 'trade_pnl': pm.get_total_value({token_info['address']: entry_price}) - initial_sol_balance, 'overall_pnl': pm.get_total_value({token_info['address']: entry_price}) - config.INITIAL_CAPITAL_SOL}

    # Atomically update the global state
    APP_STATE.update({ "active_token_info": token_info, "initial_candles": initial_candles, "initial_volumes": initial_volumes, "bot_trades": [bot_trade], "strategy_state": strategy_state, "portfolio": portfolio_status })
    APP_STATE["trade_summaries"][index]['status'] = 'Active'

    # Broadcast the complete "start" package to all clients
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
    new_trade_package = { 'type': 'NEW_TRADE_STARTING', 'data': { 'token_info': token_info, 'candles': initial_candles, 'volumes': initial_volumes, 'bot_trades': [bot_trade], 'strategy_state': strategy_state, 'portfolio': portfolio_status } }
    await broadcast(json.dumps(new_trade_package))
    await asyncio.sleep(2)

    # --- Phase 2: True Live Trading Stream ---
    for i, row in data_df.iloc[entry_index + 1:].iterrows():
        await asyncio.sleep(0.05) # Slower speed for better visualization
        current_price = row['close']
        bot_trade_event = None
        if token_info['address'] in pm.positions:
            action, sell_portion, reason = strategy.check_for_trade_action(current_price)
            if action == 'SELL':
                remaining_tokens = pm.positions[token_info['address']]['tokens']
                tokens_to_sell = remaining_tokens if sell_portion == 1.0 else strategy.initial_token_quantity * sell_portion
                tokens_to_sell = min(tokens_to_sell, remaining_tokens)
                sol_received = executor.execute_sell(token_info, tokens_to_sell, current_price)
                if sol_received > 0:
                    bot_trade_event = {'time': int(row['timestamp'].timestamp()), 'side': 'SELL', 'price': current_price, 'sol_amount': sol_received, 'token_amount': tokens_to_sell}
                    APP_STATE["bot_trades"].append(bot_trade_event)
        
        APP_STATE["strategy_state"]['stop_loss_price'] = strategy.stop_loss_price
        APP_STATE["portfolio"] = {'sol_balance': pm.sol_balance, 'positions': {k: v for k, v in pm.positions.items()}, 'total_value': pm.get_total_value({token_info['address']: current_price}), 'trade_pnl': pm.get_total_value({token_info['address']: current_price}) - initial_sol_balance, 'overall_pnl': pm.get_total_value({token_info['address']: current_price}) - config.INITIAL_CAPITAL_SOL}
        market_trade = {'side': 'BUY' if random.random() > 0.5 else 'SELL', 'sol_amount': round(random.uniform(0.05, 1.5), 4), 'price': round(current_price, 6), 'timestamp': datetime.now(timezone.utc).isoformat()} if random.random() > 0.6 else None
        candle, volume = format_candle_and_volume(row)
        update_message = {'type': 'UPDATE', 'data': {'candle': candle, 'volume': volume, 'portfolio': APP_STATE["portfolio"], 'strategy_state': APP_STATE["strategy_state"], 'bot_trade': bot_trade_event, 'market_trade': market_trade}}
        await broadcast(json.dumps(update_message))
        if token_info['address'] not in pm.positions: break

    print(f"[{token_info['symbol']}] Trade finished.")
    APP_STATE["trade_summaries"][index]['status'] = 'Finished'
    APP_STATE["trade_summaries"][index]['pnl'] = pm.sol_balance - initial_sol_balance
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))

async def listen_for_tokens(queue: asyncio.Queue, metadata: TokenMetadata):
    print("Starting SSE listener for new token signals...")
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(SSE_ENDPOINT) as response:
                    if response.status != 200:
                        print(f"SSE connection failed: {response.status}. Retrying in 10s.")
                        await asyncio.sleep(10)
                        continue
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data:'):
                            try:
                                data = json.loads(line[len('data:'):].strip())
                                token_address = data.get("tokenAddress")
                                if token_address:
                                    symbol = metadata.get_symbol(token_address)
                                    token_info = {"address": token_address, "symbol": symbol}
                                    print(f"Signal received for {symbol} ({token_address}). Adding to queue.")
                                    await queue.put(token_info)
                            except json.JSONDecodeError: pass
        except Exception as e:
            print(f"Error in SSE listener: {e}. Reconnecting in 10s.")
            await asyncio.sleep(10)

async def process_trade_queue(queue: asyncio.Queue):
    global APP_STATE
    pm = PortfolioManager(config.INITIAL_CAPITAL_SOL)
    while True:
        token_info = await queue.get()
        new_summary = {'token': token_info, 'status': 'Pending', 'pnl': 0.0}
        APP_STATE["trade_summaries"].append(new_summary)
        index = len(APP_STATE["trade_summaries"]) - 1
        await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        await process_single_token(token_info, pm, index)
        await asyncio.sleep(5)
        APP_STATE["active_token_info"] = None

async def stream_background_data():
    """Continuously streams market data when no trade is active."""
    global APP_STATE
    print("Starting background market data stream...")
    # Generate a base history for new clients
    df = generate_synthetic_data(150, 0.0001, 0.005, 200) # Simulating SOL/USDC price
    for _, row in df.iterrows():
        candle, _ = format_candle_and_volume(row)
        APP_STATE["market_index_history"].append(candle)

    # Stream live updates
    while True:
        if APP_STATE["active_token_info"] is None:
            # Generate one new tick
            last_price = APP_STATE["market_index_history"][-1]['close']
            new_price = last_price * (1 + random.normalvariate(0.0001, 0.005))
            new_candle = {'time': int(datetime.now(timezone.utc).timestamp()), 'open': last_price, 'high': max(last_price, new_price), 'low': min(last_price, new_price), 'close': new_price}
            
            APP_STATE["market_index_history"].append(new_candle)
            if len(APP_STATE["market_index_history"]) > 1000: # Keep history from growing forever
                APP_STATE["market_index_history"].pop(0)

            await broadcast(json.dumps({'type': 'UPDATE', 'data': {'candle': new_candle}}))
        
        await asyncio.sleep(2) # Send a background tick every 2 seconds

async def main():
    token_metadata = TokenMetadata()
    await token_metadata.initialize()
    trade_queue = asyncio.Queue()
    server = websockets.serve(register, "localhost", 8765)
    print("--- Autonomous Trading System Started ---")
    await asyncio.gather(
        server,
        listen_for_tokens(trade_queue, token_metadata),
        process_trade_queue(trade_queue),
        stream_background_data() # Run the new heartbeat task
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")