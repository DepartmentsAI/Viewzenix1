#!/usr/bin/env python3
"""
Paper Trading & Risk Management Integration Example

This example demonstrates the integration between WebSocket market data streams,
paper trading functionality, and the risk management system.

Usage:
    python src/integration/examples/paper_trading_risk_integration.py --symbols AAPL,MSFT,GOOGL --duration 300
"""

import os
import sys
import time
import argparse
import json
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import project modules
try:
    from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
    from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
    
    # Try to import the backend RiskManager
    try:
        from src.backend.services.risk_manager import RiskManager
        BACKEND_AVAILABLE = True
    except ImportError:
        logger.warning("Could not import RiskManager. Running in demonstration mode only.")
        BACKEND_AVAILABLE = False
        
        # Define a mock RiskManager for demonstration purposes
        class RiskManager:
            """Mock implementation for demonstration purposes"""
            def __init__(self, broker_adapter=None, order_engine=None):
                self.broker_adapter = broker_adapter
                self.order_engine = order_engine
                self.logger = logging.getLogger("MockRiskManager")
                self.positions = {}
                self.risk_limits = {
                    "max_position_size": 100,
                    "max_order_value": 10000,
                    "max_daily_loss": 500,
                    "stop_loss_percent": 0.02,  # 2%
                    "take_profit_percent": 0.05  # 5%
                }
                self.logger.info("Mock RiskManager initialized")
                
            def validate_order(self, order):
                """Validate order against risk parameters"""
                symbol = order.get("symbol")
                qty = float(order.get("qty", 0))
                side = order.get("side")
                price = float(order.get("limit_price", 100.0))  # Default to $100 if no price provided
                
                order_value = qty * price
                self.logger.info(f"Validating order: {symbol} {side} {qty} @ ${price:.2f} = ${order_value:.2f}")
                
                # Check if order value exceeds limit
                if order_value > self.risk_limits["max_order_value"]:
                    self.logger.warning(f"Order rejected: Value ${order_value:.2f} exceeds limit ${self.risk_limits['max_order_value']}")
                    return False, "Order value exceeds maximum limit"
                
                # Check if position size exceeds limit
                if qty > self.risk_limits["max_position_size"]:
                    self.logger.warning(f"Order rejected: Size {qty} exceeds limit {self.risk_limits['max_position_size']}")
                    return False, "Position size exceeds maximum limit"
                
                self.logger.info(f"Order validated successfully: {symbol} {side} {qty}")
                return True, None
                
            def process_market_data(self, symbol, price, timestamp=None):
                """Process market data update and apply risk rules"""
                self.logger.info(f"Processing market data: {symbol} @ ${price:.2f}")
                
                # Check if we have a position in this symbol
                position = self.positions.get(symbol)
                if not position:
                    return []
                
                actions = []
                
                # Check for stop loss triggers
                if position["side"] == "long" and price <= position["stop_price"]:
                    self.logger.warning(f"STOP LOSS TRIGGERED for {symbol} @ ${price:.2f} (stop price: ${position['stop_price']:.2f})")
                    actions.append({
                        "action": "stop_loss",
                        "symbol": symbol,
                        "qty": position["qty"],
                        "reason": "Price below stop loss threshold"
                    })
                
                # Check for take profit triggers
                elif position["side"] == "long" and price >= position["take_profit_price"]:
                    self.logger.info(f"TAKE PROFIT TRIGGERED for {symbol} @ ${price:.2f} (target: ${position['take_profit_price']:.2f})")
                    actions.append({
                        "action": "take_profit",
                        "symbol": symbol,
                        "qty": position["qty"],
                        "reason": "Price reached take profit target"
                    })
                
                return actions

except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


