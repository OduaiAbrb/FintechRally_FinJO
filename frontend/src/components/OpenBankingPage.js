import React, { useState, useEffect } from 'react';
import { openBankingService } from '../services/openBankingApi';
import { formatCurrency, formatDate, formatTransactionType } from '../utils/format';
import LoadingSpinner from './LoadingSpinner';

const OpenBankingPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [consentLoading, setConsentLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await openBankingService.getOpenBankingDashboard();
      setDashboardData(response.data);
    } catch (err) {
      setError('Failed to load banking data');
      console.error('Open banking error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestConsent = async () => {
    try {
      setConsentLoading(true);
      
      // Use the new connect accounts endpoint
      const response = await openBankingService.connectBankAccounts();
      
      setNotification({
        type: 'success',
        message: 'Banking accounts connected successfully! Loading your accounts...'
      });
      
      // Update dashboard data with the connected accounts
      setDashboardData(response.data);
      
      // Close modal after a short delay
      setTimeout(() => {
        setShowConsentModal(false);
      }, 2000);
      
    } catch (err) {
      setNotification({
        type: 'error',
        message: 'Failed to connect banking accounts. Please try again.'
      });
      console.error('Account connection error:', err);
    } finally {
      setConsentLoading(false);
    }
  };

  const showNotificationMessage = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Notification */}
      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Open Banking</h1>
        <p className="mt-2 text-gray-600">
          Connect and manage all your bank accounts in one place
        </p>
        
        {/* API Call Sequence Information */}
        {dashboardData?.has_linked_accounts && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-blue-600 font-semibold">🔗 Account-Dependent API Flow:</span>
            </div>
            <div className="text-sm text-blue-800">
              <div className="flex items-center space-x-1">
                <span>1️⃣</span>
                <span className="font-medium">Accounts API</span>
                <span className="text-blue-600">(with x-customer-id)</span>
                <span>→</span>
                <span className="font-medium">Balance API</span>
                <span className="text-blue-600">(without x-customer-id)</span>
                <span>→</span>
                <span className="font-medium">FX API</span>
                <span className="text-blue-600">(account-dependent)</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {!dashboardData?.has_linked_accounts ? (
        // No linked accounts - show onboarding
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="h-24 w-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">🏦</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Connect Your Bank Accounts
            </h2>
            <p className="text-gray-600 mb-8">
              Securely link your Jordanian bank accounts to get a unified view of all your finances.
              We use Jordan Open Finance APIs to ensure maximum security and compliance.
            </p>
            <button
              onClick={() => setShowConsentModal(true)}
              className="btn-primary"
            >
              Connect Bank Accounts
            </button>
          </div>
        </div>
      ) : (
        // Has linked accounts - show dashboard
        <div className="space-y-8">
          {/* Total Balance Overview */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
            <h2 className="text-lg font-semibold mb-2">Total Balance Across All Accounts</h2>
            <p className="text-3xl font-bold">
              {formatCurrency(dashboardData.total_balance, 'JD')}
            </p>
            <p className="text-blue-100 mt-2">
              From {dashboardData.total_accounts} linked account{dashboardData.total_accounts !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Account Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dashboardData.accounts.map((account) => (
              <div key={account.account_id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-gray-900">{account.bank_name}</h3>
                    <p className="text-sm text-gray-600">{account.account_name}</p>
                  </div>
                  <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xl">
                      {account.account_type === 'current' ? '💳' : 
                       account.account_type === 'savings' ? '💰' : 
                       account.account_type === 'business' ? '🏢' : '🏦'}
                    </span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Balance:</span>
                    <span className="font-semibold">
                      {formatCurrency(account.balance, 'JD')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Available:</span>
                    <span className="font-semibold text-green-600">
                      {formatCurrency(account.available_balance, 'JD')}
                    </span>
                  </div>
                  {account.detailed_balances && account.detailed_balances.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="text-xs text-gray-500 mb-2">✅ Account-Dependent Balance Data:</div>
                      {account.detailed_balances.map((balance, index) => (
                        <div key={index} className="flex justify-between text-xs text-gray-600">
                          <span>{balance.type}:</span>
                          <span>{formatCurrency(balance.amount, balance.currency)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="mt-4 flex space-x-2">
                  <button 
                    onClick={() => showNotificationMessage('Account details feature coming soon')}
                    className="btn-outline flex-1 text-sm py-2"
                  >
                    View Details
                  </button>
                  <button 
                    onClick={() => showNotificationMessage('Payment initiation feature coming soon')}
                    className="btn-primary flex-1 text-sm py-2"
                  >
                    Send Money
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Recent Transactions */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Recent Transactions</h2>
              <button 
                onClick={() => showNotificationMessage('Full transaction history coming soon')}
                className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
              >
                View all
              </button>
            </div>

            {dashboardData.recent_transactions.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-gray-400 text-4xl mb-4">📊</div>
                <p className="text-gray-500">No recent transactions</p>
              </div>
            ) : (
              <div className="space-y-4">
                {dashboardData.recent_transactions.map((transaction) => (
                  <div
                    key={transaction.transaction_id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                        transaction.amount > 0 ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                      }`}>
                        <span className="font-semibold">
                          {transaction.amount > 0 ? '+' : '-'}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {transaction.description}
                        </p>
                        <p className="text-sm text-gray-500">
                          {transaction.account_name} • {transaction.merchant}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${
                        transaction.amount > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transaction.amount > 0 ? '+' : ''}
                        {formatCurrency(Math.abs(transaction.amount), transaction.currency)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatDate(transaction.transaction_date)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
              <div className="text-center">
                <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">💸</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Send Money</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Transfer money between accounts
                </p>
                <button
                  onClick={() => showNotificationMessage('Payment initiation feature coming soon')}
                  className="btn-primary w-full"
                >
                  Send Money
                </button>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
              <div className="text-center">
                <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🔄</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Currency Exchange</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Convert between currencies
                </p>
                <button
                  onClick={() => showNotificationMessage('FX service feature coming soon')}
                  className="btn-secondary w-full"
                >
                  Exchange
                </button>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
              <div className="text-center">
                <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">📋</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Financial Products</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Explore loans and cards
                </p>
                <button
                  onClick={() => showNotificationMessage('Financial products feature coming soon')}
                  className="btn-outline w-full"
                >
                  Explore
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Consent Modal */}
      {showConsentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Banking Consent</h3>
            
            <div className="space-y-4 mb-6">
              <p className="text-sm text-gray-600">
                To provide you with account aggregation and financial services, we need your consent to:
              </p>
              
              <ul className="space-y-2 text-sm">
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Access your account information and balances</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>View your transaction history</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Initiate payments on your behalf</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Access foreign exchange rates</span>
                </li>
              </ul>
              
              <div className="bg-blue-50 p-3 rounded-md">
                <p className="text-xs text-blue-800">
                  <strong>Secure:</strong> We use Jordan Open Finance APIs with bank-grade security.
                  Your data is encrypted and never stored permanently.
                </p>
              </div>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setShowConsentModal(false)}
                className="btn-outline flex-1"
                disabled={consentLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleRequestConsent}
                className="btn-primary flex-1"
                disabled={consentLoading}
              >
                {consentLoading ? <LoadingSpinner size="sm" color="white" /> : 'Grant Consent'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OpenBankingPage;