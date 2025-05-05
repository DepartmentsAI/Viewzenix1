# Component Verification Checklist

This document provides detailed verification steps for each component in the Viewzenix1 system. Use this checklist during the environment verification process on May 10, 2025.

## Backend API Verification

### ENV-BE-01: Basic Health Check

- [ ] Start the backend server
- [ ] Make a GET request to `/api/health`
- [ ] Verify status code 200 is returned
- [ ] Verify JSON response contains `{"status": "healthy"}`
- [ ] Check response time is under 500ms

### ENV-BE-02: Detailed Health Check

- [ ] Make a GET request to `/api/health/detailed`
- [ ] Verify status code 200 is returned
- [ ] Verify JSON response contains status for all components:
  - [ ] `database`
  - [ ] `broker_service`
  - [ ] `webhook_system`
  - [ ] `risk_management`
- [ ] Check response time is under 1000ms

### ENV-BE-03: Database Connectivity

- [ ] Check `database` status in detailed health response
- [ ] Verify status is `"connected"` or `"healthy"`
- [ ] Make a test query to verify database read access
- [ ] Make a test write operation to verify database write access
- [ ] Verify rollback functionality works correctly

### ENV-BE-04: Risk Management System

- [ ] Check `risk_management` status in detailed health response
- [ ] Verify status is `"operational"`
- [ ] Test a basic risk check using a sample order
- [ ] Test position size limits
- [ ] Test volatility protection mechanisms

### ENV-BE-05: Webhook Endpoint

- [ ] Send a test webhook payload to `/api/webhook/tradingview`
- [ ] Verify status code 200 is returned
- [ ] Verify response contains appropriate confirmation
- [ ] Check webhook is processed correctly (logs/database)
- [ ] Test with invalid payload to verify error handling

## Frontend Verification

### ENV-FE-01: Frontend Accessibility

- [ ] Start the frontend server
- [ ] Access the frontend URL in Chrome
- [ ] Access the frontend URL in Firefox
- [ ] Verify main page loads without console errors
- [ ] Verify all static assets (CSS, JS, images) load correctly

### ENV-FE-02: Login Page

- [ ] Navigate to login page
- [ ] Verify form fields render correctly
- [ ] Test with valid credentials
- [ ] Test with invalid credentials
- [ ] Verify error messages display correctly
- [ ] Check "Remember Me" functionality

### ENV-FE-03: Dashboard Components

- [ ] Login to application
- [ ] Verify dashboard loads
- [ ] Check that all dashboard panels render:
  - [ ] Account summary
  - [ ] Open positions
  - [ ] Recent orders
  - [ ] Market overview
- [ ] Verify charts/graphs display correctly
- [ ] Check responsive behavior on different screen sizes

### ENV-FE-04: API Connection

- [ ] Monitor network requests during dashboard load
- [ ] Verify API calls to backend are successful
- [ ] Check authentication token is properly maintained
- [ ] Verify real-time updates are functioning
- [ ] Test session timeout handling

## Integration Verification

### ENV-INT-01: Broker Connectivity

- [ ] Verify broker connection configuration
- [ ] Test connection using configured credentials
- [ ] Verify account information can be retrieved
- [ ] Check error handling for invalid credentials
- [ ] Verify connection retry mechanism

### ENV-INT-02: Market Data

- [ ] Request market data for test symbols
- [ ] Verify quote data returned is valid
- [ ] Check historical data retrieval
- [ ] Verify market hours information
- [ ] Test rate limiting mechanisms

### ENV-INT-03: WebSocket Connection

- [ ] Establish WebSocket connection
- [ ] Verify connection remained established for >60 seconds
- [ ] Subscribe to real-time updates for test symbols
- [ ] Verify data is being received
- [ ] Test connection drop and automatic reconnection

### ENV-INT-04: Order Submission

- [ ] Submit a test order (paper trading)
- [ ] Verify order acknowledgment
- [ ] Check order appears in open orders list
- [ ] Test order modification
- [ ] Test order cancellation

## Test Data Verification

### ENV-DATA-01: Test Fixtures

- [ ] Verify all required fixture files exist:
  - [ ] `webhook_payloads.json`
  - [ ] `order_templates.json`
  - [ ] `risk_management_scenarios.json`
  - [ ] `user_accounts.json`
  - [ ] `broker_config.json`
- [ ] Check file permissions are correct
- [ ] Verify files are valid JSON

### ENV-DATA-02: Webhook Payloads

- [ ] Check webhook payloads for all required scenarios:
  - [ ] Market buy order
  - [ ] Market sell order
  - [ ] Limit orders
  - [ ] Stop orders
  - [ ] Invalid payloads for testing
- [ ] Verify payload structure matches API expectations
- [ ] Test each payload with the webhook endpoint

### ENV-DATA-03: User Accounts

- [ ] Verify test user accounts for different roles:
  - [ ] Admin
  - [ ] Regular user
  - [ ] View-only user
- [ ] Check credentials work with authentication API
- [ ] Verify appropriate permissions for each role

### ENV-DATA-04: Order Templates

- [ ] Check all required order templates exist
- [ ] Verify template structure is valid
- [ ] Test order creation from each template
- [ ] Check parameter substitution works correctly

## Additional Checks

### Security Verification

- [ ] Verify SSL/TLS configuration
- [ ] Check authentication mechanisms
- [ ] Verify API endpoints require proper authorization
- [ ] Test CORS configuration
- [ ] Check for sensitive information exposure

### Performance Basic Checks

- [ ] Measure API response times under normal load
- [ ] Check frontend page load times
- [ ] Verify WebSocket message processing rate
- [ ] Test database query performance
- [ ] Check memory usage of key processes

## Instructions for Using This Checklist

1. Make a copy of this checklist for your verification session
2. Check off items as they are verified
3. Note any issues or observations for each item
4. Include screenshots or log excerpts where helpful
5. Submit the completed checklist with your verification report

## Results Formatting

When reporting results, use the following status indicators:

- **PASS**: Requirement fully met, no issues
- **PARTIAL**: Requirement partially met, minor issues noted
- **FAIL**: Requirement not met, significant issues found
- **BLOCKED**: Unable to verify due to dependencies
- **N/A**: Not applicable in current environment 