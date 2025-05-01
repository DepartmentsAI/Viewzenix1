# Risk Management System Architecture

## 1. Overview

The Risk Management System provides safety features for automated trading by implementing stop-loss and take-profit functionality, portfolio protection mechanisms, and orphaned order cleanup. It integrates with the existing OrderEngine to add risk-aware order processing while maintaining separation of concerns.

## 2. Key Components

### 2.1 RiskManager Service

The `RiskManager` class is the core service that implements risk management functionality:

- **Stop-Loss/Take-Profit Management**: Automatically creates SL/TP orders for entry positions
- **Portfolio Protection**: Enforces position limits and drawdown thresholds
- **Orphaned Order Cleanup**: Identifies and cancels stale orders
- **Risk Metrics**: Provides insight into current risk exposure
- **Risk Parameter Management**: Allows customization of risk thresholds

### 2.2 Risk API Endpoints

The Risk API exposes RESTful endpoints for interaction with the Risk Management System:

- `GET /api/risk/parameters`: Retrieve current risk parameters
- `PUT /api/risk/parameters`: Update risk parameters
- `GET /api/risk/metrics`: Get current risk metrics (exposure, drawdown, etc.)
- `POST /api/risk/cleanup`: Trigger manual cleanup of orphaned orders
- `POST /api/risk/webhook`: Process a webhook with risk management applied

### 2.3 Integration with OrderEngine

The Risk Management System integrates with the existing OrderEngine:

- RiskManager uses OrderEngine for order execution
- Enhanced webhook processing with risk management features
- Clean separation of concerns between order execution and risk management

## 3. Risk Parameters

The following risk parameters can be configured:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stop_loss_percent` | 0.02 (2%) | Default stop-loss percentage if not specified in order |
| `take_profit_percent` | 0.05 (5%) | Default take-profit percentage if not specified in order |
| `max_position_size_percent` | 0.05 (5%) | Maximum portion of account equity for a single position |
| `max_daily_drawdown_percent` | 0.05 (5%) | Maximum daily drawdown threshold |
| `max_open_positions` | 10 | Maximum number of concurrent open positions |
| `orphaned_order_age_hours` | 24 | Age threshold for considering orders orphaned |

## 4. Data Flow

### 4.1 Risk-Managed Order Processing

1. Client sends a webhook request with trading signals
2. RiskManager validates against portfolio limits
3. RiskManager checks daily drawdown limits
4. OrderEngine processes the main order
5. RiskManager adds SL/TP orders if applicable
6. Response includes order status and risk information

### 4.2 Risk Parameter Updates

1. Client sends PUT request to `/api/risk/parameters`
2. API validates the parameter schema
3. RiskManager updates internal parameters
4. Response includes updated parameter values

### 4.3 Orphaned Order Cleanup

1. Scheduled task or manual request triggers cleanup
2. RiskManager fetches all open orders
3. Orders older than threshold are identified
4. Orphaned orders are cancelled via broker adapter
5. Response includes cleanup results

## 5. Security Considerations

- All risk parameters are validated against defined schemas
- Percentage values are bounded (0-100%)
- Count values have minimum thresholds
- Error handling with proper logging is implemented throughout
- API responses never expose broker credentials

## 6. Future Enhancements

- **Advanced Position Sizing**: Kelly criterion and other risk-adjusted sizing methods
- **Time-Based Risk Controls**: Trading hour restrictions and circuit breakers
- **Strategy-Level Risk Parameters**: Custom risk settings per trading strategy
- **Volatility-Adjusted Risk**: Dynamic risk adjustments based on market volatility
- **Risk Dashboard**: Visual monitoring of risk metrics 