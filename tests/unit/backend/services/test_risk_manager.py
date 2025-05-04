"""
Unit tests for the RiskManager class.
"""
import pytest
import json
import os
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import sys
import logging

# Import the classes we're testing
from src.backend.services.risk_manager import RiskManager
from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.broker_adapter import BrokerAdapter

# Explicitly import the paper trading adapter to ensure it's properly loaded
# This helps prevent circular import issues during testing
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@pytest.fixture
def webhook_examples():
    """Load webhook example data for testing."""
    # Get the path to the webhook examples file
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "e2e", "fixtures", "data", "webhook_examples.json"
    )
    
    # Check if the file exists and load it
    if os.path.exists(fixture_path):
        with open(fixture_path, 'r') as f:
            return json.load(f)
    else:
        logger.warning(f"Webhook examples file not found at {fixture_path}")
        # Return a minimal set of webhook examples if the file isn't found
        return {
            "long_entry": {
                "symbol": "BTCUSD",
                "strategy_order_id": "long",
                "strategy_order_action": "buy",
                "strategy_order_contracts": 0.1,
                "strategy_order_price": 50000,
                "time": 1620000000000
            }
        }

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
        """Create a mock broker adapter for testing."""
        adapter = MagicMock(spec=BrokerAdapter)
        
        # Configure adapter mocks
        adapter.get_account_info.return_value = {
            'equity': 10000.0,
            'buying_power': 20000.0,
            'cash': 5000.0,
            'currency': 'USD'
        }
        
        adapter.get_positions.return_value = [
            {
                'symbol': 'AAPL',
                'qty': 10,
                'market_value': 1500.0,
                'avg_entry_price': 145.0
            },
            {
                'symbol': 'MSFT',
                'qty': 5,
                'market_value': 1300.0,
                'avg_entry_price': 250.0
            }
        ]
        
        adapter.get_quote.return_value = {
            'last_price': 150.0,
            'ask_price': 150.05,
            'bid_price': 149.95,
            'volume': 10000
        }
        
        return adapter
    
    @pytest.fixture
    def mock_order_engine(self):
        """Create a mock order engine for testing."""
        engine = MagicMock()
        
        # Configure mock methods
        engine.process_webhook_data.return_value = {
            'status': 'success',
            'order_id': 'test-order-123',
            'message': 'Order executed successfully'
        }
        
        return engine
    
    @pytest.fixture
    def risk_manager(self, mock_broker_adapter, mock_order_engine):
        """Create a RiskManager instance with mock dependencies."""
        return RiskManager(broker_adapter=mock_broker_adapter, order_engine=mock_order_engine)
    
    def test_initialization(self, risk_manager, mock_broker_adapter, mock_order_engine):
        """Test RiskManager initialization."""
        assert risk_manager.broker_adapter == mock_broker_adapter
        assert risk_manager.order_engine == mock_order_engine
        assert risk_manager.risk_params['stop_loss_percent'] == 0.02
        assert risk_manager.risk_params['take_profit_percent'] == 0.05
        assert risk_manager.risk_params['max_position_size_percent'] == 0.05
        assert risk_manager.daily_performance['start_equity'] == 10000.0
    
    def test_update_risk_parameters(self, risk_manager):
        """Test updating risk parameters."""
        new_params = {
            'stop_loss_percent': 0.03,
            'take_profit_percent': 0.08,
            'max_daily_drawdown_percent': 0.10
        }
        
        updated = risk_manager.update_risk_parameters(new_params)
        
        assert updated['stop_loss_percent'] == 0.03
        assert updated['take_profit_percent'] == 0.08
        assert updated['max_daily_drawdown_percent'] == 0.10
        assert updated['max_position_size_percent'] == 0.05  # Unchanged
        
        # Check invalid values are ignored
        invalid_params = {
            'stop_loss_percent': 1.5,  # > 1, invalid
            'max_open_positions': -2  # < 0, invalid
        }
        
        updated = risk_manager.update_risk_parameters(invalid_params)
        
        assert updated['stop_loss_percent'] == 0.03  # Unchanged
        assert updated['max_open_positions'] == 10  # Unchanged
    
    def test_get_risk_parameters(self, risk_manager):
        """Test getting risk parameters."""
        params = risk_manager.get_risk_parameters()
        
        assert params['stop_loss_percent'] == 0.02
        assert params['take_profit_percent'] == 0.05
        assert params['max_position_size_percent'] == 0.05
        assert params['max_daily_drawdown_percent'] == 0.05
        assert params['max_open_positions'] == 10
        assert params['orphaned_order_age_hours'] == 24
    
    def test_process_order_with_risk_management_success(self, risk_manager, mock_order_engine, webhook_examples):
        """Test successful processing of an order with risk management."""
        # Use a long entry example from webhook fixtures
        order_data = webhook_examples["long_entry"]
        
        # Mock order_engine response
        mock_order_engine.process_webhook_data.return_value = {
            'status': 'success',
            'order_id': 'test-order-123',
            'message': 'Order executed successfully'
        }
        
        # Process the order with risk management
        result = risk_manager.process_order_with_risk_management(order_data)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['risk_applied'] is True
        assert 'order_result' in result
        
        # Verify order_engine was called
        mock_order_engine.process_webhook_data.assert_called_once_with(order_data)
    
    def test_process_order_with_risk_management_portfolio_limit_rejection(self, risk_manager):
        """Test order rejection due to portfolio limits."""
        # Configure broker adapter to return more positions
        positions = [MagicMock() for _ in range(15)]  # Exceeds the max_open_positions (10)
        risk_manager.broker_adapter.get_positions.return_value = positions
        
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 150.0,
            'strategy_order_contracts': 5,
            'time': 1620000000000
        }
        
        result = risk_manager.process_order_with_risk_management(order_data)
        
        assert result['status'] == 'rejected'
        assert 'portfolio limits' in result['message']
        assert 'order_data' in result
        
        # Verify order engine was not called
        risk_manager.order_engine.process_webhook_data.assert_not_called()
    
    def test_process_order_with_risk_management_drawdown_rejection(self, risk_manager):
        """Test order rejection due to drawdown limits."""
        # Set up daily performance with high drawdown
        risk_manager.daily_performance = {
            'start_equity': 10000.0,
            'current_equity': 9400.0,  # 6% drawdown, exceeds 5% limit
            'max_equity': 10000.0,
            'min_equity': 9400.0,
            'last_updated': datetime.now(),
            'reset_time': datetime.now() + timedelta(days=1)
        }
        
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 150.0,
            'strategy_order_contracts': 5,
            'time': 1620000000000
        }
        
        result = risk_manager.process_order_with_risk_management(order_data)
        
        assert result['status'] == 'rejected'
        assert 'drawdown limit' in result['message']
        assert 'daily_performance' in result
        
        # Verify order engine was not called
        risk_manager.order_engine.process_webhook_data.assert_not_called()
    
    def test_process_order_with_risk_management_exit_order(self, risk_manager, mock_order_engine):
        """Test processing an exit order with risk management."""
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'sell',  # Exit order
            'strategy_order_price': 155.0,
            'strategy_order_contracts': 5,
            'time': 1620000000000
        }
        
        result = risk_manager.process_order_with_risk_management(order_data)
        
        assert result['status'] == 'success'
        assert result['risk_applied'] == False  # No risk management for exit orders
        
        # Verify order engine was called
        mock_order_engine.process_webhook_data.assert_called_once_with(order_data)
        
        # Verify no stop loss or take profit orders were created
        risk_manager.broker_adapter.submit_order.assert_not_called()
    
    def test_check_portfolio_limits_position_size(self, risk_manager):
        """Test portfolio limits check for position size."""
        # Set up a large order that exceeds position size limit
        order_data = {
            'symbol': 'AAPL',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_price': 150.0,
            'strategy_order_contracts': 10,  # Value: $1500, exceeds 5% of $10000 = $500
            'time': 1620000000000
        }
        
        # Set max position size to a smaller value
        risk_manager.risk_params['max_position_size_percent'] = 0.01  # 1% of $10000 = $100
        
        result = risk_manager._check_portfolio_limits(order_data)
        
        assert result is False  # Should reject the order
    
    def test_add_stop_loss_take_profit(self, risk_manager, webhook_examples):
        """Test adding stop loss and take profit orders."""
        # Prepare test data
        symbol = "BTCUSD"
        entry_price = 50000.0
        parent_order_id = "test-order-123"
        
        # Mock broker adapter methods
        risk_manager.broker_adapter.place_stop_order.return_value = {
            'id': 'sl-123',
            'client_order_id': 'sl-test-order-123',
            'symbol': symbol,
            'side': 'sell',
            'type': 'stop',
            'status': 'new'
        }
        
        risk_manager.broker_adapter.place_limit_order.return_value = {
            'id': 'tp-123',
            'client_order_id': 'tp-test-order-123',
            'symbol': symbol,
            'side': 'sell',
            'type': 'limit',
            'status': 'new'
        }
        
        # Get the risk parameters
        risk_params = risk_manager.get_risk_parameters()
        
        # Calculate expected stop loss and take profit prices
        expected_sl_price = entry_price * (1 - risk_params['stop_loss_percent'])
        expected_tp_price = entry_price * (1 + risk_params['take_profit_percent'])
        
        # Test with default parameters
        result = risk_manager._add_stop_loss_take_profit(
            symbol=symbol,
            entry_price=entry_price,
            parent_order_id=parent_order_id
        )
        
        # Verify result
        assert result['status'] == 'success'
        assert 'stop_loss_order' in result
        assert 'take_profit_order' in result
        
        # Verify broker adapter calls
        risk_manager.broker_adapter.place_stop_order.assert_called_once()
        risk_manager.broker_adapter.place_limit_order.assert_called_once()
        
        # Verify the stop loss price was calculated correctly
        sl_call_args = risk_manager.broker_adapter.place_stop_order.call_args[1]
        assert sl_call_args['symbol'] == symbol
        assert sl_call_args['side'] == 'sell'
        assert abs(sl_call_args['stop_price'] - expected_sl_price) < 0.01
        
        # Verify the take profit price was calculated correctly
        tp_call_args = risk_manager.broker_adapter.place_limit_order.call_args[1]
        assert tp_call_args['symbol'] == symbol
        assert tp_call_args['side'] == 'sell'
        assert abs(tp_call_args['limit_price'] - expected_tp_price) < 0.01
        
        # Test with explicit parameters
        stop_loss_price = 45000.0
        take_profit_price = 60000.0
        
        # Reset mocks
        risk_manager.broker_adapter.place_stop_order.reset_mock()
        risk_manager.broker_adapter.place_limit_order.reset_mock()
        
        # Call with explicit parameters
        result = risk_manager._add_stop_loss_take_profit(
            symbol=symbol,
            entry_price=entry_price,
            parent_order_id=parent_order_id,
            stop_loss_param=stop_loss_price,
            take_profit_param=take_profit_price
        )
        
        # Verify broker adapter calls with explicit parameters
        sl_call_args = risk_manager.broker_adapter.place_stop_order.call_args[1]
        tp_call_args = risk_manager.broker_adapter.place_limit_order.call_args[1]
        
        assert sl_call_args['stop_price'] == stop_loss_price
        assert tp_call_args['limit_price'] == take_profit_price
    
    def test_cleanup_orphaned_orders(self, risk_manager):
        """Test cleanup of orphaned orders."""
        # Create mock orders
        now = datetime.now()
        old_time = (now - timedelta(hours=36)).isoformat()
        recent_time = (now - timedelta(hours=12)).isoformat()
        
        orders = [
            {'id': 'old-order-1', 'status': 'open', 'created_at': old_time, 'symbol': 'AAPL'},
            {'id': 'old-order-2', 'status': 'open', 'created_at': old_time, 'symbol': 'MSFT'},
            {'id': 'recent-order', 'status': 'open', 'created_at': recent_time, 'symbol': 'TSLA'}
        ]
        
        risk_manager.broker_adapter.get_orders.return_value = orders
        
        # Set up successful cancel responses
        risk_manager.broker_adapter.cancel_order.side_effect = [
            {'id': 'old-order-1', 'status': 'canceled'},
            {'id': 'old-order-2', 'status': 'canceled'}
        ]
        
        result = risk_manager.cleanup_orphaned_orders()
        
        assert result['status'] == 'success'
        assert len(result['cleaned_orders']) == 2
        assert result['cleaned_orders'][0]['order_id'] == 'old-order-1'
        assert result['cleaned_orders'][1]['order_id'] == 'old-order-2'
        assert len(result['failed_orders']) == 0
        
        # Verify cancel_order was called twice (only for old orders)
        assert risk_manager.broker_adapter.cancel_order.call_count == 2
    
    def test_get_risk_metrics(self, risk_manager):
        """Test getting risk metrics."""
        metrics = risk_manager.get_risk_metrics()
        
        assert 'account' in metrics
        assert metrics['account']['equity'] == 10000.0
        assert metrics['account']['buying_power'] == 20000.0
        
        assert 'positions' in metrics
        assert metrics['positions']['count'] == 2
        assert metrics['positions']['total_value'] == 2800.0
        assert metrics['positions']['equity_allocation'] == 0.28
        
        assert 'daily_performance' in metrics
        assert 'risk_parameters' in metrics
        assert metrics['risk_parameters']['stop_loss_percent'] == 0.02
    
    def test_update_daily_tracking(self, risk_manager):
        """Test updating daily performance tracking."""
        # First get initial values
        initial_equity = risk_manager.daily_performance['current_equity']
        initial_max = risk_manager.daily_performance['max_equity']
        
        # Change the mock response to simulate equity increase
        risk_manager.broker_adapter.get_account_info.return_value = {
            'equity': 10500.0,  # Higher than initial 10000
            'buying_power': 21000.0,
            'cash': 5500.0,
            'currency': 'USD'
        }
        
        # Update tracking
        risk_manager._update_daily_tracking()
        
        # Verify values were updated
        assert risk_manager.daily_performance['current_equity'] == 10500.0
        assert risk_manager.daily_performance['max_equity'] == 10500.0  # New max
        assert risk_manager.daily_performance['start_equity'] == initial_equity  # Unchanged
        
        # Change the mock response to simulate equity decrease
        risk_manager.broker_adapter.get_account_info.return_value = {
            'equity': 9800.0,  # Lower than current
            'buying_power': 19600.0,
            'cash': 4800.0,
            'currency': 'USD'
        }
        
        # Update tracking
        risk_manager._update_daily_tracking()
        
        # Verify min value was updated but max remains
        assert risk_manager.daily_performance['current_equity'] == 9800.0
        assert risk_manager.daily_performance['max_equity'] == 10500.0  # Unchanged
        assert risk_manager.daily_performance['min_equity'] == 9800.0  # New min 