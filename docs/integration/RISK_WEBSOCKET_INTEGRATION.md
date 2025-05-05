# Risk Management and WebSocket Market Data Integration

## Overview

This document describes the integration between the real-time market data WebSocket stream, paper trading functionality, and the risk management system in the Viewzenix1 trading platform. The integration enables automated risk management based on real-time price movements and position monitoring.

## Architecture

The integration connects three key components:

1. **WebSocket Market Data Streams** (AlpacaStreamAdapter)
   - Provides real-time market data including trades, quotes, and bars
   - Connects to Alpaca's streaming API
   - Delivers continual price updates to the system

2. **Risk Management System** (RiskManager)
   - Enforces position limits, max order size, and drawdown controls
   - Handles stop-loss and take-profit logic
   - Processes real-time market data to trigger risk actions

3. **Paper Trading System** (PaperTradingAdapter)
   - Simulates order execution in a risk-free environment
   - Maintains position and portfolio state
   - Executes risk-triggered orders (stop-loss/take-profit)

![Architecture Diagram](../../docs/architecture/images/risk_websocket_integration.png)

## Data Flow

1. **Market Data Ingestion**:
   - WebSocket connection established to Alpaca streaming API
   - System subscribes to specific symbols for trade/quote updates
   - Real-time prices flow into the system

2. **Risk Processing Pipeline**:
   - Market data received via WebSocket callbacks
   - Price updates passed to RiskManager for position evaluation
   - Risk rules applied (stop-loss, take-profit thresholds)
   - Risk actions generated if thresholds breached

3. **Risk Action Execution**:
   - Risk actions (stop-loss triggers, etc.) sent to PaperTradingAdapter
   - PaperTradingAdapter executes corresponding orders
   - Position state updated accordingly

## Implementation Details

### AlpacaStreamAdapter Enhancements

The `AlpacaStreamAdapter` has been enhanced to support direct integration with the risk management system:

```python
# Register callback for trade events with risk management
@stream_adapter.on_trade
def handle_trade(trade_data):
    symbol = trade_data.get('S')
    price = float(trade_data.get('p'))
    
    # Process through risk management
    risk_actions = risk_manager.process_market_data(symbol, price)
    
    # Handle any risk actions (e.g., stop-loss execution)
    for action in risk_actions:
        handle_risk_action(action)
```

### RiskManager Market Data Integration

The RiskManager has been extended with a `process_market_data` method to handle real-time price updates:

```python
def process_market_data(self, symbol, price, timestamp=None):
    """
    Process market data update and apply risk rules
    
    Args:
        symbol: The stock symbol
        price: Current market price
        timestamp: Optional timestamp of the market data
        
    Returns:
        List of risk actions triggered by this update
    """
    # Find positions for this symbol
    position = self._get_position(symbol)
    if not position:
        return []  # No position, no actions needed
    
    actions = []
    
    # Check for stop loss trigger
    if (position['side'] == 'long' and 
        price <= self._calculate_stop_price(position)):
        actions.append({
            'action': 'stop_loss',
            'symbol': symbol,
            'qty': position['qty'],
            'reason': 'Price below stop-loss threshold'
        })
    
    # Check for take profit trigger
    elif (position['side'] == 'long' and 
          price >= self._calculate_take_profit(position)):
        actions.append({
            'action': 'take_profit',
            'symbol': symbol,
            'qty': position['qty'],
            'reason': 'Price reached take-profit target'
        })
    
    return actions
```

### PaperTradingAdapter Integration

The PaperTradingAdapter has been integrated with the risk management system to handle risk-triggered orders:

```python
def handle_risk_action(self, action):
    """Handle risk-triggered actions"""
    action_type = action.get('action')
    symbol = action.get('symbol')
    qty = action.get('qty')
    
    if action_type == 'stop_loss':
        # Create and submit stop-loss order
        order = {
            'symbol': symbol,
            'qty': qty,
            'side': 'sell',
            'type': 'market',
            'time_in_force': 'day'
        }
        self.submit_order(order)
```

## Getting Started

### Prerequisites

- Python 3.8+
- Access to Alpaca API credentials
- Required dependencies: `websocket-client`, `requests`

### Basic Usage

1. **Initialize the components**:

```python
from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.backend.services.risk_manager import RiskManager

# Initialize components
stream_adapter = AlpacaStreamAdapter(paper_trading=True)
paper_adapter = PaperTradingAdapter(paper_trading=True)
risk_manager = RiskManager()
```

2. **Set up WebSocket callbacks**:

```python
@stream_adapter.on_trade
def handle_trade(trade_data):
    symbol = trade_data.get('S')
    price = float(trade_data.get('p'))
    
    # Process through risk management
    risk_actions = risk_manager.process_market_data(symbol, price)
    
    # Handle risk actions
    for action in risk_actions:
        if action.get('action') == 'stop_loss':
            # Create an exit order
            order = {
                'symbol': action.get('symbol'),
                'qty': action.get('qty'),
                'side': 'sell',
                'type': 'market',
                'time_in_force': 'day'
            }
            paper_adapter.submit_order(order)
```

