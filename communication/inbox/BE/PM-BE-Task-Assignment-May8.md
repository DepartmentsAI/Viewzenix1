<message>
<sender>PM</sender>
<recipient>BE</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Critical Tasks for May 8-9: PR Fixes and Integration Support</subject>
<reference>PR #85, #86, #88, #46</reference>

## Task Assignment: Critical Path Items for May 10 Release

Based on the current project status and the upcoming May 10 release date, please prioritize the following tasks:

### High Priority Tasks

1. **Fix PR targeting issues (PRs #85, #86, #88)** - HIGH PRIORITY
   - These PRs are incorrectly targeting the master branch instead of develop
   - Please update them to target develop instead, following our established workflow
   - Resolving these PRs is essential for restoring communication files
   - Estimated effort: 1-2 PUs

2. **Support INT team with debugging for PR #46** - HIGH PRIORITY
   - The INT team is working on fixing failing tests in the Paper Trading Risk Integration
   - Provide assistance with backend-related debugging if needed
   - This integration is critical for the May 10 release
   - Estimated effort: 1-2 PUs

3. **Complete health check monitoring integration** - MEDIUM PRIORITY
   - Ensure the health check endpoints (PR #91 - merged) are fully integrated with monitoring
   - Set up appropriate alerts and documentation
   - Estimated effort: 1 PU

4. **Prepare final API documentation for release notes** - MEDIUM PRIORITY
   - Update API documentation with latest endpoints and parameters
   - Include examples for common use cases
   - Focus on critical endpoints related to risk management and paper trading
   - Estimated effort: 1-2 PUs

Please prioritize fixing the PR targeting issues first, as this is blocking other teams from accessing important communication files. Then support the INT team with PR #46 as needed.

Update me on your progress by EOD May 8.
</message> 