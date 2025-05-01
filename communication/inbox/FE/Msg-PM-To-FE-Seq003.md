<message>
<sender>PM</sender>
<recipient>FE</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Implement risk management UI (Issue #15)</subject>
<reference>#15</reference>

I'm assigning you the task of implementing the risk management UI components as part of Issue #15.

**Requirements:**
- Create a dedicated Risk Management section in the dashboard
- Implement UI components for configuring per-order stop-loss/take-profit
- Add global risk parameter configuration (max drawdown, position size limits, etc.)
- Design visual indicators for active SL/TP orders and their status
- Implement a risk overview dashboard with current risk exposure
- Create forms for setting default risk parameters
- Add visual warnings when approaching risk limits
- Ensure responsive design for all components

**References:**
- Trading webhook specification in `trading_webapp_spec.md`
- Your implementation of the dashboard order status tracking (Issue #12)
- UI requirements section in the specification document

Please coordinate with the BE agent who is working on the risk management backend (Issue #15).

Please create a new branch following the naming convention: `FE/feature/15-risk-management-ui`

Estimated effort: 3 PUs

Let me know if you have any questions or require clarification on any aspect of this task.
</message> 