3. **Connect and subscribe to market data**:

```python
# Connect to the streaming API
stream_adapter.connect()

# Subscribe to trade updates for specific symbols
symbols = ['AAPL', 'MSFT', 'GOOGL']
stream_adapter.subscribe_to_trades(symbols)
```

4. **Create paper trading positions**:

```python
# Create a paper trading position
order = {
    'symbol': 'AAPL',
    'qty': 10,
    'side': 'buy',
    'type': 'market',
    'time_in_force': 'day'
}
paper_adapter.submit_order(order)
```

## Example Implementation

For a complete implementation example, see:

- `src/integration/examples/paper_trading_risk_integration.py`

This example demonstrates:
- Connecting to the WebSocket stream for real-time market data
- Setting up a paper trading environment with test positions
- Configuring risk management rules for stop-loss/take-profit
- Handling risk actions based on price movements
- Monitoring positions and performance

To run the example:

```bash
python src/integration/examples/paper_trading_risk_integration.py --symbols AAPL,MSFT,GOOGL --duration 300
```

## Risk Management Features

The integrated risk management system provides several critical features:

### Pre-Trade Risk Checks

Before order execution, the system checks:
- Maximum position size limits
- Maximum order value limits
- Account balance and buying power
- Daily risk limits

### Real-Time Position Monitoring

Once positions are open, the system:
- Monitors real-time price movements via WebSocket
- Calculates current P&L per position
- Applies stop-loss and take-profit rules
- Triggers exit orders when thresholds are breached

### Automated Risk Actions

The integration enables automated risk responses:
- Stop-loss order execution
- Take-profit order execution
- Position liquidation based on drawdown limits
- Circuit breakers during market volatility

## Testing and Validation

### Validation Utilities

The integration includes comprehensive validation utilities:

1. **Risk Market Data Validator** (`src/integration/utils/risk_market_data_validator.py`):
   - Validates WebSocket connection stability
   - Tests market data flow to risk management
   - Verifies risk rule application to real-time data
   - Confirms proper generation of risk actions

2. **Integration Validation Tool** (`src/integration/utils/validate_integration.py`):
   - Complete validation framework for the entire integration
   - Runs unit tests for all integration components
   - Checks connectivity to external APIs
   - Validates end-to-end integration from market data to risk actions

3. **Unit Tests**:
   - `tests/unit/integration/test_alpaca_stream_adapter.py`: Tests WebSocket connectivity and data handling
   - `tests/unit/integration/test_paper_trading_risk_integration.py`: Tests integration between paper trading and risk management

### Running Validation Tests

To run the validation utilities:

```bash
# Run the comprehensive integration validator
python src/integration/utils/validate_integration.py --full-test

# Run quick unit tests only
python src/integration/utils/validate_integration.py --quick-test

# Run only risk management validation
python src/integration/utils/validate_integration.py --risk-only --duration 60
```

To run the risk market data validator directly:

```python
from src.integration.utils.risk_market_data_validator import RiskMarketDataValidator

validator = RiskMarketDataValidator(use_paper=True, use_mock_risk=True)
results = validator.run_validation(duration_seconds=60)
print(f"Validation results: {results['success']}")
```

### Test Coverage

The validation suite covers:

- WebSocket connection stability and reconnection logic
- Market data parsing and delivery
- Pre-trade risk checks (position limits, order value limits)
- Real-time position monitoring
- Stop-loss and take-profit triggers
- Order execution from risk actions
- Error handling and edge cases

## Troubleshooting

### WebSocket Connection Issues

If the WebSocket connection fails:
1. Verify API credentials are correct
2. Check network connectivity to Alpaca API
3. Ensure `websocket-client` package is installed
4. Verify correct WebSocket URL for paper/live environment

### Risk Management Integration Issues

If risk actions aren't triggering properly:
1. Verify market data is flowing through callbacks
2. Check position data in RiskManager is correct
3. Verify risk thresholds are properly configured
4. Enable debug logging for detailed diagnostics

### Using the Validation Utility for Diagnostics

The validation utility can help diagnose issues:

```bash
# Run the validation utility with detailed output
python src/integration/utils/validate_integration.py --full-test
```

If issues are found, examine the output for specific error messages and failed validation steps. The utility will:

1. Identify connection problems
2. Test API credentials
3. Validate data flow
4. Check risk rule application
5. Test end-to-end integration

## Conclusion

The integration between WebSocket market data, risk management, and paper trading provides a comprehensive system for automated trading with risk controls. This integration enables:

- Real-time risk monitoring and management
- Automated protection against adverse market movements
- Systematic execution of risk-mitigation strategies
- Paper trading validation before live deployment

See the `paper_trading_risk_integration.py` example script for a complete demonstration of how market data from WebSockets integrates with the risk management system in a paper trading environment.

To run the example:
```bash
python src/integration/examples/paper_trading_risk_integration.py --duration 300
```

## Related Documentation

- [Paper Trading Integration](./paper_trading.md)
- [Alpaca WebSocket Integration](./ALPACA_WEBSOCKET_INTEGRATION.md)
- [Risk Management Architecture](../architecture/risk_management.md) 