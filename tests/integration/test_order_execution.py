"""
Integration tests for the Order Execution Engine.
Tests interaction between Order Execution Engine and broker adapters.
"""
import pytest
import os
import json
from unittest import mock
from typing import Dict, Any

from src.backend.services.order_engine import OrderEngine
from src.backend.services.risk_manager import RiskManager
from src.integration.adapters.alpaca_adapter import AlpacaAdapter
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter


@pytest.fixture
def mock_risk_manager():
    """Create a mock RiskManager for testing."""
    risk_manager = mock.MagicMock(spec=RiskManager)
    # Set up default behaviors
    risk_manager.validate_order.return_value = (True, "Order validated")
    return risk_manager


@pytest.fixture
def mock_alpaca_adapter():
    """Create a mock AlpacaAdapter for testing."""
    with mock.patch('src.integration.adapters.alpaca_adapter.AlpacaAdapter', autospec=True) as mock_adapter_class:
        mock_adapter = mock_adapter_class.return_value
        
        # Set up default behaviors
        mock_adapter.authenticate.return_value = True
        mock_adapter.get_account_info.return_value = {"equity": "10000"}
        mock_adapter.place_market_order.return_value = {"id": "test-order-id", "status": "filled"}
        mock_adapter.place_limit_order.return_value = {"id": "test-limit-order-id", "status": "new"}
        mock_adapter.get_position.return_value = None
        mock_adapter.close_position.return_value = {"symbol": "BTCUSD", "status": "closed"}
        
        yield mock_adapter


@pytest.fixture
def mock_paper_trading_adapter():
    """Create a mock PaperTradingAdapter for testing."""
    with mock.patch('src.integration.adapters.paper_trading_adapter.PaperTradingAdapter', autospec=True) as mock_adapter_class:
        mock_adapter = mock_adapter_class.return_value
        
        # Set up default behaviors
        mock_adapter.authenticate.return_value = True
        mock_adapter.get_account_info.return_value = {"equity": "10000"}
        mock_adapter.place_market_order.return_value = {"id": "paper-order-id", "status": "filled"}
        mock_adapter.place_limit_order.return_value = {"id": "paper-limit-order-id", "status": "new"}
        mock_adapter.get_position.return_value = None
        mock_adapter.close_position.return_value = {"symbol": "BTCUSD", "status": "closed"}
        
        yield mock_adapter


@pytest.fixture
def webhook_data():
    """Load webhook test data from fixtures."""
    webhook_path = os.path.join(os.path.dirname(__file__), '..', 'e2e', 'fixtures', 'data', 'webhook_examples.json')
    with open(webhook_path, 'r') as f:
        webhook_examples = json.load(f)
    return webhook_examples


