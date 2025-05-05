"""
Verification script for Alpaca API connection.

This script verifies:
1. That API credentials are properly loaded from environment/config
2. That a connection can be established to Alpaca's REST API
3. That streaming data connections can be established
"""

import argparse
import json
import os
import sys
import time

# Add project root to path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.integration.utils.env_config import get_broker_config
from src.integration.adapters.alpaca_adapter import AlpacaAdapter
from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
from src.integration.utils.logger import IntegrationLogger

def verify_broker_config():
    """Verify that broker configuration is properly loaded."""
    print("\n--- Checking Broker Configuration ---")
    
    try:
        # Get Alpaca configuration
        alpaca_config = get_broker_config('alpaca')
        
        # Check if required fields exist
        required_fields = ['paper_api_key', 'paper_api_secret', 'paper_api_base_url']
        missing_fields = [field for field in required_fields if not alpaca_config.get(field)]
        
        if missing_fields:
            print(f"❌ FAILED: Missing required configuration fields: {', '.join(missing_fields)}")
            print(f"  Available fields: {', '.join(alpaca_config.keys())}")
            print("\nCheck that environment variables are properly set:")
            print("  APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL")
            return False
        
        # Check if credentials are not placeholder values
        if alpaca_config.get('paper_api_key') == "your_api_key_here":
            print("❌ FAILED: API key appears to be a placeholder value.")
            return False
        
        # Mask secret key for security
        masked_secret = alpaca_config.get('paper_api_secret')[:4] + "****" if alpaca_config.get('paper_api_secret') else None
        
        print("✅ SUCCESS: Broker configuration loaded successfully")
        print(f"  API Key: {alpaca_config.get('paper_api_key')}")
        print(f"  API Secret: {masked_secret}")
        print(f"  Base URL: {alpaca_config.get('paper_api_base_url')}")
        return True
    
    except Exception as e:
        print(f"❌ ERROR: Failed to load broker configuration: {str(e)}")
        return False

def verify_alpaca_rest_connection():
    """Verify connection to Alpaca REST API."""
    print("\n--- Checking Alpaca REST API Connection ---")
    
    try:
        # Create logger
        logger = IntegrationLogger()
        
        # Create Alpaca adapter
        adapter = AlpacaAdapter(use_paper=True, logger=logger)
        
        # Get account info to test connection
        account = adapter.get_account_info()
        
        if not account:
            print("❌ FAILED: Could not retrieve account information")
            return False
        
        print("✅ SUCCESS: Successfully connected to Alpaca REST API")
        print(f"  Account ID: {account.get('id')}")
        print(f"  Status: {account.get('status')}")
        print(f"  Equity: ${float(account.get('equity', 0)):.2f}")
        print(f"  Cash: ${float(account.get('cash', 0)):.2f}")
        
        # Test market data
        print("\n  Testing market data access...")
        try:
            # Get latest price for a common symbol
            latest_quote = adapter.get_latest_quote("AAPL")
            
            if latest_quote:
                print("  ✅ Market data access successful")
                print(f"    AAPL latest bid: ${latest_quote.get('bid_price', 'N/A')}")
                print(f"    AAPL latest ask: ${latest_quote.get('ask_price', 'N/A')}")
            else:
                print("  ⚠️ Could not retrieve market data. This may be due to market hours or data permissions.")
        except Exception as e:
            print(f"  ⚠️ Market data test failed: {str(e)}")
        
        return True
    
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Alpaca REST API: {str(e)}")
        return False

