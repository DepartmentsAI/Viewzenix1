"""
Sample webhook payloads for testing.
"""

VALID_TRADINGVIEW_ALERTS = [
    {
        "strategy": {
            "order_action": "buy",
            "order_price": 100.50,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h"
        }
    },
    {
        "strategy": {
            "order_action": "sell",
            "order_price": 95.75,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h"
        }
    },
    {
        "strategy": {
            "order_action": "buy",
            "order_price": 150.25,
            "position_size": 2,
            "ticker": "MSFT",
            "timeframe": "4h"
        }
    },
    {
        "strategy": {
            "order_action": "sell",
            "order_price": 145.30,
            "position_size": 0.5,
            "ticker": "MSFT",
            "timeframe": "4h"
        }
    }
]

INVALID_TRADINGVIEW_ALERTS = [
    {
        "wrong_format": True
    },
    {
        "strategy": {
            "missing_fields": True
        }
    },
    {
        "strategy": {
            "order_action": "invalid_action",
            "order_price": 100.50,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h"
        }
    },
    {
        "strategy": {
            "order_action": "buy",
            "order_price": "not_a_number",
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h"
        }
    },
    {
        "strategy": {
            "order_action": "buy",
            "order_price": 100.50,
            "position_size": -1,  # Negative position size
            "ticker": "AAPL",
            "timeframe": "1h"
        }
    }
]

# Complex test cases with additional fields
COMPLEX_TRADINGVIEW_ALERTS = [
    {
        "strategy": {
            "order_action": "buy",
            "order_price": 100.50,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h",
            "stop_loss": 95.00,
            "take_profit": 110.00,
            "risk_percentage": 2.0,
            "strategy_name": "Moving Average Crossover"
        }
    },
    {
        "strategy": {
            "order_action": "sell",
            "order_price": 95.75,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h",
            "stop_loss": 100.00,
            "take_profit": 90.00,
            "risk_percentage": 1.5,
            "strategy_name": "RSI Divergence"
        }
    }
]

# Market order examples (no price specified)
MARKET_ORDER_ALERTS = [
    {
        "strategy": {
            "order_action": "buy",
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h",
            "order_type": "market"
        }
    },
    {
        "strategy": {
            "order_action": "sell",
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h",
            "order_type": "market"
        }
    }
]

# Bracket order examples (with stop loss and take profit)
BRACKET_ORDER_ALERTS = [
    {
        "strategy": {
            "order_action": "buy",
            "order_price": 100.50,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h",
            "stop_loss": 95.00,
            "take_profit": 110.00
        }
    },
    {
        "strategy": {
            "order_action": "sell",
            "order_price": 95.75,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "1h",
            "stop_loss": 100.00,
            "take_profit": 90.00
        }
    }
]

# Example signals from specific strategies
STRATEGY_SPECIFIC_ALERTS = {
    "moving_average_crossover": {
        "strategy": {
            "name": "MA Crossover",
            "order_action": "buy",
            "order_price": 220.50,
            "position_size": 1,
            "ticker": "TSLA",
            "timeframe": "1d",
            "fast_ma": 9,
            "slow_ma": 21
        }
    },
    "rsi_oversold": {
        "strategy": {
            "name": "RSI Oversold",
            "order_action": "buy",
            "order_price": 150.25,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "4h",
            "rsi_value": 29.5,
            "rsi_period": 14
        }
    },
    "rsi_overbought": {
        "strategy": {
            "name": "RSI Overbought",
            "order_action": "sell",
            "order_price": 162.75,
            "position_size": 1,
            "ticker": "AAPL",
            "timeframe": "4h",
            "rsi_value": 71.2,
            "rsi_period": 14
        }
    }
} 