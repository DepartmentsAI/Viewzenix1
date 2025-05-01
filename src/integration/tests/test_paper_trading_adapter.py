import unittest
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter

class TestPaperTradingAdapter(unittest.TestCase):
    """Test cases for the PaperTradingAdapter."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock logger to avoid file operations
        self.mock_logger = MagicMock()
        
        # Initialize the adapter with a fixed initial balance
        self.adapter = PaperTradingAdapter(initial_balance=100000.0, logger=self.mock_logger)
        
        # Add a small delay to let the market simulator initialize
        time.sleep(0.1)
    
    def tearDown(self):
        """Clean up after tests."""
        # Shut down the background thread
        self.adapter.shutdown()
    
    def test_initialization(self):
        """Test that the adapter initializes correctly."""
        # Check authentication
        self.assertTrue(self.adapter.authenticate())
        
        # Check initial account values
        account = self.adapter.get_account_info()
        self.assertEqual(account["cash"], Decimal("100000.0"))
        self.assertEqual(account["initial_balance"], Decimal("100000.0"))
        self.assertTrue(account["buying_power"] >= Decimal("100000.0"))
        self.assertEqual(account["status"], "ACTIVE")
    
    def test_place_market_order(self):
        """Test placing a market order."""
        # Place a market order
        order = self.adapter.place_market_order("AAPL", 10, "buy")
        
        # Check order properties
        self.assertEqual(order["symbol"], "AAPL")
        self.assertEqual(order["qty"], Decimal("10"))
        self.assertEqual(order["side"], "buy")
        self.assertEqual(order["type"], "market")
        
        # Let the market simulator process the order
        time.sleep(0.5)
        
        # Check order status - should be filled or new
        self.assertIn(order["status"], ["new", "filled", "partially_filled"])
        
        # Get updated order
        updated_order = self.adapter.get_order_status(order["client_order_id"])
        
        # Check if order processing happened
        self.assertEqual(updated_order["symbol"], "AAPL")
    
    def test_place_limit_order(self):
        """Test placing a limit order."""
        # Get current price for symbol
        self.adapter._get_current_price("AAPL")  # Ensure price exists
        current_price = self.adapter.market_prices["AAPL"]
        
        # Place a limit order slightly below current price (should fill soon)
        target_price = float(current_price) * 0.98
        order = self.adapter.place_limit_order("AAPL", 10, "buy", target_price)
        
        # Check order properties
        self.assertEqual(order["symbol"], "AAPL")
        self.assertEqual(order["qty"], Decimal("10"))
        self.assertEqual(order["side"], "buy")
        self.assertEqual(order["type"], "limit")
        self.assertEqual(order["limit_price"], Decimal(str(target_price)))
        
        # Order should start as new
        self.assertEqual(order["status"], "new")
        
        # Wait for potential fill (may not happen in test timeframe)
        time.sleep(1.0)
        
        # Get updated order
        updated_order = self.adapter.get_order_status(order["client_order_id"])
        
        # Order might be filled, partially filled, or still new
        self.assertIn(updated_order["status"], ["new", "filled", "partially_filled"])
    
    def test_place_bracket_order(self):
        """Test placing a bracket order with TP/SL."""
        # Get current price for symbol
        self.adapter._get_current_price("AAPL")  # Ensure price exists
        current_price = float(self.adapter.market_prices["AAPL"])
        
        # Create bracket order with TP 5% above and SL 3% below
        order = self.adapter.place_bracket_order(
            symbol="AAPL",
            qty=10,
            side="buy",
            take_profit_price=current_price * 1.05,
            stop_loss_price=current_price * 0.97
        )
        
        # Main order should be market and have bracket flag
        self.assertEqual(order["symbol"], "AAPL")
        self.assertEqual(order["qty"], Decimal("10"))
        self.assertEqual(order["side"], "buy")
        self.assertTrue(order.get("bracket", False))
        
        # Let the market simulator process the order
        time.sleep(0.5)
        
        # Find related TP/SL orders
        tp_order_id = f"{order['client_order_id']}-tp"
        sl_order_id = f"{order['client_order_id']}-sl"
        
        tp_order = self.adapter.get_order_status(tp_order_id)
        sl_order = self.adapter.get_order_status(sl_order_id)
        
        # Check TP order
        self.assertEqual(tp_order["symbol"], "AAPL")
        self.assertEqual(tp_order["side"], "sell")
        self.assertEqual(tp_order["parent_order_id"], order["client_order_id"])
        self.assertEqual(tp_order["bracket_type"], "take_profit")
        
        # Check SL order
        self.assertEqual(sl_order["symbol"], "AAPL")
        self.assertEqual(sl_order["side"], "sell")
        self.assertEqual(sl_order["parent_order_id"], order["client_order_id"])
        self.assertEqual(sl_order["bracket_type"], "stop_loss")
        
        # If main order filled, TP/SL should be activated
        if order["status"] == "filled":
            self.assertNotEqual(tp_order["status"], "held")
            self.assertNotEqual(sl_order["status"], "held")
    
    def test_cancel_order(self):
        """Test cancelling an order."""
        # Place a limit order that won't fill immediately
        order = self.adapter.place_limit_order("AAPL", 10, "buy", 1.0)  # Very low price
        
        # Cancel the order
        result = self.adapter.cancel_order(order["client_order_id"])
        
        # Check result
        self.assertEqual(result["status"], "canceled")
        
        # Try to cancel non-existent order
        error_result = self.adapter.cancel_order("non-existent-id")
        self.assertIn("error", error_result)
    
    def test_position_management(self):
        """Test position creation and management."""
        # Place a market order that should fill
        order = self.adapter.place_market_order("MSFT", 15, "buy")
        
        # Wait for order to fill
        time.sleep(0.5)
        
        # Check if position was created
        positions = self.adapter.get_all_positions()
        
        # Find the MSFT position if it exists
        msft_position = None
        for pos in positions:
            if pos["symbol"] == "MSFT":
                msft_position = pos
                break
        
        # If order was filled, position should exist
        if order["status"] == "filled":
            self.assertIsNotNone(msft_position)
            if msft_position:
                self.assertEqual(msft_position["symbol"], "MSFT")
                self.assertEqual(msft_position["side"], "long")
                self.assertEqual(msft_position["qty"], "15")
                
                # Try to close the position
                close_result = self.adapter.close_position("MSFT")
                
                # Check result
                self.assertNotIn("error", close_result)
    
    def test_notional_order(self):
        """Test placing a notional (dollar-based) order."""
        # Place a notional market order for $1000 worth of a symbol
        order = self.adapter.place_notional_order("AAPL", 1000, "buy", "market")
        
        # Check order properties
        self.assertEqual(order["symbol"], "AAPL")
        self.assertEqual(order["side"], "buy")
        self.assertTrue(order.get("notional", False))
        self.assertEqual(order["notional_amount"], 1000)
        
        # Let the market simulator process the order
        time.sleep(0.5)
        
        # Get updated order
        updated_order = self.adapter.get_order_status(order["client_order_id"])
        
        # Check status
        self.assertIn(updated_order["status"], ["new", "filled", "partially_filled"])
    
    def test_get_account_info_updates(self):
        """Test that account info updates correctly after trades."""
        # Check initial account
        initial_account = self.adapter.get_account_info()
        initial_cash = initial_account["cash"]
        
        # Place order that should fill
        order = self.adapter.place_market_order("AAPL", 10, "buy")
        
        # Wait for fill
        time.sleep(0.5)
        
        # Get updated account
        updated_account = self.adapter.get_account_info()
        
        # If order filled, cash should be reduced
        if order["status"] == "filled":
            self.assertLess(updated_account["cash"], initial_cash)
    
    def test_market_price_simulation(self):
        """Test that market prices are generated and updated."""
        # Access a few symbols to generate prices
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        
        for symbol in symbols:
            price = self.adapter._get_current_price(symbol)
            self.assertIsInstance(price, Decimal)
            self.assertGreater(price, Decimal("0"))
        
        # Wait for market simulation to update prices
        initial_prices = {s: self.adapter.market_prices[s] for s in symbols}
        
        # Wait for price movement
        time.sleep(2.0)
        
        # Check for price changes
        updated_prices = {s: self.adapter.market_prices[s] for s in symbols}
        
        # At least one price should have changed
        prices_changed = False
        for symbol in symbols:
            if initial_prices[symbol] != updated_prices[symbol]:
                prices_changed = True
                break
        
        self.assertTrue(prices_changed)
    
    def test_error_handling(self):
        """Test adapter error handling for invalid operations."""
        # Try to close a non-existent position
        result = self.adapter.close_position("NONEXISTENT")
        self.assertIn("error", result)
        
        # Try to get a non-existent order
        result = self.adapter.get_order_status("invalid-id")
        self.assertIn("error", result)
        
        # Try to place an invalid notional order
        result = self.adapter.place_notional_order("AAPL", 1000, "buy", "invalid_type")
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main() 