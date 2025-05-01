<message>
<sender>PM</sender>
<recipient>BE</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Implement Risk Management Backend (Issue #15)</subject>
<reference>#15</reference>

Dear Backend Agent,

You are assigned to implement the risk management backend component for our Trading Webhook Platform as part of Issue #15. This is a crucial safety component that will protect user funds during automated trading.

Requirements:
1. Implement per-order stop-loss/take-profit functionality:
   - Support both fixed price and percentage-based SL/TP
   - Allow customization of SL/TP parameters per incoming webhook
   - Automatically append SL/TP orders when executing main orders

2. Implement global portfolio protection:
   - Create daily maximum drawdown limit
   - Implement maximum open position count
   - Track overall portfolio risk exposure

3. Develop orphaned order cleanup service:
   - Identify orders without parent/child relationships
   - Implement background service to clean up stale orders
   - Add manual cleanup endpoint

4. Create risk manager service interface:
   - Build API for FE to configure risk parameters
   - Store risk settings in database
   - Add validation to prevent unsafe configurations

Implementation Guidelines:
- Follow service-based architecture pattern established in OrderEngine
- Add comprehensive logging
- Create unit tests for all risk management features
- Coordinate with FE team on the API design for risk management configuration
- Document all risk management features in code and in the /docs/architecture directory

Dependencies:
- Order execution engine (already implemented in PR #16)
- AlpacaAdapter (already implemented in PR #9)

Estimated Effort: 3-4 PUs

Please provide a brief plan and approach before starting implementation. Create a feature branch from develop named BE/feature/15-risk-management.

Let me know if you have any questions or need clarification.

Best regards,
PM 