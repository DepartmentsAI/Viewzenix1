#!/usr/bin/env python3
"""
Risk Management Market Data Validator

This utility validates that real-time market data is properly
integrated with the risk management system and paper trading adapter.
It can be used to verify that WebSocket connections, data flow, and 
risk calculations are working correctly.
"""

import os
import sys
import time
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import after path is set
try:
    from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
    from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
    from src.integration.utils.logger import IntegrationLogger
    
    # Import from backend if available
    try:
        from src.backend.services.risk_manager import RiskManager
        RISK_MANAGER_AVAILABLE = True
    except ImportError:
        logger.warning("Backend RiskManager not available. Using mock implementation.")
        RISK_MANAGER_AVAILABLE = False
        
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    logger.error("Please make sure you're running this script from the project root.")
    sys.exit(1)


class MockRiskManager:
    """
    Mock implementation of the RiskManager for testing without the backend service
    """
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("MockRiskManager")
        self.limits = {
            "max_position_size": 100,
            "max_order_value": 10000,
            "max_exposure_pct": 0.10,  # 10% of portfolio
            "stop_loss_pct": 0.02  # 2% below entry price
        }
        self.risk_events = []
        self.positions = {}
        self.logger.info("MockRiskManager initialized with default risk limits")
    
    def check_order_risk(self, symbol: str, qty: float, side: str, 
                        order_type: str, price: float = None) -> tuple:
        """
        Check if an order meets risk criteria
        
        Returns:
            tuple: (allowed: bool, details: dict)
        """
        self.logger.info(f"Checking risk for order: {symbol}, {qty} shares, {side}")
        
        # Calculate order value
        order_value = qty * (price or 100.0)
        
        # Check maximum position size
        if qty > self.limits["max_position_size"]:
            self.logger.warning(f"Order rejected: Position size {qty} exceeds limit {self.limits['max_position_size']}")
            return False, {
                "reason": "position_size_exceeded",
                "limit": self.limits["max_position_size"],
                "actual": qty
            }
        
        # Check maximum order value
        if order_value > self.limits["max_order_value"]:
            self.logger.warning(f"Order rejected: Order value ${order_value} exceeds limit ${self.limits['max_order_value']}")
            return False, {
                "reason": "order_value_exceeded",
                "limit": self.limits["max_order_value"],
                "actual": order_value
            }
        
        # Check if position already exists for this symbol
        current_position = self.positions.get(symbol, {"qty": 0, "value": 0})
        
        # For sell orders, check if we have the position
        if side == "sell" and qty > current_position.get("qty", 0):
            self.logger.warning(f"Order rejected: Attempting to sell {qty} shares but only have {current_position.get('qty', 0)}")
            return False, {
                "reason": "insufficient_position",
                "requested": qty,
                "available": current_position.get("qty", 0)
            }
            
        self.logger.info(f"Order approved: {symbol}, {qty} shares, {side}")
        return True, {"status": "approved"}
    
    def on_market_data_update(self, symbol: str, price: float, timestamp: str = None) -> List[dict]:
        """
        Process market data update and return any triggered risk actions
        
        Args:
            symbol: The stock symbol
            price: Current market price
            timestamp: Optional timestamp of the market data
            
        Returns:
            List of risk actions triggered by this update
        """
        if symbol not in self.positions:
            return []
        
        position = self.positions[symbol]
        entry_price = position.get("avg_entry_price", price)
        qty = position.get("qty", 0)
        
        # Skip if no position
        if qty == 0:
            return []
        
        actions = []
        
        # Check for stop loss trigger
        if position.get("side") == "long" and qty > 0:
            stop_price = float(entry_price) * (1 - self.limits["stop_loss_pct"])
            if price <= stop_price:
                self.logger.warning(f"Stop loss triggered for {symbol} at ${price} (stop: ${stop_price})")
                actions.append({
                    "action": "stop_loss_triggered",
                    "symbol": symbol,
                    "qty": qty,
                    "price": price,
                    "stop_price": stop_price,
                    "entry_price": entry_price
                })
                
                # Record risk event
                self.risk_events.append({
                    "timestamp": timestamp or time.time(),
                    "event_type": "stop_loss_triggered",
                    "symbol": symbol,
                    "price": price,
                    "stop_price": stop_price,
                    "entry_price": entry_price
                })
                
        return actions
    
    def on_order_filled(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle order filled events
        
        Args:
            order_data: Details of the filled order
            
        Returns:
            Optional dict with risk management suggestions
        """
        symbol = order_data.get("symbol")
        side = order_data.get("side")
        qty = float(order_data.get("qty", 0))
        filled_price = float(order_data.get("filled_avg_price", 0))
        
        self.logger.info(f"Order filled: {symbol}, {qty} shares at ${filled_price}")
        
        # Update position tracking
        if symbol not in self.positions:
            self.positions[symbol] = {
                "symbol": symbol,
                "qty": 0,
                "avg_entry_price": 0,
                "side": "flat"
            }
            
        position = self.positions[symbol]
        current_qty = float(position.get("qty", 0))
        current_price = float(position.get("avg_entry_price", 0))
        
        # Update position based on side
        if side == "buy":
            # Calculate new average price if adding to position
            if current_qty > 0:
                # Weighted average of existing position and new shares
                new_qty = current_qty + qty
                new_price = ((current_qty * current_price) + (qty * filled_price)) / new_qty
                position["avg_entry_price"] = new_price
                position["qty"] = new_qty
            else:
                # New position
                position["avg_entry_price"] = filled_price
                position["qty"] = qty
            
            position["side"] = "long"
            
            # Suggest stop loss
            stop_price = filled_price * (1 - self.limits["stop_loss_pct"])
            self.logger.info(f"Suggesting stop loss at ${stop_price:.2f} for {symbol}")
            return {
                "action": "stop_loss",
                "price": stop_price,
                "original_order_id": order_data.get("id"),
                "symbol": symbol,
                "qty": qty
            }
            
        elif side == "sell":
            # Reduce position
            new_qty = current_qty - qty
            if new_qty <= 0:
                # Position closed
                position["qty"] = 0
                position["avg_entry_price"] = 0
                position["side"] = "flat"
            else:
                # Partial position remaining (keep same average price)
                position["qty"] = new_qty
        
        return None


class RiskMarketDataValidator:
    """
    Utility to validate the integration between market data and risk management
    """
    def __init__(self, use_paper: bool = True, use_mock_risk: bool = False):
        """
        Initialize the validator
        
        Args:
            use_paper: Whether to use paper trading environment
            use_mock_risk: Whether to use mock risk manager (True) or backend risk manager (False)
        """
        self.logger = IntegrationLogger()
        self.use_paper = use_paper
        self.use_mock_risk = use_mock_risk
        self.stream_adapter = None
        self.paper_adapter = None
        self.risk_manager = None
        self.market_data = {}
        self.test_orders = {}
        self.risk_actions = []
        self.validation_results = {
            "connection_success": False,
            "market_data_received": False,
            "risk_processing_success": False,
            "stop_loss_trigger_success": False,
            "take_profit_trigger_success": False,
            "position_monitoring_success": False,
            "errors": []
        }
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize the components needed for validation"""
        try:
            # Initialize market data stream
            self.logger.log_info("Initializing AlpacaStreamAdapter...")
            self.stream_adapter = AlpacaStreamAdapter(
                paper_trading=self.use_paper
            )
            
            # Initialize paper trading adapter
            self.logger.log_info("Initializing PaperTradingAdapter...")
            self.paper_adapter = PaperTradingAdapter(
                paper_trading=self.use_paper
            )
            
            # Initialize risk manager (backend or mock)
            if RISK_MANAGER_AVAILABLE and not self.use_mock_risk:
                self.logger.log_info("Initializing backend RiskManager...")
                self.risk_manager = RiskManager()
                self.logger.log_info("Using backend RiskManager")
            else:
                self.logger.log_info("Initializing MockRiskManager...")
                self.risk_manager = MockRiskManager(logger=self.logger)
                self.logger.log_info("Using mock RiskManager implementation")
            
            # Set up WebSocket callbacks
            self._setup_callbacks()
            
            self.logger.log_info("Components initialized successfully")
            
        except Exception as e:
            self.logger.log_error(f"Failed to initialize components: {e}")
            self.validation_results["errors"].append(f"Component initialization error: {str(e)}")
            raise
    
    def _setup_callbacks(self):
        """Set up the callbacks for market data and connection status"""
        
        @self.stream_adapter.on_trade
        def on_trade(trade_data):
            # Extract data
            symbol = trade_data.get("S")  # Symbol
            price = float(trade_data.get("p", 0))  # Price
            timestamp = trade_data.get("t")  # Timestamp
            
            if not symbol or price <= 0:
                return
            
            self.logger.log_debug(f"Trade: {symbol} @ ${price:.2f}")
            
            # Store market data
            self.market_data[symbol] = {
                "last_price": price,
                "last_update": time.time(),
                "trade_time": timestamp
            }
            
            # Flag that we received market data
            self.validation_results["market_data_received"] = True
            
            # Process through risk management
            try:
                # Check if we have a method to process market data (depends on implementation)
                if hasattr(self.risk_manager, "on_market_data_update"):
                    actions = self.risk_manager.on_market_data_update(symbol, price, timestamp)
                elif hasattr(self.risk_manager, "process_market_data"):
                    actions = self.risk_manager.process_market_data(symbol, price, timestamp)
                else:
                    self.logger.log_warning("Risk manager doesn't have market data processing method")
                    return
                
                # Store and process any actions
                if actions:
                    for action in actions:
                        self.risk_actions.append(action)
                        self._process_risk_action(action)
                    
                    # Flag that risk processing worked
                    self.validation_results["risk_processing_success"] = True
                    
                    # Check for specific action types
                    for action in actions:
                        action_type = action.get("action", "")
                        if "stop_loss" in action_type:
                            self.validation_results["stop_loss_trigger_success"] = True
                        elif "take_profit" in action_type:
                            self.validation_results["take_profit_trigger_success"] = True
                    
            except Exception as e:
                self.logger.log_error(f"Error processing market data through risk manager: {e}")
                self.validation_results["errors"].append(f"Risk processing error: {str(e)}")
        
        @self.stream_adapter.on_quote
        def on_quote(quote_data):
            # Simple handling of quotes for validation
            symbol = quote_data.get("S")  # Symbol
            bid_price = float(quote_data.get("bp", 0))  # Bid price
            ask_price = float(quote_data.get("ap", 0))  # Ask price
            
            if not symbol or bid_price <= 0 or ask_price <= 0:
                return
            
            # Store quote data
            if symbol not in self.market_data:
                self.market_data[symbol] = {}
            
            self.market_data[symbol].update({
                "bid_price": bid_price,
                "ask_price": ask_price,
                "mid_price": (bid_price + ask_price) / 2,
                "last_quote_update": time.time()
            })
            
            # Flag that we received market data
            self.validation_results["market_data_received"] = True
        
        @self.stream_adapter.on_status
        def on_connection_status(connected, which_stream, message=None):
            status = "Connected" if connected else "Disconnected"
            self.logger.log_info(f"WebSocket {status} ({which_stream}): {message}")
            
            if connected:
                self.validation_results["connection_success"] = True
    
    def _process_risk_action(self, action):
        """Process a risk action from the risk manager"""
        action_type = action.get("action", "unknown")
        symbol = action.get("symbol")
        qty = action.get("qty", 0)
        
        self.logger.log_info(f"Processing risk action: {action_type} for {symbol}, {qty} shares")
        
        if "stop_loss" in action_type:
            # Create and execute a sell order
            order = {
                "symbol": symbol,
                "qty": qty,
                "side": "sell",
                "type": "market",
                "time_in_force": "day",
                "reason": "stop_loss"
            }
            
            try:
                result = self.paper_adapter.submit_order(order)
                self.logger.log_info(f"Executed stop loss order: {result}")
                return result
            except Exception as e:
                self.logger.log_error(f"Failed to execute stop loss order: {e}")
                self.validation_results["errors"].append(f"Stop loss execution error: {str(e)}")
                return None
    
    def connect_to_market_data(self) -> bool:
        """Connect to market data stream and subscribe to test symbols"""
        try:
            # Test symbols (commonly used, typically have good liquidity)
            test_symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "SPY"]
            
            self.logger.log_info(f"Connecting to market data stream with symbols: {test_symbols}")
            
            # Connect to WebSocket stream
            self.stream_adapter.connect()
            
            # Wait briefly for connection to establish
            time.sleep(2)
            
            # Subscribe to trades and quotes
            self.stream_adapter.subscribe_to_trades(test_symbols)
            self.stream_adapter.subscribe_to_quotes(test_symbols)
            
            # Create test positions in the mock risk manager (if using it)
            if isinstance(self.risk_manager, MockRiskManager):
                self.logger.log_info("Creating test positions in mock risk manager")
                
                # Create sample positions with stop losses close to current market price
                # for testing stop loss triggers
                for symbol in test_symbols:
                    # Simulate a position entry
                    self.risk_manager.positions[symbol] = {
                        "symbol": symbol,
                        "qty": 10,
                        "avg_entry_price": 100.0,  # Will be updated with real price
                        "side": "long",
                        "entry_time": time.time()
                    }
            
            # Wait for initial market data
            self.logger.log_info("Waiting for initial market data...")
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.market_data:
                    break
                time.sleep(0.5)
            
            # Update position prices with real market data
            if isinstance(self.risk_manager, MockRiskManager) and self.market_data:
                for symbol, position in self.risk_manager.positions.items():
                    if symbol in self.market_data:
                        # Get current price and set entry price slightly higher for stop loss testing
                        current_price = self.market_data[symbol].get("last_price", 100.0)
                        position["avg_entry_price"] = current_price * 1.03  # 3% above current price
                        
                        self.logger.log_info(f"Updated test position: {symbol} @ ${position['avg_entry_price']:.2f} "
                                            f"(current price: ${current_price:.2f})")
            
            return bool(self.market_data)
            
        except Exception as e:
            self.logger.log_error(f"Error connecting to market data: {e}")
            self.validation_results["errors"].append(f"Market data connection error: {str(e)}")
            return False
    
    def validate_risk_checks(self) -> bool:
        """Validate that risk checks are working correctly"""
        self.logger.log_info("Validating risk checks...")
        
        if not self.market_data:
            self.logger.log_warning("No market data available for risk check validation")
            return False
        
        successes = 0
        total_checks = 0
        
        # Test 1: Valid order within limits
        total_checks += 1
        symbol = next(iter(self.market_data))
        price = self.market_data[symbol].get("last_price", 100.0)
        
        try:
            # Create a small test order that should pass risk checks
            allowed, details = self.risk_manager.check_order_risk(
                symbol=symbol,
                qty=5,
                side="buy",
                order_type="market",
                price=price
            )
            
            if allowed:
                self.logger.log_info("Valid order check passed: Small order approved")
                successes += 1
            else:
                self.logger.log_warning(f"Valid order check failed: {details}")
        except Exception as e:
            self.logger.log_error(f"Error during valid order check: {e}")
            self.validation_results["errors"].append(f"Valid order check error: {str(e)}")
        
        # Test 2: Order exceeding position size limit
        total_checks += 1
        try:
            # Create a large test order that should fail position size check
            allowed, details = self.risk_manager.check_order_risk(
                symbol=symbol,
                qty=10000,  # Very large position
                side="buy",
                order_type="market",
                price=price
            )
            
            if not allowed and "position_size" in str(details):
                self.logger.log_info("Position size limit check passed: Large order rejected")
                successes += 1
            else:
                self.logger.log_warning("Position size limit check failed: Large order was not rejected")
        except Exception as e:
            self.logger.log_error(f"Error during position size check: {e}")
            self.validation_results["errors"].append(f"Position size check error: {str(e)}")
        
        # Test 3: Order exceeding value limit
        total_checks += 1
        try:
            # Create a high-value test order that should fail order value check
            allowed, details = self.risk_manager.check_order_risk(
                symbol=symbol,
                qty=200,
                side="buy",
                order_type="market",
                price=price * 10  # Artificially high price
            )
            
            if not allowed and "value" in str(details):
                self.logger.log_info("Order value limit check passed: High-value order rejected")
                successes += 1
            else:
                self.logger.log_warning("Order value limit check failed: High-value order was not rejected")
        except Exception as e:
            self.logger.log_error(f"Error during order value check: {e}")
            self.validation_results["errors"].append(f"Order value check error: {str(e)}")
        
        success_rate = successes / total_checks if total_checks > 0 else 0
        self.logger.log_info(f"Risk checks validation complete: {successes}/{total_checks} checks passed ({success_rate:.0%})")
        
        return success_rate >= 0.75  # At least 75% of checks must pass
    
    def validate_position_monitoring(self) -> bool:
        """Validate that position monitoring and risk actions work correctly"""
        self.logger.log_info("Validating position monitoring and risk actions...")
        
        if not self.market_data:
            self.logger.log_warning("No market data available for position monitoring validation")
            return False
        
        if not isinstance(self.risk_manager, MockRiskManager):
            self.logger.log_warning("Position monitoring validation requires MockRiskManager")
            return False
        
        # Check existing positions
        if not self.risk_manager.positions:
            self.logger.log_warning("No positions available for monitoring validation")
            return False
        
        # Record initial position state
        initial_positions = {}
        for symbol, position in self.risk_manager.positions.items():
            if symbol in self.market_data:
                initial_positions[symbol] = {
                    "symbol": symbol,
                    "entry_price": position.get("avg_entry_price", 0),
                    "current_price": self.market_data[symbol].get("last_price", 0),
                    "qty": position.get("qty", 0)
                }
                
                # Log position details
                self.logger.log_info(f"Monitoring position: {symbol}, {position.get('qty', 0)} shares @ "
                                   f"${position.get('avg_entry_price', 0):.2f}, current price: "
                                   f"${self.market_data[symbol].get('last_price', 0):.2f}")
        
        if not initial_positions:
            self.logger.log_warning("No positions with market data available for monitoring")
            return False
        
        # Create artificial price movements to trigger stop losses
        # In a real scenario, this would be actual market movements,
        # but for testing we'll simulate price changes
        for symbol, position in initial_positions.items():
            entry_price = position["entry_price"]
            current_price = position["current_price"]
            
            # Calculate a stop price slightly below the entry price
            stop_price = entry_price * (1 - self.risk_manager.limits["stop_loss_pct"])
            
            self.logger.log_info(f"Testing stop loss for {symbol}: Entry ${entry_price:.2f}, "
                               f"Current ${current_price:.2f}, Stop ${stop_price:.2f}")
            
            # Simulate a price drop below the stop loss
            test_price = stop_price * 0.99  # Just below stop price
            
            # Process the simulated price update
            try:
                # Process the artificial price update
                actions = self.risk_manager.on_market_data_update(symbol, test_price)
                
                if actions:
                    self.logger.log_info(f"Stop loss test successful for {symbol}: {len(actions)} actions triggered")
                    
                    # Process the actions
                    for action in actions:
                        self.risk_actions.append(action)
                        if "stop_loss" in action.get("action", ""):
                            self.validation_results["stop_loss_trigger_success"] = True
                else:
                    self.logger.log_warning(f"Stop loss test failed for {symbol}: No actions triggered")
            except Exception as e:
                self.logger.log_error(f"Error processing artificial price update: {e}")
                self.validation_results["errors"].append(f"Artificial price update error: {str(e)}")
        
        # Check if stop loss triggering worked
        if self.validation_results["stop_loss_trigger_success"]:
            self.logger.log_info("Position monitoring validation successful: Stop loss triggers working")
            self.validation_results["position_monitoring_success"] = True
            return True
        else:
            self.logger.log_warning("Position monitoring validation failed: Stop loss triggers not working")
            return False
    
    def run_validation(self, duration_seconds: int = 30) -> dict:
        """
        Run the full validation suite
        
        Args:
            duration_seconds: How long to run the validation (in seconds)
            
        Returns:
            Dictionary of validation results
        """
        try:
            start_time = time.time()
            self.logger.log_info(f"Starting validation (duration: {duration_seconds} seconds)...")
            
            # Reset validation results
            self.validation_results = {
                "connection_success": False,
                "market_data_received": False,
                "risk_processing_success": False,
                "stop_loss_trigger_success": False,
                "take_profit_trigger_success": False,
                "position_monitoring_success": False,
                "errors": []
            }
            
            # Step 1: Connect to market data
            if not self.connect_to_market_data():
                self.logger.log_error("Failed to connect to market data")
                self.validation_results["errors"].append("Market data connection failed")
                return self._finalize_validation_results()
            
            # Step 2: Validate risk checks
            self.validate_risk_checks()
            
            # Step 3: Validate position monitoring
            self.validate_position_monitoring()
            
            # Step 4: Listen for real-time data to observe how the system behaves
            # This allows us to see real market data flowing through the system
            self.logger.log_info(f"Monitoring real-time data flow for {duration_seconds} seconds...")
            
            # Wait for the specified duration to collect real-time data and observe behavior
            remaining_time = duration_seconds - (time.time() - start_time)
            if remaining_time > 0:
                end_time = time.time() + remaining_time
                
                while time.time() < end_time:
                    # Print a periodic status update
                    symbols_with_data = [s for s in self.market_data.keys() if self.market_data[s].get("last_update", 0) > time.time() - 30]
                    
                    if symbols_with_data:
                        self.logger.log_info(f"Active data streams: {len(symbols_with_data)} symbols")
                        
                        # Log a sample of the current prices
                        for symbol in list(symbols_with_data)[:3]:  # Show up to 3 symbols
                            last_price = self.market_data[symbol].get("last_price", 0)
                            self.logger.log_info(f"  {symbol}: ${last_price:.2f}")
                    
                    # Log any risk actions that occurred
                    recent_actions = [a for a in self.risk_actions if a not in self.risk_actions[:len(self.risk_actions)-3]]
                    if recent_actions:
                        self.logger.log_info(f"Recent risk actions: {len(recent_actions)}")
                        for action in recent_actions[:2]:  # Show up to 2 actions
                            self.logger.log_info(f"  {action.get('action', 'unknown')} for {action.get('symbol', 'unknown')}")
                    
                    time.sleep(5)  # Check every 5 seconds
            
            return self._finalize_validation_results()
            
        except Exception as e:
            self.logger.log_error(f"Error during validation: {e}")
            self.validation_results["errors"].append(f"Validation error: {str(e)}")
            return self._finalize_validation_results()
        
        finally:
            # Clean up resources
            try:
                self.logger.log_info("Disconnecting from market data stream...")
                self.stream_adapter.disconnect()
            except Exception as e:
                self.logger.log_error(f"Error disconnecting: {e}")
    
    def _finalize_validation_results(self) -> dict:
        """Finalize and return validation results"""
        # Calculate overall success
        success_criteria = [
            self.validation_results["connection_success"],
            self.validation_results["market_data_received"],
            self.validation_results["risk_processing_success"] or self.validation_results["position_monitoring_success"]
        ]
        
        # Overall success if all critical criteria are met
        self.validation_results["success"] = all(success_criteria)
        
        # Add data collection stats
        self.validation_results["symbols_with_data"] = len(self.market_data)
        self.validation_results["risk_actions_generated"] = len(self.risk_actions)
        
        # Print summary
        self._print_validation_summary()
        
        return self.validation_results
    
    def _print_validation_summary(self):
        """Print a summary of the validation results"""
        self.logger.log_info("\n--- VALIDATION SUMMARY ---")
        self.logger.log_info(f"Overall Success: {self.validation_results['success']}")
        self.logger.log_info(f"Connection Success: {self.validation_results['connection_success']}")
        self.logger.log_info(f"Market Data Received: {self.validation_results['market_data_received']}")
        self.logger.log_info(f"Risk Processing Success: {self.validation_results['risk_processing_success']}")
        self.logger.log_info(f"Stop Loss Trigger Success: {self.validation_results['stop_loss_trigger_success']}")
        self.logger.log_info(f"Take Profit Trigger Success: {self.validation_results['take_profit_trigger_success']}")
        self.logger.log_info(f"Position Monitoring Success: {self.validation_results['position_monitoring_success']}")
        self.logger.log_info(f"Symbols With Data: {self.validation_results.get('symbols_with_data', 0)}")
        self.logger.log_info(f"Risk Actions Generated: {self.validation_results.get('risk_actions_generated', 0)}")
        
        if self.validation_results["errors"]:
            self.logger.log_info(f"Errors ({len(self.validation_results['errors'])}):")
            for i, error in enumerate(self.validation_results["errors"][:5]):  # Show up to 5 errors
                self.logger.log_info(f"  {i+1}. {error}")
            
            if len(self.validation_results["errors"]) > 5:
                self.logger.log_info(f"  ... and {len(self.validation_results['errors']) - 5} more errors")
        else:
            self.logger.log_info("No errors reported")


def main():
    """Main entry point for the validator"""
    parser = argparse.ArgumentParser(description='Validate risk management and market data integration')
    parser.add_argument('--duration', type=int, default=30,
                        help='Duration to run the validation in seconds (default: 30)')
    parser.add_argument('--paper', action='store_true', default=True,
                        help='Use paper trading environment (default: True)')
    parser.add_argument('--mock', action='store_true',
                        help='Use mock risk manager instead of backend implementation (default: False)')
    args = parser.parse_args()
    
    logger.info(f"Starting risk market data validator (duration: {args.duration}s, "
               f"paper: {args.paper}, mock: {args.mock})")
    
    try:
        validator = RiskMarketDataValidator(use_paper=args.paper, use_mock_risk=args.mock)
        results = validator.run_validation(duration_seconds=args.duration)
        
        logger.info(f"Validation complete - Success: {results['success']}")
        
        # Return exit code based on validation success
        return 0 if results["success"] else 1
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 