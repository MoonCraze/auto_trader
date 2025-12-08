import React, { useEffect, useRef } from 'react';
import { 
    ColorType, 
    createChart, 
    IChartApi, 
    ISeriesApi,
    LineStyle,
    SeriesMarker, 
    SeriesMarkerPosition, 
    SeriesMarkerShape,
    IPriceLine
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
    const lastCandleTimeRef = useRef<number | null>(null);
    const lastVolumeTimeRef = useRef<number | null>(null);
    
    // <<< THE DEFINITIVE FIX: We will manage lines within effects, not in top-level refs.
    const stopLossLineRef = useRef<IPriceLine | null>(null);
    const priceLinesRef = useRef<IPriceLine[]>([]);

    // This effect runs ONCE when the component mounts (thanks to the key prop).
    // It is responsible for all initial setup.
    useEffect(() => {
        if (!chartContainerRef.current) return;
        
        const chart = createChart(chartContainerRef.current, { 
            autoSize: true, 
            layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: 'rgba(255, 255, 255, 0.7)'}, 
            grid: { vertLines: { color: 'rgba(255, 255, 255, 0.1)' }, horzLines: { color: 'rgba(255, 255, 255, 0.1)' }}, 
            timeScale: { timeVisible: true, secondsVisible: false }
        });
        const candleSeries = chart.addCandlestickSeries({ upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350' });
        const volumeSeries = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '', lastValueVisible: false, priceLineVisible: false });
        chart.priceScale('').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        volumeSeriesRef.current = volumeSeries;

        if (initialData && initialData.length > 0) {
            candleSeries.setData(initialData);
            lastCandleTimeRef.current = initialData[initialData.length - 1].time as number;
        }
        if (initialVolume && initialVolume.length > 0) {
            volumeSeries.setData(initialVolume);
            lastVolumeTimeRef.current = initialVolume[initialVolume.length - 1].time as number;
        }
        
        // The cleanup function is called when the component is destroyed.
        return () => {
            chart.remove();
        };
    }, []); // Empty dependency array is CRUCIAL.

    // This effect is ONLY for live candle updates.
    useEffect(() => {
        if (update && candleSeriesRef.current) {
            const updateTime = update.time as number;
            if (lastCandleTimeRef.current !== null && updateTime <= lastCandleTimeRef.current) return; // Ignore stale/duplicate updates
            candleSeriesRef.current.update(update);
            lastCandleTimeRef.current = updateTime;
        }
    }, [update]);

    // This effect is ONLY for live volume updates.
    useEffect(() => {
        if (volumeUpdate && volumeSeriesRef.current) {
            const updateTime = volumeUpdate.time as number;
            if (lastVolumeTimeRef.current !== null && updateTime <= lastVolumeTimeRef.current) return;
            volumeSeriesRef.current.update(volumeUpdate);
            lastVolumeTimeRef.current = updateTime;
        }
    }, [volumeUpdate]);
    
    // This effect is ONLY for updating the markers.
    useEffect(() => {
        if (candleSeriesRef.current) {
            const markers: SeriesMarker<any>[] = (botTrades || []).map(trade => ({ time: trade.time, position: (trade.side === 'BUY' ? 'belowBar' : 'aboveBar') as SeriesMarkerPosition, color: trade.side === 'BUY' ? '#2196F3' : '#F44336', shape: (trade.side === 'BUY' ? 'arrowUp' : 'arrowDown') as SeriesMarkerShape, text: `${trade.side} @ ${trade.price.toFixed(6)}`, size: 1.2 }));
            candleSeriesRef.current.setMarkers(markers);
        }
    }, [botTrades]);

    // <<< THE DEFINITIVE FIX: A single, clean effect for drawing and updating strategy lines.
    useEffect(() => {
        const series = candleSeriesRef.current;
        if (!strategyState || !series) return;

        // Clear old lines to prevent duplicates
        priceLinesRef.current.forEach(line => series.removePriceLine(line));
        priceLinesRef.current = [];
        stopLossLineRef.current = null;

        // Draw Entry
        const entryLine = series.createPriceLine({ price: strategyState.entry_price, color: '#2196F3', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: 'ENTRY' });
        priceLinesRef.current.push(entryLine);

        // Draw Take-Profits
        strategyState.take_profit_tiers.forEach(([targetPercent], i) => {
            const targetPrice = strategyState.entry_price * (1 + targetPercent);
            const tpLine = series.createPriceLine({ price: targetPrice, color: '#4CAF50', lineWidth: 1, lineStyle: LineStyle.Dotted, axisLabelVisible: true, title: `TP ${i + 1}` });
            priceLinesRef.current.push(tpLine);
        });
        
        // Draw Stop-Loss
        const slLine = series.createPriceLine({ price: strategyState.stop_loss_price, color: '#FFEB3B', lineWidth: 2, lineStyle: LineStyle.Solid, axisLabelVisible: true, title: 'STOP' });
        stopLossLineRef.current = slLine;
        priceLinesRef.current.push(slLine);

        // Cleanup removes all created lines
        return () => {
            priceLinesRef.current.forEach(line => series.removePriceLine(line));
            priceLinesRef.current = [];
            stopLossLineRef.current = null;
        }

    }, [strategyState?.entry_price]); // Depend only on entry_price to draw static lines once.

    // A separate, tiny effect ONLY for updating the stop-loss line.
    useEffect(() => {
        if(strategyState && stopLossLineRef.current) {
            stopLossLineRef.current.applyOptions({ price: strategyState.stop_loss_price });
        }
    }, [strategyState?.stop_loss_price]); // Depend only on the stop-loss price.

    return <div ref={chartContainerRef} className="w-full h-full" />;
};

export default CandlestickChart;