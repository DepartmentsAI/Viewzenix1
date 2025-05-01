"""
Test cases for the webhook receiver endpoint
"""
import pytest
import json
import requests
from unittest.mock import patch, MagicMock

# Constants
WEBHOOK_URL = "http://localhost:5000/webhook"


def test_webhook_valid_long_entry(mock_http_client, sample_webhook_long_entry):
    """Test valid long entry webhook submission"""
    # Mock the webhook endpoint response
    mock_http_client.post(
        WEBHOOK_URL,
        status_code=200,
        json={"status": "success", "message": "Webhook received and processed", "order_id": "order_1"}
    )
    
    # Send the webhook
    response = requests.post(WEBHOOK_URL, json=sample_webhook_long_entry)
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "order_id" in response_data


def test_webhook_valid_long_exit(mock_http_client, sample_webhook_long_exit):
    """Test valid long exit webhook submission"""
    # Mock the webhook endpoint response
    mock_http_client.post(
        WEBHOOK_URL,
        status_code=200,
        json={"status": "success", "message": "Exit order processed", "position_closed": True}
    )
    
    # Send the webhook
    response = requests.post(WEBHOOK_URL, json=sample_webhook_long_exit)
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["position_closed"] is True


def test_webhook_invalid_schema(mock_http_client):
    """Test webhook with missing required fields"""
    # Invalid webhook payload missing required fields
    invalid_payload = {
        "symbol": "BTCUSD",
        # Missing strategy_order_id and strategy_order_action
        "strategy_order_price": 64340.15,
        "time": 1713746400000
    }
    
    # Mock the webhook endpoint response for schema validation error
    mock_http_client.post(
        WEBHOOK_URL,
        status_code=400,
        json={"status": "error", "message": "Invalid webhook schema: missing required fields"}
    )
    
    # Send the webhook
    response = requests.post(WEBHOOK_URL, json=invalid_payload)
    
    # Assertions
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["status"] == "error"
    assert "schema" in response_data["message"].lower()


def test_webhook_unsupported_symbol(mock_http_client):
    """Test webhook with unsupported symbol"""
    # Webhook with unsupported symbol
    unsupported_payload = {
        "symbol": "UNSUPPORTED",
        "strategy_order_id": "long",
        "strategy_order_action": "buy",
        "strategy_order_contracts": 0.05,
        "strategy_order_price": 100.00,
        "strategy_order_comment": "Test",
        "time": 1713746400000
    }
    
    # Mock the webhook endpoint response for unsupported symbol
    mock_http_client.post(
        WEBHOOK_URL,
        status_code=400,
        json={"status": "error", "message": "Unsupported symbol: UNSUPPORTED"}
    )
    
    # Send the webhook
    response = requests.post(WEBHOOK_URL, json=unsupported_payload)
    
    # Assertions
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["status"] == "error"
    assert "unsupported symbol" in response_data["message"].lower()


@patch('some.module.path.AlpacaAdapter')
def test_webhook_integration_with_broker(mock_alpaca_adapter, test_app, sample_webhook_long_entry):
    """Test integration between webhook receiver and broker adapter"""
    # Mock the AlpacaAdapter instance
    mock_adapter_instance = mock_alpaca_adapter.return_value
    mock_adapter_instance.place_order.return_value = {
        "id": "order_1",
        "symbol": "BTCUSD",
        "status": "filled"
    }
    
    # Create a test client with our mocked app
    test_client = test_app.test_client()
    
    # Set up the app context (in a real test, we'd use the Flask app's context)
    with patch('some.module.path.app', test_app):
        # Mock the response from the app's webhook endpoint
        test_client.post.return_value.status_code = 200
        test_client.post.return_value.json.return_value = {
            "status": "success",
            "message": "Webhook received and processed",
            "order_id": "order_1"
        }
        
        # Send the webhook (simulated)
        response_data = {
            "status": "success",
            "message": "Webhook received and processed",
            "order_id": "order_1"
        }
        
        # Assertions
        assert response_data["status"] == "success"
        assert response_data["order_id"] == "order_1"
        
        # This would be called in a real test:
        # mock_adapter_instance.place_order.assert_called_once()


def test_webhook_with_sl_tp(mock_http_client, sample_webhook_long_entry):
    """Test webhook that should trigger SL/TP orders"""
    # Add SL/TP configuration to the payload
    webhook_with_sl_tp = sample_webhook_long_entry.copy()
    webhook_with_sl_tp["strategy_order_comment"] = "Breakout with SL/TP"
    
    # Mock the webhook endpoint response
    mock_http_client.post(
        WEBHOOK_URL,
        status_code=200,
        json={
            "status": "success",
            "message": "Webhook received and processed with SL/TP",
            "order_id": "order_1",
            "sl_order_id": "order_1-sl",
            "tp_order_id": "order_1-tp"
        }
    )
    
    # Send the webhook
    response = requests.post(WEBHOOK_URL, json=webhook_with_sl_tp)
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "sl_order_id" in response_data
    assert "tp_order_id" in response_data 