import React from 'react';
import { MarketTrade } from '../types';

interface TransactionFeedProps {
    trades: MarketTrade[];
}

const TransactionFeed: React.FC<TransactionFeedProps> = ({ trades }) => {
    return (
        <ul className="h-full space-y-2 overflow-y-auto pr-2">
            {trades.slice(0, 100).map((trade, index) => { // Show more trades
                const isBuy = trade.side === 'BUY';
                const bgColor = trade.isBot ? 'bg-blue-500 bg-opacity-30' : 'bg-transparent';
                return (
                    <li key={index} className={`flex justify-between items-center text-sm p-1.5 rounded ${bgColor}`}>
                        <span className={`font-semibold ${isBuy ? 'text-green-400' : 'text-red-400'}`}>
                            {isBuy ? 'BUY' : 'SELL'}
                        </span>
                        <span className="text-gray-300 font-mono">
                            {trade.sol_amount.toFixed(4)} SOL
                        </span>
                        <span className="text-gray-400 font-mono">
                            @{trade.price.toFixed(6)}
                        </span>
                    </li>
                );
            })}
        </ul>
    );
};

export default TransactionFeed;