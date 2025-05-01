"""
Unit tests for the Risk API endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

from src.backend.app import create_app
from src.backend.api.risk import risk_manager


@pytest.fixture
def app():
    """Create a test Flask app with a testing configuration."""
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client


class TestRiskAPI:
    """Test suite for the Risk API endpoints."""
    
    def test_get_risk_parameters(self, client, monkeypatch):
        """Test GET /api/risk/parameters endpoint."""
        # Mock the risk_manager.get_risk_parameters method
        mock_params = {
            'stop_loss_percent': 0.02,
            'take_profit_percent': 0.05,
            'max_position_size_percent': 0.05,
            'max_daily_drawdown_percent': 0.05,
            'max_open_positions': 10,
            'orphaned_order_age_hours': 24
        }
        
        monkeypatch.setattr(risk_manager, 'get_risk_parameters', lambda: mock_params)
        
        # Call the endpoint
        response = client.get('/api/risk/parameters')
        data = json.loads(response.data)
        
        # Verify response
        assert response.status_code == 200
        assert data['status'] == 'success'
        assert data['parameters'] == mock_params
    
    def test_update_risk_parameters_success(self, client, monkeypatch):
        """Test PUT /api/risk/parameters endpoint with valid parameters."""
        # Test data
        update_data = {
            'stop_loss_percent': 0.03,
            'take_profit_percent': 0.06
        }
        
        # Mock the update_risk_parameters method
        mock_updated_params = {
            'stop_loss_percent': 0.03,
            'take_profit_percent': 0.06,
            'max_position_size_percent': 0.05,
            'max_daily_drawdown_percent': 0.05,
            'max_open_positions': 10,
            'orphaned_order_age_hours': 24
        }
        
        def mock_update(params):
            assert params == update_data
            return mock_updated_params
        
        monkeypatch.setattr(risk_manager, 'update_risk_parameters', mock_update)
        
        # Call the endpoint
        response = client.put(
            '/api/risk/parameters',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        # Verify response
        assert response.status_code == 200
        assert data['status'] == 'success'
        assert data['message'] == 'Risk parameters updated successfully'
        assert data['parameters'] == mock_updated_params
    
    def test_update_risk_parameters_invalid_json(self, client):
        """Test PUT /api/risk/parameters with invalid JSON."""
        # Call the endpoint with invalid JSON
        response = client.put(
            '/api/risk/parameters',
            data='not a valid json',
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        # Verify response
        assert response.status_code == 400
        assert 'error' in data
        assert 'Invalid JSON format' in data['error']
    
    def test_update_risk_parameters_validation_error(self, client):
        """Test PUT /api/risk/parameters with schema validation error."""
        # Test data with invalid value (stop_loss_percent > 1)
        update_data = {
            'stop_loss_percent': 1.5,  # Invalid: must be <= 1
            'take_profit_percent': 0.06
        }
        
        # Call the endpoint
        response = client.put(
            '/api/risk/parameters',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        # Verify response
        assert response.status_code == 400
        assert data['status'] == 'error'
        assert 'Invalid payload schema' in data['message']
    
    def test_get_risk_metrics(self, client, monkeypatch):
        """Test GET /api/risk/metrics endpoint."""
        # Mock risk_manager.get_risk_metrics method
        mock_metrics = {
            'portfolio': {
                'equity': 10000,
                'cash': 5000,
                'positions_count': 2,
                'positions_value': 5000,
                'largest_position': {
                    'symbol': 'BTCUSD',
                    'value': 3000,
                    'percent_of_portfolio': 0.3
                }
            },
            'daily_performance': {
                'start_equity': 9000,
                'current_equity': 10000,
                'max_equity': 10500,
                'min_equity': 8900,
                'current_drawdown_percent': 0.0476  # (10500-10000)/10500
            },
            'risk_parameters': {
                'stop_loss_percent': 0.02,
                'take_profit_percent': 0.05
            }
        }
        
        monkeypatch.setattr(risk_manager, 'get_risk_metrics', lambda: mock_metrics)
        
        # Call the endpoint
        response = client.get('/api/risk/metrics')
        data = json.loads(response.data)
        
        # Verify response
        assert response.status_code == 200
        assert data['status'] == 'success'
        assert data['metrics'] == mock_metrics
    
    def test_cleanup_orphaned_orders(self, client, monkeypatch):
        """Test POST /api/risk/cleanup endpoint."""
        # Mock risk_manager.cleanup_orphaned_orders method
        mock_results = {
            'cleaned_orders': [
                {
                    'order_id': 'old-order-123',
                    'reason': 'stale',
                    'created_at': '2023-01-01T00:00:00'
                }
            ],
            'errors': [],
            'total_cleaned': 1
        }
        
        monkeypatch.setattr(risk_manager, 'cleanup_orphaned_orders', lambda: mock_results)
        
        # Call the endpoint
        response = client.post('/api/risk/cleanup')
        data = json.loads(response.data)
        
        # Verify response
        assert response.status_code == 200
        assert data['status'] == 'success'
        assert data['results'] == mock_results
    
    def test_process_webhook_with_risk_success(self, client, monkeypatch):
        """Test POST /api/risk/webhook endpoint with successful order."""
        # Test webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 50000,
            'strategy_order_contracts': 0.1,
            'time': 1620000000000
        }
        
        # Mock result from process_order_with_risk_management
        mock_result = {
            'status': 'success',
            'message': 'Order executed with risk management',
            'order_result': {
                'status': 'success',
                'order_id': 'test-order-123'
            },
            'risk_applied': True
        }
        
        def mock_process(data):
            # Verify webhook data is passed correctly
            assert data == webhook_data
            return mock_result
        
        monkeypatch.setattr(risk_manager, 'process_order_with_risk_management', mock_process)
        
        # Call the endpoint
        response = client.post(
            '/api/risk/webhook',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        # Verify response
        assert response.status_code == 200
        assert data == mock_result
    
    def test_process_webhook_with_risk_rejected(self, client, monkeypatch):
        """Test POST /api/risk/webhook endpoint with rejected order."""
        # Test webhook data
        webhook_data = {
            'symbol': 'ADAUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 1.5,
            'strategy_order_contracts': 100,
            'time': 1620000000000
        }
        
        # Mock result from process_order_with_risk_management - rejected order
        mock_result = {
            'status': 'rejected',
            'message': 'Order rejected due to portfolio limits',
            'order_data': webhook_data
        }
        
        monkeypatch.setattr(risk_manager, 'process_order_with_risk_management', lambda data: mock_result)
        
        # Call the endpoint
        response = client.post(
            '/api/risk/webhook',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        # Verify response - should still be 200 for rejected orders
        assert response.status_code == 200
        assert data == mock_result
        assert data['status'] == 'rejected'
    
    def test_process_webhook_with_risk_error(self, client, monkeypatch):
        """Test POST /api/risk/webhook endpoint with error result."""
        # Test webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'time': 1620000000000
            # Missing required parameters
        }
        
        # Mock result from process_order_with_risk_management - error
        mock_result = {
            'status': 'error',
            'message': 'Invalid order data',
            'order_data': webhook_data
        }
        
        monkeypatch.setattr(risk_manager, 'process_order_with_risk_management', lambda data: mock_result)
        
        # Call the endpoint
        response = client.post(
            '/api/risk/webhook',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        # Verify response - should be 400 for errors
        assert response.status_code == 400  # Error status
        assert data == mock_result
        assert data['status'] == 'error' 