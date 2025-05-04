import time
import uuid
import json
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
import threading
import datetime
import random
import logging

from src.integration.adapters.broker_adapter import BrokerAdapter
from src.integration.utils.logger import IntegrationLogger

# Initialize RiskManager to None - will be imported later to avoid circular imports
RiskManager = None  # Define initially as None

# Import RiskManager safely to avoid circular imports
def _import_risk_manager():
    """Import RiskManager class only when needed to avoid circular imports."""
    global RiskManager
    if RiskManager is None:
        try:
            from src.backend.services.risk_manager import RiskManager as RM
            RiskManager = RM
        except ImportError:
            # This can happen in test environments or circular imports
            logger = logging.getLogger(__name__)
            logger.warning("Could not import RiskManager. This is expected in test environments.")
            # Create a dummy class for testing environments
            class DummyRiskManager:
                def __init__(self, *args, **kwargs):
                    pass
            RiskManager = DummyRiskManager
    return RiskManager

class PaperTradingAdapter(BrokerAdapter):
    """Paper Trading Adapter for simulating trades without using real brokers.
    
    This adapter simulates trade execution for testing purposes, especially
    useful for testing risk management features. It maintains an in-memory
    record of orders, positions, and account info.
    """
    
    # Order status constants
    STATUS_NEW = "new"
    STATUS_FILLED = "filled"
    STATUS_PARTIALLY_FILLED = "partially_filled" 
    STATUS_CANCELED = "canceled"
    STATUS_REJECTED = "rejected"
    
    # Order types
    ORDER_TYPE_MARKET = "market"
    ORDER_TYPE_LIMIT = "limit"
    ORDER_TYPE_STOP = "stop"
    ORDER_TYPE_STOP_LIMIT = "stop_limit"
    
    # Market conditions - random fill ranges
    PRICE_VOLATILITY = 0.005  # 0.5% price movement for simulating market conditions
    MARKET_ORDER_FILL_CHANCE = 0.95  # 95% chance of a market order filling immediately
    
    # Risk management simulation parameters
    RISK_SIMULATION_ENABLED = True  # Flag to enable/disable risk simulation
    SL_TP_TRIGGER_CHECK_INTERVAL = 1  # Check for SL/TP triggers every 1 second
    EXTREME_VOLATILITY_CHANCE = 0.01  # 1% chance of extreme price movement
    EXTREME_VOLATILITY_FACTOR = 3  # 3x the normal volatility for extreme movements
    
    def __init__(self, initial_balance: float = 100000.0, 
                logger: Optional[IntegrationLogger] = None,
                risk_manager: Optional[Any] = None,
                volatility: float = 0.005):
        """Initialize the Paper Trading adapter.
        
        Args:
            initial_balance: Starting account balance in USD
            logger: Optional integration logger instance
            risk_manager: Optional risk manager instance for integration
            volatility: Price volatility factor for market simulation
        """
        # Initialize logger first so we can log import issues
        self.logger = logger or IntegrationLogger()
        
        # Import RiskManager if not already imported
        rm_class = _import_risk_manager()
        
        # Initialize risk manager relationship
        self.risk_manager = risk_manager
        
        # Validate risk_manager type if provided and if RiskManager class is available
        if risk_manager is not None and rm_class is not None:
            # Check if it's either a RiskManager instance or a mock object (for testing)
            is_risk_manager = isinstance(risk_manager, rm_class)
            is_mock = hasattr(risk_manager, 'mock_calls')
            # Only warn if it's neither a RiskManager nor a mock
            if not (is_risk_manager or is_mock):
                self.logger.log_warning(
                    "paper_trading_risk_manager", 
                    "Provided risk_manager is not an instance of RiskManager or a mock. This may be intentional in tests."
                )
        
        self.authenticated = True  # Always authenticated in paper trading
        self.PRICE_VOLATILITY = volatility  # Allow configurable volatility
        
        # In-memory storage for simulation
        self.account = {
            "cash": Decimal(str(initial_balance)),
            "portfolio_value": Decimal(str(initial_balance)),
            "initial_balance": Decimal(str(initial_balance)),
            "equity": Decimal(str(initial_balance)),
            "buying_power": Decimal(str(initial_balance * 4)),  # 4x leverage
            "account_number": f"paper-{uuid.uuid4().hex[:8]}",
            "created_at": datetime.datetime.now().isoformat(),
            "status": "ACTIVE"
        }
        
        self.orders = {}  # client_order_id -> order_details
        self.positions = {}  # symbol -> position_details
        
        # Add linked orders tracking for bracket orders and risk management
        self.linked_orders = {}  # parent_order_id -> [child_order_ids]
        self.order_parents = {}  # child_order_id -> parent_order_id
        
        # Tracking for risk events
        self.risk_events = []
        
        # Mock current market prices
        self.market_prices = {}  # symbol -> current_price
        
        # Background thread for simulating market changes and processing orders
        self.keep_running = True
        self.market_thread = threading.Thread(target=self._simulate_market)
        self.market_thread.daemon = True
        self.market_thread.start()
        
        # Dedicated thread for stop-loss/take-profit monitoring
        self.sl_tp_thread = threading.Thread(target=self._monitor_stop_loss_take_profit)
        self.sl_tp_thread.daemon = True
        self.sl_tp_thread.start()
        
        self.logger.log_info("paper_trading_init", "Paper Trading adapter initialized with balance: ${:.2f}, volatility: {:.2f}%".format(
            initial_balance, self.PRICE_VOLATILITY * 100))

    def authenticate(self) -> bool:
        """Authenticate with the broker API.
        
        For paper trading, this is a no-op that always succeeds.
        
        Returns:
            bool: Always True for paper trading
        """
        return True
        
    def place_market_order(self, symbol: str, qty: float, side: str, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a market order.
        
        Args:
            symbol: The trading symbol (e.g., 'AAPL', 'BTC/USD')
            qty: Quantity to trade
            side: 'buy' or 'sell'
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and simulated response
        """
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
            
        # Get or generate current market price for the symbol
        current_price = self._get_current_price(symbol)
        
        # Create order
        order = {
            "id": str(uuid.uuid4()),
            "client_order_id": client_order_id,
            "symbol": symbol,
            "qty": Decimal(str(qty)),
            "side": side.lower(),
            "type": self.ORDER_TYPE_MARKET,
            "time_in_force": "gtc",
            "status": self.STATUS_NEW,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "submitted_at": datetime.datetime.now().isoformat(),
            "filled_qty": Decimal("0"),
            "filled_avg_price": None,
            "order_price": current_price,  # No limit price for market orders, but store current price
            "filled_at": None
        }
        
        # Store order
        self.orders[client_order_id] = order
        
        # Simulate immediate or delayed fill for market orders
        fill_chance = random.random()
        if fill_chance <= self.MARKET_ORDER_FILL_CHANCE:
            # Simulate immediate fill with slight price variation
            price_variation = random.uniform(-self.PRICE_VOLATILITY, self.PRICE_VOLATILITY)
            fill_price = current_price * (1 + price_variation)
            self._fill_order(client_order_id, Decimal(str(qty)), Decimal(str(fill_price)))
        
        self.logger.log_info("market_order_placed", f"Paper Trading: {side} {qty} {symbol} @ market, ID: {client_order_id}")
        return self.orders[client_order_id]

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
            Dict containing the order details and simulated response
        """
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
            
        # Create order
        order = {
            "id": str(uuid.uuid4()),
            "client_order_id": client_order_id,
            "symbol": symbol,
            "qty": Decimal(str(qty)),
            "side": side.lower(),
            "type": self.ORDER_TYPE_LIMIT,
            "time_in_force": "gtc",
            "status": self.STATUS_NEW,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "submitted_at": datetime.datetime.now().isoformat(),
            "filled_qty": Decimal("0"),
            "filled_avg_price": None,
            "limit_price": Decimal(str(limit_price)),
            "filled_at": None
        }
        
        # Store order
        self.orders[client_order_id] = order
        
        self.logger.log_info("limit_order_placed", f"Paper Trading: {side} {qty} {symbol} @ limit {limit_price}, ID: {client_order_id}")
        return self.orders[client_order_id]

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
            Dict containing the order details and simulated response
        """
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
            
        # Create order
        order = {
            "id": str(uuid.uuid4()),
            "client_order_id": client_order_id,
            "symbol": symbol,
            "qty": Decimal(str(qty)),
            "side": side.lower(),
            "type": self.ORDER_TYPE_STOP,
            "time_in_force": "gtc",
            "status": self.STATUS_NEW,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "submitted_at": datetime.datetime.now().isoformat(),
            "filled_qty": Decimal("0"),
            "filled_avg_price": None,
            "stop_price": Decimal(str(stop_price)),
            "filled_at": None
        }
        
        # Store order
        self.orders[client_order_id] = order
        
        self.logger.log_info("stop_order_placed", f"Paper Trading: {side} {qty} {symbol} @ stop {stop_price}, ID: {client_order_id}")
        return self.orders[client_order_id]

    def place_bracket_order(self, symbol: str, qty: float, side: str, 
                           entry_price: Optional[float] = None,
                           take_profit_price: Optional[float] = None, 
                           stop_loss_price: Optional[float] = None,
                           client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a bracket order with optional entry, stop-loss and take-profit prices.
        
        A bracket order is a set of orders that includes an entry order, a profit target,
        and a stop loss. This is particularly useful for risk management.
        
        Args:
            symbol: The trading symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            entry_price: Optional limit price for the entry order (if None, uses market order)
            take_profit_price: Optional price at which to take profit
            stop_loss_price: Optional price at which to stop loss
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and simulated response
        """
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
        
        # Get current price for market orders
        current_price = self._get_current_price(symbol)
        
        # Create main order (entry)
        main_order = None
        if entry_price is not None:
            main_order = self.place_limit_order(
                symbol=symbol,
                qty=qty, 
                side=side, 
                limit_price=entry_price,
                client_order_id=client_order_id
            )
        else:
            main_order = self.place_market_order(
                symbol=symbol,
                qty=qty,
                side=side,
                client_order_id=client_order_id
            )
        
        # Initialize linked orders list
        self.linked_orders[client_order_id] = []
        
        # Create take profit order if specified
        tp_order = None
        if take_profit_price is not None:
            tp_side = "sell" if side == "buy" else "buy"
            tp_order_id = f"{client_order_id}-tp"
            
            tp_order = self.place_limit_order(
                symbol=symbol,
                qty=qty,
                side=tp_side,
                limit_price=take_profit_price,
                client_order_id=tp_order_id
            )
            
            # Link the take profit order to main order
            self.linked_orders[client_order_id].append(tp_order_id)
            self.order_parents[tp_order_id] = client_order_id
            
            # Set contingent status - will only be active if main order fills
            tp_order["status"] = self.STATUS_NEW
            tp_order["is_contingent"] = True
            tp_order["contingent_on"] = client_order_id
            self.orders[tp_order_id] = tp_order
        
        # Create stop loss order if specified
        sl_order = None
        if stop_loss_price is not None:
            sl_side = "sell" if side == "buy" else "buy"
            sl_order_id = f"{client_order_id}-sl"
            
            sl_order = self.place_stop_order(
                symbol=symbol,
                qty=qty,
                side=sl_side,
                stop_price=stop_loss_price,
                client_order_id=sl_order_id
            )
            
            # Link the stop loss order to main order
            self.linked_orders[client_order_id].append(sl_order_id)
            self.order_parents[sl_order_id] = client_order_id
            
            # Set contingent status - will only be active if main order fills
            sl_order["status"] = self.STATUS_NEW
            sl_order["is_contingent"] = True
            sl_order["contingent_on"] = client_order_id
            self.orders[sl_order_id] = sl_order
        
        # Log bracket order creation
        log_message = f"Paper Trading: {side} {qty} {symbol} bracket order"
        if entry_price is not None:
            log_message += f" @ limit {entry_price}"
        else:
            log_message += f" @ market {current_price}"
            
        if take_profit_price is not None:
            log_message += f", TP: {take_profit_price}"
        if stop_loss_price is not None:
            log_message += f", SL: {stop_loss_price}"
            
        self.logger.log_info("bracket_order_placed", log_message)
        
        # Return main order info with TP/SL details
        main_order["bracket_order"] = True
        main_order["take_profit_order_id"] = tp_order["client_order_id"] if tp_order else None
        main_order["stop_loss_order_id"] = sl_order["client_order_id"] if sl_order else None
        
        return main_order

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an open order.
        
        Args:
            order_id: The ID of the order to cancel
            
        Returns:
            Dict containing the order details after cancellation
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            
            # Only cancel if not already filled or canceled
            if order["status"] not in [self.STATUS_FILLED, self.STATUS_CANCELED]:
                order["status"] = self.STATUS_CANCELED
                order["updated_at"] = datetime.datetime.now().isoformat()
                self.logger.log_info("order_canceled", f"Paper Trading: Canceled order {order_id}")
            
            return order
        
        else:
            # Order not found
            error_msg = f"Order {order_id} not found"
            self.logger.log_error("order_not_found", error_msg)
            return {
                "error": "order_not_found",
                "message": error_msg
            }

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the current status of an order.
        
        Args:
            order_id: The ID of the order to check
            
        Returns:
            Dict containing order details and status
        """
        if order_id in self.orders:
            return self.orders[order_id]
        
        # Order not found
        error_msg = f"Order {order_id} not found"
        self.logger.log_error("order_not_found", error_msg)
        return {
            "error": "order_not_found",
            "message": error_msg
        }

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for a specific symbol.
        
        Args:
            symbol: The trading symbol to check
            
        Returns:
            Dict containing position details or None if no position exists
        """
        # Normalize symbol
        symbol = symbol.upper()
        
        if symbol in self.positions:
            return self.positions[symbol]
        
        return None

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all current positions.
        
        Returns:
            List of position details
        """
        return list(self.positions.values())

    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position for a specific symbol.
        
        Args:
            symbol: The trading symbol to close position for
            
        Returns:
            Dict containing details of the closing transaction
        """
        # Normalize symbol
        symbol = symbol.upper()
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            # Generate a market order to close the position
            side = "sell" if position["side"] == "long" else "buy"
            qty = abs(float(position["qty"]))
            client_order_id = self._generate_client_order_id() + "-close"
            
            # Place closing order
            closing_order = self.place_market_order(symbol, qty, side, client_order_id)
            
            # Update closing order to indicate it's a position close
            closing_order["position_close"] = True
            
            # Remove position if market order filled immediately
            if closing_order["status"] == self.STATUS_FILLED:
                # Calculate P&L
                entry_price = float(position["avg_entry_price"])
                exit_price = float(closing_order["filled_avg_price"])
                qty = float(position["qty"])
                
                pnl = (exit_price - entry_price) * qty if position["side"] == "long" else (entry_price - exit_price) * qty
                
                # Update account equity
                self.account["equity"] += Decimal(str(pnl))
                self.account["portfolio_value"] = self.account["cash"] + self.account["equity"]
                
                # Remove position
                closed_position = self.positions.pop(symbol)
                self.logger.log_info("position_closed", f"Paper Trading: Closed {closed_position['side']} position in {symbol} with P&L: ${pnl:.2f}")
                
                return {
                    "symbol": symbol,
                    "side": closed_position["side"],
                    "qty": closed_position["qty"],
                    "avg_entry_price": closed_position["avg_entry_price"],
                    "exit_price": closing_order["filled_avg_price"],
                    "pnl": str(pnl),
                    "closed_at": datetime.datetime.now().isoformat()
                }
            
            return closing_order
        
        # No position to close
        error_msg = f"No position found for {symbol}"
        self.logger.log_error("position_not_found", error_msg)
        return {
            "error": "position_not_found",
            "message": error_msg
        }

    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information.
        
        Returns:
            Dict containing account details including cash balance, equity, buying power
        """
        # Update portfolio value - recalculate based on current market prices
        portfolio_value = self.account["cash"]
        unrealized_pl = Decimal("0")
        
        # Add current position values
        for symbol, position in self.positions.items():
            current_price = self._get_current_price(symbol)
            position_value = Decimal(str(position["qty"])) * current_price
            
            # Calculate unrealized P&L
            entry_value = Decimal(str(position["qty"])) * Decimal(str(position["avg_entry_price"]))
            if position["side"] == "long":
                position_pl = position_value - entry_value
            else:
                position_pl = entry_value - position_value
            
            unrealized_pl += position_pl
            portfolio_value += position_value
        
        # Update account info
        self.account["portfolio_value"] = portfolio_value
        self.account["equity"] = self.account["cash"] + unrealized_pl
        self.account["buying_power"] = self.account["cash"] * Decimal("4")  # 4x leverage
        self.account["updated_at"] = datetime.datetime.now().isoformat()
        self.account["unrealized_pl"] = unrealized_pl
        
        return self.account

    def place_notional_order(self, symbol: str, notional_amount: float, side: str, 
                           order_type: str = "market", 
                           price: Optional[float] = None,
                           client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place an order by notional (dollar) amount rather than quantity.
        
        Args:
            symbol: The trading symbol (e.g., 'AAPL', 'BTC/USD')
            notional_amount: Dollar amount to trade
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', or 'stop'
            price: Price for limit or stop orders
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and simulated response
        """
        # Get current price to calculate quantity
        current_price = self._get_current_price(symbol)
        
        # Calculate quantity based on notional amount
        qty = notional_amount / float(current_price)
        
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id() + "-notional"
        
        # Place order based on order type
        if order_type.lower() == "market":
            order = self.place_market_order(symbol, qty, side, client_order_id)
        elif order_type.lower() == "limit" and price:
            order = self.place_limit_order(symbol, qty, side, price, client_order_id)
        elif order_type.lower() == "stop" and price:
            order = self.place_stop_order(symbol, qty, side, price, client_order_id)
        else:
            error_msg = f"Invalid order type or missing price for {order_type}"
            self.logger.log_error("invalid_order_params", error_msg)
            return {
                "error": "invalid_order_params",
                "message": error_msg
            }
        
        # Mark as notional order
        order["notional"] = True
        order["notional_amount"] = notional_amount
        
        self.logger.log_info("notional_order_placed", f"Paper Trading: {side} ${notional_amount} of {symbol} @ {order_type}, ID: {client_order_id}")
        
        return order
    
    def shutdown(self):
        """Shutdown the paper trading adapter, stopping market simulation thread."""
        self.keep_running = False
        if self.market_thread.is_alive():
            self.market_thread.join(timeout=2.0)
        self.logger.log_info("paper_trading_shutdown", "Paper Trading adapter shutdown")

    def _fill_order(self, order_id: str, qty: Decimal, price: Decimal) -> bool:
        """Fill an order with the given quantity and price.
        
        Args:
            order_id: The client order ID
            qty: Quantity to fill
            price: Fill price
            
        Returns:
            Boolean indicating success
        """
        if order_id not in self.orders:
            self.logger.log_error("fill_order_error", f"Order ID {order_id} not found")
            return False
        
        order = self.orders[order_id]
        
        # Skip if order is already filled or canceled
        if order["status"] in [self.STATUS_FILLED, self.STATUS_CANCELED, self.STATUS_REJECTED]:
            return False
            
        # Handle contingent orders - only process if parent is filled
        if order.get("is_contingent", False):
            parent_id = order.get("contingent_on")
            parent_order = self.orders.get(parent_id)
            
            if not parent_order or parent_order["status"] != self.STATUS_FILLED:
                return False
        
        # Calculate fill value
        fill_value = qty * price
        
        # Check if account has sufficient funds for buys
        if order["side"] == "buy":
            if self.account["cash"] < fill_value:
                self.logger.log_error("fill_order_error", f"Insufficient funds to fill buy order {order_id}")
                order["status"] = self.STATUS_REJECTED
                order["reject_reason"] = "Insufficient funds"
                return False
        
        # Update fill information
        if order["filled_qty"] == Decimal("0"):
            # First fill
            order["filled_qty"] = qty
            order["filled_avg_price"] = price
            order["filled_at"] = datetime.datetime.now().isoformat()
        else:
            # Additional partial fill - update average price
            total_qty = order["filled_qty"] + qty
            avg_price = ((order["filled_qty"] * order["filled_avg_price"]) + (qty * price)) / total_qty
            order["filled_qty"] = total_qty
            order["filled_avg_price"] = avg_price
            order["filled_at"] = datetime.datetime.now().isoformat()
        
        # Update order status
        if order["filled_qty"] >= order["qty"]:
            order["status"] = self.STATUS_FILLED
            order["filled_qty"] = order["qty"]  # Cap fill at ordered quantity
        else:
            order["status"] = self.STATUS_PARTIALLY_FILLED
            
        # Update position
        self._update_position(order)
        
        # Apply trading fees (0.1%)
        fee = fill_value * Decimal("0.001")
        self.account["cash"] -= fee
        
        # Log fill
        self.logger.log_info("order_filled", 
            f"Paper Trading: Order {order_id} {order['status']} at {price} ({order['filled_qty']}/{order['qty']}), fees: ${fee:.2f}")
        
        # Handle linked orders for bracket orders and risk management
        if order["status"] == self.STATUS_FILLED and order_id in self.linked_orders:
            # Activate linked orders (they were contingent on this order)
            for linked_order_id in self.linked_orders[order_id]:
                linked_order = self.orders.get(linked_order_id)
                if linked_order and linked_order["status"] == self.STATUS_NEW:
                    linked_order["is_contingent"] = False
                    self.logger.log_info("linked_order_activated", 
                        f"Paper Trading: Activating linked order {linked_order_id} after fill of {order_id}")
        
        # When SL or TP is filled, cancel other linked orders
        if order["status"] == self.STATUS_FILLED and order_id in self.order_parents:
            parent_id = self.order_parents[order_id]
            # Cancel sibling orders
            for sibling_id in self.linked_orders.get(parent_id, []):
                if sibling_id != order_id and sibling_id in self.orders:
                    sibling = self.orders[sibling_id]
                    if sibling["status"] not in [self.STATUS_FILLED, self.STATUS_CANCELED, self.STATUS_REJECTED]:
                        sibling["status"] = self.STATUS_CANCELED
                        self.logger.log_info("linked_order_canceled", 
                            f"Paper Trading: Canceling linked order {sibling_id} after fill of {order_id}")
            
            # Record risk event
            if "-sl" in order_id:
                self._record_risk_event("stop_loss_triggered", {
                    "order_id": order_id,
                    "parent_id": parent_id,
                    "symbol": order["symbol"],
                    "price": float(price),
                    "qty": float(order["qty"]),
                    "side": order["side"],
                    "timestamp": datetime.datetime.now().isoformat()
                })
            elif "-tp" in order_id:
                self._record_risk_event("take_profit_triggered", {
                    "order_id": order_id,
                    "parent_id": parent_id,
                    "symbol": order["symbol"],
                    "price": float(price),
                    "qty": float(order["qty"]),
                    "side": order["side"],
                    "timestamp": datetime.datetime.now().isoformat()
                })
        
        # Notify risk manager of order fill if integrated
        if self.risk_manager and self.RISK_SIMULATION_ENABLED:
            try:
                position = self.get_position(order["symbol"])
                self._notify_risk_manager(order, position)
            except Exception as e:
                self.logger.log_error("risk_manager_notification_error", f"Error notifying risk manager: {str(e)}")
        
        return True

    def _update_position(self, order: Dict[str, Any]) -> None:
        """Update positions based on filled order.
        
        Args:
            order: Order dictionary with fill details
        """
        if order["status"] not in [self.STATUS_FILLED, self.STATUS_PARTIALLY_FILLED]:
            return
        
        symbol = order["symbol"]
        fill_qty = order["filled_qty"]
        price = order["filled_avg_price"]
        side = order["side"]
        
        # Adjust quantity based on side
        position_qty = fill_qty if side == "buy" else -fill_qty
        
        # Update cash
        trade_value = fill_qty * price
        fee = trade_value * Decimal("0.001")  # Simulate 0.1% fee
        if side == "buy":
            self.account["cash"] -= (trade_value + fee)
        else:
            self.account["cash"] += (trade_value - fee)
        
        # Update position
        if symbol in self.positions:
            current_position = self.positions[symbol]
            current_qty = Decimal(str(current_position["qty"]))
            new_qty = current_qty + position_qty
            
            # If new position is zero or flips direction, close old position
            if new_qty == 0:
                # Position is closed
                self.positions.pop(symbol)
                return
            elif (current_qty > 0 and new_qty < 0) or (current_qty < 0 and new_qty > 0):
                # Position flipped - close old, open new
                self.positions.pop(symbol)
                
                # Create new position with the remainder
                position_side = "long" if new_qty > 0 else "short"
                self.positions[symbol] = {
                    "symbol": symbol,
                    "qty": str(abs(new_qty)),
                    "side": position_side,
                    "avg_entry_price": str(price),
                    "market_value": str(abs(new_qty) * price),
                    "cost_basis": str(abs(new_qty) * price),
                    "unrealized_pl": "0",
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat()
                }
                return
            
            # Update existing position
            current_cost = current_qty * Decimal(str(current_position["avg_entry_price"]))
            
            if current_qty > 0 and side == "buy":
                # Adding to long position
                new_cost = current_cost + (position_qty * price)
                new_avg_price = new_cost / new_qty
                current_position["avg_entry_price"] = str(new_avg_price)
            elif current_qty < 0 and side == "sell":
                # Adding to short position
                new_cost = current_cost - (position_qty * price)
                new_avg_price = new_cost / abs(new_qty)
                current_position["avg_entry_price"] = str(new_avg_price)
            
            current_position["qty"] = str(abs(new_qty))
            current_position["side"] = "long" if new_qty > 0 else "short"
            current_position["market_value"] = str(abs(new_qty) * price)
            current_position["updated_at"] = datetime.datetime.now().isoformat()
            
        else:
            # Create new position
            position_side = "long" if position_qty > 0 else "short"
            self.positions[symbol] = {
                "symbol": symbol,
                "qty": str(abs(position_qty)),
                "side": position_side,
                "avg_entry_price": str(price),
                "market_value": str(abs(position_qty) * price),
                "cost_basis": str(abs(position_qty) * price),
                "unrealized_pl": "0",
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }

    def _get_current_price(self, symbol: str) -> Decimal:
        """Get current market price for a symbol.
        
        If the price isn't available, generates a random initial price.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Decimal: Current simulated market price
        """
        symbol = symbol.upper()
        
        if symbol not in self.market_prices:
            # Generate initial price based on symbol
            # This is arbitrary but creates somewhat realistic prices
            if "BTC" in symbol:
                base_price = 45000.00
            elif "ETH" in symbol:
                base_price = 3000.00
            elif "USD" in symbol or "EUR" in symbol:
                base_price = 1.00
            else:
                # Generate random stock price between $10 and $1000
                base_price = random.uniform(10.0, 1000.0)
            
            # Add random variation
            variation = random.uniform(-0.05, 0.05)  # ±5%
            price = Decimal(str(base_price * (1 + variation)))
            
            # Set initial price
            self.market_prices[symbol] = price
        
        return self.market_prices[symbol]

    def _simulate_market(self) -> None:
        """Simulate market behavior in a background thread.
        
        This method runs in a separate thread and continuously:
        1. Updates market prices with random movements
        2. Checks if limit orders should be filled
        3. Checks if stop orders should be triggered
        4. Updates account information and position values
        """
        while self.keep_running:
            try:
                # Update prices for all symbols with positions or orders
                symbols = set()
                
                # Add symbols from positions
                for symbol in self.positions.keys():
                    symbols.add(symbol)
                    
                # Add symbols from orders
                for order in self.orders.values():
                    symbols.add(order["symbol"])
                
                # Ensure we have at least some starter symbols for testing
                starter_symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "BTC/USD", "ETH/USD"]
                for symbol in starter_symbols:
                    symbols.add(symbol)
                
                # Update each price
                for symbol in symbols:
                    # Get current price or initialize if not exists
                    if symbol not in self.market_prices:
                        # Initialize with a reasonable starter price
                        if symbol == "BTC/USD":
                            self.market_prices[symbol] = Decimal("40000")
                        elif symbol == "ETH/USD":
                            self.market_prices[symbol] = Decimal("2000")
                        else:
                            self.market_prices[symbol] = Decimal(str(random.uniform(50, 500)))
                    
                    # Simulate price movement
                    # Check for extreme volatility event (for risk management testing)
                    is_extreme = self.RISK_SIMULATION_ENABLED and random.random() < self.EXTREME_VOLATILITY_CHANCE
                    
                    volatility = self.PRICE_VOLATILITY
                    if is_extreme:
                        volatility *= self.EXTREME_VOLATILITY_FACTOR
                        self.logger.log_info("extreme_volatility", f"Simulating extreme price move for {symbol}")
                    
                    # Calculate price change
                    price_change = random.uniform(-volatility, volatility)
                    current_price = self.market_prices[symbol]
                    new_price = current_price * (Decimal("1") + Decimal(str(price_change)))
                    
                    # Ensure price doesn't go below 0.01
                    new_price = max(new_price, Decimal("0.01"))
                    
                    # Update price
                    self.market_prices[symbol] = new_price
                    
                    # Process limit and stop orders for this symbol
                    self._process_pending_orders(symbol, new_price)
                    
                # Update position values and account equity
                self._update_account_values()
                
                # Sleep to control simulation speed
                time.sleep(1)
                
            except Exception as e:
                self.logger.log_error("market_simulation_error", f"Error in market simulation: {str(e)}")
                time.sleep(1)  # Sleep on error to avoid tight loop

    def _monitor_stop_loss_take_profit(self) -> None:
        """Dedicated thread for monitoring stop-loss and take-profit orders.
        
        This provides faster and more reliable triggering of SL/TP orders
        compared to the general market simulation.
        """
        while self.keep_running:
            try:
                # Skip if risk simulation is disabled
                if not self.RISK_SIMULATION_ENABLED:
                    time.sleep(self.SL_TP_TRIGGER_CHECK_INTERVAL)
                    continue
                
                # Get all active orders
                active_orders = {order_id: order for order_id, order in self.orders.items() 
                               if order["status"] not in [self.STATUS_FILLED, self.STATUS_CANCELED, self.STATUS_REJECTED]}
                
                # Process each symbol with active orders
                processed_symbols = set()
                
                for order_id, order in active_orders.items():
                    symbol = order["symbol"]
                    
                    # Skip if we already processed this symbol
                    if symbol in processed_symbols:
                        continue
                    
                    # Get current price
                    current_price = self._get_current_price(symbol)
                    
                    # Process all active stop and take-profit orders for this symbol
                    for check_id, check_order in active_orders.items():
                        if check_order["symbol"] != symbol:
                            continue
                            
                        # Skip if order is contingent and parent not filled
                        if check_order.get("is_contingent", False):
                            parent_id = check_order.get("contingent_on")
                            parent_order = self.orders.get(parent_id)
                            if not parent_order or parent_order["status"] != self.STATUS_FILLED:
                                continue
                        
                        # Check stop orders - fill if price crosses stop price
                        if check_order["type"] == self.ORDER_TYPE_STOP:
                            stop_price = check_order.get("stop_price", None)
                            if stop_price is None:
                                continue
                                
                            if check_order["side"] == "sell" and current_price <= stop_price:
                                # Sell stop triggered (price dropped below stop)
                                self._fill_order(check_id, check_order["qty"], current_price)
                                
                            elif check_order["side"] == "buy" and current_price >= stop_price:
                                # Buy stop triggered (price rose above stop)
                                self._fill_order(check_id, check_order["qty"], current_price)
                        
                        # Check limit orders for take-profit
                        elif check_order["type"] == self.ORDER_TYPE_LIMIT:
                            limit_price = check_order.get("limit_price", None)
                            if limit_price is None:
                                continue
                                
                            # Check if it's a take-profit (based on naming or parent order side)
                            is_tp = False
                            if "-tp" in check_id:
                                is_tp = True
                            elif check_id in self.order_parents:
                                parent_id = self.order_parents[check_id]
                                parent_order = self.orders.get(parent_id)
                                if parent_order and parent_order["side"] != check_order["side"]:
                                    is_tp = True
                            
                            if is_tp:
                                if check_order["side"] == "sell" and current_price >= limit_price:
                                    # Sell limit triggered (price rose above limit)
                                    self._fill_order(check_id, check_order["qty"], limit_price)
                                    
                                elif check_order["side"] == "buy" and current_price <= limit_price:
                                    # Buy limit triggered (price dropped below limit)
                                    self._fill_order(check_id, check_order["qty"], limit_price)
                    
                    # Mark symbol as processed
                    processed_symbols.add(symbol)
                
                # Sleep to control check frequency
                time.sleep(self.SL_TP_TRIGGER_CHECK_INTERVAL)
                
            except Exception as e:
                self.logger.log_error("sl_tp_monitor_error", f"Error in SL/TP monitoring: {str(e)}")
                time.sleep(1)  # Sleep on error to avoid tight loop

    def _notify_risk_manager(self, order: Dict[str, Any], position: Optional[Dict[str, Any]]) -> None:
        """
        Notify the risk manager about executed orders and position changes.
        
        Args:
            order: The order that was executed
            position: The position that was affected (if any)
        """
        if self.risk_manager is None:
            return
            
        try:
            # Check if we have a real RiskManager or a mock object
            if hasattr(self.risk_manager, 'on_order_filled'):
                self.risk_manager.on_order_filled(order, position)
            # For mock objects, we'll record the call differently
            elif hasattr(self.risk_manager, 'mock_calls'):
                # For unittest.mock objects, we need to call a method to record it
                self.risk_manager.on_order_filled(order, position)
            else:
                # This might be a test dummy object that doesn't implement these methods
                pass
                
            # Record this event
            self._record_risk_event(
                "order_notification", 
                {
                    "order_id": order.get("client_order_id", "unknown"),
                    "symbol": order.get("symbol", "unknown"),
                    "side": order.get("side", "unknown"),
                    "status": order.get("status", "unknown"),
                    "qty": str(order.get("qty", 0)),
                    "position_updated": position is not None
                }
            )
        except Exception as e:
            self.logger.log_error(
                "risk_notification_error",
                f"Error notifying risk manager: {str(e)}"
            )

    def _record_risk_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Record a risk event for analysis.
        
        Args:
            event_type: Type of risk event (e.g., 'stop_loss_triggered')
            event_data: Data associated with the event
        """
        event = {
            "type": event_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": event_data
        }
        
        self.risk_events.append(event)
        self.logger.log_info("risk_event_recorded", f"Recorded risk event: {event_type}")

    def get_risk_events(self) -> List[Dict[str, Any]]:
        """Get all recorded risk events.
        
        Returns:
            List of risk events that have occurred
        """
        return self.risk_events.copy()

    def set_price_simulation_parameters(self, 
                                      volatility: float = 0.005, 
                                      extreme_volatility_chance: float = 0.01,
                                      extreme_volatility_factor: float = 3) -> None:
        """Set price simulation parameters for testing risk management.
        
        Args:
            volatility: Base price volatility (default: 0.5%)
            extreme_volatility_chance: Probability of extreme price movement (default: 1%)
            extreme_volatility_factor: Multiplier for extreme volatility (default: 3x)
        """
        self.PRICE_VOLATILITY = volatility
        self.EXTREME_VOLATILITY_CHANCE = extreme_volatility_chance
        self.EXTREME_VOLATILITY_FACTOR = extreme_volatility_factor
        
        self.logger.log_info("simulation_params_updated", 
            f"Updated simulation parameters: volatility={volatility}, " + 
            f"extreme_chance={extreme_volatility_chance}, " +
            f"extreme_factor={extreme_volatility_factor}")

    def get_risk_simulation_status(self) -> Dict[str, Any]:
        """Get current risk simulation status and parameters.
        
        Returns:
            Dict containing risk simulation configuration
        """
        return {
            "enabled": self.RISK_SIMULATION_ENABLED,
            "volatility": self.PRICE_VOLATILITY,
            "extreme_volatility_chance": self.EXTREME_VOLATILITY_CHANCE,
            "extreme_volatility_factor": self.EXTREME_VOLATILITY_FACTOR,
            "risk_manager_connected": self.risk_manager is not None,
            "sl_tp_check_interval": self.SL_TP_TRIGGER_CHECK_INTERVAL,
            "risk_events_count": len(self.risk_events)
        }

    def toggle_risk_simulation(self, enabled: bool = True) -> None:
        """Enable or disable risk simulation features.
        
        Args:
            enabled: Whether risk simulation should be enabled
        """
        self.RISK_SIMULATION_ENABLED = enabled
        self.logger.log_info("risk_simulation_toggled", 
            f"Risk simulation {'enabled' if enabled else 'disabled'}")

    def _generate_client_order_id(self) -> str:
        """Generate a unique client order ID.
        
        Returns:
            str: Unique order ID
        """
        return f"paper-{uuid.uuid4().hex}" 