class MockRiskManager:
    """
    Mock implementation of the RiskManager for demonstrations
    """
    def __init__(self):
        self.logger = logging.getLogger("MockRiskManager")
        self.last_prices = {}
        self.positions = {}
        self.account = {
            "cash": 100000.0,
            "portfolio_value": 100000.0,
            "buying_power": 200000.0,
            "initial_margin": 0.0,
            "maintenance_margin": 0.0,
            "day_trading_buying_power": 400000.0
        }
        self.risk_limits = {
            "max_position_size": 100,
            "max_order_value": 10000.0,
            "max_portfolio_pct": 0.10,  # 10% of portfolio
            "stop_loss_pct": 0.02,  # 2%
            "take_profit_pct": 0.05,  # 5%
        }
        self.logger.info("MockRiskManager initialized")
    
    def validate_order(self, order):
        """Validate order against risk parameters"""
        symbol = order.get("symbol")
        qty = float(order.get("qty", 0))
        side = order.get("side")
        price = float(order.get("limit_price", self.last_prices.get(symbol, 100.0)))
        
        order_value = qty * price
        self.logger.info(f"Validating order: {symbol} {side} {qty} @ ${price:.2f} = ${order_value:.2f}")
        
        # Check if order value exceeds limit
        if order_value > self.risk_limits["max_order_value"]:
            self.logger.warning(f"Order rejected: Value ${order_value:.2f} exceeds limit ${self.risk_limits['max_order_value']}")
            return False, "Order value exceeds maximum limit"
        
        # Check if position size exceeds limit
        if qty > self.risk_limits["max_position_size"]:
            self.logger.warning(f"Order rejected: Size {qty} exceeds limit {self.risk_limits['max_position_size']}")
            return False, "Position size exceeds maximum limit"
        
        # Check if order would exceed portfolio percentage limit
        portfolio_limit = self.account["portfolio_value"] * self.risk_limits["max_portfolio_pct"]
        if order_value > portfolio_limit:
            self.logger.warning(f"Order rejected: Value ${order_value:.2f} exceeds portfolio limit ${portfolio_limit:.2f}")
            return False, "Order exceeds maximum portfolio percentage"
        
        self.logger.info(f"Order validated successfully: {symbol} {side} {qty}")
        return True, None
    
    def process_market_data(self, symbol, price, timestamp=None):
        """Process market data update and apply risk rules"""
        self.last_prices[symbol] = price
        
        # Check if we have a position in this symbol
        position = self.positions.get(symbol)
        if not position:
            return []
        
        actions = []
        
        # Check for stop loss triggers
        if position["side"] == "long" and price <= position["stop_price"]:
            self.logger.warning(f"STOP LOSS TRIGGERED for {symbol} @ ${price:.2f} (stop price: ${position['stop_price']:.2f})")
            actions.append({
                "action": "stop_loss",
                "symbol": symbol,
                "qty": position["qty"],
                "reason": "Price below stop loss threshold"
            })
        
        # Check for take profit triggers
        elif position["side"] == "long" and price >= position["take_profit_price"]:
            self.logger.info(f"TAKE PROFIT TRIGGERED for {symbol} @ ${price:.2f} (target: ${position['take_profit_price']:.2f})")
            actions.append({
                "action": "take_profit",
                "symbol": symbol,
                "qty": position["qty"],
                "reason": "Price reached take profit target"
            })
        
        return actions
    
    def record_position(self, symbol, qty, entry_price, side="long"):
        """Record a position for tracking"""
        stop_price = entry_price * (1 - self.risk_limits["stop_loss_pct"])
        take_profit_price = entry_price * (1 + self.risk_limits["take_profit_pct"])
        
        self.positions[symbol] = {
            "symbol": symbol,
            "qty": qty,
            "entry_price": entry_price,
            "side": side,
            "stop_price": stop_price,
            "take_profit_price": take_profit_price,
            "created_at": datetime.now().isoformat()
        }
        
        self.logger.info(f"Position recorded: {symbol} {side} {qty} @ ${entry_price:.2f}")
        self.logger.info(f"Stop loss set at ${stop_price:.2f}, take profit at ${take_profit_price:.2f}")


