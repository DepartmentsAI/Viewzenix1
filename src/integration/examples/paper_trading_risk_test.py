#!/usr/bin/env python3
"""
Paper Trading Risk Management Integration Example

This script demonstrates how to use the PaperTradingAdapter with the RiskManager
to test and validate risk management features in a simulated environment.
"""

import time
import argparse
import sys
import os
import random
import datetime
from decimal import Decimal

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.backend.services.risk_manager import RiskManager
from src.integration.utils.logger import IntegrationLogger

def run_simulation(
    duration_seconds: int = 120,
    initial_balance: float = 100000.0,
    volatility: float = 0.01,
    extreme_volatility_chance: float = 0.05,
    extreme_volatility_factor: float = 5,
    display_interval: int = 5
):
    """
    Run a paper trading simulation with risk management integration.
    
    Args:
        duration_seconds: How long to run the simulation in seconds
        initial_balance: Starting account balance
        volatility: Base price volatility (as a decimal, e.g., 0.01 = 1%)
        extreme_volatility_chance: Probability of extreme price movements (0-1)
        extreme_volatility_factor: Multiplier for extreme volatility
        display_interval: How often to display status updates in seconds
    """
    # Initialize logger
    logger = IntegrationLogger()
    logger.log_info("simulation_start", "Starting paper trading risk simulation")
    
    # Initialize risk manager and paper trading adapter
    risk_manager = RiskManager()
    adapter = PaperTradingAdapter(
        initial_balance=initial_balance,
        logger=logger,
        risk_manager=risk_manager,
        volatility=volatility
    )
    
    # Configure simulation parameters
    adapter.set_price_simulation_parameters(
        volatility=volatility,
        extreme_volatility_chance=extreme_volatility_chance,
        extreme_volatility_factor=extreme_volatility_factor
    )
    
    # Risk management parameters
    risk_params = {
        'stop_loss_percent': 0.05,  # 5% stop loss
        'take_profit_percent': 0.10,  # 10% take profit
        'max_position_size_percent': 0.20,  # Max 20% of portfolio in one position
        'max_daily_drawdown_percent': 0.10,  # Max 10% daily drawdown
        'max_open_positions': 5,  # Max 5 open positions at once
    }
    risk_manager.update_risk_parameters(risk_params)
    
    # Create portfolio of test positions
    test_symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA"]
    positions_created = []
    
    print("\n=== PAPER TRADING WITH RISK MANAGEMENT ===")
    print(f"Initial Balance: ${initial_balance:.2f}")
    print(f"Volatility: {volatility*100:.1f}% (Extreme: {extreme_volatility_chance*100:.1f}% chance of {extreme_volatility_factor}x moves)")
    print(f"Risk Parameters: SL {risk_params['stop_loss_percent']*100:.1f}%, TP {risk_params['take_profit_percent']*100:.1f}%, Max Drawdown {risk_params['max_daily_drawdown_percent']*100:.1f}%")
    print("Creating test positions...")
    
    # Create positions with bracket orders (main + SL + TP)
    for symbol in test_symbols:
        # Get current price
        current_price = float(adapter._get_current_price(symbol))
        qty = random.randint(5, 20)
        side = random.choice(["buy", "sell"])
        
        # Calculate stop loss and take profit prices
        sl_percent = risk_params['stop_loss_percent']
        tp_percent = risk_params['take_profit_percent']
        
        if side == "buy":
            stop_loss_price = current_price * (1 - sl_percent)
            take_profit_price = current_price * (1 + tp_percent)
        else:
            stop_loss_price = current_price * (1 + sl_percent)
            take_profit_price = current_price * (1 - tp_percent)
        
        # Place bracket order
        try:
            order = adapter.place_bracket_order(
                symbol=symbol,
                qty=qty,
                side=side,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price
            )
            positions_created.append({
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "entry_price": current_price,
                "stop_loss_price": stop_loss_price,
                "take_profit_price": take_profit_price,
                "order_id": order["client_order_id"]
            })
            print(f"Created {side} position for {qty} {symbol} @ ${current_price:.2f} (SL: ${stop_loss_price:.2f}, TP: ${take_profit_price:.2f})")
        except Exception as e:
            print(f"Error creating position for {symbol}: {str(e)}")
    
    print("\nRunning simulation...")
    print("(Press Ctrl+C to stop)\n")
    
    start_time = time.time()
    last_display_time = start_time
    
    try:
        while time.time() - start_time < duration_seconds:
            current_time = time.time()
            
            # Display status at regular intervals
            if current_time - last_display_time >= display_interval:
                display_status(adapter, risk_manager)
                last_display_time = current_time
            
            # Sleep to avoid high CPU usage
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    
    # Final status display
    print("\n=== FINAL STATUS ===")
    display_status(adapter, risk_manager)
    
    # Display risk events
    print("\n=== RISK EVENTS ===")
    risk_events = adapter.get_risk_events()
    if not risk_events:
        print("No risk events occurred during simulation.")
    else:
        for i, event in enumerate(risk_events, 1):
            event_time = datetime.datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
            event_type = event["type"]
            
            if event_type == "stop_loss_triggered":
                symbol = event["data"]["symbol"]
                price = event["data"]["price"]
                print(f"{i}. [{event_time}] STOP LOSS triggered for {symbol} @ ${price:.2f}")
            
            elif event_type == "take_profit_triggered":
                symbol = event["data"]["symbol"]
                price = event["data"]["price"]
                print(f"{i}. [{event_time}] TAKE PROFIT triggered for {symbol} @ ${price:.2f}")
            
            elif event_type == "order_fill":
                symbol = event["data"]["symbol"]
                status = event["data"]["order_status"]
                side = event["data"]["side"]
                qty = event["data"]["qty"]
                price = event["data"]["filled_price"]
                if price:
                    print(f"{i}. [{event_time}] ORDER {status}: {side} {qty} {symbol} @ ${price:.2f}")
    
    # Clean up
    adapter.shutdown()
    print("\nSimulation complete.")

