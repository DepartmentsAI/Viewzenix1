#!/usr/bin/env python
"""
Environment Health Check

This script performs a quick health check of all essential environment components
for the 2:00 PM verification milestone.

Usage:
  python environment_health_check.py

Options:
  --backend-url URL       URL for backend API (default: http://localhost:5000)
  --frontend-url URL      URL for frontend application (default: http://localhost:3000)
  --verbose               Enable verbose output
  --output FILE           Save results to FILE in JSON format
"""

import sys
import json
import argparse
import time
import datetime
import requests
from pathlib import Path

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Environment Health Check")
    parser.add_argument(
        "--backend-url", 
        default="http://localhost:5000",
        help="URL for backend API"
    )
    parser.add_argument(
        "--frontend-url", 
        default="http://localhost:3000",
        help="URL for frontend application"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--output",
        help="Save results to FILE in JSON format"
    )
    return parser.parse_args()

def check_backend_health(backend_url, verbose=False):
    """Check the backend API health."""
    health_url = f"{backend_url}/api/v1/health"
    webhook_url = f"{backend_url}/api/v1/webhooks/tradingview"
    orders_url = f"{backend_url}/api/v1/orders"
    risk_url = f"{backend_url}/api/v1/risk/params"
    
    results = {}
    
    try:
        # Check API health endpoint
        print("Checking backend API health...")
        start_time = time.time()
        response = requests.get(health_url, timeout=5)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Backend API health check: PASS (latency: {latency:.2f}s)")
            try:
                health_data = response.json()
                if verbose:
                    print(f"   Version: {health_data.get('version', 'unknown')}")
                    print(f"   Status: {health_data.get('status', 'unknown')}")
                results["health"] = {
                    "status": "PASS",
                    "status_code": response.status_code,
                    "latency": latency,
                    "data": health_data
                }
            except json.JSONDecodeError:
                results["health"] = {
                    "status": "WARN",
                    "status_code": response.status_code,
                    "latency": latency,
                    "data": {"warning": "Response not valid JSON"}
                }
        else:
            print(f"❌ Backend API health check: FAIL (status code: {response.status_code})")
            results["health"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "latency": latency
            }
    except requests.RequestException as e:
        print(f"❌ Backend API health check: FAIL")
        print(f"   Error: {str(e)}")
        results["health"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Check webhook endpoint
    try:
        print("Checking webhook receiver...")
        start_time = time.time()
        response = requests.options(webhook_url, timeout=5)
        latency = time.time() - start_time
        
        if response.status_code in [200, 204]:
            print(f"✅ Webhook receiver check: PASS (latency: {latency:.2f}s)")
            results["webhook"] = {
                "status": "PASS",
                "status_code": response.status_code,
                "latency": latency
            }
        else:
            print(f"❌ Webhook receiver check: FAIL (status code: {response.status_code})")
            results["webhook"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "latency": latency
            }
    except requests.RequestException as e:
        print(f"❌ Webhook receiver check: FAIL")
        print(f"   Error: {str(e)}")
        results["webhook"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Check orders endpoint
    try:
        print("Checking order execution service...")
        start_time = time.time()
        response = requests.get(orders_url, timeout=5)
        latency = time.time() - start_time
        
        if response.status_code in [200, 401, 403]:  # Might require auth, so 401/403 is acceptable
            status = "PASS" if response.status_code == 200 else "WARN"
            status_msg = "PASS" if status == "PASS" else "WARN (may require authentication)"
            print(f"✅ Order execution service check: {status_msg} (latency: {latency:.2f}s)")
            results["orders"] = {
                "status": status,
                "status_code": response.status_code,
                "latency": latency
            }
        else:
            print(f"❌ Order execution service check: FAIL (status code: {response.status_code})")
            results["orders"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "latency": latency
            }
    except requests.RequestException as e:
        print(f"❌ Order execution service check: FAIL")
        print(f"   Error: {str(e)}")
        results["orders"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Check risk management endpoint
    try:
        print("Checking risk management service...")
        start_time = time.time()
        response = requests.get(risk_url, timeout=5)
        latency = time.time() - start_time
        
        if response.status_code in [200, 401, 403]:  # Might require auth, so 401/403 is acceptable
            status = "PASS" if response.status_code == 200 else "WARN"
            status_msg = "PASS" if status == "PASS" else "WARN (may require authentication)"
            print(f"✅ Risk management service check: {status_msg} (latency: {latency:.2f}s)")
            results["risk"] = {
                "status": status,
                "status_code": response.status_code,
                "latency": latency
            }
        else:
            print(f"❌ Risk management service check: FAIL (status code: {response.status_code})")
            results["risk"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "latency": latency
            }
    except requests.RequestException as e:
        print(f"❌ Risk management service check: FAIL")
        print(f"   Error: {str(e)}")
        results["risk"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    return results

def check_frontend_health(frontend_url, verbose=False):
    """Check the frontend application health."""
    results = {}
    
    try:
        print("Checking frontend application...")
        start_time = time.time()
        response = requests.get(frontend_url, timeout=5)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Frontend application check: PASS (latency: {latency:.2f}s)")
            if verbose:
                content_length = len(response.content)
                content_type = response.headers.get('Content-Type', 'unknown')
                print(f"   Content-Type: {content_type}")
                print(f"   Content-Length: {content_length} bytes")
            results["frontend"] = {
                "status": "PASS",
                "status_code": response.status_code,
                "latency": latency,
                "content_type": response.headers.get('Content-Type', 'unknown'),
                "content_length": len(response.content)
            }
        else:
            print(f"❌ Frontend application check: FAIL (status code: {response.status_code})")
            results["frontend"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "latency": latency
            }
    except requests.RequestException as e:
        print(f"❌ Frontend application check: FAIL")
        print(f"   Error: {str(e)}")
        results["frontend"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    return results

def check_test_fixtures():
    """Check test fixtures availability."""
    results = {}
    
    webhook_path = Path(__file__).parent / "fixtures" / "data" / "webhook_examples.py"
    webhook_json_path = Path(__file__).parent / "fixtures" / "data" / "webhook_examples.json"
    
    print("Checking test fixtures...")
    
    # Check webhook examples
    if webhook_path.exists():
        print(f"✅ Webhook examples (Python): PASS")
        results["webhook_examples_py"] = {
            "status": "PASS",
            "path": str(webhook_path)
        }
    else:
        print(f"❌ Webhook examples (Python): FAIL (file not found)")
        results["webhook_examples_py"] = {
            "status": "FAIL",
            "error": "File not found"
        }
    
    # Check webhook examples JSON
    if webhook_json_path.exists():
        print(f"✅ Webhook examples (JSON): PASS")
        results["webhook_examples_json"] = {
            "status": "PASS",
            "path": str(webhook_json_path)
        }
    else:
        print(f"❌ Webhook examples (JSON): FAIL (file not found)")
        results["webhook_examples_json"] = {
            "status": "FAIL",
            "error": "File not found"
        }
    
    return results

def check_database():
    """Check database connection."""
    results = {}
    
    try:
        import psycopg2
        print(f"✅ Database driver check: PASS (psycopg2 installed)")
        results["database_driver"] = {
            "status": "PASS",
            "driver": "psycopg2"
        }
        
        # We won't actually try to connect to the database here
        # as that would require credentials
        print("ℹ️ Database connection: SKIP (requires credentials)")
        results["database_connection"] = {
            "status": "SKIP",
            "reason": "Requires credentials"
        }
    except ImportError:
        print(f"❌ Database driver check: FAIL (psycopg2 not installed)")
        results["database_driver"] = {
            "status": "FAIL",
            "error": "psycopg2 package not installed"
        }
        results["database_connection"] = {
            "status": "SKIP",
            "reason": "Driver not available"
        }
    
    return results

def check_broker_api():
    """Check broker API configuration."""
    results = {}
    
    # We won't actually try to connect to broker APIs here
    # as that would require credentials
    print("ℹ️ Broker API check: SKIP (requires credentials)")
    results["broker_api"] = {
        "status": "SKIP",
        "reason": "Requires credentials"
    }
    
    return results

def main():
    """Main function."""
    args = parse_args()
    
    print("\n===== Viewzenix1 Environment Health Check =====")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("================================================\n")
    
    # Run all checks
    results = {}
    results["backend"] = check_backend_health(args.backend_url, args.verbose)
    results["frontend"] = check_frontend_health(args.frontend_url, args.verbose)
    results["fixtures"] = check_test_fixtures()
    results["database"] = check_database()
    results["broker"] = check_broker_api()
    
    # Summarize results
    print("\n===== Health Check Summary =====")
    total_checks = 0
    passed_checks = 0
    warned_checks = 0
    skipped_checks = 0
    failed_checks = 0
    
    for category, checks in results.items():
        for component, data in checks.items():
            total_checks += 1
            status = data.get("status", "UNKNOWN")
            if status == "PASS":
                passed_checks += 1
            elif status == "WARN":
                warned_checks += 1
            elif status == "SKIP":
                skipped_checks += 1
            else:
                failed_checks += 1
    
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Warnings: {warned_checks}")
    print(f"Skipped: {skipped_checks}")
    print(f"Failed: {failed_checks}")
    
    if failed_checks == 0 and warned_checks == 0:
        print("\nENVIRONMENT HEALTH CHECK: PASSED ✅")
        overall_status = "PASS"
    elif failed_checks == 0:
        print("\nENVIRONMENT HEALTH CHECK: PASSED WITH WARNINGS ⚠️")
        overall_status = "WARN"
    else:
        print("\nENVIRONMENT HEALTH CHECK: FAILED ❌")
        print(f"Failed checks: {failed_checks}")
        overall_status = "FAIL"
    
    # Save results if requested
    if args.output:
        output_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "overall_status": overall_status,
            "summary": {
                "total": total_checks,
                "passed": passed_checks,
                "warnings": warned_checks,
                "skipped": skipped_checks,
                "failed": failed_checks
            },
            "results": results
        }
        
        try:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"Results saved to {args.output}")
        except Exception as e:
            print(f"Error saving results: {str(e)}")
    
    return 0 if failed_checks == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 