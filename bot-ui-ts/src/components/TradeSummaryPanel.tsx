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
            case 'Screening': return `${baseClasses} bg-purple-500 text-white animate-pulse`;
            case 'Finished': return `${baseClasses} bg-gray-600 text-gray-200`;
            case 'Pending': return `${baseClasses} bg-gray-700 text-gray-400`;
            case 'Failed': return `${baseClasses} bg-red-800 text-red-200 opacity-60`;
        }
    };

    const getSentimentColor = (score: number | null) => {
        if (score === null) return 'text-gray-500';
        if (score > 75) return 'text-green-400';
        if (score > 60) return 'text-yellow-400';
        return 'text-red-400';
    }

    return (
        <ul className="space-y-3">
            {summaries.map((summary) => (
                // Filter out 'Failed' trades after 1 minute to keep the queue clean
                // A more advanced implementation could use a timestamp
                // if (summary.status === 'Failed') return null;

                <li key={summary.token.address} className={`p-3 rounded-lg border-2 transition-all ${summary.token.address === activeTokenAddress ? 'border-blue-500 bg-gray-700/50' : 'border-transparent bg-gray-800/50'}`}>
                    <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-lg truncate pr-2">{summary.token.symbol}</span>
                        <span className={getStatusChip(summary.status)}>{summary.status}</span>
                    </div>
                    <p className="text-xs text-gray-500 font-mono truncate">{summary.token.address}</p>
                    
                    {/* <<< NEW: Sentiment Score Display --- */}
                    {summary.sentiment_score !== null && (
                         <div className="text-xs mt-2 pt-2 border-t border-gray-700/50 flex justify-between items-center">
                            <span className="text-gray-400">Sentiment:</span>
                            <span className={`font-mono font-semibold ${getSentimentColor(summary.sentiment_score)}`}>
                                {summary.sentiment_score.toFixed(0)}%
                                <span className="text-gray-500 font-normal"> ({summary.mention_count} mentions)</span>
                            </span>
                        </div>
                    )}

                    {summary.status === 'Finished' && (
                        <div className={`text-right text-md font-mono mt-2 pt-2 border-t border-gray-700/50 ${summary.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                           <span className="text-sm text-gray-400">P&L:</span> {summary.pnl >= 0 ? `+${summary.pnl.toFixed(4)}` : summary.pnl.toFixed(4)} SOL
                        </div>
                    )}
                </li>
            ))}
        </ul>
    );
};

export default TradeSummaryPanel;