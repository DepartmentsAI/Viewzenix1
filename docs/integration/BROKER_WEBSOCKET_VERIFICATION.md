# Broker WebSocket Connection Verification

## Overview

This document provides instructions for verifying that the broker WebSocket connections are working correctly in the Viewzenix1 platform, focusing on the Alpaca API integration. It is intended for developers and testers who need to validate the WebSocket functionality before running tests or deploying changes.

## Prerequisites

Before running the verification process, ensure:

1. You have the required environment variables set up:
   - `ALPACA_API_KEY_ID` or `APCA_API_KEY_ID`
   - `ALPACA_API_SECRET_KEY` or `APCA_API_SECRET`
   - `ALPACA_API_BASE_URL` or `APCA_API_BASE_URL`

2. The `websocket-client` Python package is installed:
   ```bash
   pip install websocket-client==1.7.0
   ```
   
   This should already be installed if you've run `pip install -r requirements.txt` with the updated requirements file.

## Verification Scripts

### 1. Broker Connection Verification Script

The main verification script for all broker connections: 

```bash
python src/integration/utils/verify_broker_connection.py
```

This script checks:
- Broker configuration loading
- REST API connectivity
- WebSocket connectivity
- Paper trading adapter functionality

### 2. Stream Adapter Verification Script

For a focused test of just the WebSocket streaming functionality:

```bash
python src/integration/examples/stream_adapter_verification.py
```

This script demonstrates:
- WebSocket connection establishment
- Authentication
- Subscription to account updates
- Subscription to market data feeds

## Common Issues and Solutions

### 1. WebSocket Connection Errors

**Issue**: WebSocket connection fails with connection errors.

**Solutions**:
- Check that your API key and secret are correct
- Verify network connectivity and firewall settings
- Ensure the API endpoint URLs are correct (paper vs. live trading)

### 2. Authentication Failures

**Issue**: Connected to WebSocket but authentication fails.

**Solutions**:
- Double-check your API key and secret
- Verify the API key has appropriate permissions
- Check the authentication headers format

### 3. No Data Received

**Issue**: Connected and authenticated, but not receiving updates.

**Solutions**:
- Markets may be closed (no trades happening)
- Verify you're subscribed to the correct symbols
- Check that you've registered callback functions
- Monitor for any error messages in the logs

## How to Fix PR #46 Testing Issues

To ensure PR #46 (Risk Management integration with Paper Trading) passes testing:

1. Verify `websocket-client` is properly installed:
   ```bash
   pip install websocket-client==1.7.0
   ```

2. Confirm `werkzeug` version is compatible with Flask:
   ```bash
   pip install werkzeug==2.0.3
   ```

3. Run the verification scripts above to confirm connections are working.

4. If tests continue to fail:
   - Check the test output for specific error messages
   - Verify that environment variables are properly set in your test environment
   - Make sure any mocks in the test suite properly simulate WebSocket behavior

## References

- [Alpaca WebSocket API Documentation](https://alpaca.markets/docs/api-documentation/api-v2/market-data/alpaca-data-api-v2/real-time/)
- [websocket-client Documentation](https://websocket-client.readthedocs.io/)
- [PR #46 Details](https://github.com/DepartmentsAI/Viewzenix1/pull/46)
- [Viewzenix1 Integration Documentation](./ALPACA_WEBSOCKET_INTEGRATION.md) 