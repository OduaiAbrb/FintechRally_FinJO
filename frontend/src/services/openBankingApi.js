import api from './api';

// Open Banking API service functions
export const openBankingService = {
  // Consent Management
  requestConsent: (permissions) => 
    api.post('/open-banking/consent', { permissions }),
  
  connectBankAccounts: () => 
    api.post('/open-banking/connect-accounts'),
  
  // Account Information Services (AIS)
  getLinkedAccounts: () => 
    api.get('/open-banking/accounts'),
  
  getAccountBalance: (accountId) => 
    api.get(`/open-banking/accounts/${accountId}/balance`),
  
  getAccountTransactions: (accountId, params) => 
    api.get(`/open-banking/accounts/${accountId}/transactions`, { params }),
  
  // Payment Initiation Services (PIS)
  initiatePayment: (paymentData) => 
    api.post('/open-banking/payments', paymentData),
  
  getPaymentStatus: (paymentId) => 
    api.get(`/open-banking/payments/${paymentId}`),
  
  // Foreign Exchange (FX)
  getExchangeRates: (baseCurrency = 'JOD') => 
    api.get('/open-banking/fx/rates', { params: { base_currency: baseCurrency } }),
  
  convertCurrency: (fromCurrency, toCurrency, amount) => 
    api.post('/open-banking/fx/convert', {}, { 
      params: { from_currency: fromCurrency, to_currency: toCurrency, amount } 
    }),
  
  // Financial Products Services (FPS)
  getFinancialProducts: () => 
    api.get('/open-banking/products'),
  
  // Dashboard
  getOpenBankingDashboard: () => 
    api.get('/open-banking/dashboard'),
};

export default openBankingService;