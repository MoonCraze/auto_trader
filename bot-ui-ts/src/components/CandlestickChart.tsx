import React, { useEffect, useRef } from 'react';
import { 
    ColorType, 
    createChart, 
    IChartApi, 
    ISeriesApi,
    SeriesMarker,
    SeriesMarkerPosition,
    SeriesMarkerShape 
} from 'lightweight-charts';
import { BotTrade, Candle } from '../types';

interface CandlestickChartProps {
    initialData: Candle[] | null;
    update: Candle | null;
    botTrades: BotTrade[];
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({ initialData, update, botTrades }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;
        const chart = createChart(chartContainerRef.current, {
            layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: 'rgba(255, 255, 255, 0.7)' },
            grid: { vertLines: { color: 'rgba(255, 255, 255, 0.1)' }, horzLines: { color: 'rgba(255, 255, 255, 0.1)' } },
            timeScale: { timeVisible: true, secondsVisible: false },
            autoSize: true, 
        });
        
        const series = chart.addCandlestickSeries({
            upColor: '#26a69a', downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a', wickDownColor: '#ef5350',
        });
        
        chartRef.current = chart;
        seriesRef.current = series;
        
        return () => {
            chart.remove();
        };
    }, []);

    useEffect(() => {
        if (initialData && seriesRef.current) {
            seriesRef.current.setData(initialData);
        }
    }, [initialData]);

    useEffect(() => {
        if (update && seriesRef.current) {
            seriesRef.current.update(update);
        }
    }, [update]);

    useEffect(() => {
        if (botTrades && seriesRef.current) {
            const markers: SeriesMarker<typeof botTrades[0]['time']>[] = botTrades.map(trade => ({
                time: trade.time,
                position: (trade.side === 'BUY' ? 'belowBar' : 'aboveBar') as SeriesMarkerPosition,
                color: trade.side === 'BUY' ? '#2196F3' : '#F44336',
                shape: (trade.side === 'BUY' ? 'arrowUp' : 'arrowDown') as SeriesMarkerShape,
                text: `${trade.side} @ ${trade.price.toFixed(6)}`
            }));
            seriesRef.current.setMarkers(markers);
        }
    }, [botTrades]);

    return <div ref={chartContainerRef} className="w-full h-full" />;
};

export default CandlestickChart;