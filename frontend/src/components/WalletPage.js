import React, { useState, useEffect } from 'react';
import { walletService } from '../services/api';
import { formatCurrency } from '../utils/format';
import LoadingSpinner from './LoadingSpinner';

const WalletPage = () => {
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showExchangeModal, setShowExchangeModal] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchWalletData();
  }, []);

  const fetchWalletData = async () => {
    try {
      setLoading(true);
      const response = await walletService.getBalance();
      setWallet(response.data);
    } catch (err) {
      setError('Failed to load wallet data');
      console.error('Wallet error:', err);
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message, type = 'success') => {
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
        <h1 className="text-3xl font-bold text-gray-900">Your Wallet</h1>
        <p className="mt-2 text-gray-600">
          Manage your JD and DinarX balances
        </p>
      </div>

      {/* Balance cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="balance-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="balance-label">JD Balance</p>
              <p className="balance-display">
                {formatCurrency(wallet?.jd_balance || 0, 'JD')}
              </p>
            </div>
            <div className="text-white text-3xl opacity-80">
              💰
            </div>
          </div>
          <div className="exchange-rate">
            <p className="text-sm">1 JD = 1 DinarX</p>
          </div>
          <div className="quick-actions">
            <button
              onClick={() => setShowDepositModal(true)}
              className="quick-action-btn"
            >
              Add Funds
            </button>
            <button
              onClick={() => setShowExchangeModal(true)}
              className="quick-action-btn"
            >
              Exchange
            </button>
          </div>
        </div>

        <div className="balance-card-secondary">
          <div className="flex items-center justify-between">
            <div>
              <p className="balance-label">DinarX Balance</p>
              <p className="balance-display">
                {formatCurrency(wallet?.dinarx_balance || 0, 'DINARX')}
              </p>
            </div>
            <div className="text-white text-3xl opacity-80">
              🪙
            </div>
          </div>
          <div className="exchange-rate">
            <p className="text-sm">Pegged to Jordanian Dinar</p>
          </div>
          <div className="quick-actions">
            <button
              onClick={() => setShowExchangeModal(true)}
              className="quick-action-btn"
            >
              Exchange
            </button>
            <button className="quick-action-btn">
              Send
            </button>
          </div>
        </div>
      </div>

      {/* Wallet actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <div className="text-center">
            <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">💳</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Add Funds</h3>
            <p className="text-sm text-gray-600 mb-4">
              Deposit money to your JD wallet
            </p>
            <button
              onClick={() => setShowDepositModal(true)}
              className="btn-primary w-full"
            >
              Deposit
            </button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <div className="text-center">
            <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">⇄</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Exchange</h3>
            <p className="text-sm text-gray-600 mb-4">
              Convert between JD and DinarX
            </p>
            <button
              onClick={() => setShowExchangeModal(true)}
              className="btn-secondary w-full"
            >
              Exchange
            </button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <div className="text-center">
            <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🔄</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Transfer</h3>
            <p className="text-sm text-gray-600 mb-4">
              Send money to other users
            </p>
            <button
              disabled
              className="btn-outline w-full opacity-50 cursor-not-allowed"
            >
              Coming Soon
            </button>
          </div>
        </div>
      </div>

      {/* Deposit Modal */}
      {showDepositModal && (
        <DepositModal
          onClose={() => setShowDepositModal(false)}
          onSuccess={(message) => {
            showNotification(message);
            fetchWalletData();
          }}
          setActionLoading={setActionLoading}
          actionLoading={actionLoading}
        />
      )}

      {/* Exchange Modal */}
      {showExchangeModal && (
        <ExchangeModal
          wallet={wallet}
          onClose={() => setShowExchangeModal(false)}
          onSuccess={(message) => {
            showNotification(message);
            fetchWalletData();
          }}
          setActionLoading={setActionLoading}
          actionLoading={actionLoading}
        />
      )}
    </div>
  );
};

// Deposit Modal Component
const DepositModal = ({ onClose, onSuccess, setActionLoading, actionLoading }) => {
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('JD');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!amount || parseFloat(amount) <= 0) {
      return;
    }

    try {
      setActionLoading(true);
      await walletService.deposit({
        transaction_type: 'deposit',
        amount: parseFloat(amount),
        currency,
        description: description || `Deposit ${amount} ${currency}`,
      });
      
      onSuccess(`Successfully deposited ${formatCurrency(parseFloat(amount), currency)}`);
      onClose();
    } catch (error) {
      console.error('Deposit error:', error);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">Deposit Funds</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Currency
            </label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="form-input"
            >
              <option value="JD">Jordanian Dinar (JD)</option>
              <option value="DINARX">DinarX</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="form-input"
              placeholder="Enter amount"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-input"
              placeholder="Enter description"
            />
          </div>
          
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-outline flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-primary flex-1"
            >
              {actionLoading ? <LoadingSpinner size="sm" color="white" /> : 'Deposit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Exchange Modal Component
const ExchangeModal = ({ wallet, onClose, onSuccess, setActionLoading, actionLoading }) => {
  const [fromCurrency, setFromCurrency] = useState('JD');
  const [toCurrency, setToCurrency] = useState('DINARX');
  const [amount, setAmount] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!amount || parseFloat(amount) <= 0) {
      return;
    }

    try {
      setActionLoading(true);
      await walletService.exchange({
        from_currency: fromCurrency,
        to_currency: toCurrency,
        amount: parseFloat(amount),
      });
      
      onSuccess(`Successfully exchanged ${formatCurrency(parseFloat(amount), fromCurrency)} to ${toCurrency}`);
      onClose();
    } catch (error) {
      console.error('Exchange error:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const maxAmount = fromCurrency === 'JD' ? wallet?.jd_balance || 0 : wallet?.dinarx_balance || 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">Exchange Currency</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Currency
            </label>
            <select
              value={fromCurrency}
              onChange={(e) => {
                setFromCurrency(e.target.value);
                setToCurrency(e.target.value === 'JD' ? 'DINARX' : 'JD');
              }}
              className="form-input"
            >
              <option value="JD">Jordanian Dinar (JD)</option>
              <option value="DINARX">DinarX</option>
            </select>
            <p className="text-sm text-gray-500 mt-1">
              Available: {formatCurrency(maxAmount, fromCurrency)}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To Currency
            </label>
            <select
              value={toCurrency}
              onChange={(e) => setToCurrency(e.target.value)}
              className="form-input"
            >
              <option value="JD">Jordanian Dinar (JD)</option>
              <option value="DINARX">DinarX</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              max={maxAmount}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="form-input"
              placeholder="Enter amount"
              required
            />
          </div>
          
          <div className="bg-gray-50 p-3 rounded-md">
            <p className="text-sm text-gray-600">
              Exchange Rate: 1 JD = 1 DinarX
            </p>
            {amount && (
              <p className="text-sm font-medium text-gray-900 mt-1">
                You will receive: {formatCurrency(parseFloat(amount) || 0, toCurrency)}
              </p>
            )}
          </div>
          
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-outline flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading || maxAmount < parseFloat(amount)}
              className="btn-primary flex-1"
            >
              {actionLoading ? <LoadingSpinner size="sm" color="white" /> : 'Exchange'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default WalletPage;