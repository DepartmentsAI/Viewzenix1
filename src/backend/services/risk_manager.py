"""
Risk Management System

This module contains the RiskManager class which is responsible for
implementing risk management features for the trading system.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import uuid
import json
import os
from datetime import datetime, timedelta

from src.backend.services.order_engine import OrderEngine
from src.integration.adapters.broker_adapter import BrokerAdapter
from src.integration.adapters.alpaca_adapter import AlpacaAdapter
from src.backend.models.risk_models import (
    RiskParameters, 
    RiskMetrics, 
    StopLossTakeProfitSettings, 
    PortfolioProtectionSettings,
    CleanupSettings
)

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
        
        # Initialize risk parameters with default values
        self.risk_parameters = RiskParameters()
        
        # Try to load risk parameters from disk
        self._load_risk_parameters()
        
        # Initialize risk metrics
        self.risk_metrics = RiskMetrics()
        
        # Initialize the risk metrics with current account data
        self._initialize_risk_metrics()
        
        logger.info("RiskManager initialized with %s", type(self.broker_adapter).__name__)
    
    def _initialize_risk_metrics(self):
        """Initialize the risk metrics with current account equity."""
        try:
            account_info = self.broker_adapter.get_account_info()
            equity = float(account_info.get('equity', 0))
            
            self.risk_metrics.current_equity = equity
            self.risk_metrics.starting_equity = equity
            self.risk_metrics.last_updated = time.time()
            
            # Get open positions
            positions = self.broker_adapter.get_positions()
            self.risk_metrics.open_position_count = len(positions)
            
            # Calculate position sizes as percentage of equity
            position_sizes = []
            total_exposure = 0.0
            
            for position in positions:
                market_value = float(position.get('market_value', 0))
                position_size_pct = market_value / equity if equity > 0 else 0
                position_sizes.append(position_size_pct)
                total_exposure += position_size_pct
            
            self.risk_metrics.position_sizes = position_sizes
            self.risk_metrics.total_exposure_percent = total_exposure
            
            logger.info("Risk metrics initialized. Equity: %.2f, Positions: %d", 
                        equity, self.risk_metrics.open_position_count)
        except Exception as e:
            logger.exception("Error initializing risk metrics: %s", str(e))
    
    def _load_risk_parameters(self):
        """Load risk parameters from disk or create default."""
        config_dir = os.path.join("config")
        config_file = os.path.join(config_dir, "risk_parameters.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    risk_data = json.load(f)
                    self.risk_parameters = RiskParameters.from_dict(risk_data)
                    logger.info("Risk parameters loaded from %s", config_file)
            else:
                # Use defaults and save them
                logger.info("No risk parameters file found, using defaults")
                self._save_risk_parameters()
        except Exception as e:
            logger.exception("Error loading risk parameters: %s", str(e))
    
    def _save_risk_parameters(self):
        """Save current risk parameters to disk."""
        config_dir = os.path.join("config")
        
        # Ensure config directory exists
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        config_file = os.path.join(config_dir, "risk_parameters.json")
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.risk_parameters.to_dict(), f, indent=2)
                logger.info("Risk parameters saved to %s", config_file)
        except Exception as e:
            logger.exception("Error saving risk parameters: %s", str(e))
    
    def update_risk_parameters(self, new_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update risk parameters with new values.
        
        Args:
            new_params: Dictionary containing new risk parameter values
            
        Returns:
            Updated risk parameters as a dictionary
        """
        logger.info("Updating risk parameters: %s", new_params)
        
        # Update SL/TP settings
        sl_tp_data = new_params.get("sl_tp", {})
        if sl_tp_data:
            for key, value in sl_tp_data.items():
                if hasattr(self.risk_parameters.sl_tp, key):
                    setattr(self.risk_parameters.sl_tp, key, value)
                    logger.debug("Updated sl_tp.%s to %s", key, value)
        
        # Update portfolio protection settings
        portfolio_data = new_params.get("portfolio", {})
        if portfolio_data:
            for key, value in portfolio_data.items():
                if hasattr(self.risk_parameters.portfolio, key):
                    setattr(self.risk_parameters.portfolio, key, value)
                    logger.debug("Updated portfolio.%s to %s", key, value)
        
        # Update cleanup settings
        cleanup_data = new_params.get("cleanup", {})
        if cleanup_data:
            for key, value in cleanup_data.items():
                if hasattr(self.risk_parameters.cleanup, key):
                    setattr(self.risk_parameters.cleanup, key, value)
                    logger.debug("Updated cleanup.%s to %s", key, value)
        
        # Save updated parameters
        self._save_risk_parameters()
        
        return self.risk_parameters.to_dict()
    
    def get_risk_parameters(self) -> Dict[str, Any]:
        """
        Get current risk parameters.
        
        Returns:
            Current risk parameters as a dictionary
        """
        return self.risk_parameters.to_dict()
    
    def process_order_with_risk_management(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an order with risk management rules applied.
        
        Args:
            order_data: Dictionary containing order data
        
        Returns:
            Dictionary with order results and risk management information
        """
        logger.info("Processing order with risk management: %s", order_data)
        
        # Update risk metrics before processing
        self._update_risk_metrics()
        
        # Check if we can accept new positions
        if not self._check_portfolio_limits(order_data):
            logger.warning("Order rejected: Portfolio limits exceeded")
            return {
                'status': 'rejected',
                'message': 'Order rejected due to portfolio limits',
                'order_data': order_data,
                'risk_metrics': self._get_risk_metrics_dict()
            }
        
        # Check for drawdown limits
        if not self._check_drawdown_limits():
            logger.warning("Order rejected: Daily drawdown limit exceeded")
            return {
                'status': 'rejected',
                'message': 'Order rejected due to daily drawdown limit',
                'order_data': order_data,
                'risk_metrics': self._get_risk_metrics_dict()
            }
        
        # Process the main order through the order engine
        main_order_result = self.order_engine.process_webhook_data(order_data)
        
        # If the order was successful and it's a long entry
        trade_type = self._determine_trade_type(
            order_data.get('strategy_order_id', ''),
            order_data.get('strategy_order_action', '')
        )
        
        if (main_order_result.get('status') == 'success' and 
            (trade_type == 'long_entry' or trade_type == 'short_entry')):
            
            # Only add SL/TP if enabled
            if self.risk_parameters.sl_tp.enabled:
                sl_tp_result = self._add_stop_loss_take_profit(
                    order_data.get('symbol'),
                    float(order_data.get('strategy_order_price', 0)),
                    main_order_result.get('order_id'),
                    self._get_custom_sl_tp_params(order_data)
                )
                
                # Add SL/TP information to the result
                main_order_result['sl_tp_orders'] = sl_tp_result.get('orders', [])
                main_order_result['sl_tp_status'] = sl_tp_result.get('status')
            
            # Update risk metrics after successful order
            self._update_risk_metrics()
            
            return {
                'status': 'success',
                'message': 'Order executed with risk management',
                'order_result': main_order_result,
                'risk_applied': True,
                'risk_metrics': self._get_risk_metrics_dict()
            }
        
        # For exits or failed orders, just return the original result
        return {
            'status': main_order_result.get('status'),
            'message': main_order_result.get('message'),
            'order_result': main_order_result,
            'risk_applied': False,
            'risk_metrics': self._get_risk_metrics_dict()
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
        
        return 'unknown'
    
    def _get_custom_sl_tp_params(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract custom SL/TP parameters from order data if present,
        otherwise use default parameters.
        
        Args:
            order_data: Dictionary containing order data
            
        Returns:
            Dictionary with SL/TP parameters
        """
        # Start with default parameters
        params = {
            'stop_loss_percent': self.risk_parameters.sl_tp.stop_loss_percent,
            'take_profit_percent': self.risk_parameters.sl_tp.take_profit_percent,
            'use_fixed_price': self.risk_parameters.sl_tp.use_fixed_price,
            'fixed_stop_loss_price': self.risk_parameters.sl_tp.fixed_stop_loss_price,
            'fixed_take_profit_price': self.risk_parameters.sl_tp.fixed_take_profit_price,
            'use_fill_price_for_sl_tp': self.risk_parameters.sl_tp.use_fill_price_for_sl_tp
        }
        
        # Override with custom parameters from order if present
        custom_sl_tp = order_data.get('sl_tp', {})
        if custom_sl_tp:
            for key in params:
                if key in custom_sl_tp:
                    params[key] = custom_sl_tp[key]
        
        return params
    
    def _check_portfolio_limits(self, order_data: Dict[str, Any]) -> bool:
        """
        Check if order complies with portfolio limits.
        
        Args:
            order_data: Dictionary containing order data
        
        Returns:
            Boolean indicating if order complies with limits
        """
        # Skip checks if portfolio protection is disabled
        if not self.risk_parameters.portfolio.enabled:
            return True
        
        # Skip limit checks for exit orders
        trade_type = self._determine_trade_type(
            order_data.get('strategy_order_id', ''),
            order_data.get('strategy_order_action', '')
        )
        if trade_type == 'long_exit' or trade_type == 'short_exit':
            return True
        
        # Check max open positions
        if self.risk_metrics.open_position_count >= self.risk_parameters.portfolio.max_open_positions:
            logger.warning("Max open positions limit reached: %d/%d", 
                          self.risk_metrics.open_position_count, 
                          self.risk_parameters.portfolio.max_open_positions)
            return False
        
        # Check position size
        symbol = order_data.get('symbol')
        quantity = order_data.get('strategy_order_contracts')
        price = order_data.get('strategy_order_price')
        
        # If quantity or price is not provided, we can't check position size
        if not all([symbol, price]):
            logger.warning("Cannot check position size: missing symbol or price")
            return True
        
        # Calculate position size
        try:
            price = float(price)
            position_value = 0.0
            
            if quantity:
                quantity = float(quantity)
                position_value = price * quantity
            else:
                # Use default position sizing
                position_value = self.risk_metrics.current_equity * self.risk_parameters.portfolio.max_position_size_percent
            
            position_size_pct = position_value / self.risk_metrics.current_equity if self.risk_metrics.current_equity > 0 else 0
            
            # Check if position size exceeds max
            if position_size_pct > self.risk_parameters.portfolio.max_position_size_percent:
                logger.warning("Position size exceeds max: %.2f%% > %.2f%%", 
                              position_size_pct * 100, 
                              self.risk_parameters.portfolio.max_position_size_percent * 100)
                return False
            
            return True
        except Exception as e:
            logger.exception("Error checking position size: %s", str(e))
            # Allow the order if we can't check
            return True
    
    def _check_drawdown_limits(self) -> bool:
        """
        Check if current drawdown exceeds daily limits.
        
        Returns:
            Boolean indicating if drawdown is within limits
        """
        # Skip checks if portfolio protection is disabled
        if not self.risk_parameters.portfolio.enabled:
            return True
        
        # Calculate drawdown
        if self.risk_metrics.starting_equity <= 0:
            return True
        
        drawdown = (self.risk_metrics.starting_equity - self.risk_metrics.current_equity) / self.risk_metrics.starting_equity
        
        # Update risk metrics
        self.risk_metrics.current_drawdown_percent = max(0, drawdown)
        
        # Check if drawdown exceeds max
        if drawdown > self.risk_parameters.portfolio.max_daily_drawdown_percent:
            logger.warning("Daily drawdown exceeds max: %.2f%% > %.2f%%", 
                          drawdown * 100, 
                          self.risk_parameters.portfolio.max_daily_drawdown_percent * 100)
            return False
        
        return True
    
    def _update_risk_metrics(self):
        """Update risk metrics with current account information."""
        try:
            # Get account information
            account_info = self.broker_adapter.get_account_info()
            current_equity = float(account_info.get('equity', 0))
            
            # Get current time
            now = datetime.now()
            
            # Check if we need to reset daily tracking
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            metrics_time = datetime.fromtimestamp(self.risk_metrics.last_updated) if self.risk_metrics.last_updated else now
            
            # If we crossed a day boundary, reset starting equity
            if metrics_time.date() < now.date():
                self.risk_metrics.starting_equity = current_equity
            
            # Update current equity
            self.risk_metrics.current_equity = current_equity
            self.risk_metrics.last_updated = time.time()
            
            # Update position information
            positions = self.broker_adapter.get_positions()
            self.risk_metrics.open_position_count = len(positions)
            
            # Update position sizes
            position_sizes = []
            total_exposure = 0.0
            
            for position in positions:
                market_value = float(position.get('market_value', 0))
                position_size_pct = market_value / current_equity if current_equity > 0 else 0
                position_sizes.append(position_size_pct)
                total_exposure += position_size_pct
            
            self.risk_metrics.position_sizes = position_sizes
            self.risk_metrics.total_exposure_percent = total_exposure
            
            logger.debug("Risk metrics updated. Equity: %.2f, Positions: %d", 
                         current_equity, self.risk_metrics.open_position_count)
        except Exception as e:
            logger.exception("Error updating risk metrics: %s", str(e))
    
    def _get_risk_metrics_dict(self) -> Dict[str, Any]:
        """
        Convert risk metrics to a dictionary for JSON serialization.
        
        Returns:
            Risk metrics as a dictionary
        """
        return {
            'current_equity': self.risk_metrics.current_equity,
            'starting_equity': self.risk_metrics.starting_equity,
            'current_drawdown_percent': self.risk_metrics.current_drawdown_percent,
            'open_position_count': self.risk_metrics.open_position_count,
            'total_exposure_percent': self.risk_metrics.total_exposure_percent,
            'position_sizes': self.risk_metrics.position_sizes,
            'last_updated': self.risk_metrics.last_updated
        }
    
    def _get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Current price
        """
        try:
            ticker_data = self.broker_adapter.get_ticker(symbol)
            return float(ticker_data.get('last_price', 0))
        except Exception as e:
            logger.exception("Error getting current price for %s: %s", symbol, str(e))
            return 0.0
    
    def _add_stop_loss_take_profit(
        self,
        symbol: str,
        entry_price: float,
        parent_order_id: str,
        sl_tp_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add stop loss and take profit orders for an entry.
        
        Args:
            symbol: The trading symbol
            entry_price: Entry price of the position
            parent_order_id: ID of the parent order
            sl_tp_params: Dictionary of SL/TP parameters
            
        Returns:
            Dictionary with SL/TP order information
        """
        logger.info("Adding SL/TP for %s at entry price %.2f", symbol, entry_price)
        
        # Extract parameters
        stop_loss_percent = sl_tp_params.get('stop_loss_percent', self.risk_parameters.sl_tp.stop_loss_percent)
        take_profit_percent = sl_tp_params.get('take_profit_percent', self.risk_parameters.sl_tp.take_profit_percent)
        use_fixed_price = sl_tp_params.get('use_fixed_price', self.risk_parameters.sl_tp.use_fixed_price)
        fixed_stop_loss_price = sl_tp_params.get('fixed_stop_loss_price')
        fixed_take_profit_price = sl_tp_params.get('fixed_take_profit_price')
        use_fill_price = sl_tp_params.get('use_fill_price_for_sl_tp', self.risk_parameters.sl_tp.use_fill_price_for_sl_tp)
        
        # Get the position to determine side and quantity
        try:
            position = self.broker_adapter.get_position(symbol)
            
            if not position:
                logger.warning("No position found for %s, cannot add SL/TP", symbol)
                return {
                    'status': 'error',
                    'message': f'No position found for {symbol}',
                    'orders': []
                }
            
            # Get position details
            position_qty = float(position.get('qty', 0))
            position_side = 'long' if position_qty > 0 else 'short'
            avg_entry_price = float(position.get('avg_entry_price', entry_price))
            
            # Use average fill price if required, otherwise use entry price
            base_price = avg_entry_price if use_fill_price else entry_price
            
            # Create unique client order IDs for tracking
            sl_client_id = f"{parent_order_id}-sl-{uuid.uuid4().hex[:8]}"
            tp_client_id = f"{parent_order_id}-tp-{uuid.uuid4().hex[:8]}"
            
            orders = []
            
            # Stop Loss Order
            if use_fixed_price and fixed_stop_loss_price:
                # Use fixed price
                sl_price = fixed_stop_loss_price
            else:
                # Calculate SL price based on percentage
                if position_side == 'long':
                    sl_price = base_price * (1 - stop_loss_percent)
                else:
                    sl_price = base_price * (1 + stop_loss_percent)
            
            sl_order = {
                'symbol': symbol,
                'qty': abs(position_qty),
                'side': 'sell' if position_side == 'long' else 'buy',
                'type': 'stop',
                'time_in_force': 'gtc',
                'stop_price': sl_price,
                'client_order_id': sl_client_id,
                'order_class': 'simple'
            }
            
            # Take Profit Order
            if use_fixed_price and fixed_take_profit_price:
                # Use fixed price
                tp_price = fixed_take_profit_price
            else:
                # Calculate TP price based on percentage
                if position_side == 'long':
                    tp_price = base_price * (1 + take_profit_percent)
                else:
                    tp_price = base_price * (1 - take_profit_percent)
            
            tp_order = {
                'symbol': symbol,
                'qty': abs(position_qty),
                'side': 'sell' if position_side == 'long' else 'buy',
                'type': 'limit',
                'time_in_force': 'gtc',
                'limit_price': tp_price,
                'client_order_id': tp_client_id,
                'order_class': 'simple'
            }
            
            # Submit the orders
            try:
                sl_result = self.broker_adapter.place_order(**sl_order)
                orders.append({
                    'type': 'stop_loss',
                    'order_id': sl_result.get('id'),
                    'price': sl_price,
                    'status': sl_result.get('status')
                })
                logger.info("Stop loss order placed for %s at %.2f", symbol, sl_price)
            except Exception as e:
                logger.exception("Error placing stop loss order: %s", str(e))
            
            try:
                tp_result = self.broker_adapter.place_order(**tp_order)
                orders.append({
                    'type': 'take_profit',
                    'order_id': tp_result.get('id'),
                    'price': tp_price,
                    'status': tp_result.get('status')
                })
                logger.info("Take profit order placed for %s at %.2f", symbol, tp_price)
            except Exception as e:
                logger.exception("Error placing take profit order: %s", str(e))
            
            return {
                'status': 'success',
                'message': 'Stop loss and take profit orders placed',
                'orders': orders
            }
            
        except Exception as e:
            logger.exception("Error adding SL/TP for %s: %s", symbol, str(e))
            return {
                'status': 'error',
                'message': f'Error adding SL/TP: {str(e)}',
                'orders': []
            }
    
    def cleanup_orphaned_orders(self) -> Dict[str, Any]:
        """
        Cleanup orphaned stop loss and take profit orders.
        
        Returns:
            Dictionary with cleanup results
        """
        # Skip cleanup if disabled
        if not self.risk_parameters.cleanup.enabled:
            return {
                'status': 'skipped',
                'message': 'Cleanup service is disabled',
                'orders_cancelled': 0
            }
        
        logger.info("Running orphaned order cleanup")
        
        try:
            # Get current positions
            positions = self.broker_adapter.get_positions()
            position_symbols = set(p.get('symbol') for p in positions)
            
            # Get all open orders
            orders = self.broker_adapter.get_orders()
            
            # Filter for potential SL/TP orders (those with -sl or -tp in client_order_id)
            sl_tp_orders = [o for o in orders if 
                           (('-sl' in o.get('client_order_id', '')) or 
                            ('-tp' in o.get('client_order_id', '')))]
            
            # Check for orphaned orders (no position exists)
            orphaned_orders = [o for o in sl_tp_orders if o.get('symbol') not in position_symbols]
            
            # Also check for aged orders
            if self.risk_parameters.cleanup.orphaned_order_age_hours > 0:
                now = datetime.now()
                for order in sl_tp_orders:
                    if order not in orphaned_orders:  # Skip already identified orphans
                        created_at = datetime.fromisoformat(order.get('created_at').replace('Z', '+00:00'))
                        age_hours = (now - created_at).total_seconds() / 3600
                        
                        if age_hours > self.risk_parameters.cleanup.orphaned_order_age_hours:
                            orphaned_orders.append(order)
            
            # Cancel orphaned orders
            cancelled_orders = []
            for order in orphaned_orders:
                try:
                    logger.info("Cancelling orphaned order: %s (%s)", 
                               order.get('id'), order.get('client_order_id'))
                    self.broker_adapter.cancel_order(order.get('id'))
                    cancelled_orders.append(order.get('id'))
                except Exception as e:
                    logger.exception("Error cancelling order %s: %s", order.get('id'), str(e))
            
            return {
                'status': 'success',
                'message': f'Cleaned up {len(cancelled_orders)} orphaned orders',
                'orders_cancelled': len(cancelled_orders),
                'order_ids': cancelled_orders
            }
            
        except Exception as e:
            logger.exception("Error during order cleanup: %s", str(e))
            return {
                'status': 'error',
                'message': f'Error during cleanup: {str(e)}',
                'orders_cancelled': 0
            }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics.
        
        Returns:
            Current risk metrics as a dictionary
        """
        # Update metrics before returning
        self._update_risk_metrics()
        return self._get_risk_metrics_dict() 