#!/usr/bin/env python
"""
Paper Trading Adapter Example

This script demonstrates how to use the PaperTradingAdapter
for testing risk management features.
"""

import time
import argparse
from decimal import Decimal

from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.integration.utils.logger import IntegrationLogger

def main():
    """Run a paper trading demonstration with risk management features."""
    parser = argparse.ArgumentParser(description='Paper Trading Demo')
    parser.add_argument('--initial-balance', type=float, default=100000.0,
                        help='Initial account balance (default: 100000.0)')
    parser.add_argument('--test-global-sl', action='store_true',
                        help='Test global stop-loss functionality')
    parser.add_argument('--test-bracket-orders', action='store_true',
                        help='Test bracket orders with SL/TP')
    parser.add_argument('--volatility', type=float, default=0.005,
                        help='Market price volatility (default: 0.005)')
    args = parser.parse_args()

    # Create logger
    logger = IntegrationLogger()
    
    # Initialize paper trading adapter
    print(f"Initializing paper trading with ${args.initial_balance:.2f}")
    adapter = PaperTradingAdapter(initial_balance=args.initial_balance, logger=logger)
    
    # Set volatility if specified
    if args.volatility != 0.005:
        adapter.PRICE_VOLATILITY = args.volatility
        print(f"Setting custom volatility: {args.volatility:.3f}")
    
    try:
        # Test basic orders
        print("\n=== Basic Order Execution ===")
        
        # Place and track a market order
        print("\nPlacing market order for AAPL...")
        order = adapter.place_market_order("AAPL", 10, "buy")
        print(f"Order ID: {order['client_order_id']}")
        
        # Wait for potential fill
        time.sleep(1)
        
        # Check order status
        updated_order = adapter.get_order_status(order["client_order_id"])
        print(f"Order status: {updated_order['status']}")
        if updated_order["status"] in ["filled", "partially_filled"]:
            print(f"Filled quantity: {updated_order['filled_qty']}")
            print(f"Average fill price: ${float(updated_order['filled_avg_price']):.2f}")
        
        # Test limit orders
        print("\nPlacing limit order for MSFT...")
        current_price = adapter._get_current_price("MSFT")
        limit_price = float(current_price) * 0.98  # 2% below current price
        limit_order = adapter.place_limit_order("MSFT", 15, "buy", limit_price)
        print(f"Limit price: ${limit_price:.2f} (current: ${float(current_price):.2f})")
        
        # Test bracket orders if specified
        if args.test_bracket_orders:
            print("\n=== Testing Bracket Orders ===")
            
            # Get current price for AMZN
            amzn_price = float(adapter._get_current_price("AMZN"))
            
            # Place bracket order with TP 5% above and SL 3% below
            print(f"\nPlacing bracket order for AMZN @ ${amzn_price:.2f}")
            print(f"Take profit: ${amzn_price * 1.05:.2f} (+5%)")
            print(f"Stop loss: ${amzn_price * 0.97:.2f} (-3%)")
            
            bracket_order = adapter.place_bracket_order(
                symbol="AMZN",
                qty=5,
                side="buy",
                take_profit_price=amzn_price * 1.05,
                stop_loss_price=amzn_price * 0.97
            )
            
            print(f"Main order ID: {bracket_order['client_order_id']}")
            
            # Wait for market simulation
            time.sleep(1)
            
            # Check status of TP/SL orders
            tp_order_id = f"{bracket_order['client_order_id']}-tp"
            sl_order_id = f"{bracket_order['client_order_id']}-sl"
            
            tp_order = adapter.get_order_status(tp_order_id)
            sl_order = adapter.get_order_status(sl_order_id)
            
            print(f"Take profit status: {tp_order['status']}")
            print(f"Stop loss status: {sl_order['status']}")
        
        # Test global stop-loss if specified
        if args.test_global_sl:
            print("\n=== Testing Global Stop-Loss ===")
            
            # Create multiple positions to simulate a portfolio
            print("\nCreating diversified portfolio for global SL testing...")
            adapter.place_market_order("GOOGL", 5, "buy")
            adapter.place_market_order("TSLA", 10, "buy")
            adapter.place_market_order("NFLX", 8, "buy")
            
            # Wait for orders to process
            time.sleep(1)
            
            # Print portfolio status
            positions = adapter.get_all_positions()
            print(f"\nPortfolio has {len(positions)} positions:")
            for pos in positions:
                current_price = adapter._get_current_price(pos["symbol"])
                position_value = float(pos["qty"]) * float(current_price)
                print(f"{pos['qty']} {pos['symbol']} @ ${float(pos['avg_entry_price']):.2f} " 
                      f"(current: ${float(current_price):.2f}, value: ${position_value:.2f})")
            
            # Get current account status
            account = adapter.get_account_info()
            print(f"\nAccount value: ${float(account['portfolio_value']):.2f}")
            print(f"Cash: ${float(account['cash']):.2f}")
            print(f"Equity: ${float(account['equity']):.2f}")
            
            # Example global stop-loss check
            initial_equity = args.initial_balance
            current_equity = float(account['equity'])
            sl_threshold = initial_equity * 0.9  # 10% drawdown
            
            print(f"\nGlobal stop-loss would trigger at ${sl_threshold:.2f} (-10%)")
            print(f"Current equity: ${current_equity:.2f} "
                  f"({((current_equity/initial_equity)-1)*100:.2f}% change)")
            
            if current_equity < sl_threshold:
                print("GLOBAL STOP-LOSS TRIGGERED! Closing all positions...")
                for pos in positions:
                    result = adapter.close_position(pos["symbol"])
                    print(f"Closed {pos['symbol']}: {result}")
            else:
                print("Global stop-loss not triggered")
        
        # Print final account status
        print("\n=== Final Account Status ===")
        account = adapter.get_account_info()
        print(f"Cash: ${float(account['cash']):.2f}")
        print(f"Portfolio value: ${float(account['portfolio_value']):.2f}")
        print(f"Equity: ${float(account['equity']):.2f}")
        print(f"Unrealized P&L: ${float(account.get('unrealized_pl', 0)):.2f}")
        
        # Show current positions
        positions = adapter.get_all_positions()
        if positions:
            print(f"\nCurrent positions ({len(positions)}):")
            for pos in positions:
                print(f"{pos['side'].upper()}: {pos['qty']} {pos['symbol']} @ ${float(pos['avg_entry_price']):.2f}")
        else:
            print("\nNo open positions")
            
    finally:
        # Shutdown the adapter's background thread
        adapter.shutdown()
        print("\nPaper trading adapter shutdown")

if __name__ == "__main__":
    main() 