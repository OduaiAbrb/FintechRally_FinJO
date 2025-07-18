import api from './api';

const securityApi = {
  // Security System Management
  initializeSecurity: () => 
    api.post('/security/initialize'),
    
  getSecurityStatus: () => 
    api.get('/security/status'),

  // AML System
  initializeAML: () => 
    api.post('/aml/initialize'),
    
  getAMLDashboard: () => 
    api.get('/aml/dashboard'),
    
  getAMLAlerts: (filters = {}) => 
    api.get('/aml/alerts', { params: filters }),
    
  resolveAMLAlert: (alertId, resolutionData) => 
    api.post(`/aml/alerts/${alertId}/resolve`, resolutionData),
    
  getUserRiskProfile: (userId) => 
    api.get(`/aml/user-risk/${userId}`),

  // Biometric Authentication
  enrollBiometric: (biometricData) => 
    api.post('/biometric/enroll', biometricData),
    
  authenticateBiometric: (biometricData) => 
    api.post('/biometric/authenticate', biometricData),
    
  getUserBiometrics: async (userId = null) => {
    try {
      if (userId) {
        return api.get(`/biometric/user/${userId}`);
      }
      // Get current user's ID from token and use it
      const profileResponse = await api.get('/user/profile');
      const currentUserId = profileResponse.data.user_info.id;
      return api.get(`/biometric/user/${currentUserId}`);
    } catch (error) {
      // If profile call fails, return empty biometrics
      return { data: { biometrics: [] } };
    }
  },
    
  revokeBiometric: (templateId) => 
    api.delete(`/biometric/revoke/${templateId}`),
    
  getBiometricHistory: (limit = 50) => 
    api.get('/biometric/history', { params: { limit } }),

  // Risk Scoring
  getRiskAssessment: (userId, transactionData = null) => 
    api.get(`/risk/assessment/${userId}`, { params: { transaction_data: transactionData } }),
    
  getRiskHistory: (userId, limit = 10) => 
    api.get(`/risk/history/${userId}`, { params: { limit } }),
    
  getRiskDashboard: () => 
    api.get('/risk/dashboard'),

  // Enhanced Authentication
  enhancedLogin: (loginData) => 
    api.post('/auth/login-enhanced', loginData),

  // Utility Functions
  generateDeviceFingerprint: () => {
    // Generate a simple device fingerprint based on browser characteristics
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device fingerprint', 2, 2);
    
    const fingerprint = [
      navigator.userAgent,
      navigator.language,
      window.screen.width + 'x' + window.screen.height,
      new Date().getTimezoneOffset(),
      canvas.toDataURL()
    ].join('|');
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(16);
  },

  // Mock biometric data generation for demo purposes
  generateMockFaceData: () => {
    // Generate mock base64 image data for face recognition
    return btoa("mock_face_image_data_" + Date.now());
  },

  generateMockFingerprintData: () => {
    // Generate mock WebAuthn credential data
    return JSON.stringify({
      id: "mock_credential_" + Date.now(),
      response: {
        publicKey: btoa("mock_public_key_data"),
        clientDataJSON: btoa(JSON.stringify({
          type: "webauthn.create",
          challenge: btoa("mock_challenge"),
          origin: window.location.origin
        }))
      }
    });
  }
};

export { securityApi };