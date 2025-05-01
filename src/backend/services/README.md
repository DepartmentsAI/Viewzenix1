# Backend Services

This directory contains the core service modules for the Viewzenix1 trading platform backend.

## OrderEngine

The OrderEngine service (`order_engine.py`) is responsible for processing trading webhook data, validating orders, and routing them to the appropriate broker adapter. It provides:

- Webhook data processing and validation
- Order type detection (market, limit)
- Order execution via broker adapters
- Error handling and retry logic
- Transaction logging

### Usage

```python
from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.alpaca_adapter import AlpacaAdapter

# Create an OrderEngine with a specific broker adapter
adapter = AlpacaAdapter(use_paper=True)
engine = OrderEngine(broker_adapter=adapter)

# Process a webhook payload
result = engine.process_webhook_data({
    "symbol": "BTCUSD",
    "strategy_order_id": "long",
    "strategy_order_action": "buy",
    "strategy_order_price": 50000,
    "strategy_order_contracts": 0.1,
    "time": 1620000000000
})

print(result)
# {
#   "status": "success",
#   "order_id": "order_123",
#   "message": "Order executed successfully"
# }
```

## RiskManager

The RiskManager service (`risk_manager.py`) implements risk management features to protect user funds during automated trading. It integrates with the OrderEngine to provide:

- Stop-loss and take-profit order management
- Portfolio protection (position limits, drawdown limits)
- Position sizing rules
- Orphaned order cleanup

### Usage

```python
from src.backend.services.risk_manager import RiskManager
from src.backend.services.order_engine import OrderEngine

# Create a RiskManager (will use OrderEngine internally)
risk_manager = RiskManager()

# Or create with specific engines/adapters
engine = OrderEngine()
risk_manager = RiskManager(order_engine=engine)

# Process an order with risk management
result = risk_manager.process_order_with_risk_management({
    "symbol": "BTCUSD",
    "strategy_order_id": "long",
    "strategy_order_action": "buy",
    "strategy_order_price": 50000,
    "strategy_order_contracts": 0.1,
    "time": 1620000000000,
    "stop_loss": {
        "percent": 0.02  # 2% stop loss
    },
    "take_profit": {
        "percent": 0.05  # 5% take profit
    }
})

# Get current risk metrics
metrics = risk_manager.get_risk_metrics()

# Update risk parameters
new_params = {
    "stop_loss_percent": 0.03,
    "max_daily_drawdown_percent": 0.08
}
updated_params = risk_manager.update_risk_parameters(new_params)

# Clean up orphaned orders
cleanup_result = risk_manager.cleanup_orphaned_orders()
```

### Risk Parameters

The RiskManager is configurable through the following parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `stop_loss_percent` | Default percentage-based stop loss | 2% (0.02) |
| `take_profit_percent` | Default percentage-based take profit | 5% (0.05) |
| `max_position_size_percent` | Maximum position size as percentage of equity | 5% (0.05) |
| `max_daily_drawdown_percent` | Maximum allowed daily drawdown | 5% (0.05) |
| `max_open_positions` | Maximum number of open positions | 10 |
| `orphaned_order_age_hours` | Hours after which an order is considered orphaned | 24 |

For more details on the risk management implementation, see the architecture documentation at `/docs/architecture/risk_management.md`.

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