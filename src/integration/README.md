# Viewzenix1 Integration Tools

This directory contains tools, adapters, examples, and utilities for integrating various components of the Viewzenix1 trading system.

## Key Components

### Adapters

- **AlpacaStreamAdapter** (`adapters/alpaca_stream_adapter.py`) - WebSocket connection for real-time market data
- **PaperTradingAdapter** (`adapters/paper_trading_adapter.py`) - Risk-free simulation of trading operations
- **AlpacaAdapter** (`adapters/alpaca_adapter.py`) - REST API interaction with Alpaca for account/order management
- **BrokerAdapter** (`adapters/broker_adapter.py`) - Abstract base class for broker interactions

### Utils

- **RiskMarketDataValidator** (`utils/risk_market_data_validator.py`) - Validates the integration between market data and risk management
- **ValidateIntegration** (`utils/validate_integration.py`) - Comprehensive validation framework for all integration components
- **VerifyBrokerConfig** (`utils/verify_broker_config.py`) - Verifies broker API configuration and credentials
- **Logger** (`utils/logger.py`) - Custom logging for integration components
- **ApiKeyManager** (`utils/api_key_manager.py`) - Secure management of API credentials
- **EnvConfig** (`utils/env_config.py`) - Environment configuration management

### Examples

- **PaperTradingRiskIntegration** (`examples/paper_trading_risk_integration.py`) - Example demonstrating the integration between WebSocket market data, risk management, and paper trading
- **WebsocketExample** (`examples/websocket_example.py`) - Simple example of using the WebSocket adapters
- **PaperTradingExample** (`examples/paper_trading_example.py`) - Example of paper trading functionality

## Getting Started

### Prerequisites

- Python 3.8+
- API credentials for Alpaca (set as environment variables)
- Required Python packages (see requirements.txt)

### Environment Setup

Set the following environment variables:

```
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_API_BASE_URL=https://paper-api.alpaca.markets
ALPACA_WS_URL=wss://stream.data.alpaca.markets/v2/iex
```

### Validation Tools

To validate your integration setup:

```bash
# Verify broker configuration
python src/integration/utils/verify_broker_config.py

# Run the risk market data validator
python src/integration/utils/risk_market_data_validator.py

# Run the comprehensive integration validator
python src/integration/utils/validate_integration.py --full-test
```

### Running Examples

```bash
# Run the paper trading and risk management example
python src/integration/examples/paper_trading_risk_integration.py --symbols AAPL,MSFT,GOOGL --duration 300

# Run the WebSocket example
python src/integration/examples/websocket_example.py
```

## Testing

Unit tests are located in `tests/unit/integration/`:

```bash
# Run all integration tests
python -m unittest discover -s tests/unit/integration

# Run the validation utility with unit tests only
python src/integration/utils/validate_integration.py --quick-test
```

## Documentation

Detailed documentation can be found in:

- [Risk WebSocket Integration](../../docs/integration/RISK_WEBSOCKET_INTEGRATION.md)
- [Paper Trading](../../docs/integration/paper_trading.md)
- [Alpaca WebSocket Integration](../../docs/integration/ALPACA_WEBSOCKET_INTEGRATION.md)

## Troubleshooting

If you encounter issues with the integration:

1. Verify your broker configuration:
   ```bash
   python src/integration/utils/verify_broker_config.py
   ```

2. Check connectivity to WebSocket streams:
   ```bash
   python src/integration/utils/validate_integration.py --connectivity
   ```

3. Run the comprehensive validation:
   ```bash
   python src/integration/utils/validate_integration.py --full-test
   ```

4. Consult the error logs and documentation for further guidance. 