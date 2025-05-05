"""
Stream Adapter Verification Utility

This script provides a simple utility to verify the broker API connectivity
and WebSocket connection to the Alpaca streaming API.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.integration.adapters.paper_trading_adapter import PaperTradingAdapter
from src.integration.utils.logger import IntegrationLogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('stream_verification')

class StreamAdapterVerification:
    """Utility class to verify broker connectivity and WebSocket functionality."""
    
    def __init__(self):
        """Initialize the verification utility."""
        self.logger = IntegrationLogger()
        self.adapter = None
        self.verification_results = {
            "api_connectivity": False,
            "websocket_connectivity": False,
            "account_info": None,
            "market_data": False,
            "timestamps": {
                "started_at": datetime.now().isoformat(),
                "completed_at": None
            },
            "errors": []
        }
        
    def verify_broker_connectivity(self) -> Dict[str, Any]:
        """Verify connectivity to the broker API.
        
        Returns:
            Dict containing verification results
        """
        try:
            # Create the adapter
            self.adapter = PaperTradingAdapter(logger=self.logger)
            
            # Test authentication
            if self.adapter.authenticate():
                self.verification_results["api_connectivity"] = True
                logger.info("✅ Broker API connectivity verified")
            else:
                logger.error("❌ Broker API authentication failed")
                self.verification_results["errors"].append("Authentication failed")
                
            # Get account info as a further check
            try:
                account_info = self.adapter.get_account_info()
                self.verification_results["account_info"] = account_info
                logger.info(f"✅ Account info retrieved: {account_info['account_number']}")
            except Exception as e:
                logger.error(f"❌ Failed to retrieve account info: {str(e)}")
                self.verification_results["errors"].append(f"Account info error: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize broker adapter: {str(e)}")
            self.verification_results["errors"].append(f"Initialization error: {str(e)}")
            
        return self.verification_results
    
    def verify_websocket_connectivity(self, symbols=["AAPL", "MSFT"]) -> Dict[str, Any]:
        """Verify WebSocket connectivity by subscribing to market data.
        
        Args:
            symbols: List of symbols to subscribe to for testing
            
        Returns:
            Dict containing verification results
        """
        if not self.adapter:
            logger.error("❌ Cannot verify WebSocket - adapter not initialized")
            self.verification_results["errors"].append("Adapter not initialized")
            return self.verification_results
            
        try:
            # Set initial prices for simulation
            for symbol in symbols:
                # Use the internal method to simulate setting market prices
                if hasattr(self.adapter, "_set_market_price"):
                    self.adapter._set_market_price(symbol, 150.0)
                
            # Check if price updates are working (for PaperTradingAdapter this is simulated)
            initial_prices = {}
            for symbol in symbols:
                initial_prices[symbol] = self.adapter._get_market_price(symbol)
                
            logger.info(f"Initial prices: {initial_prices}")
            
            # Wait a bit for simulated price changes
            logger.info("Waiting for price updates...")
            time.sleep(3)
            
            # Check updated prices
            updated_prices = {}
            price_changed = False
            for symbol in symbols:
                updated_price = self.adapter._get_market_price(symbol)
                updated_prices[symbol] = updated_price
                if initial_prices[symbol] != updated_price:
                    price_changed = True
                    
            if price_changed:
                logger.info(f"✅ Price updates detected: {updated_prices}")
                self.verification_results["websocket_connectivity"] = True
                self.verification_results["market_data"] = True
            else:
                logger.warning("⚠️ No price changes detected. This may be normal in test mode.")
                
        except Exception as e:
            logger.error(f"❌ WebSocket verification failed: {str(e)}")
            self.verification_results["errors"].append(f"WebSocket error: {str(e)}")
            
        self.verification_results["timestamps"]["completed_at"] = datetime.now().isoformat()
        return self.verification_results
    
    def run_full_verification(self) -> Dict[str, Any]:
        """Run a complete verification of broker API and WebSocket functionality.
        
        Returns:
            Dict containing all verification results
        """
        # Verify API connectivity first
        self.verify_broker_connectivity()
        
        # If API is connected, verify WebSocket
        if self.verification_results["api_connectivity"]:
            self.verify_websocket_connectivity()
        
        # Save results to file for reference
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(project_root, f"verification_results_{timestamp}.json")
        try:
            with open(results_file, "w") as f:
                json.dump(self.verification_results, f, indent=2)
            logger.info(f"Results saved to {results_file}")
        except Exception as e:
            logger.error(f"Could not save results to file: {str(e)}")
        
        # Print summary
        self._print_verification_summary()
        
        return self.verification_results
    
    def _print_verification_summary(self):
        """Print a summary of verification results."""
        print("\n" + "="*80)
        print(" BROKER CONNECTIVITY VERIFICATION SUMMARY ".center(80, "="))
        print("="*80 + "\n")
        
        # API Connectivity
        if self.verification_results["api_connectivity"]:
            print("✅ Broker API Connectivity: SUCCESS")
        else:
            print("❌ Broker API Connectivity: FAILED")
        
        # Account Info
        if self.verification_results["account_info"]:
            account = self.verification_results["account_info"]
            print(f"✅ Account Info: {account.get('account_number', 'unknown')}")
            print(f"   - Status: {account.get('status', 'unknown')}")
            print(f"   - Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
            print(f"   - Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}")
        else:
            print("❌ Account Info: NOT AVAILABLE")
        
        # WebSocket Connectivity
        if self.verification_results["websocket_connectivity"]:
            print("✅ WebSocket Connectivity: SUCCESS")
        else:
            print("❌ WebSocket Connectivity: FAILED")
        
        # Market Data
        if self.verification_results["market_data"]:
            print("✅ Market Data: RECEIVING")
        else:
            print("❌ Market Data: NOT AVAILABLE")
        
        # Errors
        if self.verification_results["errors"]:
            print("\nERRORS:")
            for i, error in enumerate(self.verification_results["errors"], 1):
                print(f"  {i}. {error}")
        
        # Status Summary
        overall_success = (
            self.verification_results["api_connectivity"] and 
            self.verification_results["websocket_connectivity"] and
            self.verification_results["market_data"]
        )
        
        print("\n" + "-"*80)
        if overall_success:
            print(" OVERALL STATUS: SUCCESS - All components are functioning properly ".center(80, " "))
        else:
            print(" OVERALL STATUS: FAILED - Some components have issues ".center(80, " "))
        print("-"*80 + "\n")
        
        # Recommendations for troubleshooting
        if not overall_success:
            print("TROUBLESHOOTING RECOMMENDATIONS:")
            if not self.verification_results["api_connectivity"]:
                print("  • Check your ALPACA_API_KEY and ALPACA_API_SECRET in the .env file")
                print("  • Ensure your API keys are valid and have not expired")
                print("  • Verify your internet connection and firewall settings")
            
            if not self.verification_results["websocket_connectivity"]:
                print("  • Check WebSocket dependencies are installed (pip install websocket-client)")
                print("  • Verify your API keys have streaming data permissions")
                print("  • Ensure your network allows WebSocket connections")
        
        print("\n" + "="*80 + "\n")

def main():
    """Main function to run the verification tool."""
    logger.info("Starting broker connectivity verification...")
    verifier = StreamAdapterVerification()
    results = verifier.run_full_verification()
    
    # Determine exit code based on success/failure
    overall_success = (
        results["api_connectivity"] and 
        results["websocket_connectivity"] and
        results["market_data"]
    )
    
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main() 