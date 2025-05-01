"""
Unit tests for risk management API endpoints.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.backend.app import create_app

@pytest.fixture
def client():
    """Create and configure a Flask client for testing."""
    # Create app in test mode
    app = create_app('testing')
    
    # Configure test client
    with app.test_client() as client:
        yield client

@patch('src.backend.api.risk.risk_manager')
def test_get_risk_parameters(mock_risk_manager, client):
    """Test GET /api/risk/parameters endpoint."""
    # Setup mock
    mock_risk_manager.get_risk_parameters.return_value = {
        'stop_loss_percent': 0.02,
        'take_profit_percent': 0.05,
        'max_position_size_percent': 0.05,
        'max_daily_drawdown_percent': 0.05,
        'max_open_positions': 10,
        'orphaned_order_age_hours': 24
    }
    
    # Make request
    response = client.get('/api/risk/parameters')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['status'] == 'success'
    assert 'parameters' in data
    assert data['parameters']['stop_loss_percent'] == 0.02
    assert data['parameters']['take_profit_percent'] == 0.05

@patch('src.backend.api.risk.risk_manager')
def test_update_risk_parameters(mock_risk_manager, client):
    """Test PUT /api/risk/parameters endpoint."""
    # Setup mock
    mock_risk_manager.update_risk_parameters.return_value = {
        'stop_loss_percent': 0.03,  # Updated value
        'take_profit_percent': 0.08,  # Updated value
        'max_position_size_percent': 0.05,
        'max_daily_drawdown_percent': 0.05,
        'max_open_positions': 10,
        'orphaned_order_age_hours': 24
    }
    
    # Make request
    payload = {
        'stop_loss_percent': 0.03,
        'take_profit_percent': 0.08
    }
    response = client.put(
        '/api/risk/parameters',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['status'] == 'success'
    assert data['message'] == 'Risk parameters updated successfully'
    assert data['parameters']['stop_loss_percent'] == 0.03
    assert data['parameters']['take_profit_percent'] == 0.08
    
    # Check function call
    mock_risk_manager.update_risk_parameters.assert_called_once_with(payload)

@patch('src.backend.api.risk.risk_manager')
def test_get_risk_metrics(mock_risk_manager, client):
    """Test GET /api/risk/metrics endpoint."""
    # Setup mock
    mock_metrics = {
        'account': {
            'equity': 10000.0,
            'buying_power': 20000.0,
            'cash': 5000.0,
        },
        'positions': {
            'count': 3,
            'total_value': 5000.0,
            'equity_allocation': 0.5
        },
        'daily_performance': {
            'start_equity': 9800.0,
            'current_equity': 10000.0,
            'daily_return': 0.0204,
            'max_equity': 10200.0,
            'min_equity': 9700.0,
            'max_drawdown': 0.049,
            'current_drawdown': 0.0196,
            'last_updated': '2023-05-01T14:30:00'
        }
    }
    mock_risk_manager.get_risk_metrics.return_value = mock_metrics
    
    # Make request
    response = client.get('/api/risk/metrics')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['status'] == 'success'
    assert 'metrics' in data
    assert data['metrics']['account']['equity'] == 10000.0
    assert data['metrics']['positions']['count'] == 3
    assert data['metrics']['daily_performance']['daily_return'] == 0.0204

@patch('src.backend.api.risk.risk_manager')
def test_cleanup_orphaned_orders(mock_risk_manager, client):
    """Test POST /api/risk/cleanup endpoint."""
    # Setup mock
    mock_cleanup_results = {
        'cleaned_orders': [
            {'order_id': 'order1', 'symbol': 'AAPL', 'age_hours': 25.5},
            {'order_id': 'order2', 'symbol': 'MSFT', 'age_hours': 36.2}
        ],
        'failed_orders': []
    }
    mock_risk_manager.cleanup_orphaned_orders.return_value = mock_cleanup_results
    
    # Make request
    response = client.post('/api/risk/cleanup')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['status'] == 'success'
    assert 'results' in data
    assert len(data['results']['cleaned_orders']) == 2
    assert data['results']['cleaned_orders'][0]['order_id'] == 'order1'

@patch('src.backend.api.risk.risk_manager')
def test_process_webhook_with_risk(mock_risk_manager, client):
    """Test POST /api/risk/webhook endpoint."""
    # Setup mock
    mock_result = {
        'status': 'success',
        'message': 'Order executed with risk management',
        'order_result': {
            'order_id': 'order123',
            'symbol': 'AAPL',
            'side': 'buy',
            'qty': 10,
            'type': 'market',
            'status': 'filled'
        },
        'risk_applied': True
    }
    mock_risk_manager.process_order_with_risk_management.return_value = mock_result
    
    # Make request
    payload = {
        'symbol': 'AAPL',
        'strategy_order_id': 'long',
        'strategy_order_action': 'buy',
        'strategy_order_price': 150.0,
        'strategy_order_contracts': 10,
        'time': 1620000000000
    }
    response = client.post(
        '/api/risk/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['status'] == 'success'
    assert data['message'] == 'Order executed with risk management'
    assert data['order_result']['order_id'] == 'order123'
    assert data['risk_applied'] == True
    
    # Check function call
    mock_risk_manager.process_order_with_risk_management.assert_called_once_with(payload)

@patch('src.backend.api.risk.risk_manager')
def test_process_webhook_with_risk_rejected(mock_risk_manager, client):
    """Test POST /api/risk/webhook endpoint with rejected order."""
    # Setup mock for order rejection
    mock_result = {
        'status': 'rejected',
        'message': 'Order rejected due to portfolio limits',
        'order_data': {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 150.0
        }
    }
    mock_risk_manager.process_order_with_risk_management.return_value = mock_result
    
    # Make request
    payload = {
        'symbol': 'AAPL',
        'strategy_order_id': 'long',
        'strategy_order_action': 'buy',
        'strategy_order_price': 150.0,
        'strategy_order_contracts': 100,  # Large position that will be rejected
        'time': 1620000000000
    }
    response = client.post(
        '/api/risk/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    # Check response - note that rejected orders still return 200
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['status'] == 'rejected'
    assert data['message'] == 'Order rejected due to portfolio limits'
    assert 'order_data' in data 