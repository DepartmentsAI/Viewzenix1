"""
Broker configuration management for integration adapters.

This module provides a unified way to manage broker API configuration
with support for environment variables, configuration files, and defaults.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class BrokerConfig:
    """Configuration manager for broker API credentials and settings."""
    
    _instance = None
    _initialized = False
    _config = {}
    
    @staticmethod
    def get_instance():
        """Get or create the singleton instance."""
        if BrokerConfig._instance is None:
            BrokerConfig._instance = BrokerConfig()
        return BrokerConfig._instance
    
    def __init__(self):
        """Initialize the broker configuration manager."""
        if not BrokerConfig._initialized:
            self._load_environment()
            BrokerConfig._initialized = True
    
    def _load_environment(self):
        """Load configuration from environment variables and files with fallbacks."""
        # Define the potential locations of environment files
        env_paths = [
            Path(os.getcwd()) / ".env",                         # Current directory
            Path(os.getcwd()) / "src" / "integration" / ".env", # Project structure
            Path(__file__).parent.parent / ".env",              # Integration directory
        ]
        
        # Load env files if they exist (first match takes precedence)
        env_loaded = False
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment from {env_path}")
                env_loaded = True
                break
        
        # If no .env file found, try fallbacks
        if not env_loaded:
            # Check for sample config
            sample_path = Path(__file__).parent.parent / "config.sample.env"
            if sample_path.exists():
                load_dotenv(sample_path)
                logger.info(f"Loaded environment from {sample_path} (sample config)")
                env_loaded = True
        
        # Always load default values for Alpaca config
        self._load_alpaca_config()
    
    def _load_alpaca_config(self):
        """Load Alpaca API configuration with fallbacks."""
        # Determine if we're using paper trading
        paper_trading = os.environ.get("ALPACA_PAPER_TRADING", "true").lower() in ("true", "1", "yes")
        
        # Determine which API keys to use based on environment
        if paper_trading:
            api_key = os.environ.get("ALPACA_PAPER_API_KEY", 
                      os.environ.get("ALPACA_API_KEY", "demo_paper_key"))
            api_secret = os.environ.get("ALPACA_PAPER_API_SECRET", 
                         os.environ.get("ALPACA_API_SECRET", "demo_paper_secret"))
            base_url = os.environ.get("ALPACA_PAPER_BASE_URL", 
                       os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"))
        else:
            api_key = os.environ.get("ALPACA_LIVE_API_KEY", 
                      os.environ.get("ALPACA_API_KEY", ""))
            api_secret = os.environ.get("ALPACA_LIVE_API_SECRET", 
                         os.environ.get("ALPACA_API_SECRET", ""))
            base_url = os.environ.get("ALPACA_LIVE_BASE_URL", 
                       os.environ.get("ALPACA_BASE_URL", "https://api.alpaca.markets"))
        
        # Add data API URL
        data_url = os.environ.get("ALPACA_DATA_URL", "https://data.alpaca.markets")
        
        # Store the configuration
        self._config["alpaca"] = {
            "api_key": api_key,
            "api_secret": api_secret,
            "base_url": base_url,
            "data_url": data_url,
            "paper_trading": paper_trading
        }
        
        # Log configuration status (never log full secrets)
        key_preview = api_key[:4] + "****" if len(api_key) > 4 else "****"
        logger.info(f"Loaded Alpaca configuration: paper_trading={paper_trading}, key={key_preview}")
        
        # Log warning if using demo keys
        if "demo_paper_key" in api_key:
            logger.warning("Using demo Alpaca keys. This is only appropriate for testing.")
    
    def get_alpaca_config(self) -> Dict[str, Any]:
        """Get Alpaca API configuration.
        
        Returns:
            Dictionary with Alpaca configuration values
        """
        return self._config.get("alpaca", {})
    
    def get_broker_config(self, broker_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific broker.
        
        Args:
            broker_name: Name of the broker (e.g., 'alpaca')
            
        Returns:
            Dictionary of configuration values or None if not found
        """
        return self._config.get(broker_name.lower())
    
    def is_using_default_credentials(self, broker_name: str) -> bool:
        """Check if we're using default/demo credentials for a broker.
        
        Args:
            broker_name: Name of the broker (e.g., 'alpaca')
            
        Returns:
            True if using default credentials, False if using real credentials
        """
        config = self.get_broker_config(broker_name)
        if not config:
            return True
        
        if broker_name.lower() == "alpaca":
            return "demo_paper_key" in config.get("api_key", "")
        
        return False

