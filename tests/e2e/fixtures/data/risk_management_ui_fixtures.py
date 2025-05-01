"""
Fixtures for risk management UI tests.
"""
import json
import os
import pytest
from datetime import datetime, timedelta


class RiskManagementFixtures:
    """Provides test fixtures for risk management UI tests."""
    
    @staticmethod
    def get_mock_portfolio_data():
        """
        Return mock portfolio data for the risk management UI.
        
        Returns:
            dict: Portfolio data including positions, equity, and risk metrics
        """
        return {
            "account_summary": {
                "equity": 100000.00,
                "cash": 70000.00,
                "previous_day_equity": 98000.00,
                "daily_pnl": 2000.00,
                "daily_pnl_pct": 2.04,
                "margin_used": 30000.00,
                "margin_available": 70000.00
            },
            "risk_metrics": {
                "portfolio_risk_score": 0.65,  # Scale from 0-1 (low to high risk)
                "risk_exposure_pct": 0.30,     # Percentage of equity at risk
                "largest_position_pct": 0.25,  # Largest position as percentage of equity
                "daily_drawdown_pct": 0.00,    # Current day's maximum drawdown
                "emergency_threshold_pct": 0.10 # Emergency stop loss threshold
            },
            "positions": [
                {
                    "symbol": "BTCUSD",
                    "qty": 0.5,
                    "side": "long",
                    "entry_price": 60000.00,
                    "current_price": 62000.00,
                    "value": 31000.00,
                    "unrealized_pl": 1000.00,
                    "unrealized_pl_pct": 3.33,
                    "risk_score": 0.75,
                    "sl_price": 58800.00,
                    "tp_price": 63000.00,
                    "max_loss_usd": -600.00
                },
                {
                    "symbol": "ETHUSD",
                    "qty": 2.0,
                    "side": "long",
                    "entry_price": 2500.00,
                    "current_price": 2600.00,
                    "value": 5200.00,
                    "unrealized_pl": 200.00,
                    "unrealized_pl_pct": 4.00,
                    "risk_score": 0.60,
                    "sl_price": 2450.00,
                    "tp_price": 2625.00,
                    "max_loss_usd": -100.00
                }
            ],
            "active_orders": [
                {
                    "id": "ord-123",
                    "symbol": "BTCUSD",
                    "qty": 0.5,
                    "side": "sell",
                    "type": "stop",
                    "stop_price": 58800.00,
                    "status": "new",
                    "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "order_type": "sl"
                },
                {
                    "id": "ord-124",
                    "symbol": "BTCUSD",
                    "qty": 0.5,
                    "side": "sell",
                    "type": "limit",
                    "limit_price": 63000.00,
                    "status": "new",
                    "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "order_type": "tp"
                },
                {
                    "id": "ord-125",
                    "symbol": "ETHUSD",
                    "qty": 2.0,
                    "side": "sell",
                    "type": "stop",
                    "stop_price": 2450.00,
                    "status": "new",
                    "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "order_type": "sl"
                },
                {
                    "id": "ord-126",
                    "symbol": "ETHUSD",
                    "qty": 2.0,
                    "side": "sell",
                    "type": "limit",
                    "limit_price": 2625.00,
                    "status": "new",
                    "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "order_type": "tp"
                }
            ]
        }
    
    @staticmethod
    def get_risk_settings():
        """
        Return mock risk settings for the risk management UI.
        
        Returns:
            dict: Risk configuration settings
        """
        return {
            "global_settings": {
                "max_position_size_usd": 50000.00,
                "max_position_size_pct": 0.25,
                "max_single_order_size_usd": 10000.00,
                "max_daily_drawdown_pct": 0.05,
                "emergency_stop_loss_pct": 0.10,
                "max_leverage": 3.0,
                "cleanup_threshold_minutes": 30
            },
            "per_order_settings": {
                "default_sl_pct": 0.02,
                "default_tp_pct": 0.05,
                "automatic_sl_tp": True,
                "cancel_sl_tp_on_position_close": True
            },
            "currency_specific_settings": {
                "BTCUSD": {
                    "max_position_size": 1.0,
                    "sl_pct": 0.02,
                    "tp_pct": 0.05
                },
                "ETHUSD": {
                    "max_position_size": 5.0,
                    "sl_pct": 0.02,
                    "tp_pct": 0.05
                }
            }
        }
    
    @staticmethod
    def get_risk_events():
        """
        Return mock risk events for the risk management UI.
        
        Returns:
            list: Recent risk-related events
        """
        return [
            {
                "id": "evt-001",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "type": "order_rejected",
                "level": "warning",
                "details": {
                    "symbol": "BTCUSD",
                    "reason": "Order size exceeds maximum position size limit",
                    "order_size_usd": 60000.00,
                    "max_size_usd": 50000.00
                }
            },
            {
                "id": "evt-002",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "type": "sl_triggered",
                "level": "info",
                "details": {
                    "symbol": "LTCUSD",
                    "qty": 10.0,
                    "price": 180.00,
                    "loss_usd": -200.00
                }
            },
            {
                "id": "evt-003",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "type": "drawdown_warning",
                "level": "warning",
                "details": {
                    "current_drawdown_pct": 0.045,
                    "max_drawdown_pct": 0.05,
                    "message": "Approaching daily drawdown limit"
                }
            }
        ]
    
    @staticmethod
    def save_fixtures_to_json(base_dir):
        """
        Save all fixtures to JSON files for use in tests.
        
        Args:
            base_dir (str): Base directory to save fixture files
        """
        fixtures = RiskManagementFixtures()
        
        # Ensure fixtures directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Save portfolio data
        with open(os.path.join(base_dir, 'portfolio_data.json'), 'w') as f:
            json.dump(fixtures.get_mock_portfolio_data(), f, indent=2)
        
        # Save risk settings
        with open(os.path.join(base_dir, 'risk_settings.json'), 'w') as f:
            json.dump(fixtures.get_risk_settings(), f, indent=2)
        
        # Save risk events
        with open(os.path.join(base_dir, 'risk_events.json'), 'w') as f:
            json.dump(fixtures.get_risk_events(), f, indent=2)


@pytest.fixture
def risk_management_fixtures():
    """Fixture providing risk management test data."""
    return RiskManagementFixtures()


@pytest.fixture
def mock_portfolio_data():
    """Fixture providing mock portfolio data."""
    return RiskManagementFixtures.get_mock_portfolio_data()


@pytest.fixture
def mock_risk_settings():
    """Fixture providing mock risk settings."""
    return RiskManagementFixtures.get_risk_settings()


@pytest.fixture
def mock_risk_events():
    """Fixture providing mock risk events."""
    return RiskManagementFixtures.get_risk_events() 