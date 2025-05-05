import axios from 'axios';
import { 
  fetchRiskSettings, 
  updateRiskSettings, 
  fetchRiskMetrics, 
  fetchOrdersWithRiskParams, 
  updateOrderRiskParams,
  getRiskLevelInfo,
  executeEmergencyStop
} from '../../../../src/frontend/services/riskManagementService';

// Mock axios
jest.mock('axios');

describe('Risk Management Service', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchRiskSettings', () => {
    it('should fetch risk settings successfully', async () => {
      const mockData = { globalStopLoss: 20, maxPositionSize: 5 };
      axios.get.mockResolvedValueOnce({ data: mockData });

      const result = await fetchRiskSettings();
      
      expect(axios.get).toHaveBeenCalledWith('/api/v1/risk/settings');
      expect(result).toEqual(mockData);
    });

    it('should handle errors when fetching risk settings', async () => {
      const errorMessage = 'Network Error';
      axios.get.mockRejectedValueOnce(new Error(errorMessage));
      
      await expect(fetchRiskSettings()).rejects.toThrow(errorMessage);
      expect(axios.get).toHaveBeenCalledWith('/api/v1/risk/settings');
    });
  });

  describe('updateRiskSettings', () => {
    it('should update risk settings successfully', async () => {
      const settings = { globalStopLoss: 25, maxPositionSize: 6 };
      const mockResponse = { ...settings, updated: true };
      
      axios.put.mockResolvedValueOnce({ data: mockResponse });

      const result = await updateRiskSettings(settings);
      
      expect(axios.put).toHaveBeenCalledWith('/api/v1/risk/settings', settings);
      expect(result).toEqual(mockResponse);
    });

    it('should handle errors when updating risk settings', async () => {
      const settings = { globalStopLoss: 25, maxPositionSize: 6 };
      const errorMessage = 'Bad Request';
      
      axios.put.mockRejectedValueOnce(new Error(errorMessage));
      
      await expect(updateRiskSettings(settings)).rejects.toThrow(errorMessage);
      expect(axios.put).toHaveBeenCalledWith('/api/v1/risk/settings', settings);
    });
  });

  describe('fetchRiskMetrics', () => {
    it('should fetch risk metrics successfully', async () => {
      const mockMetrics = { riskExposure: 45, portfolioValue: 105000 };
      axios.get.mockResolvedValueOnce({ data: mockMetrics });

      const result = await fetchRiskMetrics();
      
      expect(axios.get).toHaveBeenCalledWith('/api/v1/risk/metrics');
      expect(result).toEqual(mockMetrics);
    });
  });

  describe('fetchOrdersWithRiskParams', () => {
    it('should fetch orders with risk parameters without filters', async () => {
      const mockOrders = [
        { id: 'ord-1', symbol: 'BTCUSD', slPrice: 63500, tpPrice: 68000 }
      ];
      
      axios.get.mockResolvedValueOnce({ data: mockOrders });

      const result = await fetchOrdersWithRiskParams();
      
      expect(axios.get).toHaveBeenCalledWith('/api/v1/risk/orders?');
      expect(result).toEqual(mockOrders);
    });

    it('should fetch orders with risk parameters with filters', async () => {
      const mockOrders = [
        { id: 'ord-1', symbol: 'BTCUSD', slPrice: 63500, tpPrice: 68000 }
      ];
      
      const filters = { symbol: 'BTCUSD', status: 'active' };
      
      axios.get.mockResolvedValueOnce({ data: mockOrders });

      const result = await fetchOrdersWithRiskParams(filters);
      
      expect(axios.get).toHaveBeenCalledWith('/api/v1/risk/orders?symbol=BTCUSD&status=active');
      expect(result).toEqual(mockOrders);
    });
  });

  describe('updateOrderRiskParams', () => {
    it('should update order risk parameters successfully', async () => {
      const orderId = 'ord-1';
      const riskParams = { slPrice: 64000, tpPrice: 69000 };
      const mockResponse = { id: orderId, ...riskParams, updated: true };
      
      axios.put.mockResolvedValueOnce({ data: mockResponse });

      const result = await updateOrderRiskParams(orderId, riskParams);
      
      expect(axios.put).toHaveBeenCalledWith(`/api/v1/risk/orders/${orderId}`, riskParams);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getRiskLevelInfo', () => {
    it('should return Low risk level for values <= 30', () => {
      expect(getRiskLevelInfo(10)).toEqual({ level: 'Low', color: 'success' });
      expect(getRiskLevelInfo(30)).toEqual({ level: 'Low', color: 'success' });
    });

    it('should return Moderate risk level for values between 31 and 60', () => {
      expect(getRiskLevelInfo(31)).toEqual({ level: 'Moderate', color: 'warning' });
      expect(getRiskLevelInfo(60)).toEqual({ level: 'Moderate', color: 'warning' });
    });

    it('should return High risk level for values between 61 and 80', () => {
      expect(getRiskLevelInfo(61)).toEqual({ level: 'High', color: 'error' });
      expect(getRiskLevelInfo(80)).toEqual({ level: 'High', color: 'error' });
    });

    it('should return Critical risk level for values > 80', () => {
      expect(getRiskLevelInfo(81)).toEqual({ level: 'Critical', color: 'error' });
      expect(getRiskLevelInfo(100)).toEqual({ level: 'Critical', color: 'error' });
    });
  });

  describe('executeEmergencyStop', () => {
    it('should execute emergency stop successfully', async () => {
      const mockResponse = { success: true, message: 'All positions closed' };
      
      axios.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await executeEmergencyStop();
      
      expect(axios.post).toHaveBeenCalledWith('/api/v1/risk/emergency-stop');
      expect(result).toEqual(mockResponse);
    });
  });
}); 