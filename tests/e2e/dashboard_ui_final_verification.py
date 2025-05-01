#!/usr/bin/env python3
"""
Final verification tests for the Dashboard UI.
Used during the final testing phase to ensure the Dashboard UI functionality
is working correctly before release.
"""

import time
import unittest
from playwright.sync_api import sync_playwright

# Test configuration
BASE_URL = "http://localhost:3000"
DASHBOARD_URL = f"{BASE_URL}/dashboard"
LOGIN_URL = f"{BASE_URL}/login"
TEST_USERNAME = "test@viewzenix.com"
TEST_PASSWORD = "TestPassword123!"


class DashboardUIFinalVerificationTests(unittest.TestCase):
    """Tests to verify the Dashboard UI functionality for final testing."""

    def setUp(self):
        """Set up test environment."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # Login before each test
        self._login()

    def tearDown(self):
        """Clean up after tests."""
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def _login(self):
        """Helper method to log in to the application."""
        self.page.goto(LOGIN_URL)
        self.page.fill('input[name="email"]', TEST_USERNAME)
        self.page.fill('input[name="password"]', TEST_PASSWORD)
        self.page.click('button[type="submit"]')
        
        # Wait for redirect to dashboard after login
        self.page.wait_for_url(DASHBOARD_URL)
        
        # Verify login was successful
        self.assertEqual(self.page.url, DASHBOARD_URL)

    def test_dashboard_loads_correctly(self):
        """Test that the dashboard page loads correctly with all required components."""
        self.page.goto(DASHBOARD_URL)
        
        # Verify essential dashboard elements are visible
        for element_id in ['order-status-panel', 'order-history-table', 'risk-management-card']:
            self.assertTrue(
                self.page.is_visible(f'#{element_id}'),
                f"Dashboard element '{element_id}' not visible"
            )
            
        # Verify page title is correct
        self.assertTrue(self.page.is_visible('text=Viewzenix Dashboard'))

    def test_order_status_tracking(self):
        """Test that the order status tracking panel displays current orders correctly."""
        self.page.goto(DASHBOARD_URL)
        
        # Verify order status panel exists
        self.assertTrue(self.page.is_visible('#order-status-panel'))
        
        # Count number of orders displayed
        order_rows = self.page.query_selector_all('#order-status-panel tbody tr')
        num_orders = len(order_rows)
        
        # Should be at least one test order in the system
        self.assertGreater(num_orders, 0, "No orders displayed in status panel")
        
        # Verify order status columns are present
        for column in ['Order ID', 'Symbol', 'Type', 'Status', 'Created At', 'Updated At']:
            self.assertTrue(
                self.page.is_visible(f'text={column}'),
                f"Column '{column}' not visible in order status panel"
            )

    def test_order_history_functionality(self):
        """Test the order history table functionality."""
        self.page.goto(DASHBOARD_URL)
        
        # Verify order history table exists
        self.assertTrue(self.page.is_visible('#order-history-table'))
        
        # Test filtering
        self.page.fill('#order-history-search', 'AAPL')
        self.page.press('#order-history-search', 'Enter')
        time.sleep(1)  # Allow time for filtering to apply
        
        # Verify filtered results contain AAPL
        order_rows = self.page.query_selector_all('#order-history-table tbody tr')
        for row in order_rows:
            self.assertIn('AAPL', row.inner_text())
            
        # Test date range filtering
        self.page.click('#date-range-picker')
        self.page.click('text=Last 7 days')
        time.sleep(1)  # Allow time for filtering to apply
        
        # Verify date range applied (check for "Showing orders from..." text)
        date_range_info = self.page.inner_text('#date-range-info')
        self.assertIn('Showing orders from', date_range_info)
        
        # Test pagination
        if self.page.is_visible('#pagination-next'):
            self.page.click('#pagination-next')
            time.sleep(1)  # Allow time for page to load
            page_info = self.page.inner_text('#pagination-info')
            self.assertIn('Page 2', page_info)

    def test_risk_management_configuration(self):
        """Test the risk management configuration interface."""
        self.page.goto(f"{DASHBOARD_URL}/risk-settings")
        
        # Verify risk settings page loaded
        self.assertTrue(self.page.is_visible('text=Risk Management Settings'))
        
        # Test modifying a risk parameter
        current_value = self.page.input_value('#max-position-size')
        new_value = str(float(current_value) + 1.0)
        
        self.page.fill('#max-position-size', new_value)
        self.page.click('#save-risk-settings')
        
        # Verify success message appears
        self.assertTrue(self.page.is_visible('text=Settings saved successfully'))
        
        # Reload page and verify setting was saved
        self.page.reload()
        self.assertEqual(self.page.input_value('#max-position-size'), new_value)
        
        # Test invalid input validation
        self.page.fill('#max-position-size', '-1')
        self.page.click('#save-risk-settings')
        
        # Verify error message appears
        self.assertTrue(self.page.is_visible('text=Value must be greater than 0'))

    def test_real_time_updates(self):
        """Test that the dashboard updates in real-time when order status changes."""
        self.page.goto(DASHBOARD_URL)
        
        # Get current number of orders
        initial_order_rows = self.page.query_selector_all('#order-status-panel tbody tr')
        initial_count = len(initial_order_rows)
        
        # Open a second page to simulate creating a new order (would normally be done via API)
        # For this test, we'll just check that the UI is set up to handle real-time updates
        second_page = self.context.new_page()
        second_page.goto(f"{BASE_URL}/create-order")
        
        # Fill order form
        second_page.fill('#symbol', 'MSFT')
        second_page.fill('#quantity', '10')
        second_page.select_option('#order-type', 'market')
        second_page.click('#submit-order')
        
        # Wait for confirmation message
        second_page.wait_for_selector('text=Order submitted successfully')
        second_page.close()
        
        # Return to first page and wait for update (maximum 5 seconds)
        max_wait = 5
        updated = False
        start_time = time.time()
        
        while time.time() - start_time < max_wait and not updated:
            current_rows = self.page.query_selector_all('#order-status-panel tbody tr')
            if len(current_rows) > initial_count:
                updated = True
            else:
                time.sleep(0.5)
                
        # Verify dashboard was updated with new order
        self.assertTrue(updated, "Dashboard did not update in real-time with new order")


if __name__ == '__main__':
    unittest.main() 