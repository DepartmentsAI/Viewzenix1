import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RiskManagement from '../../../../src/frontend/pages/RiskManagement';
import * as riskService from '../../../../src/frontend/services/riskManagementService';

// Mock the risk management service
jest.mock('../../../../src/frontend/services/riskManagementService');

describe('RiskManagement Component', () => {
  // Mock data
  const mockSettings = {
    baseEquity: 100000,
    currentEquity: 105200,
    riskExposure: 35,
    attachSlTp: true,
    useAvgFillForSlTp: true,
    slPercent: 1.0,
    tpPercent: 2.0,
    enableGlobalSlTp: true,
    globalSlPercent: 20,
    globalTpPercent: 50,
    maxPositionSize: 5
  };

  const mockOrders = [
    { 
      id: 'ord-1', 
      symbol: 'BTCUSD', 
      type: 'LONG', 
      entryPrice: 65000, 
      quantity: 0.1,
      slPrice: 63500,
      tpPrice: 68000,
      slPercent: -2.3,
      tpPercent: 4.6,
      status: 'active'
    }
  ];

  beforeEach(() => {
    // Setup default mocks
    riskService.fetchRiskSettings.mockResolvedValue(mockSettings);
    riskService.fetchOrdersWithRiskParams.mockResolvedValue(mockOrders);
    riskService.fetchRiskMetrics.mockResolvedValue({
      riskExposure: mockSettings.riskExposure,
      portfolioValue: mockSettings.currentEquity
    });
    riskService.getRiskLevelInfo.mockReturnValue({ level: 'Moderate', color: 'warning' });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the component title', () => {
    render(<RiskManagement />);
    expect(screen.getByText('Risk Management')).toBeInTheDocument();
  });

  it('displays tabs correctly', () => {
    render(<RiskManagement />);
    expect(screen.getByText('Risk Overview')).toBeInTheDocument();
    expect(screen.getByText('Per-Order Settings')).toBeInTheDocument();
    expect(screen.getByText('Global Risk Parameters')).toBeInTheDocument();
  });

  it('changes tab when clicked', () => {
    render(<RiskManagement />);
    
    // Default tab should be Risk Overview
    expect(screen.getByText('Portfolio Value')).toBeInTheDocument();
    
    // Click Per-Order Settings tab
    fireEvent.click(screen.getByText('Per-Order Settings'));
    expect(screen.getByText('Default Per-Order Stop Loss / Take Profit Settings')).toBeInTheDocument();
    
    // Click Global Risk Parameters tab
    fireEvent.click(screen.getByText('Global Risk Parameters'));
    expect(screen.getByText('Global Stop Loss / Take Profit')).toBeInTheDocument();
  });

  it('loads risk data on component mount', async () => {
    render(<RiskManagement />);
    
    // Wait for data loading to complete
    await waitFor(() => {
      expect(riskService.fetchRiskSettings).toHaveBeenCalled();
      expect(riskService.fetchRiskMetrics).toHaveBeenCalled();
      expect(riskService.fetchOrdersWithRiskParams).toHaveBeenCalled();
    });
  });

  it('displays risk exposure with correct severity', async () => {
    render(<RiskManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Risk Exposure')).toBeInTheDocument();
      expect(screen.getByText(`${mockSettings.riskExposure}%`)).toBeInTheDocument();
    });
  });

  it('displays active orders with SL/TP', async () => {
    render(<RiskManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Orders with SL/TP')).toBeInTheDocument();
      expect(screen.getByText('BTCUSD')).toBeInTheDocument();
      expect(screen.getByText('LONG')).toBeInTheDocument();
    });
  });

  it('toggles SL/TP settings when switch is clicked', async () => {
    render(<RiskManagement />);
    
    // Go to Per-Order Settings tab
    fireEvent.click(screen.getByText('Per-Order Settings'));
    
    // Find the switch
    const attachSlTpSwitch = screen.getByLabelText('Automatically attach SL/TP to all orders');
    
    // Check initial state
    expect(attachSlTpSwitch).toBeInTheDocument();
    
    // Toggle the switch
    fireEvent.click(attachSlTpSwitch);
    
    // Verify the state has changed
    await waitFor(() => {
      // The UI should reflect the change in the component's state
      expect(screen.getByLabelText('Use average fill price for SL/TP (instead of alert price)')).toBeDisabled();
    });
  });

  it('tests the save buttons', async () => {
    render(<RiskManagement />);
    
    // Go to Per-Order Settings tab
    fireEvent.click(screen.getByText('Per-Order Settings'));
    
    // Click Save button
    const saveButton = screen.getByText('Save Default Settings');
    fireEvent.click(saveButton);
    
    // Should call the update function
    await waitFor(() => {
      expect(riskService.updateRiskSettings).toHaveBeenCalled();
    });
  });

  // Add more tests as needed
}); 