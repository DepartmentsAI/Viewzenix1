import os
from typing import Tuple, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ApiKeyManager:
    """Utility class for managing API keys securely.
    
    Handles loading API keys from environment variables or secure storage.
    """
    
    @staticmethod
    def load_api_keys_from_env(api_key_name: str, api_secret_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Load API key and secret from environment variables.
        
        Args:
            api_key_name: Name of the environment variable containing the API key
            api_secret_name: Name of the environment variable containing the API secret
            
        Returns:
            Tuple of (api_key, api_secret) or (None, None) if not found
        """
        # Try to load from .env file if it exists
        load_dotenv()
        
        api_key = os.environ.get(api_key_name)
        api_secret = os.environ.get(api_secret_name)
        
        if not api_key or not api_secret:
            logger.warning(f"API credentials not found in environment variables: {api_key_name}, {api_secret_name}")
            return None, None
        
        return api_key, api_secret
        
    @staticmethod
    def validate_api_keys(api_key: Optional[str], api_secret: Optional[str]) -> bool:
        """Validate that API keys are present and have expected format.
        
        Args:
            api_key: The API key to validate
            api_secret: The API secret to validate
            
        Returns:
            bool: True if keys are valid, False otherwise
        """
        if not api_key or not api_secret:
            return False
            
        # Basic validation - can be extended with broker-specific validation
        if len(api_key) < 5 or len(api_secret) < 5:
            logger.warning("API keys appear to be too short or invalid")
            return False
            
        return True 