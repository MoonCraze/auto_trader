import React, { useState, useEffect } from 'react';
import CandlestickChart from './components/CandlestickChart';
import TransactionFeed from './components/TransactionFeed';
import Card from './components/Card';
import TradeSummaryPanel from './components/TradeSummaryPanel';
import { Candle, Portfolio, BotTrade, MarketTrade, StrategyState, VolumeData, TradeSummary, TokenInfo } from './types';

const StrategyPanel: React.FC<{ state: StrategyState | null; currentPrice: number }> = ({ state, currentPrice }) => {
    if (!state) return <p className="text-gray-500">Awaiting entry signal...</p>;

    const drawdown = state.highest_price_seen > 0 ? ((state.highest_price_seen - currentPrice) / state.highest_price_seen) * 100 : 0;

    return (
        <div className="h-full grid grid-cols-2 gap-x-6 text-sm">
            {/* --- Column 1: Trade Plan --- */}
            <div className="space-y-3">
                <p className="text-gray-400 font-semibold mb-2 border-b border-gray-700/50 pb-1">Trade Plan</p>
                <div className="flex justify-between">
                    <span className="text-gray-400">Entry Price:</span>
                    <span className="font-mono text-white">{state.entry_price.toFixed(6)}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-gray-400">Stop-Loss:</span>
                    <span className="font-mono text-yellow-400">{state.stop_loss_price.toFixed(6)}</span>
                </div>
                <div className="pt-1">
                    <p className="text-gray-400 mb-1">Take-Profit Targets:</p>
                    <ul className="space-y-1">
                        {state.take_profit_tiers.map(([target, portion], i) => (
                            <li key={`tp-${i}`} className="flex justify-between text-gray-300">
                                <span>- Sell {portion * 100}%</span>
                                <span className="font-mono text-green-400">{(state.entry_price * (1 + target)).toFixed(6)}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {/* --- Column 2: Live Analysis --- */}
            <div className="space-y-3 border-l border-gray-700/50 pl-6">
                 <p className="text-gray-400 font-semibold mb-2 border-b border-gray-700/50 pb-1">Live Analysis</p>
                 <div className="flex justify-between">
                    <span className="text-gray-400">Peak Price:</span>
                    <span className="font-mono text-cyan-400">{state.highest_price_seen.toFixed(6)}</span>
                 </div>
                 <div className="flex justify-between">
                    <span className="text-gray-400">Drawdown:</span>
                    <span className={`font-mono ${drawdown > 0 ? 'text-red-400' : 'text-gray-400'}`}>{drawdown.toFixed(2)}%</span>
                 </div>
            </div>
        </div>
    );
};


function App() {
    // All state and WebSocket logic is correct and does not need changes.
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [tradeSummaries, setTradeSummaries] = useState<TradeSummary[]>([]);
    const [activeTokenInfo, setActiveTokenInfo] = useState<TokenInfo | null>(null);
    const [initialCandles, setInitialCandles] = useState<Candle[] | null>(null);
    const [lastCandle, setLastCandle] = useState<Candle | null>(null);
    const [initialVolume, setInitialVolume] = useState<VolumeData[] | null>(null);
    const [lastVolume, setLastVolume] = useState<VolumeData | null>(null);
    const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
    const [strategyState, setStrategyState] = useState<StrategyState | null>(null);
    const [botTrades, setBotTrades] = useState<BotTrade[]>([]);
    const [marketTrades, setMarketTrades] = useState<MarketTrade[]>([]);
    const initialCapital = 50.0;

    useEffect(() => {
        // Use your production WebSocket URL here
        const ws = new WebSocket('wss://legendary-tribble-v6vgw754rrrphp4rj-8765.app.github.dev');
        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            switch (message.type) {
                case 'NEW_TRADE_STARTING':
                    const tradeData = message.data;
                    setActiveTokenInfo(tradeData.token_info);
                    setInitialCandles(tradeData.candles || []);
                    setInitialVolume(tradeData.volumes || []);
                    setBotTrades(tradeData.bot_trades || []);
                    setStrategyState(tradeData.strategy_state || null);
                    setPortfolio(tradeData.portfolio || null);
                    setMarketTrades([]);
                    setLastCandle(null);
                    setLastVolume(null);
                    break;
                case 'TRADE_SUMMARY_UPDATE':
                    setTradeSummaries(message.data.summaries);
                    break;
                case 'UPDATE':
                    if (message.data.candle) setLastCandle(message.data.candle);
                    if (message.data.volume) setLastVolume(message.data.volume);
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
            }
        };
        return () => ws.close();
    }, []);

    const tradePnl = portfolio?.trade_pnl ?? 0;
    const pnlColor = tradePnl >= 0 ? 'text-green-400' : 'text-red-400';
    const currentPrice = lastCandle?.close ?? 0;
    const overallPnl = portfolio?.overall_pnl ?? tradeSummaries.reduce((acc, s) => acc + (s.status === 'Finished' ? s.pnl : 0), 0);
    const overallPnlColor = overallPnl >= 0 ? 'text-green-400' : 'text-red-400';
    const overallPnlPercent = (overallPnl / initialCapital) * 100;
    const currentWalletValue = portfolio?.total_value ?? (initialCapital + overallPnl);

    const activeAddress = activeTokenInfo?.address || null;
    const activeSymbol = activeTokenInfo?.symbol || "SYSTEM";
    const activeTradeStatus = tradeSummaries.find(s => s.token.address === activeAddress)?.status ?? 'Inactive';

    return (
        <div className="bg-gray-900 text-white h-screen font-sans flex flex-col p-4">
            <header className="flex-shrink-0 flex justify-between items-center border-b border-gray-700 pb-3 mb-4">
                 <div>
                    <h1 className="text-2xl font-bold">{activeSymbol} / SOL</h1>
                    <p className="text-sm text-gray-400">Autonomous Trading Bot - Mission Control</p>
                </div>
                <div className="flex items-center gap-x-12">
                    <div className="text-right">
                        <p className="text-sm text-gray-400">Current Price</p>
                        <p className="text-3xl font-mono text-white">{currentPrice > 0 ? currentPrice.toPrecision(6) : '...'}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-gray-400">Trade P&L</p>
                        <p className={`text-xl font-semibold ${pnlColor}`}>{tradePnl >= 0 ? `+${tradePnl.toFixed(4)}` : tradePnl.toFixed(4)} SOL</p>
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-400">Trade Status: <span className="font-semibold text-yellow-400">{activeTradeStatus}</span></span>
                    <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                        <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                    </div>
                </div>
            </header>

            <main className="flex-grow flex flex-row gap-4 overflow-hidden">
                <div className="flex flex-col gap-4 w-full max-w-xs">
                    <Card title="Overall Performance">
                        <div className="space-y-2 text-sm">
                            <p>Initial Wallet: <span className="font-mono text-gray-400 float-right">{initialCapital.toFixed(4)} SOL</span></p>
                            <p>Current Value: <span className="font-mono text-white float-right">{currentWalletValue.toFixed(4)} SOL</span></p>
                            <div className="border-t border-gray-700 my-2"></div>
                            <p>Total P&L: <span className={`font-mono float-right ${overallPnlColor}`}>{overallPnl >= 0 ? `+${overallPnl.toFixed(4)}` : overallPnl.toFixed(4)} SOL ({overallPnlPercent.toFixed(2)}%)</span></p>
                        </div>
                    </Card>
                    <Card title="Trade Queue" className="flex-grow min-h-0">
                       <TradeSummaryPanel summaries={tradeSummaries} activeTokenAddress={activeAddress} />
                    </Card>
                </div>
                
                <div className="flex-grow flex flex-col gap-4">
                    <div className="h-3/5 grid grid-cols-1 lg:grid-cols-4 gap-4">
                        <div className="lg:col-span-1 flex flex-col gap-4">
                            <Card title="Current Position">
                                {portfolio?.positions && activeAddress && portfolio.positions[activeAddress] ? (
                                    <div className="space-y-2 text-sm">
                                        <p>Tokens Held: <span className="font-mono text-white float-right">{portfolio.positions[activeAddress].tokens.toFixed(2)}</span></p>
                                        <p>Avg Cost: <span className="font-mono text-white float-right">{portfolio.positions[activeAddress].cost_basis.toFixed(6)}</span></p>
                                    </div>
                                ) : <p className="text-gray-500">No active position.</p>}
                            </Card>
                            <Card title="Bot Trade Log" className="flex-grow min-h-0">
                                <ul className="space-y-2 overflow-y-auto pr-2 h-full">
                                    {botTrades.map((trade, index) => (
                                        <li key={index} className="text-sm p-2 rounded bg-gray-700/50">
                                            <div className="flex justify-between items-center mb-1">
                                                <span className={`font-semibold ${trade.side === 'BUY' ? 'text-blue-400' : 'text-red-400'}`}>{trade.side}</span>
                                                <span className="text-gray-400 font-mono">@ {trade.price.toFixed(6)}</span>
                                            </div>
                                            <div className="text-white font-mono text-right">{trade.token_amount.toFixed(2)} {activeSymbol?.replace('COIN','')} <span className="text-gray-500">({trade.sol_amount.toFixed(4)} SOL)</span></div>
                                        </li>
                                    ))}
                                </ul>
                            </Card>
                        </div>
                        <div className="lg:col-span-3 bg-gray-800/50 rounded-lg p-2">
                             <CandlestickChart 
                                key={activeAddress || 'market-index'} 
                                initialData={initialCandles} 
                                initialVolume={initialVolume} 
                                update={lastCandle}
                                volumeUpdate={lastVolume}
                                botTrades={botTrades} 
                                strategyState={strategyState}
                            />
                        </div>
                    </div>
                    <div className="h-2/5 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Card title="Live Trade Analysis">
                           <StrategyPanel state={strategyState} currentPrice={currentPrice} />
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