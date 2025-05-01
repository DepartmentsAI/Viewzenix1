# Order Execution Engine

The Order Execution Engine is responsible for processing trade requests from TradingView alerts and executing orders through the appropriate broker adapter.

## Features

- Processes webhook data from TradingView alerts
- Determines trade type (long entry, long exit, short entry, short exit)
- Calculates order quantity based on alert data or account equity percentage
- Executes orders through the configured broker adapter (Alpaca by default)
- Handles exit orders by closing positions
- Implements retry logic for failed order executions
- Comprehensive error handling and logging

## Usage

### Basic Usage

```python
from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.alpaca_adapter import AlpacaAdapter

# Create an OrderEngine with the default AlpacaAdapter (paper trading)
order_engine = OrderEngine()

# Or create with a custom broker adapter
broker_adapter = AlpacaAdapter(use_paper=False)  # Use live trading
order_engine = OrderEngine(broker_adapter=broker_adapter)

# Process webhook data
webhook_data = {
    'symbol': 'BTCUSD',
    'strategy_order_id': 'long',
    'strategy_order_action': 'buy',
    'strategy_order_contracts': 0.1,
    'strategy_order_price': 50000,
    'time': 1620000000000
}

result = order_engine.process_webhook_data(webhook_data)
print(result)
```

### Integration with Flask Webhook API

The OrderEngine is designed to be used with the Flask Webhook API. The webhook endpoint receives TradingView alerts, validates them against a JSON schema, and passes them to the OrderEngine for processing.

```python
# In webhook.py
from flask import Blueprint, request, jsonify
from jsonschema import validate, ValidationError
from src.backend.services.order_engine import OrderEngine

webhook_bp = Blueprint('webhook', __name__)
order_engine = OrderEngine()

@webhook_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    payload = request.get_json()
    
    # Validate payload against schema...
    
    # Process the webhook using the OrderEngine
    result = order_engine.process_webhook_data(payload)
    
    # Return the result
    if result.get('status') == 'success':
        return jsonify(result), 200
    elif result.get('status') == 'warning':
        return jsonify(result), 200
    else:
        return jsonify(result), 400
```

## Trade Type Mapping

| strategy_order_id | strategy_order_action | Trade Type    |
|-------------------|------------------------|---------------|
| long              | buy                    | Long Entry    |
| long              | sell                   | Long Exit     |
| sell              | sell                   | Short Entry   |
| sell              | buy                    | Short Exit    |

## Order Sizing

1. If `strategy_order_contracts` is provided in the webhook data, it is used as the order quantity.
2. Otherwise, the order quantity is calculated as a percentage of the account equity (default: 2%).

## Configuration

The OrderEngine can be configured with the following parameters:

- `broker_adapter`: The broker adapter to use for executing orders. If not provided, `AlpacaAdapter` with paper trading is used by default.
- `max_retries`: Maximum number of retries for failed order executions (default: 3).
- `retry_delay`: Delay between retries in seconds (default: 2). 