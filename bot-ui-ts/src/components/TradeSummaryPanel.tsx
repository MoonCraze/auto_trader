import React from 'react';
import { TradeSummary } from '../types';

interface TradeSummaryPanelProps {
    summaries: TradeSummary[];
    activeToken: string | null;
}

const TradeSummaryPanel: React.FC<TradeSummaryPanelProps> = ({ summaries, activeToken }) => {
    
    const getStatusChip = (status: TradeSummary['status']) => {
        const baseClasses = "px-2 py-0.5 text-xs font-semibold rounded-full";
        switch(status) {
            case 'Active': return `${baseClasses} bg-blue-500 text-white`;
            case 'Monitoring': return `${baseClasses} bg-yellow-500 text-black`;
            case 'Finished': return `${baseClasses} bg-gray-600 text-gray-200`;
            case 'Pending': return `${baseClasses} bg-gray-700 text-gray-400`;
        }
    };

    return (
        <ul className="space-y-3">
            {summaries.map((summary) => (
                <li key={summary.token} className={`p-3 rounded-lg border-2 transition-all ${summary.token === activeToken ? 'border-blue-500 bg-gray-700/50' : 'border-transparent bg-gray-800/50'}`}>
                    <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-lg">{summary.token}</span>
                        <span className={getStatusChip(summary.status)}>{summary.status}</span>
                    </div>
                    {summary.status === 'Finished' && (
                        <div className={`text-right text-md font-mono ${summary.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                           P&L: {summary.pnl.toFixed(4)} SOL
                        </div>
                    )}
                </li>
            ))}
        </ul>
    );
};

export default TradeSummaryPanel;