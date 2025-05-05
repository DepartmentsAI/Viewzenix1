"""
Unit tests for the RiskManager class using pytest.
"""
import pytest
import json
import os
from unittest.mock import MagicMock, patch, PropertyMock, call
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import sys
import logging
import time

# Add project root to sys.path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.backend.services.risk_manager import RiskManager, RiskParameters # Ensure models are importable if needed
from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.broker_adapter import BrokerAdapter
# from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter # Avoid direct import if mocking

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Default level set by basicConfig

@pytest.fixture
def mock_broker():
    """Fixture for a mocked BrokerAdapter."""
    adapter = MagicMock(spec=BrokerAdapter)
    # Default account info
    adapter.get_account_info.return_value = {
        'equity': 10000.0, # Use float for easier calcs
        'buying_power': 20000.0,
        'cash': 10000.0,
        'account_number': 'TESTACCT123'
    }
    # Default positions (empty)
    adapter.get_all_positions.return_value = []
    # Default order placement success
    adapter.place_market_order.return_value = {'success': True, 'order_id': 'mock_mkt_123', 'status': 'accepted'}
    adapter.place_limit_order.return_value = {'success': True, 'order_id': 'mock_lmt_123', 'status': 'accepted'}
    adapter.place_stop_order.return_value = {'success': True, 'order_id': 'mock_stp_123', 'status': 'accepted'}
    adapter.place_bracket_order.return_value = {'success': True, 'order_id': 'mock_brk_123', 'status': 'accepted', 'legs': []}
    adapter.cancel_order.return_value = {'success': True}
    adapter.get_order_status.return_value = {'status': 'filled', 'filled_avg_price': '50100'}
    adapter.get_position.return_value = None # Default to no position
    adapter.close_position.return_value = {'success': True, 'order_id': 'mock_close_123'}
    adapter.authenticate.return_value = True # Assume auth succeeds
    return adapter

@pytest.fixture
def mock_order_engine():
     """Fixture for a mocked OrderEngine."""
     engine = MagicMock(spec=OrderEngine)
     # Mock the process_webhook_data to return a success response by default
     engine.process_webhook_data.return_value = {
         'status': 'success',
         'order_id': 'engine_order_123',
         'message': 'Order placed by engine'
     }
     return engine

@pytest.fixture
def risk_manager_instance(mock_broker, mock_order_engine):
    """Fixture for a RiskManager instance with mocked dependencies."""
    # Patch the OrderEngine within the risk_manager module before creating RiskManager
    with patch('src.backend.services.risk_manager.OrderEngine', return_value=mock_order_engine):
        manager = RiskManager(broker_adapter=mock_broker)
        # Ensure metrics are initialized using mock data
        manager._initialize_risk_metrics() 
        # manager.order_engine should now be the mocked instance
        assert manager.order_engine is mock_order_engine 
    return manager

# --- Test Cases --- 

def test_risk_manager_initialization(risk_manager_instance, mock_broker):
    """Test if RiskManager initializes correctly."""
    assert risk_manager_instance is not None
    assert risk_manager_instance.broker_adapter is mock_broker
    assert isinstance(risk_manager_instance.risk_parameters, RiskParameters)
    # Check if metrics were initialized based on mock account info
    assert risk_manager_instance.risk_metrics.starting_equity == 10000.0
    assert risk_manager_instance.risk_metrics.current_equity == 10000.0
    mock_broker.get_account_info.assert_called()
    mock_broker.get_all_positions.assert_called()

