# Alpaca WebSocket Integration Guide

## Overview

This document provides information on the WebSocket integration with Alpaca API, as implemented in accordance with decision DEC-2025-05-09-04. The integration enables real-time market data streaming and order updates for the Viewzenix1 platform.

## Benefits

- **Real-time Data**: Receive market data updates in real-time without polling
- **Reduced API Calls**: Significantly reduces the number of REST API calls needed
- **Lower Latency**: Minimizes the delay between market events and their processing
- **Order Status Updates**: Immediate notification of order status changes
- **Trade Execution Reports**: Real-time trade execution confirmations

## Implementation Details

The WebSocket integration is implemented in the following components:

1. **AlpacaStreamAdapter**: Main adapter class that handles WebSocket connections
   - File: `/workspace/Viewzenix1/src/integration/adapters/alpaca_stream_adapter.py`
   - Handles connection establishment, authentication, and message processing
   - PR #120 adds the websocket-client dependency required for this feature

2. **WebSocket Example**: Demonstration code showing WebSocket usage
   - File: `/workspace/Viewzenix1/src/integration/examples/websocket_example.py`
   - Provides example implementation for reference

## Connection Types

The Alpaca API provides two distinct WebSocket endpoints:

1. **Market Data Stream**
   - Real-time quotes, trades, and bars
   - Configurable subscriptions by symbol
   - Available for both paper and live trading

2. **Account Updates Stream**
   - Real-time order status updates
   - Trade confirmations
   - Account value changes

## Usage

### Basic Connection Setup

```python
from integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter

# Initialize the adapter with your credentials
stream_adapter = AlpacaStreamAdapter(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    paper_trading=True  # Set to False for live trading
)

# Connect to the WebSocket streams
stream_adapter.connect()
```

### Subscribing to Market Data

```python
# Subscribe to trade updates for specific symbols
stream_adapter.subscribe_to_trades(["AAPL", "MSFT", "GOOGL"])

# Subscribe to quote updates
stream_adapter.subscribe_to_quotes(["AAPL", "MSFT", "GOOGL"])

# Subscribe to minute bars
stream_adapter.subscribe_to_bars(["AAPL", "MSFT", "GOOGL"], timeframe="1Min")
```

### Handling WebSocket Events

```python
# Register callback for trade events
@stream_adapter.on_trade
def handle_trade(trade_data):
    print(f"Trade received: {trade_data}")
    # Process trade data

# Register callback for quote updates
@stream_adapter.on_quote
def handle_quote(quote_data):
    print(f"Quote update: {quote_data}")
    # Process quote data

# Register callback for order status updates
@stream_adapter.on_order_update
def handle_order_update(order_data):
    print(f"Order update: {order_data}")
    # Update order status in the system
```

## Error Handling

The WebSocket connection includes automatic reconnection logic:

- Automatic reconnection on network errors
- Exponential backoff for repeated connection failures
- Resubscription to previously subscribed channels after reconnection
- Heartbeat monitoring to detect dead connections

## Dashboard Integration

The WebSocket integration can be leveraged by the frontend to provide real-time updates to the dashboard:

- Real-time order status updates
- Live profit/loss tracking
- Instant trade notifications
- Market data visualization

## Testing

A comprehensive test suite is available for verifying WebSocket functionality:

- Connection establishment and authentication tests
- Message handling tests
- Reconnection logic tests
- Error handling tests

## Environment Configuration

Required environment variables:

```
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_API_BASE_URL=https://paper-api.alpaca.markets  # or https://api.alpaca.markets for live
ALPACA_WS_URL=wss://paper-api.alpaca.markets/stream
```

## References

- [Alpaca API Documentation](https://alpaca.markets/docs/api-documentation/api-v2/market-data/streaming/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [Decision Log Entry](../communication/decision_log.md#DEC-2025-05-09-04)
- [Related PR](https://github.com/DepartmentsAI/Viewzenix1/pull/120) 