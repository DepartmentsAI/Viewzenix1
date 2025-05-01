"""
Conftest.py - Configuration and shared fixtures for E2E tests
"""
import json
import os
import pytest
from pathlib import Path
import requests_mock
from unittest.mock import patch, MagicMock

# Constants
BASE_URL = "http://localhost:5000"  # Default Flask server URL
FIXTURES_PATH = Path(__file__).parent / "fixtures"
DATA_PATH = FIXTURES_PATH / "data"


# Fixture for loading test data
@pytest.fixture
def load_test_data():
    """Fixture to load JSON test data files from the fixtures/data directory"""
    def _load_test_data(filename):
        with open(DATA_PATH / filename, "r") as f:
            return json.load(f)
    return _load_test_data


# Fixture for mocking HTTP requests
@pytest.fixture
def mock_http_client():
    """Fixture to mock HTTP requests"""
    with requests_mock.Mocker() as m:
        yield m


# Fixture for mock broker API
@pytest.fixture
def mock_broker_api():
    """Fixture to simulate broker API responses"""
    class MockBrokerAPI:
        def __init__(self):
            self.orders = []
            self.positions = {}
            self.account_info = {
                "equity": 100000.0,
                "buying_power": 200000.0,
                "cash": 100000.0
            }
        
        def place_order(self, symbol, side, qty=None, notional=None, order_type="market",
                       time_in_force="day", limit_price=None, stop_price=None,
                       client_order_id=None, extended_hours=False):
            """Simulate placing an order with the broker"""
            order_id = f"order_{len(self.orders) + 1}"
            order = {
                "id": order_id,
                "client_order_id": client_order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "notional": notional,
                "order_type": order_type,
                "time_in_force": time_in_force,
                "limit_price": limit_price,
                "stop_price": stop_price,
                "status": "filled" if order_type == "market" else "new"
            }
            self.orders.append(order)
            
            # If market order, update positions
            if order_type == "market" and order["status"] == "filled":
                self._update_position(symbol, side, qty)
            
            return order
        
        def get_order(self, order_id):
            """Get order by ID"""
            for order in self.orders:
                if order["id"] == order_id:
                    return order
            return None
        
        def get_orders(self):
            """Get all orders"""
            return self.orders
        
        def get_position(self, symbol):
            """Get position for a symbol"""
            if symbol in self.positions:
                return self.positions[symbol]
            return None
        
        def get_positions(self):
            """Get all positions"""
            return list(self.positions.values())
        
        def get_account(self):
            """Get account information"""
            return self.account_info
        
        def _update_position(self, symbol, side, qty):
            """Update position based on order"""
            qty = float(qty) if qty is not None else 0
            if symbol not in self.positions:
                self.positions[symbol] = {
                    "symbol": symbol,
                    "qty": qty if side == "buy" else -qty,
                    "avg_entry_price": 100.0,  # Mock price
                    "market_value": qty * 100.0 if side == "buy" else -qty * 100.0
                }
            else:
                position = self.positions[symbol]
                if side == "buy":
                    position["qty"] += qty
                else:
                    position["qty"] -= qty
                
                # Remove position if qty is 0
                if position["qty"] == 0:
                    del self.positions[symbol]
    
    return MockBrokerAPI()


# Fixture for mock API client
@pytest.fixture
def mock_api_client(mock_http_client):
    """Fixture for a mock API client to interact with the Flask API"""
    class MockAPIClient:
        def __init__(self, base_url):
            self.base_url = base_url
        
        def send_webhook(self, payload):
            """Send a webhook to the application"""
            url = f"{self.base_url}/webhook"
            response = requests.post(url, json=payload)
            return response
        
        def get_status(self):
            """Get application status"""
            url = f"{self.base_url}/status"
            response = requests.get(url)
            return response
        
        def run_cleanup(self):
            """Trigger cleanup service"""
            url = f"{self.base_url}/cleanup"
            response = requests.post(url)
            return response
    
    return MockAPIClient(BASE_URL)


# Fixture for a test Flask app
@pytest.fixture
def test_app():
    """Fixture for a test Flask application"""
    # This would import the actual Flask app in a real scenario
    # For now, we'll create a mock
    app = MagicMock()
    app.config = {}
    app.test_client.return_value = MagicMock()
    return app


# Fixture for sample webhook data
@pytest.fixture
def sample_webhook_long_entry():
    """Sample webhook data for a long entry"""
    return {
        "symbol": "BTCUSD",
        "strategy_order_id": "long",
        "strategy_order_action": "buy",
        "strategy_order_contracts": 0.05,
        "strategy_order_price": 64340.15,
        "strategy_order_comment": "Breakout",
        "time": 1713746400000
    }


@pytest.fixture
def sample_webhook_long_exit():
    """Sample webhook data for a long exit"""
    return {
        "symbol": "BTCUSD",
        "strategy_order_id": "long",
        "strategy_order_action": "sell",
        "strategy_order_contracts": 0.05,
        "strategy_order_price": 65000.00,
        "strategy_order_comment": "Take Profit",
        "time": 1713746500000
    }


@pytest.fixture
def sample_webhook_short_entry():
    """Sample webhook data for a short entry"""
    return {
        "symbol": "ETHUSD",
        "strategy_order_id": "sell",
        "strategy_order_action": "sell",
        "strategy_order_contracts": 0.2,
        "strategy_order_price": 3500.00,
        "strategy_order_comment": "Breakdown",
        "time": 1713746600000
    }


@pytest.fixture
def sample_webhook_short_exit():
    """Sample webhook data for a short exit"""
    return {
        "symbol": "ETHUSD",
        "strategy_order_id": "sell",
        "strategy_order_action": "buy",
        "strategy_order_contracts": 0.2,
        "strategy_order_price": 3400.00,
        "strategy_order_comment": "Take Profit",
        "time": 1713746700000
    } 