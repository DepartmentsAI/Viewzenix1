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
        # Only apply limits to buy/entry orders
        if order_data.get('strategy_order_action') != 'buy':
            return True
            
        try:
            # Get current positions
            positions = self.broker_adapter.get_positions()
            
            # Check for maximum number of open positions
            if len(positions) >= self.risk_params['max_open_positions']:
                logger.warning(
                    "Maximum number of open positions reached: %d/%d", 
                    len(positions), 
                    self.risk_params['max_open_positions']
                )
                return False
            
            # Check position size limit
            account_info = self.broker_adapter.get_account_info()
            equity = float(account_info.get('equity', 0))
            
            # Calculate order value
            price = float(order_data.get('strategy_order_price', 0))
            quantity = 1  # Default quantity if not specified
            if 'quantity' in order_data:
                quantity = int(order_data['quantity'])
            
            order_value = price * quantity
            
            # Check if order exceeds max position size percent
            max_position_value = equity * self.risk_params['max_position_size_percent']
            if order_value > max_position_value:
                logger.warning(
                    "Order value exceeds maximum position size: %.2f > %.2f (%.2f%% of %.2f)", 
                    order_value, 
                    max_position_value,
                    self.risk_params['max_position_size_percent'] * 100,
                    equity
                )
                return False
            
            return True
        except Exception as e:
            logger.exception("Error checking portfolio limits: %s", str(e))
            # Default to allowing the order in case of error
            return True
    
    def _check_drawdown_limits(self) -> bool:
        """
        Check if daily drawdown limit has been exceeded.
        
        Returns:
            Boolean indicating if drawdown limit is respected
        """
        try:
            # Check if we need to reset daily tracking (new day)
            now = datetime.now()
            if now >= self.daily_performance['reset_time']:
                logger.info("Resetting daily performance tracking for new day")
                self._initialize_daily_tracking()
                return True
            
            # Calculate current drawdown
            start_equity = self.daily_performance['start_equity']
            current_equity = self.daily_performance['current_equity']
            
            if start_equity <= 0:
                return True  # Cannot calculate drawdown with zero equity
            
            drawdown = (start_equity - current_equity) / start_equity
            max_drawdown = self.risk_params['max_daily_drawdown_percent']
            
            if drawdown > max_drawdown:
                logger.warning(
                    "Daily drawdown limit exceeded: %.2f%% > %.2f%%", 
                    drawdown * 100, 
                    max_drawdown * 100
                )
                return False
            
            return True
        except Exception as e:
            logger.exception("Error checking drawdown limits: %s", str(e))
            # Default to allowing the order in case of error
            return True
    
    def _update_daily_tracking(self):
        """Update the daily performance tracking with current account equity."""
        try:
            account_info = self.broker_adapter.get_account_info()
            equity = float(account_info.get('equity', 0))
            
            self.daily_performance['current_equity'] = equity
            self.daily_performance['last_updated'] = datetime.now()
            
            # Update max/min equity values
            if equity > self.daily_performance['max_equity']:
                self.daily_performance['max_equity'] = equity
            
            if equity < self.daily_performance['min_equity'] and equity > 0:
                self.daily_performance['min_equity'] = equity
            
            logger.debug("Updated daily tracking. Current equity: %.2f", equity)
        except Exception as e:
            logger.exception("Error updating daily performance tracking: %s", str(e))
    
    def _get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: The trading symbol to get price for
        
        Returns:
            Current price as float
        """
        try:
            return self.broker_adapter.get_current_price(symbol)
        except Exception as e:
            logger.exception("Error getting current price for %s: %s", symbol, str(e))
            return 0.0
    
    def _add_stop_loss_take_profit(
        self,
        symbol: str,
        entry_price: float,
        parent_order_id: str,
        stop_loss_param: Optional[Dict[str, Any]] = None,
        take_profit_param: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add stop loss and take profit orders for a position.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price of the position
            parent_order_id: ID of the parent order
            stop_loss_param: Optional stop loss parameters (price or percent)
            take_profit_param: Optional take profit parameters (price or percent)
            
        Returns:
            Dictionary with results of SL/TP orders
        """
        results = {
            'stop_loss': None,
            'take_profit': None
        }
        
        try:
            # Process stop loss
            if stop_loss_param:
                stop_price = None
                
                # Use explicit price if provided
                if 'price' in stop_loss_param:
                    stop_price = float(stop_loss_param['price'])
                    logger.info("Using explicit stop loss price: %.2f", stop_price)
                
                # Otherwise calculate based on percent
                elif 'percent' in stop_loss_param:
                    percent = float(stop_loss_param['percent'])
                    stop_price = entry_price * (1 - percent)
                    logger.info(
                        "Calculated stop loss price: %.2f (%.2f%% below %.2f)", 
                        stop_price, 
                        percent * 100, 
                        entry_price
                    )
                
                # If no explicit params, use default percentage
                else:
                    percent = self.risk_params['stop_loss_percent']
                    stop_price = entry_price * (1 - percent)
                    logger.info(
                        "Using default stop loss: %.2f (%.2f%% below %.2f)", 
                        stop_price, 
                        percent * 100, 
                        entry_price
                    )
                
                # Create stop loss order
                if stop_price:
                    stop_loss_data = {
                        'symbol': symbol,
                        'strategy_order_id': f"sl_{parent_order_id}",
                        'strategy_order_action': 'sell',
                        'strategy_order_price': stop_price,
                        'strategy_order_comment': f"Stop Loss for {parent_order_id}",
                        'time': int(time.time()),
                        'order_type': 'stop'
                    }
                    
                    # Process through order engine
                    sl_result = self.order_engine.process_webhook_data(stop_loss_data)
                    results['stop_loss'] = sl_result
                    logger.info("Created stop loss order: %s", sl_result)
            
            # Process take profit
            if take_profit_param:
                take_profit_price = None
                
                # Use explicit price if provided
                if 'price' in take_profit_param:
                    take_profit_price = float(take_profit_param['price'])
                    logger.info("Using explicit take profit price: %.2f", take_profit_price)
                
                # Otherwise calculate based on percent
                elif 'percent' in take_profit_param:
                    percent = float(take_profit_param['percent'])
                    take_profit_price = entry_price * (1 + percent)
                    logger.info(
                        "Calculated take profit price: %.2f (%.2f%% above %.2f)", 
                        take_profit_price, 
                        percent * 100, 
                        entry_price
                    )
                
                # If no explicit params, use default percentage
                else:
                    percent = self.risk_params['take_profit_percent']
                    take_profit_price = entry_price * (1 + percent)
                    logger.info(
                        "Using default take profit: %.2f (%.2f%% above %.2f)", 
                        take_profit_price, 
                        percent * 100, 
                        entry_price
                    )
                
                # Create take profit order
                if take_profit_price:
                    take_profit_data = {
                        'symbol': symbol,
                        'strategy_order_id': f"tp_{parent_order_id}",
                        'strategy_order_action': 'sell',
                        'strategy_order_price': take_profit_price,
                        'strategy_order_comment': f"Take Profit for {parent_order_id}",
                        'time': int(time.time()),
                        'order_type': 'limit'
                    }
                    
                    # Process through order engine
                    tp_result = self.order_engine.process_webhook_data(take_profit_data)
                    results['take_profit'] = tp_result
                    logger.info("Created take profit order: %s", tp_result)
            
            return results
        except Exception as e:
            logger.exception("Error adding stop loss/take profit: %s", str(e))
            return results
    
    def cleanup_orphaned_orders(self) -> Dict[str, Any]:
        """
        Cleanup orphaned orders older than the configured threshold.
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting orphaned order cleanup")
        
        try:
            # Get all open orders
            open_orders = self.broker_adapter.get_open_orders()
            
            cleanup_results = {
                'orders_checked': len(open_orders),
                'orders_cancelled': 0,
                'cancelled_ids': [],
                'errors': []
            }
            
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=self.risk_params['orphaned_order_age_hours'])
            
            for order in open_orders:
                # Skip if order has no timestamp or is a market order
                if 'created_at' not in order or order.get('type') == 'market':
                    continue
                
                # Parse the creation timestamp
                created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                
                # Check if order is older than the cutoff
                if created_at < cutoff_time:
                    order_id = order.get('id')
                    logger.info(
                        "Cancelling orphaned order %s created at %s (older than %s hours)",
                        order_id,
                        created_at,
                        self.risk_params['orphaned_order_age_hours']
                    )
                    
                    try:
                        self.broker_adapter.cancel_order(order_id)
                        cleanup_results['orders_cancelled'] += 1
                        cleanup_results['cancelled_ids'].append(order_id)
                    except Exception as e:
                        logger.exception("Error cancelling orphaned order %s: %s", order_id, str(e))
                        cleanup_results['errors'].append({
                            'order_id': order_id,
                            'error': str(e)
                        })
            
            logger.info(
                "Orphaned order cleanup complete: %d/%d cancelled",
                cleanup_results['orders_cancelled'],
                cleanup_results['orders_checked']
            )
            
            return cleanup_results
        except Exception as e:
            logger.exception("Error cleaning up orphaned orders: %s", str(e))
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics.
        
        Returns:
            Dictionary with current risk metrics
        """
        try:
            # Update daily tracking to get latest values
            self._update_daily_tracking()
            
            # Get account info
            account_info = self.broker_adapter.get_account_info()
            buying_power = float(account_info.get('buying_power', 0))
            equity = float(account_info.get('equity', 0))
            
            # Get positions and calculate total exposure
            positions = self.broker_adapter.get_positions()
            position_count = len(positions)
            
            position_value = 0.0
            for position in positions:
                position_value += float(position.get('market_value', 0))
            
            # Calculate exposure percentage
            exposure_percent = 0.0
            if equity > 0:
                exposure_percent = position_value / equity
            
            # Calculate daily drawdown
            drawdown = 0.0
            if self.daily_performance['start_equity'] > 0:
                drawdown = (self.daily_performance['start_equity'] - self.daily_performance['current_equity']) / self.daily_performance['start_equity']
            
            return {
                'account': {
                    'equity': equity,
                    'buying_power': buying_power
                },
                'positions': {
                    'count': position_count,
                    'value': position_value,
                    'exposure_percent': exposure_percent,
                    'max_positions': self.risk_params['max_open_positions']
                },
                'daily_performance': {
                    'start_equity': self.daily_performance['start_equity'],
                    'current_equity': self.daily_performance['current_equity'],
                    'max_equity': self.daily_performance['max_equity'],
                    'min_equity': self.daily_performance['min_equity'],
                    'drawdown': drawdown,
                    'drawdown_limit': self.risk_params['max_daily_drawdown_percent'],
                    'last_updated': self.daily_performance['last_updated'].isoformat(),
                    'reset_time': self.daily_performance['reset_time'].isoformat()
                },
                'risk_limits': {
                    'max_position_size': round(equity * self.risk_params['max_position_size_percent'], 2)
                }
            }
        except Exception as e:
            logger.exception("Error getting risk metrics: %s", str(e))
            return {
                'status': 'error',
                'message': str(e)
            } 