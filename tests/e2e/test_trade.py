"""
Test cases for the trade execution flow
"""
import pytest
import requests
from unittest.mock import patch, MagicMock

# Constants
STATUS_URL = "http://localhost:5000/status"
CLEANUP_URL = "http://localhost:5000/cleanup"


def test_order_engine_long_entry(mock_broker_api, sample_webhook_long_entry):
    """Test order engine for long entry"""
    # Use the broker API mock to simulate placing an order
    order = mock_broker_api.place_order(
        symbol=sample_webhook_long_entry["symbol"],
        side="buy",
        qty=sample_webhook_long_entry["strategy_order_contracts"],
        order_type="market",
        client_order_id="test-long-entry-1"
    )
    
    # Assertions
    assert order["symbol"] == "BTCUSD"
    assert order["side"] == "buy"
    assert order["qty"] == 0.05
    assert order["status"] == "filled"
    
    # Verify position was created
    position = mock_broker_api.get_position("BTCUSD")
    assert position is not None
    assert position["qty"] == 0.05


def test_order_engine_long_exit(mock_broker_api):
    """Test order engine for long exit"""
    # Setup: Create a position first
    mock_broker_api.place_order(
        symbol="BTCUSD",
        side="buy",
        qty=0.1,
        order_type="market",
        client_order_id="test-long-entry-2"
    )
    
    # Verify position exists
    position_before = mock_broker_api.get_position("BTCUSD")
    assert position_before is not None
    assert position_before["qty"] == 0.1
    
    # Execute exit order
    exit_order = mock_broker_api.place_order(
        symbol="BTCUSD",
        side="sell",
        qty=0.1,
        order_type="market",
        client_order_id="test-long-exit-2"
    )
    
    # Assertions
    assert exit_order["symbol"] == "BTCUSD"
    assert exit_order["side"] == "sell"
    assert exit_order["qty"] == 0.1
    assert exit_order["status"] == "filled"
    
    # Verify position was closed
    position_after = mock_broker_api.get_position("BTCUSD")
    assert position_after is None


def test_stop_loss_order_creation(mock_broker_api):
    """Test creation of stop loss orders"""
    # Setup: Create a long position
    entry_order = mock_broker_api.place_order(
        symbol="BTCUSD",
        side="buy",
        qty=0.2,
        order_type="market",
        client_order_id="test-entry-with-sl-3"
    )
    
    # Now create a stop loss order (1% below entry)
    entry_price = 50000  # Mock entry price
    stop_price = entry_price * 0.99
    
    sl_order = mock_broker_api.place_order(
        symbol="BTCUSD",
        side="sell",
        qty=0.2,
        order_type="stop",
        stop_price=stop_price,
        client_order_id="test-entry-with-sl-3-sl"
    )
    
    # Assertions
    assert sl_order["symbol"] == "BTCUSD"
    assert sl_order["side"] == "sell"
    assert sl_order["qty"] == 0.2
    assert sl_order["order_type"] == "stop"
    assert sl_order["stop_price"] == stop_price
    assert sl_order["status"] == "new"  # Stop orders aren't immediately filled


def test_take_profit_order_creation(mock_broker_api):
    """Test creation of take profit orders"""
    # Setup: Create a long position
    entry_order = mock_broker_api.place_order(
        symbol="BTCUSD",
        side="buy",
        qty=0.2,
        order_type="market",
        client_order_id="test-entry-with-tp-4"
    )
    
    # Now create a take profit order (2% above entry)
    entry_price = 50000  # Mock entry price
    limit_price = entry_price * 1.02
    
    tp_order = mock_broker_api.place_order(
        symbol="BTCUSD",
        side="sell",
        qty=0.2,
        order_type="limit",
        limit_price=limit_price,
        client_order_id="test-entry-with-tp-4-tp"
    )
    
    # Assertions
    assert tp_order["symbol"] == "BTCUSD"
    assert tp_order["side"] == "sell"
    assert tp_order["qty"] == 0.2
    assert tp_order["order_type"] == "limit"
    assert tp_order["limit_price"] == limit_price
    assert tp_order["status"] == "new"  # Limit orders aren't immediately filled


