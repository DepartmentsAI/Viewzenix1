"""
Risk Management System

This module contains the RiskManager class which is responsible for
implementing risk management features for the trading system.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import uuid
from datetime import datetime, timedelta

from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.broker_adapter import BrokerAdapter
from src.integration.adapters.alpaca_adapter import AlpacaAdapter

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Risk Management system that implements safety features for the trading system including
    stop-loss/take-profit functionality, portfolio protection, and cleanup services.
    """
    
    def __init__(self, broker_adapter: Optional[BrokerAdapter] = None, order_engine: Optional[OrderEngine] = None):
        """
        Initialize the RiskManager with a broker adapter and order engine.
        
        Args:
            broker_adapter: The broker adapter to use for executing orders.
                If None, AlpacaAdapter will be used by default.
            order_engine: The order engine to use for executing orders.
                If None, a new OrderEngine will be created.
        """
        # Use provided broker_adapter or create a default AlpacaAdapter
        self.broker_adapter = broker_adapter or AlpacaAdapter(use_paper=True)
        
        # Use provided order_engine or create a new one with our broker_adapter
        self.order_engine = order_engine or OrderEngine(broker_adapter=self.broker_adapter)
        
        # Default risk parameters
        self.default_risk_params = {
            'stop_loss_percent': 0.02,  # 2% stop loss by default
            'take_profit_percent': 0.05,  # 5% take profit by default
            'max_position_size_percent': 0.05,  # Max 5% of portfolio in one position
            'max_daily_drawdown_percent': 0.05,  # Max 5% daily drawdown
            'max_open_positions': 10,  # Max 10 open positions at once
            'orphaned_order_age_hours': 24,  # Consider orders orphaned after 24 hours
        }
        
        # Risk parameters dict - will be loaded from database in production
        self.risk_params = self.default_risk_params.copy()
        
        # Tracking data structures
        self.daily_performance = {
            'start_equity': 0.0,
            'current_equity': 0.0,
            'max_equity': 0.0,
            'min_equity': float('inf'),
            'last_updated': datetime.now(),
            'reset_time': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        }
        
        # Initialize the daily performance tracking
        self._initialize_daily_tracking()
        
        logger.info("RiskManager initialized with %s", type(self.broker_adapter).__name__)
    
    def _initialize_daily_tracking(self):
        """Initialize the daily performance tracking with current account equity."""
        try:
            account_info = self.broker_adapter.get_account_info()
            equity = float(account_info.get('equity', 0))
            
            self.daily_performance['start_equity'] = equity
            self.daily_performance['current_equity'] = equity
            self.daily_performance['max_equity'] = equity
            self.daily_performance['min_equity'] = equity if equity > 0 else float('inf')
            self.daily_performance['last_updated'] = datetime.now()
            
            logger.info("Daily performance tracking initialized. Start equity: %.2f", equity)
        except Exception as e:
            logger.exception("Error initializing daily performance tracking: %s", str(e))
    
    def update_risk_parameters(self, new_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update risk parameters with new values.
        
        Args:
            new_params: Dictionary containing new risk parameter values
            
        Returns:
            Updated risk parameters
        """
        logger.info("Updating risk parameters: %s", new_params)
        
        # Validate parameters
        for key, value in new_params.items():
            if key in self.risk_params:
                # Ensure percentages are in valid range
                if 'percent' in key and (value < 0 or value > 1):
                    logger.warning("Invalid percentage value for %s: %.2f", key, value)
                    continue
                
                # Ensure count parameters are positive
                if 'max' in key and value <= 0:
                    logger.warning("Invalid count value for %s: %d", key, value)
                    continue
                
                # Update the parameter
                self.risk_params[key] = value
                logger.debug("Updated %s to %s", key, value)
            else:
                logger.warning("Unknown risk parameter: %s", key)
        
        return self.risk_params.copy()
    
    def get_risk_parameters(self) -> Dict[str, Any]:
        """
        Get current risk parameters.
        
        Returns:
            Current risk parameters
        """
        return self.risk_params.copy()
    
    def process_order_with_risk_management(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an order with risk management rules applied.
        
        Args:
            order_data: Dictionary containing order data
        
        Returns:
            Dictionary with order results and risk management information
        """
        logger.info("Processing order with risk management: %s", order_data)
        
        # Check if we can accept new positions
        if not self._check_portfolio_limits(order_data):
            return {
                'status': 'rejected',
                'message': 'Order rejected due to portfolio limits',
                'order_data': order_data
            }
        
        # Update daily tracking
        self._update_daily_tracking()
        
        # Check for drawdown limits
        if not self._check_drawdown_limits():
            return {
                'status': 'rejected',
                'message': 'Order rejected due to daily drawdown limit',
                'order_data': order_data,
                'daily_performance': self.daily_performance
            }
        
        # Process the main order through the order engine
        main_order_result = self.order_engine.process_webhook_data(order_data)
        
        # If the order was successful and it's an entry (not an exit)
        if (main_order_result.get('status') == 'success' and 
            order_data.get('strategy_order_action') == 'buy' and 
            order_data.get('strategy_order_id') == 'long'):
            
            # Add stop loss / take profit
            self._add_stop_loss_take_profit(
                order_data.get('symbol'),
                float(order_data.get('strategy_order_price', 0)),
                main_order_result.get('order_id'),
                order_data.get('stop_loss'),
                order_data.get('take_profit')
            )
            
            return {
                'status': 'success',
                'message': 'Order executed with risk management',
                'order_result': main_order_result,
                'risk_applied': True
            }
        
        # For exits or failed orders, just return the original result
        return {
            'status': main_order_result.get('status'),
            'message': main_order_result.get('message'),
            'order_result': main_order_result,
            'risk_applied': False
        }
    
    def _check_portfolio_limits(self, order_data: Dict[str, Any]) -> bool:
        """
        Check if order complies with portfolio limits.
        
        Args:
            order_data: Dictionary containing order data
        
        Returns:
            Boolean indicating if order complies with limits
        """
        logger.debug("Checking portfolio limits for order")
        
        # Only check for entry orders, not exits
        if (order_data.get('strategy_order_id') == 'long' and order_data.get('strategy_order_action') == 'sell') or \
           (order_data.get('strategy_order_id') == 'sell' and order_data.get('strategy_order_action') == 'buy'):
            # This is an exit order, no need to check position limits
            return True
        
        try:
            # Check maximum number of open positions
            positions = self.broker_adapter.get_all_positions()
            if len(positions) >= self.risk_params['max_open_positions']:
                logger.warning("Maximum number of positions reached: %d", len(positions))
                return False
            
            # Get account info for position size check
            account_info = self.broker_adapter.get_account_info()
            equity = float(account_info.get('equity', 0))
            
            # Calculate order value
            symbol = order_data.get('symbol')
            price = float(order_data.get('strategy_order_price', 0))
            quantity = float(order_data.get('strategy_order_contracts', 0))
            
            if not price or not quantity:
                # If price or quantity is missing, we need to estimate them
                current_price = self._get_current_price(symbol)
                price = price or current_price
                
                # If quantity still missing, calculate based on account equity and default percentage
                if not quantity:
                    max_position_value = equity * self.risk_params['max_position_size_percent']
                    quantity = max_position_value / price
                    logger.debug("Calculated quantity: %f", quantity)
            
            # Calculate order value
            order_value = price * quantity
            
            # Check if order value exceeds maximum position size
            max_position_value = equity * self.risk_params['max_position_size_percent']
            if order_value > max_position_value:
                logger.warning("Order value (%.2f) exceeds maximum position size (%.2f)", 
                               order_value, max_position_value)
                return False
            
            return True
            
        except Exception as e:
            logger.exception("Error checking portfolio limits: %s", str(e))
            # If we can't check limits due to an error, we err on the side of caution
            return False
    
    def _check_drawdown_limits(self) -> bool:
        """
        Check if current drawdown exceeds daily limit.
        
        Returns:
            Boolean indicating if drawdown is within limits
        """
        logger.debug("Checking drawdown limits")
        
        try:
            # Update tracking first
            self._update_daily_tracking()
            
            if self.daily_performance['start_equity'] <= 0:
                # No valid starting equity, skip check
                return True
            
            # Calculate current drawdown
            current_equity = self.daily_performance['current_equity']
            max_equity = self.daily_performance['max_equity']
            
            # Use max equity as the reference point for drawdown
            if max_equity <= 0:
                return True
                
            drawdown_percent = (max_equity - current_equity) / max_equity
            max_allowed = self.risk_params['max_daily_drawdown_percent']
            
            if drawdown_percent > max_allowed:
                logger.warning("Daily drawdown (%.2f%%) exceeds maximum allowed (%.2f%%)", 
                               drawdown_percent * 100, max_allowed * 100)
                return False
            
            return True
            
        except Exception as e:
            logger.exception("Error checking drawdown limits: %s", str(e))
            # If we can't check limits due to an error, we err on the side of caution
            return True  # But for drawdown we allow it since blocking all trading might be worse
    
    def _update_daily_tracking(self):
        """Update daily performance tracking with current account information."""
        try:
            # Check if we need to reset daily tracking
            now = datetime.now()
            if now >= self.daily_performance['reset_time']:
                logger.info("Resetting daily performance tracking")
                self._initialize_daily_tracking()
                self.daily_performance['reset_time'] = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                return
            
            # Get current account info
            account_info = self.broker_adapter.get_account_info()
            current_equity = float(account_info.get('equity', 0))
            
            self.daily_performance['current_equity'] = current_equity
            self.daily_performance['max_equity'] = max(self.daily_performance['max_equity'], current_equity)
            
            if current_equity > 0:
                self.daily_performance['min_equity'] = min(self.daily_performance['min_equity'], current_equity)
                
            self.daily_performance['last_updated'] = now
            
        except Exception as e:
            logger.exception("Error updating daily tracking: %s", str(e))
    
    def _get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Current price
        """
        # Delegate to the order engine's method
        return self.order_engine._get_current_price(symbol)
    
    def _add_stop_loss_take_profit(
        self,
        symbol: str,
        entry_price: float,
        parent_order_id: str,
        stop_loss_param: Optional[Dict[str, Any]] = None,
        take_profit_param: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add stop loss and take profit orders for an executed entry order.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price of the main order
            parent_order_id: ID of the parent order
            stop_loss_param: Custom stop loss parameters
            take_profit_param: Custom take profit parameters
            
        Returns:
            Dictionary with results of SL/TP orders
        """
        logger.info("Adding stop loss / take profit for %s at price %.2f", symbol, entry_price)
        
        results = {
            'stop_loss': None,
            'take_profit': None
        }
        
        try:
            # Get position to determine quantity and side
            position = self.broker_adapter.get_position(symbol)
            if not position:
                logger.warning("No position found for %s to add SL/TP", symbol)
                return results
            
            position_qty = float(position.get('qty', 0))
            position_side = position.get('side', '').lower()
            
            if position_qty <= 0:
                logger.warning("Invalid position quantity: %f", position_qty)
                return results
            
            # Calculate stop loss and take profit prices
            sl_percent = stop_loss_param.get('percent') if stop_loss_param else self.risk_params['stop_loss_percent']
            tp_percent = take_profit_param.get('percent') if take_profit_param else self.risk_params['take_profit_percent']
            
            # Fixed prices take priority over percentages
            sl_price = None
            tp_price = None
            
            if stop_loss_param and 'price' in stop_loss_param:
                sl_price = float(stop_loss_param['price'])
            elif position_side == 'long':
                sl_price = entry_price * (1 - sl_percent)
            else:  # short position
                sl_price = entry_price * (1 + sl_percent)
                
            if take_profit_param and 'price' in take_profit_param:
                tp_price = float(take_profit_param['price'])
            elif position_side == 'long':
                tp_price = entry_price * (1 + tp_percent)
            else:  # short position
                tp_price = entry_price * (1 - tp_percent)
            
            # Round prices to appropriate precision
            sl_price = round(sl_price, 2)
            tp_price = round(tp_price, 2)
            
            logger.info("Calculated SL: %.2f, TP: %.2f for %s %s position", 
                       sl_price, tp_price, position_side, symbol)
            
            # Create stop loss order
            sl_side = 'sell' if position_side == 'long' else 'buy'
            sl_client_order_id = f"sl-{parent_order_id}"
            
            try:
                sl_result = self.broker_adapter.place_stop_order(
                    symbol, position_qty, sl_side, sl_price, sl_client_order_id
                )
                results['stop_loss'] = sl_result
                logger.info("Stop loss order placed: %s", sl_result.get('id'))
            except Exception as e:
                logger.exception("Error placing stop loss order: %s", str(e))
            
            # Create take profit order
            tp_side = 'sell' if position_side == 'long' else 'buy'
            tp_client_order_id = f"tp-{parent_order_id}"
            
            try:
                tp_result = self.broker_adapter.place_limit_order(
                    symbol, position_qty, tp_side, tp_price, tp_client_order_id
                )
                results['take_profit'] = tp_result
                logger.info("Take profit order placed: %s", tp_result.get('id'))
            except Exception as e:
                logger.exception("Error placing take profit order: %s", str(e))
            
            return results
            
        except Exception as e:
            logger.exception("Error adding stop loss / take profit: %s", str(e))
            return results
    
    def cleanup_orphaned_orders(self) -> Dict[str, Any]:
        """
        Clean up orphaned orders (orders without parent/child relationships or stale orders).
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info("Running orphaned order cleanup")
        
        results = {
            'cleaned_orders': [],
            'errors': [],
            'total_cleaned': 0
        }
        
        try:
            # Get all orders
            orders = self.broker_adapter.get_all_orders()
            
            # Get cutoff time for stale orders
            cutoff_time = datetime.now() - timedelta(hours=self.risk_params['orphaned_order_age_hours'])
            
            # Filter orders to find orphaned ones
            for order in orders:
                order_id = order.get('id')
                order_status = order.get('status')
                
                # Skip already filled or canceled orders
                if order_status in ['filled', 'canceled']:
                    continue
                
                # Check if order is stale
                created_at = datetime.fromisoformat(order.get('created_at').replace('Z', '+00:00'))
                if created_at < cutoff_time:
                    logger.info("Found stale order: %s, created at %s", order_id, created_at)
                    
                    # Cancel the order
                    try:
                        cancel_result = self.broker_adapter.cancel_order(order_id)
                        results['cleaned_orders'].append({
                            'order_id': order_id,
                            'reason': 'stale',
                            'created_at': created_at.isoformat()
                        })
                        results['total_cleaned'] += 1
                    except Exception as e:
                        logger.exception("Error canceling stale order %s: %s", order_id, str(e))
                        results['errors'].append({
                            'order_id': order_id,
                            'error': str(e)
                        })
            
            return results
            
        except Exception as e:
            logger.exception("Error cleaning up orphaned orders: %s", str(e))
            results['errors'].append({
                'error': str(e)
            })
            return results
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics for the account.
        
        Returns:
            Dictionary with risk metrics
        """
        metrics = {
            'portfolio': {
                'equity': 0,
                'cash': 0,
                'positions_count': 0,
                'positions_value': 0,
                'largest_position': {
                    'symbol': None,
                    'value': 0,
                    'percent_of_portfolio': 0
                }
            },
            'daily_performance': self.daily_performance.copy(),
            'risk_parameters': self.risk_params.copy()
        }
        
        try:
            # Get account info
            account_info = self.broker_adapter.get_account_info()
            metrics['portfolio']['equity'] = float(account_info.get('equity', 0))
            metrics['portfolio']['cash'] = float(account_info.get('cash', 0))
            
            # Get positions
            positions = self.broker_adapter.get_all_positions()
            metrics['portfolio']['positions_count'] = len(positions)
            
            total_value = 0
            largest_value = 0
            largest_symbol = None
            
            for position in positions:
                symbol = position.get('symbol')
                market_value = float(position.get('market_value', 0))
                
                total_value += market_value
                
                if market_value > largest_value:
                    largest_value = market_value
                    largest_symbol = symbol
            
            metrics['portfolio']['positions_value'] = total_value
            
            if largest_symbol and metrics['portfolio']['equity'] > 0:
                metrics['portfolio']['largest_position']['symbol'] = largest_symbol
                metrics['portfolio']['largest_position']['value'] = largest_value
                metrics['portfolio']['largest_position']['percent_of_portfolio'] = largest_value / metrics['portfolio']['equity']
            
            # Calculate current drawdown
            if metrics['daily_performance']['max_equity'] > 0:
                current_equity = metrics['daily_performance']['current_equity']
                max_equity = metrics['daily_performance']['max_equity']
                metrics['daily_performance']['current_drawdown_percent'] = (max_equity - current_equity) / max_equity
            
            return metrics
            
        except Exception as e:
            logger.exception("Error getting risk metrics: %s", str(e))
            return metrics 