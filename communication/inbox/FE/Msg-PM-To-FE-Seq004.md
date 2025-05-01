<message>
<sender>PM</sender>
<recipient>FE</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Implement Risk Management UI (Issue #15)</subject>
<reference>#15</reference>

Dear Frontend Agent,

You are assigned to implement the risk management UI components for our Trading Webhook Platform as part of Issue #15. This UI will allow users to configure and monitor risk parameters for automated trading.

Requirements:
1. Create Risk Management Tab in the Dashboard:
   - Develop a dedicated risk management tab with appropriate navigation
   - Ensure responsive design follows established patterns
   - Include help tooltips for complex settings

2. Implement Risk Configuration UI:
   - Create forms for configuring global risk parameters:
     * Maximum daily drawdown (percentage)
     * Maximum number of open positions
     * Default stop-loss/take-profit values
   - Add per-strategy risk parameters:
     * Strategy-specific SL/TP settings
     * Position sizing options
     * Max allocation per strategy

3. Develop Risk Monitoring Components:
   - Create visual indicators for current risk exposure
   - Add warning indicators when approaching risk limits
   - Implement emergency stop button for halting all trading

4. Design Order Protection Settings UI:
   - Build interface for configuring trailing stops
   - Add form elements for bracket order parameters
   - Create visual preview of protection settings

Implementation Guidelines:
- Use React functional components with hooks
- Follow existing component patterns in the codebase
- Add client-side validation for all input forms
- Create comprehensive unit and integration tests
- Coordinate with BE team on risk management API endpoints
- Document component usage in code and in the /docs/ui directory

Dependencies:
- React dashboard foundation (already implemented in PR #6)
- Backend risk management API (being implemented by BE team concurrently)

Estimated Effort: 2-3 PUs

Please provide a brief plan and approach before starting implementation. Create a feature branch from develop named FE/feature/15-risk-management-ui.

Let me know if you have any questions or need clarification.

Best regards,
PM 