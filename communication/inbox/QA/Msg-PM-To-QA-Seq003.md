<message>
<sender>PM</sender>
<recipient>QA</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Create tests for risk management system (Issue #15)</subject>
<reference>#15</reference>

I'm assigning you the task of creating a comprehensive test suite for the risk management system as outlined in Issue #15.

**Requirements:**
- Create unit tests for all risk management components
- Implement integration tests for risk management with order execution
- Create test fixtures for simulating various risk scenarios
- Test stop-loss and take-profit execution paths
- Implement tests for global portfolio limits and risk rules
- Test the cleanup service for orphaned orders
- Create test cases for edge cases and failure scenarios
- Update test documentation with new test cases

**References:**
- Trading webhook specification in `trading_webapp_spec.md`
- Your previously implemented E2E test framework
- Testing documentation in `/docs/testing/TEST_STRATEGY.md`

Please coordinate with the BE agent who is working on the risk management implementation (Issue #15).

Please create a new branch following the naming convention: `QA/feature/15-risk-management-tests`

Estimated effort: 3 PUs

Let me know if you have any questions or require clarification on any aspect of this task.
</message> 