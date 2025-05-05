"""
Unit tests for paper trading and risk management integration
"""

import unittest
import unittest.mock as mock
import json
import os
import sys
from datetime import datetime

# Add project root to path for imports
import os
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import modules to be tested
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.integration.examples.paper_trading_risk_integration import MockRiskManager


class TestPaperTradingRiskIntegration(unittest.TestCase):
    """Test cases for the paper trading and risk management integration"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create mock environment variables
        self.env_patcher = mock.patch.dict(os.environ, {
            'ALPACA_API_KEY': 'test_api_key',
            'ALPACA_API_SECRET': 'test_api_secret',
            'ALPACA_API_BASE_URL': 'https://paper-api.alpaca.markets'
        })
        self.env_patcher.start()
        
        # Mock the requests library
        self.requests_patcher = mock.patch('src.integration.adapters.paper_trading_adapter.requests')
        self.mock_requests = self.requests_patcher.start()
        
        # Set up mock response for API calls
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'test-order-id', 'status': 'new'}
        self.mock_requests.post.return_value = mock_response
        
        # Create the adapter instance
        self.paper_adapter = PaperTradingAdapter(paper_trading=True)
        
        # Create the risk manager instance
        self.risk_manager = MockRiskManager()
        
        # Setup test data
        self.test_symbol = 'AAPL'
        self.test_price = 150.25
        self.test_order = {
            'symbol': self.test_symbol,
            'qty': 10,
            'side': 'buy',
            'type': 'market',
            'time_in_force': 'day'
        }
    
    def tearDown(self):
        """Clean up after each test"""
        self.env_patcher.stop()
        self.requests_patcher.stop()
    
    def test_risk_validation_approve_order(self):
        """Test that valid orders pass risk validation"""
        # Risk manager should approve this order
        valid, message = self.risk_manager.validate_order(self.test_order)
        
        # Verify order was approved
        self.assertTrue(valid)
        self.assertIsNone(message)
    
    def test_risk_validation_reject_large_order(self):
        """Test that orders exceeding size limits are rejected"""
        # Create an order with excessive size
        large_order = self.test_order.copy()
        large_order['qty'] = 1000  # Large quantity
        
        # Risk manager should reject this order
        valid, message = self.risk_manager.validate_order(large_order)
        
        # Verify order was rejected
        self.assertFalse(valid)
        self.assertIn("size exceeds", message.lower())
    
    def test_risk_validation_reject_high_value_order(self):
        """Test that orders exceeding value limits are rejected"""
        # Update the test price to create a high-value order
        self.risk_manager.last_prices[self.test_symbol] = 5000.0  # High price
        
        # Risk manager should reject this order due to high value
        valid, message = self.risk_manager.validate_order(self.test_order)
        
        # Verify order was rejected
        self.assertFalse(valid)
        self.assertIn("value exceeds", message.lower())
    
    def test_stop_loss_trigger(self):
        """Test that stop losses are triggered correctly"""
        # Create a position
        self.risk_manager.record_position(
            symbol=self.test_symbol,
            qty=10,
            entry_price=100.0,  # Entry price
            side="long"
        )
        
        # Get the position
        position = self.risk_manager.positions[self.test_symbol]
        
        # Verify stop price is set correctly (2% below entry based on default)
        expected_stop = 100.0 * 0.98
        self.assertAlmostEqual(position['stop_price'], expected_stop, places=4)
        
        # Test with price above stop - should not trigger
        actions = self.risk_manager.process_market_data(self.test_symbol, 99.0)
        self.assertEqual(len(actions), 0)
        
        # Test with price below stop - should trigger
        actions = self.risk_manager.process_market_data(self.test_symbol, 97.0)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'stop_loss')
        self.assertEqual(actions[0]['symbol'], self.test_symbol)
        self.assertEqual(actions[0]['qty'], 10)
    
    def test_take_profit_trigger(self):
        """Test that take profits are triggered correctly"""
        # Create a position
        self.risk_manager.record_position(
            symbol=self.test_symbol,
            qty=10,
            entry_price=100.0,  # Entry price
            side="long"
        )
        
        # Get the position
        position = self.risk_manager.positions[self.test_symbol]
        
        # Verify take profit price is set correctly (5% above entry based on default)
        expected_target = 100.0 * 1.05
        self.assertAlmostEqual(position['take_profit_price'], expected_target, places=4)
        
        # Test with price below target - should not trigger
        actions = self.risk_manager.process_market_data(self.test_symbol, 104.0)
        self.assertEqual(len(actions), 0)
        
        # Test with price above target - should trigger
        actions = self.risk_manager.process_market_data(self.test_symbol, 106.0)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'take_profit')
        self.assertEqual(actions[0]['symbol'], self.test_symbol)
        self.assertEqual(actions[0]['qty'], 10)
    
    def test_paper_trading_order_submission(self):
        """Test that orders can be submitted through paper trading"""
        # Submit a test order
        result = self.paper_adapter.submit_order(self.test_order)
        
        # Verify order was submitted correctly
        self.mock_requests.post.assert_called_once()
        self.assertEqual(result['id'], 'test-order-id')
        self.assertEqual(result['status'], 'new')
        
        # Verify URL and authorization
        args, kwargs = self.mock_requests.post.call_args
        self.assertIn('/v2/orders', args[0])  # URL should include orders endpoint
        self.assertIn('Authorization', kwargs['headers'])  # Should include auth header
    
    def test_end_to_end_risk_trigger_trading(self):
        """Test the end-to-end flow from risk trigger to order execution"""
        # Mock paper trading adapter's submit_order method
        self.paper_adapter.submit_order = mock.MagicMock()
        self.paper_adapter.submit_order.return_value = {'id': 'test-order-id'}
        
        # Create a position
        self.risk_manager.record_position(
            symbol=self.test_symbol,
            qty=10,
            entry_price=100.0,
            side="long"
        )
        
        # Trigger a stop loss by sending a price update
        trigger_price = 97.0  # Below stop price
        actions = self.risk_manager.process_market_data(self.test_symbol, trigger_price)
        
        # Verify stop loss was triggered
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'stop_loss')
        
        # Execute the stop loss order
        for action in actions:
            if action['action'] == 'stop_loss':
                order = {
                    'symbol': action['symbol'],
                    'qty': action['qty'],
                    'side': 'sell',
                    'type': 'market',
                    'time_in_force': 'day'
                }
                self.paper_adapter.submit_order(order)
        
        # Verify order was submitted
        self.paper_adapter.submit_order.assert_called_once()
        order_args = self.paper_adapter.submit_order.call_args[0][0]
        self.assertEqual(order_args['symbol'], self.test_symbol)
        self.assertEqual(order_args['qty'], 10)
        self.assertEqual(order_args['side'], 'sell')


if __name__ == '__main__':
    unittest.main() 