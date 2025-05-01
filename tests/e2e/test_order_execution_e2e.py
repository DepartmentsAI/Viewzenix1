"""
End-to-End tests for the Order Execution Engine.
Tests the full workflow from webhook reception to order execution.
"""
import pytest
import json
import os
import time
from unittest import mock
import requests
from requests.exceptions import RequestException

from src.backend.app import create_app
from src.integration.adapters.alpaca_adapter import AlpacaAdapter
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from tests.e2e.fixtures.broker_mocks.alpaca_mock import MockAlpacaAPI


class TestOrderExecutionE2E:
    """End-to-End tests for the Order Execution flow."""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app for testing."""
        # Use testing configuration
        app = create_app(testing=True)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @pytest.fixture
    def webhook_data(self):
        """Load webhook test data from fixtures."""
        webhook_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'data', 'webhook_examples.json')
        with open(webhook_path, 'r') as f:
            webhook_examples = json.load(f)
        return webhook_examples
    
    @pytest.fixture
    def mock_alpaca_api(self):
        """Create a MockAlpacaAPI for testing."""
        mock_api = MockAlpacaAPI()
        return mock_api
    
    @pytest.fixture
    def patch_alpaca_adapter(self, mock_alpaca_api):
        """Patch AlpacaAdapter to use MockAlpacaAPI."""
        # Save original methods to restore later
        original_make_request = AlpacaAdapter._make_request
        
        # Define a mock _make_request method
        def mock_make_request(self, method, endpoint, params, order_id=None):
            return mock_alpaca_api.handle_request(method, endpoint, params, order_id)
        
        # Apply the patch
        AlpacaAdapter._make_request = mock_make_request
        
        # Return function to restore original methods
        def restore():
            AlpacaAdapter._make_request = original_make_request
        
        yield mock_alpaca_api
        
        # Restore original methods
        restore()
    
    def test_webhook_to_order_flow_long_entry(self, client, webhook_data, patch_alpaca_api):
        """Test full flow from webhook reception to long entry order execution."""
        # Get test data
        long_entry_data = webhook_data.get("long_entry", {})
        if not long_entry_data:
            pytest.skip("No long entry test data available.")
        
        # Configure mock API response for successful order
        patch_alpaca_api.set_order_response({
            "id": "mock-order-id-123",
            "client_order_id": "test-client-id",
            "status": "filled",
            "symbol": long_entry_data.get("symbol"),
            "type": "market",
            "side": "buy",
            "qty": str(long_entry_data.get("strategy_order_contracts", "0.1")),
            "filled_qty": str(long_entry_data.get("strategy_order_contracts", "0.1")),
            "filled_avg_price": "50000",
            "submitted_at": "2023-05-05T10:00:00Z",
            "filled_at": "2023-05-05T10:00:01Z"
        })
        
        # Also set account and position info
        patch_alpaca_api.set_account_response({
            "equity": "10000",
            "buying_power": "10000",
            "cash": "10000"
        })
        patch_alpaca_api.set_position_response(None)  # No existing position
        
        # Send webhook to API
        response = client.post('/api/v1/webhooks/tradingview', 
                             json=long_entry_data,
                             headers={"Content-Type": "application/json"})
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'order_id' in response_data
        assert response_data['order_id'] == "mock-order-id-123"
        
        # Verify order placement API call was made correctly
        assert patch_alpaca_api.last_request is not None
        assert patch_alpaca_api.last_request['method'] == 'POST'
        assert patch_alpaca_api.last_request['endpoint'] == '/orders'
        assert patch_alpaca_api.last_request['params']['symbol'] == long_entry_data['symbol']
        assert patch_alpaca_api.last_request['params']['side'] == 'buy'
    
    def test_webhook_to_order_flow_short_entry(self, client, webhook_data, patch_alpaca_api):
        """Test full flow from webhook reception to short entry order execution."""
        # Get test data
        short_entry_data = webhook_data.get("short_entry", {})
        if not short_entry_data:
            pytest.skip("No short entry test data available.")
        
        # Configure mock API response for successful order
        patch_alpaca_api.set_order_response({
            "id": "mock-order-id-456",
            "client_order_id": "test-client-id",
            "status": "filled",
            "symbol": short_entry_data.get("symbol"),
            "type": "market",
            "side": "sell",
            "qty": str(short_entry_data.get("strategy_order_contracts", "0.1")),
            "filled_qty": str(short_entry_data.get("strategy_order_contracts", "0.1")),
            "filled_avg_price": "50000",
            "submitted_at": "2023-05-05T10:00:00Z",
            "filled_at": "2023-05-05T10:00:01Z"
        })
        
        # Also set account and position info
        patch_alpaca_api.set_account_response({
            "equity": "10000",
            "buying_power": "10000",
            "cash": "10000"
        })
        patch_alpaca_api.set_position_response(None)  # No existing position
        
        # Send webhook to API
        response = client.post('/api/v1/webhooks/tradingview', 
                             json=short_entry_data,
                             headers={"Content-Type": "application/json"})
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'order_id' in response_data
        assert response_data['order_id'] == "mock-order-id-456"
        
        # Verify order placement API call was made correctly
        assert patch_alpaca_api.last_request is not None
        assert patch_alpaca_api.last_request['method'] == 'POST'
        assert patch_alpaca_api.last_request['endpoint'] == '/orders'
        assert patch_alpaca_api.last_request['params']['symbol'] == short_entry_data['symbol']
        assert patch_alpaca_api.last_request['params']['side'] == 'sell'
    
    def test_webhook_to_order_flow_long_exit(self, client, webhook_data, patch_alpaca_api):
        """Test full flow from webhook reception to long exit (position closing)."""
        # Get test data
        long_exit_data = webhook_data.get("long_exit", {})
        if not long_exit_data:
            pytest.skip("No long exit test data available.")
        
        # Configure mock API responses
        patch_alpaca_api.set_position_response({
            "symbol": long_exit_data.get("symbol"),
            "qty": "0.1",
            "side": "long",
            "avg_entry_price": "48000",
            "current_price": "50000",
            "unrealized_pl": "200"
        })
        
        patch_alpaca_api.set_close_position_response({
            "symbol": long_exit_data.get("symbol"),
            "status": "closed",
            "side": "long",
            "qty": "0.1",
            "avg_entry_price": "48000",
            "avg_exit_price": "50000",
            "realized_pl": "200"
        })
        
        # Send webhook to API
        response = client.post('/api/v1/webhooks/tradingview', 
                             json=long_exit_data,
                             headers={"Content-Type": "application/json"})
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'message' in response_data
        assert 'closed position' in response_data['message'].lower()
        
        # Verify position was checked and closing API call was made
        assert patch_alpaca_api.last_request is not None
        assert patch_alpaca_api.last_request['method'] == 'DELETE'
        assert long_exit_data['symbol'] in patch_alpaca_api.last_request['endpoint']
    
    def test_webhook_to_order_flow_with_limit_price(self, client, webhook_data, patch_alpaca_api):
        """Test full flow from webhook to limit order execution."""
        # Get test data
        limit_order_data = webhook_data.get("limit_order", {})
        if not limit_order_data:
            pytest.skip("No limit order test data available.")
        
        # Configure mock API response for successful order
        patch_alpaca_api.set_order_response({
            "id": "mock-limit-order-id-789",
            "client_order_id": "test-client-id",
            "status": "new",
            "symbol": limit_order_data.get("symbol"),
            "type": "limit",
            "side": "buy",
            "qty": str(limit_order_data.get("strategy_order_contracts", "0.1")),
            "limit_price": str(limit_order_data.get("strategy_order_price", "45000")),
            "filled_qty": "0",
            "submitted_at": "2023-05-05T10:00:00Z"
        })
        
        # Also set account and position info
        patch_alpaca_api.set_account_response({
            "equity": "10000",
            "buying_power": "10000",
            "cash": "10000"
        })
        
        # Send webhook to API
        response = client.post('/api/v1/webhooks/tradingview', 
                             json=limit_order_data,
                             headers={"Content-Type": "application/json"})
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'order_id' in response_data
        assert response_data['order_id'] == "mock-limit-order-id-789"
        
        # Verify order placement API call was made correctly
        assert patch_alpaca_api.last_request is not None
        assert patch_alpaca_api.last_request['method'] == 'POST'
        assert patch_alpaca_api.last_request['endpoint'] == '/orders'
        assert patch_alpaca_api.last_request['params']['symbol'] == limit_order_data['symbol']
        assert patch_alpaca_api.last_request['params']['type'] == 'limit'
        assert patch_alpaca_api.last_request['params']['limit_price'] == str(limit_order_data['strategy_order_price'])
    
    def test_webhook_to_order_flow_with_api_error(self, client, webhook_data, patch_alpaca_api):
        """Test system handles broker API errors gracefully."""
        # Get test data
        long_entry_data = webhook_data.get("long_entry", {})
        if not long_entry_data:
            pytest.skip("No long entry test data available.")
        
        # Configure mock API to generate an error
        def raise_api_error(*args, **kwargs):
            raise Exception("API Connection Error")
        
        patch_alpaca_api.place_order = raise_api_error
        
        # Send webhook to API
        response = client.post('/api/v1/webhooks/tradingview', 
                             json=long_entry_data,
                             headers={"Content-Type": "application/json"})
        
        # Verify response shows appropriate error
        assert response.status_code == 200  # API still returns 200 with error in response
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'
        assert 'error' in response_data['message'].lower()
    
    def test_invalid_webhook_data(self, client):
        """Test system handles invalid webhook data gracefully."""
        # Send invalid webhook data to API
        response = client.post('/api/v1/webhooks/tradingview', 
                             json={"invalid": "data"},
                             headers={"Content-Type": "application/json"})
        
        # Verify response
        assert response.status_code == 200  # API still returns 200 with error in response
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'
        assert 'missing required fields' in response_data['message'].lower()
    
    def test_webhook_with_risk_validation(self, client, webhook_data, patch_alpaca_api):
        """Test order execution with risk validation."""
        # Get test data
        long_entry_data = webhook_data.get("long_entry", {})
        if not long_entry_data:
            pytest.skip("No long entry test data available.")
        
        # Configure mock API responses
        patch_alpaca_api.set_order_response({
            "id": "mock-order-id-with-risk",
            "client_order_id": "test-client-id",
            "status": "filled",
            "symbol": long_entry_data.get("symbol"),
            "type": "market",
            "side": "buy",
            "qty": str(long_entry_data.get("strategy_order_contracts", "0.1")),
            "filled_qty": str(long_entry_data.get("strategy_order_contracts", "0.1")),
            "filled_avg_price": "50000",
            "submitted_at": "2023-05-05T10:00:00Z",
            "filled_at": "2023-05-05T10:00:01Z"
        })
        
        # Mock the risk validation to simulate approval
        with mock.patch('src.backend.services.risk_manager.RiskManager.validate_order', 
                       return_value=(True, "Order approved by risk manager")):
            
            # Send webhook to API
            response = client.post('/api/v1/webhooks/tradingview', 
                                 json=long_entry_data,
                                 headers={"Content-Type": "application/json"})
            
            # Verify response
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['status'] == 'success'
            assert 'order_id' in response_data
    
    def test_webhook_with_risk_rejection(self, client, webhook_data, patch_alpaca_api):
        """Test order rejection due to risk validation."""
        # Get test data
        long_entry_data = webhook_data.get("long_entry", {})
        if not long_entry_data:
            pytest.skip("No long entry test data available.")
        
        # Mock the risk validation to simulate rejection
        with mock.patch('src.backend.services.risk_manager.RiskManager.validate_order', 
                       return_value=(False, "Order rejected: Position size exceeds risk limits")):
            
            # Send webhook to API
            response = client.post('/api/v1/webhooks/tradingview', 
                                 json=long_entry_data,
                                 headers={"Content-Type": "application/json"})
            
            # Verify response
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['status'] == 'error'
            assert 'rejected' in response_data['message'].lower()
            assert 'risk limits' in response_data['message'].lower()
            
            # Verify no order was placed
            assert not patch_alpaca_api.order_was_placed() 