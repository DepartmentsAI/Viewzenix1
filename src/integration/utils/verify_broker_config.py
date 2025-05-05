#!/usr/bin/env python3
"""
Broker Configuration Verification Tool

This utility verifies that broker API configuration is correctly set up
and that all required credentials are present and valid. It helps identify
issues with API keys, URLs, or permissions.

Usage:
    python src/integration/utils/verify_broker_config.py
"""

import os
import sys
import json
import logging
import argparse
import time
import requests
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
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

# Required environment variables
REQUIRED_ENV_VARS = [
    "ALPACA_API_KEY",
    "ALPACA_API_SECRET",
    "ALPACA_API_BASE_URL",
    "ALPACA_WS_URL"
]

# Optional but recommended environment variables
OPTIONAL_ENV_VARS = [
    "ALPACA_PAPER_API_KEY",
    "ALPACA_PAPER_API_SECRET",
    "ALPACA_PAPER_API_BASE_URL",
    "ALPACA_PAPER_WS_URL"
]


def check_env_variables() -> Dict[str, Any]:
    """
    Check if the required environment variables are set
    
    Returns:
        Dictionary with results of the check
    """
    results = {
        "required_vars_present": True,
        "optional_vars_present": True,
        "missing_required": [],
        "missing_optional": [],
        "env_vars": {}
    }
    
    # Check required variables
    for var in REQUIRED_ENV_VARS:
        if var not in os.environ or not os.environ[var]:
            results["required_vars_present"] = False
            results["missing_required"].append(var)
        else:
            # Store variable (masked if it's a secret)
            if "SECRET" in var or "KEY" in var:
                value = os.environ[var]
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                results["env_vars"][var] = masked_value
            else:
                results["env_vars"][var] = os.environ[var]
    
    # Check optional variables
    for var in OPTIONAL_ENV_VARS:
        if var not in os.environ or not os.environ[var]:
            results["optional_vars_present"] = False
            results["missing_optional"].append(var)
        else:
            # Store variable (masked if it's a secret)
            if "SECRET" in var or "KEY" in var:
                value = os.environ[var]
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                results["env_vars"][var] = masked_value
            else:
                results["env_vars"][var] = os.environ[var]
    
    return results


def test_alpaca_api_connection(use_paper: bool = True) -> Dict[str, Any]:
    """
    Test connection to Alpaca API
    
    Args:
        use_paper: Whether to use paper trading API
    
    Returns:
        Dictionary with results of the connection test
    """
    results = {
        "success": False,
        "status_code": None,
        "response": None,
        "error": None,
        "account_id": None,
        "trading_allowed": False,
        "is_paper": use_paper
    }
    
    try:
        # Determine which API key to use
        if use_paper and "ALPACA_PAPER_API_KEY" in os.environ and "ALPACA_PAPER_API_SECRET" in os.environ:
            api_key = os.environ["ALPACA_PAPER_API_KEY"]
            api_secret = os.environ["ALPACA_PAPER_API_SECRET"]
            base_url = os.environ.get("ALPACA_PAPER_API_BASE_URL", "https://paper-api.alpaca.markets")
        else:
            api_key = os.environ["ALPACA_API_KEY"]
            api_secret = os.environ["ALPACA_API_SECRET"]
            base_url = os.environ.get("ALPACA_API_BASE_URL", "https://api.alpaca.markets")
        
        # Set up headers
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        
        # Test account endpoint
        url = f"{base_url}/v2/account"
        logger.info(f"Testing connection to {url}")
        
        response = requests.get(url, headers=headers)
        results["status_code"] = response.status_code
        
        if response.status_code == 200:
            results["success"] = True
            results["response"] = response.json()
            results["account_id"] = results["response"].get("id")
            results["trading_allowed"] = results["response"].get("trading_blocked") is False
        else:
            results["error"] = f"API returned status code {response.status_code}: {response.text}"
    
    except Exception as e:
        results["error"] = str(e)
    
    return results


