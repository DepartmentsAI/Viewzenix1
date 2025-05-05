import unittest
from unittest.mock import patch, MagicMock
import json
import os
import requests
from datetime import datetime

from src.integration.adapters.alpaca_adapter import AlpacaAdapter
# Import our configuration utility for testing
from src.integration.utils.env_config import EnvConfigManager, get_config_manager

class TestAlpacaAdapter(unittest.TestCase):
    """Test cases for the AlpacaAdapter class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Mock environment variables for API keys
        os.environ["ALPACA_PAPER_API_KEY"] = "test_api_key"
        os.environ["ALPACA_PAPER_API_SECRET"] = "test_api_secret"
        
        # Create a mock logger to avoid file operations
        self.mock_logger = MagicMock()
        
        # Patch the config manager to use our test values
        self.patch_config = patch.object(EnvConfigManager, 'get_broker_config')
        self.mock_get_broker_config = self.patch_config.start()
        self.mock_get_broker_config.return_value = {
            'paper_api_key': 'test_api_key',
            'paper_api_secret': 'test_api_secret',
            'paper_trading': True,
            'base_url': 'https://paper-api.alpaca.markets',
            'source': 'test'
        }
        
        # Patch the _make_request method to avoid real API calls
        self.make_request_patcher = patch.object(AlpacaAdapter, '_make_request')
        self.mock_make_request = self.make_request_patcher.start()
        
        # Set up mock response for authentication
        self.mock_make_request.return_value = {"account_number": "TEST123"}
        
        # Initialize adapter with mocked logger
        self.adapter = AlpacaAdapter(use_paper=True, logger=self.mock_logger)
    
    def tearDown(self):
        """Clean up after each test."""
        # Stop all patches
        self.make_request_patcher.stop()
        self.patch_config.stop()
        
        # Clear environment variables
        if "ALPACA_PAPER_API_KEY" in os.environ:
            del os.environ["ALPACA_PAPER_API_KEY"]
        if "ALPACA_PAPER_API_SECRET" in os.environ:
            del os.environ["ALPACA_PAPER_API_SECRET"]
    
    def test_init_and_authenticate(self):
        """Test initialization and authentication."""
        # Authentication already happens in setUp
        self.assertTrue(self.adapter.authenticated)
        self.assertEqual(self.adapter.api_key, "test_api_key")
        self.assertEqual(self.adapter.api_secret, "test_api_secret")
        self.assertEqual(self.adapter.base_url, AlpacaAdapter.PAPER_BASE_URL)
        
        # Verify _make_request was called with the account endpoint
        self.mock_make_request.assert_called_once_with("GET", "/account", {})
    
    def test_place_market_order(self):
        """Test placing a market order."""
        # Set up mock response for order placement
        order_response = {
            "id": "test-order-id",
            "client_order_id": "alpaca-123456-abcdef",
            "status": "accepted",
            "type": "market",
            "side": "buy",
            "symbol": "AAPL",
            "qty": "10",
            "filled_qty": "0"
        }
        self.mock_make_request.reset_mock()
        self.mock_make_request.return_value = order_response
        
        # Call the method under test
        result = self.adapter.place_market_order("AAPL", 10, "buy", "test-client-id")
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["order_id"], "test-order-id")
        self.assertEqual(result["symbol"], "AAPL")
        
        # Verify _make_request was called correctly
        self.mock_make_request.assert_called_once()
        method, endpoint, params = self.mock_make_request.call_args[0]
        self.assertEqual(method, "POST")
        self.assertEqual(endpoint, "/orders")
        self.assertEqual(params["symbol"], "AAPL")
        self.assertEqual(params["qty"], "10")
        self.assertEqual(params["side"], "buy")
        self.assertEqual(params["type"], "market")
        self.assertEqual(params["client_order_id"], "test-client-id")
    
    def test_place_limit_order(self):
        """Test placing a limit order."""
        # Set up mock response
        order_response = {
            "id": "test-limit-id",
            "client_order_id": "alpaca-123456-ghijkl",
            "status": "accepted",
            "type": "limit",
            "side": "sell",
            "symbol": "TSLA",
            "qty": "5",
            "limit_price": "950.50",
            "filled_qty": "0"
        }
        self.mock_make_request.reset_mock()
        self.mock_make_request.return_value = order_response
        
        # Call the method under test
        result = self.adapter.place_limit_order("TSLA", 5, "sell", 950.50)
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["order_id"], "test-limit-id")
        self.assertEqual(result["order_type"], "limit")
        
        # Verify _make_request was called correctly
        self.mock_make_request.assert_called_once()
        method, endpoint, params = self.mock_make_request.call_args[0]
        self.assertEqual(method, "POST")
        self.assertEqual(endpoint, "/orders")
        self.assertEqual(params["symbol"], "TSLA")
        self.assertEqual(params["qty"], "5")
        self.assertEqual(params["side"], "sell")
        self.assertEqual(params["type"], "limit")
        self.assertEqual(params["limit_price"], "950.5")
    
    def test_place_bracket_order(self):
        """Test placing a bracket order."""
        # Set up mock response
        order_response = {
            "id": "test-bracket-id",
            "client_order_id": "alpaca-123456-mnopqr",
            "status": "accepted",
            "type": "market",
            "side": "buy",
            "symbol": "BTCUSD",
            "qty": "0.1",
            "filled_qty": "0",
            "order_class": "bracket",
            "legs": [
                {"id": "tp-leg-id", "type": "limit"},
                {"id": "sl-leg-id", "type": "stop"}
            ]
        }
        self.mock_make_request.reset_mock()
        self.mock_make_request.return_value = order_response
        
        # Call the method under test
        result = self.adapter.place_bracket_order(
            symbol="BTC/USD",
            qty=0.1,
            side="buy",
            take_profit_price=65000,
            stop_loss_price=60000
        )
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["order_id"], "test-bracket-id")
        
        # Verify _make_request was called correctly
        self.mock_make_request.assert_called_once()
        method, endpoint, params = self.mock_make_request.call_args[0]
        self.assertEqual(method, "POST")
        self.assertEqual(endpoint, "/orders")
        self.assertEqual(params["symbol"], "BTCUSD")  # Note: format conversion
        self.assertEqual(params["qty"], "0.1")
        self.assertEqual(params["side"], "buy")
        self.assertEqual(params["type"], "market")
        self.assertEqual(params["order_class"], "bracket")
        self.assertEqual(params["take_profit"]["limit_price"], "65000")
        self.assertEqual(params["stop_loss"]["stop_price"], "60000")
    
    def test_get_position(self):
        """Test getting a position."""
        # Set up mock response
        position_response = {
            "symbol": "AAPL",
            "qty": "15",
            "avg_entry_price": "150.25",
            "market_value": "2275.50",
            "side": "long"
        }
        self.mock_make_request.reset_mock()
        self.mock_make_request.return_value = position_response
        
        # Call the method under test
        result = self.adapter.get_position("AAPL")
        
        # Verify the result
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["qty"], "15")
        
        # Verify _make_request was called correctly
        self.mock_make_request.assert_called_once_with("GET", "/positions/AAPL", {})
    
    def test_get_position_not_found(self):
        """Test getting a position that doesn't exist."""
        # Set up mock response to simulate a 404 error
        http_error = requests.exceptions.HTTPError()
        response_mock = MagicMock()
        response_mock.status_code = 404
        http_error.response = response_mock
        self.mock_make_request.reset_mock()
        self.mock_make_request.side_effect = http_error
        
        # Call the method under test
        result = self.adapter.get_position("NONEXISTENT")
        
        # Verify the result is None for a non-existent position
        self.assertIsNone(result)
        
        # Verify _make_request was called correctly
        self.mock_make_request.assert_called_once_with("GET", "/positions/NONEXISTENT", {})
    
    def test_close_position(self):
        """Test closing a position."""
        # Set up mock response
        close_response = {
            "symbol": "TSLA",
            "side": "buy",
            "qty": "5",
            "status": "accepted"
        }
        self.mock_make_request.reset_mock()
        self.mock_make_request.return_value = close_response
        
        # Call the method under test
        result = self.adapter.close_position("TSLA")
        
        # Verify the result
        self.assertEqual(result["symbol"], "TSLA")
        self.assertEqual(result["status"], "accepted")
        
        # Verify _make_request was called correctly
        self.mock_make_request.assert_called_once_with("DELETE", "/positions/TSLA", {})
    
    def test_get_account_info(self):
        """Test getting account information."""
        # Set up mock response
        account_response = {
            "account_number": "TEST123",
            "cash": "100000.50",
            "equity": "125000.75",
            "buying_power": "200000.00",
            "status": "ACTIVE"
        }
        self.mock_make_request.reset_mock()
        self.mock_make_request.return_value = account_response
        
        # Call the method under test
        result = self.adapter.get_account_info()
        
        # Verify the result
        self.assertEqual(result["account_number"], "TEST123")
        self.assertEqual(result["cash"], "100000.50")
        
        # Verify _make_request was called correctly
        self.mock_make_request.assert_called_once_with("GET", "/account", {})
    
    def test_error_handling_in_place_order(self):
        """Test error handling when placing an order."""
        # Set up mock to raise an exception
        self.mock_make_request.reset_mock()
        self.mock_make_request.side_effect = Exception("API error")
        
        # Call the method under test
        result = self.adapter.place_market_order("AAPL", 10, "buy")
        
        # Verify the error result
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("API error", result["error"])
        
        # Verify logger was called with error
        self.mock_logger.log_error.assert_called_with(
            "order_placement_error", 
            "Failed to place order: API error", 
            details={"params": dict}
        )
    
    def test_format_symbol(self):
        """Test symbol formatting for different input formats."""
        test_cases = [
            ("AAPL", "AAPL"),
            ("BTC/USD", "BTCUSD"),
            ("ETH-USD", "ETHUSD"),
            ("XRP.USD", "XRPUSD"),
            ("BTC-USDT", "BTCUSDT")
        ]
        
        for input_symbol, expected_output in test_cases:
            self.assertEqual(self.adapter._format_symbol(input_symbol), expected_output)

if __name__ == "__main__":
    unittest.main() 