"""
Unit tests for the AlpacaStreamAdapter with focus on WebSocket and risk management integration
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

# Import module to be tested
from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter


class TestAlpacaStreamAdapter(unittest.TestCase):
    """Test cases for the AlpacaStreamAdapter"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create mock environment variables
        self.env_patcher = mock.patch.dict(os.environ, {
            'ALPACA_API_KEY': 'test_api_key',
            'ALPACA_API_SECRET': 'test_api_secret',
            'ALPACA_API_BASE_URL': 'https://paper-api.alpaca.markets',
            'ALPACA_WS_URL': 'wss://paper-api.alpaca.markets/stream'
        })
        self.env_patcher.start()
        
        # Mock the WebSocket client
        self.ws_patcher = mock.patch('src.integration.adapters.alpaca_stream_adapter.websocket.WebSocketApp')
        self.mock_ws = self.ws_patcher.start()
        
        # Create the adapter instance with all external dependencies mocked
        self.adapter = AlpacaStreamAdapter(paper_trading=True)
        
        # Mock the internal WebSocket instance
        self.adapter.ws = mock.MagicMock()
        
        # Track callback registrations
        self.trade_callbacks = []
        self.quote_callbacks = []
        self.status_callbacks = []
        
        # Store original methods to use in mocked replacements
        self.original_on_trade = self.adapter.on_trade
        self.original_on_quote = self.adapter.on_quote
        self.original_on_status = self.adapter.on_status
        
        # Mock the decorator methods to capture registrations
        def mock_on_trade(callback):
            self.trade_callbacks.append(callback)
            return self.original_on_trade(callback)
        
        def mock_on_quote(callback):
            self.quote_callbacks.append(callback)
            return self.original_on_quote(callback)
        
        def mock_on_status(callback):
            self.status_callbacks.append(callback)
            return self.original_on_status(callback)
        
        self.adapter.on_trade = mock_on_trade
        self.adapter.on_quote = mock_on_quote
        self.adapter.on_status = mock_on_status
    
    def tearDown(self):
        """Clean up after each test"""
        self.env_patcher.stop()
        self.ws_patcher.stop()
    
    def test_adapter_initialization(self):
        """Test that the adapter initializes correctly"""
        self.assertEqual(self.adapter.api_key, 'test_api_key')
        self.assertEqual(self.adapter.api_secret, 'test_api_secret')
        self.assertEqual(self.adapter.base_url, 'https://paper-api.alpaca.markets')
        self.assertEqual(self.adapter.ws_url, 'wss://paper-api.alpaca.markets/stream')
        self.assertTrue(self.adapter.paper_trading)
    
    def test_connect_initializes_websocket(self):
        """Test that connect() initializes the WebSocket connection"""
        # Set up the mock
        self.adapter.ws = None
        
        # Call the method
        self.adapter.connect()
        
        # Verify WebSocketApp was created
        self.mock_ws.assert_called_once()
        
        # Verify URL contains API key and secret
        call_args = self.mock_ws.call_args[0]
        self.assertIn('wss://paper-api.alpaca.markets/stream', call_args[0])
    
    def test_subscribe_to_trades(self):
        """Test that subscribe_to_trades sends the correct message"""
        # Set up the mock
        self.adapter.ws = mock.MagicMock()
        self.adapter.authenticated = True
        
        # Call the method
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        self.adapter.subscribe_to_trades(symbols)
        
        # Verify send was called with the correct message
        expected_msg = json.dumps({
            'action': 'subscribe',
            'trades': symbols
        })
        self.adapter.ws.send.assert_called_with(expected_msg)
    
    def test_on_trade_decorator(self):
        """Test that the on_trade decorator registers callbacks correctly"""
        # Define a test callback
        def test_callback(trade_data):
            pass
        
        # Register the callback
        decorated = self.adapter.on_trade(test_callback)
        
        # Verify the callback was registered
        self.assertIn(test_callback, self.trade_callbacks)
    
    def test_process_trade_message(self):
        """Test that trade messages are processed and callbacks are executed"""
        # Create a mock callback
        mock_callback = mock.Mock()
        
        # Register the callback
        self.adapter.on_trade(mock_callback)
        
        # Create a sample trade message
        trade_msg = {
            'T': 't',  # Message type is 'trade'
            'S': 'AAPL',  # Symbol
            'p': 150.25,  # Price
            's': 100,  # Size (shares)
            't': datetime.now().isoformat()  # Timestamp
        }
        
        # Call the internal message handler (would normally be called by WebSocket)
        self.adapter._process_stream_message(json.dumps(trade_msg))
        
        # Verify callback was called with the trade data
        mock_callback.assert_called_once_with(trade_msg)
    
    def test_risk_management_integration(self):
        """Test integration with risk management through callbacks"""
        # Create mock risk manager
        mock_risk_manager = mock.MagicMock()
        mock_risk_manager.process_market_data.return_value = [{
            'action': 'stop_loss',
            'symbol': 'AAPL',
            'qty': 10,
            'reason': 'Price below stop loss threshold'
        }]
        
        # Create mock order executor
        mock_order_executor = mock.MagicMock()
        
        # Create a risk management callback that uses the risk manager
        @self.adapter.on_trade
        def handle_trade(trade_data):
            symbol = trade_data.get('S')
            price = float(trade_data.get('p', 0))
            
            # Process market data through risk manager
            actions = mock_risk_manager.process_market_data(symbol, price)
            
            # Handle any generated actions
            for action in actions:
                mock_order_executor.execute_order(action)
        
        # Create a sample trade message
        trade_msg = {
            'T': 't',  # Message type is 'trade'
            'S': 'AAPL',  # Symbol
            'p': 145.75,  # Price - below stop loss
            's': 100,  # Size (shares)
            't': datetime.now().isoformat()  # Timestamp
        }
        
        # Call the internal message handler
        self.adapter._process_stream_message(json.dumps(trade_msg))
        
        # Verify risk manager was called with correct data
        mock_risk_manager.process_market_data.assert_called_once_with('AAPL', 145.75)
        
        # Verify order executor was called with the stop loss action
        mock_order_executor.execute_order.assert_called_once()
        call_args = mock_order_executor.execute_order.call_args[0][0]
        self.assertEqual(call_args['action'], 'stop_loss')
        self.assertEqual(call_args['symbol'], 'AAPL')
    
    def test_reconnection_logic(self):
        """Test that the adapter attempts to reconnect on connection loss"""
        # Set up mocks
        self.adapter.ws = mock.MagicMock()
        self.adapter.connected = True
        self.adapter._connect = mock.MagicMock()
        
        # Register a status callback to track connection status
        status_tracker = mock.MagicMock()
        self.adapter.on_status(status_tracker)
        
        # Simulate connection loss by calling on_close
        self.adapter._on_close(None)
        
        # Verify status callback was called with disconnected status
        status_tracker.assert_called_with(False, mock.ANY, mock.ANY)
        
        # Verify reconnect attempt
        self.adapter._connect.assert_called_once()


if __name__ == '__main__':
    unittest.main() 