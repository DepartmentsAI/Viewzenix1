# Environment Verification Execution Guide

This guide provides practical, step-by-step instructions for executing the environment verification process on May 10, 2025 (9:00 AM - 12:00 PM). This document follows the test plan outlined in `ENVIRONMENT_VERIFICATION_TEST_PLAN.md`.

## Pre-Verification Setup (8:30 AM - 9:00 AM)

1. **Environment Setup Confirmation**
   ```bash
   # Team members should confirm environment availability
   cd /workspace/Viewzenix1
   git checkout develop
   git pull origin develop --rebase
   ```

2. **Verification Scripts Readiness**
   ```bash
   # Check that verification scripts are available
   cd /workspace/Viewzenix1/tests/e2e
   ls -la environment_verification.py
   ls -la run_environment_verification.*
   ```

3. **Test Fixtures Verification**
   ```bash
   # Check that test fixtures exist
   cd /workspace/Viewzenix1/tests/e2e/fixtures
   ls -la broker_config.json webhook_payloads.json order_templates.json risk_management_scenarios.json user_accounts.json
   ```

4. **Verification Team Readiness Check**
   - [ ] QA Team ready
   - [ ] Backend Team representative available
   - [ ] Frontend Team representative available 
   - [ ] Integration Team representative available
   - [ ] Communication channel established

## Phase 1: Component Verification (9:00 AM - 10:30 AM)

### Backend API Verification (9:00 AM - 9:30 AM)

1. **Start Backend Server**
   ```bash
   # In backend directory
   cd /workspace/Viewzenix1/src/backend
   python app.py
   # Or use the team's standard startup script
   ```

2. **Basic Health Check**
   ```bash
   # Using curl or browser
   curl http://localhost:5000/api/health
   # Expected: {"status": "healthy"}
   ```

3. **Detailed Health Check**
   ```bash
   # Using curl or browser
   curl http://localhost:5000/api/health/detailed
   # Verify each component status
   ```

4. **Database Connection Check**
   - [ ] Database shows "connected" in detailed health check
   - [ ] Run verification script database verification part:
   ```bash
   cd /workspace/Viewzenix1/tests/e2e
   python environment_verification.py --test-backend-only
   ```

5. **API Endpoints Check**
   - [ ] Test authentication endpoint
   - [ ] Test webhook receiver
   - [ ] Test market data endpoint
   - [ ] Test risk management endpoint

### Frontend Verification (9:30 AM - 10:00 AM)

1. **Start Frontend Server**
   ```bash
   # In frontend directory
   cd /workspace/Viewzenix1/src/frontend
   npm start
   # Or use the team's standard startup script
   ```

2. **Basic Accessibility Check**
   ```bash
   # Open in browser
   open http://localhost:3000
   # Verify page loads without errors
   ```

3. **Login Functionality**
   - [ ] Navigate to login page
   - [ ] Test with credentials from `/workspace/Viewzenix1/tests/e2e/fixtures/user_accounts.json`
   - [ ] Verify successful login

4. **Dashboard Components**
   - [ ] Verify all dashboard panels render
   - [ ] Check that API calls to backend are successful
   - [ ] Verify real-time data updates (if applicable)

5. **Run Frontend Verification Script**
   ```bash
   cd /workspace/Viewzenix1/tests/e2e
   python environment_verification.py --test-frontend-only
   ```

### Integration Verification (10:00 AM - 10:30 AM)

1. **Broker Connection Test**
   ```bash
   # Using verification script
   cd /workspace/Viewzenix1/tests/e2e
   python environment_verification.py --test-broker-only
   ```

2. **Market Data Verification**
   - [ ] Request market data for test symbols
   - [ ] Verify quote data returned is valid
   - [ ] Check historical data retrieval

3. **WebSocket Connection**
   - [ ] Establish WebSocket connection
   - [ ] Verify connection remains stable
   - [ ] Test data streaming

4. **Test Order Submission** (Paper Trading Only)
   - [ ] Submit a test order using API
   - [ ] Verify order acknowledgment
   - [ ] Check order appears in system

## Phase 2: End-to-End Verification (10:30 AM - 11:30 AM)

1. **Run Complete Verification Script**
   ```bash
   cd /workspace/Viewzenix1/tests/e2e
   
   # Linux/macOS
   ./run_environment_verification.sh
   
   # Windows
   .\run_environment_verification.ps1
   ```

2. **End-to-End Order Flow Test**
   - [ ] Create webhook payload from fixture
   - [ ] Submit to webhook endpoint
   - [ ] Verify processing through system
   - [ ] Confirm order reaches broker API
   - [ ] Check order appears in frontend

