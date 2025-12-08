# Research Diagrams

This document contains Mermaid diagrams illustrating the architecture, data flow, and logic of the Auto-Trader system. You can render these diagrams using a Mermaid-compatible viewer or editor (like the Mermaid Preview extension in VS Code).

## 1. System Architecture

This diagram provides a high-level overview of the system components and their interactions.

```mermaid
graph TD
    subgraph "Frontend (React/TypeScript)"
        UI[User Interface]
        Chart[Candlestick Chart]
        Feed[Transaction Feed]
        Summary[Trade Summary Panel]
        WS_Client[WebSocket Client]
    end

    subgraph "Backend (Python/Asyncio)"
        WS_Server[WebSocket Server]
        Main[Main Event Loop]
        
        subgraph "Core Modules"
            PM[Portfolio Manager]
            EE[Execution Engine]
            SE[Strategy Engine]
            TM[Token Metadata]
        end
        
        subgraph "Data & Signals"
            SSE_Listener[SSE Signal Listener]
            Sent_Proc[Sentiment Processor]
            Data_Feeder[Data Feeder]
        end
    end

    subgraph "External Services"
        GT_API[GeckoTerminal API]
        Signal_Source[Signal Provider (SSE)]
    end

    %% Connections
    Signal_Source -->|Stream Signals| SSE_Listener
    SSE_Listener -->|Raw Token Info| Sent_Proc
    Sent_Proc -->|Validated Token| Main
    
    Main -->|Manage| PM
    Main -->|Execute Trades| EE
    Main -->|Monitor Strategy| SE
    
    Data_Feeder -->|OHLCV Data| GT_API
    Main -->|Request Data| Data_Feeder
    
    WS_Server <-->|Real-time Updates| WS_Client
    WS_Client --> UI
    UI --> Chart
    UI --> Feed
    UI --> Summary
    
    Main -->|Broadcast State| WS_Server
```

## 2. Data Processing Pipeline

This diagram illustrates the flow of a token signal from detection to trade execution and completion.

```mermaid
flowchart LR
    Signal((Signal Received)) --> Queue1[Raw Signal Queue]
    Queue1 --> Sentiment{Sentiment Screening}
    
    Sentiment -- Pass --> Queue2[Trade Queue]
    Sentiment -- Fail --> Discard[Discard / Log]
    
    Queue2 --> Processor[Trade Processor]
    
    subgraph "Trade Lifecycle"
        Processor --> FetchData[Fetch Historical Data]
        FetchData --> EntryCheck{Entry Signal?}
        
        EntryCheck -- Yes --> Buy[Execute Buy]
        EntryCheck -- No --> Skip[Skip Token]
        
        Buy --> Monitor[Start Monitoring Loop]
        
        Monitor --> Stream[Stream Live Prices]
        Stream --> Strategy{Strategy Check}
        
        Strategy -- Hold --> Monitor
        Strategy -- Sell --> Sell[Execute Sell]
        
        Sell --> Finish((Trade Complete))
    end
```

## 3. Class Relationships

This diagram shows the structure and relationships of the key Python classes in the backend.

```mermaid
classDiagram
    class PortfolioManager {
        +float sol_balance
        +dict positions
        +list trade_log
        +record_buy(token, amount, price)
        +record_sell(token, amount, price)
        +get_total_value(current_prices)
    }

    class ExecutionEngine {
        -PortfolioManager pm
        +execute_buy(token_info, sol_amount, price)
        +execute_sell(token_info, token_amount, price)
    }

    class StrategyEngine {
        +float entry_price
        +float stop_loss_price
        +list take_profit_tiers
        +check_for_trade_action(current_price)
    }

    class GeckoTerminalClient {
        +get_ohlcv(network, pool_address)
        +get_latest_candle(network, pool_address)
    }

    class TokenMetadata {
        +initialize()
        +get_symbol(address)
    }

    ExecutionEngine --> PortfolioManager : Updates
    StrategyEngine ..> ExecutionEngine : Triggers Actions
    Main --> ExecutionEngine : Uses
    Main --> StrategyEngine : Creates & Monitors
    Main --> GeckoTerminalClient : Fetches Data
    Main --> TokenMetadata : Resolves Symbols
```

## 4. Trade Execution Sequence

This sequence diagram details the interactions during the `process_single_token` workflow.

```mermaid
sequenceDiagram
    participant Main as Main Process
    participant DF as Data Feeder
    participant EE as Execution Engine
    participant PM as Portfolio Manager
    participant SE as Strategy Engine
    participant WS as WebSocket Server

    Main->>DF: get_historical_data(pool_address)
    DF-->>Main: DataFrame (OHLCV)
    
    Main->>Main: check_for_entry_signal(history)
    
    alt Signal Found
        Main->>EE: execute_buy(token, amount, price)
        EE->>PM: record_buy()
        PM-->>EE: Success
        EE-->>Main: Tokens Bought
        
        Main->>SE: Initialize(entry_price, quantity)
        Main->>WS: Broadcast NEW_TRADE_STARTING
        
        loop Live Monitoring
            Main->>DF: stream_data()
            DF-->>Main: New Candle
            
            Main->>SE: check_for_trade_action(current_price)
            SE-->>Main: Action (HOLD/SELL)
            
            alt Action == SELL
                Main->>EE: execute_sell(token, amount, price)
                EE->>PM: record_sell()
                PM-->>EE: Success
                Main->>WS: Broadcast SELL Event
            end
            
            Main->>WS: Broadcast UPDATE (Price, Portfolio)
        end
        
        Main->>WS: Broadcast Trade Finished
    else No Signal
        Main->>WS: Broadcast Trade Skipped
    end
```
