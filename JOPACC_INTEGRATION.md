# Jordan Open Finance (JoPACC) Integration Guide

## Overview

This application is now integrated with the Jordan Open Finance Standards developed by JoPACC (Jordan Payments and Clearing Company). The integration follows the official JoPACC API specifications and supports all major services.

## Supported Services

### 1. Account Information Services (AIS)
- **Account Access Consent**: Creates consent for accessing user accounts
- **Account Information**: Retrieves account details and balances
- **Transaction History**: Fetches transaction data with proper filtering

### 2. Payment Initiation Services (PIS)
- **Payment Consent**: Creates consent for payment initiation
- **Domestic Payments**: Initiates JOD payments within Jordan
- **Payment Status**: Tracks payment execution status

### 3. Extended Services
- **Foreign Exchange**: Real-time exchange rates
- **Additional Financial Services**: Enhanced banking features

## Current Configuration

### Sandbox Mode (Default)
```env
JORDAN_OPEN_FINANCE_SANDBOX=true
JORDAN_OPEN_FINANCE_SANDBOX_URL=https://jpcjofsdev.devportal-az-eu.webmethods.io
```

### Production Configuration
To integrate with production JoPACC APIs, update your `.env` file:

```env
# Switch to production mode
JORDAN_OPEN_FINANCE_SANDBOX=false

# Production API endpoints
JORDAN_OPEN_FINANCE_BASE_URL=https://api.jopacc.com

# Your JoPACC credentials (obtain from JoPACC)
JORDAN_OPEN_FINANCE_CLIENT_ID=your_actual_client_id
JORDAN_OPEN_FINANCE_CLIENT_SECRET=your_actual_client_secret
JORDAN_OPEN_FINANCE_API_KEY=your_actual_api_key
JORDAN_OPEN_FINANCE_FINANCIAL_ID=your_financial_institution_id
```

## Getting JoPACC Credentials

1. **Visit the JoPACC Developer Portal**: https://jpcjofsdev.devportal-az-eu.webmethods.io/portal/apis
2. **Register your application** with JoPACC
3. **Obtain the following credentials**:
   - Client ID
   - Client Secret
   - API Key
   - Financial Institution ID (x-fapi-financial-id)

## API Standards Compliance

The integration follows JoPACC v1.0 standards:

### Authentication
- OAuth2 Client Credentials flow
- Bearer token authentication
- Required headers:
  - `x-fapi-financial-id`
  - `x-fapi-customer-ip-address`
  - `x-fapi-interaction-id`
  - `x-jws-signature` (for production)
  - `x-idempotency-key`

### API Endpoints Structure
```
/open-banking/v1.0/aisp/    # Account Information Services
/open-banking/v1.0/pisp/    # Payment Initiation Services
/open-banking/v1.0/fx/      # Foreign Exchange Services
```

### Data Formats
- All timestamps in ISO 8601 format with 'Z' suffix
- Amounts as strings with decimal precision
- Standard JoPACC response structures with `Data` and `Links` sections

## Testing with Real APIs

1. **Update environment variables** with your real JoPACC credentials
2. **Set sandbox mode to false**:
   ```env
   JORDAN_OPEN_FINANCE_SANDBOX=false
   ```
3. **Restart the backend service**:
   ```bash
   sudo supervisorctl restart backend
   ```
4. **Test the integration** through the application UI

## Error Handling

The integration includes comprehensive error handling for:
- Authentication failures
- API rate limiting
- Network connectivity issues
- Invalid consent scenarios
- Malformed requests

## Security Features

- **JWT signature validation** (x-jws-signature header)
- **Request idempotency** (x-idempotency-key header)
- **IP address tracking** (x-fapi-customer-ip-address header)
- **Secure token storage** in MongoDB
- **Consent expiration management**

## Monitoring and Logging

All API interactions are logged with:
- Request/response details
- Error conditions
- Performance metrics
- Consent status changes

## Support

For JoPACC-specific issues:
- JoPACC Developer Portal: https://jpcjofsdev.devportal-az-eu.webmethods.io
- JoPACC Documentation: Available through the developer portal

For application integration issues:
- Check the backend logs: `tail -f /var/log/supervisor/backend.out.log`
- Verify environment variables are correctly set
- Ensure network connectivity to JoPACC endpoints

## Example API Responses

### Account Information (JoPACC Format)
```json
{
  "Data": {
    "Account": [
      {
        "AccountId": "acc_001_jordan_bank",
        "Status": "Enabled",
        "Currency": "JOD",
        "AccountType": "Personal",
        "AccountSubType": "CurrentAccount",
        "Nickname": "Jordan Bank Current"
      }
    ]
  },
  "Links": {
    "Self": "/open-banking/v1.0/aisp/accounts"
  }
}
```

### Balance Information
```json
{
  "Data": {
    "Balance": [
      {
        "AccountId": "acc_001_jordan_bank",
        "Amount": {
          "Amount": "2500.75",
          "Currency": "JOD"
        },
        "CreditDebitIndicator": "Credit",
        "Type": "ClosingAvailable",
        "DateTime": "2025-07-17T11:58:30Z"
      }
    ]
  }
}
```

This integration ensures full compliance with Jordan's Open Banking standards while maintaining backward compatibility with the existing application interface.