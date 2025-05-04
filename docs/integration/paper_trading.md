# Paper Trading Adapter

The Paper Trading Adapter provides a simulated trading environment for testing the Trading Webhook Platform without using real money or connecting to external brokers. This is especially useful for testing risk management features, order execution flows, and algorithmic trading strategies.

## Features

- **Full Broker Interface Implementation**: Implements all methods from the `BrokerAdapter` interface
- **Realistic Market Simulation**: Simulates market price movements with configurable volatility
- **Complete Order Types**: Supports market, limit, stop, and bracket orders
- **Position Tracking**: Maintains positions, calculates P&L, and updates account equity
- **Fees Simulation**: Includes realistic fee simulation (0.1% per trade)
- **Stop-Loss/Take-Profit**: Fully simulates bracket orders with TP/SL legs
- **Account Management**: Tracks cash, equity, portfolio value, and buying power
- **Risk Management Integration**: Integrates with the Risk Management service for position sizing and risk control

## Usage

### Basic Usage

```python
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.integration.utils.logger import IntegrationLogger

# Create logger
logger = IntegrationLogger()

# Initialize adapter with $100,000 starting balance
adapter = PaperTradingAdapter(initial_balance=100000.0, logger=logger)

# Place a market order
market_order = adapter.place_market_order("AAPL", 10, "buy")

# Place a limit order
limit_order = adapter.place_limit_order("MSFT", 10, "buy", 250.0)

# Place a bracket order with TP/SL
bracket_order = adapter.place_bracket_order(
    symbol="AMZN",
    qty=5,
    side="buy",
    take_profit_price=3500.0,
    stop_loss_price=3300.0
)

# Get account info
account = adapter.get_account_info()
print(f"Cash: ${float(account['cash']):.2f}")
print(f"Equity: ${float(account['equity']):.2f}")

# Get positions
positions = adapter.get_all_positions()
for position in positions:
    print(f"Position: {position['qty']} {position['symbol']} ({position['side']})")
```

### Risk Management Integration

The Paper Trading Adapter is now fully integrated with the Risk Management service for comprehensive risk control:

```python
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.backend.services.risk_manager import RiskManager
from src.backend.services.order_engine import OrderEngine

# Initialize the adapter
adapter = PaperTradingAdapter(initial_balance=100000.0)

# Initialize the order engine with the adapter
order_engine = OrderEngine(broker_adapter=adapter)

# Initialize the risk manager with the adapter and order engine
risk_manager = RiskManager(
    broker_adapter=adapter,
    order_engine=order_engine,
    max_position_size=5000.0,  # $5000 max position size
    max_drawdown_pct=0.05  # 5% max drawdown
)

# Process a trade signal through risk management
trade_signal = {
    "symbol": "AAPL",
    "side": "buy",
    "qty": 20,
    "type": "market",
    "signal_source": "strategy_1",
    "risk_profile": "moderate"
}

# Risk manager will apply position sizing rules before execution
result = risk_manager.process_order_with_risk_management(trade_signal)
print(f"Order result: {result['status']} - {result['message']}")

# Risk manager can add stop loss and take profit based on risk parameters
parent_order_id = result.get('order_id')
if parent_order_id:
    sl_tp_result = risk_manager.add_stop_loss_take_profit(
        symbol=trade_signal["symbol"],
        entry_price=165.0,  # Current price
        parent_order_id=parent_order_id,
        risk_reward_ratio=2.0  # 2:1 reward-to-risk ratio
    )
    print(f"SL/TP orders created: {sl_tp_result}")
```

### Risk Management Testing

The Paper Trading Adapter is particularly useful for testing risk management features:

```python
# Set up bracket orders with stop-loss
order = adapter.place_bracket_order(
    symbol="TSLA",
    qty=10,
    side="buy",
    stop_loss_price=250.0,  # 5% below current price
    take_profit_price=275.0  # 5% above current price
)

# Check if SL/TP orders were created
order_id = order["client_order_id"]
sl_order = adapter.get_order_status(f"{order_id}-sl")
tp_order = adapter.get_order_status(f"{order_id}-tp")

# Test global stop-loss by creating multiple positions
adapter.place_market_order("AAPL", 20, "buy")
adapter.place_market_order("MSFT", 15, "buy")
adapter.place_market_order("GOOGL", 5, "buy")

# Check portfolio value for global SL/TP calculations
account = adapter.get_account_info()
portfolio_value = float(account["portfolio_value"])
```

## Simulation Parameters

The Paper Trading Adapter has several configurable parameters that control the simulation behavior:

- `PRICE_VOLATILITY`: Controls the magnitude of price movements (default: 0.5%)
- `MARKET_ORDER_FILL_CHANCE`: Probability of immediate fill for market orders (default: 95%)

These can be modified after initialization:

```python
adapter = PaperTradingAdapter()

# Increase volatility for more active markets
adapter.PRICE_VOLATILITY = 0.01  # 1% volatility

# Decrease market order fill chance to simulate liquidity issues
adapter.MARKET_ORDER_FILL_CHANCE = 0.8  # 80% chance
```

## Implementation Details

### Market Simulation

The adapter uses a background thread that continuously:

1. Updates market prices with random movements
2. Checks if limit orders should be filled based on new prices
3. Checks if stop orders should be triggered
4. Updates account information and position values

### Order Processing

Orders go through a realistic lifecycle:

1. **Creation**: Orders start in `new` status
2. **Execution**: Depending on order type:
   - Market orders have a chance of immediate fill
   - Limit orders fill when price crosses the limit price
   - Stop orders trigger when price crosses the stop price
3. **Fill**: Orders can be fully or partially filled
4. **Position Update**: Fills update positions and account values

### Position Management

The adapter maintains realistic positions:

- Multiple positions for different symbols
- Average entry price calculation for partial fills
- Position flipping (long to short or vice versa)
- Unrealized P&L calculation based on current prices
- Portfolio value updates

### Risk Management Integration

The adapter integrates with the Risk Management service to:

- Validate order sizes against account risk limits
- Apply position sizing algorithms based on risk profiles
- Create stop-loss and take-profit orders with appropriate risk parameters
- Monitor portfolio-wide risk metrics
- Provide real-time risk assessment on potential trades

To prevent circular imports during testing, the adapter uses a lazy-loading mechanism for RiskManager integration:

```python
# In paper_trading_adapter.py
RiskManager = None  # Initially None

def _import_risk_manager():
    global RiskManager
    if RiskManager is None:
        try:
            from src.backend.services.risk_manager import RiskManager
        except ImportError:
            # Use a placeholder for testing environments
            class DummyRiskManager:
                def __init__(self, *args, **kwargs):
                    pass
                
                def validate_order_risk(*args, **kwargs):
                    return True, "Risk validation passed"
                
            RiskManager = DummyRiskManager
```

## Testing

Comprehensive unit tests are available in `tests/unit/integration/test_paper_trading_adapter.py` and integration with risk management is tested in `tests/unit/backend/services/test_risk_manager.py`.

## Limitations

- No realistic spread simulation (bid/ask)
- No slippage modeling
- Limited order types (no trailing stops, OCOs outside of brackets)
- No realistic order book simulation

## Future Enhancements

Potential enhancements for the paper trading adapter:

- Adding bid/ask spread simulation
- Implementing slippage models
- Adding more realistic market hours
- Simulating circuit breakers and trading halts
- Supporting trading multiple assets in different currencies
- Enhanced risk management capabilities with advanced stop-loss strategies 