def test_alpaca_market_data(use_paper: bool = True) -> Dict[str, Any]:
    """
    Test access to Alpaca market data
    
    Args:
        use_paper: Whether to use paper trading API
    
    Returns:
        Dictionary with results of the market data test
    """
    results = {
        "success": False,
        "bars_success": False,
        "quotes_success": False,
        "trades_success": False,
        "error": None,
        "is_paper": use_paper
    }
    
    try:
        # Determine which API key to use
        if use_paper and "ALPACA_PAPER_API_KEY" in os.environ and "ALPACA_PAPER_API_SECRET" in os.environ:
            api_key = os.environ["ALPACA_PAPER_API_KEY"]
            api_secret = os.environ["ALPACA_PAPER_API_SECRET"]
            base_url = os.environ.get("ALPACA_PAPER_API_BASE_URL", "https://paper-api.alpaca.markets")
        else:
            api_key = os.environ["ALPACA_API_KEY"]
            api_secret = os.environ["ALPACA_API_SECRET"]
            base_url = os.environ.get("ALPACA_API_BASE_URL", "https://api.alpaca.markets")
        
        # Set up headers
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        
        # Test symbols that should always have data
        test_symbols = ["AAPL", "MSFT", "SPY"]
        symbol_str = ",".join(test_symbols)
        
        # Test bars endpoint
        bars_url = f"{base_url}/v2/stocks/bars?symbols={symbol_str}&timeframe=1D&limit=1"
        logger.info(f"Testing market data bars: {bars_url}")
        
        bars_response = requests.get(bars_url, headers=headers)
        results["bars_success"] = bars_response.status_code == 200
        
        if results["bars_success"]:
            bars_data = bars_response.json()
            results["bars_data_sample"] = {
                symbol: bars_data.get(symbol, [])
                for symbol in test_symbols if symbol in bars_data
            }
        
        # Test quotes endpoint
        quotes_url = f"{base_url}/v2/stocks/quotes?symbols={symbol_str}"
        logger.info(f"Testing market data quotes: {quotes_url}")
        
        quotes_response = requests.get(quotes_url, headers=headers)
        results["quotes_success"] = quotes_response.status_code == 200
        
        # Test trades endpoint
        trades_url = f"{base_url}/v2/stocks/trades?symbols={symbol_str}&limit=1"
        logger.info(f"Testing market data trades: {trades_url}")
        
        trades_response = requests.get(trades_url, headers=headers)
        results["trades_success"] = trades_response.status_code == 200
        
        # Overall success if at least bars and quotes work
        results["success"] = results["bars_success"] and results["quotes_success"]
        
    except Exception as e:
        results["error"] = str(e)
    
    return results


def verify_broker_config(use_paper: bool = True, detailed: bool = False) -> Dict[str, Any]:
    """
    Verify the broker configuration
    
    Args:
        use_paper: Whether to use paper trading API
        detailed: Whether to include detailed information in results
    
    Returns:
        Dictionary with verification results
    """
    results = {
        "env_vars_check": None,
        "api_connection": None,
        "market_data": None,
        "overall_success": False,
        "is_paper": use_paper,
        "timestamp": time.time()
    }
    
    # Step 1: Check environment variables
    env_results = check_env_variables()
    results["env_vars_check"] = env_results
    
    # Step 2: Test API connection
    if env_results["required_vars_present"]:
        api_results = test_alpaca_api_connection(use_paper)
        results["api_connection"] = api_results
        
        # Step 3: Test market data access
        if api_results["success"]:
            market_results = test_alpaca_market_data(use_paper)
            results["market_data"] = market_results
            
            # Overall success if all checks pass
            results["overall_success"] = (
                env_results["required_vars_present"] and
                api_results["success"] and
                market_results["success"]
            )
    
    # Clean up sensitive data if not detailed
    if not detailed:
        if "env_vars_check" in results and "env_vars" in results["env_vars_check"]:
            results["env_vars_check"]["env_vars"] = {
                k: ("***MASKED***" if "SECRET" in k or "KEY" in k else v)
                for k, v in results["env_vars_check"]["env_vars"].items()
            }
    
    return results


