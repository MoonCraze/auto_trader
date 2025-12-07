# Methodology

This document outlines the comprehensive methodology employed in the development and operation of the Autonomous Trading System. The system is designed to detect, analyze, and trade cryptocurrency tokens on the Solana blockchain in a fully automated manner.

## 1. System Overview

The Autonomous Trading System is a real-time, event-driven application built using Python's `asyncio` framework. It operates on a producer-consumer model where market signals are ingested, processed, and acted upon asynchronously. The system integrates with external data providers for market data and sentiment analysis, and it simulates trade execution within a controlled environment.

## 2. System Architecture

The architecture follows a modular design, separating concerns into distinct components:

*   **Signal Ingestion Layer**: Listens for potential trading opportunities via Server-Sent Events (SSE).
*   **Data Processing Layer**: Enriches raw signals with market data and sentiment analysis.
*   **Strategy Layer**: Determines entry and exit points based on technical indicators and risk management rules.
*   **Execution Layer**: Simulates the buying and selling of assets and manages the portfolio state.
*   **Presentation Layer**: A React/TypeScript frontend that visualizes the system's state and trade progress in real-time via WebSockets.

## 3. Data Acquisition

The system relies on three primary data sources:

1.  **Token Signals (SSE)**:
    *   The system connects to a Server-Sent Events (SSE) stream (`/stream`) to receive real-time notifications about potential token opportunities.
    *   Each signal contains the token's address and metadata (e.g., unique wallet count, window timing).
    *   **Implementation**: The `listen_for_tokens` coroutine in `websocket_server.py` handles the persistent connection and pushes raw signals to a processing queue.

2.  **Market Data (GeckoTerminal)**:
    *   Historical OHLCV (Open, High, Low, Close, Volume) data and real-time price updates are fetched from the GeckoTerminal API.
    *   **Implementation**: The `data_feeder.py` module provides `get_historical_data` for backtesting entry signals and `stream_data` for live price monitoring.

3.  **Sentiment Data**:
    *   The system queries a dedicated sentiment analysis API to gauge market sentiment for a specific token.
    *   **Implementation**: The `sentiment_analyzer.py` module fetches a sentiment score (0-100) and mention count. (Note: In the current iteration, this check is partially mocked for testing purposes).

## 4. Signal Processing Pipeline

The pipeline transforms raw signals into actionable trades through a multi-stage process:

### 4.1. Signal Ingestion & Metadata Resolution
Raw signals received from the SSE stream are parsed to extract the token address. The `TokenMetadata` class resolves this address to a human-readable symbol (e.g., "SOL", "BONK") using a mapping fetched from Jupiter's strict token list or a fallback dataset.

### 4.2. Sentiment Screening
Before any technical analysis, tokens undergo a sentiment check.
*   **Criteria**: The token must have a non-zero mention count and a sentiment score above a defined threshold (e.g., 60/100).
*   **Action**: Tokens failing this check are discarded. Passing tokens are promoted to the `Trade Queue`.

### 4.3. Technical Entry Analysis
For validated tokens, the system fetches historical price data to determine if a favorable entry condition exists. The `entry_strategy.py` module implements two strategies:
*   **SMA Crossover**: Checks if a short-term Simple Moving Average (SMA) has recently crossed above a long-term SMA.
*   **Breakout**: Checks if the current price exceeds the highest price observed in a defined lookback period.

If an entry signal is confirmed, the system proceeds to trade execution.

## 5. Trading Logic & Strategy

The core trading logic is encapsulated in the `StrategyEngine` and `PortfolioManager` classes.

### 5.1. Position Sizing
The system employs a fixed risk management rule defined in `config.py`.
*   **Risk Per Trade**: A percentage of the total portfolio balance (e.g., 2%) is allocated to each trade.
*   **Calculation**: `sol_to_invest = total_balance * RISK_PER_TRADE_PERCENT`.

### 5.2. Trade Execution (Simulation)
The `ExecutionEngine` simulates the mechanics of a decentralized exchange (DEX).
*   **Buying**: Converts the allocated SOL amount into tokens at the current market price.
*   **Selling**: Converts tokens back to SOL.
*   **Portfolio Management**: The `PortfolioManager` tracks the global SOL balance, current token holdings, and calculates the realized and unrealized P&L (Profit and Loss).

### 5.3. Exit Strategy
Once a trade is active, the `StrategyEngine` monitors price movements in real-time to decide when to sell. It uses a composite exit strategy:

*   **Stop-Loss**:
    *   **Initial**: A hard stop-loss is set at a fixed percentage below the entry price (e.g., -15%).
    *   **Breakeven**: Once the first take-profit target is hit, the stop-loss is moved to the entry price to protect capital.
    *   **Trailing**: If the price rises significantly, the stop-loss trails the highest price seen by a fixed percentage (e.g., 20%).

*   **Take-Profit (Tiered)**:
    *   The system defines multiple profit targets (e.g., +30%, +75%).
    *   When a target is reached, a pre-determined portion of the position (e.g., 33%) is sold to lock in profits while keeping the remainder for potential further gains.

## 6. Real-Time Monitoring & Visualization

To provide transparency and observability, the system broadcasts its internal state to a frontend dashboard.

*   **WebSocket Server**: A `websockets` server runs alongside the trading loop. It accepts connections from the UI.
*   **State Broadcasting**:
    *   **`NEW_TRADE_STARTING`**: Sent when a trade is entered, containing initial candles and strategy parameters.
    *   **`UPDATE`**: Sent on every new price candle (every 5 minutes or simulated interval), containing the latest price, portfolio value, and any trade events (buy/sell).
    *   **`TRADE_SUMMARY_UPDATE`**: Sent to update the list of active, pending, and finished trades.

## 7. Concurrency Model

The entire backend is orchestrated using Python's `asyncio`. This allows the system to:
1.  Maintain a persistent connection to the SSE stream.
2.  Serve WebSocket clients.
3.  Monitor multiple active trades simultaneously.
4.  Process background tasks (like market index streaming).

This non-blocking architecture ensures that the system remains responsive to new signals even while managing active positions.
