"""
WebSocket streaming adapter for Alpaca Markets.

This module provides real-time data streaming from Alpaca Markets via WebSockets,
including account updates, order status changes, and market data.
"""

import json
import logging
import threading
import time
import websocket
from typing import Dict, Any, List, Optional, Callable, Set

from src.integration.utils.env_config import get_broker_config
from src.integration.utils.logger import IntegrationLogger

class AlpacaStreamAdapter:
    """
    Adapter for Alpaca Markets WebSocket API.
    
    Provides real-time streaming of:
    - Account updates
    - Order status changes
    - Trade executions
    - Market data (quotes, trades, bars)
    """
    
    # WebSocket endpoints
    PAPER_ACCOUNT_URL = "wss://paper-api.alpaca.markets/stream"
    LIVE_ACCOUNT_URL = "wss://api.alpaca.markets/stream"
    # Updated based on documentation: data stream URL format changed
    PAPER_DATA_URL = "wss://stream.data.alpaca.markets/v2/sip" # Use sip for free data
    LIVE_DATA_URL = "wss://stream.data.alpaca.markets/v2/sip" # Use sip for free data
    
    # Reconnection parameters
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 3
    RECONNECT_BACKOFF_FACTOR = 1.5
    
    # Heartbeat parameters - Alpaca doesn't require client-side heartbeats, connection managed by ping/pong
    # HEARTBEAT_INTERVAL = 30
    # MISSED_HEARTBEATS_THRESHOLD = 3 
    CONNECTION_CHECK_INTERVAL = 15 # Check connection status periodically
    
    def __init__(self, use_paper: bool = True, logger: Optional[IntegrationLogger] = None):
        """
        Initialize the Alpaca WebSocket adapter.
        
        Args:
            use_paper: Whether to use paper trading API (True) or live trading API (False)
            logger: Optional integration logger instance
        """
        self.use_paper = use_paper
        self.logger = logger or IntegrationLogger()
        self.logger.log_info("alpaca_stream_init", f"Initializing AlpacaStreamAdapter (Paper Mode: {self.use_paper})")
        
        # Get broker configuration
        self.alpaca_config = get_broker_config('alpaca', use_paper=self.use_paper)
        
        # Get appropriate API keys and URLs
        if not self.alpaca_config or not self.alpaca_config.get('api_key') or not self.alpaca_config.get('api_secret'):
             self.logger.log_error("config_error", "Missing Alpaca API key/secret in configuration.")
             # Raise configuration error or handle appropriately
             raise ValueError("Missing Alpaca API key/secret in configuration.")

        self.api_key = self.alpaca_config.get('api_key')
        self.api_secret = self.alpaca_config.get('api_secret')
        self.account_url = self.PAPER_ACCOUNT_URL if self.use_paper else self.LIVE_ACCOUNT_URL
        self.market_data_url = self.PAPER_DATA_URL if self.use_paper else self.LIVE_DATA_URL
        self.config_source = self.alpaca_config.get('source', 'unknown')
        self.logger.log_info("config_loaded", f"Loaded Alpaca config from {self.config_source}")
        
        # WebSocket connections
        self.account_ws: Optional[websocket.WebSocketApp] = None
        self.market_data_ws: Optional[websocket.WebSocketApp] = None
        
        # Connection and subscription state
        self.is_account_connected = False
        self.is_market_data_connected = False
        self.account_authenticated = False # Track authentication status for streams
        self.market_data_authenticated = False
        self.account_subscriptions: Set[str] = set() # e.g., {"account_updates", "trade_updates"}
        self.market_data_subscriptions: Dict[str, Set[str]] = {"trades": set(), "quotes": set(), "bars": set()}
        
        # Callback registries - Structure: { topic: callback_function }
        # Account topics: "account_updates", "trade_updates"
        # Market topics: "trades/SYMBOL", "quotes/SYMBOL", "bars/SYMBOL"
        self.callbacks: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self.connection_status_callback: Optional[Callable[[str, bool], None]] = None # Callback for connection status changes

        # Threading 
        self.account_thread: Optional[threading.Thread] = None
        self.market_data_thread: Optional[threading.Thread] = None
        self.should_run = threading.Event() # Use Event for signaling threads
        self.reconnect_attempts: Dict[str, int] = {"account": 0, "market_data": 0}
    
    def connect(self) -> bool:
        """
        Establish connections to Alpaca WebSocket endpoints in separate threads.
        
        Returns:
            bool: True if initial connection attempts were initiated successfully.
        """
        if not self.api_key or not self.api_secret:
             self.logger.log_error("connect_error", "Cannot connect: API keys not configured.")
             return False

        self.logger.log_info("connect_start", "Attempting to connect to Alpaca WebSocket endpoints...")
        self.should_run.set() # Signal threads to run
        
        # Connect to account stream in a new thread
        self.account_thread = threading.Thread(target=self._run_account_connection, name="AlpacaAccountWS", daemon=True)
        self.account_thread.start()
        
        # Connect to market data stream in a new thread
        self.market_data_thread = threading.Thread(target=self._run_market_data_connection, name="AlpacaMarketDataWS", daemon=True)
        self.market_data_thread.start()

        # Give threads a moment to establish initial connection
        time.sleep(2) 
        
        # Return status based on whether threads are alive (doesn't guarantee connection yet)
        account_started = self.account_thread is not None and self.account_thread.is_alive()
        market_data_started = self.market_data_thread is not None and self.market_data_thread.is_alive()
        
        if account_started and market_data_started:
             self.logger.log_info("connect_initiated", "WebSocket connection threads started.")
             return True
        else:
             self.logger.log_error("connect_error", "Failed to start WebSocket connection threads.")
             self.disconnect() # Cleanup if threads failed to start
             return False

    def _run_account_connection(self):
        """Manages the account WebSocket connection loop, including reconnection."""
        while self.should_run.is_set():
             self.logger.log_info("account_connect_attempt", f"Connecting to account stream: {self.account_url}")
             self.account_ws = websocket.WebSocketApp(
                 self.account_url,
                 on_open=self._on_account_open,
                 on_message=self._on_account_message,
                 on_error=self._on_account_error,
                 on_close=self._on_account_close
             )
             # Run forever handles reconnect internally based on on_close logic
             self.account_ws.run_forever(ping_interval=20, ping_timeout=10) 

             # If run_forever exits and we should still be running, it means a disconnect happened
             if self.should_run.is_set():
                  self.is_account_connected = False
                  self.account_authenticated = False
                  if self.connection_status_callback:
                       self.connection_status_callback("account", False)
                  
                  self.reconnect_attempts["account"] += 1
                  if self.reconnect_attempts["account"] <= self.MAX_RECONNECT_ATTEMPTS:
                       delay = self.RECONNECT_DELAY * (self.RECONNECT_BACKOFF_FACTOR ** (self.reconnect_attempts["account"] - 1))
                       self.logger.log_warning("account_reconnect", f"Account stream disconnected. Attempting reconnect {self.reconnect_attempts['account']}/{self.MAX_RECONNECT_ATTEMPTS} in {delay:.2f}s...")
                       time.sleep(delay)
                  else:
                       self.logger.log_error("account_reconnect_failed", "Account stream reconnect attempts exceeded.")
                       self.should_run.clear() # Stop trying if max attempts reached
                       break # Exit loop
             else:
                  break # Exit loop if should_run is cleared
        self.logger.log_info("account_thread_exit", "Account WebSocket thread finished.")

    def _run_market_data_connection(self):
        """Manages the market data WebSocket connection loop, including reconnection."""
        while self.should_run.is_set():
            self.logger.log_info("market_data_connect_attempt", f"Connecting to market data stream: {self.market_data_url}")
            self.market_data_ws = websocket.WebSocketApp(
                self.market_data_url,
                on_open=self._on_market_data_open,
                on_message=self._on_market_data_message,
                on_error=self._on_market_data_error,
                on_close=self._on_market_data_close
            )
            self.market_data_ws.run_forever(ping_interval=20, ping_timeout=10)

            if self.should_run.is_set():
                self.is_market_data_connected = False
                self.market_data_authenticated = False
                if self.connection_status_callback:
                    self.connection_status_callback("market_data", False)
                
                self.reconnect_attempts["market_data"] += 1
                if self.reconnect_attempts["market_data"] <= self.MAX_RECONNECT_ATTEMPTS:
                    delay = self.RECONNECT_DELAY * (self.RECONNECT_BACKOFF_FACTOR ** (self.reconnect_attempts["market_data"] - 1))
                    self.logger.log_warning("market_data_reconnect", f"Market data stream disconnected. Attempting reconnect {self.reconnect_attempts['market_data']}/{self.MAX_RECONNECT_ATTEMPTS} in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    self.logger.log_error("market_data_reconnect_failed", "Market data stream reconnect attempts exceeded.")
                    self.should_run.clear()
                    break
            else:
                 break
        self.logger.log_info("market_data_thread_exit", "Market data WebSocket thread finished.")

    def disconnect(self) -> None:
        """Close all WebSocket connections and stop threads."""
        self.logger.log_info("disconnect_start", "Attempting to disconnect from Alpaca WebSocket endpoints...")
        self.should_run.clear() # Signal threads to stop
        
        # Close WebSockets gracefully
        if self.account_ws:
            try:
                self.account_ws.close()
            except Exception as e:
                 self.logger.log_warning("ws_close_error", f"Error closing account WebSocket: {e}")
        
        if self.market_data_ws:
            try:
                self.market_data_ws.close()
            except Exception as e:
                 self.logger.log_warning("ws_close_error", f"Error closing market data WebSocket: {e}")

        # Wait for threads to finish
        if self.account_thread and self.account_thread.is_alive():
            self.logger.log_debug("disconnect_debug", "Waiting for account thread to join...")
            self.account_thread.join(timeout=2.0)
            if self.account_thread.is_alive():
                 self.logger.log_warning("disconnect_timeout", "Account thread did not exit cleanly.")
        
        if self.market_data_thread and self.market_data_thread.is_alive():
            self.logger.log_debug("disconnect_debug", "Waiting for market data thread to join...")
            self.market_data_thread.join(timeout=2.0)
            if self.market_data_thread.is_alive():
                 self.logger.log_warning("disconnect_timeout", "Market data thread did not exit cleanly.")

        # Reset state
        self.account_ws = None
        self.market_data_ws = None
        self.is_account_connected = False
        self.is_market_data_connected = False
        self.account_authenticated = False
        self.market_data_authenticated = False
        self.account_thread = None
        self.market_data_thread = None
        self.reconnect_attempts = {"account": 0, "market_data": 0} # Reset reconnect counts
        self.logger.log_info("disconnect_complete", "WebSocket connections closed and threads stopped.")
    
    # --- Authentication --- 
    def _authenticate_stream(self, ws, stream_name: str):
        """Sends authentication message to a WebSocket connection."""
        auth_msg = {
            "action": "auth",
            "key": self.api_key,
            "secret": self.api_secret
        }
        try:
            self.logger.log_info(f"auth_{stream_name}_start", f"Authenticating {stream_name} stream...")
            ws.send(json.dumps(auth_msg))
        except Exception as e:
            self.logger.log_error(f"auth_{stream_name}_error", f"Failed to send {stream_name} authentication message: {e}")
            # Trigger reconnection or error handling
            ws.close() 

    # --- Subscription Management ---    
    def _send_subscription(self, ws, stream_name: str, action: str, subscriptions: Dict[str, List[str]]) -> bool:
        """Sends a subscription message (listen/subscribe or unsubscribe) to a WebSocket."""
        if not ws or not self.should_run.is_set(): # Ensure ws exists and we should be running
            self.logger.log_warning(f"sub_{stream_name}_skip", f"Cannot {action}: {stream_name} WebSocket not active.")
            return False
            
        # Filter out empty subscription lists
        valid_subscriptions = {k: v for k, v in subscriptions.items() if v}
        if not valid_subscriptions:
            self.logger.log_warning(f"sub_{stream_name}_skip", f"No valid symbols provided for {action}.")
            return True # No action needed if no symbols

        # Alpaca v2 data stream uses "subscribe"/"unsubscribe" actions
        # Alpaca v2 account stream uses "listen" with a "streams" list
        if stream_name == "market_data":
             message = {
                  "action": action, # e.g., "subscribe"
                  **valid_subscriptions # e.g., {"trades": ["AAPL"], "quotes": ["MSFT"]}
             }
        elif stream_name == "account":
             # Account stream uses "listen" action and "streams" key
             # Note: Alpaca account stream doesn't typically unsubscribe specific streams, just disconnects.
             # This logic primarily handles initial "listen".
             if action == "subscribe" or action == "listen":
                  stream_list = list(self.account_subscriptions) # Send current intended state
                  if not stream_list:
                       return True # Nothing to listen to yet
                  message = {
                       "action": "listen",
                       "data": {"streams": stream_list}
                  }
             else:
                  self.logger.log_warning(f"sub_{stream_name}_unsupported", f"Unsubscribe action not directly supported for Alpaca account stream via message.")
                  return False # Or handle differently if needed
        else:
             self.logger.log_error(f"sub_{stream_name}_error", f"Unknown stream name for subscription: {stream_name}")
             return False

        try:
            ws.send(json.dumps(message))
            self.logger.log_info(f"sub_{stream_name}_sent", f"Sent {action} message for {stream_name}: {valid_subscriptions}")
            return True
        except Exception as e:
            self.logger.log_error(f"sub_{stream_name}_error", f"Failed to send {action} message for {stream_name}: {e}")
            return False

    def subscribe_account_updates(self) -> bool:
        """Subscribe to account and trade updates stream."""
        self.logger.log_info("subscribe_account", "Requesting account and trade updates subscription.")
        # Define the streams to listen to
        streams_to_listen = {"account_updates", "trade_updates"}
        self.account_subscriptions.update(streams_to_listen)
        
        # Send the listen message if connected and authenticated
        if self.is_account_connected and self.account_authenticated:
            return self._send_subscription(self.account_ws, "account", "listen", {})
        elif not self.is_account_connected:
            self.logger.log_warning("subscribe_account_warn", "Account stream not connected. Subscription will be attempted upon connection.")
            return True # Indicate intent is registered
        else: # Connected but not authenticated
            self.logger.log_warning("subscribe_account_warn", "Account stream not authenticated. Subscription will be attempted upon authentication.")
            return True # Indicate intent is registered

    def subscribe_trades(self, symbols: List[str]) -> bool:
        """Subscribe to trades for the given symbols."""
        self.logger.log_info("subscribe_trades", f"Requesting trade subscription for: {symbols}")
        new_symbols = set(symbols) - self.market_data_subscriptions["trades"]
        if not new_symbols:
             return True # Already subscribed

        # Update intended state first
        self.market_data_subscriptions["trades"].update(new_symbols)

        if self.is_market_data_connected and self.market_data_authenticated:
            return self._send_subscription(self.market_data_ws, "market_data", "subscribe", {"trades": list(new_symbols)})
        else:
             self.logger.log_warning("subscribe_trades_warn", "Market data stream not connected/authenticated. Subscription will be attempted later.")
             return True # Intent registered

    def subscribe_quotes(self, symbols: List[str]) -> bool:
        """Subscribe to quotes for the given symbols."""
        self.logger.log_info("subscribe_quotes", f"Requesting quote subscription for: {symbols}")
        new_symbols = set(symbols) - self.market_data_subscriptions["quotes"]
        if not new_symbols:
             return True

        self.market_data_subscriptions["quotes"].update(new_symbols)

        if self.is_market_data_connected and self.market_data_authenticated:
             return self._send_subscription(self.market_data_ws, "market_data", "subscribe", {"quotes": list(new_symbols)})
        else:
             self.logger.log_warning("subscribe_quotes_warn", "Market data stream not connected/authenticated. Subscription will be attempted later.")
             return True

    def subscribe_bars(self, symbols: List[str]) -> bool:
        """Subscribe to minute bars for the given symbols."""
        # Note: Alpaca v2 stream sends bars, not specific timeframes like "1Min"
        self.logger.log_info("subscribe_bars", f"Requesting bar subscription for: {symbols}")
        new_symbols = set(symbols) - self.market_data_subscriptions["bars"]
        if not new_symbols:
             return True

        self.market_data_subscriptions["bars"].update(new_symbols)

        if self.is_market_data_connected and self.market_data_authenticated:
            return self._send_subscription(self.market_data_ws, "market_data", "subscribe", {"bars": list(new_symbols)})
        else:
             self.logger.log_warning("subscribe_bars_warn", "Market data stream not connected/authenticated. Subscription will be attempted later.")
             return True
             
    # --- Unsubscribe --- 
    # Note: Alpaca v2 often requires unsubscribing from all of a type for a symbol
    def unsubscribe_trades(self, symbols: List[str]) -> bool:
         current_subs = self.market_data_subscriptions["trades"]
         symbols_to_remove = set(symbols) & current_subs
         if not symbols_to_remove:
              return True
         self.logger.log_info("unsubscribe_trades", f"Requesting trade unsubscription for: {symbols_to_remove}")
         self.market_data_subscriptions["trades"] -= symbols_to_remove
         if self.is_market_data_connected and self.market_data_authenticated:
              return self._send_subscription(self.market_data_ws, "market_data", "unsubscribe", {"trades": list(symbols_to_remove)})
         return True # Intent registered

    def unsubscribe_quotes(self, symbols: List[str]) -> bool:
         current_subs = self.market_data_subscriptions["quotes"]
         symbols_to_remove = set(symbols) & current_subs
         if not symbols_to_remove:
              return True
         self.logger.log_info("unsubscribe_quotes", f"Requesting quote unsubscription for: {symbols_to_remove}")
         self.market_data_subscriptions["quotes"] -= symbols_to_remove
         if self.is_market_data_connected and self.market_data_authenticated:
              return self._send_subscription(self.market_data_ws, "market_data", "unsubscribe", {"quotes": list(symbols_to_remove)})
         return True

    def unsubscribe_bars(self, symbols: List[str]) -> bool:
         current_subs = self.market_data_subscriptions["bars"]
         symbols_to_remove = set(symbols) & current_subs
         if not symbols_to_remove:
              return True
         self.logger.log_info("unsubscribe_bars", f"Requesting bar unsubscription for: {symbols_to_remove}")
         self.market_data_subscriptions["bars"] -= symbols_to_remove
         if self.is_market_data_connected and self.market_data_authenticated:
              return self._send_subscription(self.market_data_ws, "market_data", "unsubscribe", {"bars": list(symbols_to_remove)})
         return True

    # --- Callback Registration --- 
    def register_callback(self, topic: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Register a callback function for a specific topic.
        Topic examples: "account_updates", "trade_updates", "trades/AAPL", "quotes/TSLA", "bars/MSFT"
        """
        self.logger.log_info("register_callback", f"Registering callback for topic: {topic}")
        self.callbacks[topic] = callback

    def unregister_callback(self, topic: str):
         """Unregister a callback function for a topic."""
         if topic in self.callbacks:
              self.logger.log_info("unregister_callback", f"Unregistering callback for topic: {topic}")
              del self.callbacks[topic]
         else:
              self.logger.log_warning("unregister_callback_warn", f"No callback found for topic: {topic}")
              
    def register_connection_status_callback(self, callback: Callable[[str, bool], None]):
         """Register a callback for connection status changes (stream_name, is_connected)."""
         self.connection_status_callback = callback

    # --- WebSocket Event Handlers --- 
    def _on_account_open(self, ws):
        """Handler for when the account WebSocket connection is opened."""
        self.logger.log_info("ws_account_open", "Account WebSocket connection opened.")
        self.is_account_connected = True
        self.reconnect_attempts["account"] = 0 # Reset reconnect counter on successful open
        if self.connection_status_callback:
            self.connection_status_callback("account", True)
        self._authenticate_stream(ws, "account")

    def _on_account_message(self, ws, message):
        """Handler for messages received on the account WebSocket."""
        # self.logger.log_debug("ws_account_message", f"Raw message: {message}")
        try:
            data = json.loads(message)
            stream = data.get("stream")
            msg_data = data.get("data")

            if stream == "authorization":
                if msg_data.get("status") == "authorized":
                    self.account_authenticated = True
                    self.logger.log_info("ws_account_auth_success", "Account stream authenticated successfully.")
                    # Resubscribe on successful auth/reconnect
                    if self.account_subscriptions:
                         self._send_subscription(ws, "account", "listen", {})
                else:
                    self.account_authenticated = False
                    status = msg_data.get("status", "unknown")
                    self.logger.log_error("ws_account_auth_failed", f"Account stream authentication failed: {status}")
                    ws.close() # Close connection on auth failure
            
            elif stream == "listening":
                 # Confirmation of successful listen/subscription
                 listening_to = data.get("data", {}).get("streams", [])
                 self.logger.log_info("ws_account_listening", f"Successfully listening to account streams: {listening_to}")
                 # Update internal state if needed, though self.account_subscriptions should track intent

            elif stream == "account_updates" or stream == "trade_updates":
                 if stream in self.callbacks:
                      try:
                           self.callbacks[stream](msg_data)
                      except Exception as e:
                           self.logger.log_error("callback_error", f"Error in callback for {stream}: {e}")
                 # else: # Optional: Log if no callback registered
                 #     self.logger.log_debug("callback_missing", f"No callback registered for received stream: {stream}")
            
            else:
                 self.logger.log_warning("ws_account_unknown_stream", f"Received unknown stream type: {stream}", details=data)

        except json.JSONDecodeError:
            self.logger.log_error("ws_account_json_error", f"Failed to decode JSON message: {message}")
        except Exception as e:
            self.logger.log_error("ws_account_handler_error", f"Error processing account message: {e}")

    def _on_account_error(self, ws, error):
        """Handler for errors on the account WebSocket."""
        # Log specific websocket errors if available
        error_msg = str(error)
        if isinstance(error, websocket.WebSocketException):
             error_msg = f"WebSocketException: {error}"
        self.logger.log_error("ws_account_error", f"Account WebSocket error: {error_msg}")
        # Connection closure and reconnection is handled by on_close

    def _on_account_close(self, ws, close_status_code, close_msg):
        """Handler for when the account WebSocket connection is closed."""
        status_str = f"(Code: {close_status_code}, Msg: {close_msg})" if close_status_code else "(Unknown reason)"
        self.logger.log_warning("ws_account_close", f"Account WebSocket connection closed {status_str}")
        self.is_account_connected = False
        self.account_authenticated = False
        if self.connection_status_callback:
            self.connection_status_callback("account", False)
        # Reconnection logic is handled in the _run_account_connection loop

    # --- Market Data Handlers ---
    def _on_market_data_open(self, ws):
        """Handler for when the market data WebSocket connection is opened."""
        self.logger.log_info("ws_market_data_open", "Market Data WebSocket connection opened.")
        self.is_market_data_connected = True
        self.reconnect_attempts["market_data"] = 0
        if self.connection_status_callback:
            self.connection_status_callback("market_data", True)
        self._authenticate_stream(ws, "market_data")

    def _on_market_data_message(self, ws, message):
        """Handler for messages received on the market data WebSocket."""
        # self.logger.log_debug("ws_market_data_message", f"Raw message: {message}")
        try:
            data_list = json.loads(message)
            for item in data_list: # Market data messages often come in lists
                 msg_type = item.get("T") # Message Type (e.g., "success", "error", "subscription", "t", "q", "b")
                 
                 if msg_type == "success" and item.get("msg") == "authenticated":
                      self.market_data_authenticated = True
                      self.logger.log_info("ws_market_data_auth_success", "Market data stream authenticated successfully.")
                      # Resubscribe to intended state upon successful auth/reconnect
                      subs_to_resend = {}
                      if self.market_data_subscriptions["trades"]:
                           subs_to_resend["trades"] = list(self.market_data_subscriptions["trades"])
                      if self.market_data_subscriptions["quotes"]:
                           subs_to_resend["quotes"] = list(self.market_data_subscriptions["quotes"])
                      if self.market_data_subscriptions["bars"]:
        Subscribe to account updates (orders, positions, account details).
        
        Returns:
            bool: True if subscription was successful
        """
        if not self.is_account_connected:
            self.logger.log_error("websocket_error", "Cannot subscribe: account WebSocket not connected")
            return False
        
        subscription_msg = {
            "action": "listen",
            "data": {
                "streams": ["account_updates", "trade_updates"]
            }
        }
        
        try:
            self.account_ws.send(json.dumps(subscription_msg))
            self.account_subscriptions.update(["account_updates", "trade_updates"])
            self.logger.log_info("Subscribed to account updates")
            return True
        except Exception as e:
            self.logger.log_error("websocket_error", f"Failed to subscribe to account updates: {str(e)}")
            return False
    
    def subscribe_trades(self, symbols: List[str]) -> bool:
        """
        Subscribe to trade data for specified symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe to
            
        Returns:
            bool: True if subscription was successful
        """
        if not self.is_market_data_connected:
            self.logger.log_error("websocket_error", "Cannot subscribe: market data WebSocket not connected")
            return False
        
        subscription_msg = {
            "action": "subscribe",
            "trades": symbols
        }
        
        try:
            self.market_data_ws.send(json.dumps(subscription_msg))
            self.market_data_subscriptions.update([f"trades.{s}" for s in symbols])
            self.logger.log_info(f"Subscribed to trades for: {', '.join(symbols)}")
            return True
        except Exception as e:
            self.logger.log_error("websocket_error", f"Failed to subscribe to trades: {str(e)}")
            return False
    
    def subscribe_quotes(self, symbols: List[str]) -> bool:
        """
        Subscribe to quote data for specified symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe to
            
        Returns:
            bool: True if subscription was successful
        """
        if not self.is_market_data_connected:
            self.logger.log_error("websocket_error", "Cannot subscribe: market data WebSocket not connected")
            return False
        
        subscription_msg = {
            "action": "subscribe",
            "quotes": symbols
        }
        
        try:
            self.market_data_ws.send(json.dumps(subscription_msg))
            self.market_data_subscriptions.update([f"quotes.{s}" for s in symbols])
            self.logger.log_info(f"Subscribed to quotes for: {', '.join(symbols)}")
            return True
        except Exception as e:
            self.logger.log_error("websocket_error", f"Failed to subscribe to quotes: {str(e)}")
            return False
    
    def subscribe_bars(self, symbols: List[str], timeframe: str = "1Min") -> bool:
        """
        Subscribe to bar (OHLCV) data for specified symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe to
            timeframe: Bar timeframe (e.g., "1Min", "5Min", "1Hour", "1Day")
            
        Returns:
            bool: True if subscription was successful
        """
        if not self.is_market_data_connected:
            self.logger.log_error("websocket_error", "Cannot subscribe: market data WebSocket not connected")
            return False
        
        subscription_msg = {
            "action": "subscribe",
            "bars": symbols
        }
        
        try:
            self.market_data_ws.send(json.dumps(subscription_msg))
            self.market_data_subscriptions.update([f"bars.{timeframe}.{s}" for s in symbols])
            self.logger.log_info(f"Subscribed to {timeframe} bars for: {', '.join(symbols)}")
            return True
        except Exception as e:
            self.logger.log_error("websocket_error", f"Failed to subscribe to bars: {str(e)}")
            return False
    
    def register_order_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for order updates.
        
        Args:
            callback: Function to call when order updates are received
        """
        self.account_callbacks["order_updates"] = callback
    
    def register_trade_callback(self, symbol: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for trade data.
        
        Args:
            symbol: Ticker symbol to register callback for
            callback: Function to call when trade data is received
        """
        self.trade_callbacks[symbol] = callback
    
    def register_quote_callback(self, symbol: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for quote data.
        
        Args:
            symbol: Ticker symbol to register callback for
            callback: Function to call when quote data is received
        """
        self.quote_callbacks[symbol] = callback
    
    def register_bar_callback(self, symbol: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for bar data.
        
        Args:
            symbol: Ticker symbol to register callback for
            callback: Function to call when bar data is received
        """
        self.bar_callbacks[symbol] = callback
    
    def _connect_account_stream(self) -> bool:
        """
        Establish connection to account stream WebSocket.
        
        Returns:
            bool: True if connection was successful
        """
        try:
            # Setup WebSocket connection with callbacks
>>>>>>> develop
            self.account_ws = websocket.WebSocketApp(
                self.account_url,
                on_open=self._on_account_open,
                on_message=self._on_account_message,
                on_error=self._on_account_error,
                on_close=self._on_account_close,
<<<<<<< HEAD
                header=self._get_auth_headers()
            )
            
            # Setup market data WebSocket
            self.market_data_ws = websocket.WebSocketApp(
                self.market_data_url,
                on_open=self._on_market_open,
                on_message=self._on_market_message,
                on_error=self._on_market_error,
                on_close=self._on_market_close,
                header=self._get_auth_headers()
            )
            
            # Start WebSocket thread
            self.ws_thread = threading.Thread(target=self._run_websocket_connections)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait a bit for connections to establish
            time.sleep(2)
            
            return self.connected_account or self.connected_market
            
        except Exception as e:
            self.logger.log_error("stream_connect_error", f"Failed to connect to Alpaca WebSocket streams: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Alpaca WebSocket streams."""
        self.keep_running = False
        
        if self.account_ws:
            self.account_ws.close()
            
        if self.market_data_ws:
            self.market_data_ws.close()
            
        self.connected_account = False
        self.connected_market = False
        self.authenticated_account = False
        self.authenticated_market = False
    
    def subscribe_account_updates(self) -> bool:
        """
        Subscribe to account updates (trades, orders, positions).
        
        Returns:
            bool: True if subscription request was sent, False otherwise
        """
        if not self.connected_account or not self.authenticated_account:
            self.logger.log_warning("stream_subscribe", "Cannot subscribe: not connected to account stream")
            return False
        
        try:
            # Subscribe to account update channels
            message = {
                "action": "listen",
                "data": {
                    "streams": ["account_updates"]
                }
            }
            
            self.account_ws.send(json.dumps(message))
            self.subscribed_account_channels.add("account_updates")
            
            self.logger.log_info("stream_subscribe", "Subscribed to account updates")
            return True
            
        except Exception as e:
            self.logger.log_error("stream_subscribe_error", f"Failed to subscribe to account updates: {str(e)}")
            return False
    
    def subscribe_trades(self, symbols: List[str]) -> bool:
        """
        Subscribe to trade updates for the given symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe to
            
        Returns:
            bool: True if subscription request was sent, False otherwise
        """
        if not self.connected_market or not self.authenticated_market:
            self.logger.log_warning("stream_subscribe", "Cannot subscribe: not connected to market data stream")
            return False
        
        try:
            # Subscribe to trade feeds for the symbols
            message = {
                "action": "subscribe",
                "trades": symbols
            }
            
            self.market_data_ws.send(json.dumps(message))
            self.subscribed_symbols.update(symbols)
            self.subscribed_channels.add("trades")
            
            self.logger.log_info("stream_subscribe", f"Subscribed to trades for: {', '.join(symbols)}")
            return True
            
        except Exception as e:
            self.logger.log_error("stream_subscribe_error", f"Failed to subscribe to trades: {str(e)}")
            return False
    
    def subscribe_quotes(self, symbols: List[str]) -> bool:
        """
        Subscribe to quote updates for the given symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe to
            
        Returns:
            bool: True if subscription request was sent, False otherwise
        """
        if not self.connected_market or not self.authenticated_market:
            self.logger.log_warning("stream_subscribe", "Cannot subscribe: not connected to market data stream")
            return False
        
        try:
            # Subscribe to quote feeds for the symbols
            message = {
                "action": "subscribe",
                "quotes": symbols
            }
            
            self.market_data_ws.send(json.dumps(message))
            self.subscribed_symbols.update(symbols)
            self.subscribed_channels.add("quotes")
            
            self.logger.log_info("stream_subscribe", f"Subscribed to quotes for: {', '.join(symbols)}")
            return True
            
        except Exception as e:
            self.logger.log_error("stream_subscribe_error", f"Failed to subscribe to quotes: {str(e)}")
            return False
    
    def set_account_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback for account updates.
        
        Args:
            callback: Function to call with account update data
        """
        self.on_account_update = callback
    
    def set_trade_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback for trade updates.
        
        Args:
            callback: Function to call with trade data
        """
        self.on_trade = callback
    
    def set_quote_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback for quote updates.
        
        Args:
            callback: Function to call with quote data
        """
        self.on_quote = callback
    
    def set_connection_status_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        Set callback for connection status changes.
        
        Args:
            callback: Function to call with status updates (stream_type, is_connected)
        """
        self.on_connection_status = callback
    
    def _get_auth_headers(self) -> List[str]:
        """
        Create authentication headers for WebSocket connection.
        
        Returns:
            List of header strings
        """
        return [
            f"APCA-API-KEY-ID: {self.api_key}",
            f"APCA-API-SECRET-KEY: {self.api_secret}"
        ]
    
    def _run_websocket_connections(self) -> None:
        """Run WebSocket connections in a separate thread."""
        try:
            if self.account_ws:
                account_thread = threading.Thread(target=lambda: self.account_ws.run_forever(ping_interval=30, ping_timeout=10, sslopt={"cert_reqs": ssl.CERT_NONE}))
                account_thread.daemon = True
                account_thread.start()
            
            if self.market_data_ws:
                market_thread = threading.Thread(target=lambda: self.market_data_ws.run_forever(ping_interval=30, ping_timeout=10, sslopt={"cert_reqs": ssl.CERT_NONE}))
                market_thread.daemon = True
                market_thread.start()
                
            # Keep thread alive while running
            while self.keep_running:
                time.sleep(1)
                
        except Exception as e:
            self.logger.log_error("stream_thread_error", f"WebSocket thread error: {str(e)}")
    
    def _on_account_open(self, ws) -> None:
        """Callback when account WebSocket connection is opened."""
        self.connected_account = True
        self.authenticated_account = True  # Alpaca validates credentials during connection
        
        self.logger.log_info("stream_connected", "Connected to Alpaca account stream")
        
        if self.on_connection_status:
            self.on_connection_status("account", True)
    
    def _on_account_message(self, ws, message) -> None:
        """Callback when account WebSocket receives a message."""
        try:
            data = json.loads(message)
            
            # Process authentication confirmation if present
            if isinstance(data, dict) and data.get("stream") == "authorization" and data.get("data", {}).get("status") == "authorized":
                self.authenticated_account = True
                self.logger.log_info("stream_auth", "Authenticated with Alpaca account stream")
                return
            
            # Process account updates
            if self.on_account_update and isinstance(data, dict) and data.get("stream") == "account_updates":
                self.on_account_update(data.get("data", {}))
            
        except json.JSONDecodeError:
            self.logger.log_warning("stream_message_parse", f"Failed to parse account message: {message[:100]}...")
        except Exception as e:
            self.logger.log_error("stream_message_error", f"Error processing account message: {str(e)}")
    
    def _on_account_error(self, ws, error) -> None:
        """Callback when account WebSocket encounters an error."""
        self.logger.log_error("stream_error", f"Account stream error: {str(error)}")
    
    def _on_account_close(self, ws, close_status_code, close_msg) -> None:
        """Callback when account WebSocket connection is closed."""
        self.connected_account = False
        self.authenticated_account = False
        
        close_info = f" (Code: {close_status_code}, Msg: {close_msg})" if close_status_code or close_msg else ""
        self.logger.log_info("stream_disconnected", f"Disconnected from Alpaca account stream{close_info}")
        
        if self.on_connection_status:
            self.on_connection_status("account", False)
    
    def _on_market_open(self, ws) -> None:
        """Callback when market data WebSocket connection is opened."""
        self.connected_market = True
        self.authenticated_market = True  # Alpaca validates credentials during connection
        
        self.logger.log_info("stream_connected", "Connected to Alpaca market data stream")
        
        if self.on_connection_status:
            self.on_connection_status("market", True)
    
    def _on_market_message(self, ws, message) -> None:
        """Callback when market data WebSocket receives a message."""
        try:
            data = json.loads(message)
            
            # Process authentication confirmation if present
            if isinstance(data, dict) and data.get("T") == "success" and data.get("msg") == "authenticated":
                self.authenticated_market = True
                self.logger.log_info("stream_auth", "Authenticated with Alpaca market data stream")
                return
            
            # Process subscription confirmation
            if isinstance(data, dict) and data.get("T") == "subscription":
                self.logger.log_info("stream_subscription", f"Subscription confirmed: {json.dumps(data)}")
                return
            
            # Process trade updates
            if self.on_trade and isinstance(data, dict) and data.get("T") == "t":
                self.on_trade(data)
            
            # Process quote updates
            if self.on_quote and isinstance(data, dict) and data.get("T") == "q":
                self.on_quote(data)
            
        except json.JSONDecodeError:
            self.logger.log_warning("stream_message_parse", f"Failed to parse market message: {message[:100]}...")
        except Exception as e:
            self.logger.log_error("stream_message_error", f"Error processing market message: {str(e)}")
    
    def _on_market_error(self, ws, error) -> None:
        """Callback when market data WebSocket encounters an error."""
        self.logger.log_error("stream_error", f"Market data stream error: {str(error)}")
    
    def _on_market_close(self, ws, close_status_code, close_msg) -> None:
        """Callback when market data WebSocket connection is closed."""
        self.connected_market = False
        self.authenticated_market = False
        
        close_info = f" (Code: {close_status_code}, Msg: {close_msg})" if close_status_code or close_msg else ""
        self.logger.log_info("stream_disconnected", f"Disconnected from Alpaca market data stream{close_info}")
        
        if self.on_connection_status:
            self.on_connection_status("market", False) 
=======
                header={
                    "APCA-API-KEY-ID": self.api_key,
                    "APCA-API-SECRET-KEY": self.api_secret
                }
            )
            
            # Start WebSocket connection in a background thread
            account_thread = threading.Thread(target=self.account_ws.run_forever, daemon=True)
            account_thread.start()
            
            # Wait for connection to be established
            timeout = 5.0
            start_time = time.time()
            while not self.is_account_connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            return self.is_account_connected
            
        except Exception as e:
            self.logger.log_error("websocket_error", f"Failed to connect to account stream: {str(e)}")
            return False
    
    def _connect_market_data_stream(self) -> bool:
        """
        Establish connection to market data stream WebSocket.
        
        Returns:
            bool: True if connection was successful
        """
        try:
            # Setup WebSocket connection with callbacks
            self.market_data_ws = websocket.WebSocketApp(
                self.MARKET_DATA_URL,
                on_open=self._on_market_data_open,
                on_message=self._on_market_data_message,
                on_error=self._on_market_data_error,
                on_close=self._on_market_data_close
            )
            
            # Start WebSocket connection in a background thread
            market_data_thread = threading.Thread(target=self.market_data_ws.run_forever, daemon=True)
            market_data_thread.start()
            
            # Wait for connection to be established
            timeout = 5.0
            start_time = time.time()
            while not self.is_market_data_connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            # Authenticate if connected
            if self.is_market_data_connected:
                auth_msg = {
                    "action": "auth",
                    "key": self.api_key,
                    "secret": self.api_secret
                }
                self.market_data_ws.send(json.dumps(auth_msg))
            
            return self.is_market_data_connected
            
        except Exception as e:
            self.logger.log_error("websocket_error", f"Failed to connect to market data stream: {str(e)}")
            return False
    
    def _heartbeat_monitor(self) -> None:
        """
        Monitor WebSocket connections and handle reconnections.
        
        This runs in a separate thread to ensure connections stay alive.
        """
        while self.should_run:
            current_time = time.time()
            
            # Check account stream
            if self.is_account_connected:
                if current_time - self.last_account_heartbeat > self.HEARTBEAT_INTERVAL:
                    self.missed_account_heartbeats += 1
                    if self.missed_account_heartbeats >= self.MISSED_HEARTBEATS_THRESHOLD:
                        self.logger.log_error("websocket_error", "Account stream connection lost, reconnecting...")
                        self._reconnect_account_stream()
            
            # Check market data stream
            if self.is_market_data_connected:
                if current_time - self.last_market_data_heartbeat > self.HEARTBEAT_INTERVAL:
                    self.missed_market_data_heartbeats += 1
                    if self.missed_market_data_heartbeats >= self.MISSED_HEARTBEATS_THRESHOLD:
                        self.logger.log_error("websocket_error", "Market data stream connection lost, reconnecting...")
                        self._reconnect_market_data_stream()
            
            time.sleep(1)
    
    def _reconnect_account_stream(self) -> None:
        """Reconnect to the account WebSocket stream with backoff."""
        self.is_account_connected = False
        if self.account_ws:
            try:
                self.account_ws.close()
            except:
                pass
        
        attempt = 0
        while attempt < self.MAX_RECONNECT_ATTEMPTS and not self.is_account_connected:
            attempt += 1
            delay = self.RECONNECT_DELAY * (self.RECONNECT_BACKOFF_FACTOR ** (attempt - 1))
            
            self.logger.log_info(f"Reconnecting to account stream (attempt {attempt}/{self.MAX_RECONNECT_ATTEMPTS})")
            time.sleep(delay)
            
            if self._connect_account_stream():
                # Resubscribe to previous subscriptions
                if "account_updates" in self.account_subscriptions:
                    self.subscribe_account_updates()
                break
        
        if not self.is_account_connected:
            self.logger.log_error("websocket_error", "Failed to reconnect to account stream after multiple attempts")
    
    def _reconnect_market_data_stream(self) -> None:
        """Reconnect to the market data WebSocket stream with backoff."""
        self.is_market_data_connected = False
        if self.market_data_ws:
            try:
                self.market_data_ws.close()
            except:
                pass
        
        attempt = 0
        while attempt < self.MAX_RECONNECT_ATTEMPTS and not self.is_market_data_connected:
            attempt += 1
            delay = self.RECONNECT_DELAY * (self.RECONNECT_BACKOFF_FACTOR ** (attempt - 1))
            
            self.logger.log_info(f"Reconnecting to market data stream (attempt {attempt}/{self.MAX_RECONNECT_ATTEMPTS})")
            time.sleep(delay)
            
            if self._connect_market_data_stream():
                # Resubscribe to previous subscriptions
                trades = [s.split('.')[1] for s in self.market_data_subscriptions if s.startswith("trades.")]
                quotes = [s.split('.')[1] for s in self.market_data_subscriptions if s.startswith("quotes.")]
                bars = [s.split('.')[2] for s in self.market_data_subscriptions if s.startswith("bars.")]
                
                if trades:
                    self.subscribe_trades(trades)
                if quotes:
                    self.subscribe_quotes(quotes)
                if bars:
                    # For simplicity, use default timeframe for reconnection
                    self.subscribe_bars(bars)
                break
        
        if not self.is_market_data_connected:
            self.logger.log_error("websocket_error", "Failed to reconnect to market data stream after multiple attempts")
    
    # WebSocket event handlers
    def _on_account_open(self, ws) -> None:
        """Handle account WebSocket connection open event."""
        self.is_account_connected = True
        self.missed_account_heartbeats = 0
        self.last_account_heartbeat = time.time()
        self.logger.log_info("Connected to Alpaca account stream")
    
    def _on_account_message(self, ws, message) -> None:
        """Handle messages from account WebSocket."""
        self.last_account_heartbeat = time.time()
        self.missed_account_heartbeats = 0
        
        try:
            data = json.loads(message)
            msg_type = data.get("stream")
            
            if msg_type == "authorization":
                if data.get("data", {}).get("status") == "authorized":
                    self.logger.log_info("Successfully authenticated with account stream")
                else:
                    self.logger.log_error("auth_error", "Failed to authenticate with account stream")
            
            elif msg_type == "listening":
                self.logger.log_info(f"Listening to streams: {data.get('data', {}).get('streams', [])}")
            
            elif msg_type == "trade_updates":
                # Process trade/order update
                order_data = data.get("data", {})
                self.logger.log_info(f"Received trade update: {order_data.get('order', {}).get('id')}")
                
                # Dispatch to callback if registered
                if "order_updates" in self.account_callbacks:
                    self.account_callbacks["order_updates"](order_data)
            
            elif msg_type == "account_updates":
                # Process account update
                account_data = data.get("data", {})
                self.logger.log_info(f"Received account update: {account_data.get('id')}")
                
                # Dispatch to callback if registered
                if "account_updates" in self.account_callbacks:
                    self.account_callbacks["account_updates"](account_data)
            
        except Exception as e:
            self.logger.log_error("websocket_error", f"Error processing account message: {str(e)}")
    
    def _on_account_error(self, ws, error) -> None:
        """Handle account WebSocket error event."""
        self.logger.log_error("websocket_error", f"Account stream error: {str(error)}")
    
    def _on_account_close(self, ws, close_status_code, close_msg) -> None:
        """Handle account WebSocket close event."""
        self.is_account_connected = False
        self.logger.log_info(f"Account stream closed: {close_status_code} - {close_msg}")
    
    def _on_market_data_open(self, ws) -> None:
        """Handle market data WebSocket connection open event."""
        self.is_market_data_connected = True
        self.missed_market_data_heartbeats = 0
        self.last_market_data_heartbeat = time.time()
        self.logger.log_info("Connected to Alpaca market data stream")
    
    def _on_market_data_message(self, ws, message) -> None:
        """Handle messages from market data WebSocket."""
        self.last_market_data_heartbeat = time.time()
        self.missed_market_data_heartbeats = 0
        
        try:
            data = json.loads(message)
            
            if data.get("T") == "success" and data.get("msg") == "authenticated":
                self.logger.log_info("Successfully authenticated with market data stream")
                return
                
            # Process different types of market data
            msg_type = data.get("T")
            
            if msg_type == "t":  # Trade
                symbol = data.get("S")
                if symbol in self.trade_callbacks:
                    self.trade_callbacks[symbol](data)
            
            elif msg_type == "q":  # Quote
                symbol = data.get("S")
                if symbol in self.quote_callbacks:
                    self.quote_callbacks[symbol](data)
            
            elif msg_type == "b":  # Bar
                symbol = data.get("S")
                if symbol in self.bar_callbacks:
                    self.bar_callbacks[symbol](data)
            
            elif msg_type == "subscription":
                self.logger.log_info(f"Subscription update: {data}")
            
            elif msg_type == "error":
                self.logger.log_error("websocket_error", f"Market data stream error: {data.get('msg')}")
            
        except Exception as e:
            self.logger.log_error("websocket_error", f"Error processing market data message: {str(e)}")
    
    def _on_market_data_error(self, ws, error) -> None:
        """Handle market data WebSocket error event."""
        self.logger.log_error("websocket_error", f"Market data stream error: {str(error)}")
    
    def _on_market_data_close(self, ws, close_status_code, close_msg) -> None:
        """Handle market data WebSocket close event."""
        self.is_market_data_connected = False
        self.logger.log_info(f"Market data stream closed: {close_status_code} - {close_msg}") 
>>>>>>> develop
