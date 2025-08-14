import React from 'react';
import { TradeSummary } from '../types';

interface TradeSummaryPanelProps {
    summaries: TradeSummary[];
    activeTokenAddress: string | null;
}

const TradeSummaryPanel: React.FC<TradeSummaryPanelProps> = ({ summaries, activeTokenAddress }) => {
    
    const getStatusChip = (status: TradeSummary['status']) => {
        const baseClasses = "px-2 py-0.5 text-xs font-semibold rounded-full";
        switch(status) {
            case 'Active': return `${baseClasses} bg-blue-500 text-white`;
            case 'Monitoring': return `${baseClasses} bg-yellow-500 text-black`;
            case 'Finished': return `${baseClasses} bg-gray-600 text-gray-200`;
            case 'Pending': return `${baseClasses} bg-gray-700 text-gray-400`;
        }
    };

    // <<< THE DEFINITIVE FIX IS HERE ---
    return (
        <ul className="h-full space-y-3 overflow-y-auto pr-2">
            {summaries.map((summary) => (
                <li key={summary.token.address} className={`p-3 rounded-lg border-2 transition-all ${summary.token.address === activeTokenAddress ? 'border-blue-500 bg-gray-700/50' : 'border-transparent bg-gray-800/50'}`}>
                    <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-lg">{summary.token.symbol}</span>
                        <span className={getStatusChip(summary.status)}>{summary.status}</span>
                    </div>
                    <p className="text-xs text-gray-500 font-mono truncate">{summary.token.address}</p>
                    {summary.status === 'Finished' && (
                        <div className={`text-right text-md font-mono mt-2 ${summary.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                           P&L: {summary.pnl >= 0 ? `+${summary.pnl.toFixed(4)}` : summary.pnl.toFixed(4)} SOL
                        </div>
                    )}
                </li>
            ))}
        </ul>
    );
};

export default TradeSummaryPanel;