"""
Example demonstrating the AlpacaStreamAdapter for real-time data streaming.

This example shows how to:
1. Connect to Alpaca's WebSocket streams
2. Subscribe to account updates, trade data, quotes, and bars
3. Process real-time data via callbacks
"""

import time
import json
from typing import Dict, Any
import signal
import sys

from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
from src.integration.utils.logger import IntegrationLogger

# Create logger
logger = IntegrationLogger()

# Callback functions for different data types
def order_update_callback(data: Dict[str, Any]) -> None:
    """Handle order updates."""
    print(f"Order Update: {data.get('order', {}).get('id')}")
    print(f"  Status: {data.get('order', {}).get('status')}")
    print(f"  Symbol: {data.get('order', {}).get('symbol')}")
    print(f"  Side: {data.get('order', {}).get('side')}")
    print(f"  Qty: {data.get('order', {}).get('qty')}")
    print(f"  Filled Qty: {data.get('order', {}).get('filled_qty')}")
    print(f"  Type: {data.get('order', {}).get('order_type')}")
    print()

def account_update_callback(data: Dict[str, Any]) -> None:
    """Handle account updates."""
    print(f"Account Update: {data.get('id')}")
    print(f"  Cash: {data.get('cash')}")
    print(f"  Portfolio Value: {data.get('portfolio_value')}")
    print()

def trade_callback(data: Dict[str, Any]) -> None:
    """Handle trade data."""
    print(f"Trade: {data.get('S')} @ {data.get('p')}")
    print(f"  Size: {data.get('s')}")
    print(f"  Timestamp: {data.get('t')}")
    print()

def quote_callback(data: Dict[str, Any]) -> None:
    """Handle quote data."""
    print(f"Quote: {data.get('S')}")
    print(f"  Bid: {data.get('bp')} x {data.get('bs')}")
    print(f"  Ask: {data.get('ap')} x {data.get('as')}")
    print(f"  Timestamp: {data.get('t')}")
    print()

def bar_callback(data: Dict[str, Any]) -> None:
    """Handle bar (OHLCV) data."""
    print(f"Bar: {data.get('S')}")
    print(f"  Open: {data.get('o')}")
    print(f"  High: {data.get('h')}")
    print(f"  Low: {data.get('l')}")
    print(f"  Close: {data.get('c')}")
    print(f"  Volume: {data.get('v')}")
    print(f"  Timestamp: {data.get('t')}")
    print()

def main():
    """Main example function."""
    # Set up signal handler for clean shutdown
    def signal_handler(sig, frame):
        print("Shutting down...")
        if stream_adapter:
            stream_adapter.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create the stream adapter (using paper trading by default)
    stream_adapter = AlpacaStreamAdapter(use_paper=True, logger=logger)
    
    try:
        # Connect to WebSocket endpoints
        print("Connecting to Alpaca WebSocket streams...")
        if not stream_adapter.connect():
            print("Failed to connect to WebSocket streams.")
            return
        
        print("Successfully connected to Alpaca WebSocket streams.")
        
        # Register callbacks
        stream_adapter.register_order_callback(order_update_callback)
        stream_adapter.register_trade_callback("AAPL", trade_callback)
        stream_adapter.register_trade_callback("TSLA", trade_callback)
        stream_adapter.register_quote_callback("AAPL", quote_callback)
        stream_adapter.register_quote_callback("TSLA", quote_callback)
        stream_adapter.register_bar_callback("AAPL", bar_callback)
        stream_adapter.register_bar_callback("TSLA", bar_callback)
        
        # Subscribe to account updates
        print("Subscribing to account updates...")
        if stream_adapter.subscribe_account_updates():
            print("Successfully subscribed to account updates.")
        else:
            print("Failed to subscribe to account updates.")
        
        # Subscribe to market data
        symbols = ["AAPL", "TSLA"]
        
        print(f"Subscribing to trades for: {', '.join(symbols)}")
        if stream_adapter.subscribe_trades(symbols):
            print("Successfully subscribed to trades.")
        else:
            print("Failed to subscribe to trades.")
        
        print(f"Subscribing to quotes for: {', '.join(symbols)}")
        if stream_adapter.subscribe_quotes(symbols):
            print("Successfully subscribed to quotes.")
        else:
            print("Failed to subscribe to quotes.")
        
        print(f"Subscribing to 1-minute bars for: {', '.join(symbols)}")
        if stream_adapter.subscribe_bars(symbols, timeframe="1Min"):
            print("Successfully subscribed to bars.")
        else:
            print("Failed to subscribe to bars.")
        
        print("\nStreaming data... (Press Ctrl+C to exit)")
        print("--------------------------------------------------")
        
        # Keep application running to receive WebSocket data
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("User interrupted. Shutting down...")
    finally:
        # Clean up WebSocket connections
        if stream_adapter:
            stream_adapter.disconnect()
            print("WebSocket connections closed.")

if __name__ == "__main__":
    main() 