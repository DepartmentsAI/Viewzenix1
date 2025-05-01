"""
Unit tests for the RiskManager service.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time

from src.backend.services.risk_manager import RiskManager
from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.broker_adapter import BrokerAdapter

class TestRiskManager(unittest.TestCase):
    """
    Test suite for the RiskManager class.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_broker = Mock(spec=BrokerAdapter)
        self.mock_order_engine = Mock(spec=OrderEngine)
        
        # Mock account info
        self.mock_broker.get_account_info.return_value = {
            'equity': '10000',
            'buying_power': '20000'
        }
        
        # Mock current price
        self.mock_broker.get_current_price.return_value = 100.0
        
        # Set up RiskManager with mocks
        self.risk_manager = RiskManager(
            broker_adapter=self.mock_broker,
            order_engine=self.mock_order_engine
        )
    
    def test_initialization(self):
        """Test RiskManager initialization."""
        # Verify init called get_account_info
        self.mock_broker.get_account_info.assert_called_once()
        
        # Verify default risk parameters
        params = self.risk_manager.get_risk_parameters()
        self.assertEqual(params['stop_loss_percent'], 0.02)
        self.assertEqual(params['take_profit_percent'], 0.05)
        self.assertEqual(params['max_position_size_percent'], 0.05)
        self.assertEqual(params['max_daily_drawdown_percent'], 0.05)
        self.assertEqual(params['max_open_positions'], 10)
        self.assertEqual(params['orphaned_order_age_hours'], 24)
    
    def test_update_risk_parameters(self):
        """Test updating risk parameters."""
        # Update parameters
        new_params = {
            'stop_loss_percent': 0.03,
            'take_profit_percent': 0.1,
            'max_open_positions': 5
        }
        
        updated = self.risk_manager.update_risk_parameters(new_params)
        
        # Verify parameters were updated
        self.assertEqual(updated['stop_loss_percent'], 0.03)
        self.assertEqual(updated['take_profit_percent'], 0.1)
        self.assertEqual(updated['max_open_positions'], 5)
        
        # Verify unchanged parameters remain default
        self.assertEqual(updated['max_position_size_percent'], 0.05)
        self.assertEqual(updated['max_daily_drawdown_percent'], 0.05)
        self.assertEqual(updated['orphaned_order_age_hours'], 24)
    
    def test_update_risk_parameters_invalid_values(self):
        """Test updating risk parameters with invalid values."""
        # Update with invalid values
        new_params = {
            'stop_loss_percent': 1.5,  # > 1 is invalid
            'take_profit_percent': -0.1,  # < 0 is invalid
            'max_open_positions': 0,  # 0 is invalid
            'unknown_param': 'test'  # Unknown parameter
        }
        
        updated = self.risk_manager.update_risk_parameters(new_params)
        
        # Verify invalid parameters were not updated
        self.assertEqual(updated['stop_loss_percent'], 0.02)  # Still default
        self.assertEqual(updated['take_profit_percent'], 0.05)  # Still default
        self.assertEqual(updated['max_open_positions'], 10)  # Still default
        self.assertNotIn('unknown_param', updated)  # Not added
    
    def test_process_order_with_risk_management_success(self):
        """Test processing an order with risk management that succeeds."""
        # Mock successful order result
        self.mock_order_engine.process_webhook_data.return_value = {
            'status': 'success',
            'order_id': 'test123',
            'message': 'Order executed successfully'
        }
        
        # Mock empty positions list (no position limit hit)
        self.mock_broker.get_positions.return_value = []
        
        # Create test order data
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 150.0,
            'strategy_order_comment': 'Test order',
            'time': int(time.time()),
            'stop_loss': {
                'percent': 0.02
            },
            'take_profit': {
                'percent': 0.05
            }
        }
        
        # Process the order
        result = self.risk_manager.process_order_with_risk_management(order_data)
        
        # Verify the result
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['risk_applied'])
        
        # Verify original order was processed
        self.mock_order_engine.process_webhook_data.assert_called_with(order_data)
        
        # Verify stop loss and take profit orders were added
        # Process_webhook_data should be called 3 times (original order + SL + TP)
        self.assertEqual(self.mock_order_engine.process_webhook_data.call_count, 3)
    
    def test_portfolio_limit_rejection(self):
        """Test order rejection due to portfolio limits."""
        # Mock positions list with max positions
        self.mock_broker.get_positions.return_value = [{}] * 10  # 10 positions
        
        # Create test order data for a new position
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 150.0,
            'time': int(time.time())
        }
        
        # Process the order
        result = self.risk_manager.process_order_with_risk_management(order_data)
        
        # Verify the order was rejected
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('portfolio limits', result['message'])
        
        # Verify order engine was not called
        self.mock_order_engine.process_webhook_data.assert_not_called()
    
    def test_position_size_limit_rejection(self):
        """Test order rejection due to position size limits."""
        # Mock empty positions list
        self.mock_broker.get_positions.return_value = []
        
        # Create test order data with very high price
        order_data = {
            'symbol': 'TSLA',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 1000.0,  # High price
            'quantity': 10,  # Multiple shares
            'time': int(time.time())
        }
        
        # Process the order
        result = self.risk_manager.process_order_with_risk_management(order_data)
        
        # Verify the order was rejected (order value > 5% of equity)
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('portfolio limits', result['message'])
        
        # Verify order engine was not called
        self.mock_order_engine.process_webhook_data.assert_not_called()
    
    def test_drawdown_limit_rejection(self):
        """Test order rejection due to drawdown limits."""
        # Mock broker account info for drawdown test
        self.mock_broker.get_account_info.return_value = {
            'equity': '9500',  # Current equity reduced from initial 10000
            'buying_power': '19000'
        }
        
        # Manually set daily performance to simulate drawdown
        self.risk_manager.daily_performance['start_equity'] = 10000
        self.risk_manager.daily_performance['current_equity'] = 9500
        
        # Set drawdown limit to 2% (below our current 5% drawdown)
        self.risk_manager.risk_params['max_daily_drawdown_percent'] = 0.02
        
        # Create test order data
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 150.0,
            'time': int(time.time())
        }
        
        # Process the order
        result = self.risk_manager.process_order_with_risk_management(order_data)
        
        # Verify the order was rejected
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('drawdown limit', result['message'])
        
        # Verify order engine was not called
        self.mock_order_engine.process_webhook_data.assert_not_called()
    
    def test_sell_order_bypass_portfolio_limits(self):
        """Test that sell orders bypass portfolio limits."""
        # Create test order data for a sell order
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'sell',  # Sell order
            'strategy_order_price': 150.0,
            'time': int(time.time())
        }
        
        # Set up order engine to return success
        self.mock_order_engine.process_webhook_data.return_value = {
            'status': 'success',
            'order_id': 'test123',
            'message': 'Order executed successfully'
        }
        
        # Process the order
        result = self.risk_manager.process_order_with_risk_management(order_data)
        
        # Verify the order was processed (not rejected by limits)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['risk_applied'], False)  # No risk for sell orders
        
        # Verify order engine was called once
        self.mock_order_engine.process_webhook_data.assert_called_once_with(order_data)
    
    def test_add_stop_loss_take_profit_with_explicit_price(self):
        """Test adding stop loss and take profit orders with explicit prices."""
        # Setup
        symbol = 'AAPL'
        entry_price = 150.0
        parent_order_id = 'test123'
        stop_loss_param = {'price': 145.0}  # Explicit price
        take_profit_param = {'price': 160.0}  # Explicit price
        
        # Set up order engine to return success for SL/TP orders
        self.mock_order_engine.process_webhook_data.side_effect = [
            {'status': 'success', 'order_id': 'sl_test123'},  # SL order
            {'status': 'success', 'order_id': 'tp_test123'}   # TP order
        ]
        
        # Call the method
        result = self.risk_manager._add_stop_loss_take_profit(
            symbol, entry_price, parent_order_id, stop_loss_param, take_profit_param
        )
        
        # Verify results
        self.assertIsNotNone(result['stop_loss'])
        self.assertIsNotNone(result['take_profit'])
        
        # Verify order engine called twice with correct parameters
        self.assertEqual(self.mock_order_engine.process_webhook_data.call_count, 2)
        
        # Check SL order params
        sl_call_args = self.mock_order_engine.process_webhook_data.call_args_list[0][0][0]
        self.assertEqual(sl_call_args['symbol'], symbol)
        self.assertEqual(sl_call_args['strategy_order_price'], 145.0)
        self.assertEqual(sl_call_args['strategy_order_action'], 'sell')
        self.assertEqual(sl_call_args['order_type'], 'stop')
        
        # Check TP order params
        tp_call_args = self.mock_order_engine.process_webhook_data.call_args_list[1][0][0]
        self.assertEqual(tp_call_args['symbol'], symbol)
        self.assertEqual(tp_call_args['strategy_order_price'], 160.0)
        self.assertEqual(tp_call_args['strategy_order_action'], 'sell')
        self.assertEqual(tp_call_args['order_type'], 'limit')
    
    def test_add_stop_loss_take_profit_with_percentages(self):
        """Test adding stop loss and take profit orders with percentages."""
        # Setup
        symbol = 'AAPL'
        entry_price = 100.0  # Simple price for easy percentage calculation
        parent_order_id = 'test123'
        stop_loss_param = {'percent': 0.05}  # 5% below
        take_profit_param = {'percent': 0.1}  # 10% above
        
        # Set up order engine to return success for SL/TP orders
        self.mock_order_engine.process_webhook_data.side_effect = [
            {'status': 'success', 'order_id': 'sl_test123'},  # SL order
            {'status': 'success', 'order_id': 'tp_test123'}   # TP order
        ]
        
        # Call the method
        result = self.risk_manager._add_stop_loss_take_profit(
            symbol, entry_price, parent_order_id, stop_loss_param, take_profit_param
        )
        
        # Verify results
        self.assertIsNotNone(result['stop_loss'])
        self.assertIsNotNone(result['take_profit'])
        
        # Verify order engine called twice with correct parameters
        self.assertEqual(self.mock_order_engine.process_webhook_data.call_count, 2)
        
        # Check SL order params
        sl_call_args = self.mock_order_engine.process_webhook_data.call_args_list[0][0][0]
        self.assertEqual(sl_call_args['symbol'], symbol)
        self.assertEqual(sl_call_args['strategy_order_price'], 95.0)  # 5% below 100
        self.assertEqual(sl_call_args['strategy_order_action'], 'sell')
        
        # Check TP order params
        tp_call_args = self.mock_order_engine.process_webhook_data.call_args_list[1][0][0]
        self.assertEqual(tp_call_args['symbol'], symbol)
        self.assertEqual(tp_call_args['strategy_order_price'], 110.0)  # 10% above 100
        self.assertEqual(tp_call_args['strategy_order_action'], 'sell')
    
    def test_cleanup_orphaned_orders(self):
        """Test cleanup of orphaned orders."""
        # Mock current time
        current_time = datetime.now()
        
        # Mock open orders with some old and some new
        old_time = (current_time - timedelta(hours=30)).isoformat() + 'Z'
        new_time = (current_time - timedelta(hours=5)).isoformat() + 'Z'
        
        mock_orders = [
            {'id': 'order1', 'created_at': old_time, 'type': 'limit'},  # Old, should be cancelled
            {'id': 'order2', 'created_at': old_time, 'type': 'stop'},   # Old, should be cancelled
            {'id': 'order3', 'created_at': new_time, 'type': 'limit'},  # New, should be kept
            {'id': 'order4', 'created_at': old_time, 'type': 'market'}  # Market order, should be kept
        ]
        
        self.mock_broker.get_open_orders.return_value = mock_orders
        
        # Mock successful cancellation
        self.mock_broker.cancel_order.return_value = True
        
        # Call cleanup
        result = self.risk_manager.cleanup_orphaned_orders()
        
        # Verify results
        self.assertEqual(result['orders_checked'], 4)
        self.assertEqual(result['orders_cancelled'], 2)
        self.assertEqual(len(result['cancelled_ids']), 2)
        self.assertIn('order1', result['cancelled_ids'])
        self.assertIn('order2', result['cancelled_ids'])
        
        # Verify broker cancel_order called twice
        self.assertEqual(self.mock_broker.cancel_order.call_count, 2)
    
    def test_get_risk_metrics(self):
        """Test getting risk metrics."""
        # Mock positions
        mock_positions = [
            {'market_value': '2000'},
            {'market_value': '3000'}
        ]
        self.mock_broker.get_positions.return_value = mock_positions
        
        # Set daily performance values
        self.risk_manager.daily_performance = {
            'start_equity': 10000.0,
            'current_equity': 9500.0,
            'max_equity': 10200.0,
            'min_equity': 9400.0,
            'last_updated': datetime.now(),
            'reset_time': datetime.now() + timedelta(days=1)
        }
        
        # Get metrics
        metrics = self.risk_manager.get_risk_metrics()
        
        # Verify metrics structure and values
        self.assertEqual(metrics['account']['equity'], 9500.0)
        self.assertEqual(metrics['account']['buying_power'], 20000.0)
        
        self.assertEqual(metrics['positions']['count'], 2)
        self.assertEqual(metrics['positions']['value'], 5000.0)
        self.assertAlmostEqual(metrics['positions']['exposure_percent'], 5000.0/9500.0)
        self.assertEqual(metrics['positions']['max_positions'], 10)
        
        self.assertEqual(metrics['daily_performance']['start_equity'], 10000.0)
        self.assertEqual(metrics['daily_performance']['current_equity'], 9500.0)
        self.assertEqual(metrics['daily_performance']['max_equity'], 10200.0)
        self.assertEqual(metrics['daily_performance']['min_equity'], 9400.0)
        self.assertAlmostEqual(metrics['daily_performance']['drawdown'], 0.05)  # 5% drawdown
        
        self.assertEqual(metrics['risk_limits']['max_position_size'], 475.0)  # 5% of 9500
        
if __name__ == '__main__':
    unittest.main() 