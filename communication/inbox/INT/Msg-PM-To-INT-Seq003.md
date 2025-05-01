<message>
<sender>PM</sender>
<recipient>INT</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Integrate Risk Management with Paper Trading Adapter (Issues #13, #15)</subject>
<reference>#13, #15</reference>

Dear Integration Agent,

You are assigned to integrate the Risk Management System (Issue #15) with the Paper Trading Adapter (Issue #13). This integration will allow us to test and demonstrate risk management features in a simulated environment.

Requirements:
1. Enhance Paper Trading Adapter:
   - Modify the adapter to support stop-loss/take-profit orders
   - Implement price simulation that can trigger SL/TP orders
   - Add support for bracket orders (main order + SL + TP)
   - Create order status tracking for risk management validation

2. Implement Risk Management Integration:
   - Connect the paper trading adapter to the risk management service
   - Create simulated portfolio for testing drawdown limits
   - Implement position tracking for max position limits
   - Add support for cleanup service to detect orphaned paper orders

3. Develop Testing Utilities:
   - Create price movement simulation tools for triggering risk events
   - Build market condition scenarios (volatile, trending, etc.)
   - Implement simulation speed controls (normal, accelerated)
   - Add manual override capabilities for testing extreme cases

4. Create Documentation:
   - Document integration points between paper trading and risk management
   - Create example usage scenarios in `/docs/integration/paper-trading-risk-examples.md`
   - Provide troubleshooting guidelines for testing with paper trading

Implementation Guidelines:
- Extend the AlpacaAdapter patterns for consistent interface
- Focus on realistic simulation that can verify risk management behaviors
- Add comprehensive logging for debugging integration issues
- Create specific test scenarios that QA can use in their test suite
- Coordinate with BE team on risk management service integration

Dependencies:
- AlpacaAdapter (already implemented in PR #9)
- Paper Trading Adapter (in progress, Issue #13)
- Backend risk management (being implemented by BE team concurrently)

Estimated Effort: 2-3 PUs

Please provide a brief plan and approach before starting implementation. Continue working in your feature branch INT/feature/13-paper-trading-adapter and ensure it includes risk management integration capabilities.

Let me know if you have any questions or need clarification.

Best regards,
PM 