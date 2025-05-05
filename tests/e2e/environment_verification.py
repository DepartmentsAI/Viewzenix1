#!/usr/bin/env python
# Environment Verification Script for Viewzenix1
# May 10, 2025 - Created as part of contingency test plan

import argparse
import json
import logging
import os
import sys
import time
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"env_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("environment_verification")

# Default configuration
CONFIG = {
    "backend_url": "http://localhost:5000",
    "frontend_url": "http://localhost:3000",
    "broker_config_path": "./broker_config.json",
    "timeout": 10  # seconds
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Verify Viewzenix1 environment before testing")
    parser.add_argument("--backend-url", help=f"Backend API URL (default: {CONFIG['backend_url']})")
    parser.add_argument("--frontend-url", help=f"Frontend URL (default: {CONFIG['frontend_url']})")
    parser.add_argument("--broker-config", help=f"Path to broker config JSON (default: {CONFIG['broker_config_path']})")
    parser.add_argument("--timeout", type=int, help=f"Request timeout in seconds (default: {CONFIG['timeout']})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Update config with provided args
    if args.backend_url:
        CONFIG["backend_url"] = args.backend_url
    if args.frontend_url:
        CONFIG["frontend_url"] = args.frontend_url
    if args.broker_config:
        CONFIG["broker_config_path"] = args.broker_config
    if args.timeout:
        CONFIG["timeout"] = args.timeout
    
    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    return args

def check_backend_health():
    """Verify backend API health."""
    logger.info("Checking backend API health...")
    
    try:
        # Basic health check
        url = f"{CONFIG['backend_url']}/api/health"
        response = requests.get(url, timeout=CONFIG["timeout"])
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"Backend API is healthy: {health_data.get('status', 'unknown')}")
            
            # Detailed health check
            detailed_url = f"{CONFIG['backend_url']}/api/health/detailed"
            detailed_response = requests.get(detailed_url, timeout=CONFIG["timeout"])
            
            if detailed_response.status_code == 200:
                detailed_health = detailed_response.json()
                logger.debug(f"Detailed health: {json.dumps(detailed_health, indent=2)}")
                
                # Check components
                components = [
                    "database", 
                    "broker_service", 
                    "webhook_system", 
                    "risk_management"
                ]
                
                for component in components:
                    if component in detailed_health:
                        status = detailed_health[component].get("status", "unknown")
                        logger.info(f"Component '{component}' status: {status}")
                        
                        if status != "connected" and status != "healthy":
                            logger.warning(f"Component '{component}' may have issues!")
                
                return True, detailed_health
            else:
                logger.error(f"Detailed health check failed: {detailed_response.status_code}")
                return False, {"error": f"Detailed health check failed: {detailed_response.status_code}"}
        else:
            logger.error(f"Backend health check failed with status code: {response.status_code}")
            return False, {"error": f"Health check failed: {response.status_code}"}
    
    except requests.RequestException as e:
        logger.error(f"Failed to connect to backend API: {str(e)}")
        return False, {"error": str(e)}

def check_frontend_availability():
    """Verify frontend application availability."""
    logger.info("Checking frontend application availability...")
    
    try:
        response = requests.get(CONFIG["frontend_url"], timeout=CONFIG["timeout"])
        
        if response.status_code == 200:
            logger.info("Frontend application is accessible")
            return True, {"status": "accessible"}
        else:
            logger.error(f"Frontend check failed with status code: {response.status_code}")
            return False, {"error": f"Frontend check failed: {response.status_code}"}
    
    except requests.RequestException as e:
        logger.error(f"Failed to connect to frontend: {str(e)}")
        return False, {"error": str(e)}

def check_broker_connection():
    """Verify broker API connection."""
    logger.info("Checking broker API connection...")
    
    try:
        # Try to load broker config
        if not os.path.exists(CONFIG["broker_config_path"]):
            logger.error(f"Broker config file not found: {CONFIG['broker_config_path']}")
            return False, {"error": f"Broker config file not found: {CONFIG['broker_config_path']}"}
        
        with open(CONFIG["broker_config_path"], "r") as f:
            broker_config = json.load(f)
        
        # Check if the broker connection verification endpoint exists
        url = f"{CONFIG['backend_url']}/api/integration/verify-broker"
        payload = {"config": broker_config}
        
        response = requests.post(url, json=payload, timeout=CONFIG["timeout"])
        
        if response.status_code == 200:
            result = response.json()
            if result.get("connected", False):
                logger.info("Broker connection successful")
                return True, result
            else:
                logger.error(f"Broker connection failed: {result.get('error', 'Unknown error')}")
                return False, result
        else:
            logger.error(f"Broker verification failed with status code: {response.status_code}")
            return False, {"error": f"Broker verification failed: {response.status_code}"}
    
    except (requests.RequestException, json.JSONDecodeError, IOError) as e:
        logger.error(f"Error checking broker connection: {str(e)}")
        return False, {"error": str(e)}

def check_test_fixtures():
    """Verify required test fixtures are available."""
    logger.info("Checking test fixtures...")
    
    fixtures_dir = "./fixtures"
    required_fixtures = [
        "webhook_payloads.json",
        "order_templates.json",
        "risk_management_scenarios.json",
        "user_accounts.json"
    ]
    
    missing_fixtures = []
    for fixture in required_fixtures:
        fixture_path = os.path.join(fixtures_dir, fixture)
        if not os.path.exists(fixture_path):
            missing_fixtures.append(fixture)
            logger.error(f"Required fixture not found: {fixture_path}")
    
    if missing_fixtures:
        return False, {"missing_fixtures": missing_fixtures}
    else:
        logger.info("All required test fixtures are available")
        return True, {"status": "all_fixtures_available"}

def run_verification():
    """Run the complete environment verification."""
    logger.info("Starting environment verification...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENV", "development"),
        "components": {},
        "overall_status": "pending"
    }
    
    # Check backend health
    backend_success, backend_result = check_backend_health()
    results["components"]["backend"] = {
        "status": "pass" if backend_success else "fail",
        "details": backend_result
    }
    
    # Check frontend availability
    frontend_success, frontend_result = check_frontend_availability()
    results["components"]["frontend"] = {
        "status": "pass" if frontend_success else "fail",
        "details": frontend_result
    }
    
    # Check broker connection
    broker_success, broker_result = check_broker_connection()
    results["components"]["broker"] = {
        "status": "pass" if broker_success else "fail",
        "details": broker_result
    }
    
    # Check test fixtures
    fixtures_success, fixtures_result = check_test_fixtures()
    results["components"]["fixtures"] = {
        "status": "pass" if fixtures_success else "fail",
        "details": fixtures_result
    }
    
    # Determine overall status
    if backend_success and frontend_success and broker_success and fixtures_success:
        results["overall_status"] = "pass"
        logger.info("Environment verification PASSED")
    else:
        results["overall_status"] = "fail"
        logger.error("Environment verification FAILED - See component details")
    
    # Write results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"env_verification_results_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {results_file}")
    
    return results

def main():
    """Main entry point."""
    args = parse_args()
    results = run_verification()
    
    # Output summary
    print("\n" + "="*50)
    print("ENVIRONMENT VERIFICATION SUMMARY")
    print("="*50)
    
    for component, info in results["components"].items():
        status = "✅ PASS" if info["status"] == "pass" else "❌ FAIL"
        print(f"{component.upper()}: {status}")
    
    print("-"*50)
    print(f"OVERALL: {'✅ PASS' if results['overall_status'] == 'pass' else '❌ FAIL'}")
    print("="*50)
    
    # Return appropriate exit code
    if results["overall_status"] == "pass":
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 