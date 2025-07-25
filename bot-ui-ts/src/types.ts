import type { Time } from 'lightweight-charts';

// The shape of a single candle for the chart
export interface Candle {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
}

// The shape of a trade made by our bot
export interface BotTrade {
    time: Time;
    side: 'BUY' | 'SELL';
    price: number;
    sol_amount: number;
}

// A generic market trade, which could be from our bot
export interface MarketTrade {
    side: 'BUY' | 'SELL';
    sol_amount: number;
    price: number;
    timestamp: string; // ISO string from backend
    isBot?: boolean; // Optional flag to highlight our trades
}

// The state of a single token position in our portfolio
export interface Position {
    tokens: number;
    cost_basis: number;
}

// The overall portfolio state
export interface Portfolio {
    sol_balance: number;
    total_value: number;
    pnl: number;
    positions: Record<string, Position>; // A dictionary mapping token symbol to position
}

export interface StrategyState {
    entry_price: number;
    stop_loss_price: number;
    take_profit_tiers: [number, number][]; // Array of tuples [target_percent, sell_portion]
}

export interface VolumeData {
  time: Time;
  value: number;
  color: string;
}