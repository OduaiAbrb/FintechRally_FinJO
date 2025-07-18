import React, { useState, useEffect } from 'react';
import { transactionService } from '../services/api';
import { formatCurrency, formatDate, formatTransactionType, getTransactionIcon, getTransactionColor, getStatusColor } from '../utils/format';
import LoadingSpinner from './LoadingSpinner';

const TransactionsPage = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    fetchTransactions();
  }, [limit, offset]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await transactionService.getTransactions({ limit, offset });
      setTransactions(response.data.transactions);
    } catch (err) {
      setError('Failed to load transactions');
      console.error('Transactions error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredTransactions = transactions.filter(transaction => {
    if (filter === 'all') return true;
    return transaction.transaction_type === filter;
  });

  const transactionTypes = [
    { value: 'all', label: 'All Transactions' },
    { value: 'deposit', label: 'Deposits' },
    { value: 'withdrawal', label: 'Withdrawals' },
    { value: 'exchange', label: 'Exchanges' },
    { value: 'transfer', label: 'Transfers' },
  ];

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
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Transaction History</h1>
        <p className="mt-2 text-gray-600">
          Track all your wallet activities and transactions
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Filter by:</label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {transactionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Show:</label>
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value={10}>10 items</option>
            <option value={20}>20 items</option>
            <option value={50}>50 items</option>
            <option value={100}>100 items</option>
          </select>
        </div>
      </div>

      {/* Transactions */}
      <div className="bg-white rounded-lg shadow-md">
        {filteredTransactions.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📭</div>
            <p className="text-gray-500 text-lg">No transactions found</p>
            <p className="text-sm text-gray-400">
              {filter === 'all' 
                ? 'Start by adding funds to your wallet' 
                : `No ${filter} transactions found`}
            </p>
          </div>
        ) : (
          <div className="overflow-hidden">
            {/* Table header */}
            <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-sm font-medium text-gray-500 uppercase tracking-wider">
                <div>Type</div>
                <div>Amount</div>
                <div>Status</div>
                <div>Date</div>
                <div>Description</div>
              </div>
            </div>

            {/* Table body */}
            <div className="divide-y divide-gray-200">
              {filteredTransactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="px-6 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
                    {/* Type */}
                    <div className="flex items-center space-x-3">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center text-lg ${
                        transaction.transaction_type === 'deposit' 
                          ? 'bg-green-100 text-green-600'
                          : transaction.transaction_type === 'withdrawal'
                          ? 'bg-red-100 text-red-600'
                          : transaction.transaction_type === 'exchange'
                          ? 'bg-yellow-100 text-yellow-600'
                          : 'bg-blue-100 text-blue-600'
                      }`}>
                        {getTransactionIcon(transaction.transaction_type)}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {formatTransactionType(transaction.transaction_type)}
                        </p>
                        <p className="text-sm text-gray-500">
                          {transaction.currency}
                        </p>
                      </div>
                    </div>

                    {/* Amount */}
                    <div>
                      <p className={`font-semibold ${getTransactionColor(transaction.transaction_type)}`}>
                        {transaction.transaction_type === 'withdrawal' ? '-' : '+'}
                        {formatCurrency(transaction.amount, transaction.currency)}
                      </p>
                    </div>

                    {/* Status */}
                    <div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.status)}`}>
                        {transaction.status}
                      </span>
                    </div>

                    {/* Date */}
                    <div>
                      <p className="text-sm text-gray-900">
                        {formatDate(transaction.created_at)}
                      </p>
                    </div>

                    {/* Description */}
                    <div>
                      <p className="text-sm text-gray-600 truncate">
                        {transaction.description || 'No description'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Load more button */}
      {transactions.length === limit && (
        <div className="text-center mt-6">
          <button
            onClick={() => setOffset(offset + limit)}
            className="btn-outline"
          >
            Load More
          </button>
        </div>
      )}
    </div>
  );
};

export default TransactionsPage;