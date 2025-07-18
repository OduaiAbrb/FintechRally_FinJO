import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import LoadingSpinner from './LoadingSpinner';

const MicroLoansPage = () => {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [eligibilityData, setEligibilityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkingEligibility, setCheckingEligibility] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loanAmount, setLoanAmount] = useState('');
  const [loanTerm, setLoanTerm] = useState('12');
  const [selectedBank, setSelectedBank] = useState('');
  const [showApplication, setShowApplication] = useState(false);
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
    } catch (err) {
      setError('Failed to fetch accounts');
      console.error('Error fetching accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  const checkEligibility = async (accountId) => {
    if (!accountId) return;
    
    setCheckingEligibility(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await api.get(`/loans/eligibility/${accountId}`, {
        headers: {
          'x-customer-id': customerId
        }
      });
      setEligibilityData(response.data);
      setShowApplication(response.data.eligible_for_loan);
    } catch (err) {
      setError('Failed to check loan eligibility');
      console.error('Error checking eligibility:', err);
    } finally {
      setCheckingEligibility(false);
    }
  };

  const handleAccountChange = (accountId) => {
    setSelectedAccount(accountId);
    setEligibilityData(null);
    setShowApplication(false);
    setLoanAmount('');
    setSelectedBank('');
    if (accountId) {
      checkEligibility(accountId);
    }
  };

  const handleCustomerIdChange = (e) => {
    e.preventDefault();
    setShowCustomerForm(false);
    setSelectedAccount('');
    setEligibilityData(null);
    setShowApplication(false);
    fetchAccounts();
  };

  const applyForLoan = async (e) => {
    e.preventDefault();
    
    if (!selectedAccount || !loanAmount || !selectedBank) {
      setError('Please fill in all required fields');
      return;
    }
    
    const amount = parseFloat(loanAmount);
    if (amount <= 0 || amount > eligibilityData.max_loan_amount) {
      setError(`Loan amount must be between 1 and ${eligibilityData.max_loan_amount} JOD`);
      return;
    }
    
    setApplying(true);
    setError(null);
    
    try {
      const response = await api.post('/loans/apply', {
        account_id: selectedAccount,
        loan_amount: amount,
        selected_bank: selectedBank,
        loan_term: parseInt(loanTerm),
        customer_id: customerId
      });
      
      setSuccess(`Loan application submitted successfully! Application ID: ${response.data.application_id}`);
      setShowApplication(false);
      setLoanAmount('');
      setSelectedBank('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to apply for loan');
      console.error('Error applying for loan:', err);
    } finally {
      setApplying(false);
    }
  };

  const getEligibilityColor = (eligibility) => {
    switch (eligibility?.toLowerCase()) {
      case 'excellent':
        return 'bg-green-100 text-green-800';
      case 'good':
        return 'bg-blue-100 text-blue-800';
      case 'fair':
        return 'bg-yellow-100 text-yellow-800';
      case 'poor':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCreditScoreColor = (score) => {
    if (score >= 750) return 'text-green-600';
    if (score >= 650) return 'text-blue-600';
    if (score >= 550) return 'text-yellow-600';
    return 'text-red-600';
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
          <h1 className="text-3xl font-bold text-gray-900">Micro Loans</h1>
          <p className="mt-2 text-gray-600">
            Quick access to small loans with AI-powered approval based on your account data
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
          </div>
        </div>

        {/* Account Selection */}
        {accounts.length > 0 && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Account for Loan Assessment</h2>
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

        {/* Success Message */}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-green-600 font-medium">✅ {success}</span>
            </div>
          </div>
        )}

        {/* Eligibility Checking */}
        {checkingEligibility && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-center">
              <LoadingSpinner />
              <span className="ml-3 text-gray-600">Checking loan eligibility...</span>
            </div>
          </div>
        )}

        {/* Eligibility Results */}
        {eligibilityData && !checkingEligibility && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Loan Eligibility Assessment</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Credit Score */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Credit Score</div>
                <div className={`text-2xl font-bold ${getCreditScoreColor(eligibilityData.credit_score)}`}>
                  {eligibilityData.credit_score}
                </div>
                <div className="text-xs text-gray-500">out of 850</div>
              </div>

              {/* Eligibility Status */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Eligibility</div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEligibilityColor(eligibilityData.eligibility)}`}>
                  {eligibilityData.eligibility}
                </span>
              </div>

              {/* Max Loan Amount */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Max Loan Amount</div>
                <div className="text-xl font-bold text-gray-900">
                  {eligibilityData.max_loan_amount} JOD
                </div>
              </div>

              {/* Account Balance */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Account Balance</div>
                <div className="text-xl font-bold text-gray-900">
                  {eligibilityData.account_info.balance} JOD
                </div>
              </div>
            </div>

            {/* Available Banks */}
            {eligibilityData.available_banks && eligibilityData.available_banks.length > 0 && (
              <div className="mb-6">
                <h3 className="text-md font-medium text-gray-900 mb-3">Available Banks</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {eligibilityData.available_banks.map((bank, index) => (
                    <div key={index} className="bg-blue-50 rounded-lg p-3 flex items-center">
                      <div className="text-blue-600 mr-3">🏦</div>
                      <div>
                        <div className="font-medium text-gray-900">{bank.name}</div>
                        <div className="text-sm text-gray-600">{bank.code}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Loan Application Form */}
        {showApplication && eligibilityData && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Apply for Micro Loan</h2>
            
            <form onSubmit={applyForLoan} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Loan Amount */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Loan Amount (JOD)
                  </label>
                  <input
                    type="number"
                    value={loanAmount}
                    onChange={(e) => setLoanAmount(e.target.value)}
                    max={eligibilityData.max_loan_amount}
                    min="1"
                    step="0.01"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder={`Max: ${eligibilityData.max_loan_amount} JOD`}
                    required
                  />
                </div>

                {/* Loan Term */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Loan Term (months)
                  </label>
                  <select
                    value={loanTerm}
                    onChange={(e) => setLoanTerm(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="6">6 months</option>
                    <option value="12">12 months</option>
                    <option value="18">18 months</option>
                    <option value="24">24 months</option>
                    <option value="36">36 months</option>
                  </select>
                </div>
              </div>

              {/* Bank Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Bank
                </label>
                <select
                  value={selectedBank}
                  onChange={(e) => setSelectedBank(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Choose a bank...</option>
                  {eligibilityData.available_banks.map((bank, index) => (
                    <option key={index} value={bank.name}>
                      {bank.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Monthly Payment Estimate */}
              {loanAmount && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-blue-800">Estimated Monthly Payment:</span>
                    <span className="text-lg font-bold text-blue-900">
                      {(parseFloat(loanAmount) * 1.085 / parseInt(loanTerm)).toFixed(2)} JOD
                    </span>
                  </div>
                  <div className="text-xs text-blue-600 mt-1">
                    Based on 8.5% annual interest rate
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <div className="flex space-x-3">
                <button
                  type="submit"
                  disabled={applying}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors duration-200 font-medium"
                >
                  {applying ? 'Applying...' : 'Apply for Loan'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowApplication(false)}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors duration-200 font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Not Eligible Message */}
        {eligibilityData && !eligibilityData.eligible_for_loan && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="text-yellow-600 mr-3">⚠️</div>
              <div>
                <h3 className="text-lg font-medium text-yellow-900">Not Eligible for Loan</h3>
                <p className="text-yellow-800">
                  Based on your current credit score and account balance, you are not eligible for a micro loan at this time.
                  Consider improving your account balance or credit history.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* No Accounts Message */}
        {accounts.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">🏦</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No linked accounts</h3>
            <p className="text-gray-600 mb-4">
              Connect your bank accounts to check loan eligibility.
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

export default MicroLoansPage;