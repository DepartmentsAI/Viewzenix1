"""
Environment Configuration Manager for Integration Services.

This utility provides a unified way to access environment configuration
from various sources (environment variables, config files, etc.).
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvConfigManager:
    """Manages loading and accessing environment configuration."""

    _instance = None
    _config = {}
    _env_loaded = False

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = EnvConfigManager()
        return cls._instance

    def __init__(self):
        """Initialize the config manager."""
        if not self._env_loaded:
            self._load_environment()

    def _load_environment(self):
        """Load environment variables from various sources with fallbacks."""
        # Try to load from .env file
        env_file = Path(__file__).parent.parent / ".env"
        sample_env_file = Path(__file__).parent.parent / "config.sample.env"
        
        # Primary .env file
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
        # Fall back to sample file if available
        elif sample_env_file.exists():
            load_dotenv(sample_env_file)
            logger.info(f"Loaded environment from {sample_env_file} (sample config)")
        
        # Load all config into the dictionary
        self._load_alpaca_config()
        
        EnvConfigManager._env_loaded = True
        logger.info("Environment configuration loaded successfully")

    def _load_alpaca_config(self):
        """Load Alpaca-specific configuration."""
        # Check for paper trading environment
        paper_trading = os.environ.get("ALPACA_PAPER_TRADING", "true").lower() == "true"
        
        # Determine which keys to use based on paper trading setting
        key_name = "ALPACA_PAPER_API_KEY" if paper_trading else "ALPACA_LIVE_API_KEY"
        secret_name = "ALPACA_PAPER_API_SECRET" if paper_trading else "ALPACA_LIVE_API_SECRET"
        
        # Get the keys with fallbacks for testing environments
        api_key = os.environ.get(key_name, os.environ.get("ALPACA_API_KEY", "demo_key_for_testing"))
        api_secret = os.environ.get(secret_name, os.environ.get("ALPACA_API_SECRET", "demo_secret_for_testing"))
        
        # Determine base URL
        if paper_trading:
            base_url = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        else:
            base_url = os.environ.get("ALPACA_BASE_URL", "https://api.alpaca.markets")
        
        # Store in config dictionary
        self._config.update({
            "alpaca": {
                "api_key": api_key,
                "api_secret": api_secret,
                "base_url": base_url,
                "paper_trading": paper_trading
            }
        })
        
        # Log loading status (redacting actual secrets)
        logger.info(f"Loaded Alpaca configuration (paper_trading={paper_trading}, " 
                   f"key={api_key[:4]}****, using_sample={'demo_key' in api_key})")

    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config

    def get_broker_config(self, broker_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific broker.
        
        Args:
            broker_name: Name of the broker (e.g., 'alpaca')
            
        Returns:
            Dictionary of configuration values or None if not found
        """
        return self._config.get(broker_name)

# Convenience function to get the config manager
def get_config_manager() -> EnvConfigManager:
    """Get the configuration manager instance."""
    return EnvConfigManager.get_instance()

def get_alpaca_config(logger=None):
    """
    Get the Alpaca API configuration from environment variables.
    
    Args:
        logger: Optional integration logger for recording configuration loading
        
    Returns:
        Dictionary with Alpaca API configuration parameters
    """
    # Import from adapters directory to avoid circular imports
    from src.integration.adapters.config import get_alpaca_config as get_config
    return get_config(logger) 