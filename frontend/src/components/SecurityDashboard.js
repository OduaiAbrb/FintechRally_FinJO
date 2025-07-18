import React, { useState, useEffect } from 'react';
import { securityApi } from '../services/securityApi';
import LoadingSpinner from './LoadingSpinner';

const SecurityDashboard = () => {
  const [securityStatus, setSecurityStatus] = useState(null);
  const [amlDashboard, setAmlDashboard] = useState(null);
  const [riskDashboard, setRiskDashboard] = useState(null);
  const [userBiometrics, setUserBiometrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    try {
      setLoading(true);
      
      // Load security data (biometric disabled)
      const [statusResponse, amlResponse, riskResponse] = await Promise.all([
        securityApi.getSecurityStatus(),
        securityApi.getAMLDashboard(),
        securityApi.getRiskDashboard()
      ]);

      setSecurityStatus(statusResponse.data);
      setAmlDashboard(amlResponse.data);
      setRiskDashboard(riskResponse.data);
      setUserBiometrics({ biometrics: [] }); // Disabled
      
    } catch (err) {
      setError('Failed to load security data');
      console.error('Security dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const initializeSecurity = async () => {
    try {
      setLoading(true);
      await securityApi.initializeSecurity();
      await loadSecurityData();
    } catch (err) {
      setError('Failed to initialize security systems');
      console.error('Security initialization error:', err);
    } finally {
      setLoading(false);
    }
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
          <button
            onClick={loadSecurityData}
            className="mt-2 btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Monitor and manage advanced security features including AML, biometric authentication, and risk scoring
        </p>
      </div>

      {/* Security Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🛡️</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">AML System</h3>
              <p className="text-sm text-gray-600">
                Status: {securityStatus?.aml_system?.status || 'Unknown'}
              </p>
              <p className="text-xs text-gray-500">
                Alerts (7d): {securityStatus?.aml_system?.total_alerts || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🚫</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Biometric Auth</h3>
              <p className="text-sm text-gray-600">
                Status: {securityStatus?.biometric_system?.status || 'Unknown'}
              </p>
              <p className="text-xs text-gray-500">
                {securityStatus?.biometric_system?.message || 'Disabled'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">📊</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Risk Scoring</h3>
              <p className="text-sm text-gray-600">
                Status: {securityStatus?.risk_system?.status || 'Unknown'}
              </p>
              <p className="text-xs text-gray-500">
                Assessments: {securityStatus?.risk_system?.total_assessments || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Initialize Security Button */}
      <div className="mb-8">
        <button
          onClick={initializeSecurity}
          className="btn-primary"
        >
          Initialize Security Systems
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📋' },
            { id: 'aml', name: 'AML Monitoring', icon: '🛡️' },
            { id: 'risk', name: 'Risk Scoring', icon: '📊' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Security Overview</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-900">Jordan Central Bank Compliance</h4>
                <p className="text-sm text-gray-600">✅ AML monitoring active</p>
                <p className="text-sm text-gray-600">✅ Risk scoring enabled</p>
                <p className="text-sm text-gray-600">✅ Transaction monitoring</p>
                <p className="text-sm text-gray-600">🚫 Biometric authentication disabled</p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Advanced Features</h4>
                <p className="text-sm text-gray-600">✅ ML-based fraud detection</p>
                <p className="text-sm text-gray-600">✅ Continuous learning models</p>
                <p className="text-sm text-gray-600">✅ User-to-user transfers</p>
                <p className="text-sm text-gray-600">🚫 Biometric features disabled</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'aml' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">AML Monitoring</h3>
            
            {amlDashboard?.alert_counts && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {Object.entries(amlDashboard.alert_counts).map(([level, count]) => (
                  <div key={level} className="text-center">
                    <div className={`text-2xl font-bold ${
                      level === 'critical' ? 'text-red-600' :
                      level === 'high' ? 'text-orange-600' :
                      level === 'medium' ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {count}
                    </div>
                    <div className="text-sm text-gray-600 capitalize">{level} Risk</div>
                  </div>
                ))}
              </div>
            )}

            {amlDashboard?.recent_alerts && amlDashboard.recent_alerts.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Recent Alerts</h4>
                <div className="space-y-2">
                  {amlDashboard.recent_alerts.slice(0, 5).map((alert, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <span className="font-medium">{alert.alert_id}</span>
                        <span className="ml-2 text-sm text-gray-600">
                          Risk: {alert.risk_level}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500">
                        Score: {alert.score?.toFixed(3)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'risk' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Risk Scoring</h3>
            
            {riskDashboard?.risk_statistics && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                {Object.entries(riskDashboard.risk_statistics).map(([level, stats]) => (
                  <div key={level} className="text-center">
                    <div className={`text-2xl font-bold ${
                      level === 'very_high' ? 'text-red-600' :
                      level === 'high' ? 'text-orange-600' :
                      level === 'medium' ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {stats.count}
                    </div>
                    <div className="text-sm text-gray-600 capitalize">
                      {level.replace('_', ' ')}
                    </div>
                    <div className="text-xs text-gray-500">
                      Avg: {stats.avg_score?.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {riskDashboard?.recent_assessments && riskDashboard.recent_assessments.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Recent Risk Assessments</h4>
                <div className="space-y-2">
                  {riskDashboard.recent_assessments.slice(0, 5).map((assessment, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <span className="font-medium">{assessment.user_id}</span>
                        <span className="ml-2 text-sm text-gray-600">
                          Risk: {assessment.risk_level}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500">
                        Score: {assessment.risk_score?.toFixed(3)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SecurityDashboard;