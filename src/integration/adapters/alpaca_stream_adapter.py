import json
import threading
import websocket
import logging
import time
from typing import Dict, Any, List, Optional, Callable
import ssl

from src.integration.utils.logger import IntegrationLogger
from src.integration.adapters.config import get_alpaca_config

class AlpacaStreamAdapter:
    """
    Adapter for connecting to Alpaca's WebSocket streams.
    Supports:
    - Account updates (trades, orders, positions)
    - Market data (trades, quotes, bars)
    """
    
    def __init__(self, use_paper: bool = True, logger: Optional[IntegrationLogger] = None):
        """
        Initialize the AlpacaStreamAdapter.
        
        Args:
            use_paper: Whether to use paper trading environment
            logger: Optional integration logger for recording events
        """
        self.logger = logger or IntegrationLogger()
        self.alpaca_config = get_alpaca_config()
        self.use_paper = use_paper
        
        # Determine endpoints based on paper/live
        if use_paper:
            self.base_url = self.alpaca_config.get("paper_api_base_url", "").replace("https://", "wss://")
            self.api_key = self.alpaca_config.get("paper_api_key", "")
            self.api_secret = self.alpaca_config.get("paper_api_secret", "")
        else:
            self.base_url = self.alpaca_config.get("live_api_base_url", "").replace("https://", "wss://")
            self.api_key = self.alpaca_config.get("live_api_key", "")
            self.api_secret = self.alpaca_config.get("live_api_secret", "")
        
        # Format WebSocket URLs
        self.account_url = f"{self.base_url}/stream"
        self.market_data_url = f"{self.base_url}/stream/market_data"
        
        # Initialize WebSocket connections
        self.account_ws = None
        self.market_data_ws = None
        
        # Status tracking
        self.connected_account = False
        self.connected_market = False
        self.authenticated_account = False
        self.authenticated_market = False
        
        # Callbacks
        self.on_account_update = None
        self.on_trade = None
        self.on_quote = None
        self.on_bar = None
        self.on_connection_status = None
        
        # Subscriptions
        self.subscribed_account_channels = set()
        self.subscribed_symbols = set()
        self.subscribed_channels = set()
        
        # Message handling thread
        self.keep_running = True
        self.ws_thread = None
    
    def connect(self) -> bool:
        """
        Connect to Alpaca WebSocket streams.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Setup account updates WebSocket
            self.account_ws = websocket.WebSocketApp(
                self.account_url,
                on_open=self._on_account_open,
                on_message=self._on_account_message,
                on_error=self._on_account_error,
                on_close=self._on_account_close,
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