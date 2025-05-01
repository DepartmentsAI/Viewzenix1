"""
Fixtures for risk notification system testing.
"""
import pytest
import json
import requests_mock
from datetime import datetime, timedelta

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing API interactions."""
    with requests_mock.Mocker() as m:
        yield m

@pytest.fixture
def mock_broker_api():
    """Create a mock broker API for testing trading operations."""
    class MockBrokerApi:
        def __init__(self):
            self.orders = {}
            self.positions = {}
            self.account_info = {
                "equity": 100000.0,
                "buying_power": 200000.0,
                "cash": 100000.0,
                "initial_equity": 100000.0
            }
            self.reject_order = False
            self.rejection_reason = None
        
        def place_order(self, symbol, side, qty, order_type, client_order_id, **kwargs):
            """Place a simulated order."""
            if self.reject_order:
                raise Exception(f"Order rejected: {self.rejection_reason}")
                
            # Create the order
            order = {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "order_type": order_type,
                "client_order_id": client_order_id,
                "status": "new",
                "filled_qty": 0,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
            
            # For market orders, automatically fill them
            if order_type == "market":
                order["status"] = "filled"
                order["filled_qty"] = qty
                
                # Update positions (simplified)
                position_key = symbol
                if position_key not in self.positions:
                    self.positions[position_key] = {
                        "symbol": symbol,
                        "qty": 0,
                        "avg_price": 0,
                    }
                
                current_position = self.positions[position_key]
                
                if side == "buy":
                    # Simulate entry price
                    price = kwargs.get("price", 100.0)  # Default price if not provided
                    order["filled_price"] = price
                    
                    # Update position
                    current_position["qty"] += qty
                    current_position["avg_price"] = price
                else:  # sell
                    # Simulate exit price
                    price = kwargs.get("price", 100.0)  # Default price if not provided
                    order["filled_price"] = price
                    
                    # Update position
                    current_position["qty"] -= qty
                    if current_position["qty"] <= 0:
                        # Position closed, can set avg_price to 0
                        current_position["avg_price"] = 0
                
            # Store the order
            self.orders[client_order_id] = order
            return order
        
        def get_order(self, client_order_id):
            """Retrieve an order by its client ID."""
            return self.orders.get(client_order_id)
        
        def get_position(self, symbol):
            """Retrieve a position by symbol."""
            return self.positions.get(symbol)
        
        def get_account(self):
            """Get account information."""
            return self.account_info
        
        def cancel_order(self, client_order_id):
            """Cancel an existing order."""
            if client_order_id in self.orders:
                self.orders[client_order_id]["status"] = "canceled"
                return True
            return False
        
        def cleanup_orphaned_orders(self, threshold_minutes=30):
            """Simulate cleaning up orphaned orders."""
            threshold_time = datetime.now() - timedelta(minutes=threshold_minutes)
            cleaned_orders = []
            
            for order_id, order in list(self.orders.items()):
                # Check if order is old enough and still open
                is_old = datetime.fromisoformat(order["timestamp"]) < threshold_time
                is_open = order["status"] in ["new", "partially_filled"]
                
                # Check if related position is closed
                if is_open and "symbol" in order:
                    symbol = order["symbol"]
                    position = self.get_position(symbol)
                    position_closed = position is None or position["qty"] == 0
                    
                    if is_old or position_closed:
                        self.cancel_order(order_id)
                        cleaned_orders.append(order_id)
            
            return {
                "status": "success",
                "orders_canceled": cleaned_orders,
                "count": len(cleaned_orders)
            }
    
    return MockBrokerApi()

@pytest.fixture
def risk_notification_examples():
    """Test data for risk notification tests."""
    return {
        "orphaned_order_notifications": [
            {
                "id": "notif-123",
                "type": "risk_event",
                "title": "Orphaned Orders Cleaned Up",
                "message": "2 orphaned orders for MSFT have been automatically canceled.",
                "timestamp": datetime.now().isoformat(),
                "read": False,
                "link": "/risk/events",
                "event_id": "evt-456"
            }
        ],
        "drawdown_notifications": [
            {
                "id": "notif-124",
                "type": "risk_event",
                "title": "Approaching Maximum Drawdown",
                "message": "Current drawdown of 15.00% is approaching the daily limit of 20%.",
                "timestamp": datetime.now().isoformat(),
                "read": False,
                "link": "/risk/events",
                "event_id": "evt-457"
            },
            {
                "id": "notif-125",
                "type": "risk_event",
                "title": "Maximum Drawdown Exceeded",
                "message": "Current drawdown of 21.50% has exceeded the daily limit of 20%.",
                "timestamp": datetime.now().isoformat(),
                "read": False,
                "link": "/risk/events",
                "event_id": "evt-458"
            }
        ],
        "risk_limit_notifications": [
            {
                "id": "notif-126",
                "type": "risk_event",
                "title": "Risk Limit Breach",
                "message": "Order for 100 shares of AMZN rejected: Position size limit exceeded (max: 50).",
                "timestamp": datetime.now().isoformat(),
                "read": False,
                "link": "/risk/events",
                "event_id": "evt-459"
            }
        ],
        "risk_events": [
            {
                "event_type": "orphaned_order_cleanup",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "orders_canceled": ["order-123", "order-124"],
                    "symbol": "MSFT",
                    "cleanup_reason": "position_closed"
                },
                "severity": "info"
            },
            {
                "event_type": "drawdown_warning",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "current_drawdown_pct": 15.0,
                    "max_drawdown_pct": 20.0,
                    "warning_threshold_pct": 15.0,
                    "current_equity": 85000.0,
                    "initial_equity": 100000.0
                },
                "severity": "warning"
            },
            {
                "event_type": "drawdown_exceeded",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "current_drawdown_pct": 21.5,
                    "max_drawdown_pct": 20.0,
                    "current_equity": 78500.0,
                    "initial_equity": 100000.0
                },
                "severity": "error"
            },
            {
                "event_type": "risk_limit_breach",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "limit_type": "position_size",
                    "symbol": "AMZN",
                    "requested_qty": 100,
                    "max_allowed_qty": 50,
                    "rejected_order_id": "order-456"
                },
                "severity": "error"
            }
        ]
    } 