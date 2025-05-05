# Risk Management UI Documentation

## Overview

The Risk Management UI provides a comprehensive interface for traders to monitor and manage trading risks. It offers real-time risk exposure visualization, stop-loss/take-profit management, and portfolio protection tools to help users maintain control over their trading activities.

## Key Features

1. **Risk Overview Dashboard**
   - Portfolio value monitoring with percentage change
   - Risk exposure visualization with severity indicators
   - Global stop-loss/take-profit status display
   - Active orders with stop-loss/take-profit levels

2. **Per-Order Risk Settings**
   - Default stop-loss and take-profit configuration
   - Percentage-based risk management tools
   - Visual representation of SL/TP placement
   - Automatic SL/TP attachment options

3. **Global Risk Parameters**
   - Account-wide stop-loss/take-profit circuit breakers
   - Position size limitation controls
   - Dynamic calculation of maximum position sizes
   - Emergency stop functionality for risk management

## Component Architecture

The Risk Management UI consists of several interconnected components:

- `RiskManagement.js` - Main component with tabbed interface
- `riskManagementService.js` - API service for risk management operations

### Data Flow

```
User Interaction → RiskManagement Component → Risk Management Service → Backend API
```

## API Integration

The Risk Management UI integrates with the backend through the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/risk/settings` | GET | Retrieve risk management settings |
| `/api/v1/risk/settings` | PUT | Update risk management settings |
| `/api/v1/risk/metrics` | GET | Fetch current portfolio risk metrics |
| `/api/v1/risk/orders` | GET | Fetch orders with risk parameters |
| `/api/v1/risk/orders/{orderId}` | PUT | Update risk parameters for a specific order |
| `/api/v1/risk/emergency-stop` | POST | Execute emergency stop (close all positions) |

## Usage Examples

### Setting Default Stop-Loss/Take-Profit

1. Navigate to the "Per-Order Settings" tab
2. Enable "Automatically attach SL/TP to all orders"
3. Adjust the SL and TP percentages using sliders
4. Click "Save Default Settings"

### Monitoring Risk Exposure

1. View the "Risk Overview" tab
2. Check the Risk Exposure percentage and color
3. Monitor active orders with their individual SL/TP levels
4. Review the portfolio value and change percentage

### Setting Global Risk Parameters

1. Navigate to the "Global Risk Parameters" tab
2. Enable "Global SL/TP circuit breaker"
3. Set base equity value for calculations
4. Adjust global SL/TP percentages
5. Configure maximum position size as percentage of equity
6. Save changes

## Risk Level Indicators

The UI uses a color-coded system to indicate risk severity:

| Risk Level | Range | Color |
|------------|-------|-------|
| Low | 0-30% | Green (success) |
| Moderate | 31-60% | Yellow (warning) |
| High | 61-80% | Red (error) |
| Critical | 81-100% | Red (error) |

## Best Practices

1. **Set Reasonable Defaults**: Configure per-order SL/TP defaults to match your risk tolerance
2. **Enable Global Circuit Breakers**: Use global SL/TP to protect against extreme market conditions
3. **Limit Position Sizes**: Use maximum position size limits to prevent overexposure
4. **Monitor Regularly**: Check the Risk Overview tab to stay informed about your risk exposure
5. **Test Emergency Stop**: Understand how the emergency stop works before needing it in live trading

## Implementation Notes

The Risk Management UI uses:
- Material UI components for consistent design
- Responsive layouts for all device sizes
- Real-time data fetching for up-to-date risk information
- Form validation to prevent invalid settings
- Error handling with user-friendly notifications

## Future Enhancements

Planned improvements to the Risk Management UI include:
- Risk visualization with historical charts
- Advanced risk modeling with scenario testing
- Customizable risk thresholds based on market conditions
- Integration with external risk assessment tools
- Automated risk adjustment based on market volatility 