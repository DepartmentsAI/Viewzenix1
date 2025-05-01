"""
Unit tests for the OrderEngine class.
"""
import pytest
import unittest.mock as mock
from typing import Dict, Any, Optional

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


class TestOrderEngine:
    """Test suite for the OrderEngine class."""
    
    @pytest.fixture
    def mock_broker_adapter(self):
        """Create a MockBrokerAdapter instance."""
        return MockBrokerAdapter()
    
    @pytest.fixture
    def order_engine(self, mock_broker_adapter):
        """Create an OrderEngine instance with a mock broker adapter."""
        return OrderEngine(broker_adapter=mock_broker_adapter)
    
    def test_init(self, order_engine, mock_broker_adapter):
        """Test OrderEngine initialization."""
        assert order_engine.broker_adapter == mock_broker_adapter
        assert order_engine.max_retries == 3
        assert order_engine.retry_delay == 2
    
    def test_determine_trade_type(self, order_engine):
        """Test _determine_trade_type method."""
        assert order_engine._determine_trade_type('long', 'buy') == 'long_entry'
        assert order_engine._determine_trade_type('long', 'sell') == 'long_exit'
        assert order_engine._determine_trade_type('sell', 'sell') == 'short_entry'
        assert order_engine._determine_trade_type('sell', 'buy') == 'short_exit'
        assert order_engine._determine_trade_type('unknown', 'buy') == 'unknown'
    
    def test_determine_order_quantity_with_contracts(self, order_engine):
        """Test _determine_order_quantity with contracts from webhook."""
        qty = order_engine._determine_order_quantity(1.5, 'BTCUSD', 'long_entry')
        assert qty == 1.5
    
    def test_determine_order_quantity_without_contracts(self, order_engine, mock_broker_adapter):
        """Test _determine_order_quantity without contracts."""
        # Set up mock responses
        mock_broker_adapter.set_response('get_account_info', {'equity': '10000'})
        mock_broker_adapter.set_response('get_position', None)
        
        # Call method
        qty = order_engine._determine_order_quantity(None, 'BTCUSD', 'long_entry')
        
        # Verify calls
        assert mock_broker_adapter.calls[0]['method'] == 'get_account_info'
        assert mock_broker_adapter.calls[1]['method'] == 'get_position'
        
        # Verify result
        assert qty == 0.02  # 10000 * 0.02 / 10000 = 0.02
    
    def test_get_current_price(self, order_engine, mock_broker_adapter):
        """Test _get_current_price method."""
        # Test with position
        mock_broker_adapter.set_response('get_position', {'current_price': '50000'})
        price = order_engine._get_current_price('BTCUSD')
        assert price == 50000
        
        # Test without position
        mock_broker_adapter.set_response('get_position', None)
        price = order_engine._get_current_price('BTCUSD')
        assert price == 10000  # Default
    
    def test_process_webhook_data_long_entry(self, order_engine, mock_broker_adapter):
        """Test process_webhook_data for long entry."""
        # Set up mock responses
        mock_broker_adapter.set_response('place_market_order', {'id': 'order-123', 'status': 'filled'})
        
        # Create webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'buy',
            'strategy_order_contracts': 0.1,
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process webhook data
        result = order_engine.process_webhook_data(webhook_data)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['order_id'] == 'order-123'
        assert 'client_order_id' in result
        
        # Verify calls
        place_order_call = None
        for call in mock_broker_adapter.calls:
            if call['method'] == 'place_market_order':
                place_order_call = call
                break
        
        assert place_order_call is not None
        assert place_order_call['args'][0] == 'BTCUSD'  # symbol
        assert place_order_call['args'][1] == 0.1       # quantity
        assert place_order_call['args'][2] == 'buy'     # side
    
    def test_process_webhook_data_short_entry(self, order_engine, mock_broker_adapter):
        """Test process_webhook_data for short entry."""
        # Set up mock responses
        mock_broker_adapter.set_response('place_market_order', {'id': 'order-123', 'status': 'filled'})
        
        # Create webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'sell',
            'strategy_order_action': 'sell',
            'strategy_order_contracts': 0.1,
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process webhook data
        result = order_engine.process_webhook_data(webhook_data)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['order_id'] == 'order-123'
        
        # Verify calls
        place_order_call = None
        for call in mock_broker_adapter.calls:
            if call['method'] == 'place_market_order':
                place_order_call = call
                break
        
        assert place_order_call is not None
        assert place_order_call['args'][0] == 'BTCUSD'  # symbol
        assert place_order_call['args'][1] == 0.1       # quantity
        assert place_order_call['args'][2] == 'sell'    # side
    
    def test_process_webhook_data_long_exit(self, order_engine, mock_broker_adapter):
        """Test process_webhook_data for long exit."""
        # Set up mock responses
        mock_broker_adapter.set_response('get_position', {'symbol': 'BTCUSD', 'qty': 0.1, 'side': 'long'})
        mock_broker_adapter.set_response('close_position', {'symbol': 'BTCUSD', 'status': 'closed'})
        
        # Create webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'sell',
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process webhook data
        result = order_engine.process_webhook_data(webhook_data)
        
        # Verify result
        assert result['status'] == 'success'
        assert 'Successfully closed position' in result['message']
        
        # Verify calls
        get_position_call = None
        close_position_call = None
        for call in mock_broker_adapter.calls:
            if call['method'] == 'get_position':
                get_position_call = call
            elif call['method'] == 'close_position':
                close_position_call = call
        
        assert get_position_call is not None
        assert get_position_call['args'][0] == 'BTCUSD'
        
        assert close_position_call is not None
        assert close_position_call['args'][0] == 'BTCUSD'
    
    def test_process_webhook_data_short_exit(self, order_engine, mock_broker_adapter):
        """Test process_webhook_data for short exit."""
        # Set up mock responses
        mock_broker_adapter.set_response('get_position', {'symbol': 'BTCUSD', 'qty': 0.1, 'side': 'short'})
        mock_broker_adapter.set_response('close_position', {'symbol': 'BTCUSD', 'status': 'closed'})
        
        # Create webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'sell',
            'strategy_order_action': 'buy',
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process webhook data
        result = order_engine.process_webhook_data(webhook_data)
        
        # Verify result
        assert result['status'] == 'success'
        assert 'Successfully closed position' in result['message']
        
        # Verify calls
        get_position_call = None
        close_position_call = None
        for call in mock_broker_adapter.calls:
            if call['method'] == 'get_position':
                get_position_call = call
            elif call['method'] == 'close_position':
                close_position_call = call
        
        assert get_position_call is not None
        assert get_position_call['args'][0] == 'BTCUSD'
        
        assert close_position_call is not None
        assert close_position_call['args'][0] == 'BTCUSD'
    
    def test_process_webhook_data_exit_no_position(self, order_engine, mock_broker_adapter):
        """Test process_webhook_data for exit with no position."""
        # Set up mock responses
        mock_broker_adapter.set_response('get_position', None)
        
        # Create webhook data
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'long',
            'strategy_order_action': 'sell',
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process webhook data
        result = order_engine.process_webhook_data(webhook_data)
        
        # Verify result
        assert result['status'] == 'warning'
        assert 'No position found' in result['message']
        
        # Verify calls
        get_position_call = None
        for call in mock_broker_adapter.calls:
            if call['method'] == 'get_position':
                get_position_call = call
                break
        
        assert get_position_call is not None
        assert get_position_call['args'][0] == 'BTCUSD'
    
    def test_process_webhook_data_invalid_trade_type(self, order_engine):
        """Test process_webhook_data with invalid trade type."""
        # Create webhook data with invalid combination
        webhook_data = {
            'symbol': 'BTCUSD',
            'strategy_order_id': 'invalid',
            'strategy_order_action': 'buy',
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process webhook data
        result = order_engine.process_webhook_data(webhook_data)
        
        # Verify result
        assert result['status'] == 'error'
        assert 'Unknown trade type' in result['message']
    
    def test_process_webhook_data_missing_fields(self, order_engine):
        """Test process_webhook_data with missing fields."""
        # Create webhook data with missing fields
        webhook_data = {
            'symbol': 'BTCUSD',
            # Missing strategy_order_id and strategy_order_action
            'strategy_order_price': 50000,
            'time': 1620000000000
        }
        
        # Process webhook data
        result = order_engine.process_webhook_data(webhook_data)
        
        # Verify result
        assert result['status'] == 'error'
        assert 'Missing required fields' in result['message'] 