import apiService from '../../../../src/frontend/services/apiService';
import riskManagementService from '../../../../src/frontend/services/riskManagementService';

// Mock the API service
jest.mock('../../../../src/frontend/services/apiService');

describe('Risk Management Service', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  describe('Risk Profile Methods', () => {
    test('getRiskProfiles should call API with correct endpoint', async () => {
      // Setup mock response
      const mockProfiles = [
        { id: '1', name: 'Conservative', maxRisk: 2 },
        { id: '2', name: 'Moderate', maxRisk: 5 },
        { id: '3', name: 'Aggressive', maxRisk: 10 }
      ];
      apiService.get.mockResolvedValue(mockProfiles);

      // Call the service method
      const result = await riskManagementService.getRiskProfiles();

      // Assertions
      expect(apiService.get).toHaveBeenCalledWith('/risk-profiles');
      expect(result).toEqual(mockProfiles);
    });

    test('getRiskProfileById should call API with correct endpoint and ID', async () => {
      // Setup mock response
      const mockProfile = { id: '2', name: 'Moderate', maxRisk: 5 };
      apiService.get.mockResolvedValue(mockProfile);

      // Call the service method
      const result = await riskManagementService.getRiskProfileById('2');

      // Assertions
      expect(apiService.get).toHaveBeenCalledWith('/risk-profiles/2');
      expect(result).toEqual(mockProfile);
    });

    test('createRiskProfile should call API with correct endpoint and data', async () => {
      // Setup mock data and response
      const profileData = { name: 'Custom', maxRisk: 7 };
      const mockResponse = { id: '4', ...profileData };
      apiService.post.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.createRiskProfile(profileData);

      // Assertions
      expect(apiService.post).toHaveBeenCalledWith('/risk-profiles', profileData);
      expect(result).toEqual(mockResponse);
    });

    test('updateRiskProfile should call API with correct endpoint, ID and data', async () => {
      // Setup mock data and response
      const profileId = '2';
      const profileData = { name: 'Updated', maxRisk: 6 };
      const mockResponse = { id: profileId, ...profileData };
      apiService.put.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.updateRiskProfile(profileId, profileData);

      // Assertions
      expect(apiService.put).toHaveBeenCalledWith('/risk-profiles/2', profileData);
      expect(result).toEqual(mockResponse);
    });

    test('deleteRiskProfile should call API with correct endpoint and ID', async () => {
      // Setup mock response
      const mockResponse = { success: true };
      apiService.delete.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.deleteRiskProfile('3');

      // Assertions
      expect(apiService.delete).toHaveBeenCalledWith('/risk-profiles/3');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Risk Settings Methods', () => {
    test('getRiskSettings should call API with correct endpoint', async () => {
      // Setup mock response
      const mockSettings = {
        defaultRiskPercentage: 2,
        maxRiskPercentage: 5,
        defaultRiskRewardRatio: 2,
        minimumRiskRewardRatio: 1.5
      };
      apiService.get.mockResolvedValue(mockSettings);

      // Call the service method
      const result = await riskManagementService.getRiskSettings();

      // Assertions
      expect(apiService.get).toHaveBeenCalledWith('/risk-settings');
      expect(result).toEqual(mockSettings);
    });

    test('updateRiskSettings should call API with correct endpoint and data', async () => {
      // Setup mock data and response
      const settingsData = {
        defaultRiskPercentage: 1.5,
        maxRiskPercentage: 4,
        defaultRiskRewardRatio: 2.5,
        minimumRiskRewardRatio: 2
      };
      const mockResponse = { ...settingsData, updated: true };
      apiService.put.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.updateRiskSettings(settingsData);

      // Assertions
      expect(apiService.put).toHaveBeenCalledWith('/risk-settings', settingsData);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Calculation Methods', () => {
    test('calculatePositionSize should call API with correct endpoint and parameters', async () => {
      // Setup mock data and response
      const params = {
        accountSize: 10000,
        riskPercentage: 2,
        entryPrice: 150.5,
        stopLoss: 148.75,
        symbol: 'AAPL'
      };
      const mockResponse = {
        positionSize: 1145,
        riskAmount: 200,
        riskPerShare: 1.75
      };
      apiService.post.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.calculatePositionSize(params);

      // Assertions
      expect(apiService.post).toHaveBeenCalledWith('/position-size', params);
      expect(result).toEqual(mockResponse);
    });

    test('calculateRiskReward should call API with correct endpoint and parameters', async () => {
      // Setup mock data and response
      const params = {
        entryPrice: 150.5,
        stopLoss: 148.75,
        takeProfit: 155.25
      };
      const mockResponse = {
        riskRewardRatio: 2.5,
        riskAmount: 1.75,
        rewardAmount: 4.75
      };
      apiService.post.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.calculateRiskReward(params);

      // Assertions
      expect(apiService.post).toHaveBeenCalledWith('/risk-reward', params);
      expect(result).toEqual(mockResponse);
    });

    test('assessTradeRisk should call API with correct endpoint and parameters', async () => {
      // Setup mock data and response
      const tradingSetup = {
        symbol: 'AAPL',
        direction: 'long',
        entryPrice: 150.5,
        stopLoss: 148.75,
        takeProfit: 155.25,
        position: 1145
      };
      const mockResponse = {
        riskLevel: 'medium',
        riskAmount: 200.38,
        rewardAmount: 543.88,
        riskRewardRatio: 2.71,
        recommendation: 'Consider position size reduction'
      };
      apiService.post.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.assessTradeRisk(tradingSetup);

      // Assertions
      expect(apiService.post).toHaveBeenCalledWith('/risk-calculations/assessment', tradingSetup);
      expect(result).toEqual(mockResponse);
    });

    test('validateTrade should call API with correct endpoint and parameters', async () => {
      // Setup mock data and response
      const tradeParams = {
        accountSize: 10000,
        positionSize: 1145,
        entryPrice: 150.5,
        stopLoss: 148.75,
        takeProfit: 155.25,
        symbol: 'AAPL'
      };
      const mockResponse = {
        isValid: true,
        validationResults: [
          { check: 'riskPercentage', passed: true, value: 2, limit: 3 },
          { check: 'riskRewardRatio', passed: true, value: 2.71, limit: 2 }
        ]
      };
      apiService.post.mockResolvedValue(mockResponse);

      // Call the service method
      const result = await riskManagementService.validateTrade(tradeParams);

      // Assertions
      expect(apiService.post).toHaveBeenCalledWith('/risk-calculations/validate', tradeParams);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Error Handling', () => {
    test('should propagate API errors', async () => {
      // Setup mock error
      const mockError = new Error('API error');
      apiService.get.mockRejectedValue(mockError);

      // Call the service method and expect it to throw
      await expect(riskManagementService.getRiskProfiles()).rejects.toThrow('API error');
    });
  });
}); 