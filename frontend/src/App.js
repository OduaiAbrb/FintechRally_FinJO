import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import Dashboard from './components/Dashboard';
import WalletPage from './components/WalletPage';
import TransactionsPage from './components/TransactionsPage';
import OpenBankingPage from './components/OpenBankingPage';
import HeyDinarPage from './components/HeyDinarPage';
import UserProfilePage from './components/UserProfilePage';
import TransferPage from './components/TransferPage';
import SecurityDashboard from './components/SecurityDashboard';
import OffersPage from './components/OffersPage';
import MicroLoansPage from './components/MicroLoansPage';
import IBANValidation from './components/IBANValidation';
import Navbar from './components/Navbar';
import LoadingSpinner from './components/LoadingSpinner';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return user ? children : <Navigate to="/login" />;
};

// Public Route component (redirect to dashboard if already logged in)
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return user ? <Navigate to="/dashboard" /> : children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App min-h-screen bg-gray-50">
          <Routes>
            <Route path="/login" element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            } />
            <Route path="/register" element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <Dashboard />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/wallet" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <WalletPage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/transactions" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <TransactionsPage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/open-banking" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <OpenBankingPage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/hey-dinar" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <HeyDinarPage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <UserProfilePage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/transfers" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <TransferPage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/security" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <SecurityDashboard />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/offers" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <OffersPage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/micro-loans" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <MicroLoansPage />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/iban-validation" element={
              <ProtectedRoute>
                <div className="flex flex-col h-screen">
                  <Navbar />
                  <main className="flex-1 overflow-auto">
                    <IBANValidation />
                  </main>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;