import api from './api';

const transferApi = {
  // User-to-User Transfers
  createUserTransfer: (transferData) => 
    api.post('/transfers/user-to-user', transferData),
    
  getTransferHistory: (limit = 50) => 
    api.get('/transfers/history', { params: { limit } }),
    
  searchUsers: (query) => 
    api.get('/users/search', { params: { query } }),
    
  // Transfer validation
  validateTransfer: (transferData) => 
    api.post('/transfers/validate', transferData),
    
  // Cancel pending transfer (if implemented)
  cancelTransfer: (transferId) => 
    api.delete(`/transfers/${transferId}`),
    
  // Get transfer details
  getTransferDetails: (transferId) => 
    api.get(`/transfers/${transferId}`)
};

export { transferApi };