import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isServicesOpen, setIsServicesOpen] = useState(false);
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Core navigation items - always visible
  const coreNavItems = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Wallet', path: '/wallet', icon: '💳' },
    { name: 'Transfers', path: '/transfers', icon: '💸' },
  ];

  // Banking services dropdown
  const bankingServices = [
    { name: 'Open Banking', path: '/open-banking', icon: '🏦' },
    { name: 'Offers', path: '/offers', icon: '🎁' },
    { name: 'Micro Loans', path: '/micro-loans', icon: '💰' },
  ];

  // Tools & utilities dropdown
  const toolsItems = [
    { name: 'IBAN Validation', path: '/iban-validation', icon: '✅' },
    { name: 'Hey Dinar', path: '/hey-dinar', icon: '🤖' },
    { name: 'Transactions', path: '/transactions', icon: '📈' },
    { name: 'Security', path: '/security', icon: '🔒' },
  ];

  const isActive = (path) => location.pathname === path;

  const isDropdownActive = (items) => {
    return items.some(item => isActive(item.path));
  };

  return (
    <nav className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-gradient-to-r from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">F</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Finjo</span>
            </Link>
          </div>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-6">
            {/* Core navigation items */}
            {coreNavItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive(item.path)
                    ? 'bg-amber-100 text-amber-700'
                    : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            ))}

            {/* Banking Services Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsServicesOpen(!isServicesOpen)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isDropdownActive(bankingServices)
                    ? 'bg-amber-100 text-amber-700'
                    : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
                }`}
              >
                <span>🏦</span>
                <span>Banking</span>
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isServicesOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                  <div className="py-1">
                    {bankingServices.map((item) => (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setIsServicesOpen(false)}
                        className={`flex items-center space-x-2 px-4 py-2 text-sm transition-colors ${
                          isActive(item.path)
                            ? 'bg-amber-100 text-amber-700'
                            : 'text-gray-700 hover:bg-amber-50 hover:text-amber-600'
                        }`}
                      >
                        <span>{item.icon}</span>
                        <span>{item.name}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Tools Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsToolsOpen(!isToolsOpen)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isDropdownActive(toolsItems)
                    ? 'bg-amber-100 text-amber-700'
                    : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
                }`}
              >
                <span>🔧</span>
                <span>Tools</span>
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isToolsOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                  <div className="py-1">
                    {toolsItems.map((item) => (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setIsToolsOpen(false)}
                        className={`flex items-center space-x-2 px-4 py-2 text-sm transition-colors ${
                          isActive(item.path)
                            ? 'bg-amber-100 text-amber-700'
                            : 'text-gray-700 hover:bg-amber-50 hover:text-amber-600'
                        }`}
                      >
                        <span>{item.icon}</span>
                        <span>{item.name}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-3">
              <Link
                to="/profile"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/profile')
                    ? 'bg-amber-100 text-amber-700'
                    : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
                }`}
              >
                <span>👤</span>
                <span>Profile</span>
              </Link>
              <div className="h-8 w-8 bg-gradient-to-r from-amber-500 to-orange-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold text-sm">
                  {user?.full_name?.charAt(0)?.toUpperCase()}
                </span>
              </div>
            </div>
            
            <button
              onClick={handleLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Logout
            </button>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-amber-500"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t border-gray-200">
            {/* Core items */}
            {coreNavItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                  isActive(item.path)
                    ? 'bg-amber-100 text-amber-700'
                    : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            ))}

            {/* Banking Services */}
            <div className="py-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 pb-2">
                Banking Services
              </div>
              {bankingServices.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                    isActive(item.path)
                      ? 'bg-amber-100 text-amber-700'
                      : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              ))}
            </div>

            {/* Tools */}
            <div className="py-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 pb-2">
                Tools
              </div>
              {toolsItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                    isActive(item.path)
                      ? 'bg-amber-100 text-amber-700'
                      : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              ))}
            </div>

            {/* Profile */}
            <Link
              to="/profile"
              onClick={() => setIsMenuOpen(false)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                isActive('/profile')
                  ? 'bg-amber-100 text-amber-700'
                  : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
              }`}
            >
              <span>👤</span>
              <span>Profile</span>
            </Link>
            
            {/* Mobile user info */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center space-x-3 px-3 py-2">
                <div className="h-10 w-10 bg-gradient-to-r from-amber-500 to-orange-600 rounded-full flex items-center justify-center">
                  <span className="text-white font-semibold">
                    {user?.full_name?.charAt(0)?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-gray-900 font-medium">{user?.full_name}</p>
                  <p className="text-gray-500 text-sm">{user?.email}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;