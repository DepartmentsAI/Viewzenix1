<message>
<sender>PM</sender>
<recipient>BE</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Implement risk management system (Issue #15)</subject>
<reference>#15</reference>

I'm assigning you the task of implementing a comprehensive risk management system as outlined in Issue #15.

**Requirements:**
- Create a risk management module that integrates with the order execution engine
- Implement per-order stop-loss/take-profit functionality
- Add global portfolio limit monitoring (max drawdown, position size limits)
- Develop a system for tracking active stop-loss and take-profit orders
- Create a cleanup service for orphaned orders
- Implement configurable risk rules and parameters
- Add proper error handling and logging
- Develop unit tests for all risk management components

**References:**
- Trading webhook specification in `trading_webapp_spec.md`
- Your implementation of the order execution engine (Issue #10)
- Architecture document in `/docs/architecture/ARCHITECTURE.md`

Please coordinate with the INT agent who has implemented broker adapters.

Please create a new branch following the naming convention: `BE/feature/15-risk-management-system`

Estimated effort: 4 PUs

Let me know if you have any questions or require clarification on any aspect of this task.
</message> 