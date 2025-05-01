"""
Unit tests for the RiskManager service.
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import os
from datetime import datetime, timedelta
import time

from src.backend.services.risk_manager import RiskManager
from src.backend.models.risk_models import RiskParameters, RiskMetrics
from src.integration.adapters.broker_adapter import BrokerAdapter

class TestRiskManager(unittest.TestCase):
    """Test cases for the RiskManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock broker adapter
        self.mock_broker = MagicMock(spec=BrokerAdapter)
        
        # Set up mock account info
        self.mock_broker.get_account_info.return_value = {
            'equity': '10000.0',
            'buying_power': '20000.0',
            'cash': '10000.0'
        }
        
        # Set up mock positions
        self.mock_broker.get_positions.return_value = []
        
        # Create risk manager with mock broker
        self.risk_manager = RiskManager(broker_adapter=self.mock_broker)

    def test_initialize_risk_metrics(self):
        """Test the initialization of risk metrics."""
        # Arrange
        self.mock_broker.get_account_info.return_value = {
            'equity': '15000.0'
        }
        
        # Act
        self.risk_manager._initialize_risk_metrics()
        
        # Assert
        self.assertEqual(self.risk_manager.risk_metrics.current_equity, 15000.0)
        self.assertEqual(self.risk_manager.risk_metrics.starting_equity, 15000.0)
        self.mock_broker.get_account_info.assert_called_once()
        self.mock_broker.get_positions.assert_called_once()

    def test_update_risk_parameters(self):
        """Test updating risk parameters."""
        # Arrange
        new_parameters = {
            "sl_tp": {
                "stop_loss_percent": 0.03,
                "take_profit_percent": 0.06
            },
            "portfolio": {
                "max_daily_drawdown_percent": 0.10,
                "max_open_positions": 15
            }
        }
        
        # Act
        result = self.risk_manager.update_risk_parameters(new_parameters)
        
        # Assert
        self.assertEqual(self.risk_manager.risk_parameters.sl_tp.stop_loss_percent, 0.03)
        self.assertEqual(self.risk_manager.risk_parameters.sl_tp.take_profit_percent, 0.06)
        self.assertEqual(self.risk_manager.risk_parameters.portfolio.max_daily_drawdown_percent, 0.10)
        self.assertEqual(self.risk_manager.risk_parameters.portfolio.max_open_positions, 15)
        
        # Verify default values are maintained for fields not specified
        self.assertEqual(self.risk_manager.risk_parameters.sl_tp.enabled, True)
        self.assertEqual(self.risk_manager.risk_parameters.cleanup.orphaned_order_age_hours, 24)

    def test_check_portfolio_limits_max_positions(self):
        """Test portfolio limits check for maximum positions."""
        # Arrange
        self.mock_broker.get_positions.return_value = [
            {'symbol': 'AAPL'}, {'symbol': 'MSFT'}, {'symbol': 'GOOG'}
        ]
        self.risk_manager.risk_metrics.open_position_count = 3
        self.risk_manager.risk_parameters.portfolio.max_open_positions = 3
        
        order_data = {
            'symbol': 'AMZN',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': '100.0'
        }
        
        # Act
        result = self.risk_manager._check_portfolio_limits(order_data)
        
        # Assert
        self.assertFalse(result)

    def test_check_portfolio_limits_position_size(self):
        """Test portfolio limits check for position size."""
        # Arrange
        self.risk_manager.risk_metrics.current_equity = 10000.0
        self.risk_manager.risk_parameters.portfolio.max_position_size_percent = 0.05
        
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': '100.0',
            'strategy_order_contracts': '10.0'  # 100 * 10 = 1000 (10% of equity)
        }
        
        # Act
        result = self.risk_manager._check_portfolio_limits(order_data)
        
        # Assert
        self.assertFalse(result)

    def test_check_drawdown_limits(self):
        """Test drawdown limits checking."""
        # Arrange
        self.risk_manager.risk_metrics.starting_equity = 10000.0
        self.risk_manager.risk_metrics.current_equity = 9000.0  # 10% drawdown
        self.risk_manager.risk_parameters.portfolio.max_daily_drawdown_percent = 0.05  # 5% limit
        
        # Act
        result = self.risk_manager._check_drawdown_limits()
        
        # Assert
        self.assertFalse(result)
        self.assertEqual(self.risk_manager.risk_metrics.current_drawdown_percent, 0.1)

    def test_process_order_with_risk_management_rejected_portfolio_limits(self):
        """Test order processing when portfolio limits are exceeded."""
        # Arrange
        self.risk_manager._check_portfolio_limits = MagicMock(return_value=False)
        
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': '100.0'
        }
        
        # Act
        result = self.risk_manager.process_order_with_risk_management(order_data)
        
        # Assert
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('portfolio limits', result['message'])
        self.assertEqual(result['order_data'], order_data)

    def test_process_order_with_risk_management_success(self):
        """Test successful order processing with risk management."""
        # Arrange
        self.risk_manager._check_portfolio_limits = MagicMock(return_value=True)
        self.risk_manager._check_drawdown_limits = MagicMock(return_value=True)
        
        mock_order_result = {
            'status': 'success',
            'order_id': 'test_order_123',
            'message': 'Order executed successfully'
        }
        self.risk_manager.order_engine.process_webhook_data = MagicMock(return_value=mock_order_result)
        
        self.risk_manager._add_stop_loss_take_profit = MagicMock(return_value={
            'status': 'success',
            'orders': [
                {'type': 'stop_loss', 'order_id': 'sl_123', 'price': 95.0},
                {'type': 'take_profit', 'order_id': 'tp_123', 'price': 105.0}
            ]
        })
        
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': '100.0'
        }
        
        # Act
        result = self.risk_manager.process_order_with_risk_management(order_data)
        
        # Assert
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['order_result'], mock_order_result)
        self.assertEqual(result['risk_applied'], True)
        self.assertIn('risk_metrics', result)

    def test_add_stop_loss_take_profit(self):
        """Test adding stop loss and take profit orders."""
        # Arrange
        symbol = 'AAPL'
        entry_price = 100.0
        parent_order_id = 'parent_123'
        sl_tp_params = {
            'stop_loss_percent': 0.05,
            'take_profit_percent': 0.10,
            'use_fixed_price': False,
            'use_fill_price_for_sl_tp': False
        }
        
        # Mock get_position to return a long position with 10 shares
        self.mock_broker.get_position.return_value = {
            'symbol': 'AAPL',
            'qty': '10.0',
            'avg_entry_price': '100.0'
        }
        
        # Mock place_order to simulate successful orders
        self.mock_broker.place_order.side_effect = [
            {'id': 'sl_123', 'status': 'new'},
            {'id': 'tp_123', 'status': 'new'}
        ]
        
        # Act
        result = self.risk_manager._add_stop_loss_take_profit(
            symbol, entry_price, parent_order_id, sl_tp_params
        )
        
        # Assert
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['orders']), 2)
        
        # Verify SL parameters
        sl_call_args = self.mock_broker.place_order.call_args_list[0][1]
        self.assertEqual(sl_call_args['symbol'], 'AAPL')
        self.assertEqual(sl_call_args['qty'], 10.0)
        self.assertEqual(sl_call_args['side'], 'sell')
        self.assertEqual(sl_call_args['type'], 'stop')
        self.assertEqual(sl_call_args['stop_price'], 95.0)  # 100.0 * (1 - 0.05)
        
        # Verify TP parameters
        tp_call_args = self.mock_broker.place_order.call_args_list[1][1]
        self.assertEqual(tp_call_args['symbol'], 'AAPL')
        self.assertEqual(tp_call_args['qty'], 10.0)
        self.assertEqual(tp_call_args['side'], 'sell')
        self.assertEqual(tp_call_args['type'], 'limit')
        self.assertEqual(tp_call_args['limit_price'], 110.0)  # 100.0 * (1 + 0.10)

    def test_cleanup_orphaned_orders(self):
        """Test cleanup of orphaned orders."""
        # Arrange
        # Empty positions list means no active positions
        self.mock_broker.get_positions.return_value = []
        
        # Set up mock orders with some having SL/TP in their client_order_id
        self.mock_broker.get_orders.return_value = [
            {'id': 'order1', 'client_order_id': 'normal_order', 'symbol': 'AAPL'},
            {'id': 'order2', 'client_order_id': 'parent-sl-123', 'symbol': 'MSFT', 'created_at': '2023-01-01T00:00:00Z'},
            {'id': 'order3', 'client_order_id': 'parent-tp-456', 'symbol': 'GOOG', 'created_at': '2023-01-01T00:00:00Z'}
        ]
        
        # Act
        result = self.risk_manager.cleanup_orphaned_orders()
        
        # Assert
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['orders_cancelled'], 2)
        self.assertEqual(len(result['order_ids']), 2)
        self.assertIn('order2', result['order_ids'])
        self.assertIn('order3', result['order_ids'])
        
        # Verify cancel_order was called for the orphaned orders
        self.mock_broker.cancel_order.assert_any_call('order2')
        self.mock_broker.cancel_order.assert_any_call('order3')

if __name__ == '__main__':
    unittest.main() 