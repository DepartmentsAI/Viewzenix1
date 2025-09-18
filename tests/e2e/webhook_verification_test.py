#!/usr/bin/env python
"""
Webhook Verification Test Script

This script tests the webhook receiver endpoint to verify it's properly configured
and responding to different types of webhook requests.

Usage:
  python webhook_verification_test.py

Options:
  --endpoint URL  The webhook endpoint URL (default: http://localhost:5000/api/v1/webhooks/tradingview)
  --verbose       Enable verbose output
"""

import sys
import json
import requests
import argparse
from pathlib import Path

# Import webhook examples
sys.path.insert(0, str(Path(__file__).parent / "fixtures" / "data"))
try:
    from webhook_examples import (
        VALID_TRADINGVIEW_ALERTS,
        INVALID_TRADINGVIEW_ALERTS, 
        COMPLEX_TRADINGVIEW_ALERTS,
        RISK_WEBHOOK_EXAMPLES
    )
except ImportError:
    print("Error: Cannot import webhook examples. Make sure webhook_examples.py exists in the fixtures/data directory.")
    sys.exit(1)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Webhook Verification Test")
    parser.add_argument(
        "--endpoint", 
        default="http://localhost:5000/api/v1/webhooks/tradingview",
        help="The webhook endpoint URL"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()

def test_webhook(endpoint, payload, expected_status=200, expected_result="success", description=""):
    """Send webhook request and verify response."""
    print(f"Testing: {description}")
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Get status code
        status_code = response.status_code
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            response_status = response_data.get("status", "unknown")
        except json.JSONDecodeError:
            response_data = {"raw": response.text}
            response_status = "unknown"
        
        # Print results
        result = "PASS" if status_code == expected_status and response_status == expected_result else "FAIL"
        print(f"  Result: {result}")
        print(f"  Status Code: {status_code} (Expected: {expected_status})")
        print(f"  Response Status: {response_status} (Expected: {expected_result})")
        
        if args.verbose:
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            print(f"  Response: {json.dumps(response_data, indent=2)}")
        
        print()
        
        return result == "PASS"
    except requests.RequestException as e:
        print(f"  Result: FAIL - Connection Error")
        print(f"  Error: {str(e)}")
        print()
        return False

def main():
    """Main test function."""
    args = parse_args()
    endpoint = args.endpoint
    
    print("===== Webhook Verification Test =====")
    print(f"Testing endpoint: {endpoint}")
    print()
    
    # Test health/status endpoint
    try:
        status_endpoint = endpoint.replace("webhooks/tradingview", "health")
        response = requests.get(status_endpoint)
        print(f"Health check: {'PASS' if response.status_code == 200 else 'FAIL'}")
        print(f"Status: {response.status_code}")
        if args.verbose and response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    except requests.RequestException as e:
        print(f"Health check: FAIL - {str(e)}")
        print()
    
    # Test valid webhooks
    print("===== Testing Valid Webhooks =====")
    valid_results = []
    for i, webhook in enumerate(VALID_TRADINGVIEW_ALERTS):
        valid_results.append(
            test_webhook(
                endpoint, 
                webhook, 
                expected_status=200, 
                expected_result="success",
                description=f"Valid TradingView Alert #{i+1}"
            )
        )
    
    # Test invalid webhooks
    print("===== Testing Invalid Webhooks =====")
    invalid_results = []
    for i, webhook in enumerate(INVALID_TRADINGVIEW_ALERTS):
        # We expect these to be rejected but still return 200 with status "error"
        invalid_results.append(
            test_webhook(
                endpoint, 
                webhook, 
                expected_status=200, 
                expected_result="error",
                description=f"Invalid TradingView Alert #{i+1}"
            )
        )
    
    # Test complex webhooks
    print("===== Testing Complex Webhooks =====")
    complex_results = []
    for i, webhook in enumerate(COMPLEX_TRADINGVIEW_ALERTS):
        complex_results.append(
            test_webhook(
                endpoint, 
                webhook, 
                expected_status=200, 
                expected_result="success",
                description=f"Complex TradingView Alert #{i+1}"
            )
        )
    
    # Test risk management webhooks
    print("===== Testing Risk Webhooks =====")
    risk_endpoint = endpoint.replace("webhooks/tradingview", "risk/webhook")
    risk_results = []
    risk_results.append(
        test_webhook(
            risk_endpoint, 
            RISK_WEBHOOK_EXAMPLES["success_case"], 
            expected_status=200, 
            expected_result="success",
            description="Risk Success Case"
        )
    )
    risk_results.append(
        test_webhook(
            risk_endpoint, 
            RISK_WEBHOOK_EXAMPLES["rejected_case"], 
            expected_status=200, 
            expected_result="rejected",
            description="Risk Rejection Case"
        )
    )
    
    # Summary
    print("===== Test Summary =====")
    total_tests = len(valid_results) + len(invalid_results) + len(complex_results) + len(risk_results)
    passed_tests = sum(valid_results) + sum(invalid_results) + sum(complex_results) + sum(risk_results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
    
    if passed_tests == total_tests:
        print("\nWEBHOOK VERIFICATION: PASSED ✅")
        return 0
    else:
        print("\nWEBHOOK VERIFICATION: FAILED ❌")
        return 1

if __name__ == "__main__":
    args = parse_args()
    sys.exit(main()) 