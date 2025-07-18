import React, { useState } from 'react';
import api from '../services/api';

const IBANValidation = () => {
  const [ibanData, setIbanData] = useState({
    accountType: '',
    accountId: '',
    ibanType: 'IBAN',
    ibanValue: '',
    uidType: 'CUSTOMER_ID',
    uidValue: 'IND_CUST_015'
  });
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [error, setError] = useState(null);

  const validateIBAN = async (e) => {
    e.preventDefault();
    
    if (!ibanData.accountType || !ibanData.accountId || !ibanData.ibanValue || !ibanData.uidValue) {
      setError('Please fill in all required fields');
      return;
    }

    setValidating(true);
    setError(null);
    setValidationResult(null);

    try {
      const response = await api.post('/auth/validate-iban', ibanData);
      setValidationResult(response.data);
    } catch (err) {
      setError('Failed to validate IBAN');
      console.error('IBAN validation error:', err);
    } finally {
      setValidating(false);
    }
  };

  const handleInputChange = (field, value) => {
    setIbanData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear previous results when data changes
    setValidationResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">IBAN Validation</h1>
          <p className="text-gray-600 mb-6">
            Validate IBAN using the JoPACC IBAN Confirmation API. This is a standalone validation tool.
          </p>

          <form onSubmit={validateIBAN} className="space-y-6">
            {/* Customer ID Section */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-medium text-blue-900 mb-4">Customer Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    UID Type
                  </label>
                  <select
                    value={ibanData.uidType}
                    onChange={(e) => handleInputChange('uidType', e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="CUSTOMER_ID">Customer ID</option>
                    <option value="NATIONAL_ID">National ID</option>
                    <option value="PASSPORT">Passport</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    UID Value
                  </label>
                  <input
                    type="text"
                    value={ibanData.uidValue}
                    onChange={(e) => handleInputChange('uidValue', e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter UID value (e.g., IND_CUST_015)"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Account Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Type
                </label>
                <select
                  value={ibanData.accountType}
                  onChange={(e) => handleInputChange('accountType', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select account type...</option>
                  <option value="SAVINGS">Savings Account</option>
                  <option value="CURRENT">Current Account</option>
                  <option value="SALARY">Salary Account</option>
                  <option value="BUSINESS">Business Account</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account ID
                </label>
                <input
                  type="text"
                  value={ibanData.accountId}
                  onChange={(e) => handleInputChange('accountId', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter account ID"
                  required
                />
              </div>
            </div>

            {/* IBAN Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  IBAN Type
                </label>
                <select
                  value={ibanData.ibanType}
                  onChange={(e) => handleInputChange('ibanType', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="IBAN">IBAN</option>
                  <option value="ACCOUNT_NUMBER">Account Number</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  IBAN Value
                </label>
                <input
                  type="text"
                  value={ibanData.ibanValue}
                  onChange={(e) => handleInputChange('ibanValue', e.target.value.toUpperCase())}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="JO27CBJO0000000000000000001023"
                  required
                />
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={validating}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors duration-200 font-medium"
              >
                {validating ? 'Validating IBAN...' : 'Validate IBAN'}
              </button>
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-red-600 text-sm">⚠️ {error}</span>
              </div>
            </div>
          )}

          {/* Validation Result */}
          {validationResult && (
            <div className={`mt-6 rounded-lg p-6 ${
              validationResult.valid 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center mb-4">
                <span className={`text-xl font-bold ${
                  validationResult.valid ? 'text-green-800' : 'text-red-800'
                }`}>
                  {validationResult.valid ? '✅ IBAN Valid' : '❌ IBAN Invalid'}
                </span>
              </div>
              
              <div className="space-y-3">
                <div className={`text-sm ${validationResult.valid ? 'text-green-700' : 'text-red-700'}`}>
                  <strong>IBAN:</strong> {validationResult.iban_value}
                </div>
                
                {validationResult.api_info && (
                  <div className="text-sm text-gray-600">
                    <strong>Validated by:</strong> {validationResult.api_info.endpoint}
                  </div>
                )}
                
                {validationResult.error && (
                  <div className="text-sm text-red-700">
                    <strong>Error:</strong> {validationResult.error}
                  </div>
                )}
              </div>
              
              {/* Validation Details */}
              {validationResult.validation_result && (
                <div className="mt-4 p-4 bg-gray-50 rounded border">
                  <div className="text-sm text-gray-600 mb-2">
                    <strong>Full API Response:</strong>
                  </div>
                  <pre className="text-xs text-gray-700 overflow-x-auto">
                    {JSON.stringify(validationResult.validation_result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* API Information */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-blue-600 font-semibold">🔒 JoPACC IBAN Confirmation API</span>
            </div>
            <div className="text-sm text-blue-800">
              <div className="flex items-center space-x-1">
                <span>Endpoint:</span>
                <span className="font-medium">JoPACC IBAN Confirmation</span>
                <span>•</span>
                <span>Secure validation service</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IBANValidation;