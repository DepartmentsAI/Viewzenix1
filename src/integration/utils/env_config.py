"""
Environment Configuration Manager for Integration Services.

This utility provides a unified way to access environment configuration
from various sources (environment variables, config files, etc.).
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

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
            cls._instance = cls()
            cls._instance._load_configuration()
        return cls._instance

    def _load_configuration(self):
        """Load configuration from all available sources."""
        if self._env_loaded:
            return
        
        # Try to load from environment variables directly
        self._load_from_env()
        
        # Try to load from .env file if available
        self._load_from_env_file()
        
        # Fall back to sample config file if needed
        self._load_from_sample_config()
        
        # Set defaults for any missing required values
        self._set_defaults()
        
        self._env_loaded = True

    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Alpaca configuration
        if os.environ.get('ALPACA_PAPER_API_KEY') and os.environ.get('ALPACA_PAPER_API_SECRET'):
            self._config['alpaca'] = {
                'paper_api_key': os.environ.get('ALPACA_PAPER_API_KEY'),
                'paper_api_secret': os.environ.get('ALPACA_PAPER_API_SECRET'),
                'paper_trading': os.environ.get('ALPACA_PAPER_TRADING', 'true').lower() == 'true',
                'base_url': os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
                'source': 'environment'
            }
            logger.info("Loaded Alpaca configuration from environment variables")
        
        # Live API keys if available
        if os.environ.get('ALPACA_LIVE_API_KEY') and os.environ.get('ALPACA_LIVE_API_SECRET'):
            if 'alpaca' not in self._config:
                self._config['alpaca'] = {}
            self._config['alpaca'].update({
                'live_api_key': os.environ.get('ALPACA_LIVE_API_KEY'),
                'live_api_secret': os.environ.get('ALPACA_LIVE_API_SECRET'),
                'source': 'environment'
            })

    def _load_from_env_file(self):
        """Load configuration from .env file."""
        # Look for .env file in integration directory
        env_file = Path(__file__).parent.parent / '.env'
        
        if not env_file.exists():
            logger.debug(".env file not found in integration directory")
            return
        
        try:
            # Parse .env file manually
            config = {}
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
            
            # Extract Alpaca configuration
            if 'ALPACA_PAPER_API_KEY' in config and 'ALPACA_PAPER_API_SECRET' in config:
                self._config['alpaca'] = {
                    'paper_api_key': config.get('ALPACA_PAPER_API_KEY'),
                    'paper_api_secret': config.get('ALPACA_PAPER_API_SECRET'),
                    'paper_trading': config.get('ALPACA_PAPER_TRADING', 'true').lower() == 'true',
                    'base_url': config.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
                    'source': '.env file'
                }
                logger.info("Loaded Alpaca configuration from .env file")
            
            # Live API keys if available
            if 'ALPACA_LIVE_API_KEY' in config and 'ALPACA_LIVE_API_SECRET' in config:
                if 'alpaca' not in self._config:
                    self._config['alpaca'] = {}
                self._config['alpaca'].update({
                    'live_api_key': config.get('ALPACA_LIVE_API_KEY'),
                    'live_api_secret': config.get('ALPACA_LIVE_API_SECRET'),
                    'source': '.env file'
                })
        
        except Exception as e:
            logger.warning(f"Error loading .env file: {str(e)}")

    def _load_from_sample_config(self):
        """Load configuration from sample config file as fallback."""
        # Skip if we already have Alpaca config
        if 'alpaca' in self._config and 'paper_api_key' in self._config['alpaca']:
            return
            
        # Look for sample config file
        sample_file = Path(__file__).parent.parent / 'config.sample.env'
        
        if not sample_file.exists():
            logger.debug("Sample config file not found")
            return
        
        try:
            # Parse sample config file manually
            config = {}
            with open(sample_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
            
            # Extract Alpaca configuration
            if 'ALPACA_PAPER_API_KEY' in config and 'ALPACA_PAPER_API_SECRET' in config:
                self._config['alpaca'] = {
                    'paper_api_key': config.get('ALPACA_PAPER_API_KEY'),
                    'paper_api_secret': config.get('ALPACA_PAPER_API_SECRET'),
                    'paper_trading': config.get('ALPACA_PAPER_TRADING', 'true').lower() == 'true',
                    'base_url': config.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
                    'source': 'sample config'
                }
                logger.warning("Using sample API keys from config.sample.env. This is not recommended for production.")
            
        except Exception as e:
            logger.warning(f"Error loading sample config file: {str(e)}")

    def _set_defaults(self):
        """Set default values for missing required configuration."""
        # Ensure we have at least placeholder values for Alpaca
        if 'alpaca' not in self._config:
            self._config['alpaca'] = {
                'paper_api_key': 'DEFAULT_PLACEHOLDER_KEY',
                'paper_api_secret': 'DEFAULT_PLACEHOLDER_SECRET',
                'paper_trading': True,
                'base_url': 'https://paper-api.alpaca.markets',
                'source': 'default values'
            }
            logger.warning("Using default placeholder values for Alpaca API. These will not work for real API calls.")

    def get_broker_config(self, broker: str) -> Dict[str, Any]:
        """Get configuration for a specific broker.
        
        Args:
            broker: Name of the broker (e.g., 'alpaca')
            
        Returns:
            Dictionary with broker configuration
        """
        if not self._env_loaded:
            self._load_configuration()
            
        if broker not in self._config:
            logger.warning(f"Configuration for broker '{broker}' not found")
            return {}
            
        return self._config[broker]
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """Get a configuration value by path.
        
        Args:
            path: Path to the value, using dot notation (e.g., 'alpaca.paper_api_key')
            default: Default value to return if path not found
            
        Returns:
            Configuration value or default
        """
        if not self._env_loaded:
            self._load_configuration()
            
        parts = path.split('.')
        value = self._config
        
        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default


# Module-level functions for easier access
def get_config_manager() -> EnvConfigManager:
    """Get the singleton config manager instance."""
    return EnvConfigManager.get_instance()

def get_broker_config(broker: str) -> Dict[str, Any]:
    """Get configuration for a specific broker."""
    return get_config_manager().get_broker_config(broker)

def get_config_value(path: str, default: Any = None) -> Any:
    """Get a configuration value by path."""
    return get_config_manager().get_config_value(path, default) 