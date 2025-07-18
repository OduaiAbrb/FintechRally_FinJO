import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import LoadingSpinner from './LoadingSpinner';

const OffersPage = () => {
  const [offers, setOffers] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingOffers, setLoadingOffers] = useState(false);
  const [customerId, setCustomerId] = useState('IND_CUST_015');
  const [showCustomerForm, setShowCustomerForm] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchAccounts();
  }, [customerId]);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/open-banking/accounts', {
        headers: {
          'x-customer-id': customerId
        }
      });
      setAccounts(response.data.accounts || []);
      
      // Auto-select first account if available
      if (response.data.accounts && response.data.accounts.length > 0) {
        const firstAccount = response.data.accounts[0];
        setSelectedAccount(firstAccount.account_id);
        fetchOffers(firstAccount.account_id);
      }
    } catch (err) {
      setError('Failed to fetch accounts');
      console.error('Error fetching accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOffers = async (accountId) => {
    if (!accountId) return;
    
    setLoadingOffers(true);
    setError(null);
    
    try {
      const response = await api.get(`/open-banking/accounts/${accountId}/offers`, {
        headers: {
          'x-customer-id': customerId
        }
      });
      setOffers(response.data.offers || []);
    } catch (err) {
      setError('Failed to fetch offers');
      console.error('Error fetching offers:', err);
    } finally {
      setLoadingOffers(false);
    }
  };

  const handleAccountChange = (accountId) => {
    setSelectedAccount(accountId);
    fetchOffers(accountId);
  };

  const handleCustomerIdChange = (e) => {
    e.preventDefault();
    setShowCustomerForm(false);
    setSelectedAccount('');
    setOffers([]);
    fetchAccounts();
  };

  const getOfferTypeColor = (offerType) => {
    switch (offerType?.toLowerCase()) {
      case 'loan':
        return 'bg-blue-100 text-blue-800';
      case 'credit':
        return 'bg-green-100 text-green-800';
      case 'savings':
        return 'bg-purple-100 text-purple-800';
      case 'investment':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Bank Offers</h1>
          <p className="mt-2 text-gray-600">
            Explore personalized offers from your linked bank accounts
          </p>
          
          {/* Customer ID Management */}
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="text-blue-600 font-semibold">🎯 JoPACC Customer ID</span>
                <span className="text-sm text-blue-800">Current: {customerId}</span>
              </div>
              <button
                onClick={() => setShowCustomerForm(!showCustomerForm)}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                {showCustomerForm ? 'Cancel' : 'Change Customer ID'}
              </button>
            </div>
            
            {showCustomerForm && (
              <form onSubmit={handleCustomerIdChange} className="mt-3">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter customer ID (e.g., IND_CUST_015)"
                  />
                  <button
                    type="submit"
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200"
                  >
                    Update
                  </button>
                </div>
              </form>
            )}
            
            <div className="text-sm text-blue-800 mt-2">
              <div className="flex items-center space-x-1">
                <span>API Endpoint:</span>
                <span className="font-medium">JoPACC Offers API</span>
                <span>•</span>
                <span>Account-dependent offers</span>
              </div>
            </div>
          </div>
        </div>

        {/* Account Selection */}
        {accounts.length > 0 && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Account for Offers
            </label>
            <select
              value={selectedAccount}
              onChange={(e) => handleAccountChange(e.target.value)}
              className="block w-full max-w-md px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose an account...</option>
              {accounts.map((account) => (
                <option key={account.account_id} value={account.account_id}>
                  {account.account_name} - {account.bank_name} ({account.balance} JOD)
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-red-600 font-medium">⚠️ {error}</span>
            </div>
          </div>
        )}

        {/* Offers Loading */}
        {loadingOffers && (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        )}

        {/* Offers Grid */}
        {!loadingOffers && offers.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {offers.map((offer, index) => (
              <div key={offer.offerId || index} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                <div className="p-6">
                  {/* Offer Type Badge */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getOfferTypeColor(offer.offerType)}`}>
                      {offer.offerType || 'General'}
                    </span>
                    <span className="text-sm text-gray-500">
                      {offer.priority || 'Standard'}
                    </span>
                  </div>

                  {/* Offer Title */}
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {offer.title || offer.offerName || 'Bank Offer'}
                  </h3>

                  {/* Offer Description */}
                  <p className="text-gray-600 text-sm mb-4">
                    {offer.description || 'Special offer available for your account'}
                  </p>

                  {/* Offer Details */}
                  <div className="space-y-2 mb-4">
                    {offer.interestRate && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Interest Rate:</span>
                        <span className="font-medium">{offer.interestRate}%</span>
                      </div>
                    )}
                    {offer.amount && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Amount:</span>
                        <span className="font-medium">{offer.amount} JOD</span>
                      </div>
                    )}
                    {offer.validUntil && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Valid Until:</span>
                        <span className="font-medium">
                          {new Date(offer.validUntil).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Action Button */}
                  <div className="flex space-x-2">
                    <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200 text-sm font-medium">
                      View Details
                    </button>
                    <button className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors duration-200 text-sm font-medium">
                      Apply Now
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* No Offers Message */}
        {!loadingOffers && offers.length === 0 && selectedAccount && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">🎁</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No offers available</h3>
            <p className="text-gray-600">
              There are currently no offers available for the selected account.
            </p>
          </div>
        )}

        {/* No Accounts Message */}
        {accounts.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">🏦</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No linked accounts</h3>
            <p className="text-gray-600 mb-4">
              Connect your bank accounts to see personalized offers.
            </p>
            <button 
              onClick={() => setShowCustomerForm(true)}
              className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200"
            >
              Update Customer ID
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OffersPage;