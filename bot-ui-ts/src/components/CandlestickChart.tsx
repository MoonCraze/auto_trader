import React, { useEffect, useRef } from 'react';
import { 
    ColorType, 
    createChart, 
    IChartApi, 
    ISeriesApi, 
    PriceLineOptions, 
    SeriesMarker, 
    SeriesMarkerPosition, 
    SeriesMarkerShape, 
    IPriceLine, 
    LineStyle 
} from 'lightweight-charts';
import { BotTrade, Candle, StrategyState, VolumeData } from '../types';

interface CandlestickChartProps {
    initialData: Candle[] | null;
    initialVolume: VolumeData[] | null;
    update: Candle | null;
    volumeUpdate: VolumeData | null;
    botTrades: BotTrade[];
    strategyState: StrategyState | null;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({ initialData, initialVolume, update, volumeUpdate, botTrades, strategyState }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
    const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
    
    // Refs to hold our dynamic line objects
    const entryPriceLineRef = useRef<IPriceLine | null>(null);
    const stopLossLineRef = useRef<IPriceLine | null>(null);
    const takeProfitLineRefs = useRef<(IPriceLine | null)[]>([]);

    // Initialization Effect (Correct - No Changes)
    useEffect(() => {
        if (!chartContainerRef.current) return;
        const chart = createChart(chartContainerRef.current, { autoSize: true, layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: 'rgba(255, 255, 255, 0.7)'}, grid: { vertLines: { color: 'rgba(255, 255, 255, 0.1)' }, horzLines: { color: 'rgba(255, 255, 255, 0.1)' }}, timeScale: { timeVisible: true, secondsVisible: false }});
        const candleSeries = chart.addCandlestickSeries({ upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350' });
        const volumeSeries = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '', lastValueVisible: false, priceLineVisible: false });
        chart.priceScale('').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });
        
        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        volumeSeriesRef.current = volumeSeries;

        return () => chart.remove();
    }, []);

    // Data Update Effects (Correct - No Changes)
    useEffect(() => {
        if (initialData && candleSeriesRef.current) candleSeriesRef.current.setData(initialData);
        if (initialVolume && volumeSeriesRef.current) volumeSeriesRef.current.setData(initialVolume);
    }, [initialData, initialVolume]);

    useEffect(() => {
        if (update && candleSeriesRef.current) candleSeriesRef.current.update(update);
        if (volumeUpdate && volumeSeriesRef.current) volumeSeriesRef.current.update(volumeUpdate);
    }, [update, volumeUpdate]);

    // <<< FIX 1: This hook is now ONLY responsible for trade markers. ---
    useEffect(() => {
        if (botTrades && candleSeriesRef.current) {
            const markers: SeriesMarker<any>[] = botTrades.map(trade => ({ 
                time: trade.time, 
                position: (trade.side === 'BUY' ? 'belowBar' : 'aboveBar') as SeriesMarkerPosition, 
                color: trade.side === 'BUY' ? '#2196F3' : '#F44336', 
                shape: (trade.side === 'BUY' ? 'arrowUp' : 'arrowDown') as SeriesMarkerShape, 
                text: `${trade.side} @ ${trade.price.toFixed(6)}`, 
                size: 1.2 
            }));
            candleSeriesRef.current.setMarkers(markers);
            
            // The old logic that tried to create a price line here has been REMOVED.
        }
    }, [botTrades]);

    // <<< FIX 2: This hook is the SINGLE SOURCE OF TRUTH for drawing strategy lines. ---
    useEffect(() => {
        if (!candleSeriesRef.current) return;

        // If strategyState is null (e.g., in "Monitoring" phase), remove all lines.
        if (!strategyState) {
            if (entryPriceLineRef.current) candleSeriesRef.current.removePriceLine(entryPriceLineRef.current);
            if (stopLossLineRef.current) candleSeriesRef.current.removePriceLine(stopLossLineRef.current);
            takeProfitLineRefs.current.forEach(line => { if(line) candleSeriesRef.current!.removePriceLine(line)});
            
            entryPriceLineRef.current = null;
            stopLossLineRef.current = null;
            takeProfitLineRefs.current = [];
            return;
        }

        // --- Create or Update Entry Price Line ---
        if (!entryPriceLineRef.current) {
            entryPriceLineRef.current = candleSeriesRef.current.createPriceLine({ price: strategyState.entry_price, color: '#2196F3', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: 'ENTRY' });
        }

        // --- Create or Update Stop-Loss Line ---
        if (!stopLossLineRef.current) {
            stopLossLineRef.current = candleSeriesRef.current.createPriceLine({ price: strategyState.stop_loss_price, color: '#FFEB3B', lineWidth: 2, lineStyle: LineStyle.Solid, axisLabelVisible: true, title: 'STOP' });
        } else {
            stopLossLineRef.current.applyOptions({ price: strategyState.stop_loss_price });
        }
        
        // --- Create Take-Profit Lines (only once) ---
        if (takeProfitLineRefs.current.length === 0) {
            strategyState.take_profit_tiers.forEach(([targetPercent], i) => {
                const targetPrice = strategyState.entry_price * (1 + targetPercent);
                const tpLine = candleSeriesRef.current!.createPriceLine({ price: targetPrice, color: '#4CAF50', lineWidth: 1, lineStyle: LineStyle.Dotted, axisLabelVisible: true, title: `TP ${i + 1}` });
                takeProfitLineRefs.current.push(tpLine);
            });
        }

    }, [strategyState]);

    return <div ref={chartContainerRef} className="w-full h-full" />;
};

export default CandlestickChart;