def display_status(adapter, risk_manager):
    """Display current account status and positions."""
    # Get account info
    account = adapter.get_account_info()
    positions = adapter.get_all_positions()
    
    # Display account info
    equity = float(account["equity"])
    cash = float(account["cash"])
    initial = float(account["initial_balance"])
    pnl_percent = ((equity - initial) / initial) * 100
    
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Equity: ${equity:.2f} ({pnl_percent:+.2f}%), Cash: ${cash:.2f}")
    
    # Display positions
    if positions:
        print("Current Positions:")
        for pos in positions:
            symbol = pos["symbol"]
            qty = float(pos["qty"])
            side = "LONG" if pos["side"] == "long" else "SHORT"
            entry = float(pos["avg_entry_price"])
            current = float(adapter._get_current_price(symbol))
            unrealized_pnl = float(pos["unrealized_pl"])
            pnl_pct = (unrealized_pnl / (entry * abs(qty))) * 100
            
            print(f"  {symbol}: {qty} {side} @ ${entry:.2f} (Current: ${current:.2f}, P&L: ${unrealized_pnl:.2f} {pnl_pct:+.2f}%)")
    else:
        print("No open positions.")
    
    # Get risk metrics
    risk_metrics = risk_manager.get_risk_metrics()
    daily_pnl_pct = risk_metrics.get('daily_pnl_percent', 0) * 100
    print(f"Risk Status: Daily P&L: {daily_pnl_pct:+.2f}%, Max Drawdown: {risk_metrics.get('max_drawdown_percent', 0) * 100:.2f}%")
    print("")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paper Trading Risk Management Simulation")
    parser.add_argument("--duration", type=int, default=120, help="Simulation duration in seconds")
    parser.add_argument("--balance", type=float, default=100000.0, help="Initial account balance")
    parser.add_argument("--volatility", type=float, default=0.01, help="Base price volatility (decimal)")
    parser.add_argument("--extreme-chance", type=float, default=0.05, help="Chance of extreme price moves (0-1)")
    parser.add_argument("--extreme-factor", type=float, default=5, help="Multiplier for extreme volatility")
    parser.add_argument("--interval", type=int, default=5, help="Status display interval in seconds")
    
    args = parser.parse_args()
    
    run_simulation(
        duration_seconds=args.duration,
        initial_balance=args.balance,
        volatility=args.volatility,
        extreme_volatility_chance=args.extreme_chance,
        extreme_volatility_factor=args.extreme_factor,
        display_interval=args.interval
    ) 