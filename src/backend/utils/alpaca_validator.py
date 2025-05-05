"""
Alpaca API Credential Validator

This utility verifies that the Alpaca API credentials in the environment
are valid and can connect to the Alpaca API.
"""
import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger("alpaca_validator")

def load_credentials():
    """Load the Alpaca API credentials from environment variables."""
    # Load .env file if it exists
    load_dotenv()
    
    # Get the credentials
    key_id = os.environ.get('APCA_API_KEY_ID')
    secret_key = os.environ.get('APCA_API_SECRET_KEY')
    base_url = os.environ.get('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets/v2')
    
    if not key_id or not secret_key:
        logger.error("Missing Alpaca API credentials in environment variables")
        return None, None, base_url
    
    return key_id, secret_key, base_url

def validate_credentials(key_id, secret_key, base_url):
    """Validate the Alpaca API credentials by making a test API call."""
    if not key_id or not secret_key:
        return False, "Missing API credentials"
    
    try:
        # Try to get account information
        account_url = f"{base_url}/account"
        headers = {
            'APCA-API-KEY-ID': key_id,
            'APCA-API-SECRET-KEY': secret_key
        }
        
        logger.info(f"Testing connection to Alpaca API: {account_url}")
        response = requests.get(account_url, headers=headers)
        
        if response.status_code == 200:
            account_data = response.json()
            logger.info(f"Successfully connected to Alpaca API. Account ID: {account_data.get('id')}")
            return True, account_data
        else:
            logger.error(f"Error connecting to Alpaca API. Status: {response.status_code}, Response: {response.text}")
            return False, f"API Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        logger.error(f"Exception when validating Alpaca credentials: {str(e)}")
        return False, f"Connection Error: {str(e)}"

def verify_trading_status():
    """Verify if the market is open for trading."""
    key_id, secret_key, base_url = load_credentials()
    
    if not key_id or not secret_key:
        return False, "Missing API credentials"
    
    try:
        # Get the market clock
        clock_url = f"{base_url}/clock"
        headers = {
            'APCA-API-KEY-ID': key_id,
            'APCA-API-SECRET-KEY': secret_key
        }
        
        response = requests.get(clock_url, headers=headers)
        
        if response.status_code == 200:
            clock_data = response.json()
            is_open = clock_data.get('is_open', False)
            current_time = datetime.fromisoformat(clock_data.get('timestamp').replace('Z', '+00:00'))
            
            status = "open" if is_open else "closed"
            logger.info(f"Market is currently {status}. Server time: {current_time}")
            
            return True, clock_data
        else:
            logger.error(f"Error getting market clock. Status: {response.status_code}, Response: {response.text}")
            return False, f"API Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        logger.error(f"Exception when checking market status: {str(e)}")
        return False, f"Connection Error: {str(e)}"

if __name__ == "__main__":
    logger.info("Validating Alpaca API credentials...")
    
    # Load credentials
    key_id, secret_key, base_url = load_credentials()
    
    if not key_id or not secret_key:
        logger.error("Alpaca API credentials not found in environment variables.")
        logger.error("Please ensure APCA_API_KEY_ID and APCA_API_SECRET_KEY are set.")
        exit(1)
    
    # Validate credentials
    is_valid, result = validate_credentials(key_id, secret_key, base_url)
    
    if is_valid:
        logger.info("✅ Alpaca API credentials are valid!")
        account_id = result.get('id', 'Unknown')
        account_status = result.get('status', 'Unknown')
        buying_power = result.get('buying_power', 'Unknown')
        
        logger.info(f"Account ID: {account_id}")
        logger.info(f"Account Status: {account_status}")
        logger.info(f"Buying Power: ${buying_power}")
        
        # Check market status
        market_valid, market_data = verify_trading_status()
        
        if market_valid:
            is_open = market_data.get('is_open', False)
            next_open = datetime.fromisoformat(market_data.get('next_open').replace('Z', '+00:00'))
            next_close = datetime.fromisoformat(market_data.get('next_close').replace('Z', '+00:00'))
            
            if is_open:
                logger.info(f"Market is OPEN. Will close at: {next_close}")
            else:
                logger.info(f"Market is CLOSED. Will open at: {next_open}")
    else:
        logger.error(f"❌ Alpaca API validation failed: {result}")
        exit(1)
    
    logger.info("Validation complete.") 