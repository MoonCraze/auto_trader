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
from data_feeder import get_historical_data, stream_data
from entry_strategy import check_for_entry_signal
from token_metadata import TokenMetadata
# from sentiment_analyzer import check_sentiment

SSE_ENDPOINT = "https://humble-system-q756ppwr9j7v3x7gg-5000.app.github.dev/stream"

APP_STATE = { "trade_summaries": [], "active_token_info": None, "initial_candles": [], "initial_volumes": [], "bot_trades": [], "strategy_state": None, "portfolio": None, "market_index_history": [] }
CONNECTIONS = set()

async def register(websocket):
    CONNECTIONS.add(websocket)
    print(f"New UI client connected. Total clients: {len(CONNECTIONS)}")
    try:
        await websocket.send(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        if APP_STATE["active_token_info"]:
            start_package = { 'type': 'NEW_TRADE_STARTING', 'data': { 'token_info': APP_STATE["active_token_info"], 'candles': APP_STATE["initial_candles"], 'volumes': APP_STATE["initial_volumes"], 'bot_trades': APP_STATE["bot_trades"], 'strategy_state': APP_STATE["strategy_state"], } }
            await websocket.send(json.dumps(start_package))
            if APP_STATE["portfolio"]:
                 await websocket.send(json.dumps({'type': 'UPDATE', 'data': {'portfolio': APP_STATE["portfolio"]}}))
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
    data_df = await get_historical_data(token_info['pool_address'])
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
    strategy_state = {'entry_price': strategy.entry_price, 'stop_loss_price': strategy.stop_loss_price, 'take_profit_tiers': config.TAKE_PROFIT_TIERS, 'highest_price_seen': strategy.highest_price_seen}
    portfolio_status = {'sol_balance': pm.sol_balance, 'positions': {k: v for k, v in pm.positions.items()}, 'total_value': pm.get_total_value({token_info['address']: entry_price}), 'trade_pnl': pm.get_total_value({token_info['address']: entry_price}) - initial_sol_balance, 'overall_pnl': pm.get_total_value({token_info['address']: entry_price}) - config.INITIAL_CAPITAL_SOL}
    APP_STATE.update({ "active_token_info": token_info, "initial_candles": initial_candles, "initial_volumes": initial_volumes, "bot_trades": [bot_trade], "strategy_state": strategy_state, "portfolio": portfolio_status })
    APP_STATE["trade_summaries"][index]['status'] = 'Active'
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
    new_trade_package = { 'type': 'NEW_TRADE_STARTING', 'data': { 'token_info': token_info, 'candles': initial_candles, 'volumes': initial_volumes, 'bot_trades': [bot_trade], 'strategy_state': strategy_state, 'portfolio': portfolio_status } }
    await broadcast(json.dumps(new_trade_package))
    await asyncio.sleep(2)

    async for candle in stream_data(token_info['pool_address']):
        current_price = candle['close']
        bot_trade_event = None
        if token_info['address'] in pm.positions:
            action, sell_portion, reason = strategy.check_for_trade_action(current_price)
            if action == 'SELL':
                remaining_tokens = pm.positions[token_info['address']]['tokens']
                tokens_to_sell = remaining_tokens if sell_portion == 1.0 else strategy.initial_token_quantity * sell_portion
                tokens_to_sell = min(tokens_to_sell, remaining_tokens)
                sol_received = executor.execute_sell(token_info, tokens_to_sell, current_price)
                if sol_received > 0:
                    bot_trade_event = {
                        'time': int(candle['timestamp'].timestamp()),
                        'side': 'SELL',
                        'price': current_price,
                        'sol_amount': sol_received,
                        'token_amount': tokens_to_sell
                    }
                    APP_STATE["bot_trades"].append(bot_trade_event)
        
        APP_STATE["strategy_state"] = {
            'entry_price': strategy.entry_price,
            'stop_loss_price': strategy.stop_loss_price,
            'take_profit_tiers': config.TAKE_PROFIT_TIERS,
            'highest_price_seen': strategy.highest_price_seen
        }
        
        APP_STATE["portfolio"] = {
            'sol_balance': pm.sol_balance,
            'positions': {k: v for k, v in pm.positions.items()},
            'total_value': pm.get_total_value({token_info['address']: current_price}),
            'trade_pnl': pm.get_total_value({token_info['address']: current_price}) - initial_sol_balance,
            'overall_pnl': pm.get_total_value({token_info['address']: current_price}) - config.INITIAL_CAPITAL_SOL
        }
        
        formatted_candle = {
            'time': int(candle['timestamp'].timestamp()),
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close']
        }
        
        volume_color = '#26a69a80' if candle['close'] >= candle['open'] else '#ef535080'
        formatted_volume = {
            'time': int(candle['timestamp'].timestamp()),
            'value': candle['volume'],
            'color': volume_color
        }
        
        update_message = {
            'type': 'UPDATE',
            'data': {
                'candle': formatted_candle,
                'volume': formatted_volume,
                'portfolio': APP_STATE["portfolio"],
                'strategy_state': APP_STATE["strategy_state"],
                'bot_trade': bot_trade_event,
            }
        }
        
        await broadcast(json.dumps(update_message))
        if token_info['address'] not in pm.positions: break

    print(f"[{token_info['symbol']}] Trade finished.")
    APP_STATE["trade_summaries"][index]['status'] = 'Finished'
    APP_STATE["trade_summaries"][index]['pnl'] = pm.sol_balance - initial_sol_balance
    await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))

