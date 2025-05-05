import time
import uuid
import json
from typing import Dict, Any, Optional, List
from decimal import Decimal
import threading
import datetime
import random

from src.integration.adapters.broker_adapter import BrokerAdapter
from src.integration.utils.logger import IntegrationLogger

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
    
    def __init__(self, initial_balance: float = 100000.0, logger: Optional[IntegrationLogger] = None):
        """Initialize the Paper Trading adapter.
        
        Args:
            initial_balance: Starting account balance in USD
            logger: Optional integration logger instance
        """
        self.logger = logger or IntegrationLogger()
        self.authenticated = True  # Always authenticated in paper trading
        
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
        
        # Mock current market prices
        self.market_prices = {}  # symbol -> current_price
        
        # Background thread for simulating market changes and processing orders
        self.keep_running = True
        self.market_thread = threading.Thread(target=self._simulate_market)
        self.market_thread.daemon = True
        self.market_thread.start()
        
        self.logger.log_info("paper_trading_init", "Paper Trading adapter initialized with balance: ${:.2f}".format(initial_balance))

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
        """Place a bracket order with entry, take-profit, and stop-loss.
        
        Args:
            symbol: The trading symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            entry_price: Optional entry price (limit price for the main order)
            take_profit_price: Optional price for take-profit order
            stop_loss_price: Optional price for stop-loss order
            client_order_id: Optional client-defined order ID for tracking
            
        Returns:
            Dict containing the order details and simulated response
        """
        # Generate client_order_id if not provided
        if not client_order_id:
            client_order_id = self._generate_client_order_id()
            
        # Generate related IDs for take-profit and stop-loss orders
        tp_order_id = f"{client_order_id}-tp"
        sl_order_id = f"{client_order_id}-sl"
        
        # Create main order (entry)
        if entry_price:
            # Limit order
            main_order = self.place_limit_order(symbol, qty, side, entry_price, client_order_id)
            main_order["bracket"] = True
        else:
            # Market order
            main_order = self.place_market_order(symbol, qty, side, client_order_id)
            main_order["bracket"] = True
        
        # Create take-profit order if price provided
        if take_profit_price:
            tp_side = "sell" if side.lower() == "buy" else "buy"
            tp_order = self.place_limit_order(symbol, qty, tp_side, take_profit_price, tp_order_id)
            tp_order["parent_order_id"] = client_order_id
            tp_order["bracket_type"] = "take_profit"
            
        # Create stop-loss order if price provided
        if stop_loss_price:
            sl_side = "sell" if side.lower() == "buy" else "buy"
            sl_order = self.place_stop_order(symbol, qty, sl_side, stop_loss_price, sl_order_id)
            sl_order["parent_order_id"] = client_order_id
            sl_order["bracket_type"] = "stop_loss"
        
        # Only activate TP/SL when main order is filled
        if main_order["status"] != self.STATUS_FILLED:
            if take_profit_price:
                self.orders[tp_order_id]["status"] = "held"
            if stop_loss_price:
                self.orders[sl_order_id]["status"] = "held"
        
        self.logger.log_info("bracket_order_placed", 
                           f"Paper Trading: Bracket order - {side} {qty} {symbol} with TP:{take_profit_price}, SL:{stop_loss_price}, ID: {client_order_id}")
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
        """Internally fill an order (fully or partially).
        
        Args:
            order_id: The order ID to fill
            qty: Quantity to fill
            price: Price at which to fill
            
        Returns:
            bool: True if fill was successful, False otherwise
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        # Skip already filled or canceled orders
        if order["status"] in [self.STATUS_FILLED, self.STATUS_CANCELED]:
            return False
        
        # Calculate remaining quantity
        remaining_qty = order["qty"] - order["filled_qty"]
        fill_qty = min(qty, remaining_qty)
        
        # Update order
        if order["filled_qty"] == Decimal("0"):
            # First fill
            order["filled_avg_price"] = price
        else:
            # Update average price for partial fills
            total_value = order["filled_qty"] * order["filled_avg_price"] + fill_qty * price
            new_total_qty = order["filled_qty"] + fill_qty
            order["filled_avg_price"] = total_value / new_total_qty
        
        order["filled_qty"] += fill_qty
        
        # Update status
        if order["filled_qty"] >= order["qty"]:
            order["status"] = self.STATUS_FILLED
            order["filled_at"] = datetime.datetime.now().isoformat()
        else:
            order["status"] = self.STATUS_PARTIALLY_FILLED
        
        order["updated_at"] = datetime.datetime.now().isoformat()
        
        # Update position
        self._update_position(order)
        
        # Activate related bracket orders if this was a main bracket order
        if order["status"] == self.STATUS_FILLED and order.get("bracket", False):
            for related_id, related_order in self.orders.items():
                if related_order.get("parent_order_id") == order_id and related_order["status"] == "held":
                    related_order["status"] = self.STATUS_NEW
        
        self.logger.log_info("order_filled", 
                           f"Paper Trading: {order['symbol']} order {order_id} filled {fill_qty} @ {price}")
        
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

    def _set_market_price(self, symbol: str, price: float) -> None:
        """Manually set a market price for a symbol (for testing and verification).
        
        Args:
            symbol: The trading symbol
            price: The price to set
            
        Returns:
            None
        """
        symbol = symbol.upper()
        self.market_prices[symbol] = Decimal(str(price))
        self.logger.log_info(
            "market_price_set", 
            f"Manually set {symbol} price to {price:.2f} for testing"
        )

    def _simulate_market(self) -> None:
        """Background thread to simulate market changes and process orders.
        
        This continuously updates market prices and checks if limit/stop orders
        should be filled based on price movements.
        """
        while self.keep_running:
            # Sleep to avoid consuming too much CPU
            time.sleep(0.5)
            
            # Update market prices
            for symbol in list(self.market_prices.keys()):
                current_price = self.market_prices[symbol]
                
                # Random price change (±0.5%)
                change_pct = random.uniform(-0.005, 0.005)
                new_price = current_price * (1 + Decimal(str(change_pct)))
                
                # Ensure price doesn't go negative or zero
                if new_price <= Decimal("0"):
                    new_price = current_price
                
                self.market_prices[symbol] = new_price
            
            # Process pending orders
            for order_id, order in list(self.orders.items()):
                # Skip filled, canceled, or held orders
                if order["status"] in [self.STATUS_FILLED, self.STATUS_CANCELED, "held"]:
                    continue
                
                symbol = order["symbol"]
                current_price = self._get_current_price(symbol)
                
                # Check if limit orders can be filled
                if order["type"] == self.ORDER_TYPE_LIMIT:
                    limit_price = Decimal(str(order["limit_price"]))
                    if (order["side"] == "buy" and current_price <= limit_price) or \
                       (order["side"] == "sell" and current_price >= limit_price):
                        # Limit condition met, fill the order
                        self._fill_order(order_id, order["qty"], current_price)
                
                # Check if stop orders can be triggered
                elif order["type"] == self.ORDER_TYPE_STOP:
                    stop_price = Decimal(str(order["stop_price"]))
                    if (order["side"] == "buy" and current_price >= stop_price) or \
                       (order["side"] == "sell" and current_price <= stop_price):
                        # Stop triggered, convert to market order and fill
                        order["type"] = self.ORDER_TYPE_MARKET
                        self._fill_order(order_id, order["qty"], current_price)
            
            # Update account info with current market value of positions
            self.get_account_info()

    def _generate_client_order_id(self) -> str:
        """Generate a unique client order ID.
        
        Returns:
            str: Unique order ID
        """
        return f"paper-{uuid.uuid4().hex}" 