"""
Unit tests for the RiskManager class.
"""
import pytest
import unittest.mock as mock
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.backend.services.risk_manager import RiskManager
from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.broker_adapter import BrokerAdapter


class MockBrokerAdapter(BrokerAdapter):
    """Mock BrokerAdapter implementation for testing."""
    
    def __init__(self):
        self.calls = []
        self.responses = {}
        self.default_response = {'id': 'test-order-id', 'status': 'filled'}
    
    def set_response(self, method: str, response: Any):
        """Set a custom response for a method."""
        self.responses[method] = response
    
    def _record_call(self, method: str, *args, **kwargs):
        """Record a method call."""
        self.calls.append({
            'method': method,
            'args': args,
            'kwargs': kwargs
        })
    
    def _get_response(self, method: str):
        """Get the response for a method."""
        return self.responses.get(method, self.default_response)
    
    def authenticate(self) -> bool:
        self._record_call('authenticate')
        return self._get_response('authenticate')
    
    def place_market_order(self, symbol: str, qty: float, side: str, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        self._record_call('place_market_order', symbol, qty, side, client_order_id)
        return self._get_response('place_market_order')
    
    def place_limit_order(self, symbol: str, qty: float, side: str, limit_price: float, 
                         client_order_id: Optional[str] = None) -> Dict[str, Any]:
        self._record_call('place_limit_order', symbol, qty, side, limit_price, client_order_id)
        return self._get_response('place_limit_order')
    
    def place_stop_order(self, symbol: str, qty: float, side: str, stop_price: float,
                        client_order_id: Optional[str] = None) -> Dict[str, Any]:
        self._record_call('place_stop_order', symbol, qty, side, stop_price, client_order_id)
        return self._get_response('place_stop_order')
    
    def place_bracket_order(self, symbol: str, qty: float, side: str, 
                           entry_price: Optional[float] = None,
                           take_profit_price: Optional[float] = None, 
                           stop_loss_price: Optional[float] = None,
                           client_order_id: Optional[str] = None) -> Dict[str, Any]:
        self._record_call('place_bracket_order', symbol, qty, side, entry_price, 
                         take_profit_price, stop_loss_price, client_order_id)
        return self._get_response('place_bracket_order')
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        self._record_call('cancel_order', order_id)
        return self._get_response('cancel_order')
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        self._record_call('get_order_status', order_id)
        return self._get_response('get_order_status')
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        self._record_call('get_position', symbol)
        return self._get_response('get_position')
    
    def get_all_positions(self) -> Dict[str, Any]:
        self._record_call('get_all_positions')
        return self._get_response('get_all_positions')
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        self._record_call('close_position', symbol)
        return self._get_response('close_position')
    
    def get_account_info(self) -> Dict[str, Any]:
        self._record_call('get_account_info')
        return self._get_response('get_account_info')
    
    def get_all_orders(self) -> Dict[str, Any]:
        self._record_call('get_all_orders')
        return self._get_response('get_all_orders')


class MockOrderEngine:
    """Mock OrderEngine implementation for testing."""
    
    def __init__(self):
        self.calls = []
        self.responses = {}
        self.default_response = {'status': 'success', 'order_id': 'test-order-id'}
    
    def set_response(self, method: str, response: Any):
        """Set a custom response for a method."""
        self.responses[method] = response
    
    def _record_call(self, method: str, *args, **kwargs):
        """Record a method call."""
        self.calls.append({
            'method': method,
            'args': args,
            'kwargs': kwargs
        })
    
    def _get_response(self, method: str):
        """Get the response for a method."""
        return self.responses.get(method, self.default_response)
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        self._record_call('process_webhook_data', webhook_data)
        return self._get_response('process_webhook_data')
    
    def _get_current_price(self, symbol: str) -> float:
        self._record_call('_get_current_price', symbol)
        return self._get_response('_get_current_price')


class TestRiskManager:
    """Test suite for the RiskManager class."""
    
    @pytest.fixture
    def mock_broker_adapter(self):
        """Create a MockBrokerAdapter instance."""
        return MockBrokerAdapter()
    
    @pytest.fixture
    def mock_order_engine(self, mock_broker_adapter):
        """Create a MockOrderEngine instance."""
        engine = MockOrderEngine()
        engine.broker_adapter = mock_broker_adapter
        return engine
    
    @pytest.fixture
    def risk_manager(self, mock_broker_adapter, mock_order_engine):
        """Create a RiskManager instance with mock dependencies."""
        return RiskManager(broker_adapter=mock_broker_adapter, order_engine=mock_order_engine)
    
    def test_init(self, risk_manager, mock_broker_adapter, mock_order_engine):
        """Test RiskManager initialization."""
        assert risk_manager.broker_adapter == mock_broker_adapter
        assert risk_manager.order_engine == mock_order_engine
        assert 'stop_loss_percent' in risk_manager.risk_params
        assert 'take_profit_percent' in risk_manager.risk_params
        assert 'max_position_size_percent' in risk_manager.risk_params
        assert 'max_daily_drawdown_percent' in risk_manager.risk_params
        assert 'max_open_positions' in risk_manager.risk_params
        assert 'daily_performance' in vars(risk_manager)
    
    def test_initialize_daily_tracking(self, risk_manager, mock_broker_adapter):
        """Test _initialize_daily_tracking method."""
        # Setup mock response
        mock_broker_adapter.set_response('get_account_info', {'equity': '10000'})
        
        # Call method
        risk_manager._initialize_daily_tracking()
        
        # Verify calls
        assert mock_broker_adapter.calls[0]['method'] == 'get_account_info'
        
        # Verify tracking was initialized correctly
        assert risk_manager.daily_performance['start_equity'] == 10000
        assert risk_manager.daily_performance['current_equity'] == 10000
        assert risk_manager.daily_performance['max_equity'] == 10000
        assert risk_manager.daily_performance['min_equity'] == 10000
    
    def test_update_risk_parameters(self, risk_manager):
        """Test update_risk_parameters method."""
        # Initial values
        initial_sl = risk_manager.risk_params['stop_loss_percent']
        initial_tp = risk_manager.risk_params['take_profit_percent']
        
        # Update parameters
        new_params = {
            'stop_loss_percent': 0.03,
            'take_profit_percent': 0.07
        }
        result = risk_manager.update_risk_parameters(new_params)
        
        # Verify parameters were updated
        assert result['stop_loss_percent'] == 0.03
        assert result['take_profit_percent'] == 0.07
        assert risk_manager.risk_params['stop_loss_percent'] == 0.03
        assert risk_manager.risk_params['take_profit_percent'] == 0.07
        
        # Test validation - percent value must be between 0 and 1
        risk_manager.update_risk_parameters({'stop_loss_percent': 1.5})
        # Invalid value should be rejected, value should not change
        assert risk_manager.risk_params['stop_loss_percent'] == 0.03
    
    def test_get_risk_parameters(self, risk_manager):
        """Test get_risk_parameters method."""
        params = risk_manager.get_risk_parameters()
        assert params == risk_manager.risk_params
        assert params is not risk_manager.risk_params  # Should be a copy
    
    def test_check_portfolio_limits_entry_under_limit(self, risk_manager, mock_broker_adapter):
        """Test _check_portfolio_limits with entry order under limits."""
        # Setup mock responses
        mock_broker_adapter.set_response('get_all_positions', [{'symbol': 'BTCUSD'}])  # 1 position
        mock_broker_adapter.set_response('get_account_info', {'equity': '10000'})
        mock_broker_adapter.set_response('get_position', {'current_price': '50000'})
        
        # Set max positions to 5
        risk_manager.risk_params['max_open_positions'] = 5
        
        # Create order data for entry
        order_data = {
            'symbol': 'ETHUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 2000,
            'strategy_order_contracts': 0.1
        }
        
        # Check limits
        result = risk_manager._check_portfolio_limits(order_data)
        
        # Verify result
        assert result is True
        
        # Verify calls
        get_positions_call = None
        get_account_call = None
        for call in mock_broker_adapter.calls:
            if call['method'] == 'get_all_positions':
                get_positions_call = call
            elif call['method'] == 'get_account_info':
                get_account_call = call
        
        assert get_positions_call is not None
        assert get_account_call is not None
    
    def test_check_portfolio_limits_exit_order(self, risk_manager, mock_broker_adapter):
        """Test _check_portfolio_limits with exit order."""
        # For exit orders, should always return True without checking limits
        
        # Create order data for exit
        order_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'sell',  # Exit action for long
            'strategy_order_price': 50000
        }
        
        # Check limits
        result = risk_manager._check_portfolio_limits(order_data)
        
        # Verify result
        assert result is True
        
        # Verify no calls to get positions/account were made
        get_positions_call = None
        for call in mock_broker_adapter.calls:
            if call['method'] == 'get_all_positions':
                get_positions_call = call
        
        assert get_positions_call is None
    
    def test_check_portfolio_limits_max_positions_reached(self, risk_manager, mock_broker_adapter):
        """Test _check_portfolio_limits when max positions is reached."""
        # Setup mock responses - 5 positions
        mock_broker_adapter.set_response('get_all_positions', [
            {'symbol': 'BTCUSD'}, {'symbol': 'ETHUSD'}, {'symbol': 'LTCUSD'},
            {'symbol': 'XRPUSD'}, {'symbol': 'DOTUSD'}
        ])
        
        # Set max positions to 5
        risk_manager.risk_params['max_open_positions'] = 5
        
        # Create order data for entry
        order_data = {
            'symbol': 'ADAUSD',  # New position
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 1.5,
            'strategy_order_contracts': 100
        }
        
        # Check limits
        result = risk_manager._check_portfolio_limits(order_data)
        
        # Verify result - should be rejected
        assert result is False
    
    def test_check_portfolio_limits_position_size_exceeded(self, risk_manager, mock_broker_adapter):
        """Test _check_portfolio_limits when position size is too large."""
        # Setup mock responses
        mock_broker_adapter.set_response('get_all_positions', [{'symbol': 'BTCUSD'}])
        mock_broker_adapter.set_response('get_account_info', {'equity': '10000'})
        
        # Set max position size to 5%
        risk_manager.risk_params['max_position_size_percent'] = 0.05
        
        # Create order data for entry with value of 1000 (10% of equity)
        order_data = {
            'symbol': 'ETHUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 2000,
            'strategy_order_contracts': 0.5  # Total value: 1000
        }
        
        # Check limits
        result = risk_manager._check_portfolio_limits(order_data)
        
        # Verify result - should be rejected
        assert result is False
    
    def test_check_drawdown_limits_under_limit(self, risk_manager):
        """Test _check_drawdown_limits when drawdown is under limit."""
        # Setup tracking data
        risk_manager.daily_performance = {
            'start_equity': 10000,
            'current_equity': 9800,  # 2% drawdown from start
            'max_equity': 10000,
            'min_equity': 9800,
            'last_updated': datetime.now(),
            'reset_time': datetime.now() + timedelta(days=1)
        }
        
        # Set max drawdown to 5%
        risk_manager.risk_params['max_daily_drawdown_percent'] = 0.05
        
        # Check drawdown limits
        result = risk_manager._check_drawdown_limits()
        
        # Verify result - should be under limit
        assert result is True
    
    def test_check_drawdown_limits_over_limit(self, risk_manager):
        """Test _check_drawdown_limits when drawdown exceeds limit."""
        # Setup tracking data
        risk_manager.daily_performance = {
            'start_equity': 10000,
            'current_equity': 9400,  # 6% drawdown from start
            'max_equity': 10000,
            'min_equity': 9400,
            'last_updated': datetime.now(),
            'reset_time': datetime.now() + timedelta(days=1)
        }
        
        # Set max drawdown to 5%
        risk_manager.risk_params['max_daily_drawdown_percent'] = 0.05
        
        # Check drawdown limits
        result = risk_manager._check_drawdown_limits()
        
        # Verify result - should be over limit
        assert result is False
    
    def test_process_order_with_risk_management_success(self, risk_manager, mock_order_engine, mock_broker_adapter):
        """Test process_order_with_risk_management with successful order."""
        # Setup mocks
        mock_broker_adapter.set_response('get_all_positions', [])
        mock_broker_adapter.set_response('get_account_info', {'equity': '10000'})
        mock_broker_adapter.set_response('get_position', {
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'long'
        })
        
        mock_order_engine.set_response('process_webhook_data', {
            'status': 'success',
            'order_id': 'test-order-123',
            'message': 'Order executed successfully'
        })
        
        # Setup risk manager
        risk_manager.daily_performance = {
            'start_equity': 10000,
            'current_equity': 10000,
            'max_equity': 10000,
            'min_equity': 10000,
            'last_updated': datetime.now(),
            'reset_time': datetime.now() + timedelta(days=1)
        }
        
        # Create webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 50000,
            'strategy_order_contracts': 0.1,
            'time': 1620000000000
        }
        
        # Process order
        result = risk_manager.process_order_with_risk_management(webhook_data)
        
        # Verify result
        assert result['status'] == 'success'
        assert 'order_result' in result
        assert result['risk_applied'] is True
        
        # Verify order engine was called
        process_call = None
        for call in mock_order_engine.calls:
            if call['method'] == 'process_webhook_data':
                process_call = call
                break
        
        assert process_call is not None
        assert process_call['args'][0] == webhook_data
    
    def test_process_order_with_risk_management_exit(self, risk_manager, mock_order_engine):
        """Test process_order_with_risk_management with exit order."""
        # Setup order engine response
        mock_order_engine.set_response('process_webhook_data', {
            'status': 'success',
            'message': 'Position closed successfully'
        })
        
        # Create webhook data for exit
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'sell',  # Exit long position
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process order
        result = risk_manager.process_order_with_risk_management(webhook_data)
        
        # Verify result
        assert result['status'] == 'success'
        assert 'order_result' in result
        assert result['risk_applied'] is False  # No risk management for exits
    
    def test_process_order_with_risk_management_rejected_portfolio(self, risk_manager, mock_broker_adapter):
        """Test process_order_with_risk_management when order is rejected due to portfolio limits."""
        # Setup mock responses - max positions reached
        mock_broker_adapter.set_response('get_all_positions', [
            {'symbol': 'BTCUSD'}, {'symbol': 'ETHUSD'}, {'symbol': 'LTCUSD'},
            {'symbol': 'XRPUSD'}, {'symbol': 'DOTUSD'}
        ])
        
        # Set max positions to 5
        risk_manager.risk_params['max_open_positions'] = 5
        
        # Create webhook data
        webhook_data = {
            'symbol': 'ADAUSD',  # New position
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 1.5,
            'strategy_order_contracts': 100,
            'time': 1620000000000
        }
        
        # Process order
        result = risk_manager.process_order_with_risk_management(webhook_data)
        
        # Verify result
        assert result['status'] == 'rejected'
        assert 'portfolio limits' in result['message'].lower()
    
    def test_add_stop_loss_take_profit(self, risk_manager, mock_broker_adapter):
        """Test _add_stop_loss_take_profit method."""
        # Setup mock responses
        mock_broker_adapter.set_response('get_position', {
            'symbol': 'BTCUSD',
            'qty': 0.1,
            'side': 'long'
        })
        mock_broker_adapter.set_response('place_stop_order', {
            'id': 'sl-order-123',
            'status': 'new'
        })
        mock_broker_adapter.set_response('place_limit_order', {
            'id': 'tp-order-123',
            'status': 'new'
        })
        
        # Set risk parameters
        risk_manager.risk_params['stop_loss_percent'] = 0.02
        risk_manager.risk_params['take_profit_percent'] = 0.05
        
        # Call method
        result = risk_manager._add_stop_loss_take_profit(
            'BTCUSD',
            50000,  # Entry price
            'parent-order-123'
        )
        
        # Verify result
        assert 'stop_loss' in result
        assert 'take_profit' in result
        assert result['stop_loss']['id'] == 'sl-order-123'
        assert result['take_profit']['id'] == 'tp-order-123'
        
        # Verify calls
        get_position_call = None
        stop_order_call = None
        limit_order_call = None
        
        for call in mock_broker_adapter.calls:
            if call['method'] == 'get_position':
                get_position_call = call
            elif call['method'] == 'place_stop_order':
                stop_order_call = call
            elif call['method'] == 'place_limit_order':
                limit_order_call = call
        
        assert get_position_call is not None
        assert get_position_call['args'][0] == 'BTCUSD'
        
        assert stop_order_call is not None
        assert stop_order_call['args'][0] == 'BTCUSD'  # Symbol
        assert stop_order_call['args'][1] == 0.1      # Quantity
        assert stop_order_call['args'][2] == 'sell'    # Side (sell for long position)
        assert stop_order_call['args'][3] == 49000    # Stop price (2% below entry)
        
        assert limit_order_call is not None
        assert limit_order_call['args'][0] == 'BTCUSD'  # Symbol
        assert limit_order_call['args'][1] == 0.1      # Quantity
        assert limit_order_call['args'][2] == 'sell'    # Side (sell for long position)
        assert limit_order_call['args'][3] == 52500    # Limit price (5% above entry)
    
    def test_cleanup_orphaned_orders(self, risk_manager, mock_broker_adapter):
        """Test cleanup_orphaned_orders method."""
        # Current time
        now = datetime.now()
        
        # Old order (26 hours ago) - should be cleaned up
        old_order_time = (now - timedelta(hours=26)).isoformat() + 'Z'
        
        # Recent order (1 hour ago) - should NOT be cleaned up
        recent_order_time = (now - timedelta(hours=1)).isoformat() + 'Z'
        
        # Setup mock response - two open orders, one old and one recent
        mock_broker_adapter.set_response('get_all_orders', [
            {
                'id': 'old-order-123',
                'status': 'new',
                'created_at': old_order_time
            },
            {
                'id': 'recent-order-456',
                'status': 'new',
                'created_at': recent_order_time
            },
            {
                'id': 'filled-order-789',
                'status': 'filled',  # Already filled - should be ignored
                'created_at': old_order_time
            }
        ])
        
        mock_broker_adapter.set_response('cancel_order', {
            'id': 'old-order-123',
            'status': 'canceled'
        })
        
        # Set orphaned age to 24 hours
        risk_manager.risk_params['orphaned_order_age_hours'] = 24
        
        # Call method
        result = risk_manager.cleanup_orphaned_orders()
        
        # Verify result
        assert result['total_cleaned'] == 1
        assert len(result['cleaned_orders']) == 1
        assert result['cleaned_orders'][0]['order_id'] == 'old-order-123'
        assert len(result['errors']) == 0
        
        # Verify calls
        get_orders_call = None
        cancel_order_call = None
        
        for call in mock_broker_adapter.calls:
            if call['method'] == 'get_all_orders':
                get_orders_call = call
            elif call['method'] == 'cancel_order':
                cancel_order_call = call
        
        assert get_orders_call is not None
        
        assert cancel_order_call is not None
        assert cancel_order_call['args'][0] == 'old-order-123'
    
    def test_get_risk_metrics(self, risk_manager, mock_broker_adapter):
        """Test get_risk_metrics method."""
        # Setup mock responses
        mock_broker_adapter.set_response('get_account_info', {
            'equity': '10000',
            'cash': '5000'
        })
        
        mock_broker_adapter.set_response('get_all_positions', [
            {
                'symbol': 'BTCUSD',
                'market_value': '3000'
            },
            {
                'symbol': 'ETHUSD',
                'market_value': '2000'
            }
        ])
        
        # Setup daily performance
        risk_manager.daily_performance = {
            'start_equity': 9000,
            'current_equity': 10000,
            'max_equity': 10500,
            'min_equity': 8900,
            'last_updated': datetime.now(),
            'reset_time': datetime.now() + timedelta(days=1)
        }
        
        # Call method
        metrics = risk_manager.get_risk_metrics()
        
        # Verify metrics
        assert 'portfolio' in metrics
        assert 'daily_performance' in metrics
        assert 'risk_parameters' in metrics
        
        # Check portfolio metrics
        assert metrics['portfolio']['equity'] == 10000
        assert metrics['portfolio']['cash'] == 5000
        assert metrics['portfolio']['positions_count'] == 2
        assert metrics['portfolio']['positions_value'] == 5000  # 3000 + 2000
        
        # Check largest position
        assert metrics['portfolio']['largest_position']['symbol'] == 'BTCUSD'
        assert metrics['portfolio']['largest_position']['value'] == 3000
        assert metrics['portfolio']['largest_position']['percent_of_portfolio'] == 0.3  # 3000/10000
        
        # Check daily performance
        assert metrics['daily_performance']['start_equity'] == 9000
        assert metrics['daily_performance']['current_equity'] == 10000
        assert metrics['daily_performance']['max_equity'] == 10500
        assert metrics['daily_performance']['min_equity'] == 8900
        assert 'current_drawdown_percent' in metrics['daily_performance']
        assert metrics['daily_performance']['current_drawdown_percent'] == (10500 - 10000) / 10500
        
        # Check risk parameters
        assert metrics['risk_parameters'] == risk_manager.risk_params 