#!/usr/bin/env python3
"""
Risk Management and Market Data Integration Validator

This utility script validates the integration between WebSocket market data streams,
risk management, and paper trading functionality. It can be used to verify that
all components are properly connected and working together.

Usage:
    python src/integration/utils/validate_integration.py --full-test
    python src/integration/utils/validate_integration.py --quick-test
"""

import os
import sys
import time
import argparse
import unittest
import logging
from typing import Dict, Any, List, Optional

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

# Import after path is set
try:
    from src.integration.utils.risk_market_data_validator import RiskMarketDataValidator
    from src.integration.adapters.alpaca_stream_adapter import AlpacaStreamAdapter
    from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    logger.error("Please make sure you're running this script from the project root.")
    sys.exit(1)


def run_unit_tests(test_pattern: str = "*") -> bool:
    """
    Run unit tests for the integration components
    
    Args:
        test_pattern: Pattern to match test files (default: all tests)
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    logger.info(f"Running integration unit tests matching pattern: {test_pattern}")
    
    # Configure test loader
    loader = unittest.TestLoader()
    
    # Set test directory
    test_dir = os.path.join(project_root, "tests", "unit", "integration")
    
    # Define a custom test pattern (default is test*.py)
    if test_pattern != "*":
        loader.testNamePattern = test_pattern
    
    # Discover and run tests
    suite = loader.discover(test_dir)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(suite)
    
    # Return True if all tests passed
    passed = (len(result.errors) == 0 and len(result.failures) == 0)
    
    if passed:
        logger.info("All unit tests passed successfully")
    else:
        logger.error(f"Unit tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
    
    return passed


def check_adapter_connectivity() -> bool:
    """
    Check if the adapters can connect to their respective APIs
    
    Returns:
        bool: True if all connections successful, False otherwise
    """
    logger.info("Checking adapter connectivity...")
    success = True
    
    # Test Alpaca Stream Adapter connectivity
    try:
        logger.info("Testing AlpacaStreamAdapter connectivity...")
        stream_adapter = AlpacaStreamAdapter(paper_trading=True)
        
        # Register a status callback
        status_results = {"connected": False}
        
        @stream_adapter.on_status
        def handle_status(connected, stream_type, message=None):
            status_results["connected"] = connected
            status_results["message"] = message
        
        # Try to connect
        stream_adapter.connect()
        
        # Wait briefly for connection
        time.sleep(3)
        
        # Check connection status
        if status_results.get("connected", False):
            logger.info("Successfully connected to Alpaca WebSocket stream")
        else:
            logger.error(f"Failed to connect to Alpaca WebSocket stream: {status_results.get('message', 'Unknown error')}")
            success = False
        
        # Disconnect
        stream_adapter.disconnect()
        
    except Exception as e:
        logger.error(f"Error testing AlpacaStreamAdapter: {e}")
        success = False
    
    # Test Paper Trading Adapter connectivity
    try:
        logger.info("Testing PaperTradingAdapter connectivity...")
        paper_adapter = PaperTradingAdapter(paper_trading=True)
        
        # Try to get account info
        account = paper_adapter.get_account()
        
        if account and account.get("id"):
            logger.info(f"Successfully connected to paper trading API: Account ID {account.get('id')}")
        else:
            logger.error("Failed to retrieve account information from paper trading API")
            success = False
            
    except Exception as e:
        logger.error(f"Error testing PaperTradingAdapter: {e}")
        success = False
    
    return success


def run_risk_validation(duration_seconds: int = 30) -> bool:
    """
    Run the risk market data validator
    
    Args:
        duration_seconds: How long to run the validation
        
    Returns:
        bool: True if validation succeeded, False otherwise
    """
    logger.info(f"Running risk market data validation (duration: {duration_seconds}s)...")
    
    try:
        # Create validator with mock risk manager
        validator = RiskMarketDataValidator(use_paper=True, use_mock_risk=True)
        
        # Run validation
        results = validator.run_validation(duration_seconds=duration_seconds)
        
        # Check results
        success = results.get("success", False)
        if success:
            logger.info("Risk market data validation succeeded")
        else:
            logger.error("Risk market data validation failed")
            
            # Log specific failures
            for key, value in results.items():
                if key.endswith("_success") and not value:
                    logger.error(f"  - {key}: Failed")
            
            # Log errors if any
            errors = results.get("errors", [])
            if errors:
                logger.error(f"Validation errors ({len(errors)}):")
                for i, error in enumerate(errors[:5]):
                    logger.error(f"  {i+1}. {error}")
                
                if len(errors) > 5:
                    logger.error(f"  ... and {len(errors) - 5} more errors")
        
        return success
        
    except Exception as e:
        logger.error(f"Error running risk market data validation: {e}")
        return False


def run_full_validation() -> bool:
    """
    Run a full validation of all integration components
    
    Returns:
        bool: True if all validations passed, False otherwise
    """
    results = {
        "unit_tests": False,
        "connectivity": False,
        "risk_validation": False
    }
    
    # Step 1: Run unit tests
    results["unit_tests"] = run_unit_tests()
    
    # Step 2: Check adapter connectivity
    results["connectivity"] = check_adapter_connectivity()
    
    # Step 3: Run risk validation
    results["risk_validation"] = run_risk_validation(duration_seconds=60)
    
    # Determine overall success
    overall_success = all(results.values())
    
    # Print summary
    logger.info("\n=== INTEGRATION VALIDATION SUMMARY ===")
    logger.info(f"Overall Success: {overall_success}")
    for key, value in results.items():
        status = "PASSED" if value else "FAILED"
        logger.info(f"{key}: {status}")
    
    return overall_success


def run_quick_validation() -> bool:
    """
    Run a quick validation (unit tests only)
    
    Returns:
        bool: True if validation passed, False otherwise
    """
    # Run unit tests only
    return run_unit_tests()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Validate integration between market data, risk management, and paper trading')
    parser.add_argument('--quick-test', action='store_true',
                        help='Run only unit tests (quick)')
    parser.add_argument('--full-test', action='store_true',
                        help='Run full validation including connectivity and risk tests')
    parser.add_argument('--risk-only', action='store_true',
                        help='Run only risk market data validation')
    parser.add_argument('--duration', type=int, default=30,
                        help='Duration for risk validation tests in seconds')
    args = parser.parse_args()
    
    start_time = time.time()
    success = False
    
    try:
        if args.risk_only:
            success = run_risk_validation(duration_seconds=args.duration)
        elif args.full_test:
            success = run_full_validation()
        else:  # Default to quick test
            success = run_quick_validation()
        
        # Measure time taken
        elapsed_time = time.time() - start_time
        logger.info(f"Validation completed in {elapsed_time:.2f} seconds")
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 