def test_update_risk_parameters(risk_manager_instance):
    """Test updating risk parameters."""
    new_params_data = {
        "sl_tp": {"enabled": False, "stop_loss_percent": 0.03, "take_profit_percent": 0.06},
        "portfolio": {"max_daily_drawdown_percent": 0.10, "max_position_size_percent": 0.15, "max_open_positions": 8},
        "cleanup": {"enabled": False, "orphaned_order_age_hours": 48}
    }
    risk_manager_instance.update_risk_parameters(new_params_data)
    
    params = risk_manager_instance.risk_parameters
    assert params.sl_tp.enabled is False
    assert params.sl_tp.stop_loss_percent == 0.03
    assert params.sl_tp.take_profit_percent == 0.06
    assert params.portfolio.max_daily_drawdown_percent == 0.10
    assert params.portfolio.max_position_size_percent == 0.15
    assert params.portfolio.max_open_positions == 8
    assert params.cleanup.enabled is False
    assert params.cleanup.orphaned_order_age_hours == 48

def test_check_portfolio_limits_max_positions_violated(risk_manager_instance, mock_broker):
    """Test portfolio limits check when max open positions is violated."""
    # Arrange: 3 existing positions, limit is 3
    mock_broker.get_all_positions.return_value = [
        {'symbol': 'AAPL', 'qty': '10'}, {'symbol': 'MSFT', 'qty': '5'}, {'symbol': 'GOOG', 'qty': '2'}
    ]
    risk_manager_instance.risk_metrics.open_position_count = 3
    risk_manager_instance.risk_parameters.portfolio.max_open_positions = 3
    
    # Mock order data for a new position
    order_data = {"symbol": "TSLA", "side": "buy", "qty": 1, "price": 200.0}
    
    # Act
    allowed, reason = risk_manager_instance._check_portfolio_limits(order_data)
    
    # Assert
    assert not allowed
    assert "Maximum open positions limit reached" in reason

def test_check_portfolio_limits_position_size_violated(risk_manager_instance):
    """Test portfolio limits check when max position size is violated."""
    # Arrange: Equity 10k, Max size 5% (500 USD), Order value 600 USD
    risk_manager_instance.risk_metrics.current_equity = 10000.0
    risk_manager_instance.risk_parameters.portfolio.max_position_size_percent = 0.05
    order_data = {"symbol": "AMZN", "side": "buy", "qty": 3, "price": 200.0}
    
    # Act
    allowed, reason = risk_manager_instance._check_portfolio_limits(order_data)
    
    # Assert
    assert not allowed
    assert "Exceeds maximum position size limit" in reason

def test_check_portfolio_limits_allowed(risk_manager_instance, mock_broker):
    """Test portfolio limits check when order is within limits."""
    # Arrange: Limit 5 pos, have 2. Limit 10% size, order is 5%.
    mock_broker.get_all_positions.return_value = [{"symbol": "A"}, {"symbol": "B"}]
    risk_manager_instance.risk_metrics.open_position_count = 2
    risk_manager_instance.risk_parameters.portfolio.max_open_positions = 5
    risk_manager_instance.risk_metrics.current_equity = 10000.0
    risk_manager_instance.risk_parameters.portfolio.max_position_size_percent = 0.10
    order_data = {"symbol": "C", "side": "buy", "qty": 5, "price": 100.0} # Value 500 (5%)

    # Act
    allowed, reason = risk_manager_instance._check_portfolio_limits(order_data)

    # Assert
    assert allowed
    assert reason == "Portfolio limits check passed"

def test_check_drawdown_limits_violated(risk_manager_instance):
    """Test drawdown limits check when limit is violated."""
    # Arrange: Start 10k, Current 9k (10% drawdown), Limit 5%
    risk_manager_instance.risk_metrics.starting_equity = 10000.0
    risk_manager_instance.risk_metrics.current_equity = 9000.0 
    risk_manager_instance.risk_parameters.portfolio.max_daily_drawdown_percent = 0.05
    
    # Act
    allowed, reason = risk_manager_instance._check_drawdown_limits("new_order_check")
    
    # Assert
    assert not allowed
    assert "Maximum daily drawdown limit exceeded" in reason
    assert risk_manager_instance.risk_metrics.current_drawdown_percent == 0.10

