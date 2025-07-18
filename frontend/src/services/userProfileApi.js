import api from './api';

// User Profile API service functions
export const userProfileService = {
  // Get comprehensive user profile
  getUserProfile: () => 
    api.get('/user/profile'),
  
  // Create transfer between accounts or to wallet
  createTransfer: (transferData) => 
    api.post('/user/transfer', transferData),
  
  // Get FX quote for currency conversion
  getFXQuote: (targetCurrency, amount) => 
    api.get('/user/fx-quote', { 
      params: { target_currency: targetCurrency, amount } 
    }),
};

export default userProfileService;