import type { Time } from 'lightweight-charts';

export interface Candle {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface BotTrade {
    time: Time;
    side: 'BUY' | 'SELL';
    price: number;
    sol_amount: number;
    token_amount: number;
}

export interface MarketTrade {
    side: 'BUY' | 'SELL';
    sol_amount: number;
    price: number;
    timestamp: string;
    isBot?: boolean;
}

export interface Position {
    tokens: number;
    cost_basis: number;
}

export interface Portfolio {
    sol_balance: number;
    total_value: number;
    pnl: number;
    positions: Record<string, Position>;
}

export interface StrategyState {
    entry_price: number;
    stop_loss_price: number;
    take_profit_tiers: [number, number][];
}

export interface VolumeData {
  time: Time;
  value: number;
  color: string;
}

export interface TradeSummary {
  token: string;
  status: 'Pending' | 'Monitoring' | 'Active' | 'Finished';
  pnl: number;
}