import unittest
from unittest import mock
import websocket

from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
from src.integration.utils.logger import IntegrationLogger

class TestWebsocketConnection(unittest.TestCase):
    """Test the websocket connection functionality."""

    def test_websocket_import(self):
        """Test that websocket-client is correctly installed and importable."""
        # This test passes if the import statement above works
        self.assertTrue(hasattr(websocket, 'WebSocketApp'))
        
    @mock.patch('websocket.WebSocketApp')
    def test_alpaca_stream_adapter_creation(self, mock_websocket_app):
        """Test that AlpacaStreamAdapter can be instantiated with mocked WebSocket."""
        # Create a logger
        logger = IntegrationLogger()
        
        # Create the adapter
        adapter = AlpacaStreamAdapter(use_paper=True, logger=logger)
        
        # Verify the adapter was created
        self.assertIsNotNone(adapter)
        self.assertTrue(isinstance(adapter, AlpacaStreamAdapter))
        
        # Verify that we can mock the WebSocket functionality
        adapter.connect()
        mock_websocket_app.assert_called()
        
if __name__ == "__main__":
    unittest.main() 