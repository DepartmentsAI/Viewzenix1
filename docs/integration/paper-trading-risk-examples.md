# Paper Trading and Risk Management Integration

This document provides examples and usage patterns for integrating the Paper Trading Adapter with the Risk Management System. This integration enables realistic testing of risk management features in a simulated environment without using real money.

## Overview

The Paper Trading Adapter has been enhanced to fully integrate with the Risk Management System, enabling:

1. Risk-aware order execution
2. Stop-loss/take-profit order support
3. Position tracking for risk limits
4. Realistic market simulation for testing risk events
5. Comprehensive logging and event tracking

## Integration Architecture

The integration follows this architecture:

```
┌───────────────────────┐      ┌───────────────────────┐
│                       │      │                       │
│   Paper Trading       │◄────►│   Risk Management     │
│   Adapter             │      │   System              │
│                       │      │                       │
└───────────────────────┘      └───────────────────────┘
        ▲                              ▲
        │                              │
        │                              │
        ▼                              ▼
┌───────────────────────┐      ┌───────────────────────┐
│                       │      │                       │
│   Trading Platform    │◄────►│   Cleanup Service     │
│   (Order Execution)   │      │   (Orphaned Orders)   │
│                       │      │                       │
└───────────────────────┘      └───────────────────────┘
```

## Key Features

### 1. Stop-Loss and Take-Profit Support

The Paper Trading Adapter fully supports bracket orders with stop-loss and take-profit legs:

```python
# Example: Creating a bracket order with SL/TP
adapter = PaperTradingAdapter(initial_balance=100000.0)

# Buy AAPL with stop-loss and take-profit
order = adapter.place_bracket_order(
    symbol="AAPL",
    qty=10,
    side="buy",
    stop_loss_price=150.0,  # Sell if price drops to 150
    take_profit_price=180.0  # Sell if price rises to 180
)

# Order IDs for tracking
main_order_id = order["client_order_id"]
sl_order_id = order["stop_loss_order_id"]
tp_order_id = order["take_profit_order_id"]
```

### 2. Risk-Aware Price Simulation

The Paper Trading Adapter can simulate extreme price movements to test risk management features:

```python
# Configure price simulation for risk testing
adapter.set_price_simulation_parameters(
    volatility=0.01,               # 1% base volatility
    extreme_volatility_chance=0.05, # 5% chance of extreme move
    extreme_volatility_factor=5    # 5x volatility during extreme moves
)

# Enable/disable risk simulation features
adapter.toggle_risk_simulation(enabled=True)
```

### 3. Risk Event Tracking

The integration records and tracks risk events for analysis:

```python
# After running a simulation, get risk events
risk_events = adapter.get_risk_events()

# Example events include:
# - stop_loss_triggered
# - take_profit_triggered
# - order_fill
# - position_limit_reached
# - drawdown_limit_reached
```

### 4. Integration with Risk Manager

The adapter can be initialized with a risk manager instance:

```python
from src.backend.services.risk_manager import RiskManager

# Create risk manager with desired parameters
risk_manager = RiskManager()
risk_manager.update_risk_parameters({
    'stop_loss_percent': 0.05,  # 5% stop loss
    'max_daily_drawdown_percent': 0.10  # 10% max daily drawdown
})

# Initialize adapter with risk manager
adapter = PaperTradingAdapter(
    initial_balance=100000.0,
    risk_manager=risk_manager
)
```

## Usage Examples

### Basic Integration Example

