import React, { useState, useEffect } from 'react';
import CandlestickChart from './components/CandlestickChart';
import TransactionFeed from './components/TransactionFeed';
import Card from './components/Card';
import { Candle, Portfolio, BotTrade, MarketTrade, StrategyState } from './types';

const StrategyPanel: React.FC<{ state: StrategyState | null }> = ({ state }) => {
    if (!state) return <p className="text-gray-500">Awaiting entry signal...</p>;

    // <<< FIX: Add h-full and overflow-y-auto to make this panel scrollable
    return (
        <div className="h-full space-y-3 text-sm overflow-y-auto pr-2">
            <div>
                <span className="text-gray-400">Entry Price: </span>
                <span className="font-mono text-white">{state.entry_price.toFixed(6)}</span>
            </div>
            <div>
                <span className="text-gray-400">Stop-Loss: </span>
                <span className="font-mono text-yellow-400">{state.stop_loss_price.toFixed(6)}</span>
            </div>
            <div>
                <p className="text-gray-400 mb-1">Take-Profit Targets:</p>
                <ul className="space-y-1">
                    {/* Added a key for better React performance */}
                    {state.take_profit_tiers.map(([target, portion], i) => (
                        <li key={`tp-${i}`} className="text-gray-300">
                            - Sell {portion * 100}% at <span className="font-mono text-green-400">{(state.entry_price * (1 + target)).toFixed(6)}</span>
                        </li>
                    ))}
                    {/* You can add more content here to test the scrollbar */}
                    {/* <li className='text-gray-600'>Extra Item 1</li> */}
                    {/* <li className='text-gray-600'>Extra Item 2</li> */}
                    {/* <li className='text-gray-600'>Extra Item 3</li> */}
                </ul>
            </div>
        </div>
    );
};

// The main App component in src/App.tsx
function App() {
    // All state and WebSocket logic remains the same...
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [isFinished, setIsFinished] = useState<boolean>(false);
    const [initialCandles, setInitialCandles] = useState<Candle[] | null>(null);
    const [lastCandle, setLastCandle] = useState<Candle | null>(null);
    const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
    const [strategyState, setStrategyState] = useState<StrategyState | null>(null);
    const [botTrades, setBotTrades] = useState<BotTrade[]>([]);
    const [marketTrades, setMarketTrades] = useState<MarketTrade[]>([]);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8765');
        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            switch (message.type) {
                case 'INITIAL_STATE':
                    setInitialCandles(message.data.candles);
                    setBotTrades(message.data.bot_trades);
                    break;
                case 'UPDATE':
                    if (message.data.candle) setLastCandle(message.data.candle);
                    if (message.data.portfolio) setPortfolio(message.data.portfolio);
                    if (message.data.strategy_state) setStrategyState(message.data.strategy_state);
                    if (message.data.bot_trade) {
                        setBotTrades(prev => [...prev, message.data.bot_trade]);
                        setMarketTrades(prev => [{ ...message.data.bot_trade, isBot: true }, ...prev]);
                    }
                    if (message.data.market_trade) {
                        setMarketTrades(prev => [message.data.market_trade, ...prev]);
                    }
                    break;
                case 'FINAL_STATE':
                    setIsFinished(true);
                    break;
            }
        };
        return () => ws.close();
    }, []);

    const pnl = portfolio?.pnl ?? 0;
    const pnlColor = pnl >= 0 ? 'text-green-400' : 'text-red-400';
    const currentPrice = lastCandle?.close ?? portfolio?.positions?.MOGCOIN?.cost_basis ?? 0;

    return (
        <div className="bg-gray-900 text-white h-screen font-sans flex flex-col p-4">
            <header className="flex-shrink-0 flex justify-between items-center border-b border-gray-700 pb-3 mb-4">
                 <div>
                    <h1 className="text-2xl font-bold">MOGCOIN/SOL</h1>
                    <p className="text-sm text-gray-400">Autonomous Trading Bot - Mission Control</p>
                </div>
                <div className="text-center">
                    <p className="text-3xl font-mono">{currentPrice > 0 ? currentPrice.toFixed(6) : '...'}</p>
                    <p className={`text-lg font-semibold ${pnlColor}`}>{pnl.toFixed(4)} SOL</p>
                </div>
                <div className="flex items-center space-x-4">
                    <span className={`text-sm ${isFinished ? 'text-yellow-400' : 'text-gray-400'}`}>{isFinished ? 'Simulation Finished' : 'Simulation Running'}</span>
                    <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                        <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                    </div>
                </div>
            </header>

            <main className="flex-grow flex flex-row gap-4 overflow-hidden">
                <div className="flex flex-col gap-4 w-full max-w-xs">
                    <Card title="Portfolio">
                        <div className="space-y-2 text-sm">
                            <p>Total Value: <span className="font-mono text-white float-right">{portfolio?.total_value.toFixed(4) ?? '...'} SOL</span></p>
                            <p>SOL Balance: <span className="font-mono text-white float-right">{portfolio?.sol_balance.toFixed(4) ?? '...'} SOL</span></p>
                        </div>
                    </Card>
                    <Card title="Current Position">
                        {portfolio?.positions && Object.keys(portfolio.positions).length > 0 ? (
                             <div className="space-y-2 text-sm">
                                <p>Tokens Held: <span className="font-mono text-white float-right">{portfolio.positions.MOGCOIN.tokens.toFixed(2)}</span></p>
                                <p>Avg Cost: <span className="font-mono text-white float-right">{portfolio.positions.MOGCOIN.cost_basis.toFixed(6)}</span></p>
                            </div>
                        ) : <p className="text-gray-500">No active position.</p>}
                    </Card>
                    <Card title="Bot Trade Log" className="flex-grow">
                        <ul className="space-y-2 overflow-y-auto pr-2 h-full">
                             {botTrades.map((trade, index) => (
                                 <li key={index} className="text-sm p-1.5 rounded bg-blue-900/50">
                                    <span className={trade.side === 'BUY' ? 'text-blue-400' : 'text-red-400'}>{trade.side} </span>
                                    <span className="text-gray-300">{trade.sol_amount.toFixed(4)} SOL </span>
                                    <span className="text-gray-400">@ {trade.price.toFixed(6)}</span>
                                 </li>
                             ))}
                        </ul>
                    </Card>
                </div>
                
                <div className="flex-grow flex flex-col gap-4">
                    {/* <<< FIX: Reduced chart height to 3/5 (60%) of the space */}
                    <div className="h-3/5 bg-gray-800/50 rounded-lg p-2">
                         <CandlestickChart initialData={initialCandles} update={lastCandle} botTrades={botTrades} />
                    </div>
                     {/* <<< FIX: Increased panel height to 2/5 (40%) of the space */}
                    <div className="h-2/5 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Card title="Strategy Brain">
                           <StrategyPanel state={strategyState}/>
                        </Card>
                        <Card title="Live Transactions">
                           <TransactionFeed trades={marketTrades} />
                        </Card>
                    </div>
                </div>
            </main>
        </div>
    );
}


export default App;