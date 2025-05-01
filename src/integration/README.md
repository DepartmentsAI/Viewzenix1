# Integration Components

This directory contains the integration components for the Trading Webhook Platform, responsible for connecting the system with external services and brokers.

## Structure

- `adapters/`: Contains adapter implementations for various brokers
  - `broker_adapter.py`: Base interface for all broker adapters
  - `alpaca_adapter.py`: Alpaca Markets API implementation
- `utils/`: Utility classes for integration support
  - `api_key_manager.py`: Secure management of API keys
  - `logger.py`: Structured logging for integration operations
- `services/`: Integration service implementations
- `tests/`: Unit tests for integration components

## Adapters

### BrokerAdapter

The `BrokerAdapter` is an abstract base class that defines the interface for all broker-specific adapters. It requires implementations for:

- Authentication with broker APIs
- Placing various order types (market, limit, stop, bracket)
- Managing positions and account information
- Handling broker-specific responses and errors

### AlpacaAdapter

The `AlpacaAdapter` is a concrete implementation of the `BrokerAdapter` interface for Alpaca Markets. Features include:

- Paper and live trading modes
- Support for all required order types
- Comprehensive error handling and retry mechanism
- Extensive logging of all API interactions
- Symbol format normalization (handling different formats like BTC/USD → BTCUSD)

## Configuration

The adapters use environment variables for configuration:

- `ALPACA_PAPER_API_KEY`: API key for Alpaca paper trading
- `ALPACA_PAPER_API_SECRET`: API secret for Alpaca paper trading
- `ALPACA_LIVE_API_KEY`: API key for Alpaca live trading
- `ALPACA_LIVE_API_SECRET`: API secret for Alpaca live trading

## Usage Example

```python
from src.integration.adapters.alpaca_adapter import AlpacaAdapter

# Initialize the adapter (defaults to paper trading)
adapter = AlpacaAdapter(use_paper=True)

# Check authentication
if adapter.authenticated:
    # Place a market order
    result = adapter.place_market_order(
        symbol="AAPL", 
        qty=10, 
        side="buy"
    )
    
    if result["success"]:
        print(f"Order placed! Order ID: {result['order_id']}")
    else:
        print(f"Order failed: {result['error']}")
```

## Logging

The integration components use structured logging to capture all API interactions:

- `logs.jsonl`: Machine-readable logs in JSON format
- `activity.log`: Human-readable logs with timestamps and levels

## Tests

Run the integration tests with:

```bash
python -m unittest discover -s src/integration/tests
```

## Future Broker Support

To add support for a new broker:

1. Create a new adapter class that implements the `BrokerAdapter` interface
2. Implement all required methods for the specific broker's API
3. Add appropriate tests in the `tests/` directory
4. Update the documentation in this README 