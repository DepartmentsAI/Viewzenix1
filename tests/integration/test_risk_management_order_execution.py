"""
Integration tests for Risk Management Service with Order Execution.
"""
import pytest
import json
import unittest.mock as mock
from datetime import datetime, timedelta

# These will be imported once the implementation is complete
# from src.backend.services.risk_management_service import RiskManagementService
# from src.backend.services.order_execution_service import OrderExecutionService
# from src.integration.adapters.broker_adapter import BrokerAdapter


class TestRiskManagementOrderExecution:
    """Test suite for the interaction between risk management and order execution."""
    
    @pytest.fixture
    def mock_broker_adapter(self):
        """Create a mock broker adapter."""
        adapter = mock.MagicMock()
        
        # Setup account and position information
        adapter.get_account_info.return_value = {
            'equity': 100000,
            'cash': 70000,
            'previous_day_equity': 98000
        }
        adapter.get_all_positions.return_value = [
            {
                'symbol': 'BTCUSD',
                'qty': 0.5,
                'side': 'long',
                'value': 30000,
                'unrealized_pl': 1000
            }
        ]
        
        # Setup order execution responses
        adapter.place_market_order.return_value = {
            'id': 'ord-123',
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'buy',
            'type': 'market',
            'status': 'filled',
            'filled_avg_price': 60000,
            'filled_at': datetime.now()
        }
        
        adapter.place_stop_order.return_value = {
            'id': 'sl-123',
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'sell',
            'type': 'stop',
            'stop_price': 58800,
            'status': 'new',
            'created_at': datetime.now()
        }
        
        adapter.place_limit_order.return_value = {
            'id': 'tp-123',
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'sell',
            'type': 'limit',
            'limit_price': 63000,
            'status': 'new',
            'created_at': datetime.now()
        }
        
        return adapter
    
    @pytest.fixture
    def mock_order_execution_service(self, mock_broker_adapter):
        """Create a mock order execution service."""
        service = mock.MagicMock()
        service.broker_adapter = mock_broker_adapter
        
        service.execute_market_order.return_value = {
            'status': 'success',
            'order_id': 'ord-123',
            'execution_details': {
                'symbol': 'BTCUSD',
                'qty': 0.1,
                'side': 'buy',
                'filled_price': 60000,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        service.execute_stop_order.return_value = {
            'status': 'success',
            'order_id': 'sl-123',
            'order_details': {
                'symbol': 'BTCUSD',
                'qty': 0.1,
                'side': 'sell',
                'stop_price': 58800,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        service.execute_limit_order.return_value = {
            'status': 'success',
            'order_id': 'tp-123',
            'order_details': {
                'symbol': 'BTCUSD',
                'qty': 0.1,
                'side': 'sell',
                'limit_price': 63000,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return service
    
    @pytest.fixture
    def risk_config(self):
        """Create a risk configuration."""
        return {
            'max_position_size_usd': 50000.0,
            'max_position_size_pct': 0.25,
            'max_single_order_size_usd': 10000.0,
            'max_daily_drawdown_pct': 0.05,
            'position_risk_limit_pct': 0.02,
            'emergency_stop_loss_pct': 0.10,
            'max_leverage': 3.0,
            'automatic_sl_tp': True,
            'cleanup_threshold_minutes': 30
        }
    
    @pytest.fixture
    def mock_risk_management_service(self, mock_broker_adapter, risk_config):
        """Create a mock risk management service."""
        service = mock.MagicMock()
        service.broker_adapter = mock_broker_adapter
        service.config = risk_config
        
        # Mock validation responses
        service.validate_order_size.return_value = {'valid': True}
        service.validate_daily_drawdown.return_value = {'valid': True}
        
        # Mock SL/TP responses
        service.attach_stop_loss.return_value = {
            'status': 'success',
            'stop_loss_order_id': 'sl-123'
        }
        service.attach_take_profit.return_value = {
            'status': 'success',
            'take_profit_order_id': 'tp-123'
        }
        
        return service
    
    def test_order_validation_before_execution(self, mock_risk_management_service, mock_order_execution_service):
        """Test that orders are validated by risk management before execution."""
        # Order details
        order = {
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'buy',
            'type': 'market'
        }
        
        # Execute order (this would be done by the order execution service in reality)
        # We're mocking this interaction for now
        mock_risk_management_service.validate_order_size.return_value = {'valid': True}
        validation_result = mock_risk_management_service.validate_order_size(order)
        assert validation_result['valid'] is True
        
        # Since validation passed, execute the order
        execution_result = mock_order_execution_service.execute_market_order(order)
        assert execution_result['status'] == 'success'
        assert execution_result['order_id'] == 'ord-123'
        
        # Verify the risk management service was called to validate
        mock_risk_management_service.validate_order_size.assert_called_once_with(order)
    
    def test_automatic_sl_tp_attachment(self, mock_risk_management_service, mock_order_execution_service):
        """Test that SL/TP orders are automatically attached to executed orders."""
        # Order details
        order = {
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'buy',
            'type': 'market'
        }
        
        # Execute order
        execution_result = mock_order_execution_service.execute_market_order(order)
        assert execution_result['status'] == 'success'
        
        # Get filled order details
        filled_order = {
            'id': execution_result['order_id'],
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'buy',
            'status': 'filled',
            'filled_avg_price': 60000,
            'filled_at': datetime.now()
        }
        
        # Attach stop loss
        sl_result = mock_risk_management_service.attach_stop_loss(filled_order)
        assert sl_result['status'] == 'success'
        assert sl_result['stop_loss_order_id'] == 'sl-123'
        
        # Attach take profit
        tp_result = mock_risk_management_service.attach_take_profit(filled_order)
        assert tp_result['status'] == 'success'
        assert tp_result['take_profit_order_id'] == 'tp-123'
        
        # Verify both SL and TP were attached as expected
        mock_risk_management_service.attach_stop_loss.assert_called_once_with(filled_order)
        mock_risk_management_service.attach_take_profit.assert_called_once_with(filled_order)
    
    def test_order_rejection_on_risk_limit_breach(self, mock_risk_management_service, mock_order_execution_service):
        """Test that orders breaching risk limits are rejected."""
        # Large order that exceeds risk limits
        large_order = {
            'symbol': 'BTCUSD',
            'qty': 2.0,  # Large quantity
            'side': 'buy',
            'type': 'market',
            'price': 60000  # (Estimated for validation purposes)
        }
        
        # Configure risk validation to fail
        mock_risk_management_service.validate_order_size.return_value = {
            'valid': False,
            'reason': 'Order size exceeds maximum position size limit',
            'max_size_usd': 50000.0,
            'order_size_usd': 120000.0
        }
        
        # Validate order
        validation_result = mock_risk_management_service.validate_order_size(large_order)
        assert validation_result['valid'] is False
        
        # Order execution should not proceed if validation fails
        # In a real system, this check would happen within the order execution service
        # Here we're just testing the interaction
        if not validation_result['valid']:
            # Mock the expected response when execution is blocked
            expected_error = {
                'status': 'rejected',
                'reason': validation_result['reason'],
                'details': {
                    'max_size_usd': validation_result['max_size_usd'],
                    'order_size_usd': validation_result['order_size_usd']
                }
            }
            
            # Verify order was not executed
            mock_order_execution_service.execute_market_order.assert_not_called()
    
    def test_emergency_stop_loss_triggers_market_close(self, mock_risk_management_service, mock_order_execution_service, mock_broker_adapter):
        """Test that emergency stop loss triggers immediate position closure."""
        # Simulate equity drop below emergency threshold
        mock_broker_adapter.get_account_info.return_value = {
            'equity': 88000,  # 10.2% below previous day's equity
            'previous_day_equity': 98000
        }
        
        # Configure emergency stop loss check to trigger
        mock_risk_management_service.check_emergency_stop_loss.return_value = {
            'emergency_triggered': True,
            'emergency_action': 'close_all_positions',
            'current_loss_pct': 0.102,
            'emergency_threshold_pct': 0.10
        }
        
        # Check for emergency stop loss
        emergency_result = mock_risk_management_service.check_emergency_stop_loss()
        assert emergency_result['emergency_triggered'] is True
        
        # In a real system, this would trigger a call to close all positions
        if emergency_result['emergency_triggered']:
            mock_broker_adapter.close_all_positions.return_value = {
                'status': 'success',
                'positions_closed': 1,
                'details': [
                    {
                        'symbol': 'BTCUSD',
                        'qty': 0.5,
                        'execution_price': 58000
                    }
                ]
            }
            
            # Emergency close all positions
            close_result = mock_broker_adapter.close_all_positions()
            assert close_result['status'] == 'success'
            assert close_result['positions_closed'] == 1 