def test_check_drawdown_limits_ok(risk_manager_instance):
    """Test drawdown limits check when within limits."""
    # Arrange: Start 10k, Current 9.8k (2% drawdown), Limit 5%
    risk_manager_instance.risk_metrics.starting_equity = 10000.0
    risk_manager_instance.risk_metrics.current_equity = 9800.0
    risk_manager_instance.risk_parameters.portfolio.max_daily_drawdown_percent = 0.05

    # Act
    allowed, reason = risk_manager_instance._check_drawdown_limits("test_context")

    # Assert
    assert allowed
    assert reason == "Drawdown limits check passed"
    assert risk_manager_instance.risk_metrics.current_drawdown_percent == 0.02

def test_process_order_rejected_portfolio_limits(risk_manager_instance):
    """Test order processing rejection due to portfolio limits."""
    # Arrange
    order_data = {"symbol": "XYZ", "side": "buy", "qty": 100, "price": 10.0}
    # Make portfolio check fail
    risk_manager_instance.risk_parameters.portfolio.max_open_positions = 0 
    risk_manager_instance.risk_metrics.open_position_count = 0
    
    # Act
    result = risk_manager_instance.process_order_with_risk_management(order_data)
    
    # Assert
    assert result['status'] == 'rejected'
    assert "portfolio limits" in result['reason']
    risk_manager_instance.order_engine.process_webhook_data.assert_not_called()

def test_process_order_rejected_drawdown_limits(risk_manager_instance):
    """Test order processing rejection due to drawdown limits."""
     # Arrange
    order_data = {"symbol": "ABC", "side": "sell", "qty": 5, "price": 50.0}
    # Make drawdown check fail
    risk_manager_instance.risk_metrics.starting_equity = 1000.0
    risk_manager_instance.risk_metrics.current_equity = 800.0 # 20% drawdown
    risk_manager_instance.risk_parameters.portfolio.max_daily_drawdown_percent = 0.10 # 10% limit
    
    # Act
    result = risk_manager_instance.process_order_with_risk_management(order_data)
    
    # Assert
    assert result['status'] == 'rejected'
    assert "drawdown limit" in result['reason']
    risk_manager_instance.order_engine.process_webhook_data.assert_not_called()

def test_process_order_accepted_and_sent_to_engine(risk_manager_instance, mock_order_engine):
    """Test successful order processing passed to OrderEngine."""
    # Arrange: Ensure limits pass
    risk_manager_instance.risk_parameters.portfolio.max_open_positions = 5
    risk_manager_instance.risk_metrics.open_position_count = 1
    risk_manager_instance.risk_parameters.portfolio.max_position_size_percent = 0.20
    risk_manager_instance.risk_metrics.starting_equity = 10000.0
    risk_manager_instance.risk_metrics.current_equity = 9900.0
    risk_manager_instance.risk_parameters.portfolio.max_daily_drawdown_percent = 0.10
    
    order_data = {"symbol": "AAPL", "side": "buy", "qty": 10, "price": 150.0}
    engine_response = {'status': 'success', 'order_id': 'engine123', 'message': 'Passed to engine'}
    mock_order_engine.process_webhook_data.return_value = engine_response
    
    # Act
    result = risk_manager_instance.process_order_with_risk_management(order_data)
    
    # Assert
    # It should return the response from the mocked OrderEngine
    assert result == engine_response
    # Verify OrderEngine was called with the original data + risk status
    mock_order_engine.process_webhook_data.assert_called_once()
    call_args = mock_order_engine.process_webhook_data.call_args[0][0]
    assert call_args['symbol'] == "AAPL"
    assert call_args['risk_check_status'] == 'approved' # Check added field
    assert call_args['risk_check_reason'] == 'Risk checks passed'

# TODO: Add tests for _add_stop_loss_take_profit logic if enabled
# TODO: Add tests for cleanup logic
# TODO: Add tests for metric updates on order fills/pnl
