export const formatCurrency = (amount, currency = 'JOD') => {
  if (typeof amount !== 'number') {
    amount = parseFloat(amount) || 0;
  }
  
  if (currency === 'JOD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'JOD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } else if (currency === 'DINARX') {
    return `${amount.toFixed(2)} DinarX`;
  } else {
    return `${amount.toFixed(2)} ${currency}`;
  }
};

export const formatDate = (date) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (date) => {
  if (!date) return '';
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatTransactionType = (type) => {
  if (!type) return 'Unknown';
  return type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
};

export const getTransactionIcon = (type) => {
  switch (type?.toLowerCase()) {
    case 'deposit':
      return '💰';
    case 'withdrawal':
      return '🏧';
    case 'transfer':
      return '💸';
    case 'payment':
      return '💳';
    case 'exchange':
      return '🔄';
    default:
      return '📊';
  }
};

export const getTransactionColor = (type) => {
  switch (type?.toLowerCase()) {
    case 'deposit':
      return 'text-green-600';
    case 'withdrawal':
      return 'text-red-600';
    case 'transfer':
      return 'text-blue-600';
    case 'payment':
      return 'text-purple-600';
    case 'exchange':
      return 'text-amber-600';
    default:
      return 'text-gray-600';
  }
};

export const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'cancelled':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};