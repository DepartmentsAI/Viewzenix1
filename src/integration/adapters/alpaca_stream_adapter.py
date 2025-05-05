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
    MARKET_DATA_URL = "wss://stream.data.alpaca.markets/v2"
    
    # Reconnection parameters
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 3
    RECONNECT_BACKOFF_FACTOR = 1.5
    
    # Heartbeat parameters 
    HEARTBEAT_INTERVAL = 30  # seconds
    MISSED_HEARTBEATS_THRESHOLD = 3
    
    def __init__(self, use_paper: bool = True, logger: Optional[IntegrationLogger] = None):
        """
        Initialize the Alpaca WebSocket adapter.
        
        Args:
            use_paper: Whether to use paper trading API (True) or live trading API (False)
            logger: Optional integration logger instance
        """
        self.use_paper = use_paper
        self.logger = logger or IntegrationLogger()
        
        # Get broker configuration
        alpaca_config = get_broker_config('alpaca')
        
        # Get appropriate API keys
        if self.use_paper:
            self.api_key = alpaca_config.get('paper_api_key')
            self.api_secret = alpaca_config.get('paper_api_secret')
            self.account_url = self.PAPER_ACCOUNT_URL
        else:
            self.api_key = alpaca_config.get('live_api_key')
            self.api_secret = alpaca_config.get('live_api_secret')
            self.account_url = self.LIVE_ACCOUNT_URL
        
        # WebSocket connections
        self.account_ws = None
        self.market_data_ws = None
        
        # Connection and subscription state
        self.is_account_connected = False
        self.is_market_data_connected = False
        self.account_subscriptions = set()
        self.market_data_subscriptions = set()
        
        # Heartbeat tracking
        self.last_account_heartbeat = 0
        self.last_market_data_heartbeat = 0
        self.missed_account_heartbeats = 0
        self.missed_market_data_heartbeats = 0
        
        # Callback registries
        self.account_callbacks = {}
        self.trade_callbacks = {}
        self.quote_callbacks = {}
        self.bar_callbacks = {}
        
        # Threading 
        self.heartbeat_thread = None
        self.should_run = False
    
    def connect(self) -> bool:
        """
        Establish connections to Alpaca WebSocket endpoints.
        
        Returns:
            bool: True if connections were established successfully
        """
        self.logger.log_info("Connecting to Alpaca WebSocket endpoints")
        
        # Setup heartbeat thread
        self.should_run = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
        self.heartbeat_thread.start()
        
        # Connect to account stream
        account_connected = self._connect_account_stream()
        
        # Connect to market data stream
        market_data_connected = self._connect_market_data_stream()
        
        return account_connected and market_data_connected
    
    def disconnect(self) -> None:
        """Close all WebSocket connections."""
        self.logger.log_info("Disconnecting from Alpaca WebSocket endpoints")
        
        self.should_run = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1.0)
        
        if self.account_ws:
            self.account_ws.close()
            self.account_ws = None
        
        if self.market_data_ws:
            self.market_data_ws.close()
            self.market_data_ws = None
        
        self.is_account_connected = False
        self.is_market_data_connected = False
    
    def subscribe_account_updates(self) -> bool:
        """
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
            self.account_ws = websocket.WebSocketApp(
                self.account_url,
                on_open=self._on_account_open,
                on_message=self._on_account_message,
                on_error=self._on_account_error,
                on_close=self._on_account_close,
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