3. **Error Handling Verification**
   - [ ] Test invalid webhook payload
   - [ ] Verify appropriate error responses
   - [ ] Check error logging and monitoring

4. **Performance Basic Check**
   - [ ] Measure API response times under normal load
   - [ ] Check frontend page load times
   - [ ] Verify WebSocket message processing rate

## Phase 3: Go/No-Go Evaluation (11:30 AM - 12:00 PM)

1. **Collect Verification Results**
   - [ ] Backend verification results
   - [ ] Frontend verification results
   - [ ] Integration verification results
   - [ ] End-to-end test results

2. **Document Issues**
   - [ ] Create GitHub Issues for any identified problems
   - [ ] Assign to appropriate teams
   - [ ] Determine severity and impact on testing

3. **Apply Go/No-Go Criteria**
   - [ ] Backend API availability is ≥ 99%
   - [ ] Critical endpoint response time < 200ms
   - [ ] Test pass rate ≥ 95%
   - [ ] No unresolved critical issues
   - [ ] No more than 2 unresolved major issues
   - [ ] Broker connection successful
   - [ ] Frontend loads successfully

4. **Prepare Verification Results Document**
   ```bash
   cp /workspace/Viewzenix1/docs/testing/VERIFICATION_RESULTS_TEMPLATE.md /workspace/Viewzenix1/docs/testing/VERIFICATION_RESULTS_MAY10.md
   # Edit the results document with actual findings
   ```

5. **Team Discussion and Decision**
   - [ ] Present verification results
   - [ ] Discuss any issues and mitigations
   - [ ] Record formal Go/No-Go decision
   - [ ] Document decision rationale

## Phase 4: Post-Decision Actions (12:00 PM)

### If GO Decision:

1. **Notify All Teams**
   ```
   <message>
   <sender>QA</sender>
   <recipient>ALL</recipient>
   <type>INFO</type>
   <subject>GO Decision: Proceed with Critical Path Testing</subject>
   <content>
   Environment verification completed successfully. Proceed with critical path testing as scheduled.
   
   Summary of verification:
   - All components operational
   - [Any specific notes or minor issues]
   
   Testing will proceed according to the test plan at 1:00 PM.
   </content>
   </message>
   ```

2. **Prepare Testing Environment**
   - [ ] Ensure all test data is ready
   - [ ] Prepare test tracking sheets
   - [ ] Brief testing team on any limitations

### If NO-GO Decision:

1. **Notify All Teams**
   ```
   <message>
   <sender>QA</sender>
   <recipient>ALL</recipient>
   <type>BLOCKER_REPORT</type>
   <subject>NO-GO Decision: Environment Verification Failed</subject>
   <content>
   Environment verification has failed. Critical path testing is on hold.
   
   Blocking issues:
   - [List critical issues]
   
   Next steps:
   - [List resolution actions]
   - [List revised timeline]
   
   We will reconvene at [time] to reassess.
   </content>
   </message>
   ```

2. **Activate Contingency Plan**
   - [ ] Implement fixes for blocking issues
   - [ ] Schedule re-verification
   - [ ] Update test plan timeline

## Quick Reference

### Key Endpoints:
- Backend Health: http://localhost:5000/api/health
- Backend Detailed Health: http://localhost:5000/api/health/detailed
- Webhook Endpoint: http://localhost:5000/api/webhook/tradingview
- Frontend: http://localhost:3000

### Test Credentials (from fixtures):
- Admin: admin@viewzenix.example.com / Admin123!
- Regular User: user@viewzenix.example.com / User123!
- Viewer: viewer@viewzenix.example.com / Viewer123!

### Verification Script Options:
```bash
# Test specific components
python environment_verification.py --test-backend-only
python environment_verification.py --test-frontend-only
python environment_verification.py --test-broker-only

# Use different endpoints
python environment_verification.py --backend-url http://custom-backend:5000 --frontend-url http://custom-frontend:3000

# Enable verbose logging
python environment_verification.py --verbose
```

### Common Issues and Fixes:

| Issue | Quick Fix |
|-------|-----------|
| Backend won't start | Check port conflicts with `netstat -ano \| findstr 5000` |
| Database connection | Verify database is running and credentials are correct |
| Frontend blank page | Check browser console for errors, verify API URL |
| Broker connection | Verify credentials in broker_config.json |
| WebSocket issues | Check network restrictions, try REST fallback |

## Contacts for Critical Issues

| Role | Name | Contact |
|------|------|---------|
| QA Lead | [Name] | [Contact] |
| BE Lead | [Name] | [Contact] |
| FE Lead | [Name] | [Contact] |
| INT Lead | [Name] | [Contact] |
| PM | [Name] | [Contact] | 