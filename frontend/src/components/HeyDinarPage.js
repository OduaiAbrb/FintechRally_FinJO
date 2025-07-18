import React, { useState, useEffect, useRef } from 'react';
import { heyDinarService } from '../services/heyDinarApi';
import { formatDate } from '../utils/format';
import LoadingSpinner from './LoadingSpinner';

const HeyDinarPage = () => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [quickActions, setQuickActions] = useState([]);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    loadConversationHistory();
    loadQuickActions();
    
    // Add welcome message
    const welcomeMessage = {
      id: 'welcome',
      type: 'ai',
      message: "Hello! I'm Hey Dinar, your AI financial assistant. I can help you check your balance, analyze spending, view transactions, and provide financial advice. How can I assist you today?",
      timestamp: new Date(),
      intent: 'greeting',
      confidence: 1.0
    };
    setMessages([welcomeMessage]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversationHistory = async () => {
    try {
      setIsLoading(true);
      const response = await heyDinarService.getConversationHistory();
      const history = response.data.conversations.map(conv => [
        {
          id: conv.id + '_user',
          type: 'user',
          message: conv.message,
          timestamp: new Date(conv.timestamp),
        },
        {
          id: conv.id + '_ai',
          type: 'ai',
          message: conv.response,
          timestamp: new Date(conv.timestamp),
          intent: conv.intent,
          confidence: conv.confidence,
        }
      ]).flat();
      
      if (history.length > 0) {
        setMessages(history);
      }
    } catch (err) {
      console.error('Error loading conversation history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadQuickActions = async () => {
    try {
      const response = await heyDinarService.getQuickActions();
      setQuickActions(response.data.quick_actions);
    } catch (err) {
      console.error('Error loading quick actions:', err);
    }
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      message: messageText,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsTyping(true);
    setError(null);

    try {
      const response = await heyDinarService.sendMessage(messageText);
      const aiMessage = {
        id: response.data.message_id,
        type: 'ai',
        message: response.data.ai_response,
        timestamp: new Date(response.data.timestamp),
        intent: response.data.intent,
        confidence: response.data.confidence,
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      setError('Sorry, I encountered an error processing your message. Please try again.');
      console.error('Error sending message:', err);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(currentMessage);
  };

  const handleQuickAction = (action) => {
    sendMessage(action.query);
  };

  const clearHistory = async () => {
    try {
      await heyDinarService.clearConversationHistory();
      setMessages([]);
      // Add welcome message back
      const welcomeMessage = {
        id: 'welcome',
        type: 'ai',
        message: "Hello! I'm Hey Dinar, your AI financial assistant. How can I assist you today?",
        timestamp: new Date(),
        intent: 'greeting',
        confidence: 1.0
      };
      setMessages([welcomeMessage]);
    } catch (err) {
      console.error('Error clearing history:', err);
    }
  };

  const formatAIMessage = (message) => {
    // Convert markdown-style formatting to JSX
    return message.split('\n').map((line, index) => {
      if (line.startsWith('**') && line.endsWith('**')) {
        return (
          <div key={index} className="font-semibold text-gray-900 mb-2">
            {line.replace(/\*\*/g, '')}
          </div>
        );
      } else if (line.startsWith('• ')) {
        return (
          <div key={index} className="ml-4 text-gray-700 mb-1">
            {line}
          </div>
        );
      } else if (line.trim() === '') {
        return <br key={index} />;
      } else {
        return (
          <div key={index} className="text-gray-700 mb-1">
            {line}
          </div>
        );
      }
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-12 w-12 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Hey Dinar</h1>
              <p className="text-gray-600">Your AI Financial Assistant</p>
            </div>
          </div>
          <button
            onClick={clearHistory}
            className="btn-outline text-sm"
          >
            Clear History
          </button>
        </div>
      </div>

      {/* Chat Container */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Messages */}
        <div className="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {isLoading && (
            <div className="flex justify-center">
              <LoadingSpinner size="md" />
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}>
                {message.type === 'ai' ? (
                  <div className="whitespace-pre-wrap">
                    {formatAIMessage(message.message)}
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap">{message.message}</div>
                )}
                <div className={`text-xs mt-1 ${
                  message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {formatDate(message.timestamp)}
                  {message.intent && (
                    <span className="ml-2">
                      • {message.intent} ({Math.round(message.confidence * 100)}%)
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 border border-gray-200 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="text-gray-500">Hey Dinar is typing...</span>
                </div>
              </div>
            </div>
          )}
          
          {error && (
            <div className="flex justify-start">
              <div className="bg-red-50 text-red-800 border border-red-200 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                {error}
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        {quickActions.length > 0 && (
          <div className="p-4 bg-gray-100 border-t border-gray-200">
            <div className="flex flex-wrap gap-2">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action)}
                  className="px-3 py-1 bg-white text-gray-700 border border-gray-300 rounded-full text-sm hover:bg-gray-50 transition-colors"
                >
                  {action.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-gray-200">
          <div className="flex space-x-4">
            <input
              ref={inputRef}
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder="Ask me about your finances..."
              className="flex-1 form-input"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={isTyping || !currentMessage.trim()}
              className="btn-primary"
            >
              {isTyping ? (
                <LoadingSpinner size="sm" color="white" />
              ) : (
                'Send'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Features Info */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
            <span className="text-2xl">💰</span>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Balance & Spending</h3>
          <p className="text-sm text-gray-600">
            Ask about your balances, spending patterns, and transaction history across all accounts.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
            <span className="text-2xl">🎯</span>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Smart Insights</h3>
          <p className="text-sm text-gray-600">
            Get personalized financial insights and advice based on your spending patterns.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
            <span className="text-2xl">🔍</span>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Natural Language</h3>
          <p className="text-sm text-gray-600">
            Ask questions in plain English. No need to learn commands or complex syntax.
          </p>
        </div>
      </div>
    </div>
  );
};

export default HeyDinarPage;