class TestOrderEngineIntegration:
    """Integration tests for OrderEngine's interaction with adapters and services."""
    
    def test_order_engine_with_alpaca_adapter(self, mock_alpaca_adapter, webhook_data):
        """Test OrderEngine's integration with AlpacaAdapter."""
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Process a long entry webhook
        long_entry_data = webhook_data.get("long_entry", {})
        if long_entry_data:
            result = order_engine.process_webhook_data(long_entry_data)
            
            # Verify the result
            assert result['status'] == 'success'
            assert 'order_id' in result
            
            # Verify adapter was called correctly
            mock_alpaca_adapter.place_market_order.assert_called_once()
            call_args = mock_alpaca_adapter.place_market_order.call_args[0]
            assert call_args[0] == long_entry_data['symbol']  # symbol
            assert call_args[2] == 'buy'  # side
    
    def test_order_engine_with_paper_trading_adapter(self, mock_paper_trading_adapter, webhook_data):
        """Test OrderEngine's integration with PaperTradingAdapter."""
        # Create OrderEngine with the mock PaperTradingAdapter
        order_engine = OrderEngine(broker_adapter=mock_paper_trading_adapter)
        
        # Process a short entry webhook
        short_entry_data = webhook_data.get("short_entry", {})
        if short_entry_data:
            result = order_engine.process_webhook_data(short_entry_data)
            
            # Verify the result
            assert result['status'] == 'success'
            assert 'order_id' in result
            
            # Verify adapter was called correctly
            mock_paper_trading_adapter.place_market_order.assert_called_once()
            call_args = mock_paper_trading_adapter.place_market_order.call_args[0]
            assert call_args[0] == short_entry_data['symbol']  # symbol
            assert call_args[2] == 'sell'  # side
    
    def test_order_engine_position_closing(self, mock_alpaca_adapter, webhook_data):
        """Test OrderEngine's position closing with AlpacaAdapter."""
        # Set up mock to have an existing position
        mock_alpaca_adapter.get_position.return_value = {
            "symbol": "BTCUSD",
            "qty": "0.1",
            "side": "long",
            "avg_entry_price": "50000",
            "current_price": "55000",
            "unrealized_pl": "500"
        }
        
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Process a long exit webhook
        long_exit_data = webhook_data.get("long_exit", {})
        if long_exit_data:
            result = order_engine.process_webhook_data(long_exit_data)
            
            # Verify the result
            assert result['status'] == 'success'
            assert 'closed position' in result['message'].lower()
            
            # Verify adapter was called correctly
            mock_alpaca_adapter.get_position.assert_called_with(long_exit_data['symbol'])
            mock_alpaca_adapter.close_position.assert_called_with(long_exit_data['symbol'])
    
    def test_order_engine_with_risk_validation(self, mock_alpaca_adapter, mock_risk_manager, webhook_data):
        """Test OrderEngine integration with RiskManager for order validation."""
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Patch the risk manager into the order engine
        with mock.patch.object(order_engine, '_validate_with_risk_manager', 
                              wraps=lambda order_data: mock_risk_manager.validate_order(order_data)):
            
            # Set up risk manager to approve the order
            mock_risk_manager.validate_order.return_value = (True, "Order approved")
            
            # Process a long entry webhook
            long_entry_data = webhook_data.get("long_entry", {})
            if long_entry_data:
                result = order_engine.process_webhook_data(long_entry_data)
                
                # Verify the risk manager was called
                mock_risk_manager.validate_order.assert_called_once()
                
                # Verify the order was placed
                assert result['status'] == 'success'
                assert 'order_id' in result
                mock_alpaca_adapter.place_market_order.assert_called_once()
    
    def test_order_engine_with_risk_rejection(self, mock_alpaca_adapter, mock_risk_manager, webhook_data):
        """Test OrderEngine rejects orders that fail risk validation."""
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Patch the risk manager into the order engine
        with mock.patch.object(order_engine, '_validate_with_risk_manager', 
                              wraps=lambda order_data: mock_risk_manager.validate_order(order_data)):
            
            # Set up risk manager to reject the order
            mock_risk_manager.validate_order.return_value = (False, "Order rejected: Position size exceeds limit")
            
            # Process a long entry webhook
            long_entry_data = webhook_data.get("long_entry", {})
            if long_entry_data:
                result = order_engine.process_webhook_data(long_entry_data)
                
                # Verify the risk manager was called
                mock_risk_manager.validate_order.assert_called_once()
                
                # Verify the order was rejected
                assert result['status'] == 'error'
                assert 'rejected' in result['message'].lower()
                assert 'position size exceeds limit' in result['message'].lower()
                
                # Verify no order was placed
                mock_alpaca_adapter.place_market_order.assert_not_called()
    
    def test_limit_order_placement(self, mock_alpaca_adapter, webhook_data):
        """Test OrderEngine can place limit orders with AlpacaAdapter."""
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Process a limit order webhook
        limit_order_data = webhook_data.get("limit_order", {})
        if limit_order_data:
            result = order_engine.process_webhook_data(limit_order_data)
            
            # Verify the result
            assert result['status'] == 'success'
            assert 'order_id' in result
            
            # Verify adapter was called correctly
            mock_alpaca_adapter.place_limit_order.assert_called_once()
            call_args = mock_alpaca_adapter.place_limit_order.call_args[0]
            assert call_args[0] == limit_order_data['symbol']  # symbol
            assert call_args[3] == limit_order_data['strategy_order_price']  # limit_price
    
    def test_order_with_stop_loss_take_profit(self, mock_alpaca_adapter, webhook_data, mock_risk_manager):
        """Test OrderEngine applies stop-loss and take-profit from risk management."""
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Patch the risk manager into the order engine
        with mock.patch.object(order_engine, '_validate_with_risk_manager', 
                              wraps=lambda order_data: mock_risk_manager.validate_order(order_data)):
            
            # Set up risk manager to approve the order with SL/TP levels
            mock_risk_manager.validate_order.return_value = (
                True, 
                {
                    "message": "Order approved with risk management",
                    "stop_loss": 45000,
                    "take_profit": 60000
                }
            )
            
            # Process a long entry webhook
            long_entry_data = webhook_data.get("long_entry", {})
            if long_entry_data:
                result = order_engine.process_webhook_data(long_entry_data)
                
                # Verify the risk manager was called
                mock_risk_manager.validate_order.assert_called_once()
                
                # Verify bracket order was placed
                mock_alpaca_adapter.place_bracket_order.assert_called_once()
                call_args = mock_alpaca_adapter.place_bracket_order.call_args[0]
                call_kwargs = mock_alpaca_adapter.place_bracket_order.call_args[1]
                
                assert call_args[0] == long_entry_data['symbol']  # symbol
                assert call_args[2] == 'buy'  # side
                assert call_kwargs.get('stop_loss_price') == 45000
                assert call_kwargs.get('take_profit_price') == 60000
    
    def test_broker_adapter_error_handling(self, mock_alpaca_adapter, webhook_data):
        """Test OrderEngine handles broker adapter errors gracefully."""
        # Set up the adapter to raise an exception
        mock_alpaca_adapter.place_market_order.side_effect = Exception("API Connection Error")
        
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Process a long entry webhook
        long_entry_data = webhook_data.get("long_entry", {})
        if long_entry_data:
            result = order_engine.process_webhook_data(long_entry_data)
            
            # Verify the result shows an error
            assert result['status'] == 'error'
            assert 'error' in result['message'].lower()
            
            # Verify the adapter method was called
            mock_alpaca_adapter.place_market_order.assert_called_once()
    
    def test_invalid_webhook_data_handling(self, mock_alpaca_adapter):
        """Test OrderEngine handles invalid webhook data gracefully."""
        # Create OrderEngine with the mock AlpacaAdapter
        order_engine = OrderEngine(broker_adapter=mock_alpaca_adapter)
        
        # Empty webhook data
        result = order_engine.process_webhook_data({})
        assert result['status'] == 'error'
        assert 'missing required fields' in result['message'].lower()
        
        # Invalid webhook data
        result = order_engine.process_webhook_data({"symbol": "BTCUSD", "invalid_field": "value"})
        assert result['status'] == 'error'
        assert 'missing required fields' in result['message'].lower()
        
        # Verify no orders were placed
        mock_alpaca_adapter.place_market_order.assert_not_called()
        mock_alpaca_adapter.place_limit_order.assert_not_called()
        mock_alpaca_adapter.close_position.assert_not_called() 