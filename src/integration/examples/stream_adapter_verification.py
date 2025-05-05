#!/usr/bin/env python3
"""
Verification script for AlpacaStreamAdapter

This script demonstrates the basic usage of the AlpacaStreamAdapter 
to confirm that WebSocket streaming functionality works correctly.
"""

import os
import sys
import time
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import after path is set
from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
from src.integration.utils.logger import IntegrationLogger

def verify_stream_adapter():
    """
    Verify that AlpacaStreamAdapter can connect to Alpaca API streams.
    """
    print("=== ALPACA STREAM ADAPTER VERIFICATION ===")
    
    # Create logger for events
    logger = IntegrationLogger()
    
    # Create adapter with paper trading mode
    adapter = AlpacaStreamAdapter(use_paper=True, logger=logger)
    
    # Connect to WebSocket streams
    print("Connecting to Alpaca WebSocket streams...")
    connected = adapter.connect()
    
    if not connected:
        print("❌ Failed to connect to Alpaca WebSocket streams")
        return False
    
    print("✅ Successfully connected to WebSocket streams")
    
    # Define callback for trades
    def on_trade(trade_data):
        print(f"Trade received: {trade_data}")
    
    # Set callbacks
    adapter.set_trade_callback(on_trade)
    
    # Subscribe to account updates
    print("Subscribing to account updates...")
    if adapter.subscribe_account_updates():
        print("✅ Subscribed to account updates")
    else:
        print("❌ Failed to subscribe to account updates")
    
    # Subscribe to trades for test symbols
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    print(f"Subscribing to trades for {', '.join(test_symbols)}...")
    
    if adapter.subscribe_trades(test_symbols):
        print(f"✅ Subscribed to trades for {', '.join(test_symbols)}")
    else:
        print(f"❌ Failed to subscribe to trades for {', '.join(test_symbols)}")
    
    # Keep connection open for a bit to observe behavior
    print("\nKeeping connection open for 15 seconds to check for messages...")
    print("(You may see trade data appear if markets are open)")
    try:
        for i in range(15):
            sys.stdout.write(f"\rTime remaining: {15-i} seconds")
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nVerification interrupted by user")
    
    # Disconnect
    print("\n\nDisconnecting from WebSocket streams...")
    adapter.disconnect()
    print("✅ Disconnected from WebSocket streams")
    
    return True

if __name__ == "__main__":
    success = verify_stream_adapter()
    sys.exit(0 if success else 1) 