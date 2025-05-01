"""
Unit tests for the Risk API endpoints.
"""
import unittest
import json
from unittest.mock import patch, MagicMock
from flask import Flask

from src.backend.api.risk import risk_bp, risk_manager

class TestRiskApi(unittest.TestCase):
    """
    Test suite for the Risk API endpoints.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create Flask test app
        self.app = Flask(__name__)
        self.app.register_blueprint(risk_bp, url_prefix='/api')
        self.client = self.app.test_client()
        
        # Default risk parameters for testing
        self.default_risk_params = {
            'sl_tp': {
                'enabled': True,
                'stop_loss_percent': 0.02,
                'take_profit_percent': 0.05,
                'use_fixed_price': False,
                'fixed_stop_loss_price': None,
                'fixed_take_profit_price': None,
                'use_fill_price_for_sl_tp': True
            },
            'portfolio': {
                'enabled': True,
                'max_position_size_percent': 0.05,
                'max_daily_drawdown_percent': 0.05,
                'max_open_positions': 10
            },
            'cleanup': {
                'enabled': True,
                'orphaned_order_age_hours': 24
            }
        }
        
        # Sample risk metrics
        self.sample_metrics = {
            'current_equity': 10000.0,
            'starting_equity': 10000.0,
            'current_drawdown_percent': 0.02,
            'open_position_count': 2,
            'total_exposure_percent': 0.5,
            'position_sizes': [0.3, 0.2],
            'last_updated': 1620000000.0
        }
    
    @patch('src.backend.api.risk.risk_manager')
    def test_get_risk_parameters(self, mock_risk_manager):
        """Test GET /api/risk/parameters endpoint."""
        # Mock risk_manager.get_risk_parameters
        mock_risk_manager.get_risk_parameters.return_value = self.default_risk_params
        
        # Make request
        response = self.client.get('/api/risk/parameters')
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['parameters'], self.default_risk_params)
        
        # Verify risk_manager method was called
        mock_risk_manager.get_risk_parameters.assert_called_once()
    
    @patch('src.backend.api.risk.risk_manager')
    def test_get_risk_parameters_error(self, mock_risk_manager):
        """Test GET /api/risk/parameters endpoint error handling."""
        # Mock risk_manager to raise exception
        mock_risk_manager.get_risk_parameters.side_effect = Exception("Test error")
        
        # Make request
        response = self.client.get('/api/risk/parameters')
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Test error', data['message'])
    
    @patch('src.backend.api.risk.risk_manager')
    def test_update_risk_parameters_success(self, mock_risk_manager):
        """Test PUT /api/risk/parameters endpoint success."""
        # New parameters to update
        new_params = {
            'sl_tp': {
                'stop_loss_percent': 0.03,
                'take_profit_percent': 0.07
            }
        }
        
        # Updated parameters (merged with defaults)
        updated_params = self.default_risk_params.copy()
        updated_params['sl_tp']['stop_loss_percent'] = 0.03
        updated_params['sl_tp']['take_profit_percent'] = 0.07
        
        # Mock risk_manager.update_risk_parameters
        mock_risk_manager.update_risk_parameters.return_value = updated_params
        
        # Make request
        response = self.client.put(
            '/api/risk/parameters',
            data=json.dumps(new_params),
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['parameters'], updated_params)
        
        # Verify risk_manager method was called with correct params
        mock_risk_manager.update_risk_parameters.assert_called_once_with(new_params)
    
    @patch('src.backend.api.risk.risk_manager')
    def test_update_risk_parameters_invalid_json(self, mock_risk_manager):
        """Test PUT /api/risk/parameters with invalid JSON."""
        # Make request with invalid JSON
        response = self.client.put(
            '/api/risk/parameters',
            data='invalid json',
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid JSON format', data['error'])
        
        # Verify risk_manager method was not called
        mock_risk_manager.update_risk_parameters.assert_not_called()
    
    @patch('src.backend.api.risk.validate')
    @patch('src.backend.api.risk.risk_manager')
    def test_update_risk_parameters_validation_error(self, mock_risk_manager, mock_validate):
        """Test PUT /api/risk/parameters with schema validation error."""
        # Invalid parameters (stop_loss_percent > 1)
        invalid_params = {
            'sl_tp': {
                'stop_loss_percent': 1.5  # Invalid: must be <= 1
            }
        }
        
        # Mock validate to raise ValidationError
        from jsonschema import ValidationError
        mock_validate.side_effect = ValidationError("Invalid schema")
        
        # Make request
        response = self.client.put(
            '/api/risk/parameters',
            data=json.dumps(invalid_params),
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Invalid payload schema', data['message'])
        
        # Verify risk_manager method was not called
        mock_risk_manager.update_risk_parameters.assert_not_called()
    
    @patch('src.backend.api.risk.risk_manager')
    def test_update_risk_parameters_error(self, mock_risk_manager):
        """Test PUT /api/risk/parameters endpoint error handling."""
        # New parameters to update
        new_params = {
            'sl_tp': {
                'stop_loss_percent': 0.03,
                'take_profit_percent': 0.07
            }
        }
        
        # Mock risk_manager to raise exception
        mock_risk_manager.update_risk_parameters.side_effect = Exception("Test error")
        
        # Make request
        response = self.client.put(
            '/api/risk/parameters',
            data=json.dumps(new_params),
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Test error', data['message'])
    
    @patch('src.backend.api.risk.risk_manager')
    def test_get_risk_metrics(self, mock_risk_manager):
        """Test GET /api/risk/metrics endpoint."""
        # Mock risk_manager.get_risk_metrics
        mock_risk_manager.get_risk_metrics.return_value = self.sample_metrics
        
        # Make request
        response = self.client.get('/api/risk/metrics')
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['metrics'], self.sample_metrics)
        
        # Verify risk_manager method was called
        mock_risk_manager.get_risk_metrics.assert_called_once()
    
    @patch('src.backend.api.risk.risk_manager')
    def test_get_risk_metrics_error(self, mock_risk_manager):
        """Test GET /api/risk/metrics endpoint error handling."""
        # Mock risk_manager to raise exception
        mock_risk_manager.get_risk_metrics.side_effect = Exception("Test error")
        
        # Make request
        response = self.client.get('/api/risk/metrics')
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Test error', data['message'])
    
    @patch('src.backend.api.risk.risk_manager')
    def test_cleanup_orphaned_orders(self, mock_risk_manager):
        """Test POST /api/risk/cleanup endpoint."""
        # Mock risk_manager.cleanup_orphaned_orders
        cleanup_result = {
            'status': 'success',
            'message': 'Cleaned up 3 orphaned orders',
            'orders_cancelled': 3,
            'order_ids': ['order1', 'order2', 'order3']
        }
        mock_risk_manager.cleanup_orphaned_orders.return_value = cleanup_result
        
        # Make request
        response = self.client.post('/api/risk/cleanup')
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['results'], cleanup_result)
        
        # Verify risk_manager method was called
        mock_risk_manager.cleanup_orphaned_orders.assert_called_once()
    
    @patch('src.backend.api.risk.risk_manager')
    def test_cleanup_orphaned_orders_error(self, mock_risk_manager):
        """Test POST /api/risk/cleanup endpoint error handling."""
        # Mock risk_manager to raise exception
        mock_risk_manager.cleanup_orphaned_orders.side_effect = Exception("Test error")
        
        # Make request
        response = self.client.post('/api/risk/cleanup')
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Test error', data['message'])
    
    @patch('src.backend.api.risk.risk_manager')
    def test_process_webhook_with_risk_success(self, mock_risk_manager):
        """Test POST /api/risk/webhook endpoint with successful order."""
        # Sample webhook data
        webhook_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': '150.0',
            'strategy_order_contracts': '10'
        }
        
        # Mock successful order result
        success_result = {
            'status': 'success',
            'message': 'Order executed with risk management',
            'order_result': {
                'order_id': 'test_order_123',
                'status': 'success',
                'message': 'Order executed successfully',
                'sl_tp_orders': [
                    {'type': 'stop_loss', 'order_id': 'sl_123', 'price': 147.0},
                    {'type': 'take_profit', 'order_id': 'tp_123', 'price': 157.5}
                ],
                'sl_tp_status': 'success'
            },
            'risk_applied': True,
            'risk_metrics': self.sample_metrics
        }
        mock_risk_manager.process_order_with_risk_management.return_value = success_result
        
        # Make request
        response = self.client.post(
            '/api/risk/webhook',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['order_result']['order_id'], 'test_order_123')
        self.assertEqual(data['risk_applied'], True)
        
        # Verify risk_manager method was called with webhook data
        mock_risk_manager.process_order_with_risk_management.assert_called_once_with(webhook_data)
    
    @patch('src.backend.api.risk.risk_manager')
    def test_process_webhook_with_risk_rejected(self, mock_risk_manager):
        """Test POST /api/risk/webhook endpoint with rejected order."""
        # Sample webhook data
        webhook_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': '150.0',
            'strategy_order_contracts': '1000'  # Very large order that should be rejected
        }
        
        # Mock rejected order result
        rejected_result = {
            'status': 'rejected',
            'message': 'Order rejected due to portfolio limits',
            'order_data': webhook_data,
            'risk_metrics': self.sample_metrics
        }
        mock_risk_manager.process_order_with_risk_management.return_value = rejected_result
        
        # Make request
        response = self.client.post(
            '/api/risk/webhook',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)  # Still 200 even for rejected orders
        self.assertEqual(data['status'], 'rejected')
        self.assertEqual(data['message'], 'Order rejected due to portfolio limits')
        
        # Verify risk_manager method was called with webhook data
        mock_risk_manager.process_order_with_risk_management.assert_called_once_with(webhook_data)
    
    @patch('src.backend.api.risk.risk_manager')
    def test_process_webhook_with_risk_invalid_json(self, mock_risk_manager):
        """Test POST /api/risk/webhook with invalid JSON."""
        # Make request with invalid JSON
        response = self.client.post(
            '/api/risk/webhook',
            data='invalid json',
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid JSON format', data['error'])
        
        # Verify risk_manager method was not called
        mock_risk_manager.process_order_with_risk_management.assert_not_called()
    
    @patch('src.backend.api.risk.risk_manager')
    def test_process_webhook_with_risk_error(self, mock_risk_manager):
        """Test POST /api/risk/webhook endpoint error handling."""
        # Sample webhook data
        webhook_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': '150.0',
            'strategy_order_contracts': '10'
        }
        
        # Mock risk_manager to raise exception
        mock_risk_manager.process_order_with_risk_management.side_effect = Exception("Test error")
        
        # Make request
        response = self.client.post(
            '/api/risk/webhook',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Error processing webhook with risk management', data['message'])
        
        # Verify risk_manager method was called with webhook data
        mock_risk_manager.process_order_with_risk_management.assert_called_once_with(webhook_data)


if __name__ == '__main__':
    unittest.main()
