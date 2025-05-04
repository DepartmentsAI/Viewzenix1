import { useState, useEffect, useCallback } from 'react';
import riskManagementService from '../../services/riskManagementService';
import useNotification from './useNotification';

/**
 * React hook for risk management functionality
 * 
 * @returns {Object} Risk management methods and state
 */
const useRiskManagement = () => {
  const [riskProfiles, setRiskProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [riskSettings, setRiskSettings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const notification = useNotification();

  /**
   * Load all risk profiles
   */
  const loadRiskProfiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const profiles = await riskManagementService.getRiskProfiles();
      setRiskProfiles(profiles);
      return profiles;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to load risk profiles');
      return [];
    } finally {
      setLoading(false);
    }
  }, [notification]);

  /**
   * Load risk profile by ID
   * @param {string} profileId - Risk profile ID
   */
  const loadRiskProfile = useCallback(async (profileId) => {
    if (!profileId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const profile = await riskManagementService.getRiskProfileById(profileId);
      setSelectedProfile(profile);
      return profile;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, `Failed to load risk profile: ${profileId}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification]);

  /**
   * Create a new risk profile
   * @param {Object} profileData - Risk profile data
   */
  const createProfile = useCallback(async (profileData) => {
    setLoading(true);
    setError(null);
    
    try {
      const newProfile = await riskManagementService.createRiskProfile(profileData);
      setRiskProfiles(prev => [...prev, newProfile]);
      notification.success('Risk profile created successfully');
      return newProfile;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to create risk profile');
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification]);

  /**
   * Update an existing risk profile
   * @param {string} profileId - Risk profile ID
   * @param {Object} profileData - Updated risk profile data
   */
  const updateProfile = useCallback(async (profileId, profileData) => {
    setLoading(true);
    setError(null);
    
    try {
      const updatedProfile = await riskManagementService.updateRiskProfile(profileId, profileData);
      
      // Update the profiles list
      setRiskProfiles(prev => 
        prev.map(profile => profile.id === profileId ? updatedProfile : profile)
      );
      
      // Update selected profile if it's the one being edited
      if (selectedProfile && selectedProfile.id === profileId) {
        setSelectedProfile(updatedProfile);
      }
      
      notification.success('Risk profile updated successfully');
      return updatedProfile;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to update risk profile');
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification, selectedProfile]);

  /**
   * Delete a risk profile
   * @param {string} profileId - Risk profile ID
   */
  const deleteProfile = useCallback(async (profileId) => {
    setLoading(true);
    setError(null);
    
    try {
      await riskManagementService.deleteRiskProfile(profileId);
      
      // Remove from profiles list
      setRiskProfiles(prev => prev.filter(profile => profile.id !== profileId));
      
      // Clear selected profile if it's the one being deleted
      if (selectedProfile && selectedProfile.id === profileId) {
        setSelectedProfile(null);
      }
      
      notification.success('Risk profile deleted successfully');
      return true;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to delete risk profile');
      return false;
    } finally {
      setLoading(false);
    }
  }, [notification, selectedProfile]);

  /**
   * Load risk settings
   */
  const loadRiskSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const settings = await riskManagementService.getRiskSettings();
      setRiskSettings(settings);
      return settings;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to load risk settings');
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification]);

  /**
   * Update risk settings
   * @param {Object} settingsData - Updated risk settings
   */
  const updateSettings = useCallback(async (settingsData) => {
    setLoading(true);
    setError(null);
    
    try {
      const updatedSettings = await riskManagementService.updateRiskSettings(settingsData);
      setRiskSettings(updatedSettings);
      notification.success('Risk settings updated successfully');
      return updatedSettings;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to update risk settings');
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification]);

  /**
   * Calculate position size
   * @param {Object} params - Position size parameters
   */
  const calculatePosition = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await riskManagementService.calculatePositionSize(params);
      return result;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to calculate position size');
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification]);

  /**
   * Calculate risk/reward ratio
   * @param {Object} params - Risk/reward parameters
   */
  const calculateRiskReward = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await riskManagementService.calculateRiskReward(params);
      return result;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to calculate risk/reward ratio');
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification]);

  /**
   * Validate a trade against risk criteria
   * @param {Object} tradeParams - Trade parameters
   */
  const validateTrade = useCallback(async (tradeParams) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await riskManagementService.validateTrade(tradeParams);
      
      // Show warning notification if the trade doesn't meet risk criteria
      if (!result.isValid) {
        notification.warning('Trade does not meet risk criteria', {
          details: result.reason || 'Check risk parameters and try again'
        });
      }
      
      return result;
    } catch (err) {
      setError(err);
      notification.handleApiError(err, 'Failed to validate trade');
      return null;
    } finally {
      setLoading(false);
    }
  }, [notification]);

  // Load profiles on mount
  useEffect(() => {
    loadRiskProfiles();
  }, [loadRiskProfiles]);

  return {
    // State
    riskProfiles,
    selectedProfile,
    riskSettings,
    loading,
    error,
    
    // Profile methods
    loadRiskProfiles,
    loadRiskProfile,
    createProfile,
    updateProfile,
    deleteProfile,
    
    // Settings methods
    loadRiskSettings,
    updateSettings,
    
    // Calculation methods
    calculatePosition,
    calculateRiskReward,
    validateTrade
  };
};

export default useRiskManagement; 