import React, { useState, useEffect } from 'react';
import { transferApi } from '../services/transferApi';
import LoadingSpinner from './LoadingSpinner';

const TransferPage = () => {
  const [recipientSearch, setRecipientSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('JOD');
  const [description, setDescription] = useState('');
  const [transferHistory, setTransferHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadTransferHistory();
  }, []);

  const loadTransferHistory = async () => {
    try {
      setLoading(true);
      const response = await transferApi.getTransferHistory();
      setTransferHistory(response.data.transfers || []);
    } catch (err) {
      setError('Failed to load transfer history');
      console.error('Transfer history error:', err);
    } finally {
      setLoading(false);
    }
  };

  const searchUsers = async (query) => {
    if (query.length < 3) {
      setSearchResults([]);
      return;
    }

    try {
      setSearchLoading(true);
      const response = await transferApi.searchUsers(query);
      setSearchResults(response.data.users || []);
    } catch (err) {
      console.error('User search error:', err);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleRecipientSearch = (value) => {
    setRecipientSearch(value);
    setSelectedRecipient(null);
    searchUsers(value);
  };

  const selectRecipient = (user) => {
    setSelectedRecipient(user);
    setRecipientSearch(user.full_name);
    setSearchResults([]);
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    
    if (!selectedRecipient) {
      setError('Please select a recipient');
      return;
    }

    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const transferData = {
        recipient_identifier: selectedRecipient.email,
        amount: parseFloat(amount),
        currency,
        description
      };

      const response = await transferApi.createUserTransfer(transferData);
      
      setSuccess(`Transfer successful! Sent ${amount} ${currency} to ${selectedRecipient.full_name}`);
      
      // Reset form
      setRecipientSearch('');
      setSelectedRecipient(null);
      setAmount('');
      setDescription('');
      
      // Reload transfer history
      await loadTransferHistory();
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Transfer failed');
      console.error('Transfer error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Transfer Money</h1>
        <p className="mt-2 text-gray-600">
          Send money to other platform users instantly
        </p>
      </div>

      {/* Transfer Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Send Transfer</h2>
        
        <form onSubmit={handleTransfer} className="space-y-6">
          {/* Recipient Search */}
          <div className="relative">
            <label htmlFor="recipient" className="block text-sm font-medium text-gray-700 mb-2">
              Recipient
            </label>
            <input
              type="text"
              id="recipient"
              value={recipientSearch}
              onChange={(e) => handleRecipientSearch(e.target.value)}
              placeholder="Search by name, email, or phone..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
            
            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-md mt-1 max-h-60 overflow-y-auto">
                {searchResults.map((user) => (
                  <div
                    key={user.id}
                    onClick={() => selectRecipient(user)}
                    className="p-3 hover:bg-gray-100 cursor-pointer border-b border-gray-200 last:border-b-0"
                  >
                    <div className="font-medium text-gray-900">{user.full_name}</div>
                    <div className="text-sm text-gray-600">{user.email}</div>
                    {user.phone && <div className="text-sm text-gray-500">{user.phone}</div>}
                  </div>
                ))}
              </div>
            )}
            
            {searchLoading && (
              <div className="absolute right-3 top-10">
                <LoadingSpinner size="sm" />
              </div>
            )}
          </div>

          {/* Selected Recipient */}
          {selectedRecipient && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <span className="text-2xl">👤</span>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">
                    Selected: {selectedRecipient.full_name}
                  </p>
                  <p className="text-sm text-green-600">{selectedRecipient.email}</p>
                </div>
              </div>
            </div>
          )}

          {/* Amount and Currency */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
                Amount
              </label>
              <input
                type="number"
                id="amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                step="0.01"
                min="0.01"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-2">
                Currency
              </label>
              <select
                id="currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="JOD">JOD (Jordanian Dinar)</option>
                <option value="DINARX">DinarX</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <input
              type="text"
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this transfer for?"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !selectedRecipient || !amount}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <LoadingSpinner size="sm" /> : 'Send Transfer'}
          </button>
        </form>

        {/* Error and Success Messages */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-800">{success}</p>
          </div>
        )}
      </div>

      {/* Transfer History */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Transfer History</h2>
        
        {loading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : transferHistory.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-4">📊</div>
            <p className="text-gray-500">No transfers yet</p>
            <p className="text-sm text-gray-400">Your transfer history will appear here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {transferHistory.map((transfer) => (
              <div key={transfer.transaction_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">
                      {transfer.type === 'transfer_out' ? '↗️' : '↘️'}
                    </span>
                    <div>
                      <div className="font-medium text-gray-900">
                        {transfer.type === 'transfer_out' ? 'Sent to' : 'Received from'} {transfer.counterparty?.name}
                      </div>
                      <div className="text-sm text-gray-600">{transfer.description}</div>
                      <div className="text-sm text-gray-500">
                        {new Date(transfer.timestamp).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-semibold ${
                      transfer.type === 'transfer_out' ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {transfer.type === 'transfer_out' ? '-' : '+'}
                      {Math.abs(transfer.amount)} {transfer.currency}
                    </div>
                    <div className="text-sm text-gray-500 capitalize">{transfer.status}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TransferPage;