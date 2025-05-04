#!/usr/bin/env python3
"""
Environment Verification Script for Viewzenix1

This script verifies that all required services and components are running
and accessible for testing. It checks:
1. Backend API availability
2. Frontend application availability
3. Broker API connectivity
4. Test fixtures availability

Usage:
    python environment_verification.py [--verbose]

Options:
    --verbose   Show detailed output for each check
"""

import argparse
import json
import os
import requests
import sys
from pathlib import Path
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:3000"
BROKER_API_URL = os.environ.get("BROKER_API_URL", "https://paper-api.alpaca.markets")
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

# ANSI color codes for output formatting
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def log_status(status, message, details=None, verbose=False):
    """Log a status message with color coding"""
    status_color = {
        "PASS": f"{GREEN}[PASS]{RESET}",
        "FAIL": f"{RED}[FAIL]{RESET}",
        "WARN": f"{YELLOW}[WARN]{RESET}",
        "INFO": f"{BLUE}[INFO]{RESET}"
    }.get(status, f"[{status}]")
    
    print(f"{status_color} {message}")
    if details and verbose:
        print(f"       {details}")

def check_backend_api(verbose=False):
    """Check if backend API is accessible"""
    try:
        # Try health endpoint
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            log_status("PASS", "Backend API health check successful", 
                       f"Status code: {response.status_code}, Response: {response.text[:100]}", verbose)
            return True
        else:
            log_status("FAIL", "Backend API returned non-200 status code", 
                       f"Status code: {response.status_code}, Response: {response.text[:100]}", verbose)
            return False
    except requests.exceptions.ConnectionError:
        log_status("FAIL", "Backend API connection refused", f"URL: {BACKEND_URL}", verbose)
        return False
    except Exception as e:
        log_status("FAIL", "Backend API check failed with exception", str(e), verbose)
        return False

def check_frontend_app(verbose=False):
    """Check if frontend application is accessible"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200 and "<title>Viewzenix Trading</title>" in response.text:
            log_status("PASS", "Frontend application is accessible", 
                       f"Status code: {response.status_code}", verbose)
            return True
        else:
            log_status("FAIL", "Frontend application check failed", 
                       f"Status code: {response.status_code}", verbose)
            return False
    except requests.exceptions.ConnectionError:
        log_status("FAIL", "Frontend application connection refused", f"URL: {FRONTEND_URL}", verbose)
        return False
    except Exception as e:
        log_status("FAIL", "Frontend application check failed with exception", str(e), verbose)
        return False

def check_broker_api(verbose=False):
    """Check if broker API credentials are configured and accessible"""
    api_key = os.environ.get("BROKER_API_KEY")
    api_secret = os.environ.get("BROKER_API_SECRET")
    
    if not api_key or not api_secret:
        log_status("FAIL", "Broker API credentials not configured", 
                   "BROKER_API_KEY or BROKER_API_SECRET environment variables not set", verbose)
        return False
    
    try:
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        response = requests.get(f"{BROKER_API_URL}/v2/account", headers=headers, timeout=10)
        
        if response.status_code == 200:
            log_status("PASS", "Broker API connection successful", 
                       f"Status code: {response.status_code}", verbose)
            return True
        else:
            log_status("FAIL", "Broker API returned non-200 status code", 
                       f"Status code: {response.status_code}, Response: {response.text[:100]}", verbose)
            return False
    except Exception as e:
        log_status("FAIL", "Broker API check failed with exception", str(e), verbose)
        return False

def check_test_fixtures(verbose=False):
    """Check if required test fixtures are available"""
    required_fixtures = [
        "data/tradingview_alerts.json",
        "data/webhook_schema.json",
        "data/test_orders.json",
        "broker_mocks/market_data.json"
    ]
    
    all_fixtures_available = True
    
    for fixture in required_fixtures:
        fixture_path = FIXTURES_DIR / fixture
        if fixture_path.exists():
            log_status("PASS", f"Test fixture available: {fixture}", fixture_path, verbose)
        else:
            log_status("FAIL", f"Test fixture missing: {fixture}", fixture_path, verbose)
            all_fixtures_available = False
    
    return all_fixtures_available

def main():
    parser = argparse.ArgumentParser(description="Verify environment readiness for Viewzenix1 testing")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print(f"{BOLD}Environment Verification - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print("=" * 80)
    
    # Run checks
    backend_ok = check_backend_api(args.verbose)
    frontend_ok = check_frontend_app(args.verbose)
    broker_ok = check_broker_api(args.verbose)
    fixtures_ok = check_test_fixtures(args.verbose)
    
    print("=" * 80)
    
    # Summary
    checks_passed = sum([backend_ok, frontend_ok, broker_ok, fixtures_ok])
    total_checks = 4
    
    print(f"{BOLD}Summary: {checks_passed}/{total_checks} checks passed{RESET}")
    
    if checks_passed == total_checks:
        print(f"{GREEN}All environment checks PASSED. Ready for testing!{RESET}")
        return 0
    else:
        print(f"{RED}Some environment checks FAILED. Testing environment is not ready.{RESET}")
        
        # Detailed result
        print("\nStatus by component:")
        print(f"  Backend API: {'OK' if backend_ok else 'FAILED'}")
        print(f"  Frontend Application: {'OK' if frontend_ok else 'FAILED'}")
        print(f"  Broker API: {'OK' if broker_ok else 'FAILED'}")
        print(f"  Test Fixtures: {'OK' if fixtures_ok else 'FAILED'}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 