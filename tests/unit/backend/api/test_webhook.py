"""
Tests for the webhook endpoint.
"""
import json
import pytest
from src.backend.app import create_app

@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app("testing")
    with app.test_client() as client:
        yield client

def test_webhook_status(client):
    """Test the webhook status endpoint."""
    response = client.get('/api/webhook/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'active'
    assert data['service'] == 'TradingView Webhook Receiver'
    assert 'version' in data

def test_webhook_valid_payload(client):
    """Test the webhook endpoint with a valid payload."""
    payload = {
        "symbol": "BTCUSD",
        "strategy_order_id": "long",
        "strategy_order_action": "buy",
        "strategy_order_contracts": 0.05,
        "strategy_order_price": 64340.15,
        "strategy_order_comment": "Breakout",
        "time": 1713746400000
    }
    
    response = client.post(
        '/api/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'BTCUSD' in data['message']
    assert data['trade_type'] == 'long buy'

def test_webhook_invalid_payload(client):
    """Test the webhook endpoint with an invalid payload."""
    # Missing required fields
    payload = {
        "symbol": "BTCUSD",
        "strategy_order_action": "buy"
    }
    
    response = client.post(
        '/api/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid payload schema' in data['error']

def test_webhook_invalid_content_type(client):
    """Test the webhook endpoint with an invalid content type."""
    response = client.post(
        '/api/webhook',
        data="This is not JSON",
        content_type='text/plain'
    )
    
    assert response.status_code == 415
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Content type must be application/json' in data['error']

def test_webhook_invalid_json(client):
    """Test the webhook endpoint with invalid JSON."""
    response = client.post(
        '/api/webhook',
        data="This is not valid JSON",
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid JSON format' in data['error'] 