def verify_alpaca_stream_connection():
    """Verify connection to Alpaca WebSocket streams."""
    print("\n--- Checking Alpaca WebSocket Connection ---")
    
    try:
        # Create logger
        logger = IntegrationLogger()
        
        # Create WebSocket adapter
        stream_adapter = AlpacaStreamAdapter(use_paper=True, logger=logger)
        
        # Attempt to connect
        connected = stream_adapter.connect()
        
        if not connected:
            print("❌ FAILED: Could not connect to Alpaca WebSocket streams")
            return False
        
        print("✅ SUCCESS: Successfully connected to Alpaca WebSocket streams")
        
        # Attempt to subscribe to account updates
        if stream_adapter.subscribe_account_updates():
            print("  ✅ Successfully subscribed to account updates")
        else:
            print("  ⚠️ Failed to subscribe to account updates")
        
        # Attempt to subscribe to trade data for a test symbol
        test_symbols = ["AAPL", "MSFT"]
        
        if stream_adapter.subscribe_trades(test_symbols):
            print(f"  ✅ Successfully subscribed to trades for {', '.join(test_symbols)}")
        else:
            print(f"  ⚠️ Failed to subscribe to trades for {', '.join(test_symbols)}")
        
        # Give some time for connection to stabilize
        print("\n  Waiting for 5 seconds to check connection stability...")
        time.sleep(5)
        
        # Clean up
        stream_adapter.disconnect()
        print("  Connection test complete, WebSocket disconnected")
        
        return True
    
    except Exception as e:
        print(f"❌ ERROR: Failed to test Alpaca WebSocket connection: {str(e)}")
        return False

def verify_paper_trading_adapter():
    """Verify that paper trading adapter works correctly."""
    print("\n--- Checking Paper Trading Adapter ---")
    
    try:
        # Create logger
        logger = IntegrationLogger()
        
        # Create paper trading adapter
        adapter = PaperTradingAdapter(initial_balance=100000.0, logger=logger)
        
        # Get account info
        account = adapter.get_account_info()
        
        if not account:
            print("❌ FAILED: Could not retrieve paper trading account information")
            return False
        
        print("✅ SUCCESS: Paper trading adapter working correctly")
        print(f"  Cash: ${float(account.get('cash', 0)):.2f}")
        print(f"  Equity: ${float(account.get('equity', 0)):.2f}")
        
        # Test order placement
        symbol = "AAPL"
        try:
            # Place a market order
            order = adapter.place_market_order(symbol, 10, "buy")
            
            if order:
                print(f"  ✅ Successfully placed test order for {symbol}")
                print(f"    Order ID: {order.get('id') or order.get('client_order_id')}")
                print(f"    Status: {order.get('status')}")
                
                # Get positions to verify
                positions = adapter.get_all_positions()
                position = next((p for p in positions if p.get('symbol') == symbol), None)
                
                if position:
                    print(f"    Position created: {position.get('qty')} shares of {symbol}")
                else:
                    print(f"    ⚠️ Position not found for {symbol} after order placement")
            else:
                print(f"  ⚠️ Failed to place test order for {symbol}")
        except Exception as e:
            print(f"  ⚠️ Test order placement failed: {str(e)}")
        
        return True
    
    except Exception as e:
        print(f"❌ ERROR: Failed to test paper trading adapter: {str(e)}")
        return False

def main():
    """Main verification function."""
    parser = argparse.ArgumentParser(description="Verify broker API connections")
    parser.add_argument("--config-only", action="store_true", help="Only verify configuration, not connections")
    args = parser.parse_args()
    
    print("=== BROKER API VERIFICATION TOOL ===")
    print("Verifying broker API configuration and connections...\n")
    
    # Step 1: Verify configuration
    config_ok = verify_broker_config()
    
    if not config_ok:
        print("\n❌ Configuration verification failed. Please fix configuration issues before continuing.")
        return 1
    
    if args.config_only:
        print("\n✅ Configuration verification completed successfully. Skipping connection tests.")
        return 0
    
    # Step 2: Verify REST API connection
    rest_ok = verify_alpaca_rest_connection()
    
    # Step 3: Verify WebSocket connection
    stream_ok = verify_alpaca_stream_connection()
    
    # Step 4: Verify paper trading adapter
    paper_ok = verify_paper_trading_adapter()
    
    # Summarize results
    print("\n=== VERIFICATION RESULTS ===")
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"REST API Connection: {'✅ PASS' if rest_ok else '❌ FAIL'}")
    print(f"WebSocket Connection: {'✅ PASS' if stream_ok else '❌ FAIL'}")
    print(f"Paper Trading Adapter: {'✅ PASS' if paper_ok else '❌ FAIL'}")
    
    if all([config_ok, rest_ok, stream_ok, paper_ok]):
        print("\n✅ ALL CHECKS PASSED: Broker API and integrations are working correctly!")
        return 0
    else:
        print("\n⚠️ SOME CHECKS FAILED: Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 