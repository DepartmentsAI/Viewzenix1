# Risk Management System

This document outlines the risk management system implemented in the Viewzenix1 trading platform to protect user funds during automated trading.

## Overview

The risk management system provides essential safety features for automated trading, including:

1. **Per-Order Stop-Loss and Take-Profit Functionality**: Automatically append stop-loss and take-profit orders when executing main orders.
2. **Global Portfolio Protection**: Monitor and enforce portfolio-level risk constraints.
3. **Orphaned Order Cleanup**: Identify and clean up stale or orphaned orders.
4. **Risk Configuration API**: Allow configuration of risk parameters through a RESTful API.

## Architecture

The risk management system is built around the `RiskManager` class that integrates with the existing `OrderEngine` and broker adapters:

```
                   ┌───────────────┐
                   │  Web Clients  │
                   └───────┬───────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                     API Layer                         │
├──────────────┬─────────────────────┬─────────────────┤
│ /api/webhook │ /api/risk/parameters│ /api/risk/metrics│
└──────┬───────┴──────────┬──────────┴─────────┬───────┘
       │                  │                    │
       ▼                  ▼                    ▼
┌─────────────┐    ┌────────────┐     ┌─────────────────┐
│ OrderEngine │◄───┤ RiskManager├────►│ Broker Adapters │
└─────────────┘    └────────────┘     └─────────────────┘
```

## Risk Manager

The `RiskManager` class (`src/backend/services/risk_manager.py`) provides the following core functionality:

### 1. Stop-Loss and Take-Profit Management

- Automatically calculates and places stop-loss and take-profit orders when a position is opened
- Supports both fixed price and percentage-based SL/TP levels
- Allows customization per incoming webhook (via `stop_loss` and `take_profit` parameters)

### 2. Portfolio Protection

- **Maximum Position Count**: Limits the number of simultaneous open positions
- **Position Size Limits**: Ensures no position exceeds a specific percentage of account equity
- **Daily Drawdown Limit**: Tracks equity changes and prevents trading when daily drawdown exceeds threshold

### 3. Orphaned Order Cleanup

- Identifies open orders that have been pending for longer than a specific time
- Provides a service to automatically cancel these stale orders
- Includes both scheduled and manual cleanup mechanisms

## API Endpoints

### Risk Management API

The risk management system exposes the following REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/risk/parameters` | GET | Get current risk parameters |
| `/api/risk/parameters` | PUT | Update risk parameters |
| `/api/risk/metrics` | GET | Get current risk metrics |
| `/api/risk/cleanup` | POST | Trigger cleanup of orphaned orders |
| `/api/risk/webhook` | POST | Process a webhook with risk management |

### Webhook Integration

The existing webhook endpoint (`/api/webhook`) has been enhanced to support risk management:

- Added support for `stop_loss` and `take_profit` parameters in webhook payload
- Added `use_risk_management` flag to enable/disable risk checks for specific webhooks

## Risk Parameters

The risk management system uses the following configurable parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `stop_loss_percent` | Default percentage-based stop loss | 2% (0.02) |
| `take_profit_percent` | Default percentage-based take profit | 5% (0.05) |
| `max_position_size_percent` | Maximum position size as percentage of equity | 5% (0.05) |
| `max_daily_drawdown_percent` | Maximum allowed daily drawdown | 5% (0.05) |
| `max_open_positions` | Maximum number of open positions | 10 |
| `orphaned_order_age_hours` | Hours after which an order is considered orphaned | 24 |

## Usage Examples

### 1. Sending a webhook with stop-loss and take-profit parameters

```json
{
  "symbol": "BTCUSD",
  "strategy_order_id": "long",
  "strategy_order_action": "buy",
  "strategy_order_price": 50000,
  "strategy_order_contracts": 0.1,
  "time": 1620000000000,
  "stop_loss": {
    "percent": 0.03
  },
  "take_profit": {
    "price": 55000
  }
}
```

### 2. Updating risk parameters

```json
// PUT /api/risk/parameters
{
  "stop_loss_percent": 0.02,
  "take_profit_percent": 0.05,
  "max_daily_drawdown_percent": 0.08
}
```

### 3. Retrieving risk metrics

```
GET /api/risk/metrics
```

Response:
```json
{
  "status": "success",
  "metrics": {
    "portfolio": {
      "equity": 10000,
      "cash": 5000,
      "positions_count": 2,
      "positions_value": 5000,
      "largest_position": {
        "symbol": "BTCUSD",
        "value": 3000,
        "percent_of_portfolio": 0.3
      }
    },
    "daily_performance": {
      "start_equity": 9000,
      "current_equity": 10000,
      "max_equity": 10500,
      "min_equity": 8900,
      "current_drawdown_percent": 0.0476
    },
    "risk_parameters": {
      "stop_loss_percent": 0.02,
      "take_profit_percent": 0.05,
      "max_position_size_percent": 0.05,
      "max_daily_drawdown_percent": 0.05,
      "max_open_positions": 10,
      "orphaned_order_age_hours": 24
    }
  }
}
```

## Implementation Details

### Order Rejection Process

Orders can be rejected by the risk management system for the following reasons:

1. **Portfolio Limits**: When maximum number of positions is reached or position size exceeds limits
2. **Drawdown Limits**: When daily drawdown exceeds the configured threshold

When an order is rejected, a response with `status: "rejected"` is returned with the specific reason.

### Stop-Loss/Take-Profit Calculation

For a long position:
- Default stop-loss price = entry_price * (1 - stop_loss_percent)
- Default take-profit price = entry_price * (1 + take_profit_percent)

For a short position:
- Default stop-loss price = entry_price * (1 + stop_loss_percent)
- Default take-profit price = entry_price * (1 - take_profit_percent)

Fixed price SL/TP parameters in the webhook payload override these calculated values.

## Testing

Comprehensive unit tests are provided for both the RiskManager class and the risk API endpoints:

- `tests/unit/backend/services/test_risk_manager.py`: Tests for RiskManager functionality
- `tests/unit/backend/api/test_risk_api.py`: Tests for risk API endpoints

## Future Enhancements

1. **Risk Profiles**: Support for multiple named risk profiles for different trading strategies
2. **Time-Based Rules**: Implement time-of-day based risk rules
3. **Volatility-Based Adjustments**: Dynamically adjust risk parameters based on market volatility
4. **Position Correlation Analysis**: Calculate portfolio risk considering correlations between positions 