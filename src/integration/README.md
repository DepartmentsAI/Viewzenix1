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

# Integration Service Configuration Guide

This document outlines how to configure broker integrations for the Viewzenix1 platform.

## Broker API Credentials

### Configuration Files

The system uses a multi-layered configuration approach for maximum flexibility:

1. **Environment Variables** (highest priority)
   - Set directly in the environment
   - Most secure for production deployments

2. **.env File** (second priority)
   - Create a `.env` file in the `src/integration` directory
   - Copy from `config.sample.env` and add your actual credentials
   - Good for local development

3. **Sample Config** (third priority)
   - `config.sample.env` provides template values
   - Used as fallback for non-critical environments

4. **Default Values** (lowest priority)
   - Hardcoded placeholder values
   - Will not work for actual API calls
   - Used only for initialization and testing

### Alpaca Trading API Configuration

To configure Alpaca Trading API credentials:

```
# Add to .env file or environment variables
ALPACA_PAPER_API_KEY=your_paper_api_key
ALPACA_PAPER_API_SECRET=your_paper_api_secret
ALPACA_PAPER_TRADING=true
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# For live trading (optional)
ALPACA_LIVE_API_KEY=your_live_api_key
ALPACA_LIVE_API_SECRET=your_live_api_secret
```

## Configuration Utility

The `env_config.py` utility provides a unified way to access configuration:

```python
from src.integration.utils.env_config import get_broker_config, get_config_value

# Get all configuration for a broker
alpaca_config = get_broker_config('alpaca')

# Get a specific configuration value
api_key = get_config_value('alpaca.paper_api_key')
```

## Security Considerations

- Never commit real API credentials to version control
- Always use the `.env` file or environment variables for real credentials
- The sample config contains dummy values that won't work with real APIs
- For production, use secure environment variable management

## Testing

The configuration system supports testing by allowing:

- Mock configuration during tests
- Fallback to sample values for test environments
- Clear logging of configuration sources for debugging 