# Convenience function to get broker configuration
def get_broker_config(broker_name: str = "alpaca") -> Dict[str, Any]:
    """Get configuration for a specific broker.
    
    Args:
        broker_name: Name of the broker (e.g., 'alpaca')
        
    Returns:
        Dictionary of configuration values (empty dict if not found)
    """
    config = BrokerConfig.get_instance().get_broker_config(broker_name)
    return config or {}

def get_alpaca_config(logger=None):
    """
    Get the Alpaca API configuration from environment variables.
    
    Args:
        logger: Optional integration logger for recording configuration loading
        
    Returns:
        Dictionary with Alpaca API configuration parameters
    """
    # Determine if using paper trading
    use_paper = os.environ.get("ALPACA_PAPER_TRADING", "true").lower() == "true"
    
    # Get API keys based on environment
    if use_paper:
        api_key = os.environ.get("ALPACA_PAPER_API_KEY", "test-paper-key")
        api_secret = os.environ.get("ALPACA_PAPER_API_SECRET", "test-paper-secret")
    else:
        api_key = os.environ.get("ALPACA_LIVE_API_KEY", "")
        api_secret = os.environ.get("ALPACA_LIVE_API_SECRET", "")
    
    # Build config
    config = {
        "paper_trading": use_paper,
        "paper_api_key": os.environ.get("ALPACA_PAPER_API_KEY", "test-paper-key"),
        "paper_api_secret": os.environ.get("ALPACA_PAPER_API_SECRET", "test-paper-secret"),
        "live_api_key": os.environ.get("ALPACA_LIVE_API_KEY", ""),
        "live_api_secret": os.environ.get("ALPACA_LIVE_API_SECRET", ""),
        "paper_api_base_url": os.environ.get("ALPACA_PAPER_API_URL", "https://paper-api.alpaca.markets"),
        "live_api_base_url": os.environ.get("ALPACA_LIVE_API_URL", "https://api.alpaca.markets"),
        "paper_data_feed_url": os.environ.get("ALPACA_PAPER_DATA_URL", "https://data.alpaca.markets"),
        "live_data_feed_url": os.environ.get("ALPACA_LIVE_DATA_URL", "https://data.alpaca.markets"),
        "paper_ws_url": os.environ.get("ALPACA_PAPER_WS_URL", "wss://paper-api.alpaca.markets/stream"),
        "live_ws_url": os.environ.get("ALPACA_LIVE_WS_URL", "wss://api.alpaca.markets/stream"),
        "data_ws_url": os.environ.get("ALPACA_DATA_WS_URL", "wss://stream.data.alpaca.markets/v2/iex"),
    }
    
    # Log configuration if logger provided
    if logger:
        # Mask API keys for security when logging
        masked_key = api_key[:4] + "****" if api_key else "None"
        if hasattr(logger, 'log_info'):
            logger.log_info("alpaca_config_loaded", f"Loaded Alpaca configuration: paper_trading={use_paper}, key={masked_key}")
        else:
            # Fallback if logger doesn't have log_info
            logging.info(f"Loaded Alpaca configuration: paper_trading={use_paper}, key={masked_key}")
    else:
        # Use standard logging if no custom logger
        masked_key = api_key[:4] + "****" if api_key else "None"
        logging.info(f"Loaded Alpaca configuration: paper_trading={use_paper}, key={masked_key}")
    
    return config 