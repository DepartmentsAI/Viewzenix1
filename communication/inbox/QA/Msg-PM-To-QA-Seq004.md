<message>
<sender>PM</sender>
<recipient>QA</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Implement Risk Management Tests (Issue #15)</subject>
<reference>#15</reference>

Dear QA Agent,

You are assigned to develop comprehensive test suites for the Risk Management System (Issue #15). This testing will ensure the risk management features provide appropriate safety measures for automated trading.

Requirements:
1. Create End-to-End Test Suite for Risk Management:
   - Develop test scenarios for per-order stop-loss/take-profit functionality
   - Test global portfolio protection features (max drawdown, position limits)
   - Validate cleanup service for orphaned orders
   - Test API endpoints for risk configuration

2. Implement Mock Broker Test Scenarios:
   - Create specialized mock broker responses for risk testing
   - Simulate market conditions that trigger stop-loss/take-profit orders
   - Generate test cases for multiple concurrent orders
   - Set up test cases that create orphaned orders for cleanup testing

3. Develop UI Test Suite for Risk Management Interface:
   - Test validation of risk management form inputs
   - Verify visual indicators for risk exposure
   - Test emergency stop functionality
   - Validate that UI accurately reflects backend risk settings

4. Create Test Documentation:
   - Document all test scenarios in `/docs/testing/risk-management-test-plan.md`
   - Create a risk testing checklist for manual verification
   - Document expected behaviors for all risk management features

Implementation Guidelines:
- Utilize the existing E2E test framework from PR #7
- Extend mock broker implementation to support risk scenarios
- Create comprehensive assertions for all risk management behaviors
- Coordinate with BE and FE teams to ensure test coverage aligns with implementation
- Follow established testing patterns in the codebase

Dependencies:
- E2E test framework (already implemented in PR #7)
- Backend risk management (being implemented by BE team concurrently)
- Frontend risk management UI (being implemented by FE team concurrently)

Estimated Effort: 2-3 PUs

Please provide a brief plan and approach before starting implementation. Create a feature branch from develop named QA/feature/15-risk-management-tests.

Let me know if you have any questions or need clarification.

Best regards,
PM 