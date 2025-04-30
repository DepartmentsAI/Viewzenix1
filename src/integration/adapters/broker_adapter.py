from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BrokerAdapter(ABC):
    """Base interface for all broker adapters.
    
    All broker-specific adapters should implement this interface to ensure
    consistent functionality across different brokers.
    """
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the broker API.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order.
        
        Args:
            order_id: The ID of the order to cancel
            
        Returns:
            Dict containing the cancellation result
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the status of an existing order.
        
        Args:
            order_id: The ID of the order to check
            
        Returns:
            Dict containing the order status
        """
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for a symbol.
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Dict containing position information or None if no position exists
        """
        pass
    
    @abstractmethod
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all current positions.
        
        Returns:
            List of dictionaries containing position information
        """
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position for a specific symbol.
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Dict containing the result of the position closure
        """
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information including equity, buying power, etc.
        
        Returns:
            Dict containing account information
        """
        pass 