import React from 'react';

const LoadingSpinner = ({ size = 'md', color = 'primary' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  const colorClasses = {
    primary: 'border-blue-600',
    secondary: 'border-green-600',
    white: 'border-white',
    gray: 'border-gray-600',
  };

  return (
    <div className="flex items-center justify-center">
      <div
        className={`animate-spin rounded-full border-4 border-gray-200 ${sizeClasses[size]} ${colorClasses[color]}`}
        style={{ borderTopColor: 'transparent' }}
      />
    </div>
  );
};

export default LoadingSpinner;