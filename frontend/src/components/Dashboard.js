import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { formatCurrency, formatDate } from '../utils/format';
import LoadingSpinner from './LoadingSpinner';
import api from '../services/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [dashboardResponse, walletResponse] = await Promise.all([
        api.get('/open-banking/dashboard'),
        api.get('/wallet')
      ]);

      setDashboardData(dashboardResponse.data);
      setWallet(walletResponse.data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 mb-4">⚠️ {error}</div>
          <button 
            onClick={fetchDashboardData}
            className="bg-amber-600 text-white px-4 py-2 rounded-md hover:bg-amber-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.full_name || 'User'}! 👋
          </h1>
          <p className="mt-2 text-gray-600">
            Here's what's happening with your DinarX wallet today.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* DinarX Balance */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-amber-100">
                <span className="text-2xl">💰</span>
              </div>
              <div className="ml-4">
                <p className="balance-label">DinarX Balance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(wallet?.dinarx_balance || 0, 'DINARX')}
                </p>
              </div>
            </div>
          </div>

          {/* JD Balance */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100">
                <span className="text-2xl">💵</span>
              </div>
              <div className="ml-4">
                <p className="balance-label">JD Balance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(wallet?.jd_balance || 0, 'JOD')}
                </p>
              </div>
            </div>
          </div>

          {/* Total Bank Balance */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100">
                <span className="text-2xl">🏦</span>
              </div>
              <div className="ml-4">
                <p className="balance-label">Total Bank Balance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(dashboardData?.total_balance || 0, 'JOD')}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link
                to="/transfers"
                className="flex flex-col items-center p-4 bg-amber-50 rounded-lg hover:bg-amber-100 transition-colors"
              >
                <span className="text-2xl mb-2">💸</span>
                <span className="text-sm font-medium text-gray-900">Send Money</span>
              </Link>
              <Link
                to="/wallet"
                className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
              >
                <span className="text-2xl mb-2">💳</span>
                <span className="text-sm font-medium text-gray-900">Wallet</span>
              </Link>
              <Link
                to="/offers"
                className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
              >
                <span className="text-2xl mb-2">🎁</span>
                <span className="text-sm font-medium text-gray-900">Offers</span>
              </Link>
              <Link
                to="/micro-loans"
                className="flex flex-col items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
              >
                <span className="text-2xl mb-2">💰</span>
                <span className="text-sm font-medium text-gray-900">Loans</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Recent Transactions</h2>
              <Link
                to="/transactions"
                className="text-amber-600 hover:text-amber-700 text-sm font-medium"
              >
                View All
              </Link>
            </div>
          </div>
          <div className="p-6">
            {dashboardData?.recent_transactions?.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.recent_transactions.slice(0, 5).map((transaction, index) => (
                  <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                    <div className="flex items-center">
                      <div className="p-2 bg-gray-100 rounded-full">
                        <span className="text-sm">
                          {transaction.type === 'debit' ? '↗️' : '↙️'}
                        </span>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {transaction.description || 'Bank Transaction'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(transaction.date)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${
                        transaction.type === 'debit' ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {transaction.type === 'debit' ? '-' : '+'}
                        {formatCurrency(transaction.amount, 'JOD')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <span className="text-4xl mb-4 block">📈</span>
                <p className="text-gray-500">No recent transactions</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;