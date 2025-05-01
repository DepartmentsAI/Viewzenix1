#!/usr/bin/env python3
"""
Final verification tests for the Webhook system.
Used during the final testing phase to ensure webhook functionality
is working correctly before release.
"""

import json
import os
import requests
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import test fixtures
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'fixtures'))
from data.webhook_examples import valid_webhook_samples, invalid_webhook_samples

# Configuration
WEBHOOK_ENDPOINT = "http://localhost:5000/api/v1/webhooks/tradingview"
CONCURRENT_REQUESTS = 10
MAX_WORKERS = 10


class WebhookFinalVerificationTests(unittest.TestCase):
    """Tests to verify the webhook system functionality for final testing."""

    def setUp(self):
        """Set up test environment."""
        self.session = requests.Session()
        # Add any authentication headers if required
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': 'test-api-key'  # Replace with actual test API key
        })

    def tearDown(self):
        """Clean up after tests."""
        self.session.close()

    def test_valid_webhook_reception(self):
        """Test that valid webhooks are correctly received and processed."""
        for i, sample in enumerate(valid_webhook_samples):
            with self.subTest(f"Valid webhook sample {i+1}"):
                response = self.session.post(
                    WEBHOOK_ENDPOINT,
                    data=json.dumps(sample)
                )
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertTrue(result.get('success'))
                self.assertIn('webhookId', result)
                
                # Verify webhook was processed (could check a status endpoint or database)
                webhook_id = result.get('webhookId')
                time.sleep(1)  # Allow time for processing
                status_response = self.session.get(f"http://localhost:5000/api/v1/webhooks/{webhook_id}/status")
                self.assertEqual(status_response.status_code, 200)
                status = status_response.json()
                self.assertEqual(status.get('status'), 'processed')

    def test_invalid_webhook_handling(self):
        """Test that invalid webhooks are properly rejected with appropriate errors."""
        for i, sample in enumerate(invalid_webhook_samples):
            with self.subTest(f"Invalid webhook sample {i+1}"):
                response = self.session.post(
                    WEBHOOK_ENDPOINT,
                    data=json.dumps(sample)
                )
                self.assertEqual(response.status_code, 400)
                result = response.json()
                self.assertFalse(result.get('success'))
                self.assertIn('error', result)

    def test_concurrent_webhook_submission(self):
        """Test system can handle multiple concurrent webhook submissions."""
        sample = valid_webhook_samples[0]
        
        # Create multiple copies of the sample with different identifiers
        samples = []
        for i in range(CONCURRENT_REQUESTS):
            # Deep copy the sample and modify order ID to make it unique
            modified_sample = json.loads(json.dumps(sample))
            if 'orderId' in modified_sample:
                modified_sample['orderId'] = f"{modified_sample['orderId']}-{i}"
            samples.append(modified_sample)
        
        # Submit concurrently
        start_time = time.time()
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_sample = {
                executor.submit(self._submit_webhook, sample): i 
                for i, sample in enumerate(samples)
            }
            
            for future in as_completed(future_to_sample):
                sample_index = future_to_sample[future]
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                except Exception as exc:
                    print(f"Sample {sample_index} generated an exception: {exc}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests succeeded
        self.assertEqual(success_count, CONCURRENT_REQUESTS)
        # Verify total processing time is within acceptable limits (e.g., 5 seconds)
        self.assertLess(total_time, 5.0)
        
        print(f"Concurrent webhook test: {CONCURRENT_REQUESTS} webhooks processed in {total_time:.2f} seconds")

    def test_webhook_validation(self):
        """Test webhook field validation logic works correctly."""
        # Test with missing required fields
        required_fields = ['ticker', 'action', 'quantity', 'price']
        sample = valid_webhook_samples[0].copy()
        
        for field in required_fields:
            with self.subTest(f"Missing required field: {field}"):
                # Remove the field
                test_sample = sample.copy()
                if field in test_sample:
                    del test_sample[field]
                
                response = self.session.post(
                    WEBHOOK_ENDPOINT,
                    data=json.dumps(test_sample)
                )
                self.assertEqual(response.status_code, 400)
                result = response.json()
                self.assertFalse(result.get('success'))
                self.assertIn('error', result)
                # Verify error message contains field name
                self.assertIn(field, result.get('error').lower())

    def test_unauthorized_webhook_rejected(self):
        """Test that webhooks without proper authorization are rejected."""
        # Create a new session without auth headers
        unauth_session = requests.Session()
        unauth_session.headers.update({'Content-Type': 'application/json'})
        
        response = unauth_session.post(
            WEBHOOK_ENDPOINT,
            data=json.dumps(valid_webhook_samples[0])
        )
        
        self.assertEqual(response.status_code, 401)
        result = response.json()
        self.assertFalse(result.get('success'))
        self.assertIn('error', result)
        self.assertIn('unauthorized', result.get('error').lower())
        
        unauth_session.close()

    def _submit_webhook(self, sample):
        """Helper method to submit a webhook and return success status."""
        response = self.session.post(
            WEBHOOK_ENDPOINT,
            data=json.dumps(sample)
        )
        return response.status_code == 200 and response.json().get('success', False)


if __name__ == '__main__':
    unittest.main() 