def print_verification_results(results: Dict[str, Any]):
    """
    Print the verification results in a readable format
    
    Args:
        results: The verification results dictionary
    """
    print("\n=== BROKER CONFIGURATION VERIFICATION RESULTS ===")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}")
    print(f"Environment: {'Paper Trading' if results['is_paper'] else 'Live Trading'}")
    print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
    print("\n--- Environment Variables ---")
    
    env_check = results["env_vars_check"]
    if env_check["required_vars_present"]:
        print("Required Variables: ✅ PASSED")
    else:
        print(f"Required Variables: ❌ FAILED - Missing: {', '.join(env_check['missing_required'])}")
    
    if env_check["optional_vars_present"]:
        print("Optional Variables: ✅ PASSED")
    else:
        print(f"Optional Variables: ⚠️ WARNING - Missing: {', '.join(env_check['missing_optional'])}")
    
    if results["api_connection"] is not None:
        print("\n--- API Connection ---")
        api_check = results["api_connection"]
        
        if api_check["success"]:
            print(f"API Connection: ✅ PASSED")
            print(f"Account ID: {api_check['account_id']}")
            print(f"Trading Allowed: {'✅ Yes' if api_check['trading_allowed'] else '❌ No'}")
        else:
            print(f"API Connection: ❌ FAILED")
            print(f"Error: {api_check['error']}")
            print(f"Status Code: {api_check['status_code']}")
    
    if results["market_data"] is not None:
        print("\n--- Market Data Access ---")
        market_check = results["market_data"]
        
        if market_check["success"]:
            print(f"Market Data Access: ✅ PASSED")
            print(f"Bars Data: {'✅ Available' if market_check['bars_success'] else '❌ Unavailable'}")
            print(f"Quotes Data: {'✅ Available' if market_check['quotes_success'] else '❌ Unavailable'}")
            print(f"Trades Data: {'✅ Available' if market_check['trades_success'] else '❌ Unavailable'}")
        else:
            print(f"Market Data Access: ❌ FAILED")
            if market_check["error"]:
                print(f"Error: {market_check['error']}")
    
    print("\n--- Recommendation ---")
    if results["overall_success"]:
        print("✅ The broker configuration appears to be correct and working properly.")
    else:
        print("❌ The broker configuration has issues that need to be fixed:")
        
        if not env_check["required_vars_present"]:
            print(f"  - Set the missing environment variables: {', '.join(env_check['missing_required'])}")
        
        if results["api_connection"] is not None and not results["api_connection"]["success"]:
            print(f"  - Fix API connection issues: {results['api_connection']['error']}")
        
        if results["market_data"] is not None and not results["market_data"]["success"]:
            if results["market_data"]["error"]:
                print(f"  - Fix market data access issues: {results['market_data']['error']}")
            else:
                print("  - Check market data permissions for your API key")


def export_results(results: Dict[str, Any], output_file: str = None):
    """
    Export the verification results to a file
    
    Args:
        results: The verification results dictionary
        output_file: The file to export to (default: broker_config_verification_{timestamp}.json)
    """
    if output_file is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(results["timestamp"]))
        output_file = f"broker_config_verification_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results exported to {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Verify broker configuration')
    parser.add_argument('--live', action='store_true',
                        help='Verify live trading configuration (default is paper trading)')
    parser.add_argument('--detailed', action='store_true',
                        help='Include detailed information in results')
    parser.add_argument('--export', action='store_true',
                        help='Export results to a JSON file')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file for exported results')
    args = parser.parse_args()
    
    use_paper = not args.live
    
    logger.info(f"Verifying {'paper' if use_paper else 'live'} trading broker configuration...")
    
    results = verify_broker_config(use_paper=use_paper, detailed=args.detailed)
    
    print_verification_results(results)
    
    if args.export:
        export_results(results, args.output)
    
    return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main()) 