class PaperTradingRiskExample:
    """
    Example demonstrating paper trading with WebSocket market data and risk management
    """
    def __init__(self, symbols=None, use_mock=False):
        """
        Initialize the example
        
        Args:
            symbols: List of symbols to trade and monitor
            use_mock: Whether to use mock risk manager even if backend is available
        """
        self.symbols = symbols or ["AAPL", "MSFT", "GOOGL"]
        self.use_mock = use_mock
        self.logger = logging.getLogger(__name__)
        self.market_data = {}
        self.last_trade_time = {}
        self.stop_event = threading.Event()
        
        # Initialize components
        try:
            # Initialize market data stream
            self.stream_adapter = AlpacaStreamAdapter(
                paper_trading=True  # Always use paper trading for example
            )
            
            # Initialize paper trading adapter
            self.paper_adapter = PaperTradingAdapter(
                paper_trading=True
            )
            
            # Initialize risk manager
            if BACKEND_AVAILABLE and not use_mock:
                self.risk_manager = RiskManager()
                self.logger.info("Using backend RiskManager")
            else:
                self.risk_manager = MockRiskManager()
                self.logger.info("Using MockRiskManager for demonstration")
                
            self.logger.info("Components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
            
    def setup_market_data(self):
        """Set up the market data stream and callbacks"""
        
        # Register callbacks for market data
        @self.stream_adapter.on_trade
        def handle_trade(trade_data):
            symbol = trade_data.get("S")  # Symbol
            price = float(trade_data.get("p", 0))  # Price
            timestamp = trade_data.get("t")  # Timestamp
            
            self.market_data[symbol] = {
                "price": price,
                "timestamp": timestamp,
                "updated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Trade: {symbol} @ ${price:.2f}")
            
            # Process through risk management
            if hasattr(self.risk_manager, "process_market_data"):
                actions = self.risk_manager.process_market_data(symbol, price, timestamp)
                
                # Handle any risk actions
                for action in actions:
                    self._handle_risk_action(action)
            
            # Record last trade time
            self.last_trade_time[symbol] = time.time()
        
        # Register connection status callback
        @self.stream_adapter.on_status
        def handle_status(connected, which, message=None):
            status = "Connected" if connected else "Disconnected"
            self.logger.info(f"WebSocket {status} ({which}): {message}")
            
            # Check if trades stream is disconnected
            if not connected and which == "trades":
                self.logger.error("Trades stream disconnected. Attempting to reconnect...")
                self.stream_adapter.reconnect()
    
    def _handle_risk_action(self, action):
        """Handle risk management actions"""
        action_type = action.get("action")
        symbol = action.get("symbol")
        qty = action.get("qty")
        
        if action_type == "stop_loss":
            self.logger.warning(f"Executing STOP LOSS for {symbol}, {qty} shares")
            self._execute_exit_order(symbol, qty, "stop_loss")
            
        elif action_type == "take_profit":
            self.logger.info(f"Executing TAKE PROFIT for {symbol}, {qty} shares")
            self._execute_exit_order(symbol, qty, "take_profit")
    
    def _execute_exit_order(self, symbol, qty, reason):
        """Execute an exit order through paper trading"""
        try:
            # Create and send the order
            order = {
                "symbol": symbol,
                "qty": qty,
                "side": "sell",
                "type": "market",
                "time_in_force": "day",
                "reason": reason
            }
            
            # Validate with risk manager
            valid, message = self.risk_manager.validate_order(order)
            if not valid:
                self.logger.error(f"Exit order validation failed: {message}")
                return None
            
            # Send to paper trading adapter
            result = self.paper_adapter.submit_order(order)
            self.logger.info(f"Exit order submitted: {result}")
            
            # Clear position from risk manager if it's a mock
            if isinstance(self.risk_manager, MockRiskManager) and symbol in self.risk_manager.positions:
                del self.risk_manager.positions[symbol]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute exit order: {e}")
            return None
    
    def create_example_position(self, symbol, qty=10):
        """Create an example position for demonstration"""
        # Get current price
        price = self.market_data.get(symbol, {}).get("price")
        if not price:
            self.logger.warning(f"No market data available for {symbol}. Using default price.")
            price = 100.0
        
        self.logger.info(f"Creating example position: {symbol}, {qty} shares @ ${price:.2f}")
        
        # Record in risk manager if it's a mock
        if isinstance(self.risk_manager, MockRiskManager):
            self.risk_manager.record_position(symbol, qty, price)
        
        # Create order
        order = {
            "symbol": symbol,
            "qty": qty,
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }
        
        # Validate with risk manager
        valid, message = self.risk_manager.validate_order(order)
        if not valid:
            self.logger.error(f"Order validation failed: {message}")
            return None
        
        # Submit to paper trading adapter
        try:
            result = self.paper_adapter.submit_order(order)
            self.logger.info(f"Order submitted: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to submit order: {e}")
            return None
    
    def start(self, duration_seconds=300):
        """
        Start the example
        
        Args:
            duration_seconds: How long to run the example (in seconds)
        """
        try:
            # Set up market data callbacks
            self.setup_market_data()
            
            # Connect to the market data stream
            self.logger.info("Connecting to market data stream...")
            self.stream_adapter.connect()
            
            # Subscribe to trades
            self.logger.info(f"Subscribing to trades for {self.symbols}")
            self.stream_adapter.subscribe_to_trades(self.symbols)
            
            # Wait for some initial market data
            self.logger.info("Waiting for initial market data...")
            start_time = time.time()
            while time.time() - start_time < 10:
                if any(self.market_data):
                    break
                time.sleep(0.5)
            
            # Create example positions
            for symbol in self.symbols:
                if symbol in self.market_data:
                    self.logger.info(f"Creating example position for {symbol}")
                    self.create_example_position(symbol)
            
            # Run for the specified duration
            self.logger.info(f"Example running for {duration_seconds} seconds...")
            end_time = time.time() + duration_seconds
            
            # Monitor positions
            while time.time() < end_time and not self.stop_event.is_set():
                # Print current positions and market data
                if isinstance(self.risk_manager, MockRiskManager):
                    for symbol, position in self.risk_manager.positions.items():
                        current_price = self.market_data.get(symbol, {}).get("price", 0)
                        if current_price > 0:
                            entry_price = position["entry_price"]
                            pnl_pct = (current_price - entry_price) / entry_price * 100
                            self.logger.info(f"Position: {symbol}, {position['qty']} shares, "
                                           f"Entry: ${entry_price:.2f}, Current: ${current_price:.2f}, "
                                           f"P&L: {pnl_pct:.2f}%")
                
                # Check for market data timeouts
                current_time = time.time()
                for symbol in self.symbols:
                    last_time = self.last_trade_time.get(symbol, 0)
                    if last_time > 0 and current_time - last_time > 30:
                        self.logger.warning(f"No market data received for {symbol} in 30 seconds")
                
                time.sleep(5)
                
            self.logger.info("Example completed")
            
        except KeyboardInterrupt:
            self.logger.info("Example stopped by user")
        except Exception as e:
            self.logger.error(f"Error during example: {e}")
        finally:
            # Clean up
            self.logger.info("Disconnecting from market data stream...")
            self.stream_adapter.disconnect()
    
    def stop(self):
        """Stop the example"""
        self.stop_event.set()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Paper Trading Risk Management Example')
    parser.add_argument('--symbols', type=str, default='AAPL,MSFT,GOOGL',
                        help='Comma-separated list of symbols to monitor')
    parser.add_argument('--duration', type=int, default=300,
                        help='Duration to run the example (in seconds)')
    parser.add_argument('--mock', action='store_true',
                        help='Use mock risk manager even if backend is available')
    args = parser.parse_args()
    
    symbols = args.symbols.split(',')
    
    logger.info(f"Starting paper trading risk management example with symbols: {symbols}")
    logger.info(f"Running for {args.duration} seconds")
    
    try:
        example = PaperTradingRiskExample(symbols=symbols, use_mock=args.mock)
        example.start(duration_seconds=args.duration)
    except Exception as e:
        logger.error(f"Failed to run example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 