async def listen_for_tokens(raw_queue: asyncio.Queue, metadata: TokenMetadata):
    print("Starting lean SSE listener...")
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
                                    # Include pool_address for the token
                                    token_info = {
                                        "address": token_address,
                                        "symbol": symbol,
                                        "pool_address": "DCTvr8KcsR3Da4fQXbPdhEH87rW7y2T34U8YAFww2sCp"  # Use as default for testing
                                    }
                                    print(f"Raw signal received for {symbol}. Pushing to screening queue.")
                                    await raw_queue.put(token_info)
                            except json.JSONDecodeError: pass
        except Exception as e:
            print(f"Error in SSE listener: {e}. Reconnecting in 10s.")
            await asyncio.sleep(10)

async def process_sentiment_queue(raw_queue: asyncio.Queue, trade_queue: asyncio.Queue):
    global APP_STATE
    print("Starting sentiment screening processor...")
    while True:
        token_info = await raw_queue.get()
        new_summary = {'token': token_info, 'status': 'Screening', 'pnl': 0.0, 'sentiment_score': None, 'mention_count': None}
        APP_STATE["trade_summaries"].append(new_summary)
        summary_index = len(APP_STATE["trade_summaries"]) - 1
        await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        # sentiment_result = await check_sentiment(token_info['address'], token_info['symbol'])
        # if sentiment_result and sentiment_result['score'] > 60:
        #     print(f"Token {token_info['symbol']} passed sentiment. Pushing to trade queue.")
        #     await trade_queue.put((token_info, sentiment_result))
        # else:
        #     print(f"Token {token_info['symbol']} failed sentiment screening.")
        #     APP_STATE["trade_summaries"][summary_index]['status'] = 'Failed'
        #     if sentiment_result:
        #         APP_STATE["trade_summaries"][summary_index]['sentiment_score'] = sentiment_result['score']
        #         APP_STATE["trade_summaries"][summary_index]['mention_count'] = sentiment_result['mentions']
        #     await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
        # print("Waiting 30 seconds before next sentiment check to respect rate limit...")
        # await asyncio.sleep(30)
        dummy_sentiment = {'score': 100, 'mentions': 0}  # Dummy high score to ensure it passes
        print(f"Token {token_info['symbol']} proceeding to trade queue (sentiment check disabled).")
        await trade_queue.put((token_info, dummy_sentiment))
        
        # Small delay between tokens to prevent overwhelming the system
        await asyncio.sleep(2)

async def process_trade_queue(trade_queue: asyncio.Queue):
    global APP_STATE
    pm = PortfolioManager(config.INITIAL_CAPITAL_SOL)
    while True:
        token_info_tuple = await trade_queue.get()
        token_info, sentiment_result = token_info_tuple
        summary_to_update = next((s for s in APP_STATE["trade_summaries"] if s['token']['address'] == token_info['address']), None)
        if summary_to_update:
            summary_to_update['status'] = 'Pending'
            summary_to_update['sentiment_score'] = sentiment_result['score']
            summary_to_update['mention_count'] = sentiment_result['mentions']
            index = APP_STATE["trade_summaries"].index(summary_to_update)
            await broadcast(json.dumps({'type': 'TRADE_SUMMARY_UPDATE', 'data': {'summaries': APP_STATE["trade_summaries"]}}))
            await process_single_token(token_info, pm, index)
            await asyncio.sleep(5)
            APP_STATE["active_token_info"] = None
        else:
            # <<< THE DEFINITIVE FIX IS HERE
            # Correctly access the symbol from the token_info dictionary inside the tuple.
            print(f"Error: Could not find summary for validated token {token_info['symbol']}")

async def stream_background_data():
    global APP_STATE
    print("Starting background market data stream...")
    # Use SOL/USDC pool as market index
    pool_address = "DCTvr8KcsR3Da4fQXbPdhEH87rW7y2T34U8YAFww2sCp"
    
    try:
        # Get initial data
        data_df = await get_historical_data(pool_address)
        APP_STATE["market_index_history"] = []
        
        # Initialize with historical data
        for _, row in data_df.iterrows():
            candle = {
                'time': int(row['timestamp'].timestamp()),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            }
            APP_STATE["market_index_history"].append(candle)
            
        # Stream live updates
        async for candle in stream_data(pool_address):
            if APP_STATE["active_token_info"] is None:
                new_candle = {
                    'time': int(candle['timestamp'].timestamp()),
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close']
                }
                APP_STATE["market_index_history"].append(new_candle)
                if len(APP_STATE["market_index_history"]) > 1000:
                    APP_STATE["market_index_history"].pop(0)
                await broadcast(json.dumps({'type': 'UPDATE', 'data': {'candle': new_candle}}))
    except Exception as e:
        print(f"Error in background stream: {e}")
        # Fallback to simple placeholder data if API fails
        APP_STATE["market_index_history"] = [{
            'time': int(datetime.now(timezone.utc).timestamp()),
            'open': 100.0,
            'high': 100.0,
            'low': 100.0,
            'close': 100.0
        }]
    
    await asyncio.sleep(300)  # Wait 5 minutes between updates

async def main():
    token_metadata = TokenMetadata()
    await token_metadata.initialize()
    raw_signal_queue = asyncio.Queue()
    trade_queue = asyncio.Queue()
    server = websockets.serve(register, "localhost", 8765)
    print("--- Autonomous Trading System Started ---")
    await asyncio.gather(
        server,
        listen_for_tokens(raw_signal_queue, token_metadata),
        process_sentiment_queue(raw_signal_queue, trade_queue),
        process_trade_queue(trade_queue),
        stream_background_data()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")