def test_cleanup_service(mock_broker_api, mock_http_client):
    """Test the cleanup service for orphaned SL/TP orders"""
    # Setup: Create a position and SL/TP orders
    mock_broker_api.place_order(
        symbol="AAPL",
        side="buy",
        qty=10,
        order_type="market",
        client_order_id="test-cleanup-5"
    )
    
    # Create SL order
    mock_broker_api.place_order(
        symbol="AAPL",
        side="sell",
        qty=10,
        order_type="stop",
        stop_price=150.0,
        client_order_id="test-cleanup-5-sl"
    )
    
    # Create TP order
    mock_broker_api.place_order(
        symbol="AAPL",
        side="sell",
        qty=10,
        order_type="limit",
        limit_price=170.0,
        client_order_id="test-cleanup-5-tp"
    )
    
    # Create another position and SL/TP that will become orphaned
    mock_broker_api.place_order(
        symbol="MSFT",
        side="buy",
        qty=5,
        order_type="market",
        client_order_id="test-cleanup-6"
    )
    
    # Create SL order for MSFT
    mock_broker_api.place_order(
        symbol="MSFT",
        side="sell",
        qty=5,
        order_type="stop",
        stop_price=250.0,
        client_order_id="test-cleanup-6-sl"
    )
    
    # Create TP order for MSFT
    mock_broker_api.place_order(
        symbol="MSFT",
        side="sell",
        qty=5,
        order_type="limit",
        limit_price=280.0,
        client_order_id="test-cleanup-6-tp"
    )
    
    # Close MSFT position (making SL/TP orphaned)
    mock_broker_api.place_order(
        symbol="MSFT",
        side="sell",
        qty=5,
        order_type="market",
        client_order_id="test-cleanup-6-exit"
    )
    
    # Mock the cleanup service endpoint
    mock_http_client.post(
        CLEANUP_URL,
        status_code=200,
        json={
            "status": "success",
            "message": "Cleanup completed",
            "orders_canceled": 2  # Should cancel the 2 orphaned MSFT orders
        }
    )
    
    # Call cleanup service
    response = requests.post(CLEANUP_URL)
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["orders_canceled"] == 2


def test_global_sl_trigger(mock_broker_api, mock_http_client):
    """Test the global stop loss trigger functionality"""
    # Mock initial account equity
    mock_broker_api.account_info = {
        "equity": 100000.0,
        "buying_power": 200000.0,
        "cash": 100000.0
    }
    
    # Setup: Enable global SL/TP
    global_settings = {
        "enable_global_sl_tp": True,
        "global_sl_pct": 0.80,  # 80% of base equity
        "global_tp_pct": 1.20,  # 120% of base equity
        "base_equity": 100000.0
    }
    
    # Simulate equity dropping below SL threshold
    mock_broker_api.account_info["equity"] = 79000.0  # Below 80% threshold
    
    # Mock the status endpoint for checking global SL/TP
    mock_http_client.get(
        STATUS_URL,
        status_code=200,
        json={
            "status": "triggered",
            "message": "Global stop loss triggered",
            "current_equity": 79000.0,
            "threshold": 80000.0,
            "action": "liquidate_all"
        }
    )
    
    # Check status
    response = requests.get(STATUS_URL)
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "triggered"
    assert response_data["action"] == "liquidate_all"


def test_global_tp_trigger(mock_broker_api, mock_http_client):
    """Test the global take profit trigger functionality"""
    # Mock initial account equity
    mock_broker_api.account_info = {
        "equity": 100000.0,
        "buying_power": 200000.0,
        "cash": 100000.0
    }
    
    # Setup: Enable global SL/TP
    global_settings = {
        "enable_global_sl_tp": True,
        "global_sl_pct": 0.80,  # 80% of base equity
        "global_tp_pct": 1.20,  # 120% of base equity
        "base_equity": 100000.0
    }
    
    # Simulate equity rising above TP threshold
    mock_broker_api.account_info["equity"] = 121000.0  # Above 120% threshold
    
    # Mock the status endpoint for checking global SL/TP
    mock_http_client.get(
        STATUS_URL,
        status_code=200,
        json={
            "status": "triggered",
            "message": "Global take profit triggered",
            "current_equity": 121000.0,
            "threshold": 120000.0,
            "action": "notify"
        }
    )
    
    # Check status
    response = requests.get(STATUS_URL)
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "triggered"
    assert "take profit" in response_data["message"].lower() 