#!/usr/bin/env python

"""
Simple verification script to test broker configuration.
This will check if:
1. The websocket-client package is installed
2. Environment variables are loaded properly 
3. The API keys are accessible
"""

import os
import sys
import logging
import importlib
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verification")

def main():
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check current directory
    logger.info(f"Current directory: {os.path.abspath(os.curdir)}")
    
    # Check for websocket-client
    try:
        import websocket
        logger.info(f"websocket-client version: {websocket.__version__}")
    except ImportError:
        logger.error("websocket-client package not installed. Run: pip install websocket-client")
        return 1
    
    # Make sure path is set up correctly
    sys.path.insert(0, os.path.abspath(os.curdir))
    
    # Check environment variables
    try:
        from dotenv import load_dotenv
        
        # Try to load .env files
        env_loaded = False
        # Try integration directory
        env_path = Path('./src/integration/.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded environment from {env_path}")
            env_loaded = True
            
        # Try workspace root
        if os.path.exists(Path('.env')):
            load_dotenv()
            logger.info("Loaded environment from workspace root .env")
            env_loaded = True
            
        # Try sample config
        sample_path = Path('./src/integration/config.sample.env')
        if os.path.exists(sample_path):
            load_dotenv(dotenv_path=sample_path)
            logger.info(f"Loaded environment from {sample_path} (sample config)")
            env_loaded = True
            
        if not env_loaded:
            logger.warning("No environment file found")
    except ImportError:
        logger.error("python-dotenv package not installed. Run: pip install python-dotenv")
        return 1
    
    # Display environment variables (masked)
    logger.info("Checking environment variables:")
    paper_trading = os.environ.get("ALPACA_PAPER_TRADING", "true")
    paper_key = os.environ.get("ALPACA_PAPER_API_KEY", "")
    paper_secret = os.environ.get("ALPACA_PAPER_API_SECRET", "")
    
    logger.info(f"ALPACA_PAPER_TRADING: {paper_trading}")
    masked_key = paper_key[:4] + "****" if paper_key else "None"
    logger.info(f"ALPACA_PAPER_API_KEY: {masked_key}")
    masked_secret = paper_secret[:4] + "****" if paper_secret else "None"
    logger.info(f"ALPACA_PAPER_API_SECRET: {masked_secret}")
    
    # Try importing broker configuration
    try:
        sys.path.insert(0, os.path.abspath('./src'))
        from integration.adapters.config import get_alpaca_config
        config = get_alpaca_config()
        logger.info("Successfully imported broker configuration")
        logger.info(f"Paper trading mode: {config.get('paper_trading', False)}")
        key = config.get('paper_api_key', '')
        masked_key = key[:4] + "****" if key else "None"
        logger.info(f"API key: {masked_key}")
    except Exception as e:
        logger.error(f"Error importing broker configuration: {str(e)}")
        
    logger.info("Verification complete")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 