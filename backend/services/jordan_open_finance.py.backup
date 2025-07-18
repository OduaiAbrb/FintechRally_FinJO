import httpx
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

class JordanOpenFinanceService:
    """
    Service for integrating with Jordan Open Finance APIs (JoPACC)
    Supports AIS, PIS, FPS, and Extended Services
    Based on Jordan Open Finance Standards 2025
    """
    
    def __init__(self):
        # Production JoPACC API Configuration - Using standardized JOPACC_ environment variables
        self.base_url = os.getenv("JOPACC_BASE_URL", "https://api.jopacc.com")
        self.sandbox_url = os.getenv("JOPACC_SANDBOX_URL", "https://jpcjofsdev.apigw-az-eu.webmethods.io")
        self.client_id = os.getenv("JOPACC_CLIENT_ID")
        self.client_secret = os.getenv("JOPACC_CLIENT_SECRET")
        self.api_key = os.getenv("JOPACC_API_KEY")
        self.x_financial_id = os.getenv("JOPACC_FINANCIAL_ID", "001")
        self.timeout = 30
        
        # Always use real API endpoints - no sandbox mode
        self.api_base = "https://jpcjofsdev.apigw-az-eu.webmethods.io"
        self.sandbox_mode = False  # Permanently disabled - only real API calls
        
    # Removed OAuth2 method - JoPACC uses direct token authentication
    # Direct token authentication is handled in get_headers() method
    
    async def get_headers(self, customer_ip: str = "127.0.0.1") -> Dict[str, str]:
        """Get standard headers for real JoPACC API requests - Direct token authentication"""
        interaction_id = str(uuid.uuid4())
        
        return {
            "Authorization": os.getenv("JOPACC_AUTHORIZATION", "Bearer demo_token"),
            "x-financial-id": os.getenv("JOPACC_FINANCIAL_ID", "001"),
            "x-customer-ip-address": customer_ip,
            "x-customer-user-agent": "StableCoin-Fintech-App/1.0",
            "x-interactions-id": interaction_id,
            "x-idempotency-key": str(uuid.uuid4()),
            "x-jws-signature": os.getenv("JOPACC_JWS_SIGNATURE", ""),
            "x-auth-date": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "x-customer-id": os.getenv("JOPACC_CUSTOMER_ID", "customer_123"),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    # Real API Endpoints based on the portal documentation
    
    async def get_accounts_new(self, skip: int = 0, account_type: str = None, limit: int = 10, 
                          account_status: str = None, sort: str = "desc") -> Dict[str, Any]:
        """Get user accounts using real JoPACC endpoint - only real API calls"""
        
        # Real JoPACC API call with exact headers and URL you provided
        headers = {
            "x-jws-signature": os.getenv("JOPACC_JWS_SIGNATURE", ""),
            "x-auth-date": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "x-idempotency-key": str(uuid.uuid4()),
            "Authorization": os.getenv("JOPACC_AUTHORIZATION", "Bearer demo_token"),
            "x-customer-user-agent": "StableCoin-Fintech-App/1.0",
            "x-financial-id": os.getenv("JOPACC_FINANCIAL_ID", "001"),
            "x-customer-ip-address": "127.0.0.1",
            "x-interactions-id": str(uuid.uuid4()),
            "x-customer-id": os.getenv("JOPACC_CUSTOMER_ID", "customer_123")
        }
        
        querystring = {
            "skip": skip,
            "limit": limit,
            "sort": sort
        }
        
        if account_type:
            querystring["accountType"] = account_type
        if account_status:
            querystring["accountStatus"] = account_status
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                "https://jpcjofsdev.apigw-az-eu.webmethods.io/gateway/Accounts/v0.4.3/accounts",
                headers=headers,
                params=querystring
            )
            
            if response.status_code == 200:
                # Return the actual API data
                api_data = response.json()
                print(f"JoPACC API Success: {api_data}")
                return api_data
            else:
                # Return error response instead of mock data
                error_msg = f"JoPACC API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
    
    async def get_account_balances(self, account_id: str, customer_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """Get account balances using real JoPACC endpoint - only real API calls"""
        
        # Real JoPACC API call with exact headers and URL you provided
        # NOTE: x-customer-id is NOT included for balance API as per user specification
        headers = {
            "x-customer-ip-address": customer_ip,
            "x-customer-user-agent": "StableCoin-Fintech-App/1.0",
            "Authorization": os.getenv("JOPACC_AUTHORIZATION", "Bearer demo_token"),
            "x-financial-id": os.getenv("JOPACC_FINANCIAL_ID", "001"),
            "x-auth-date": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "x-idempotency-key": str(uuid.uuid4()),
            "x-jws-signature": os.getenv("JOPACC_JWS_SIGNATURE", ""),
            "x-interactions-id": str(uuid.uuid4())
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"https://jpcjofsdev.apigw-az-eu.webmethods.io/gateway/Balances/v0.4.3/accounts/{account_id}/balances",
                headers=headers
            )
            
            if response.status_code == 200:
                # Return the actual API data
                return response.json()
            else:
                # Return error response instead of mock data
                error_msg = f"JoPACC Balance API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
        
    async def get_accounts_with_balances(self, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """Get accounts and their balances in a single dependent call flow"""
        
        # First, get all accounts (this API includes x-customer-id)
        accounts_response = await self.get_accounts_new(skip=skip, limit=limit)
        
        # Extract account IDs from the response
        enriched_accounts = []
        for account in accounts_response.get("accounts", []):
            account_id = account.get("accountId")
            if account_id:
                # Get balance for this specific account (this API does NOT include x-customer-id)
                try:
                    balance_response = await self.get_account_balances(account_id)
                    # Enrich account data with detailed balance information
                    account_with_balance = {
                        **account,
                        "detailed_balances": balance_response.get("balances", []),
                        "balance_last_updated": balance_response.get("lastUpdated", account.get("lastUpdated"))
                    }
                    enriched_accounts.append(account_with_balance)
                except Exception as e:
                    # If balance API fails, keep original account data
                    print(f"Balance API failed for account {account_id}: {e}")
                    enriched_accounts.append(account)
            else:
                enriched_accounts.append(account)
        
        return {
            "accounts": enriched_accounts,
            "totalCount": len(enriched_accounts),
            "hasMore": accounts_response.get("hasMore", False)
        }
        
    async def get_fx_rates_for_account(self, account_id: str) -> Dict[str, Any]:
        """Get FX rates for a specific account - FX API depends on account_id"""
        
        # First verify account exists by getting account details
        try:
            accounts_response = await self.get_accounts_new(limit=50)
            account_exists = False
            account_currency = "JOD"  # Default
            
            for account in accounts_response.get("accounts", []):
                if account.get("accountId") == account_id:
                    account_exists = True
                    account_currency = account.get("currency", "JOD")
                    break
            
            if not account_exists:
                raise ValueError(f"Account {account_id} not found")
            
            # Now get FX rates with account context
            fx_response = await self.get_fx_rates()
            
            # Enrich FX response with account information
            return {
                "account_id": account_id,
                "account_currency": account_currency,
                "fx_data": fx_response,
                "rates_for_account": fx_response.get("rates", []),
                "last_updated": fx_response.get("lastUpdated", datetime.utcnow().isoformat() + "Z")
            }
            
        except Exception as e:
            # If account verification fails, return basic FX data
            print(f"Account verification failed for FX rates: {e}")
            fx_response = await self.get_fx_rates()
            return {
                "account_id": account_id,
                "account_currency": "JOD",
                "fx_data": fx_response,
                "rates_for_account": fx_response.get("rates", []),
                "last_updated": fx_response.get("lastUpdated", datetime.utcnow().isoformat() + "Z"),
                "warning": "Account verification failed, using default FX rates"
            }
    
    async def get_fx_quote_for_account(self, account_id: str, target_currency: str, amount: float = None) -> Dict[str, Any]:
        """Get FX quote for a specific account - FX API depends on account_id"""
        
        # First verify account exists and get account details
        try:
            accounts_response = await self.get_accounts_new(limit=50)
            account_exists = False
            account_currency = "JOD"  # Default
            
            for account in accounts_response.get("accounts", []):
                if account.get("accountId") == account_id:
                    account_exists = True
                    account_currency = account.get("currency", "JOD")
                    break
            
            if not account_exists:
                raise ValueError(f"Account {account_id} not found")
            
            # Get FX quote
            quote_response = await self.get_fx_quote(target_currency, amount)
            
            # Enrich quote response with account information
            return {
                "account_id": account_id,
                "account_currency": account_currency,
                "quote_data": quote_response,
                "base_currency": quote_response.get("baseCurrency", account_currency),
                "target_currency": target_currency,
                "rate": quote_response.get("rate", 1.0),
                "amount": amount,
                "converted_amount": quote_response.get("convertedAmount"),
                "quote_id": quote_response.get("quoteId"),
                "valid_until": quote_response.get("validUntil"),
                "timestamp": quote_response.get("timestamp")
            }
            
        except Exception as e:
            # If account verification fails, return basic FX quote
            print(f"Account verification failed for FX quote: {e}")
            quote_response = await self.get_fx_quote(target_currency, amount)
            return {
                "account_id": account_id,
                "account_currency": "JOD",
                "quote_data": quote_response,
                **quote_response,
                "warning": "Account verification failed, using default FX quote"
            }
    
    
    
    # Account Information Services (AIS) - Following JoPACC v1.0 Standards
    async def create_account_access_consent(self, permissions: List[str], user_id: str) -> Dict[str, Any]:
        """Create account access consent following JoPACC AIS standards - only real API calls"""
        
        headers = await self.get_headers()
        consent_data = {
            "Data": {
                "Permissions": permissions,
                "ExpirationDateTime": (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z",
                "TransactionFromDateTime": datetime.utcnow().isoformat() + "Z",
                "TransactionToDateTime": (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"
            },
            "Risk": {}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/open-banking/v1.0/aisp/account-access-consents",
                headers=headers,
                json=consent_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"JoPACC Consent API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
    
    async def get_accounts(self, consent_id: str) -> List[Dict[str, Any]]:
        """Get user accounts following JoPACC AIS v1.0 standards - only real API calls"""
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/open-banking/v1.0/aisp/accounts",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"JoPACC Accounts API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
    
    async def get_account_transactions(self, account_id: str, from_booking_date: Optional[datetime] = None,
                                     to_booking_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get account transactions following JoPACC AIS v1.0 standards"""
        if self.sandbox_mode:
            # Generate mock transaction data in JoPACC format
            base_date = datetime.utcnow() - timedelta(days=30)
            transactions = []
            
            mock_transactions = [
                {"amount": "-250.00", "description": "ATM Cash Withdrawal", "merchant": "Jordan Bank ATM", "reference": "ATM001"},
                {"amount": "1500.00", "description": "Salary Payment", "merchant": "ABC Company Ltd", "reference": "SAL001"},
                {"amount": "-75.50", "description": "Grocery Purchase", "merchant": "Carrefour Jordan", "reference": "POS001"},
                {"amount": "-120.00", "description": "Fuel Purchase", "merchant": "Total Jordan", "reference": "POS002"},
                {"amount": "500.00", "description": "Money Transfer", "merchant": "Family Transfer", "reference": "TRF001"},
                {"amount": "-45.25", "description": "Restaurant Payment", "merchant": "Fakhr El-Din Restaurant", "reference": "POS003"},
                {"amount": "-200.00", "description": "Online Purchase", "merchant": "Amazon", "reference": "WEB001"},
                {"amount": "-35.00", "description": "Mobile Top-up", "merchant": "Zain Jordan", "reference": "BIL001"},
                {"amount": "2000.00", "description": "Investment Return", "merchant": "Jordan Investment Bank", "reference": "INV001"},
                {"amount": "-150.00", "description": "Electricity Bill", "merchant": "EDCO", "reference": "BIL002"}
            ]
            
            for i, tx in enumerate(mock_transactions):
                transaction_date = base_date + timedelta(days=i*3)
                amount = float(tx["amount"])
                
                transactions.append({
                    "AccountId": account_id,
                    "TransactionId": f"tx_{account_id}_{i+1}",
                    "TransactionReference": tx["reference"],
                    "Amount": {
                        "Amount": str(abs(amount)),
                        "Currency": "JOD"
                    },
                    "CreditDebitIndicator": "Credit" if amount > 0 else "Debit",
                    "Status": "Booked",
                    "BookingDateTime": transaction_date.isoformat() + "Z",
                    "ValueDateTime": transaction_date.isoformat() + "Z",
                    "TransactionInformation": tx["description"],
                    "MerchantDetails": {
                        "MerchantName": tx["merchant"],
                        "MerchantCategoryCode": "5411"
                    },
                    "ProprietaryBankTransactionCode": {
                        "Code": "Transfer",
                        "Issuer": "JoPACC"
                    }
                })
            
            return {
                "Data": {
                    "Transaction": transactions
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/aisp/accounts/{account_id}/transactions"
                }
            }
        
        headers = await self.get_headers()
        params = {}
        if from_booking_date:
            params["fromBookingDateTime"] = from_booking_date.isoformat() + "Z"
        if to_booking_date:
            params["toBookingDateTime"] = to_booking_date.isoformat() + "Z"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/open-banking/v1.0/aisp/accounts/{account_id}/transactions",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    # Payment Initiation Services (PIS) - Following JoPACC v1.0 Standards
    async def create_payment_consent(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment consent following JoPACC PIS v1.0 standards"""
        if self.sandbox_mode:
            consent_id = f"urn:jopacc:payment-consent:{str(uuid.uuid4())}"
            return {
                "Data": {
                    "ConsentId": consent_id,
                    "Status": "AwaitingAuthorisation",
                    "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                    "CreationDateTime": datetime.utcnow().isoformat() + "Z",
                    "Initiation": payment_data
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/pisp/domestic-payment-consents/{consent_id}"
                }
            }
        
        headers = await self.get_headers()
        consent_data = {
            "Data": {
                "Initiation": payment_data
            },
            "Risk": {
                "PaymentContextCode": "Other"
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/open-banking/v1.0/pisp/domestic-payment-consents",
                headers=headers,
                json=consent_data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_payment(self, consent_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment following JoPACC PIS v1.0 standards"""
        if self.sandbox_mode:
            payment_id = f"urn:jopacc:payment:{str(uuid.uuid4())}"
            return {
                "Data": {
                    "DomesticPaymentId": payment_id,
                    "ConsentId": consent_id,
                    "Status": "AcceptedSettlementInProcess",
                    "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                    "CreationDateTime": datetime.utcnow().isoformat() + "Z",
                    "Initiation": payment_data
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/pisp/domestic-payments/{payment_id}"
                }
            }
        
        headers = await self.get_headers()
        payment_request = {
            "Data": {
                "ConsentId": consent_id,
                "Initiation": payment_data
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/open-banking/v1.0/pisp/domestic-payments",
                headers=headers,
                json=payment_request
            )
            response.raise_for_status()
            return response.json()
    
    # Extended Services - FX and Additional Services
    async def get_exchange_rates(self, base_currency: str = "JOD") -> Dict[str, Any]:
        """Get exchange rates - Extended Service - only real API calls"""
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/open-banking/v1.0/fx/exchange-rates",
                headers=headers,
                params={"baseCurrency": base_currency}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"JoPACC Exchange Rates API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
    
    async def get_fx_rates(self) -> Dict[str, Any]:
        """Get FX rates using real JoPACC endpoint - only real API calls"""
        
        headers = await self.get_headers()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/gateway/Foreign%20Exchange/v1.3/institution/FXs",
                headers=headers
            )
            
            if response.status_code == 200:
                # Return the actual API data
                return response.json()
            else:
                # Return error response instead of mock data
                error_msg = f"JoPACC FX Rates API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
    
    async def get_fx_quote(self, target_currency: str, amount: float = None) -> Dict[str, Any]:
        """Get FX quote using real JoPACC endpoint - only real API calls"""
        
        # Real JoPACC API call with exact headers and URL you provided
        headers = {
            "x-interactions-id": str(uuid.uuid4()),
            "Authorization": os.getenv("JOPACC_AUTHORIZATION", "Bearer demo_token"),
            "x-financial-id": os.getenv("JOPACC_FINANCIAL_ID", "001"),
            "x-jws-signature": os.getenv("JOPACC_JWS_SIGNATURE", ""),
            "x-idempotency-key": str(uuid.uuid4())
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                "https://jpcjofsdev.apigw-az-eu.webmethods.io/gateway/Foreign%20Exchange%20%28FX%29/v0.4.3/institution/FXs",
                headers=headers
            )
            
            if response.status_code == 200:
                # Process the real API response
                fx_data = response.json()
                
                # Convert JoPACC FX API response to our expected format
                if "data" in fx_data and fx_data["data"]:
                    # Find the target currency in the response
                    for fx_rate in fx_data["data"]:
                        if fx_rate.get("targetCurrency") == target_currency:
                            rate = fx_rate.get("conversionValue", 1.0)
                            converted_amount = amount * rate if amount else None
                            
                            return {
                                "quoteId": str(uuid.uuid4()),
                                "baseCurrency": fx_rate.get("sourceCurrency", "JOD"),
                                "targetCurrency": target_currency,
                                "rate": rate,
                                "amount": amount,
                                "convertedAmount": converted_amount,
                                "validUntil": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z",
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                    
                    # If target currency not found, use first available rate
                    if fx_data["data"]:
                        first_rate = fx_data["data"][0]
                        rate = first_rate.get("conversionValue", 1.0)
                        converted_amount = amount * rate if amount else None
                        
                        return {
                            "quoteId": str(uuid.uuid4()),
                            "baseCurrency": first_rate.get("sourceCurrency", "JOD"),
                            "targetCurrency": first_rate.get("targetCurrency", target_currency),
                            "rate": rate,
                            "amount": amount,
                            "convertedAmount": converted_amount,
                            "validUntil": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                
                # If no data in response, raise error
                error_msg = "JoPACC FX API returned no data"
                print(error_msg)
                raise Exception(error_msg)
            else:
                # Return error response instead of mock data
                error_msg = f"JoPACC FX API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
    
    async def create_transfer(self, from_account_id: str, to_account_id: str, amount: float, 
                            currency: str = "JOD", description: str = None) -> Dict[str, Any]:
        """Create transfer between accounts or to wallet - only real API calls"""
        
        headers = await self.get_headers()
        transfer_data = {
            "fromAccount": from_account_id,
            "toAccount": to_account_id,
            "amount": amount,
            "currency": currency,
            "description": description,
            "transferType": "internal"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/gateway/Payments/v1.3/transfers",
                headers=headers,
                json=transfer_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"JoPACC Transfer API Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
        
    # Legacy methods for backward compatibility
    async def get_user_accounts(self, user_consent_id: str) -> List[Dict[str, Any]]:
        """Legacy method - converts new format to old format"""
        accounts_response = await self.get_accounts_new()
        
        # Convert new format to legacy format
        accounts = []
        for account in accounts_response["accounts"]:
            accounts.append({
                "account_id": account["accountId"],
                "account_name": account["accountName"],
                "account_number": account["accountNumber"],
                "bank_name": account["bankName"],
                "bank_code": account["bankCode"],
                "account_type": account["accountType"],
                "currency": account["currency"],
                "balance": account["balance"]["current"],
                "available_balance": account["balance"]["available"],
                "status": "active",
                "last_updated": account["lastUpdated"]
            })
        return accounts
    
    async def request_user_consent(self, user_id: str, permissions: List[str]) -> Dict[str, Any]:
        """Legacy method - creates account access consent"""
        consent_response = await self.create_account_access_consent(permissions, user_id)
        
        if self.sandbox_mode:
            return {
                "consent_id": consent_response["Data"]["ConsentId"],
                "user_id": user_id,
                "permissions": permissions,
                "status": "granted",
                "consent_url": f"https://sandbox.jopacc.com/consent/{consent_response['Data']['ConsentId']}",
                "expires_at": consent_response["Data"]["ExpirationDateTime"],
                "created_at": consent_response["Data"]["CreationDateTime"]
            }
        
        return consent_response
    
    async def convert_currency(self, from_currency: str, to_currency: str, amount: float) -> Dict[str, Any]:
        """Legacy method for currency conversion"""
        if from_currency != "JOD":
            # For now, we only support JOD as base currency
            raise ValueError("Only JOD base currency is supported")
        
        quote = await self.get_fx_quote(to_currency, amount)
        
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "original_amount": amount,
            "converted_amount": quote.get("convertedAmount", amount),
            "exchange_rate": quote.get("rate", 1.0),
            "conversion_date": quote.get("timestamp", datetime.utcnow().isoformat() + "Z")
        }
        
    # Removed duplicate OAuth2 methods - using direct token authentication instead
    
    async def get_consent_status(self, consent_id: str) -> Dict[str, Any]:
        """Get consent status"""
        if self.sandbox_mode:
            return {
                "consent_id": consent_id,
                "status": "granted",
                "permissions": ["ais", "pis", "fps", "fx"],
                "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/consent/v1/status/{consent_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()