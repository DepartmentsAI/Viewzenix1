import requests
import time
from typing import Dict, Any, Optional, List, Tuple
import uuid
import json

from src.integration.adapters.broker_adapter import BrokerAdapter
from src.integration.utils.logger import IntegrationLogger
from src.integration.utils.env_config import get_broker_config

class AlpacaAdapter(BrokerAdapter):
    """Adapter for Alpaca Markets API.
    
    Implementation of BrokerAdapter interface for Alpaca Markets.
    Handles order execution, position management, and account information.
    """
    
    # Alpaca API URLs are now handled by env_config utility
    API_VERSION = "v2"
    
    # API Endpoints
    ACCOUNT_ENDPOINT = "/account"
    ORDERS_ENDPOINT = "/orders"
    POSITIONS_ENDPOINT = "/positions"
    
    # Maximum retry attempts for API calls
    MAX_RETRIES = 3
    # Delay between retries (seconds)
    RETRY_DELAY = 2
    
    def __init__(self, use_paper: bool = True, 
                 logger: Optional[IntegrationLogger] = None):
        """Initialize AlpacaAdapter.
        
        Args:
            use_paper: Whether to use paper trading (default: True)
            logger: Optional logger instance
        """
        self.logger = logger or IntegrationLogger()
        self.use_paper = use_paper
        self.authenticated = False
        self.account_id = None
        self.api_key = None # Will be set during authentication
        self.api_secret = None # Will be set during authentication
        self.base_url = None # Will be set during authentication

        # Log initialization status
        self.logger.log_info("alpaca_init", 
                       f"AlpacaAdapter initialized: paper={self.use_paper}")

    def authenticate(self) -> bool:
        """Authenticate with Alpaca API using credentials from config.
        
        Returns:
            bool: True if authentication succeeded, False otherwise
        """
        # Get broker configuration from the utility
        alpaca_config = get_broker_config('alpaca', use_paper=self.use_paper)
        
        if not alpaca_config or not alpaca_config.get('api_key') or not alpaca_config.get('api_secret'):
            self.logger.log_error(
                "auth_error", 
                f"Failed to load valid Alpaca API configuration for {'paper' if self.use_paper else 'live'} mode."
            )
            return False

        self.api_key = alpaca_config.get('api_key')
        self.api_secret = alpaca_config.get('api_secret')
        self.base_url = alpaca_config.get('base_url')
        config_source = alpaca_config.get('source', 'unknown')

        # Check if we have valid keys
        if not self.api_key or not self.api_secret or self.api_key.startswith('DEFAULT_PLACEHOLDER'):
            self.logger.log_error(
                "auth_error", 
                f"Invalid Alpaca API keys found in configuration source: {config_source}"
            )
            return False

        # Test authentication by getting account info
        try:
            response = self._make_request("GET", self.ACCOUNT_ENDPOINT)
            if response and "account_number" in response:
                self.authenticated = True
                self.account_id = response.get("id") # Store account ID
                self.logger.log_info(
                    "auth_success", 
                    f"Authenticated with Alpaca API (Account: {response.get('account_number', 'N/A')}) using credentials from {config_source}"
                )
                return True
            else:
                error_detail = response.get('message', 'No response or account number') if isinstance(response, dict) else 'Invalid response'
                self.logger.log_error("auth_error", f"Failed to authenticate with Alpaca API: {error_detail}")
                return False
        except Exception as e:
            self.authenticated = False
            self.logger.log_error("alpaca_auth_failed", f"Authentication failed during API request: {str(e)}")
            return False

    def place_market_order(self, symbol: str, qty: float, side: str, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a market order."""
        if not self.authenticated:
            self.logger.log_error("order_error", "Cannot place order: Not authenticated.")
            return {"success": False, "error": "Not authenticated"}
            
        formatted_symbol = self._format_symbol(symbol)
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
        
        params = {
            "symbol": formatted_symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": "market",
            "time_in_force": "gtc",
            "client_order_id": client_order_id
        }
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
        """Cancel a specific order by its ID."""
        if not self.authenticated:
            self.logger.log_error("cancel_order_error", "Cannot cancel order: Not authenticated.")
            return {"success": False, "error": "Not authenticated"}

        endpoint = f"{self.ORDERS_ENDPOINT}/{order_id}"
        try:
            response = self._make_request("DELETE", endpoint)
            # Successful cancel often returns 204 No Content
            if response.get('status_code') == 204:
                 self.logger.log_info("cancel_order_success", f"Order {order_id} cancelled successfully.")
                 return {"success": True, "order_id": order_id}
            elif isinstance(response, dict) and "error" in response:
                 # Handle cases like 404 if order doesn't exist or 422 if not cancelable
                 error_msg = response['error']
                 status_code = response.get('status_code')
                 if status_code == 404:
                     self.logger.log_warning("cancel_order_warning", f"Order {order_id} not found for cancellation.")
                     return {"success": False, "error": "Order not found", "order_id": order_id}
                 elif status_code == 422:
                     self.logger.log_warning("cancel_order_warning", f"Order {order_id} could not be cancelled (already filled/cancelled?). Error: {error_msg}")
                     return {"success": False, "error": f"Order not cancelable: {error_msg}", "order_id": order_id}
                 else:
                     self.logger.log_error("cancel_order_error", f"Failed to cancel order {order_id}: {error_msg}", details=response.get('details'))
                     return {"success": False, "error": error_msg, "order_id": order_id, "details": response.get('details')}
            else:
                 self.logger.log_error("cancel_order_error", f"Unexpected response format cancelling order {order_id}.", details=response)
                 return {"success": False, "error": "Unexpected response format", "order_id": order_id, "details": response}
        except Exception as e:
            self.logger.log_error("cancel_order_exception", f"Exception cancelling order {order_id}: {str(e)}")
            return {"success": False, "error": str(e), "order_id": order_id}
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the status of a specific order by its ID."""
        if not self.authenticated:
            self.logger.log_error("get_order_status_error", "Cannot get order status: Not authenticated.")
            return {"error": "Not authenticated"}
        
        endpoint = f"{self.ORDERS_ENDPOINT}/{order_id}"
        try:
            response = self._make_request("GET", endpoint)
            if isinstance(response, dict) and "id" in response:
                return response # Successful response with order data
            elif isinstance(response, dict) and "error" in response:
                 self.logger.log_error("get_order_status_error", f"Failed to get status for order {order_id}: {response['error']}", details=response.get('details'))
                 return {"error": response['error'], "details": response.get('details')}
            else:
                 self.logger.log_error("get_order_status_error", f"Unexpected response format getting status for order {order_id}.", details=response)
                 return {"error": "Unexpected response format", "details": response}
        except Exception as e:
            self.logger.log_error("get_order_status_exception", f"Exception getting status for order {order_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position details for a specific symbol."""
        if not self.authenticated:
            self.logger.log_error("get_position_error", "Cannot get position: Not authenticated.")
            return None
        
        formatted_symbol = self._format_symbol(symbol)
        endpoint = f"{self.POSITIONS_ENDPOINT}/{formatted_symbol}"
        try:
            response = self._make_request("GET", endpoint)
            if isinstance(response, dict) and "error" in response:
                 # Handle cases where position doesn't exist (often 404)
                 if response.get("status_code") == 404:
                      self.logger.log_info("get_position_info", f"No position found for symbol {symbol}.")
                      return None
                 else:
                      self.logger.log_error("get_position_error", f"Failed to get position for {symbol}: {response['error']}", details=response.get('details'))
                      return None
            elif isinstance(response, dict):
                 return response # Successful response with position data
            else:
                 self.logger.log_error("get_position_error", f"Unexpected response format when getting position for {symbol}.", details=response)
                 return None
        except Exception as e:
            self.logger.log_error("get_position_exception", f"Exception getting position for {symbol}: {str(e)}")
            return None
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        if not self.authenticated:
            self.logger.log_error("get_positions_error", "Cannot get positions: Not authenticated.")
            return []
        try:
            response = self._make_request("GET", self.POSITIONS_ENDPOINT)
            if isinstance(response, list):
                 return response # Successful response is a list of positions
            elif isinstance(response, dict) and "error" in response:
                 self.logger.log_error("get_positions_error", f"Failed to get positions: {response['error']}", details=response.get('details'))
                 return []
            else:
                 self.logger.log_error("get_positions_error", "Unexpected response format when getting all positions.", details=response)
                 return []
        except Exception as e:
            self.logger.log_error("get_positions_exception", f"Exception getting all positions: {str(e)}")
            return []
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close the position for a specific symbol."""
        if not self.authenticated:
            self.logger.log_error("close_position_error", "Cannot close position: Not authenticated.")
            return {"success": False, "error": "Not authenticated"}
        
        formatted_symbol = self._format_symbol(symbol)
        endpoint = f"{self.POSITIONS_ENDPOINT}/{formatted_symbol}"
        try:
            response = self._make_request("DELETE", endpoint)
            # Successful close usually returns the order details for closing the position
            if isinstance(response, dict) and "id" in response:
                 self.logger.log_info("close_position_success", f"Position for {symbol} closed successfully. Closing order: {response['id']}", details=response)
                 return {"success": True, "details": response}
            elif isinstance(response, dict) and "error" in response:
                 self.logger.log_error("close_position_error", f"Failed to close position for {symbol}: {response['error']}", details=response.get('details'))
                 return {"success": False, "error": response['error'], "details": response.get('details')}
            else:
                 # Handle cases like 404 if position didn't exist
                 if response.get("status_code") == 404:
                     self.logger.log_info("close_position_info", f"No position found for {symbol} to close.")
                     return {"success": True, "message": "No position found to close"} # Consider this success
                 else:
                     self.logger.log_error("close_position_error", f"Unexpected response format closing position for {symbol}.", details=response)
                     return {"success": False, "error": "Unexpected response format", "details": response}
        except Exception as e:
            self.logger.log_error("close_position_exception", f"Exception closing position for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.authenticated:
            # Attempt to authenticate if not already
            if not self.authenticate():
                return {"error": "Authentication failed."}
        
        try:
            response = self._make_request("GET", self.ACCOUNT_ENDPOINT)
            if isinstance(response, dict) and "error" not in response:
                return response # Successful response with account data
            elif isinstance(response, dict):
                 self.logger.log_error("get_account_error", f"Failed to get account info: {response['error']}", details=response.get('details'))
                 return {"error": response['error'], "details": response.get('details')}
            else:
                 self.logger.log_error("get_account_error", "Unexpected response format when getting account info.", details=response)
                 return {"error": "Unexpected response format", "details": response}
        except Exception as e:
            self.logger.log_error("get_account_exception", f"Exception getting account info: {str(e)}")
            return {"error": str(e)}
    
    def _place_order(self, params: Dict[str, Any], client_order_id: str) -> Dict[str, Any]:
        """Internal helper to place an order."""
        if not self.authenticated:
             self.logger.log_error("order_error", f"Cannot place order {client_order_id}: Not authenticated.")
             return {"success": False, "error": "Not authenticated", "client_order_id": client_order_id}

        try:
            response = self._make_request("POST", self.ORDERS_ENDPOINT, params)
            
            if response and "id" in response: # Check for successful order placement response
                self.logger.log_info("order_placed", f"Order {response['id']} placed successfully.", details=response)
                return {"success": True, "order_id": response["id"], "client_order_id": response["client_order_id"], "details": response}
            else:
                error_message = response.get('message', 'Unknown error') if isinstance(response, dict) else 'Invalid response'
                self.logger.log_error("order_failed", f"Failed to place order {client_order_id}: {error_message}", details=response)
                return {"success": False, "error": error_message, "client_order_id": client_order_id, "details": response}

        except Exception as e:
            self.logger.log_error("order_exception", f"Exception placing order {client_order_id}: {str(e)}")
            return {"success": False, "error": str(e), "client_order_id": client_order_id}

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, order_id: Optional[str] = None) -> Any:
        """Make a generic request to the Alpaca API with retries."""
        if not self.base_url or not self.api_key or not self.api_secret:
            self.logger.log_error("_make_request_error", "Cannot make request: API credentials or base URL not set.")
            # Attempt to authenticate implicitly if needed and not already tried
            if not self.authenticated:
                 if not self.authenticate(): # Try authenticating
                      return {"error": "Authentication failed or required configuration missing."}
                 # If auth succeeded, credentials/base_url are now set, continue with request
            else:
                 # Already authenticated but config missing? Should not happen if auth succeeded.
                 return {"error": "Configuration missing despite being authenticated."} 

        # Construct the full URL
        url = f"{self.base_url}{self.API_VERSION}{endpoint}"
        if order_id:
            url = f"{url}/{order_id}"

        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json"
        }

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=headers, json=params, timeout=15) # Longer timeout for POST
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=10)
                else:
                    self.logger.log_error("invalid_method", f"Unsupported HTTP method: {method}")
                    return {"error": f"Unsupported HTTP method: {method}"}

                # Check for non-JSON response before parsing
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    self.logger.log_error("non_json_response", 
                                        f"Received non-JSON response ({content_type}) from {url}: {response.text[:100]}...",
                                        details={"status_code": response.status_code})
                    # Return error for non-JSON if status indicates failure
                    if not response.ok:
                         return {"error": f"Request failed with status {response.status_code}", "details": response.text}
                    # Otherwise, maybe it's an okay response without JSON body (e.g., 204 No Content)
                    return {"status_code": response.status_code, "content": response.text} 
                
                # Process JSON response
                response_data = response.json()
                
                if response.ok: # Status code 2xx
                    return response_data
                else: # Status code 4xx or 5xx
                    error_message = response_data.get("message", "Unknown API error")
                    self.logger.log_warning("api_error", 
                                         f"API request to {url} failed (Status {response.status_code}): {error_message}",
                                         details=response_data)
                    # If it's a client error (4xx) that's unlikely to be fixed by retry, return error immediately
                    if 400 <= response.status_code < 500:
                         return {"error": error_message, "details": response_data, "status_code": response.status_code}
                    # For server errors (5xx) or specific retryable errors, continue to retry logic

            except requests.exceptions.RequestException as e:
                self.logger.log_warning("request_exception", f"Request to {url} failed (Attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {e}")
                # If it's the last attempt, return the error
                if attempt == self.MAX_RETRIES:
                    return {"error": str(e)}
                # Wait before retrying
                time.sleep(self.RETRY_DELAY)
            except json.JSONDecodeError as e:
                 self.logger.log_error("json_decode_error", f"Failed to decode JSON response from {url}: {response.text[:100]}...", details={"error": str(e)})
                 return {"error": "Failed to decode JSON response", "details": response.text}

        # Should not be reached if MAX_RETRIES >= 0, but as a fallback
        return {"error": "Request failed after multiple retries"}

    def _generate_client_order_id(self) -> str:
        """Generate a unique client order ID."""
        return f"vz-{uuid.uuid4().hex[:16]}"

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for Alpaca API (e.g., BTC/USD -> BTCUSD)."""
        return symbol.replace("/", "") 