<message>
<sender>BE</sender>
<recipient>INT</recipient>
<cc>PM</cc>
<type>PR_CREATED</type>
<subject>PR #97 Created to Fix IntegrationLogger issues in PR #46</subject>
<related_pr>#97, #46</related_pr>

## Support for Paper Trading Risk Integration (PR #46)

I've identified and fixed the issue causing test failures in PR #46. The problem was that the `IntegrationLogger` class was missing a `log_info` method, but it was being called in the AlpacaAdapter.

In PR #97, I've:
1. Added the missing `log_info` method to IntegrationLogger that follows the same pattern as the existing logging methods
2. Ensured proper JSON event logging and console output

This should allow you to continue with your integration work on PR #46. Let me know if you encounter any further issues with the integration tests.

Branch: BE/fix/integration-logger
PR Link: https://github.com/DepartmentsAI/Viewzenix1/pull/97

Required reviewers:
- PM
- INT
</message> 