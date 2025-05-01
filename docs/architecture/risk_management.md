# Risk Management System - Architecture Documentation

## Overview

The Risk Management System is a critical safety component of the Trading Webhook Platform designed to protect user funds during automated trading. It provides configurable risk parameters, stop-loss/take-profit functionality, portfolio protection mechanisms, and cleanup services for orphaned orders.

## System Components

### 1. RiskManager Service

The core component of the system is the `RiskManager` class in `src/backend/services/risk_manager.py`. This service:

- Applies risk rules to incoming orders
- Monitors account performance and enforces drawdown limits
- Creates stop-loss and take-profit orders automatically
- Cleans up orphaned orders
- Provides risk metrics for monitoring

### 2. Risk API

The Risk API (`src/backend/api/risk.py`) exposes endpoints for:

- Retrieving and updating risk parameters
- Accessing risk metrics
- Triggering cleanup of orphaned orders
- Processing webhooks with risk management applied

## Risk Management Features

### Stop-Loss and Take-Profit Functionality

- Automatically creates stop-loss and take-profit orders for entry positions
- Supports both fixed price and percentage-based stop-loss/take-profit
- Customizable per incoming webhook
- Uses bracket orders where supported by the broker

### Portfolio Protection

- Maximum position size (percentage of portfolio)
- Maximum open positions limit
- Daily maximum drawdown limit
- Equity allocation tracking

### Orphaned Order Cleanup

- Identifies and cancels orders that have been open too long
- Configurable time threshold (default: 24 hours)
- Both automatic and manual cleanup options

## Configuration

Risk parameters are configurable via the API and include:

```json
{
  "stop_loss_percent": 0.02,
  "take_profit_percent": 0.05,
  "max_position_size_percent": 0.05,
  "max_daily_drawdown_percent": 0.05,
  "max_open_positions": 10,
  "orphaned_order_age_hours": 24
}
```

## Integration Points

The Risk Management System integrates with:

- **Order Execution Engine**: Applies risk rules before executing orders
- **Broker Adapter**: Executes stop-loss/take-profit orders, retrieves account information
- **Webhook API**: Provides risk-managed webhook endpoint

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/risk/parameters` | GET | Get current risk parameters |
| `/api/risk/parameters` | PUT | Update risk parameters |
| `/api/risk/metrics` | GET | Get current risk metrics |
| `/api/risk/cleanup` | POST | Trigger cleanup of orphaned orders |
| `/api/risk/webhook` | POST | Process a webhook with risk management applied |

## Risk Monitoring

The system provides comprehensive risk metrics, including:

- Current equity and buying power
- Position count and total value
- Equity allocation percentage
- Daily performance tracking
- Current and maximum daily drawdown

## Implementation Details

The RiskManager initializes with default risk parameters and can use any broker adapter that implements the `BrokerAdapter` interface. It maintains daily performance tracking and resets this tracking at the end of each trading day.

When processing orders, the RiskManager:

1. Checks portfolio limits (max positions, position size)
2. Updates daily performance tracking
3. Checks drawdown limits
4. Processes the main order via the OrderEngine
5. Adds stop-loss and take-profit orders if appropriate

## Security Considerations

- All risk parameters are validated before application
- Default values are conservative to protect user accounts
- API endpoints require proper authentication and authorization
- Error handling includes detailed logging but limits exposure of sensitive information in responses 