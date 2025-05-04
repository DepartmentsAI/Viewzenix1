import unittest
import os
import sys
from unittest import mock

# Import the function to test
from src.integration.utils.env_config import get_alpaca_config

class TestEnvConfig(unittest.TestCase):
    """Test the env_config module."""

    @mock.patch.dict(os.environ, {
        "ALPACA_PAPER_TRADING": "true",
        "ALPACA_PAPER_API_KEY": "test-paper-key",
        "ALPACA_PAPER_API_SECRET": "test-paper-secret",
        "ALPACA_LIVE_API_KEY": "test-live-key",
        "ALPACA_LIVE_API_SECRET": "test-live-secret"
    })
    def test_get_alpaca_config(self):
        """Test that get_alpaca_config can load config from environment variables."""
        # Call the function
        config = get_alpaca_config()
        
        # Verify the expected values are present
        self.assertIsNotNone(config)
        self.assertTrue(config.get("paper_trading"))
        self.assertEqual(config.get("paper_api_key"), "test-paper-key")
        self.assertEqual(config.get("paper_api_secret"), "test-paper-secret")
        self.assertEqual(config.get("live_api_key"), "test-live-key")
        self.assertEqual(config.get("live_api_secret"), "test-live-secret")
        
        # Verify the basic URL configurations
        self.assertIn("alpaca.markets", config.get("paper_api_base_url", ""))
        
    @mock.patch("src.integration.utils.logger.IntegrationLogger")
    @mock.patch.dict(os.environ, {
        "ALPACA_PAPER_TRADING": "true",
        "ALPACA_PAPER_API_KEY": "test-paper-key",
        "ALPACA_PAPER_API_SECRET": "test-paper-secret"
    })
    def test_get_alpaca_config_with_logging(self, mock_logger):
        """Test that get_alpaca_config logs appropriately."""
        # Call the function
        config = get_alpaca_config(logger=mock_logger)
        
        # Verify the logger was called
        mock_logger.log_info.assert_called()
        
if __name__ == "__main__":
    print("Running test_env_config.py")
    print(f"Python version: {sys.version}")
    print(f"Module search paths: {sys.path}")
    unittest.main() 