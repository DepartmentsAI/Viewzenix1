#!/usr/bin/env python3
"""
System Readiness Check Script

This script performs a comprehensive health check of all Viewzenix1 system components
to verify they are operational before beginning the final testing phase.
Run this script at the start of the testing day to confirm environment readiness.
"""

import os
import sys
import json
import time
import requests
import datetime
import argparse
import subprocess
from typing import Dict, List, Tuple, Optional

# Configuration
DEFAULT_CONFIG = {
    "backend_api_url": "http://localhost:5000/api/v1",
    "frontend_url": "http://localhost:3000",
    "webhook_receiver_url": "http://localhost:5000/api/v1/webhooks/tradingview",
    "order_execution_url": "http://localhost:5000/api/v1/orders",
    "risk_management_url": "http://localhost:5000/api/v1/risk/params",
    "database_connection_string": "postgresql://user:password@localhost:5432/viewzenix_test",
    "broker_api_url": "https://paper-api.alpaca.markets",
    "broker_api_key": os.environ.get("ALPACA_API_KEY", ""),
    "broker_api_secret": os.environ.get("ALPACA_API_SECRET", ""),
    "log_path": "./system_readiness_check.log"
}

# ANSI color codes for console output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

class SystemReadinessCheck:
    """
    Performs comprehensive system health checks for the Viewzenix1 application.
    """
    
    def __init__(self, config: Dict):
        """Initialize with config settings."""
        self.config = config
        self.results = {
            "backend_api": {"status": "NOT_CHECKED", "details": ""},
            "frontend": {"status": "NOT_CHECKED", "details": ""},
            "webhook_receiver": {"status": "NOT_CHECKED", "details": ""},
            "order_execution": {"status": "NOT_CHECKED", "details": ""},
            "risk_management": {"status": "NOT_CHECKED", "details": ""},
            "database": {"status": "NOT_CHECKED", "details": ""},
            "broker_api": {"status": "NOT_CHECKED", "details": ""},
            "test_fixtures": {"status": "NOT_CHECKED", "details": ""},
        }
        self.log_file = open(config["log_path"], "w")
    
    def log(self, message: str):
        """Log message to file and console."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_file.write(log_message + "\n")
        self.log_file.flush()
        print(log_message)
    
    def check_backend_api(self) -> bool:
        """
        Check if the backend API is responding.
        """
        self.log("Checking Backend API...")
        try:
            response = requests.get(f"{self.config['backend_api_url']}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                version = data.get("version", "unknown")
                self.results["backend_api"] = {
                    "status": "PASS", 
                    "details": f"Backend API v{version} is operational"
                }
                return True
            else:
                self.results["backend_api"] = {
                    "status": "FAIL", 
                    "details": f"Backend API responded with status code {response.status_code}"
                }
                return False
        except Exception as e:
            self.results["backend_api"] = {
                "status": "FAIL", 
                "details": f"Failed to connect to Backend API: {str(e)}"
            }
            return False
    
    def check_frontend(self) -> bool:
        """
        Check if the frontend is accessible.
        """
        self.log("Checking Frontend...")
        try:
            response = requests.get(self.config['frontend_url'], timeout=5)
            if response.status_code == 200:
                self.results["frontend"] = {
                    "status": "PASS", 
                    "details": "Frontend is accessible"
                }
                return True
            else:
                self.results["frontend"] = {
                    "status": "FAIL", 
                    "details": f"Frontend responded with status code {response.status_code}"
                }
                return False
        except Exception as e:
            self.results["frontend"] = {
                "status": "FAIL", 
                "details": f"Failed to connect to Frontend: {str(e)}"
            }
            return False
    
    def check_webhook_receiver(self) -> bool:
        """
        Check if the webhook receiver is operational.
        """
        self.log("Checking Webhook Receiver...")
        try:
            # We'll use a HEAD request to check if the endpoint exists without triggering an actual webhook
            response = requests.head(self.config['webhook_receiver_url'], timeout=5)
            if response.status_code in [200, 204, 404, 405]:  # Common status codes when endpoint exists
                self.results["webhook_receiver"] = {
                    "status": "PASS", 
                    "details": "Webhook receiver endpoint is responding"
                }
                return True
            else:
                self.results["webhook_receiver"] = {
                    "status": "FAIL", 
                    "details": f"Webhook receiver responded with status code {response.status_code}"
                }
                return False
        except Exception as e:
            self.results["webhook_receiver"] = {
                "status": "FAIL", 
                "details": f"Failed to connect to Webhook receiver: {str(e)}"
            }
            return False
    
    def check_order_execution(self) -> bool:
        """
        Check if the order execution service is operational.
        """
        self.log("Checking Order Execution Service...")
        try:
            # We'll use a GET request to check the orders endpoint
            response = requests.get(
                self.config['order_execution_url'], 
                params={"status": "all", "limit": 1},
                timeout=5
            )
            if response.status_code in [200, 401, 403]:  # Even auth errors indicate service is up
                self.results["order_execution"] = {
                    "status": "PASS", 
                    "details": "Order execution service is responding"
                }
                return True
            else:
                self.results["order_execution"] = {
                    "status": "FAIL", 
                    "details": f"Order execution service responded with status code {response.status_code}"
                }
                return False
        except Exception as e:
            self.results["order_execution"] = {
                "status": "FAIL", 
                "details": f"Failed to connect to Order execution service: {str(e)}"
            }
            return False
    
    def check_risk_management(self) -> bool:
        """
        Check if the risk management service is operational.
        """
        self.log("Checking Risk Management Service...")
        try:
            response = requests.get(self.config['risk_management_url'], timeout=5)
            if response.status_code in [200, 401, 403]:  # Even auth errors indicate service is up
                self.results["risk_management"] = {
                    "status": "PASS", 
                    "details": "Risk management service is responding"
                }
                return True
            else:
                self.results["risk_management"] = {
                    "status": "FAIL", 
                    "details": f"Risk management service responded with status code {response.status_code}"
                }
                return False
        except Exception as e:
            self.results["risk_management"] = {
                "status": "FAIL",

                "details": f"Failed to connect to Risk management service: {str(e)}"
            }
            return False
    
    def check_database(self) -> bool:
        """
        Check if the database is accessible.
        """
        self.log("Checking Database Connection...")
        try:
            # We'll try to run a simple query to check if the database is up
            # This requires psycopg2 to be installed
            import psycopg2
            conn = psycopg2.connect(self.config['database_connection_string'])
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            self.results["database"] = {
                "status": "PASS", 
                "details": "Database connection successful"
            }
            return True
        except ImportError:
            self.results["database"] = {
                "status": "WARN", 
                "details": "Could not check database - psycopg2 package not installed"
            }
            return False
        except Exception as e:
            self.results["database"] = {
                "status": "FAIL", 
                "details": f"Database connection failed: {str(e)}"
            }
            return False
    
    def check_broker_api(self) -> bool:
        """
        Check if the broker API connection is working.
        """
        self.log("Checking Broker API Connection...")
        
        if not self.config['broker_api_key'] or not self.config['broker_api_secret']:
            self.results["broker_api"] = {
                "status": "WARN", 
                "details": "Broker API credentials not provided in configuration"
            }
            return False
        
        try:
            headers = {
                'APCA-API-KEY-ID': self.config['broker_api_key'],
                'APCA-API-SECRET-KEY': self.config['broker_api_secret']
            }
            response = requests.get(f"{self.config['broker_api_url']}/v2/account", headers=headers, timeout=5)
            
            if response.status_code == 200:
                account_data = response.json()
                self.results["broker_api"] = {
                    "status": "PASS", 
                    "details": f"Broker API connection successful - Account Status: {account_data.get('status', 'Unknown')}"
                }
                return True
            else:
                self.results["broker_api"] = {
                    "status": "FAIL", 
                    "details": f"Broker API responded with status code {response.status_code}: {response.text}"
                }
                return False
        except Exception as e:
            self.results["broker_api"] = {
                "status": "FAIL", 
                "details": f"Failed to connect to Broker API: {str(e)}"
            }
            return False
    
    def check_test_fixtures(self) -> bool:
        """
        Check if required test fixtures are present.
        """
        self.log("Checking Test Fixtures...")
        
        # Define the paths to check
        fixtures_paths = [
            "./tests/e2e/fixtures/data",
            "./tests/e2e/fixtures/broker_mocks"
        ]
        
        missing_paths = []
        
        for path in fixtures_paths:
            if not os.path.exists(path):
                missing_paths.append(path)
        
        if missing_paths:
            self.results["test_fixtures"] = {
                "status": "FAIL", 
                "details": f"Missing test fixture directories: {', '.join(missing_paths)}"
            }
            return False
        
        # Check if we have webhook examples
        webhook_examples_path = "./tests/e2e/fixtures/data/webhook_examples.py"
        if not os.path.exists(webhook_examples_path):
            self.results["test_fixtures"] = {
                "status": "FAIL", 
                "details": f"Missing webhook examples file: {webhook_examples_path}"
            }
            return False
        
        self.results["test_fixtures"] = {
            "status": "PASS", 
            "details": "All required test fixtures are present"
        }
        return True
    
    def run_all_checks(self) -> bool:
        """
        Run all system checks and return overall status.
        """
        self.log(f"{BOLD}Starting Viewzenix1 System Readiness Check{RESET}")
        self.log(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=====================================")
        
        checks = [
            self.check_backend_api,
            self.check_frontend,
            self.check_webhook_receiver,
            self.check_order_execution,
            self.check_risk_management,
            self.check_database,
            self.check_broker_api,
            self.check_test_fixtures
        ]
        
        all_passed = True
        
        for check in checks:
            if not check():
                all_passed = False
        
        return all_passed
    
    def display_results(self):
        """
        Display the results of all checks.
        """
        self.log("\n=====================================")
        self.log(f"{BOLD}System Readiness Check Results{RESET}")
        self.log("=====================================")
        
        fail_count = 0
        warn_count = 0
        pass_count = 0
        
        for component, result in self.results.items():
            status = result["status"]
            details = result["details"]
            
            if status == "PASS":
                pass_count += 1
                status_display = f"{GREEN}PASS{RESET}"
            elif status == "WARN":
                warn_count += 1
                status_display = f"{YELLOW}WARN{RESET}"
            elif status == "FAIL":
                fail_count += 1
                status_display = f"{RED}FAIL{RESET}"
            else:
                status_display = status
            
            self.log(f"{BOLD}{component.replace('_', ' ').upper()}{RESET}: {status_display}")
            self.log(f"  {details}")
        
        self.log("\n=====================================")
        self.log(f"{BOLD}Summary:{RESET}")
        self.log(f"  {GREEN}Pass:{RESET} {pass_count}")
        self.log(f"  {YELLOW}Warnings:{RESET} {warn_count}")
        self.log(f"  {RED}Failures:{RESET} {fail_count}")
        
        if fail_count > 0:
            self.log(f"\n{RED}❌ System is NOT ready for testing! Please address the failures.{RESET}")
            return False
        elif warn_count > 0:
            self.log(f"\n{YELLOW}⚠️ System has warnings but may be able to proceed with testing.{RESET}")
            return True
        else:
            self.log(f"\n{GREEN}✅ System is ready for testing! All checks passed.{RESET}")
            return True
    
    def close(self):
        """Close log file."""
        if self.log_file:
            self.log_file.close()

def main():
    """Main function to run the system readiness check."""
    parser = argparse.ArgumentParser(description='Check system readiness for Viewzenix1 testing.')
    parser.add_argument('--config', type=str, help='Path to config JSON file')
    args = parser.parse_args()
    
    config = DEFAULT_CONFIG
    
    if args.config:
        try:
            with open(args.config, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration.")
    
    checker = SystemReadinessCheck(config)
    
    try:
        checker.run_all_checks()
        success = checker.display_results()
        checker.close()
        
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nCheck interrupted by user")
        checker.close()
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during system check: {e}")
        checker.close()
        sys.exit(1)

if __name__ == "__main__":
    main() 