import api from './api';

// Hey Dinar AI API service functions
export const heyDinarService = {
  // Chat with AI assistant
  sendMessage: (message) => 
    api.post('/hey-dinar/chat', { message }),
  
  // Get conversation history
  getConversationHistory: (params) => 
    api.get('/hey-dinar/conversation', { params }),
  
  // Get quick action buttons
  getQuickActions: () => 
    api.get('/hey-dinar/quick-actions'),
  
  // Clear chat history
  clearConversationHistory: () => 
    api.delete('/hey-dinar/conversation'),
};

export default heyDinarService;