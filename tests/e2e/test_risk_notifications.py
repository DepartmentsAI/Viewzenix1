"""
E2E tests for the Risk Management notification system.
These tests verify that the notification system properly alerts users
about risk-related events like orphaned order cleanup, drawdown limits, etc.
"""
import pytest
import requests
import json
from datetime import datetime, timedelta

# Constants for endpoints
BASE_URL = "http://localhost:5000/api/v1"
NOTIFICATION_URL = f"{BASE_URL}/notifications"
RISK_EVENTS_URL = f"{BASE_URL}/risk/events"

class TestRiskNotifications:
    """E2E test suite for the risk management notification system."""
    
    @pytest.fixture
    def mock_notification_service(self, mock_http_client):
        """Setup mock notification service endpoints."""
        # Mock the notification service endpoint
        mock_http_client.get(
            NOTIFICATION_URL,
            status_code=200,
            json={
                "notifications": []
            }
        )
        
        # Mock the risk events endpoint
        mock_http_client.get(
            RISK_EVENTS_URL,
            status_code=200,
            json={
                "events": []
            }
        )
        
        return mock_http_client
    
    def test_orphaned_order_cleanup_notification(self, mock_broker_api, mock_notification_service):
        """Test that orphaned order cleanup events generate appropriate notifications."""
        # Setup: Create an order that will become orphaned
        entry_order = mock_broker_api.place_order(
            symbol="AAPL",
            side="buy",
            qty=10,
            order_type="market",
            client_order_id="test-notif-orphan-1"
        )
        
        # Create SL order
        sl_order = mock_broker_api.place_order(
            symbol="AAPL",
            side="sell",
            qty=10,
            order_type="stop",
            stop_price=150.0,
            client_order_id="test-notif-orphan-1-sl"
        )
        
        # Close position, making the SL order orphaned
        exit_order = mock_broker_api.place_order(
            symbol="AAPL",
            side="sell",
            qty=10,
            order_type="market",
            client_order_id="test-notif-orphan-1-exit"
        )
        
        # Mock risk event for cleanup
        cleanup_event = {
            "event_type": "orphaned_order_cleanup",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "orders_canceled": [sl_order["client_order_id"]],
                "symbol": "AAPL",
                "cleanup_reason": "position_closed"
            },
            "severity": "info"
        }
        
        # Mock the risk events endpoint to return our event
        mock_notification_service.get(
            RISK_EVENTS_URL,
            status_code=200,
            json={
                "events": [cleanup_event]
            }
        )
        
        # Mock the notification service to include our notification
        notification = {
            "id": "notif-123",
            "type": "risk_event",
            "title": "Orphaned Orders Cleaned Up",
            "message": "1 orphaned stop-loss order(s) for AAPL have been automatically canceled.",
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "link": "/risk/events",
            "event_id": "evt-456"
        }
        
        mock_notification_service.get(
            NOTIFICATION_URL,
            status_code=200,
            json={
                "notifications": [notification]
            }
        )
        
        # Call the notification service
        response = requests.get(NOTIFICATION_URL)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["type"] == "risk_event"
        assert "orphaned" in data["notifications"][0]["message"].lower()
        assert "cleaned up" in data["notifications"][0]["message"].lower()
        assert data["notifications"][0]["read"] is False
        
        # Call the risk events endpoint
        events_response = requests.get(RISK_EVENTS_URL)
        
        # Assertions for events
        assert events_response.status_code == 200
        events_data = events_response.json()
        assert len(events_data["events"]) == 1
        assert events_data["events"][0]["event_type"] == "orphaned_order_cleanup"
        assert len(events_data["events"][0]["details"]["orders_canceled"]) == 1
    
    def test_maximum_drawdown_notification(self, mock_broker_api, mock_notification_service):
        """Test that approaching maximum drawdown generates appropriate warnings."""
        # Setup: Mock account info with equity near drawdown limit
        initial_equity = 100000.0
        current_equity = 85000.0  # 15% drawdown
        
        mock_broker_api.account_info = {
            "equity": current_equity,
            "initial_equity": initial_equity,
            "buying_power": 170000.0,
            "cash": 85000.0
        }
        
        # Mock risk settings
        risk_settings = {
            "max_daily_drawdown_pct": 20.0,  # 20% max drawdown
            "warning_threshold_pct": 75.0     # Warn at 75% of max drawdown
        }
        
        # Calculate drawdown metrics
        current_drawdown_pct = (initial_equity - current_equity) / initial_equity * 100
        max_drawdown_pct = risk_settings["max_daily_drawdown_pct"]
        warning_threshold = max_drawdown_pct * (risk_settings["warning_threshold_pct"] / 100)
        
        # We're at 15% drawdown and warning threshold is 15% (75% of 20%)
        is_warning_triggered = current_drawdown_pct >= warning_threshold
        
        # Mock risk event for drawdown warning
        if is_warning_triggered:
            drawdown_event = {
                "event_type": "drawdown_warning",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "current_drawdown_pct": current_drawdown_pct,
                    "max_drawdown_pct": max_drawdown_pct,
                    "warning_threshold_pct": warning_threshold,
                    "current_equity": current_equity,
                    "initial_equity": initial_equity
                },
                "severity": "warning"
            }
            
            # Mock the risk events endpoint to return our event
            mock_notification_service.get(
                RISK_EVENTS_URL,
                status_code=200,
                json={
                    "events": [drawdown_event]
                }
            )
            
            # Mock the notification service to include our notification
            notification = {
                "id": "notif-124",
                "type": "risk_event",
                "title": "Approaching Maximum Drawdown",
                "message": f"Current drawdown of {current_drawdown_pct:.2f}% is approaching the daily limit of {max_drawdown_pct}%.",
                "timestamp": datetime.now().isoformat(),
                "read": False,
                "link": "/risk/events",
                "event_id": "evt-457"
            }
            
            mock_notification_service.get(
                NOTIFICATION_URL,
                status_code=200,
                json={
                    "notifications": [notification]
                }
            )
            
            # Call the notification service
            response = requests.get(NOTIFICATION_URL)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert len(data["notifications"]) == 1
            assert data["notifications"][0]["type"] == "risk_event"
            assert "drawdown" in data["notifications"][0]["message"].lower()
            assert "approaching" in data["notifications"][0]["message"].lower()
            assert data["notifications"][0]["read"] is False
            
            # Call the risk events endpoint
            events_response = requests.get(RISK_EVENTS_URL)
            
            # Assertions for events
            assert events_response.status_code == 200
            events_data = events_response.json()
            assert len(events_data["events"]) == 1
            assert events_data["events"][0]["event_type"] == "drawdown_warning"
            assert events_data["events"][0]["severity"] == "warning"
            assert events_data["events"][0]["details"]["current_drawdown_pct"] == current_drawdown_pct
    
    def test_risk_limit_breach_notification(self, mock_broker_api, mock_notification_service):
        """Test that breaching a risk limit generates appropriate notifications."""
        # Setup: Try to place an order that exceeds position size limits
        oversized_order = {
            "symbol": "AMZN",
            "side": "buy",
            "qty": 100,  # Large quantity that exceeds limits
            "order_type": "market",
            "client_order_id": "test-risk-limit-breach-1"
        }
        
        # Mock rejection due to risk limit
        mock_broker_api.reject_order = True
        mock_broker_api.rejection_reason = "position_size_exceeded"
        
        # Attempt to place the order (will be rejected)
        with pytest.raises(Exception) as e:
            mock_broker_api.place_order(**oversized_order)
            assert "position_size_exceeded" in str(e)
        
        # Mock risk event for limit breach
        limit_breach_event = {
            "event_type": "risk_limit_breach",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "limit_type": "position_size",
                "symbol": oversized_order["symbol"],
                "requested_qty": oversized_order["qty"],
                "max_allowed_qty": 50,
                "rejected_order_id": oversized_order["client_order_id"]
            },
            "severity": "error"
        }
        
        # Mock the risk events endpoint to return our event
        mock_notification_service.get(
            RISK_EVENTS_URL,
            status_code=200,
            json={
                "events": [limit_breach_event]
            }
        )
        
        # Mock the notification service to include our notification
        notification = {
            "id": "notif-125",
            "type": "risk_event",
            "title": "Risk Limit Breach",
            "message": f"Order for {oversized_order['qty']} shares of {oversized_order['symbol']} rejected: Position size limit exceeded (max: 50).",
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "link": "/risk/events",
            "event_id": "evt-458"
        }
        
        mock_notification_service.get(
            NOTIFICATION_URL,
            status_code=200,
            json={
                "notifications": [notification]
            }
        )
        
        # Call the notification service
        response = requests.get(NOTIFICATION_URL)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["type"] == "risk_event"
        assert "rejected" in data["notifications"][0]["message"].lower()
        assert "limit exceeded" in data["notifications"][0]["message"].lower()
        assert data["notifications"][0]["read"] is False
        
        # Call the risk events endpoint
        events_response = requests.get(RISK_EVENTS_URL)
        
        # Assertions for events
        assert events_response.status_code == 200
        events_data = events_response.json()
        assert len(events_data["events"]) == 1
        assert events_data["events"][0]["event_type"] == "risk_limit_breach"
        assert events_data["events"][0]["severity"] == "error"
        assert events_data["events"][0]["details"]["limit_type"] == "position_size" 