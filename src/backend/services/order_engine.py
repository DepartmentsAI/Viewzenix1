"""
Order Execution Engine

This module contains the OrderEngine class which is responsible for processing
trade requests and executing orders through the appropriate broker adapter.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import uuid

from src.integration.adapters.broker_adapter import BrokerAdapter
from src.integration.adapters.alpaca_adapter import AlpacaAdapter

logger = logging.getLogger(__name__)

class OrderEngine:
    """
    Order Execution Engine for processing trade requests and executing orders
    through the appropriate broker adapter.
    """
    
    def __init__(self, broker_adapter: Optional[BrokerAdapter] = None):
        """
        Initialize the OrderEngine with a broker adapter.
        
        Args:
            broker_adapter: The broker adapter to use for executing orders.
                If None, AlpacaAdapter will be used by default.
        """
        # Use provided broker_adapter or create a default AlpacaAdapter
        self.broker_adapter = broker_adapter or AlpacaAdapter(use_paper=True)
        
        # Maximum number of retries for failed order executions
        self.max_retries = 3
        
        # Delay between retries in seconds
        self.retry_delay = 2
        
        logger.info("OrderEngine initialized with %s", type(self.broker_adapter).__name__)
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook data and execute the appropriate order.
        
        Args:
            webhook_data: Dictionary containing webhook data from TradingView alerts
        
        Returns:
            Dict containing the result of the order execution
        """
        logger.info("Processing webhook data: %s", webhook_data)
        
        try:
            # Extract necessary information from webhook data
            symbol = webhook_data.get('symbol')
            strategy_order_id = webhook_data.get('strategy_order_id')
            strategy_order_action = webhook_data.get('strategy_order_action')
            strategy_order_contracts = webhook_data.get('strategy_order_contracts')
            strategy_order_price = webhook_data.get('strategy_order_price')
            
            # Validate required fields
            if not all([symbol, strategy_order_id, strategy_order_action]):
                logger.error("Missing required fields in webhook data")
                return {
                    'status': 'error',
                    'message': 'Missing required fields in webhook data',
                    'webhook_data': webhook_data
                }
            
            # Determine trade type based on mapping
            trade_type = self._determine_trade_type(strategy_order_id, strategy_order_action)
            
            # Handle different trade types
            if trade_type == 'long_entry' or trade_type == 'short_entry':
                # For entries, we need quantity
                quantity = self._determine_order_quantity(
                    strategy_order_contracts, symbol, trade_type
                )
                
                # Execute the order
                return self._execute_entry_order(
                    symbol, 
                    quantity, 
                    'buy' if trade_type == 'long_entry' else 'sell',
                    strategy_order_price,
                    webhook_data
                )
            
            elif trade_type == 'long_exit' or trade_type == 'short_exit':
                # For exits, we close the position
                return self._execute_exit_order(
                    symbol,
                    'sell' if trade_type == 'long_exit' else 'buy',
                    webhook_data
                )
            
            else:
                logger.error("Unknown trade type: %s", trade_type)
                return {
                    'status': 'error',
                    'message': f'Unknown trade type: {trade_type}',
                    'webhook_data': webhook_data
                }
                
        except Exception as e:
            logger.exception("Error processing webhook data: %s", str(e))
            return {
                'status': 'error',
                'message': f'Error processing webhook data: {str(e)}',
                'webhook_data': webhook_data
            }
    
    def _determine_trade_type(self, strategy_order_id: str, strategy_order_action: str) -> str:
        """
        Determine the trade type based on strategy_order_id and strategy_order_action.
        
        Args:
            strategy_order_id: 'long' or 'sell'
            strategy_order_action: 'buy' or 'sell'
        
        Returns:
            Trade type: 'long_entry', 'long_exit', 'short_entry', or 'short_exit'
        """
        logger.debug("Determining trade type: %s, %s", strategy_order_id, strategy_order_action)
        
        if strategy_order_id == 'long':
            if strategy_order_action == 'buy':
                return 'long_entry'
            elif strategy_order_action == 'sell':
                return 'long_exit'
        
        elif strategy_order_id == 'sell':
            if strategy_order_action == 'sell':
                return 'short_entry'
            elif strategy_order_action == 'buy':
                return 'short_exit'
        
        logger.warning("Unknown combination: %s, %s", strategy_order_id, strategy_order_action)
        return 'unknown'
    
    def _determine_order_quantity(
        self, 
        strategy_order_contracts: Optional[float],
        symbol: str,
        trade_type: str
    ) -> float:
        """
        Determine the order quantity based on strategy_order_contracts or a default calculation.
        
        Args:
            strategy_order_contracts: Optional quantity from TradingView alert
            symbol: The trading symbol
            trade_type: Type of trade ('long_entry', 'short_entry', etc.)
        
        Returns:
            Quantity to trade
        """
        logger.debug("Determining order quantity for %s", symbol)
        
        # If contracts are specified in the alert, use them
        if strategy_order_contracts is not None:
            logger.debug("Using quantity from alert: %s", strategy_order_contracts)
            return float(strategy_order_contracts)
        
        # Otherwise, calculate based on account equity and default percentage
        try:
            # Get account information
            account_info = self.broker_adapter.get_account_info()
            
            # Use 2% of equity by default
            equity = float(account_info.get('equity', 0))
            default_percentage = 0.02
            
            # Get current price (in a production system, this would be more robust)
            price = self._get_current_price(symbol)
            
            # Calculate quantity
            quantity = (equity * default_percentage) / price
            
            logger.debug("Calculated quantity: %s (%.2f%% of equity)", quantity, default_percentage * 100)
            return quantity
            
        except Exception as e:
            logger.exception("Error calculating order quantity: %s", str(e))
            # Return a safe minimum quantity
            return 0.01  # Minimum for crypto, would need to be adjusted for other asset classes
    
    def _get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        In a real implementation, this would call a market data provider.
        For now, we use a simplistic approach by checking if there's an existing position.
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Current price
        """
        # In a real implementation, this would use a market data provider
        # For simplicity, we're using a fixed value if we can't get a position
        position = self.broker_adapter.get_position(symbol)
        if position:
            return float(position.get('current_price', 10000))
        return 10000  # Default for testing
    
    def _execute_entry_order(
        self,
        symbol: str,
        quantity: float,
        side: str,
        price: Optional[float] = None,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an entry order with retries.
        
        Args:
            symbol: The trading symbol
            quantity: Quantity to trade
            side: 'buy' or 'sell'
            price: Optional price for limit orders
            webhook_data: Original webhook data for logging
            
        Returns:
            Dict containing the result of the order execution
        """
        logger.info("Executing %s entry order for %s, quantity: %s", side, symbol, quantity)
        
        # Generate a unique client order ID
        client_order_id = f"tv-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        
        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                # Execute order based on price
                if price is None:
                    # Market order
                    result = self.broker_adapter.place_market_order(
                        symbol, quantity, side, client_order_id
                    )
                else:
                    # Limit order
                    result = self.broker_adapter.place_limit_order(
                        symbol, quantity, side, price, client_order_id
                    )
                
                # Check if order was successful
                if result and 'id' in result:
                    logger.info("Order executed successfully: %s", result.get('id'))
                    return {
                        'status': 'success',
                        'order_id': result.get('id'),
                        'client_order_id': client_order_id,
                        'message': f"Successfully placed {side} order for {symbol}",
                        'result': result
                    }
                else:
                    logger.warning("Order execution returned unexpected result: %s", result)
                    if attempt < self.max_retries:
                        logger.info("Retrying order execution (attempt %s of %s)...", 
                                  attempt, self.max_retries)
                        time.sleep(self.retry_delay)
                    else:
                        return {
                            'status': 'error',
                            'message': f"Failed to execute order after {self.max_retries} attempts",
                            'result': result,
                            'webhook_data': webhook_data
                        }
            
            except Exception as e:
                logger.exception("Error executing order (attempt %s of %s): %s", 
                               attempt, self.max_retries, str(e))
                if attempt < self.max_retries:
                    logger.info("Retrying order execution...")
                    time.sleep(self.retry_delay)
                else:
                    return {
                        'status': 'error',
                        'message': f"Exception during order execution: {str(e)}",
                        'webhook_data': webhook_data
                    }
        
        # Should not reach here, but just in case
        return {
            'status': 'error',
            'message': "Failed to execute order",
            'webhook_data': webhook_data
        }
    
    def _execute_exit_order(
        self,
        symbol: str,
        side: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an exit order (close position).
        
        Args:
            symbol: The trading symbol
            side: 'buy' or 'sell'
            webhook_data: Original webhook data for logging
            
        Returns:
            Dict containing the result of the order execution
        """
        logger.info("Executing exit order for %s", symbol)
        
        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                # Check if position exists
                position = self.broker_adapter.get_position(symbol)
                
                if not position:
                    logger.warning("No position found for %s", symbol)
                    return {
                        'status': 'warning',
                        'message': f"No position found for {symbol}",
                        'webhook_data': webhook_data
                    }
                
                # Close the position
                result = self.broker_adapter.close_position(symbol)
                
                if result and 'symbol' in result:
                    logger.info("Position closed successfully: %s", symbol)
                    return {
                        'status': 'success',
                        'message': f"Successfully closed position for {symbol}",
                        'result': result
                    }
                else:
                    logger.warning("Position closure returned unexpected result: %s", result)
                    if attempt < self.max_retries:
                        logger.info("Retrying position closure (attempt %s of %s)...", 
                                   attempt, self.max_retries)
                        time.sleep(self.retry_delay)
                    else:
                        return {
                            'status': 'error',
                            'message': f"Failed to close position after {self.max_retries} attempts",
                            'result': result,
                            'webhook_data': webhook_data
                        }
            
            except Exception as e:
                logger.exception("Error closing position (attempt %s of %s): %s", 
                                attempt, self.max_retries, str(e))
                if attempt < self.max_retries:
                    logger.info("Retrying position closure...")
                    time.sleep(self.retry_delay)
                else:
                    return {
                        'status': 'error',
                        'message': f"Exception during position closure: {str(e)}",
                        'webhook_data': webhook_data
                    }
        
        # Should not reach here, but just in case
        return {
            'status': 'error',
            'message': "Failed to close position",
            'webhook_data': webhook_data
        } 