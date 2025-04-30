"""
Mock implementation of the Alpaca API for testing purposes
"""

class AlpacaMock:
    """
    Mock implementation of the Alpaca API for testing
    """
    
    def __init__(self):
        """Initialize the mock API with empty collections"""
        self.orders = []
        self.positions = {}
        self.account = {
            "id": "test-account",
            "cash": 100000.0,
            "buying_power": 200000.0,
            "equity": 100000.0,
            "currency": "USD",
            "status": "ACTIVE",
            "pattern_day_trader": False,
            "trading_blocked": False,
            "transfers_blocked": False,
            "account_blocked": False
        }
        self.next_order_id = 1
    
    def get_account(self):
        """Get account information"""
        return self.account
    
    def list_orders(self, status=None, limit=None, after=None, until=None, direction=None):
        """List orders based on filters"""
        if status:
            return [order for order in self.orders if order["status"] == status]
        return self.orders
    
    def get_order(self, order_id):
        """Get a specific order by ID"""
        for order in self.orders:
            if order["id"] == order_id:
                return order
        return None
    
    def get_order_by_client_order_id(self, client_order_id):
        """Get a specific order by client order ID"""
        for order in self.orders:
            if order["client_order_id"] == client_order_id:
                return order
        return None
    
    def submit_order(self, symbol, qty=None, notional=None, side="buy", type="market", 
                     time_in_force="day", limit_price=None, stop_price=None, 
                     client_order_id=None, extended_hours=False, order_class=None,
                     take_profit=None, stop_loss=None):
        """Submit a new order"""
        order_id = f"order-{self.next_order_id}"
        self.next_order_id += 1
        
        order = {
            "id": order_id,
            "client_order_id": client_order_id or f"default-{order_id}",
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "notional": notional,
            "type": type,
            "time_in_force": time_in_force,
            "limit_price": limit_price,
            "stop_price": stop_price,
            "status": "new",
            "extended_hours": extended_hours,
            "order_class": order_class,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "filled_qty": 0,
            "filled_avg_price": None,
            "filled_at": None,
            "created_at": "2025-01-01T12:00:00Z"
        }
        
        self.orders.append(order)
        
        # Auto-fill market orders
        if type == "market":
            self._fill_order(order)
        
        return order
    
    def cancel_order(self, order_id):
        """Cancel an existing order"""
        order = self.get_order(order_id)
        if order and order["status"] in ["new", "partially_filled"]:
            order["status"] = "canceled"
            return order
        return None
    
    def cancel_all_orders(self):
        """Cancel all open orders"""
        canceled = []
        for order in self.orders:
            if order["status"] in ["new", "partially_filled"]:
                order["status"] = "canceled"
                canceled.append(order)
        return canceled
    
    def list_positions(self):
        """List all open positions"""
        return list(self.positions.values())
    
    def get_position(self, symbol):
        """Get a specific position by symbol"""
        return self.positions.get(symbol)
    
    def close_position(self, symbol):
        """Close a specific position"""
        position = self.get_position(symbol)
        if position:
            # Create a closing order
            side = "sell" if position["side"] == "long" else "buy"
            qty = abs(float(position["qty"]))
            
            order = self.submit_order(
                symbol=symbol,
                side=side,
                qty=qty,
                type="market",
                time_in_force="day",
                client_order_id=f"close-{symbol}"
            )
            
            # Remove the position
            del self.positions[symbol]
            
            return order
        return None
    
    def close_all_positions(self):
        """Close all open positions"""
        closed = []
        symbols = list(self.positions.keys())
        for symbol in symbols:
            closed.append(self.close_position(symbol))
        return closed
    
    def _fill_order(self, order):
        """
        Simulate filling an order (internal method)
        """
        symbol = order["symbol"]
        side = order["side"]
        qty = float(order["qty"]) if order["qty"] is not None else 0
        notional = float(order["notional"]) if order["notional"] is not None else None
        
        # Mock price for fills
        mock_price = 100.0  # Default mock price
        if symbol.startswith("BTC"):
            mock_price = 60000.0
        elif symbol.startswith("ETH"):
            mock_price = 3500.0
        elif symbol in ["AAPL", "MSFT", "GOOG"]:
            mock_price = 200.0
        
        # If notional is provided, calculate qty
        if notional is not None:
            qty = notional / mock_price
        
        # Update order with fill information
        order["status"] = "filled"
        order["filled_qty"] = qty
        order["filled_avg_price"] = mock_price
        order["filled_at"] = "2025-01-01T12:01:00Z"
        
        # Update positions
        if side == "buy":
            self._add_to_position(symbol, qty, mock_price, "long")
        else:  # side == "sell"
            self._add_to_position(symbol, -qty, mock_price, "short")
    
    def _add_to_position(self, symbol, qty, price, side):
        """
        Update position information (internal method)
        """
        if symbol in self.positions:
            position = self.positions[symbol]
            current_qty = float(position["qty"])
            current_value = current_qty * float(position["avg_entry_price"])
            
            new_qty = current_qty + qty
            new_value = current_value + (qty * price)
            
            # If position size becomes zero, remove it
            if new_qty == 0:
                del self.positions[symbol]
                return
            
            # Update position
            position["qty"] = str(new_qty)
            position["avg_entry_price"] = str(new_value / new_qty)
            position["side"] = "long" if new_qty > 0 else "short"
            position["market_value"] = str(new_qty * price)
            position["cost_basis"] = str(new_value)
        else:
            # Create new position
            side = "long" if qty > 0 else "short"
            self.positions[symbol] = {
                "symbol": symbol,
                "qty": str(qty),
                "avg_entry_price": str(price),
                "side": side,
                "market_value": str(qty * price),
                "cost_basis": str(qty * price),
                "unrealized_pl": "0",
                "unrealized_plpc": "0",
                "current_price": str(price)
            } 