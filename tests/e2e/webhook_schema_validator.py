#!/usr/bin/env python
"""
Webhook Schema Validator

This script validates the webhook example data against the defined backend API schema
to ensure that our test data is compatible with the actual API requirements.

Usage:
  python webhook_schema_validator.py

Options:
  --schema PATH    Path to the API schema file (default: ../../docs/schemas/tradingview-alert.json)
  --verbose        Enable verbose output
"""

import sys
import json
import argparse
from pathlib import Path
from jsonschema import validate, ValidationError, SchemaError

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
    parser = argparse.ArgumentParser(description="Webhook Schema Validator")
    parser.add_argument(
        "--schema", 
        default="../../docs/schemas/tradingview-alert.json",
        help="Path to the API schema file"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()

def load_schema(schema_path):
    """Load the JSON schema from a file."""
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found at {schema_path}")
        print("Falling back to a basic schema validation...")
        # Create a basic schema as fallback
        return {
            "type": "object",
            "required": ["strategy"],
            "properties": {
                "strategy": {
                    "type": "object",
                    "required": ["order_action", "order_price"],
                    "properties": {
                        "order_action": {"type": "string"},
                        "order_price": {"type": "number"},
                        "position_size": {"type": "number"},
                        "ticker": {"type": "string"}
                    }
                }
            }
        }
    except json.JSONDecodeError:
        print(f"Error: Schema file is not valid JSON: {schema_path}")
        sys.exit(1)

def validate_webhook(schema, webhook, description, verbose=False):
    """Validate a webhook against the schema."""
    try:
        validate(instance=webhook, schema=schema)
        print(f"✅ {description}: Valid")
        if verbose:
            print(f"   Data: {json.dumps(webhook, indent=2)}")
        return True
    except ValidationError as e:
        print(f"❌ {description}: Invalid")
        print(f"   Error: {e.message}")
        if verbose:
            print(f"   Data: {json.dumps(webhook, indent=2)}")
            print(f"   Schema path: {' -> '.join([str(path) for path in e.path])}")
        return False
    except SchemaError as e:
        print(f"❌ Schema error: {e.message}")
        return False

def main():
    """Main function."""
    args = parse_args()
    schema = load_schema(args.schema)
    
    print("\n===== Validating Webhook Examples Against Schema =====\n")
    
    # Validate valid webhooks
    print("== Valid TradingView Alerts (Expected to be valid) ==")
    valid_results = []
    for i, webhook in enumerate(VALID_TRADINGVIEW_ALERTS):
        result = validate_webhook(schema, webhook, f"Valid Alert #{i+1}", args.verbose)
        valid_results.append(result)
    
    # Validate invalid webhooks
    print("\n== Invalid TradingView Alerts (Expected to be invalid) ==")
    invalid_results = []
    for i, webhook in enumerate(INVALID_TRADINGVIEW_ALERTS):
        # For these, we expect validation to fail, so we invert the result
        result = not validate_webhook(schema, webhook, f"Invalid Alert #{i+1}", args.verbose)
        invalid_results.append(result)
    
    # Validate complex webhooks
    print("\n== Complex TradingView Alerts (Expected to be valid) ==")
    complex_results = []
    for i, webhook in enumerate(COMPLEX_TRADINGVIEW_ALERTS):
        result = validate_webhook(schema, webhook, f"Complex Alert #{i+1}", args.verbose)
        complex_results.append(result)
    
    # Summary
    print("\n===== Validation Summary =====")
    valid_count = sum(valid_results)
    invalid_count = sum(invalid_results)
    complex_count = sum(complex_results)
    total_valid = len(valid_results)
    total_invalid = len(invalid_results)
    total_complex = len(complex_results)
    
    print(f"Valid Alerts: {valid_count}/{total_valid} pass")
    print(f"Invalid Alerts: {invalid_count}/{total_invalid} pass (inverted check)")
    print(f"Complex Alerts: {complex_count}/{total_complex} pass")
    
    total_pass = valid_count + invalid_count + complex_count
    total_tests = total_valid + total_invalid + total_complex
    
    print(f"\nOverall: {total_pass}/{total_tests} tests passed ({total_pass/total_tests*100:.1f}%)")
    
    if total_pass == total_tests:
        print("\nWEBHOOK SCHEMA VALIDATION: PASSED ✅")
        return 0
    else:
        print("\nWEBHOOK SCHEMA VALIDATION: FAILED ❌")
        print("Some webhook examples do not match the expected schema.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 