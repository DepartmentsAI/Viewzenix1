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

# Add imports for the paper trading adapter tests
from src.backend.services.risk_manager import RiskManager
from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter


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
    
    @pytest.fixture
    def paper_trading_adapter(self):
        """Create a real paper trading adapter for integration testing."""
        return PaperTradingAdapter(initial_balance=100000.0)
    
    @pytest.fixture
    def order_engine(self, paper_trading_adapter):
        """Create a real order engine with paper trading adapter."""
        return OrderEngine(broker_adapter=paper_trading_adapter)
    
    @pytest.fixture
    def risk_manager(self, paper_trading_adapter, order_engine):
        """Create a real risk manager with paper trading adapter."""
        return RiskManager(
            broker_adapter=paper_trading_adapter,
            order_engine=order_engine,
            max_position_size=5000.0,
            max_drawdown_pct=0.05
        )
    
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
            'filled_avg_price': 60000
        }
        
        # Attach SL and TP
        sl_result = mock_risk_management_service.attach_stop_loss(
            order_id=filled_order['id'],
            symbol=filled_order['symbol'],
            qty=filled_order['qty'],
            side='sell',
            price=59400  # 1% below entry
        )
        
        tp_result = mock_risk_management_service.attach_take_profit(
            order_id=filled_order['id'],
            symbol=filled_order['symbol'],
            qty=filled_order['qty'],
            side='sell',
            price=63000  # 5% above entry
        )
        
        # Verify SL/TP were attached
        assert sl_result['status'] == 'success'
        assert tp_result['status'] == 'success'
    
    def test_order_rejection_on_risk_limit_breach(self, mock_risk_management_service, mock_order_execution_service):
        """Test that orders breaching risk limits are rejected."""
        # Set up risk management to reject the order
        mock_risk_management_service.validate_order_size.return_value = {
            'valid': False,
            'reason': 'Order size exceeds maximum position size',
            'details': {
                'order_size_usd': 60000,
                'max_allowed_usd': 50000
            }
        }
        
        # Order details (intentionally large)
        order = {
            'symbol': 'BTCUSD',
            'qty': 1.0,  # Large order
            'side': 'buy',
            'type': 'market'
        }
        
        # Validate order
        validation_result = mock_risk_management_service.validate_order_size(order)
        
        # Verify validation failed
        assert validation_result['valid'] is False
        
        # Ensure order execution was not called
        mock_order_execution_service.execute_market_order.assert_not_called()
    
    def test_emergency_stop_loss_triggers_market_close(self, mock_risk_management_service, mock_order_execution_service, mock_broker_adapter):
        """Test that emergency stop loss triggers closing all positions."""
        # Setup daily drawdown breach
        mock_risk_management_service.validate_daily_drawdown.return_value = {
            'valid': False,
            'reason': 'Daily drawdown limit exceeded',
            'details': {
                'current_drawdown_pct': 0.06,
                'max_allowed_pct': 0.05,
                'emergency_action': 'close_all_positions'
            }
        }
        
        # Mock the close all positions method
        mock_risk_management_service.close_all_positions.return_value = {
            'status': 'success',
            'positions_closed': 1,
            'details': [
                {
                    'symbol': 'BTCUSD',
                    'qty': 0.5,
                    'order_id': 'close-123',
                    'filled_price': 59800
                }
            ]
        }
        
        # Check daily drawdown - this would trigger emergency action
        drawdown_check = mock_risk_management_service.validate_daily_drawdown()
        assert drawdown_check['valid'] is False
        
        # Emergency action: close all positions
        if drawdown_check.get('details', {}).get('emergency_action') == 'close_all_positions':
            close_result = mock_risk_management_service.close_all_positions()
            assert close_result['status'] == 'success'
            
            # Verify the broker adapter was called to close positions
            mock_broker_adapter.get_all_positions.assert_called()
            assert mock_broker_adapter.place_market_order.call_count >= 1
    
    # Add test for paper trading adapter with risk management
    def test_paper_trading_with_risk_management_integration(self, paper_trading_adapter, order_engine, risk_manager):
        """Test the integration between paper trading adapter and risk management."""
        # Create a valid trade signal
        trade_signal = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 20,
            "type": "market",
            "signal_source": "strategy_1",
            "risk_profile": "moderate"
        }
        
        # Process the order through risk management
        result = risk_manager.process_order_with_risk_management(trade_signal)
        
        # Verify the result
        assert result['status'] == 'success', f"Order failed: {result.get('message', 'Unknown error')}"
        assert 'order_id' in result, "Order ID not returned in successful result"
        
        # Get the parent order ID
        parent_order_id = result['order_id']
        
        # Add stop loss and take profit
        sl_tp_result = risk_manager.add_stop_loss_take_profit(
            symbol=trade_signal["symbol"],
            entry_price=150.0,  # Simulate current price
            parent_order_id=parent_order_id,
            risk_reward_ratio=2.0  # 2:1 reward-to-risk ratio
        )
        
        # Verify stop loss and take profit orders
        assert sl_tp_result['status'] == 'success', f"SL/TP creation failed: {sl_tp_result.get('message', 'Unknown error')}"
        assert 'stop_loss_order_id' in sl_tp_result, "Stop loss order ID not returned"
        assert 'take_profit_order_id' in sl_tp_result, "Take profit order ID not returned"
        
        # Verify account and position updates
        account = paper_trading_adapter.get_account_info()
        positions = paper_trading_adapter.get_all_positions()
        
        # Check that account equity has been updated
        assert account['equity'] is not None
        
        # Check that we have an AAPL position
        aapl_position = next((p for p in positions if p['symbol'] == 'AAPL'), None)
        assert aapl_position is not None, "AAPL position not created"
        assert aapl_position['side'] == 'long', "Position side is not long"
        assert float(aapl_position['qty']) == 20, "Position quantity is not correct"
        
        # Test circular import handling - ensure no errors occurred during import
        assert risk_manager is not None, "Risk manager not properly initialized" 