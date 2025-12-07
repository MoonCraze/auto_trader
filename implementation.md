## 1. Development Environment & Technologies

The system was developed using a modern full-stack approach, leveraging Python for high-performance backend processing and TypeScript/React for a responsive user interface.

*   **Backend Language**: Python 3.10+ was chosen for its rich ecosystem of data science libraries (`pandas`, `numpy`) and robust asynchronous support (`asyncio`).
*   **Frontend Framework**: React 18 with TypeScript was selected for building a type-safe, component-based UI. Vite was used as the build tool for its fast hot-module replacement (HMR) capabilities.
*   **Asynchronous Networking**: The `aiohttp` library handles asynchronous HTTP requests, while `websockets` manages real-time bidirectional communication.
*   **Data Visualization**: `lightweight-charts` (by TradingView) renders high-performance financial charts in the frontend.

## 2. Backend Implementation

The backend is the core of the system, responsible for data ingestion, strategy execution, and state management. It is structured around a central event loop managed by `asyncio`.

### 2.1. Core Event Loop (`websocket_server.py`)
The entry point of the application is the `main()` coroutine in `websocket_server.py`. It initializes the system components and uses `asyncio.gather()` to run multiple concurrent tasks:
1.  **WebSocket Server**: Listens for incoming UI connections on port 8765.
2.  **Signal Listener**: A dedicated coroutine `listen_for_tokens` that maintains a persistent connection to the SSE stream.
3.  **Sentiment Processor**: A consumer coroutine `process_sentiment_queue` that validates raw signals.
4.  **Trade Processor**: The `process_trade_queue` coroutine that manages the lifecycle of active trades.
5.  **Background Data Stream**: Fetches and broadcasts market index data to keep the UI alive even when no trades are active.

### 2.2. Data Ingestion & Simulation
*   **SSE Client**: The `sse.py` module implements a mock Flask server to simulate the Server-Sent Events provider. It generates random token signals with metadata (e.g., wallet counts, timestamps) to test the system's ingestion pipeline.
*   **GeckoTerminal Client**: The `geckoterminal_client.py` module interfaces with the GeckoTerminal API. It includes:
    *   `get_ohlcv()`: Fetches historical candlestick data for backtesting entry signals.
    *   `stream_data()`: An asynchronous generator that polls for the latest candle data, simulating a real-time WebSocket feed.

### 2.3. Trading Engine
The trading logic is decoupled into three specialized classes:
*   **`PortfolioManager`**: Acts as the ledger for the system. It tracks the global SOL balance and maintains a dictionary of open positions. It calculates Realized P&L (on sell) and Unrealized P&L (mark-to-market) in real-time.
*   **`ExecutionEngine`**: Abstracts the complexity of trade execution. In this simulation, it calculates slippage-free token amounts based on current prices and updates the `PortfolioManager`.
*   **`StrategyEngine`**: Manages the state of an individual trade. It stores the entry price, calculates dynamic stop-loss levels (trailing stop), and tracks take-profit targets. The `check_for_trade_action()` method is called on every price update to determine if a `SELL` or `HOLD` decision is required.

### 2.4. Signal Processing
*   **Entry Strategy**: The `entry_strategy.py` module implements technical analysis algorithms using `pandas`. The `find_sma_buy_signal` function calculates rolling averages to detect crossovers, while `find_breakout_buy_signal` compares current prices against a historical window.
*   **Sentiment Analysis**: The `sentiment_analyzer.py` module performs HTTP GET requests to a sentiment API. It implements an exponential backoff retry mechanism to handle transient network failures and API rate limits.

## 3. Frontend Implementation

The frontend is a single-page application (SPA) built with React and TypeScript. It provides a real-time "Mission Control" dashboard for the user.

### 3.1. Component Architecture
The UI is composed of modular components:
*   **`App.tsx`**: The root component that manages the WebSocket connection and global application state (e.g., `portfolio`, `activeTokenInfo`).
*   **`CandlestickChart.tsx`**: A wrapper around the `lightweight-charts` library. It uses React `useEffect` hooks to efficiently update candle data and draw dynamic price lines (Entry, Stop-Loss, Take-Profit) without re-rendering the entire chart.
*   **`TradeSummaryPanel.tsx`**: Displays a list of all processed tokens, showing their current status (Screening, Active, Finished) and P&L.
*   **`TransactionFeed.tsx`**: A scrolling list of recent market and bot trades.

### 3.2. Real-Time State Management
The frontend does not poll the backend. Instead, it relies entirely on WebSocket messages pushed by the server. The `App` component maintains a `websocket` instance and updates React state based on message types:
*   **`NEW_TRADE_STARTING`**: Resets the chart and loads historical data for the new token.
*   **`UPDATE`**: Appends a new candle to the chart and updates the portfolio summary.
*   **`TRADE_SUMMARY_UPDATE`**: Refreshes the side panel list of processed tokens.

## 4. Integration & Data Flow

The integration between backend and frontend is achieved through a custom JSON-based protocol over WebSockets.

1.  **Initialization**: When the UI connects, the backend immediately sends the current `APP_STATE`, ensuring the user sees the latest data even if they refresh the page.
2.  **Broadcasting**: The `broadcast()` function in `websocket_server.py` iterates through all connected clients and sends JSON payloads. This allows multiple UI instances to monitor the bot simultaneously.
3.  **Concurrency**: The backend uses `asyncio.sleep(0)` or `await` points during heavy data processing to ensure the WebSocket heartbeat is maintained, preventing client disconnections during intensive tasks.
