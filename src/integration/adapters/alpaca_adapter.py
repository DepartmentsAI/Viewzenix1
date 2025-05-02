import requests
import time
from typing import Dict, Any, Optional, List, Tuple
import uuid
import json

from src.integration.adapters.broker_adapter import BrokerAdapter
from src.integration.utils.api_key_manager import ApiKeyManager
from src.integration.utils.logger import IntegrationLogger
from src.integration.utils.env_config import get_broker_config, get_config_value

class AlpacaAdapter(BrokerAdapter):
    """Adapter for Alpaca Markets API.
    
    Implementation of BrokerAdapter interface for Alpaca Markets.
    Handles order execution, position management, and account information.
    """
    
    # Alpaca API URLs
    PAPER_BASE_URL = "https://paper-api.alpaca.markets"
    LIVE_BASE_URL = "https://api.alpaca.markets"
    API_VERSION = "v2"
    
    # API Endpoints
    ACCOUNT_ENDPOINT = "/account"
    ORDERS_ENDPOINT = "/orders"
    POSITIONS_ENDPOINT = "/positions"
    
    # Maximum retry attempts for API calls
    MAX_RETRIES = 3
    # Delay between retries (seconds)
    RETRY_DELAY = 2
    
    def __init__(self, use_paper: bool = True, logger: Optional[IntegrationLogger] = None):
        """Initialize the Alpaca adapter.
        
        Args:
            use_paper: Whether to use paper trading API (True) or live trading API (False)
            logger: Optional integration logger instance
        """
        self.use_paper = use_paper
        self.base_url = self.PAPER_BASE_URL if use_paper else self.LIVE_BASE_URL
        self.api_key = None
        self.api_secret = None
        self.authenticated = False
        
        # Initialize logger
        self.logger = logger or IntegrationLogger()
        
        # Authenticate upon initialization
        self.authenticate()
    
    def authenticate(self) -> bool:
        """Authenticate with Alpaca API using environment variables.
        
        Loads API key and secret from environment variables and verifies them by making
        a test request to the account endpoint.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        # Get broker configuration from our new config utility
        alpaca_config = get_broker_config('alpaca')
        
        if not alpaca_config:
            self.logger.log_error(
                "auth_error", 
                "Failed to load Alpaca API configuration from any source"
            )
            return False
        
        # Use the appropriate keys based on paper/live mode
        if self.use_paper:
            api_key = alpaca_config.get('paper_api_key')
            api_secret = alpaca_config.get('paper_api_secret')
            config_source = alpaca_config.get('source', 'unknown')
        else:
            api_key = alpaca_config.get('live_api_key')
            api_secret = alpaca_config.get('live_api_secret')
            config_source = alpaca_config.get('source', 'unknown')
        
        # Check if we have valid keys
        if not api_key or not api_secret or api_key.startswith('DEFAULT_PLACEHOLDER'):
            self.logger.log_error(
                "auth_error", 
                f"Invalid Alpaca API keys from source: {config_source}"
            )
            return False
        
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Test authentication by getting account info
        try:
            response = self._make_request("GET", self.ACCOUNT_ENDPOINT, {})
            if response and "account_number" in response:
                self.authenticated = True
                self.logger.log_info(
                    "auth_success", 
                    f"Authenticated with Alpaca API using credentials from {config_source}"
                )
                return True
            else:
                self.logger.log_error("auth_error", "Failed to authenticate with Alpaca API")
                return False
        except Exception as e:
            self.logger.log_error("auth_error", f"Exception during Alpaca authentication: {str(e)}")
            return False
    
    def place_market_order(self, symbol: str, qty: float, side: str, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a market order.
        
        Args:
            symbol: The trading symbol (e.g., 'AAPL', 'BTC/USD')
            qty: Quantity to trade
            side: 'buy' or 'sell'
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and broker response
        """
        # Format the symbol for Alpaca (handle crypto format if needed)
        formatted_symbol = self._format_symbol(symbol)
        
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
        
        # Prepare order parameters
        params = {
            "symbol": formatted_symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": "market",
            "time_in_force": "gtc",
            "client_order_id": client_order_id
        }
        
        # Make the API request
        return self._place_order(params, client_order_id)
    
    def place_limit_order(self, symbol: str, qty: float, side: str, limit_price: float, 
                         client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a limit order.
        
        Args:
            symbol: The trading symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            limit_price: Price at which to execute the limit order
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and broker response
        """
        # Format the symbol for Alpaca
        formatted_symbol = self._format_symbol(symbol)
        
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
        
        # Prepare order parameters
        params = {
            "symbol": formatted_symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": "limit",
            "time_in_force": "gtc",
            "limit_price": str(limit_price),
            "client_order_id": client_order_id
        }
        
        # Make the API request
        return self._place_order(params, client_order_id)
    
    def place_stop_order(self, symbol: str, qty: float, side: str, stop_price: float,
                        client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a stop order.
        
        Args:
            symbol: The trading symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            stop_price: Price at which to trigger the stop order
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and broker response
        """
        # Format the symbol for Alpaca
        formatted_symbol = self._format_symbol(symbol)
        
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
        
        # Prepare order parameters
        params = {
            "symbol": formatted_symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": "stop",
            "time_in_force": "gtc",
            "stop_price": str(stop_price),
            "client_order_id": client_order_id
        }
        
        # Make the API request
        return self._place_order(params, client_order_id)
    
    def place_bracket_order(self, symbol: str, qty: float, side: str, 
                           entry_price: Optional[float] = None,
                           take_profit_price: Optional[float] = None, 
                           stop_loss_price: Optional[float] = None,
                           client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a bracket order with entry, take-profit, and stop-loss.
        
        Args:
            symbol: The trading symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            entry_price: Optional price for entry (None for market entry)
            take_profit_price: Price for take-profit order
            stop_loss_price: Price for stop-loss order
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and broker response
        """
        # Format the symbol for Alpaca
        formatted_symbol = self._format_symbol(symbol)
        
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
        
        # Prepare order parameters
        params = {
            "symbol": formatted_symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": "market" if entry_price is None else "limit",
            "time_in_force": "gtc",
            "client_order_id": client_order_id,
            "order_class": "bracket"
        }
        
        # Add limit price if provided
        if entry_price is not None:
            params["limit_price"] = str(entry_price)
        
        # Add take profit and stop loss
        if take_profit_price is not None:
            params["take_profit"] = {"limit_price": str(take_profit_price)}
        
        if stop_loss_price is not None:
            params["stop_loss"] = {"stop_price": str(stop_loss_price)}
        
        # Make the API request
        return self._place_order(params, client_order_id)
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order.
        
        Args:
            order_id: The ID of the order to cancel
            
        Returns:
            Dict containing the cancellation result
        """
        endpoint = f"{self.ORDERS_ENDPOINT}/{order_id}"
        
        try:
            return self._make_request("DELETE", endpoint, {}, order_id=order_id)
        except Exception as e:
            error_msg = f"Failed to cancel order {order_id}: {str(e)}"
            self.logger.log_error("cancel_order_error", error_msg)
            return {"success": False, "error": error_msg}
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the status of an existing order.
        
        Args:
            order_id: The ID of the order to check
            
        Returns:
            Dict containing the order status
        """
        endpoint = f"{self.ORDERS_ENDPOINT}/{order_id}"
        
        try:
            return self._make_request("GET", endpoint, {}, order_id=order_id)
        except Exception as e:
            error_msg = f"Failed to get order status for {order_id}: {str(e)}"
            self.logger.log_error("order_status_error", error_msg)
            return {"success": False, "error": error_msg}
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for a symbol.
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Dict containing position information or None if no position exists
        """
        formatted_symbol = self._format_symbol(symbol)
        endpoint = f"{self.POSITIONS_ENDPOINT}/{formatted_symbol}"
        
        try:
            return self._make_request("GET", endpoint, {})
        except requests.exceptions.HTTPError as e:
            # 404 means no position exists
            if e.response.status_code == 404:
                return None
            # Other errors
            error_msg = f"Failed to get position for {symbol}: {str(e)}"
            self.logger.log_error("position_error", error_msg)
            return None
        except Exception as e:
            error_msg = f"Failed to get position for {symbol}: {str(e)}"
            self.logger.log_error("position_error", error_msg)
            return None
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all current positions.
        
        Returns:
            List of dictionaries containing position information
        """
        try:
            positions = self._make_request("GET", self.POSITIONS_ENDPOINT, {})
            return positions if isinstance(positions, list) else []
        except Exception as e:
            error_msg = f"Failed to get all positions: {str(e)}"
            self.logger.log_error("positions_error", error_msg)
            return []
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position for a specific symbol.
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Dict containing the result of the position closure
        """
        formatted_symbol = self._format_symbol(symbol)
        endpoint = f"{self.POSITIONS_ENDPOINT}/{formatted_symbol}"
        
        try:
            return self._make_request("DELETE", endpoint, {})
        except Exception as e:
            error_msg = f"Failed to close position for {symbol}: {str(e)}"
            self.logger.log_error("close_position_error", error_msg)
            return {"success": False, "error": error_msg}
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information including equity, buying power, etc.
        
        Returns:
            Dict containing account information
        """
        try:
            return self._make_request("GET", self.ACCOUNT_ENDPOINT, {})
        except Exception as e:
            error_msg = f"Failed to get account info: {str(e)}"
            self.logger.log_error("account_info_error", error_msg)
            return {"success": False, "error": error_msg}
    
    def _place_order(self, params: Dict[str, Any], client_order_id: str) -> Dict[str, Any]:
        """Internal method to place orders with common error handling.
        
        Args:
            params: Order parameters for Alpaca API
            client_order_id: Client-defined order ID for tracking
            
        Returns:
            Dict containing the order result
        """
        try:
            response = self._make_request("POST", self.ORDERS_ENDPOINT, params, order_id=client_order_id)
            return {
                "success": True,
                "order_id": response.get("id"),
                "client_order_id": response.get("client_order_id"),
                "status": response.get("status"),
                "order_type": response.get("type"),
                "side": response.get("side"),
                "symbol": response.get("symbol"),
                "qty": response.get("qty"),
                "filled_qty": response.get("filled_qty"),
                "response": response
            }
        except Exception as e:
            error_msg = f"Failed to place order: {str(e)}"
            self.logger.log_error("order_placement_error", error_msg, details={"params": params})
            return {"success": False, "error": error_msg, "params": params}
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any], order_id: Optional[str] = None) -> Any:
        """Make an HTTP request to the Alpaca API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            order_id: Optional order ID for logging
            
        Returns:
            API response as dictionary or list
            
        Raises:
            requests.exceptions.HTTPError: If API returns an error status
            Exception: For other errors
        """
        if not self.api_key or not self.api_secret:
            raise Exception("API keys not set. Call authenticate() first.")
        
        # Prepare headers
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json"
        }
        
        # Full URL
        url = f"{self.base_url}/{self.API_VERSION}{endpoint}"
        
        # Log the request
        sanitized_params = params.copy()
        if "client_order_id" in sanitized_params:
            sanitized_params["client_order_id"] = sanitized_params["client_order_id"]
        
        self.logger.log_broker_request(
            broker="alpaca",
            endpoint=endpoint,
            method=method,
            params=sanitized_params,
            order_id=order_id
        )
        
        # Implement retry logic
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                elif method == "POST":
                    response = requests.post(url, headers=headers, data=json.dumps(params), timeout=10)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Raise an exception for bad status codes
                response.raise_for_status()
                
                # Parse the response
                response_data = response.json() if response.text else {}
                
                # Log the response
                self.logger.log_broker_response(
                    broker="alpaca",
                    endpoint=endpoint,
                    status_code=response.status_code,
                    response_data=response_data,
                    order_id=order_id
                )
                
                return response_data
                
            except requests.exceptions.HTTPError as e:
                # Log the error response
                error_response = {}
                try:
                    error_response = e.response.json()
                except:
                    error_response = {"text": e.response.text}
                
                self.logger.log_broker_response(
                    broker="alpaca",
                    endpoint=endpoint,
                    status_code=e.response.status_code,
                    response_data=error_response,
                    order_id=order_id
                )
                
                # Don't retry client errors except for rate limits (429)
                if e.response.status_code != 429 and e.response.status_code < 500:
                    raise
                
                retries += 1
                if retries >= self.MAX_RETRIES:
                    raise
                
                # Wait before retrying (with backoff)
                time.sleep(self.RETRY_DELAY * retries)
                
            except Exception as e:
                # Log the exception
                self.logger.log_error(
                    "request_error",
                    f"Error making request to Alpaca API: {str(e)}",
                    {"method": method, "endpoint": endpoint, "retries": retries}
                )
                
                retries += 1
                if retries >= self.MAX_RETRIES:
                    raise
                
                # Wait before retrying (with backoff)
                time.sleep(self.RETRY_DELAY * retries)
    
    def _generate_client_order_id(self) -> str:
        """Generate a unique client order ID.
        
        Returns:
            A string in the format required by the spec: {bot_id}-{timestamp}-{uuid}
        """
        bot_id = "alpaca"
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"{bot_id}-{timestamp}-{unique_id}"
    
    def _format_symbol(self, symbol: str) -> str:
        """Format a symbol for Alpaca API.
        
        Handles various formats like 'BTC/USD' -> 'BTCUSD'.
        
        Args:
            symbol: The symbol in any format
            
        Returns:
            Symbol formatted for Alpaca API
        """
        # Remove common delimiters for crypto
        if '/' in symbol:
            symbol = symbol.replace('/', '')
        
        # Remove other common delimiters
        symbol = symbol.replace('-', '')
        symbol = symbol.replace('.', '')
        
        return symbol 