```python
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.backend.services.risk_manager import RiskManager

# Setup
risk_manager = RiskManager()
adapter = PaperTradingAdapter(
    initial_balance=100000.0,
    risk_manager=risk_manager
)

# Update risk parameters
risk_manager.update_risk_parameters({
    'stop_loss_percent': 0.02,  # 2% stop loss
    'take_profit_percent': 0.05,  # 5% take profit
    'max_position_size_percent': 0.10,  # Max 10% portfolio in one position
    'max_daily_drawdown_percent': 0.05,  # Max 5% daily drawdown
})

# Create positions with automatic SL/TP based on risk parameters
symbols = ["AAPL", "MSFT", "AMZN", "GOOGL"]
for symbol in symbols:
    current_price = float(adapter._get_current_price(symbol))
    
    # Calculate position size based on risk limits
    account = adapter.get_account_info()
    equity = float(account["equity"])
    max_position_value = equity * risk_manager.risk_params['max_position_size_percent']
    qty = max_position_value / current_price
    
    # Apply stop loss and take profit based on risk parameters
    sl_percent = risk_manager.risk_params['stop_loss_percent']
    tp_percent = risk_manager.risk_params['take_profit_percent']
    
    stop_loss = current_price * (1 - sl_percent)
    take_profit = current_price * (1 + tp_percent)
    
    # Place bracket order
    adapter.place_bracket_order(
        symbol=symbol,
        qty=qty,
        side="buy",
        stop_loss_price=stop_loss,
        take_profit_price=take_profit
    )

# Simulate market for testing
adapter.set_price_simulation_parameters(
    volatility=0.01,
    extreme_volatility_chance=0.05
)

# After simulation, analyze risk events
events = adapter.get_risk_events()
for event in events:
    print(f"Event: {event['type']}, Time: {event['timestamp']}")
    
# Check risk metrics
metrics = risk_manager.get_risk_metrics()
print(f"Max Drawdown: {metrics['max_drawdown_percent']*100:.2f}%")
```

### Testing Portfolio-Level Risk Management

```python
# Example: Testing global portfolio stop-loss
risk_manager = RiskManager()
adapter = PaperTradingAdapter(risk_manager=risk_manager)

# Set global drawdown limit
risk_manager.update_risk_parameters({
    'max_daily_drawdown_percent': 0.05  # 5% max drawdown
})

# Create multiple positions
for symbol in ["AAPL", "MSFT", "TSLA"]:
    adapter.place_market_order(symbol, 10, "buy")

# Simulate extreme market crash
adapter.set_price_simulation_parameters(
    volatility=0.02,
    extreme_volatility_chance=0.80,  # High chance of extreme move
    extreme_volatility_factor=3
)

# Check if positions were automatically closed due to drawdown limit
time.sleep(60)  # Let simulation run
account = adapter.get_account_info()
positions = adapter.get_all_positions()

print(f"Remaining positions: {len(positions)}")
print(f"Drawdown: {risk_manager.get_risk_metrics()['current_drawdown_percent']*100:.2f}%")
```

## Running the Simulation Example

For a complete working example, run the provided simulation script:

```bash
# Basic usage
python src/integration/examples/paper_trading_risk_test.py

# Customize parameters
python src/integration/examples/paper_trading_risk_test.py \
    --duration 300 \
    --balance 100000 \
    --volatility 0.01 \
    --extreme-chance 0.05 \
    --extreme-factor 5 \
    --interval 5
```

This script creates a portfolio of positions with stop-loss and take-profit orders, then simulates market activity to test how the risk management system responds.

## Troubleshooting

### Common Issues

1. **SL/TP orders not triggering:**
   - Check that `RISK_SIMULATION_ENABLED` is set to `True`
   - Ensure volatility settings are high enough to hit trigger prices
   - Verify that SL/TP prices are set properly relative to entry price

2. **Risk Manager not receiving updates:**
   - Ensure the risk manager is properly passed to the adapter
   - Check that the risk manager's daily tracking is initialized

3. **Orphaned orders:**
   - If testing long-running simulations, use the cleanup service:
   ```python
   orphaned_orders = risk_manager.cleanup_orphaned_orders()
   ```

### Debugging Tips

- Enable detailed logging with a custom logger:
  ```python
  logger = IntegrationLogger(level="DEBUG")
  adapter = PaperTradingAdapter(logger=logger)
  ```
  
- Monitor risk events in real-time:
  ```python
  last_event_count = 0
  while True:
      events = adapter.get_risk_events()
      if len(events) > last_event_count:
          for i in range(last_event_count, len(events)):
              print(f"New event: {events[i]['type']}")
          last_event_count = len(events)
      time.sleep(1)
  ```
  
- Test extreme scenarios with 100% volatility chance:
  ```python
  adapter.set_price_simulation_parameters(
      volatility=0.05,
      extreme_volatility_chance=1.0,  # 100% chance of extreme moves
      extreme_volatility_factor=10     # 10x volatility multiplier
  )
  ```

## Performance Considerations

When running simulations with many positions or high-frequency price updates:

- Use a dedicated thread for stop-loss/take-profit monitoring
- Adjust the `SL_TP_TRIGGER_CHECK_INTERVAL` for more/less frequent checks
- For large-scale simulations, consider using a separate process 