import React, { useState, useEffect } from 'react';
import { userProfileService } from '../services/userProfileApi';
import { formatCurrency, formatDate } from '../utils/format';
import LoadingSpinner from './LoadingSpinner';

const UserProfilePage = () => {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferLoading, setTransferLoading] = useState(false);
  const [notification, setNotification] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      const response = await userProfileService.getUserProfile();
      setProfileData(response.data);
    } catch (err) {
      setError('Failed to load profile data');
      console.error('Profile error:', err);
    } finally {
      setLoading(false);
    }
  };

  const showNotificationMessage = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleTransferSuccess = () => {
    showNotificationMessage('Transfer completed successfully!');
    loadProfileData(); // Refresh data
    setShowTransferModal(false);
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
        <h1 className="text-3xl font-bold text-gray-900">User Profile</h1>
        <p className="mt-2 text-gray-600">
          Comprehensive view of your financial accounts and transfer capabilities
        </p>
      </div>

      {/* User Info Card */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Personal Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500">Full Name</label>
            <p className="text-lg text-gray-900">{profileData?.user_info?.full_name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Email</label>
            <p className="text-lg text-gray-900">{profileData?.user_info?.email}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Phone Number</label>
            <p className="text-lg text-gray-900">{profileData?.user_info?.phone_number || 'Not provided'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Member Since</label>
            <p className="text-lg text-gray-900">{formatDate(profileData?.user_info?.created_at)}</p>
          </div>
        </div>
      </div>

      {/* Financial Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Total Balance</h3>
          <p className="text-3xl font-bold">
            {formatCurrency(profileData?.total_balance || 0, 'JD')}
          </p>
          <p className="text-blue-100 text-sm mt-2">
            Across {profileData?.summary?.total_accounts} accounts + wallet
          </p>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Wallet Balance</h3>
          <p className="text-2xl font-bold">
            {formatCurrency(profileData?.wallet_balance?.jd_balance || 0, 'JD')}
          </p>
          <p className="text-green-100 text-sm mt-2">
            + {formatCurrency(profileData?.wallet_balance?.dinarx_balance || 0, 'DINARX')}
          </p>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Bank Accounts</h3>
          <p className="text-2xl font-bold">
            {formatCurrency(profileData?.summary?.total_bank_balance || 0, 'JD')}
          </p>
          <p className="text-purple-100 text-sm mt-2">
            {profileData?.summary?.total_accounts} linked accounts
          </p>
        </div>
      </div>

      {/* Bank Accounts */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Bank Accounts</h2>
          <button
            onClick={() => setShowTransferModal(true)}
            className="btn-primary"
          >
            Transfer Money
          </button>
        </div>

        {profileData?.linked_accounts?.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-4">🏦</div>
            <p className="text-gray-500">No bank accounts linked</p>
            <p className="text-sm text-gray-400 mb-4">Connect your accounts to start transferring</p>
            <button
              onClick={() => window.location.href = '/open-banking'}
              className="btn-primary"
            >
              Connect Bank Accounts
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {profileData?.linked_accounts?.map((account) => (
              <div key={account.account_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{account.bank_name}</h3>
                    <p className="text-sm text-gray-600">{account.account_name}</p>
                    <p className="text-xs text-gray-500">**** {account.account_number.slice(-4)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(account.balance, 'JD')}
                    </p>
                    <p className="text-sm text-gray-500">
                      Available: {formatCurrency(account.available_balance, 'JD')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    account.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {account.status}
                  </span>
                  <button
                    onClick={() => {
                      setSelectedAccount(account);
                      setShowTransferModal(true);
                    }}
                    className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
                  >
                    Transfer
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Exchange Rates */}
      {Object.keys(profileData?.fx_rates || {}).length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Current Exchange Rates (JOD)</h2>
          
          {/* Account Context for FX Rates */}
          {profileData?.fx_rates?.account_context && (
            <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 text-sm text-blue-800">
                <span className="font-medium">🏦 Account-Dependent FX Data:</span>
                <span>Account ID: {profileData.fx_rates.account_context.account_id}</span>
                <span>•</span>
                <span>Base Currency: {profileData.fx_rates.account_context.account_currency}</span>
              </div>
            </div>
          )}
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(profileData.fx_rates).map(([currency, rate]) => {
              // Skip the account_context entry
              if (currency === 'account_context') return null;
              
              return (
                <div key={currency} className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700">{currency}</p>
                  <p className="text-lg font-bold text-gray-900">{rate}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Transfers */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Transfers</h2>
        
        {profileData?.recent_transfers?.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-4">📝</div>
            <p className="text-gray-500">No recent transfers</p>
          </div>
        ) : (
          <div className="space-y-4">
            {profileData?.recent_transfers?.map((transfer) => (
              <div key={transfer.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                    transfer.type === 'transfer' 
                      ? 'bg-blue-100 text-blue-600'
                      : transfer.type === 'exchange'
                      ? 'bg-yellow-100 text-yellow-600'
                      : 'bg-green-100 text-green-600'
                  }`}>
                    <span className="font-semibold">
                      {transfer.type === 'transfer' ? '↔' : 
                       transfer.type === 'exchange' ? '⇄' : '↗'}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {transfer.type === 'transfer' ? 'Transfer' : 
                       transfer.type === 'exchange' ? 'Exchange' : 'Deposit'}
                    </p>
                    <p className="text-sm text-gray-500">
                      {transfer.description || 'No description'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">
                    {formatCurrency(transfer.amount, transfer.currency)}
                  </p>
                  <p className="text-sm text-gray-500">
                    {formatDate(transfer.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Transfer Modal */}
      {showTransferModal && (
        <TransferModal
          accounts={profileData?.linked_accounts || []}
          selectedAccount={selectedAccount}
          onClose={() => {
            setShowTransferModal(false);
            setSelectedAccount(null);
          }}
          onSuccess={handleTransferSuccess}
          setTransferLoading={setTransferLoading}
          transferLoading={transferLoading}
        />
      )}
    </div>
  );
};

// Transfer Modal Component
const TransferModal = ({ accounts, selectedAccount, onClose, onSuccess, setTransferLoading, transferLoading }) => {
  const [formData, setFormData] = useState({
    from_account_id: selectedAccount?.account_id || '',
    to_account_id: 'wallet_jd',
    amount: '',
    currency: 'JOD',
    description: ''
  });
  const [fxQuote, setFxQuote] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (formData.to_account_id !== 'wallet_jd' && formData.amount) {
      fetchFXQuote();
    }
  }, [formData.to_account_id, formData.amount]);

  const fetchFXQuote = async () => {
    try {
      const response = await userProfileService.getFXQuote('DINARX', parseFloat(formData.amount));
      setFxQuote(response.data);
    } catch (err) {
      console.error('FX Quote error:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newErrors = {};
    if (!formData.from_account_id) newErrors.from_account_id = 'Please select source account';
    if (!formData.amount || parseFloat(formData.amount) <= 0) newErrors.amount = 'Please enter valid amount';
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setTransferLoading(true);
      await userProfileService.createTransfer(formData);
      onSuccess();
    } catch (err) {
      console.error('Transfer error:', err);
      setErrors({ submit: err.response?.data?.detail || 'Transfer failed' });
    } finally {
      setTransferLoading(false);
    }
  };

  const getAvailableBalance = () => {
    const account = accounts.find(acc => acc.account_id === formData.from_account_id);
    return account ? account.available_balance : 0;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">Transfer Money</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Account
            </label>
            <select
              value={formData.from_account_id}
              onChange={(e) => setFormData(prev => ({ ...prev, from_account_id: e.target.value }))}
              className={`form-input ${errors.from_account_id ? 'error' : ''}`}
            >
              <option value="">Select source account</option>
              {accounts.map(account => (
                <option key={account.account_id} value={account.account_id}>
                  {account.bank_name} - {formatCurrency(account.available_balance, 'JD')}
                </option>
              ))}
            </select>
            {errors.from_account_id && <p className="text-red-600 text-sm mt-1">{errors.from_account_id}</p>}
            {formData.from_account_id && (
              <p className="text-sm text-gray-500 mt-1">
                Available: {formatCurrency(getAvailableBalance(), 'JD')}
              </p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To Account
            </label>
            <select
              value={formData.to_account_id}
              onChange={(e) => setFormData(prev => ({ ...prev, to_account_id: e.target.value }))}
              className="form-input"
            >
              <option value="wallet_jd">My JD Wallet</option>
              {accounts.filter(acc => acc.account_id !== formData.from_account_id).map(account => (
                <option key={account.account_id} value={account.account_id}>
                  {account.bank_name} - {account.account_name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount (JOD)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              max={getAvailableBalance()}
              value={formData.amount}
              onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
              className={`form-input ${errors.amount ? 'error' : ''}`}
              placeholder="Enter amount"
            />
            {errors.amount && <p className="text-red-600 text-sm mt-1">{errors.amount}</p>}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="form-input"
              placeholder="Transfer description"
            />
          </div>

          {fxQuote && (
            <div className="bg-blue-50 p-3 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>Exchange Rate:</strong> 1 JOD = {fxQuote.rate} {fxQuote.targetCurrency}
              </p>
              {fxQuote.convertedAmount && (
                <p className="text-sm text-blue-800">
                  You will receive: {fxQuote.convertedAmount} {fxQuote.targetCurrency}
                </p>
              )}
            </div>
          )}

          {errors.submit && (
            <div className="bg-red-50 p-3 rounded-md">
              <p className="text-sm text-red-800">{errors.submit}</p>
            </div>
          )}
          
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-outline flex-1"
              disabled={transferLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={transferLoading || !formData.from_account_id || !formData.amount}
              className="btn-primary flex-1"
            >
              {transferLoading ? <LoadingSpinner size="sm" color="white" /> : 'Transfer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserProfilePage;