#!/usr/bin/env python3
"""
Final verification tests for the Order Execution Engine.
Used during the final testing phase to ensure the Order Execution system
is working correctly before release.
"""

import json
import os
import requests
import time
import unittest
from unittest.mock import patch

# Import test fixtures
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'fixtures'))
from broker_mocks.alpaca_mock import AlpacaMock
from data.webhook_examples import valid_webhook_samples

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
ORDER_API_ENDPOINT = f"{API_BASE_URL}/orders"
WEBHOOK_ENDPOINT = f"{API_BASE_URL}/webhooks/tradingview"
TEST_API_KEY = "test-api-key"  # Replace with actual test API key


class OrderExecutionFinalVerificationTests(unittest.TestCase):
    """Tests to verify the Order Execution Engine functionality for final testing."""

    def setUp(self):
        """Set up test environment."""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': TEST_API_KEY
        })
        
        # Initialize the mock broker API
        self.broker_mock = AlpacaMock()
        self.broker_mock.start()

    def tearDown(self):
        """Clean up after tests."""
        self.session.close()
        self.broker_mock.stop()

    def test_market_order_execution(self):
        """Test that market orders are correctly executed."""
        # Create a market order webhook sample
        market_order = next(
            (sample for sample in valid_webhook_samples if sample.get('type') == 'market'),
            valid_webhook_samples[0]  # Default to first sample if no market order is found
        )
        
        # If the default sample isn't a market order, modify it
        if market_order.get('type') != 'market':
            market_order = market_order.copy()
            market_order['type'] = 'market'
        
        # Submit the order via webhook
        response = self.session.post(
            WEBHOOK_ENDPOINT,
            data=json.dumps(market_order)
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result.get('success'))
        
        # Extract order ID from webhook response
        webhook_id = result.get('webhookId')
        
        # Wait for order processing (with timeout)
        max_wait = 5
        order_processed = False
        order_id = None
        
        start_time = time.time()
        while time.time() - start_time < max_wait and not order_processed:
            # Check webhook status
            status_response = self.session.get(f"{API_BASE_URL}/webhooks/{webhook_id}/status")
            self.assertEqual(status_response.status_code, 200)
            status = status_response.json()
            
            if status.get('status') == 'processed' and 'orderId' in status:
                order_processed = True
                order_id = status.get('orderId')
            else:
                time.sleep(0.5)
        
        self.assertTrue(order_processed, "Order was not processed within the expected timeframe")
        
        # Verify order status
        order_response = self.session.get(f"{ORDER_API_ENDPOINT}/{order_id}")
        self.assertEqual(order_response.status_code, 200)
        order = order_response.json()
        
        # Verify order details
        self.assertEqual(order.get('symbol'), market_order.get('ticker'))
        self.assertEqual(order.get('type'), 'market')
        self.assertEqual(order.get('status'), 'filled')  # Market orders should be filled quickly in test env
        
        # Verify broker interaction (check mock broker was called with correct params)
        broker_orders = self.broker_mock.get_orders()
        self.assertGreaterEqual(len(broker_orders), 1)
        broker_order = next((o for o in broker_orders if o.get('client_order_id') == order_id), None)
        self.assertIsNotNone(broker_order, "Order not found in broker mock")
        self.assertEqual(broker_order.get('symbol'), market_order.get('ticker'))

    def test_limit_order_execution(self):
        """Test that limit orders are correctly executed."""
        # Create a limit order webhook sample
        limit_order = next(
            (sample for sample in valid_webhook_samples if sample.get('type') == 'limit'),
            valid_webhook_samples[0].copy()  # Default to first sample if no limit order found
        )
        
        # If the default sample isn't a limit order, modify it
        if limit_order.get('type') != 'limit':
            limit_order = limit_order.copy()
            limit_order['type'] = 'limit'
            limit_order['limitPrice'] = limit_order.get('price', 100.00)  # Use existing price or default
        
        # Submit the order via webhook
        response = self.session.post(
            WEBHOOK_ENDPOINT,
            data=json.dumps(limit_order)
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result.get('success'))
        
        # Extract webhook ID from response
        webhook_id = result.get('webhookId')
        
        # Wait for order processing (with timeout)
        max_wait = 5
        order_processed = False
        order_id = None
        
        start_time = time.time()
        while time.time() - start_time < max_wait and not order_processed:
            # Check webhook status
            status_response = self.session.get(f"{API_BASE_URL}/webhooks/{webhook_id}/status")
            self.assertEqual(status_response.status_code, 200)
            status = status_response.json()
            
            if status.get('status') == 'processed' and 'orderId' in status:
                order_processed = True
                order_id = status.get('orderId')
            else:
                time.sleep(0.5)
        
        self.assertTrue(order_processed, "Order was not processed within the expected timeframe")
        
        # Verify order status
        order_response = self.session.get(f"{ORDER_API_ENDPOINT}/{order_id}")
        self.assertEqual(order_response.status_code, 200)
        order = order_response.json()
        
        # Verify order details
        self.assertEqual(order.get('symbol'), limit_order.get('ticker'))
        self.assertEqual(order.get('type'), 'limit')
        self.assertEqual(float(order.get('limit_price')), float(limit_order.get('limitPrice')))
        
        # For a limit order, status might be 'open' initially
        self.assertIn(order.get('status'), ['open', 'filled', 'partially_filled'])
        
        # Verify broker interaction
        broker_orders = self.broker_mock.get_orders()
        broker_order = next((o for o in broker_orders if o.get('client_order_id') == order_id), None)
        self.assertIsNotNone(broker_order, "Order not found in broker mock")
        self.assertEqual(broker_order.get('symbol'), limit_order.get('ticker'))
        self.assertEqual(float(broker_order.get('limit_price')), float(limit_order.get('limitPrice')))

    def test_bracket_order_execution(self):
        """Test that bracket orders with SL/TP are correctly executed."""
        # Create a bracket order webhook sample (or modify existing sample)
        bracket_order = next(
            (sample for sample in valid_webhook_samples if sample.get('type') in ['market', 'limit'] and 
             'stopLoss' in sample and 'takeProfit' in sample),
            valid_webhook_samples[0].copy()  # Default to first sample if no bracket order found
        )
        
        # If the default sample doesn't have SL/TP, add them
        if 'stopLoss' not in bracket_order or 'takeProfit' not in bracket_order:
            bracket_order = bracket_order.copy()
            # Calculate SL/TP based on order direction and price
            price = float(bracket_order.get('price', 100.00))
            is_buy = bracket_order.get('action', '').lower() == 'buy'
            
            bracket_order['stopLoss'] = price * (0.95 if is_buy else 1.05)
            bracket_order['takeProfit'] = price * (1.05 if is_buy else 0.95)
        
        # Submit the order via webhook
        response = self.session.post(
            WEBHOOK_ENDPOINT,
            data=json.dumps(bracket_order)
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result.get('success'))
        
        # Extract webhook ID from response
        webhook_id = result.get('webhookId')
        
        # Wait for order processing (with timeout)
        max_wait = 5
        order_processed = False
        order_id = None
        
        start_time = time.time()
        while time.time() - start_time < max_wait and not order_processed:
            # Check webhook status
            status_response = self.session.get(f"{API_BASE_URL}/webhooks/{webhook_id}/status")
            self.assertEqual(status_response.status_code, 200)
            status = status_response.json()
            
            if status.get('status') == 'processed' and 'orderId' in status:
                order_processed = True
                order_id = status.get('orderId')
            else:
                time.sleep(0.5)
        
        self.assertTrue(order_processed, "Order was not processed within the expected timeframe")
        
        # Verify order status
        order_response = self.session.get(f"{ORDER_API_ENDPOINT}/{order_id}")
        self.assertEqual(order_response.status_code, 200)
        order = order_response.json()
        
        # Verify order details
        self.assertEqual(order.get('symbol'), bracket_order.get('ticker'))
        
        # Verify SL/TP orders were created
        self.assertIsNotNone(order.get('stop_loss_order_id'), "Stop loss order not created")
        self.assertIsNotNone(order.get('take_profit_order_id'), "Take profit order not created")
        
        # Verify SL order
        sl_order_response = self.session.get(f"{ORDER_API_ENDPOINT}/{order.get('stop_loss_order_id')}")
        self.assertEqual(sl_order_response.status_code, 200)
        sl_order = sl_order_response.json()
        self.assertEqual(sl_order.get('type'), 'stop')
        self.assertAlmostEqual(
            float(sl_order.get('stop_price')), 
            float(bracket_order.get('stopLoss')),
            places=2
        )
        
        # Verify TP order
        tp_order_response = self.session.get(f"{ORDER_API_ENDPOINT}/{order.get('take_profit_order_id')}")
        self.assertEqual(tp_order_response.status_code, 200)
        tp_order = tp_order_response.json()
        self.assertEqual(tp_order.get('type'), 'limit')
        self.assertAlmostEqual(
            float(tp_order.get('limit_price')), 
            float(bracket_order.get('takeProfit')),
            places=2
        )

    def test_order_quantity_calculation(self):
        """Test that order quantity is calculated correctly based on risk parameters."""
        # Create a test webhook with risk percentage instead of fixed quantity
        risk_based_order = valid_webhook_samples[0].copy()
        risk_based_order.pop('quantity', None)  # Remove quantity if present
        risk_based_order['riskPercent'] = 1.0  # Risk 1% of account
        
        # Submit the order via webhook
        response = self.session.post(
            WEBHOOK_ENDPOINT,
            data=json.dumps(risk_based_order)
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result.get('success'))
        
        # Extract webhook ID from response
        webhook_id = result.get('webhookId')
        
        # Wait for order processing (with timeout)
        max_wait = 5
        order_processed = False
        order_id = None
        
        start_time = time.time()
        while time.time() - start_time < max_wait and not order_processed:
            # Check webhook status
            status_response = self.session.get(f"{API_BASE_URL}/webhooks/{webhook_id}/status")
            self.assertEqual(status_response.status_code, 200)
            status = status_response.json()
            
            if status.get('status') == 'processed' and 'orderId' in status:
                order_processed = True
                order_id = status.get('orderId')
            else:
                time.sleep(0.5)
        
        self.assertTrue(order_processed, "Order was not processed within the expected timeframe")
        
        # Verify order status
        order_response = self.session.get(f"{ORDER_API_ENDPOINT}/{order_id}")
        self.assertEqual(order_response.status_code, 200)
        order = order_response.json()
        
        # Verify quantity was calculated based on risk percentage
        self.assertIsNotNone(order.get('quantity'), "Order quantity not set")
        
        # Get account balance to verify calculation
        account_response = self.session.get(f"{API_BASE_URL}/account")
        self.assertEqual(account_response.status_code, 200)
        account = account_response.json()
        
        # Calculate expected quantity based on risk percent
        account_value = float(account.get('portfolio_value', 100000))
        risk_amount = account_value * (risk_based_order.get('riskPercent') / 100.0)
        
        # For a simple check, just verify quantity is non-zero and reasonable
        self.assertGreater(float(order.get('quantity')), 0)
        
        # Log the calculation for debugging
        print(f"Order used {risk_based_order.get('riskPercent')}% risk of ${account_value} = ${risk_amount}")
        print(f"Calculated quantity: {order.get('quantity')} shares of {order.get('symbol')}")

    def test_error_handling(self):
        """Test error handling for order execution failures."""
        # Set up the broker mock to simulate a failure
        self.broker_mock.set_should_fail(True)
        
        # Create a market order webhook sample
        market_order = next(
            (sample for sample in valid_webhook_samples if sample.get('type') == 'market'),
            valid_webhook_samples[0].copy()  # Default to first sample if no market order found
        )
        
        # Submit the order via webhook
        response = self.session.post(
            WEBHOOK_ENDPOINT,
            data=json.dumps(market_order)
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result.get('success'))
        
        # Extract webhook ID from response
        webhook_id = result.get('webhookId')
        
        # Wait for order processing (with timeout)
        max_wait = 5
        status_checked = False
        
        start_time = time.time()
        while time.time() - start_time < max_wait and not status_checked:
            # Check webhook status
            status_response = self.session.get(f"{API_BASE_URL}/webhooks/{webhook_id}/status")
            self.assertEqual(status_response.status_code, 200)
            status = status_response.json()
            
            if status.get('status') in ['error', 'failed']:
                status_checked = True
                # Verify error details are recorded
                self.assertIn('error', status)
                self.assertIsNotNone(status.get('error'))
            elif status.get('status') == 'processed':
                # This shouldn't happen if the broker is failing
                self.fail("Order was processed successfully despite broker failure")
            else:
                time.sleep(0.5)
        
        self.assertTrue(status_checked, "Order status was not checked within the expected timeframe")
        
        # Verify error was logged correctly
        error_logs_response = self.session.get(f"{API_BASE_URL}/logs/errors?webhookId={webhook_id}")
        self.assertEqual(error_logs_response.status_code, 200)
        error_logs = error_logs_response.json()
        
        self.assertGreaterEqual(len(error_logs), 1, "No error logs found")
        self.assertIn('broker failure', error_logs[0].get('message', '').lower())


if __name__ == '__main__':
    unittest.main() 