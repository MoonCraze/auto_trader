import React from 'react';
import { Portfolio, BotTrade } from '../types';

interface InfoPanelProps {
    portfolio: Portfolio | null;
    botTrades: BotTrade[];
}

const InfoPanel: React.FC<InfoPanelProps> = ({ portfolio, botTrades }) => {
    // Safely access portfolio data using optional chaining (?.)
    const pnl = portfolio?.pnl ?? 0;
    const initialCapital = (portfolio?.total_value ?? 0) - pnl;
    const pnlPercent = initialCapital > 0 ? (pnl / initialCapital) * 100 : 0;
    const pnlColor = pnl >= 0 ? 'text-green-400' : 'text-red-400';
    
    const currentPosition = portfolio?.positions?.MOGCOIN;

    return (
        <div className="bg-gray-800 p-4 rounded-lg h-full flex flex-col space-y-4">
            <div>
                <h3 className="text-lg font-semibold text-white mb-2 border-b border-gray-700 pb-2">Portfolio</h3>
                <div className="space-y-1 text-gray-300">
                    <p>Total Value: <span className="font-mono text-white">{portfolio?.total_value.toFixed(4) ?? '...'} SOL</span></p>
                    <p>SOL Balance: <span className="font-mono text-white">{portfolio?.sol_balance.toFixed(4) ?? '...'} SOL</span></p>
                    <p>Total P&L: <span className={`font-mono ${pnlColor}`}>{pnl.toFixed(4)} SOL ({pnlPercent.toFixed(2)}%)</span></p>
                </div>
            </div>
            
            {currentPosition && (
                 <div>
                    <h3 className="text-lg font-semibold text-white mb-2 border-b border-gray-700 pb-2">Current Position (MOGCOIN)</h3>
                    <div className="space-y-1 text-gray-300">
                        <p>Tokens Held: <span className="font-mono text-white">{currentPosition.tokens.toFixed(2)}</span></p>
                        <p>Avg Cost: <span className="font-mono text-white">{currentPosition.cost_basis.toFixed(6)}</span></p>
                    </div>
                </div>
            )}

            <div className="flex-grow flex flex-col">
                <h3 className="text-lg font-semibold text-white mb-2 border-b border-gray-700 pb-2">Bot Trade Log</h3>
                <ul className="space-y-2 overflow-y-auto pr-2 flex-grow">
                     {botTrades.map((trade, index) => (
                         <li key={index} className="text-sm p-1.5 rounded bg-blue-900 bg-opacity-50">
                            <span className={trade.side === 'BUY' ? 'text-blue-400' : 'text-red-400'}>{trade.side} </span>
                            <span className="text-gray-300">{trade.sol_amount.toFixed(4)} SOL </span>
                            <span className="text-gray-400">@ {trade.price.toFixed(6)}</span>
                         </li>
                     ))}
                </ul>
            </div>
        </div>
    );
};

export default InfoPanel;