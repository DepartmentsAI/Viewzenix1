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
    _config: Dict[str, Dict[str, Any]] = {}
    _env_loaded = False

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_configuration()
        return cls._instance

    def _load_configuration(self):
        """Load configuration from all available sources in order of priority."""
        if self._env_loaded:
            logger.debug("Configuration already loaded.")
            return
        
        logger.info("Loading environment configuration...")
        
        # Priority: Environment Variables > .env File > Sample Config File > Defaults
        self._load_from_env()
        self._load_from_env_file(overwrite=False)
        self._load_from_sample_config(overwrite=False)
        
        # Set defaults for any missing required values after loading
        self._set_defaults()
        
        self._env_loaded = True
        logger.info("Environment configuration loading complete.")

    def _load_from_env(self):
        """Load configuration from environment variables."""
        logger.debug("Attempting to load configuration from environment variables...")
        alpaca_config = {}
        loaded = False

        # Paper keys take precedence if ALPACA_PAPER_TRADING is true or default
        paper_trading_env = os.environ.get('ALPACA_PAPER_TRADING', 'true').lower() == 'true'
        
        paper_key = os.environ.get('ALPACA_PAPER_API_KEY')
        paper_secret = os.environ.get('ALPACA_PAPER_API_SECRET')
        live_key = os.environ.get('ALPACA_LIVE_API_KEY')
        live_secret = os.environ.get('ALPACA_LIVE_API_SECRET')
        base_url = os.environ.get('ALPACA_BASE_URL')

        if paper_key and paper_secret:
             alpaca_config['paper_api_key'] = paper_key
             alpaca_config['paper_api_secret'] = paper_secret
             alpaca_config['paper_trading'] = True
             loaded = True
        
        if live_key and live_secret:
             alpaca_config['live_api_key'] = live_key
             alpaca_config['live_api_secret'] = live_secret
             if not loaded:
                  alpaca_config['paper_trading'] = False
             loaded = True

        # If any keys were loaded, set base_url and source
        if loaded:
            # Set base_url based on paper_trading, allowing override from env
            is_paper = alpaca_config.get('paper_trading', paper_trading_env)
            default_url = 'https://paper-api.alpaca.markets' if is_paper else 'https://api.alpaca.markets'
            alpaca_config['base_url'] = base_url or default_url
            alpaca_config['source'] = 'environment'
            self._config['alpaca'] = alpaca_config
            logger.info("Loaded Alpaca configuration from environment variables")
        else:
             logger.debug("No complete Alpaca key pairs found in environment variables.")

    def _load_from_file(self, file_path: Path, source_name: str, overwrite: bool = True):
         """Helper to load key-value pairs from a file."""
         if not file_path.exists():
             logger.debug(f"{source_name} file not found at {file_path}")
             return {}
         
         file_config = {}
         try:
             with open(file_path, 'r') as f:
                 for line in f:
                     line = line.strip()
                     if not line or line.startswith('#') or '=' not in line:
                         continue
                     key, value = line.split('=', 1)
                     # Remove potential quotes from value
                     value = value.strip().strip('"').strip("'") 
                     file_config[key.strip()] = value
             logger.debug(f"Successfully parsed {source_name} file: {file_path}")
             return file_config
         except Exception as e:
             logger.warning(f"Error loading {source_name} file ({file_path}): {str(e)}")
             return {}

    def _update_config_from_file_data(self, file_data: Dict[str, str], source_name: str, overwrite: bool):
         """Updates the internal config with data loaded from a file."""
         if not file_data:
              return

         alpaca_config = self._config.get('alpaca', {}) 
         updated = False
         file_alpaca_config = {}

         paper_key = file_data.get('ALPACA_PAPER_API_KEY')
         paper_secret = file_data.get('ALPACA_PAPER_API_SECRET')
         live_key = file_data.get('ALPACA_LIVE_API_KEY')
         live_secret = file_data.get('ALPACA_LIVE_API_SECRET')
         paper_trading_file = file_data.get('ALPACA_PAPER_TRADING', 'true').lower() == 'true'
         base_url_file = file_data.get('ALPACA_BASE_URL')

         if paper_key and paper_secret:
              file_alpaca_config['paper_api_key'] = paper_key
              file_alpaca_config['paper_api_secret'] = paper_secret
              file_alpaca_config['paper_trading'] = True
              updated = True
         
         if live_key and live_secret:
              file_alpaca_config['live_api_key'] = live_key
              file_alpaca_config['live_api_secret'] = live_secret
              if not updated:
                   file_alpaca_config['paper_trading'] = False
              updated = True

         if updated:
             is_paper = file_alpaca_config.get('paper_trading', paper_trading_file)
             default_url = 'https://paper-api.alpaca.markets' if is_paper else 'https://api.alpaca.markets'
             file_alpaca_config['base_url'] = base_url_file or default_url
             file_alpaca_config['source'] = source_name
             
             # Merge with existing config respecting overwrite flag
             if 'alpaca' not in self._config or overwrite:
                 self._config['alpaca'] = {**alpaca_config, **file_alpaca_config}
                 logger.info(f"Loaded/Updated Alpaca configuration from {source_name}")
             else:
                 # Only add keys if they don't exist in the current config
                 original_source = self._config['alpaca'].get('source', 'unknown')
                 for key, value in file_alpaca_config.items():
                      if key not in self._config['alpaca']:
                           self._config['alpaca'][key] = value
                 # Update source if we added anything
                 if self._config['alpaca'].get('source') == original_source and len(self._config['alpaca']) > len(alpaca_config):
                      self._config['alpaca']['source'] = source_name 
                 logger.info(f"Configuration from {source_name} considered, but higher priority source already exists.")
         else:
              logger.debug(f"No complete Alpaca key pairs found in {source_name} data.")

    def _load_from_env_file(self, overwrite: bool = True):
        """Load configuration from .env file."""
        env_file = Path(__file__).parent.parent / '.env'
        logger.debug(f"Attempting to load configuration from {env_file} (overwrite={overwrite})...")
        file_data = self._load_from_file(env_file, '.env file', overwrite)
        self._update_config_from_file_data(file_data, '.env file', overwrite)

    def _load_from_sample_config(self, overwrite: bool = True):
        """Load configuration from sample config file as fallback."""
        sample_file = Path(__file__).parent.parent / 'config.sample.env'
        logger.debug(f"Attempting to load configuration from {sample_file} (overwrite={overwrite})...")
        file_data = self._load_from_file(sample_file, 'sample .env file', overwrite)
        self._update_config_from_file_data(file_data, 'sample .env file', overwrite)

    def _set_defaults(self):
        """Set default values if configuration is missing."""
        if 'alpaca' not in self._config:
            logger.warning("Alpaca configuration missing. Setting defaults for testing/fallback.")
            self._config['alpaca'] = {
                'paper_api_key': 'DEFAULT_PLACEHOLDER_PAPER_KEY',
                'paper_api_secret': 'DEFAULT_PLACEHOLDER_PAPER_SECRET',
                'live_api_key': 'DEFAULT_PLACEHOLDER_LIVE_KEY',
                'live_api_secret': 'DEFAULT_PLACEHOLDER_LIVE_SECRET',
                'paper_trading': True,
                'base_url': 'https://paper-api.alpaca.markets',
                'source': 'defaults'
            }
        else:
             # Ensure essential keys have defaults even if partially loaded
             alpaca_conf = self._config['alpaca']
             alpaca_conf.setdefault('paper_trading', True)
             is_paper = alpaca_conf['paper_trading']
             default_url = 'https://paper-api.alpaca.markets' if is_paper else 'https://api.alpaca.markets'
             alpaca_conf.setdefault('base_url', default_url)
             alpaca_conf.setdefault('paper_api_key', 'DEFAULT_PLACEHOLDER_PAPER_KEY')
             alpaca_conf.setdefault('paper_api_secret', 'DEFAULT_PLACEHOLDER_PAPER_SECRET')
             alpaca_conf.setdefault('live_api_key', 'DEFAULT_PLACEHOLDER_LIVE_KEY')
             alpaca_conf.setdefault('live_api_secret', 'DEFAULT_PLACEHOLDER_LIVE_SECRET')
             alpaca_conf.setdefault('source', 'unknown')

    def get_broker_config(self, broker: str, use_paper: Optional[bool] = None) -> Dict[str, Any]:
        """Get configuration for a specific broker, optionally selecting paper/live keys.
        
        Args:
            broker: Name of the broker (e.g., 'alpaca')
            use_paper: If True, prioritizes paper keys. If False, prioritizes live keys. 
                       If None, returns all keys.
            
        Returns:
            Dictionary of configuration values for the specified broker and mode.
        """
        broker_conf = self._config.get(broker, {}).copy()
        
        if broker == 'alpaca' and use_paper is not None:
             if use_paper:
                  broker_conf['api_key'] = broker_conf.get('paper_api_key')
                  broker_conf['api_secret'] = broker_conf.get('paper_api_secret')
                  if 'paper-api.alpaca.markets' not in broker_conf.get('base_url',''):
                      broker_conf['base_url'] = 'https://paper-api.alpaca.markets' 
             else:
                  broker_conf['api_key'] = broker_conf.get('live_api_key')
                  broker_conf['api_secret'] = broker_conf.get('live_api_secret')
                  if 'api.alpaca.markets' not in broker_conf.get('base_url',''):
                       broker_conf['base_url'] = 'https://api.alpaca.markets'
             broker_conf['paper_trading'] = use_paper

        return broker_conf

    def get_config_value(self, path: str, default: Any = None) -> Any:
        """Get a specific configuration value using dot notation (e.g., 'alpaca.api_key')."""
        keys = path.split('.')
        value = self._config
        try:
            for key in keys:
                if isinstance(value, dict):
                     value = value[key]
                else:
                     return default
            return value
        except KeyError:
            return default

# --- Global Access Functions --- 

def get_config_manager() -> EnvConfigManager:
    """Convenience function to get the EnvConfigManager instance."""
    return EnvConfigManager.get_instance()

def get_broker_config(broker: str, use_paper: Optional[bool] = None) -> Dict[str, Any]:
    """Convenience function to get broker configuration."""
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
=======
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
>>>>>>> develop
