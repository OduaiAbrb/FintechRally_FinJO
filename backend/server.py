from fastapi import FastAPI, HTTPException, Depends, status, Request, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import uuid
from bson import ObjectId
import logging
from services.jordan_open_finance import JordanOpenFinanceService
from services.hey_dinar_ai import HeyDinarAI
from services.aml_monitor import AMLMonitor
from services.biometric_auth import BiometricAuthenticationService, BiometricType
from services.risk_scoring import RiskScoringService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Finjo DinarX Platform", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# MongoDB configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/stablecoin_db")
client = AsyncIOMotorClient(MONGO_URL)
database = client.get_database("stablecoin_db")
db = database  # Alias for database

# Database collections
users_collection = database.get_collection("users")
wallets_collection = database.get_collection("wallets")
transactions_collection = database.get_collection("transactions")
accounts_collection = database.get_collection("accounts")
linked_accounts_collection = database.get_collection("linked_accounts")
consents_collection = database.get_collection("consents")
payments_collection = database.get_collection("payments")
chat_conversations_collection = database.get_collection("chat_conversations")

# Initialize services
jof_service = JordanOpenFinanceService()
hey_dinar_ai = HeyDinarAI()
aml_monitor = AMLMonitor(MONGO_URL)
biometric_service = BiometricAuthenticationService(MONGO_URL)
risk_service = RiskScoringService(MONGO_URL)

# Database migration function
async def migrate_wallet_fields():
    """Migrate wallet documents from stablecoin_balance to dinarx_balance"""
    try:
        # Find all wallets that have stablecoin_balance but not dinarx_balance
        wallets_to_migrate = await wallets_collection.find({
            "stablecoin_balance": {"$exists": True},
            "dinarx_balance": {"$exists": False}
        }).to_list(length=None)
        
        for wallet in wallets_to_migrate:
            # Update the wallet to use dinarx_balance instead of stablecoin_balance
            await wallets_collection.update_one(
                {"_id": wallet["_id"]},
                {
                    "$set": {
                        "dinarx_balance": wallet.get("stablecoin_balance", 0),
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "stablecoin_balance": ""
                    }
                }
            )
        
        print(f"Migrated {len(wallets_to_migrate)} wallet documents to use dinarx_balance")
        
    except Exception as e:
        print(f"Error during wallet migration: {e}")

# Run migration on startup
@app.on_event("startup")
async def startup_event():
    await migrate_wallet_fields()

# Pydantic models
class UserRegistration(BaseModel):
    email: str
    password: str
    full_name: str
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: Optional[str] = None
    created_at: datetime
    is_active: bool = True

class WalletBalance(BaseModel):
    id: str
    user_id: str
    jd_balance: float = 0.0
    dinarx_balance: float = 0.0
    created_at: datetime
    updated_at: datetime

class Transaction(BaseModel):
    id: str
    user_id: str
    transaction_type: str  # 'deposit', 'withdrawal', 'transfer', 'exchange'
    amount: float
    currency: str  # 'JD' or 'DINARX'
    status: str  # 'pending', 'completed', 'failed'
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TransactionCreate(BaseModel):
    transaction_type: str
    amount: float
    currency: str
    description: Optional[str] = None

class ExchangeRequest(BaseModel):
    from_currency: str  # 'JD' or 'DINARX'
    to_currency: str    # 'JD' or 'DINARX'
    amount: float

class ConsentRequest(BaseModel):
    permissions: List[str]

class PaymentInitiation(BaseModel):
    recipient_account: str
    amount: float
    currency: str = "JOD"
    reference: Optional[str] = None
    description: Optional[str] = None

class LinkedAccount(BaseModel):
    account_id: str
    account_name: str
    account_number: str
    bank_name: str
    bank_code: str
    account_type: str
    currency: str
    balance: float
    available_balance: float
    status: str
    last_updated: datetime

class ChatMessageRequest(BaseModel):
    message: str

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str = "JOD"
    description: Optional[str] = None

class UserProfileResponse(BaseModel):
    user_info: dict
    wallet_balance: dict
    linked_accounts: List[dict]
    total_balance: float
    fx_rates: dict
    recent_transfers: List[dict]

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await users_collection.find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
    return user

# API Routes
@app.get("/")
async def root():
    return {"message": "Stablecoin Fintech Platform API", "version": "1.0.0"}

@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    user_doc = {
        "_id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "phone_number": user_data.phone_number,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await users_collection.insert_one(user_doc)
    
    # Create wallet for new user
    wallet_id = str(uuid.uuid4())
    wallet_doc = {
        "_id": wallet_id,
        "user_id": user_id,
        "jd_balance": 0.0,
        "dinarx_balance": 0.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await wallets_collection.insert_one(wallet_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "phone_number": user_data.phone_number
        }
    }

@app.post("/api/auth/login")
async def login_user(user_credentials: UserLogin):
    user = await users_collection.find_one({"email": user_credentials.email})
    
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    access_token = create_access_token(data={"sub": user["_id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "phone_number": user.get("phone_number")
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "phone_number": current_user.get("phone_number"),
        "created_at": current_user["created_at"],
        "is_active": current_user["is_active"]
    }

@app.get("/api/wallet")
async def get_wallet_balance(current_user: dict = Depends(get_current_user)):
    wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
    
    if not wallet:
        # Create wallet if it doesn't exist
        wallet_id = str(uuid.uuid4())
        wallet_doc = {
            "_id": wallet_id,
            "user_id": current_user["_id"],
            "jd_balance": 0.0,
            "dinarx_balance": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await wallets_collection.insert_one(wallet_doc)
        wallet = wallet_doc
    
    return {
        "id": wallet["_id"],
        "user_id": wallet["user_id"],
        "jd_balance": wallet["jd_balance"],
        "dinarx_balance": wallet.get("dinarx_balance", wallet.get("stablecoin_balance", 0)),
        "created_at": wallet["created_at"],
        "updated_at": wallet["updated_at"]
    }

@app.post("/api/wallet/exchange")
async def exchange_currency(
    exchange_request: ExchangeRequest,
    current_user: dict = Depends(get_current_user)
):
    wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Simple 1:1 exchange rate for MVP
    exchange_rate = 1.0
    
    # Validate exchange request
    if exchange_request.from_currency == exchange_request.to_currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot exchange same currency"
        )
    
    # Check sufficient balance
    if exchange_request.from_currency == "JD":
        if wallet["jd_balance"] < exchange_request.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient JD balance"
            )
    else:
        current_dinarx_balance = wallet.get("dinarx_balance", wallet.get("stablecoin_balance", 0))
        if current_dinarx_balance < exchange_request.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient DinarX balance"
            )
    
    # Perform exchange
    if exchange_request.from_currency == "JD":
        new_jd_balance = wallet["jd_balance"] - exchange_request.amount
        new_dinarx_balance = wallet.get("dinarx_balance", wallet.get("stablecoin_balance", 0)) + (exchange_request.amount * exchange_rate)
    else:
        new_jd_balance = wallet["jd_balance"] + (exchange_request.amount * exchange_rate)
        new_dinarx_balance = wallet.get("dinarx_balance", wallet.get("stablecoin_balance", 0)) - exchange_request.amount
    
    # Update wallet
    await wallets_collection.update_one(
        {"user_id": current_user["_id"]},
        {
            "$set": {
                "jd_balance": new_jd_balance,
                "dinarx_balance": new_dinarx_balance,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_doc = {
        "_id": transaction_id,
        "transaction_id": transaction_id,
        "user_id": current_user["_id"],
        "transaction_type": "exchange",
        "amount": exchange_request.amount,
        "currency": exchange_request.from_currency,
        "to_currency": exchange_request.to_currency,
        "exchange_rate": exchange_rate,
        "status": "completed",
        "description": f"Exchange {exchange_request.amount} {exchange_request.from_currency} to {exchange_request.to_currency}",
        "timestamp": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "account_id": current_user.get("_id"),
        "account_age_days": (datetime.utcnow() - current_user.get("created_at", datetime.utcnow())).days
    }
    
    await transactions_collection.insert_one(transaction_doc)
    
    # Run AML monitoring
    try:
        aml_alert = await aml_monitor.monitor_transaction(transaction_doc)
        if aml_alert:
            logging.info(f"AML Alert generated for exchange {transaction_id}: {aml_alert.alert_type.value}")
    except Exception as e:
        logging.error(f"AML monitoring error for exchange {transaction_id}: {e}")
        # Don't fail the transaction due to AML monitoring errors
    
    return {
        "message": "Exchange completed successfully",
        "transaction_id": transaction_id,
        "new_jd_balance": new_jd_balance,
        "new_dinarx_balance": new_dinarx_balance
    }

@app.get("/api/transactions")
async def get_transactions(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    cursor = transactions_collection.find({"user_id": current_user["_id"]})
    cursor = cursor.sort("created_at", -1).skip(offset).limit(limit)
    
    transactions = []
    async for transaction in cursor:
        transactions.append({
            "id": transaction["_id"],
            "user_id": transaction["user_id"],
            "transaction_type": transaction["transaction_type"],
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "status": transaction["status"],
            "description": transaction.get("description"),
            "created_at": transaction["created_at"],
            "updated_at": transaction["updated_at"]
        })
    
    return {
        "transactions": transactions,
        "total": len(transactions),
        "limit": limit,
        "offset": offset
    }

@app.post("/api/wallet/deposit")
async def deposit_funds(
    transaction_request: TransactionCreate,
    current_user: dict = Depends(get_current_user)
):
    wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Update wallet balance
    if transaction_request.currency == "JD":
        new_balance = wallet["jd_balance"] + transaction_request.amount
        await wallets_collection.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {
                    "jd_balance": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        current_dinarx_balance = wallet.get("dinarx_balance", wallet.get("stablecoin_balance", 0))
        new_balance = current_dinarx_balance + transaction_request.amount
        await wallets_collection.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {
                    "dinarx_balance": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_doc = {
        "_id": transaction_id,
        "transaction_id": transaction_id,
        "user_id": current_user["_id"],
        "transaction_type": "deposit",
        "amount": transaction_request.amount,
        "currency": transaction_request.currency,
        "status": "completed",
        "description": transaction_request.description or f"Deposit {transaction_request.amount} {transaction_request.currency}",
        "timestamp": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "account_id": current_user.get("_id"),
        "account_age_days": (datetime.utcnow() - current_user.get("created_at", datetime.utcnow())).days
    }
    
    await transactions_collection.insert_one(transaction_doc)
    
    # Run AML monitoring
    try:
        aml_alert = await aml_monitor.monitor_transaction(transaction_doc)
        if aml_alert:
            # Log alert for monitoring
            logging.info(f"AML Alert generated for transaction {transaction_id}: {aml_alert.alert_type.value}")
    except Exception as e:
        logging.error(f"AML monitoring error for transaction {transaction_id}: {e}")
        # Don't fail the transaction due to AML monitoring errors
    
    return {
        "message": "Deposit completed successfully",
        "transaction_id": transaction_id,
        "new_balance": new_balance
    }

# Open Banking API Endpoints

@app.post("/api/open-banking/consent")
async def request_banking_consent(
    consent_request: ConsentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Request user consent for accessing banking data using JoPACC standards"""
    try:
        # Create account access consent using JoPACC AIS standards
        consent_response = await jof_service.create_account_access_consent(
            permissions=consent_request.permissions,
            user_id=current_user["_id"]
        )
        
        # Store consent in database
        consent_id = consent_response["Data"]["ConsentId"]
        consent_doc = {
            "_id": consent_id,
            "user_id": current_user["_id"],
            "permissions": consent_request.permissions,
            "status": consent_response["Data"]["Status"],
            "expires_at": datetime.fromisoformat(consent_response["Data"]["ExpirationDateTime"].replace("Z", "+00:00")),
            "created_at": datetime.fromisoformat(consent_response["Data"]["CreationDateTime"].replace("Z", "+00:00")),
            "jopacc_consent_data": consent_response
        }
        
        await consents_collection.insert_one(consent_doc)
        
        # Return in legacy format for frontend compatibility
        return {
            "consent_id": consent_id,
            "user_id": current_user["_id"],
            "permissions": consent_request.permissions,
            "status": "granted",
            "consent_url": f"https://sandbox.jopacc.com/consent/{consent_id}",
            "expires_at": consent_response["Data"]["ExpirationDateTime"],
            "created_at": consent_response["Data"]["CreationDateTime"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error requesting consent: {str(e)}"
        )

@app.post("/api/open-banking/connect-accounts")
async def connect_accounts(current_user: dict = Depends(get_current_user)):
    """Connect user accounts without requiring full consent process"""
    try:
        # For demo purposes, we'll simulate account connection
        # In production, this would trigger the full JoPACC consent flow
        
        # Create or update a demo consent record
        consent_doc = {
            "user_id": current_user["_id"],
            "consent_id": f"demo_consent_{str(uuid.uuid4())[:8]}",
            "permissions": ["accounts", "balances", "transactions"],
            "status": "granted",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=90)
        }
        
        await consents_collection.update_one(
            {"user_id": current_user["_id"]},
            {"$set": consent_doc},
            upsert=True
        )
        
        # Get and return the connected accounts in dashboard format
        accounts_response = await get_linked_accounts(current_user)
        
        # Convert to dashboard format
        dashboard_data = {
            "has_linked_accounts": True,
            "total_balance": sum(acc["balance"] for acc in accounts_response["accounts"]),
            "accounts": accounts_response["accounts"],
            "recent_transactions": [],  # Will be populated by real API
            "total_accounts": len(accounts_response["accounts"])
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting accounts: {str(e)}"
        )

@app.get("/api/open-banking/accounts")
async def get_linked_accounts(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get user's linked bank accounts using JoPACC AIS standards with account-dependent flow"""
    try:
        # Get customer ID from header or use default
        customer_id = request.headers.get("x-customer-id", "IND_CUST_015")
        
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No banking consent found. Please link your bank accounts first."
            )
        
        # Get accounts with balances using the new dependent flow - only real API calls
        try:
            accounts_response = await jof_service.get_accounts_with_balances(limit=20, customer_id=customer_id)
        except Exception as api_error:
            # Return detailed error information instead of mock data
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"JoPACC API unavailable: {str(api_error)}"
            )
        
        # Convert JoPACC format to legacy format for frontend compatibility
        accounts = []
        
        # Process accounts from real API response
        for account in accounts_response.get("accounts", []):
            # Extract account info from the real JoPACC response structure
            account_type_info = account.get("accountType", {})
            available_balance_info = account.get("availableBalance", {})
            main_route_info = account.get("mainRoute", {})
            institution_info = account.get("institutionBasicInfo", {})
            institution_name = institution_info.get("name", {})
            
            account_data = {
                "account_id": account.get("accountId", ""),
                "account_name": account_type_info.get("name", "Unknown Account"),
                "account_number": main_route_info.get("address", "").replace("JO27CBJO", "").replace("0000000000000000", ""),
                "bank_name": institution_name.get("enName", "Unknown Bank"),
                "bank_code": institution_info.get("institutionIdentification", {}).get("address", ""),
                "account_type": account_type_info.get("code", "UNKNOWN"),
                "currency": account.get("accountCurrency", "JOD"),
                "balance": float(available_balance_info.get("balanceAmount", 0)),
                "available_balance": float(available_balance_info.get("balanceAmount", 0)),
                "status": account.get("accountStatus", "unknown"),
                "last_updated": account.get("lastModificationDateTime", ""),
                "iban": main_route_info.get("address", ""),
                "balance_position": available_balance_info.get("balancePosition", "credit"),
                # Add detailed balance information if available
                "detailed_balances": account.get("detailed_balances", []),
                "balance_last_updated": account.get("balance_last_updated")
            }
            
            accounts.append(account_data)
            
            # Store/update account in database
            account_doc = {
                "_id": account.get("accountId", ""),
                "user_id": current_user["_id"],
                "account_name": account_type_info.get("name", "Unknown Account"),
                "account_number": main_route_info.get("address", "").replace("JO27CBJO", "").replace("0000000000000000", ""),
                "bank_name": institution_name.get("enName", "Unknown Bank"),
                "bank_code": institution_info.get("institutionIdentification", {}).get("address", ""),
                "account_type": account_type_info.get("code", "UNKNOWN"),
                "currency": account.get("accountCurrency", "JOD"),
                "balance": float(available_balance_info.get("balanceAmount", 0)),
                "available_balance": float(available_balance_info.get("balanceAmount", 0)),
                "status": account.get("accountStatus", "unknown"),
                "last_updated": datetime.utcnow(),
                "jopacc_account_data": account
            }
            
            await linked_accounts_collection.update_one(
                {"_id": account["accountId"]},
                {"$set": account_doc},
                upsert=True
            )
        
        return {
            "accounts": accounts,
            "total": len(accounts),
            "dependency_flow": "accounts_with_balances",
            "api_call_sequence": "1. get_accounts_new (with x-customer-id), 2. get_account_balances (without x-customer-id) for each account",
            "data_source": "real_api_only"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching accounts: {str(e)}"
        )

@app.get("/api/open-banking/accounts/{account_id}/balance")
async def get_account_balance(
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific account balance - depends on account_id from accounts API"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No banking consent found"
            )
        
        # Verify account belongs to user
        linked_account = await linked_accounts_collection.find_one({
            "_id": account_id,
            "user_id": current_user["_id"]
        })
        if not linked_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not linked to your profile"
            )
        
        # Use the new account-dependent balance API (without x-customer-id)
        balance_response = await jof_service.get_account_balances(account_id)
        
        # Convert to legacy format for frontend compatibility
        balance = {
            "account_id": account_id,
            "balance": balance_response.get("balances", [{}])[0].get("amount", 0.0),
            "available_balance": balance_response.get("balances", [{}])[0].get("amount", 0.0),
            "currency": balance_response.get("balances", [{}])[0].get("currency", "JOD"),
            "last_updated": balance_response.get("balances", [{}])[0].get("lastUpdated", datetime.utcnow().isoformat() + "Z"),
            "detailed_balances": balance_response.get("balances", []),
            "api_call_info": {
                "method": "get_account_balances",
                "includes_x_customer_id": False,
                "depends_on_account_id": True
            }
        }
        
        # Update stored balance
        await linked_accounts_collection.update_one(
            {"_id": account_id},
            {
                "$set": {
                    "balance": balance["balance"],
                    "available_balance": balance["available_balance"],
                    "last_updated": datetime.utcnow()
                }
            }
        )
        
        return balance
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching balance: {str(e)}"
        )

@app.get("/api/open-banking/accounts/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    limit: int = 50,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get account transaction history"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No banking consent found"
            )
        
        # Verify account belongs to user
        linked_account = await linked_accounts_collection.find_one({
            "_id": account_id,
            "user_id": current_user["_id"]
        })
        if not linked_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not linked to your profile"
            )
        
        # Parse dates if provided
        from_datetime = None
        to_datetime = None
        if from_date:
            from_datetime = datetime.fromisoformat(from_date)
        if to_date:
            to_datetime = datetime.fromisoformat(to_date)
        
        transactions = await jof_service.get_account_transactions(
            account_id, consent["_id"], from_datetime, to_datetime, limit
        )
        
        return {
            "transactions": transactions,
            "total": len(transactions),
            "account_id": account_id,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transactions: {str(e)}"
        )

@app.post("/api/open-banking/payments")
async def initiate_payment(
    payment_request: PaymentInitiation,
    current_user: dict = Depends(get_current_user)
):
    """Initiate payment using PIS"""
    try:
        # Prepare payment data
        payment_data = {
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "recipient": payment_request.recipient_account,
            "reference": payment_request.reference,
            "description": payment_request.description,
            "user_id": current_user["_id"]
        }
        
        # Initiate payment through Jordan Open Finance
        payment_response = await jof_service.initiate_payment(payment_data)
        
        # Store payment record
        payment_doc = {
            "_id": payment_response["payment_id"],
            "user_id": current_user["_id"],
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "recipient": payment_request.recipient_account,
            "reference": payment_request.reference,
            "description": payment_request.description,
            "status": payment_response["status"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await payments_collection.insert_one(payment_doc)
        
        return payment_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating payment: {str(e)}"
        )

@app.get("/api/open-banking/payments/{payment_id}")
async def get_payment_status(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get payment status"""
    try:
        # Verify payment belongs to user
        payment = await payments_collection.find_one({
            "_id": payment_id,
            "user_id": current_user["_id"]
        })
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Get status from Jordan Open Finance
        status_response = await jof_service.get_payment_status(payment_id)
        
        # Update payment status
        await payments_collection.update_one(
            {"_id": payment_id},
            {
                "$set": {
                    "status": status_response["status"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return status_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payment status: {str(e)}"
        )

@app.get("/api/open-banking/fx/rates")
async def get_exchange_rates(
    account_id: str = None,
    base_currency: str = "JOD",
    current_user: dict = Depends(get_current_user)
):
    """Get current exchange rates - optionally account-dependent"""
    try:
        if account_id:
            # Use account-dependent FX rates
            rates_response = await jof_service.get_fx_rates_for_account(account_id)
            return rates_response
        else:
            # Use general FX rates
            rates = await jof_service.get_exchange_rates(base_currency)
            return rates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching exchange rates: {str(e)}"
        )

@app.post("/api/open-banking/fx/convert")
async def convert_currency_amount(
    from_currency: str,
    to_currency: str,
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Convert currency amount"""
    try:
        conversion = await jof_service.convert_currency(from_currency, to_currency, amount)
        return conversion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting currency: {str(e)}"
        )

@app.get("/api/open-banking/products")
async def get_financial_products(current_user: dict = Depends(get_current_user)):
    """Get available financial products"""
    try:
        products = await jof_service.get_financial_products(current_user["_id"])
        return {
            "products": products,
            "total": len(products)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching financial products: {str(e)}"
        )

@app.get("/api/open-banking/dashboard")
async def get_open_banking_dashboard(current_user: dict = Depends(get_current_user)):
    """Get aggregated dashboard data from all linked accounts using real JoPACC API"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            return {
                "message": "No banking consent found",
                "has_linked_accounts": False,
                "total_balance": 0.0,
                "accounts": [],
                "recent_transactions": []
            }
        
        # Get all linked accounts from real JoPACC API
        accounts = []
        total_balance = 0.0
        
        try:
            # Use real JoPACC API to get accounts with balances
            accounts_response = await jof_service.get_accounts_with_balances(limit=20)
            
            for account in accounts_response.get("accounts", []):
                # Extract account info from the real JoPACC response structure
                account_type_info = account.get("accountType", {})
                available_balance_info = account.get("availableBalance", {})
                main_route_info = account.get("mainRoute", {})
                institution_info = account.get("institutionBasicInfo", {})
                institution_name = institution_info.get("name", {})
                
                account_data = {
                    "account_id": account.get("accountId", ""),
                    "account_name": account_type_info.get("name", "Unknown Account"),
                    "bank_name": institution_name.get("enName", "Unknown Bank"),
                    "balance": float(available_balance_info.get("balanceAmount", 0)),
                    "available_balance": float(available_balance_info.get("balanceAmount", 0)),
                    "currency": account.get("accountCurrency", "JOD"),
                    "account_type": account_type_info.get("code", "UNKNOWN"),
                    "status": account.get("accountStatus", "unknown"),
                    "iban": main_route_info.get("address", ""),
                    "balance_position": available_balance_info.get("balancePosition", "credit"),
                    "last_updated": account.get("lastModificationDateTime", ""),
                    "data_source": "real_jopacc_api"
                }
                accounts.append(account_data)
                total_balance += account_data["balance"]
                
                # Store/update account in database for future reference
                account_doc = {
                    "_id": account.get("accountId", ""),
                    "user_id": current_user["_id"],
                    "account_name": account_data["account_name"],
                    "account_number": main_route_info.get("address", "").replace("JO27CBJO", "").replace("0000000000000000", ""),
                    "bank_name": account_data["bank_name"],
                    "bank_code": institution_info.get("institutionIdentification", {}).get("address", ""),
                    "account_type": account_data["account_type"],
                    "currency": account_data["currency"],
                    "balance": account_data["balance"],
                    "available_balance": account_data["available_balance"],
                    "status": account_data["status"],
                    "last_updated": datetime.utcnow(),
                    "jopacc_account_data": account
                }
                
                await linked_accounts_collection.update_one(
                    {"_id": account.get("accountId", "")},
                    {"$set": account_doc},
                    upsert=True
                )
        
        except Exception as e:
            print(f"Error fetching real JoPACC accounts: {e}")
            # If real API fails, fall back to database
            accounts_cursor = linked_accounts_collection.find({"user_id": current_user["_id"]})
            async for account in accounts_cursor:
                account_data = {
                    "account_id": account["_id"],
                    "account_name": account["account_name"],
                    "bank_name": account["bank_name"],
                    "balance": account["balance"],
                    "available_balance": account["available_balance"],
                    "currency": account["currency"],
                    "account_type": account["account_type"],
                    "last_updated": account["last_updated"],
                    "data_source": "database_fallback"
                }
                accounts.append(account_data)
                total_balance += account["balance"]
        
        # Get recent transactions (simplified for now)
        recent_transactions = []
        
        return {
            "has_linked_accounts": len(accounts) > 0,
            "total_balance": total_balance,
            "accounts": accounts,
            "recent_transactions": recent_transactions,
            "total_accounts": len(accounts)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {str(e)}"
        )

# Hey Dinar AI Chat Endpoints

@app.post("/api/hey-dinar/chat")
async def chat_with_hey_dinar(
    chat_request: ChatMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Chat with Hey Dinar AI assistant"""
    try:
        # Gather context data for AI processing
        context_data = {}
        
        # Get wallet balance
        wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
        if wallet:
            context_data["wallet_balance"] = {
                "jd_balance": wallet.get("jd_balance", 0),
                "dinarx_balance": wallet.get("dinarx_balance", wallet.get("stablecoin_balance", 0))
            }
        
        # Get open banking data
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if consent:
            try:
                # Get accounts and transactions
                accounts = await jof_service.get_user_accounts(consent["_id"])
                recent_transactions = []
                
                total_balance = 0
                for account in accounts:
                    total_balance += account.get("balance", 0)
                    try:
                        transactions = await jof_service.get_account_transactions(
                            account["account_id"], consent["_id"], limit=10
                        )
                        for tx in transactions:
                            tx["account_name"] = account["account_name"]
                            tx["bank_name"] = account["bank_name"]
                        recent_transactions.extend(transactions)
                    except:
                        continue
                
                # Sort transactions by date
                recent_transactions.sort(key=lambda x: x["transaction_date"], reverse=True)
                
                context_data["open_banking_data"] = {
                    "has_linked_accounts": len(accounts) > 0,
                    "total_balance": total_balance,
                    "accounts": accounts,
                    "recent_transactions": recent_transactions[:20],  # Top 20 recent transactions
                    "total_accounts": len(accounts)
                }
            except:
                context_data["open_banking_data"] = {"has_linked_accounts": False}
        
        # Get exchange rates
        try:
            exchange_rates = await jof_service.get_exchange_rates()
            context_data["exchange_rates"] = exchange_rates
        except:
            context_data["exchange_rates"] = {}
        
        # Process message with AI
        chat_message = await hey_dinar_ai.process_message(
            user_id=current_user["_id"],
            message=chat_request.message,
            context_data=context_data
        )
        
        # Store chat message in database
        chat_doc = {
            "_id": chat_message.id,
            "user_id": chat_message.user_id,
            "message": chat_message.message,
            "response": chat_message.response,
            "intent": chat_message.intent,
            "confidence": chat_message.confidence,
            "timestamp": chat_message.timestamp,
            "context_data": chat_message.context_data
        }
        
        await chat_conversations_collection.insert_one(chat_doc)
        
        # Get quick actions
        quick_actions = hey_dinar_ai.get_quick_actions()
        
        return {
            "message_id": chat_message.id,
            "user_message": chat_message.message,
            "ai_response": chat_message.response,
            "intent": chat_message.intent,
            "confidence": chat_message.confidence,
            "timestamp": chat_message.timestamp,
            "quick_actions": quick_actions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )

@app.get("/api/hey-dinar/conversation")
async def get_chat_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get chat conversation history"""
    try:
        cursor = chat_conversations_collection.find({"user_id": current_user["_id"]})
        cursor = cursor.sort("timestamp", -1).skip(offset).limit(limit)
        
        conversations = []
        async for chat in cursor:
            conversations.append({
                "id": chat["_id"],
                "message": chat["message"],
                "response": chat["response"],
                "intent": chat["intent"],
                "confidence": chat["confidence"],
                "timestamp": chat["timestamp"]
            })
        
        return {
            "conversations": list(reversed(conversations)),  # Reverse to show oldest first
            "total": len(conversations),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching chat history: {str(e)}"
        )

@app.get("/api/hey-dinar/quick-actions")
async def get_quick_actions(current_user: dict = Depends(get_current_user)):
    """Get quick action buttons for the chat interface"""
    try:
        quick_actions = hey_dinar_ai.get_quick_actions()
        return {"quick_actions": quick_actions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching quick actions: {str(e)}"
        )

@app.delete("/api/hey-dinar/conversation")
async def clear_chat_history(current_user: dict = Depends(get_current_user)):
    """Clear chat conversation history"""
    try:
        result = await chat_conversations_collection.delete_many({"user_id": current_user["_id"]})
        return {
            "message": "Chat history cleared successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing chat history: {str(e)}"
        )

# User Profile and Transfer API Endpoints

@app.get("/api/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get comprehensive user profile with all financial data from real APIs"""
    try:
        # Get user basic info
        user_info = {
            "id": current_user["_id"],
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "phone_number": current_user.get("phone_number"),
            "created_at": current_user["created_at"],
            "is_active": current_user["is_active"]
        }
        
        # Get wallet balance
        wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
        wallet_balance = {
            "jd_balance": wallet.get("jd_balance", 0) if wallet else 0,
            "dinarx_balance": wallet.get("dinarx_balance", wallet.get("stablecoin_balance", 0)) if wallet else 0
        }
        
        # Get linked accounts using real JoPACC API with account-dependent flow - only real API calls
        linked_accounts = []
        total_bank_balance = 0
        
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if consent:
            try:
                # Use the new account-dependent method that gets accounts and balances together
                accounts_response = await jof_service.get_accounts_with_balances(limit=20)
                
                for account in accounts_response.get("accounts", []):
                    # Extract account info from the real JoPACC response structure
                    account_type_info = account.get("accountType", {})
                    available_balance_info = account.get("availableBalance", {})
                    main_route_info = account.get("mainRoute", {})
                    institution_info = account.get("institutionBasicInfo", {})
                    institution_name = institution_info.get("name", {})
                    
                    account_data = {
                        "account_id": account.get("accountId", ""),
                        "account_name": account_type_info.get("name", "Unknown Account"),
                        "account_number": main_route_info.get("address", "").replace("JO27CBJO", "").replace("0000000000000000", ""),
                        "bank_name": institution_name.get("enName", "Unknown Bank"),
                        "bank_code": institution_info.get("institutionIdentification", {}).get("address", ""),
                        "account_type": account_type_info.get("code", "UNKNOWN"),
                        "currency": account.get("accountCurrency", "JOD"),
                        "balance": float(available_balance_info.get("balanceAmount", 0)),
                        "available_balance": float(available_balance_info.get("balanceAmount", 0)),
                        "status": account.get("accountStatus", "unknown"),
                        "last_updated": account.get("lastModificationDateTime", ""),
                        "iban": main_route_info.get("address", ""),
                        "balance_position": available_balance_info.get("balancePosition", "credit"),
                        "detailed_balances": account.get("detailed_balances", []),
                        "balance_last_updated": account.get("balance_last_updated")
                    }
                    
                    linked_accounts.append(account_data)
                    total_bank_balance += account_data["balance"]
                    
            except Exception as e:
                print(f"Error fetching accounts (no fallback): {e}")
                # Set accounts info to indicate API failure
                linked_accounts = []
                total_bank_balance = 0
        
        # Get FX rates using real JoPACC API (account-dependent if we have linked accounts) - only real API calls
        fx_rates = {}
        try:
            if linked_accounts:
                # Use account-dependent FX rates for the first account
                first_account_id = linked_accounts[0]["account_id"]
                fx_response = await jof_service.get_fx_rates_for_account(first_account_id)
                fx_data = fx_response.get("fx_data", {})
                for rate_info in fx_data.get("data", []):
                    fx_rates[rate_info["targetCurrency"]] = rate_info["conversionValue"]
                # Add account context to FX rates
                fx_rates["account_context"] = {
                    "account_id": first_account_id,
                    "account_currency": fx_response.get("account_currency", "JOD")
                }
            else:
                # Use general FX rates
                fx_response = await jof_service.get_fx_rates()
                for rate_info in fx_response.get("data", []):
                    fx_rates[rate_info["targetCurrency"]] = rate_info["conversionValue"]
        except Exception as e:
            print(f"Error fetching FX rates (no fallback): {e}")
            # Set FX rates to empty to indicate API failure
            fx_rates = {}
        
        # Get recent transfers (from transactions collection)
        recent_transfers = []
        try:
            cursor = transactions_collection.find({
                "user_id": current_user["_id"],
                "transaction_type": {"$in": ["transfer", "exchange", "deposit"]}
            }).sort("created_at", -1).limit(10)
            
            async for transfer in cursor:
                recent_transfers.append({
                    "id": transfer["_id"],
                    "type": transfer["transaction_type"],
                    "amount": transfer["amount"],
                    "currency": transfer["currency"],
                    "status": transfer["status"],
                    "description": transfer.get("description"),
                    "created_at": transfer["created_at"]
                })
        except Exception as e:
            print(f"Error fetching transfers: {e}")
        
        # Calculate total balance
        total_balance = total_bank_balance + wallet_balance["jd_balance"] + wallet_balance["dinarx_balance"]
        
        return {
            "user_info": user_info,
            "wallet_balance": wallet_balance,
            "linked_accounts": linked_accounts,
            "total_balance": total_balance,
            "fx_rates": fx_rates,
            "recent_transfers": recent_transfers,
            "summary": {
                "total_accounts": len(linked_accounts),
                "total_bank_balance": total_bank_balance,
                "wallet_total": wallet_balance["jd_balance"] + wallet_balance["dinarx_balance"],
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        )

@app.post("/api/user/transfer")
async def create_transfer(
    transfer_request: TransferRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create transfer from bank account to wallet or between accounts"""
    try:
        # Validate transfer request
        if transfer_request.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer amount must be greater than 0"
            )
        
        # Check if this is a transfer to wallet (indicated by special wallet account ID)
        if transfer_request.to_account_id == "wallet_jd":
            # Transfer from bank account to JD wallet
            # First, verify the source account belongs to user
            consent = await consents_collection.find_one({"user_id": current_user["_id"]})
            if not consent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No banking consent found"
                )
            
            # Get account details and verify balance
            try:
                balance_response = await jof_service.get_account_balances(transfer_request.from_account_id)
                available_balance = 0
                for balance in balance_response.get("balances", []):
                    if balance["type"] == "available":
                        available_balance = balance["amount"]
                        break
                
                if available_balance < transfer_request.amount:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Insufficient balance in source account"
                    )
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not verify account balance"
                )
            
            # Create transfer using JoPACC API (in real implementation)
            # For now, we'll simulate the transfer
            transfer_response = await jof_service.create_transfer(
                from_account_id=transfer_request.from_account_id,
                to_account_id="wallet_jd",
                amount=transfer_request.amount,
                currency=transfer_request.currency,
                description=transfer_request.description or f"Transfer to JD Wallet"
            )
            
            # Update wallet balance
            wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found"
                )
            
            new_jd_balance = wallet["jd_balance"] + transfer_request.amount
            await wallets_collection.update_one(
                {"user_id": current_user["_id"]},
                {
                    "$set": {
                        "jd_balance": new_jd_balance,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Create transaction record
            transaction_id = str(uuid.uuid4())
            transaction_doc = {
                "_id": transaction_id,
                "user_id": current_user["_id"],
                "transaction_type": "transfer",
                "amount": transfer_request.amount,
                "currency": transfer_request.currency,
                "from_account": transfer_request.from_account_id,
                "to_account": "wallet_jd",
                "status": "completed",
                "description": transfer_request.description or f"Transfer to JD Wallet",
                "jopacc_transfer_id": transfer_response.get("transferId"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await transactions_collection.insert_one(transaction_doc)
            
            return {
                "transfer_id": transaction_id,
                "jopacc_transfer_id": transfer_response.get("transferId"),
                "status": "completed",
                "amount": transfer_request.amount,
                "currency": transfer_request.currency,
                "from_account": transfer_request.from_account_id,
                "to_account": "wallet_jd",
                "new_wallet_balance": new_jd_balance,
                "description": transfer_request.description,
                "created_at": datetime.utcnow().isoformat()
            }
            
        else:
            # Transfer between bank accounts using JoPACC API
            transfer_response = await jof_service.create_transfer(
                from_account_id=transfer_request.from_account_id,
                to_account_id=transfer_request.to_account_id,
                amount=transfer_request.amount,
                currency=transfer_request.currency,
                description=transfer_request.description
            )
            
            # Create transaction record
            transaction_id = str(uuid.uuid4())
            transaction_doc = {
                "_id": transaction_id,
                "user_id": current_user["_id"],
                "transaction_type": "transfer",
                "amount": transfer_request.amount,
                "currency": transfer_request.currency,
                "from_account": transfer_request.from_account_id,
                "to_account": transfer_request.to_account_id,
                "status": transfer_response.get("status", "pending"),
                "description": transfer_request.description,
                "jopacc_transfer_id": transfer_response.get("transferId"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await transactions_collection.insert_one(transaction_doc)
            
            return {
                "transfer_id": transaction_id,
                "jopacc_transfer_id": transfer_response.get("transferId"),
                "status": transfer_response.get("status", "pending"),
                "amount": transfer_request.amount,
                "currency": transfer_request.currency,
                "from_account": transfer_request.from_account_id,
                "to_account": transfer_request.to_account_id,
                "description": transfer_request.description,
                "estimated_completion": transfer_response.get("estimatedCompletion"),
                "created_at": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transfer: {str(e)}"
        )

@app.get("/api/user/fx-quote")
async def get_fx_quote(
    target_currency: str,
    amount: float = None,
    account_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get FX quote for currency conversion - optionally account-dependent - only real API calls"""
    try:
        if account_id:
            # Use account-dependent FX quote
            quote_response = await jof_service.get_fx_quote_for_account(account_id, target_currency, amount)
            return quote_response
        else:
            # Use general FX quote
            quote_response = await jof_service.get_fx_quote(target_currency, amount)
            return quote_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"JoPACC FX API unavailable: {str(e)}"
        )

# AML Monitoring API Endpoints

@app.get("/api/aml/dashboard")
async def get_aml_dashboard(current_user: dict = Depends(get_current_user)):
    """Get AML monitoring dashboard data"""
    try:
        # Check if user has admin privileges (in real implementation)
        # For now, allow all authenticated users to access
        dashboard_data = await aml_monitor.get_aml_dashboard()
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching AML dashboard: {str(e)}"
        )

@app.get("/api/aml/alerts")
async def get_aml_alerts(
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get AML alerts with optional filtering"""
    try:
        query = {}
        if risk_level:
            query["risk_level"] = risk_level
        if status:
            query["status"] = status
        
        cursor = aml_monitor.alerts_collection.find(query).sort("timestamp", -1).limit(limit)
        alerts = []
        
        async for alert in cursor:
            alerts.append({
                "alert_id": alert["alert_id"],
                "transaction_id": alert["transaction_id"],
                "user_id": alert["user_id"],
                "alert_type": alert["alert_type"],
                "risk_level": alert["risk_level"],
                "score": alert["score"],
                "description": alert["description"],
                "timestamp": alert["timestamp"],
                "status": alert["status"],
                "cbj_reported": alert.get("cbj_reported", False)
            })
        
        return {"alerts": alerts, "total": len(alerts)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching AML alerts: {str(e)}"
        )

@app.post("/api/aml/alerts/{alert_id}/resolve")
async def resolve_aml_alert(
    alert_id: str,
    resolution_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Resolve an AML alert with analyst feedback"""
    try:
        is_false_positive = resolution_data.get("is_false_positive", False)
        resolution = resolution_data.get("resolution", "")
        analyst_id = current_user["_id"]
        
        await aml_monitor.process_alert_feedback(
            alert_id, is_false_positive, resolution, analyst_id
        )
        
        return {"message": "Alert resolved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolving alert: {str(e)}"
        )

@app.get("/api/aml/user-risk/{user_id}")
async def get_user_risk_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user's risk profile and transaction patterns"""
    try:
        # Get user's recent transactions
        cursor = transactions_collection.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)],
            limit=100
        )
        
        transactions = []
        async for tx in cursor:
            transactions.append({
                "transaction_id": tx.get("transaction_id", tx["_id"]),
                "amount": tx["amount"],
                "transaction_type": tx["transaction_type"],
                "timestamp": tx.get("timestamp", tx["created_at"].isoformat()),
                "currency": tx.get("currency", "JOD")
            })
        
        # Get user's alerts
        alert_cursor = aml_monitor.alerts_collection.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)],
            limit=20
        )
        
        alerts = []
        async for alert in alert_cursor:
            alerts.append({
                "alert_id": alert["alert_id"],
                "alert_type": alert["alert_type"],
                "risk_level": alert["risk_level"],
                "score": alert["score"],
                "timestamp": alert["timestamp"],
                "status": alert["status"]
            })
        
        # Calculate risk metrics
        if transactions:
            amounts = [tx["amount"] for tx in transactions]
            risk_metrics = {
                "total_transactions": len(transactions),
                "total_amount": sum(amounts),
                "avg_amount": sum(amounts) / len(amounts),
                "max_amount": max(amounts),
                "total_alerts": len(alerts),
                "high_risk_alerts": len([a for a in alerts if a["risk_level"] == "high"]),
                "critical_alerts": len([a for a in alerts if a["risk_level"] == "critical"])
            }
        else:
            risk_metrics = {
                "total_transactions": 0,
                "total_amount": 0,
                "avg_amount": 0,
                "max_amount": 0,
                "total_alerts": 0,
                "high_risk_alerts": 0,
                "critical_alerts": 0
            }
        
        return {
            "user_id": user_id,
            "risk_metrics": risk_metrics,
            "recent_transactions": transactions[:10],
            "recent_alerts": alerts[:10]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user risk profile: {str(e)}"
        )

# Biometric Authentication API Endpoints - DISABLED AS REQUESTED

# @app.post("/api/biometric/enroll")
# async def enroll_biometric(
#     biometric_data: dict,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Enroll user's biometric data - DISABLED"""
#     return {"message": "Biometric authentication is currently disabled"}

# @app.post("/api/biometric/authenticate")
# async def authenticate_biometric(
#     biometric_data: dict,
#     request: Request,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Authenticate user using biometric data - DISABLED"""
#     return {"message": "Biometric authentication is currently disabled"}

# @app.get("/api/biometric/user/{user_id}")
# async def get_user_biometrics(
#     user_id: str,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Get user's enrolled biometrics - DISABLED"""
#     return {"biometrics": []}

# @app.delete("/api/biometric/revoke/{template_id}")
# async def revoke_biometric(
#     template_id: str,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Revoke a biometric template - DISABLED"""
#     return {"message": "Biometric authentication is currently disabled"}

# @app.get("/api/biometric/history")
# async def get_biometric_history(
#     limit: int = 50,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Get user's biometric authentication history - DISABLED"""
#     return {"history": []}

# Risk Scoring API Endpoints

@app.get("/api/risk/assessment/{user_id}")
async def get_risk_assessment(
    user_id: str,
    transaction_data: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive risk assessment for user"""
    try:
        # In production, check admin privileges
        assessment = await risk_service.assess_comprehensive_risk(
            user_id,
            transaction_data
        )
        
        return {
            "assessment_id": assessment.assessment_id,
            "risk_level": assessment.risk_level.value,
            "risk_score": assessment.risk_score,
            "credit_score": int(assessment.credit_score * 850),  # Convert back to credit score
            "fraud_score": assessment.fraud_score,
            "behavioral_score": assessment.behavioral_score,
            "risk_factors": assessment.risk_factors,
            "protective_factors": assessment.protective_factors,
            "recommendations": assessment.recommendations,
            "timestamp": assessment.timestamp
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment error: {str(e)}"
        )

@app.get("/api/risk/history/{user_id}")
async def get_risk_history(
    user_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get user's risk assessment history"""
    try:
        history = await risk_service.get_user_risk_history(user_id, limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching risk history: {str(e)}"
        )

@app.get("/api/risk/dashboard")
async def get_risk_dashboard(current_user: dict = Depends(get_current_user)):
    """Get risk management dashboard"""
    try:
        # Get risk statistics
        pipeline = [
            {
                "$group": {
                    "_id": "$risk_level",
                    "count": {"$sum": 1},
                    "avg_score": {"$avg": "$risk_score"}
                }
            }
        ]
        
        cursor = risk_service.risk_assessments_collection.aggregate(pipeline)
        risk_stats = {}
        
        async for doc in cursor:
            risk_stats[doc["_id"]] = {
                "count": doc["count"],
                "avg_score": doc["avg_score"]
            }
        
        # Get recent assessments
        recent_cursor = risk_service.risk_assessments_collection.find(
            {}
        ).sort("timestamp", -1).limit(10)
        
        recent_assessments = []
        async for doc in recent_cursor:
            recent_assessments.append({
                "assessment_id": doc["assessment_id"],
                "user_id": doc["user_id"],
                "risk_level": doc["risk_level"],
                "risk_score": doc["risk_score"],
                "timestamp": doc["timestamp"]
            })
        
        return {
            "risk_statistics": risk_stats,
            "recent_assessments": recent_assessments
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching risk dashboard: {str(e)}"
        )

@app.get("/api/open-banking/accounts/{account_id}/offers")
async def get_account_offers(
    account_id: str,
    product_id: str = None,
    skip: int = 0,
    limit: int = 10,
    sort: str = "desc",
    current_user: dict = Depends(get_current_user)
):
    """Get account offers using JoPACC Offers API - account-dependent"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No banking consent found"
            )
        
        # Verify account belongs to user
        linked_account = await linked_accounts_collection.find_one({
            "_id": account_id,
            "user_id": current_user["_id"]
        })
        if not linked_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not linked to your profile"
            )
        
        # Get offers from JoPACC API
        offers_response = await jof_service.get_account_offers(
            account_id=account_id,
            product_id=product_id,
            skip=skip,
            limit=limit,
            sort=sort
        )
        
        return {
            "account_id": account_id,
            "offers": offers_response.get("data", []),
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": len(offers_response.get("data", []))
            },
            "api_info": {
                "endpoint": "JoPACC Offers API",
                "account_dependent": True,
                "customer_id": "IND_CUST_015"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching offers: {str(e)}"
        )

@app.post("/api/auth/validate-iban")
async def validate_iban(
    iban_data: dict
):
    """Validate IBAN using JoPACC IBAN Confirmation API"""
    try:
        # Extract IBAN validation parameters
        account_type = iban_data.get("accountType", "")
        account_id = iban_data.get("accountId", "")
        iban_type = iban_data.get("ibanType", "")
        iban_value = iban_data.get("ibanValue", "")
        uid_type = iban_data.get("uidType", "CUSTOMER_ID")
        uid_value = iban_data.get("uidValue", "IND_CUST_015")
        
        if not all([account_type, account_id, iban_type, iban_value, uid_value]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required IBAN validation parameters"
            )
        
        # Validate IBAN using JoPACC API with manual UID
        validation_response = await jof_service.validate_iban(
            account_type=account_type,
            account_id=account_id,
            iban_type=iban_type,
            iban_value=iban_value,
            customer_id=uid_value
        )
        
        return {
            "valid": True,
            "iban_value": iban_value,
            "validation_result": validation_response,
            "api_info": {
                "endpoint": "JoPACC IBAN Confirmation API",
                "customer_id": uid_value,
                "uid_type": uid_type,
                "validated_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        return {
            "valid": False,
            "iban_value": iban_data.get("ibanValue", ""),
            "error": str(e),
            "api_info": {
                "endpoint": "JoPACC IBAN Confirmation API",
                "customer_id": iban_data.get("uidValue", ""),
                "uid_type": iban_data.get("uidType", ""),
                "validated_at": datetime.utcnow().isoformat() + "Z"
            }
        }

@app.get("/api/loans/eligibility/{account_id}")
async def get_micro_loan_eligibility(
    account_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get micro loan eligibility based on credit score"""
    try:
        # Get customer ID from header or use default
        customer_id = request.headers.get("x-customer-id", "IND_CUST_015")
        
        # Calculate credit score and eligibility
        credit_info = await jof_service.calculate_credit_score(account_id, customer_id)
        
        # Get available banks from accounts API
        accounts_response = await jof_service.get_accounts_new(limit=20, customer_id=customer_id)
        available_banks = []
        
        for account in accounts_response.get("data", []):
            institution_info = account.get("institutionBasicInfo", {})
            bank_name = institution_info.get("name", {}).get("enName", "Unknown Bank")
            bank_code = institution_info.get("institutionIdentification", {}).get("address", "")
            
            if bank_name not in [bank["name"] for bank in available_banks]:
                available_banks.append({
                    "name": bank_name,
                    "code": bank_code,
                    "type": "BANK"
                })
        
        return {
            "account_id": account_id,
            "customer_id": customer_id,
            "credit_score": credit_info["credit_score"],
            "eligibility": credit_info["eligibility"],
            "max_loan_amount": credit_info["max_loan_amount"],
            "eligible_for_loan": credit_info["max_loan_amount"] > 0,
            "available_banks": available_banks,
            "account_info": {
                "balance": credit_info["balance_amount"],
                "status": credit_info["account_status"],
                "type": credit_info["account_type"]
            },
            "calculated_at": credit_info["calculated_at"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating loan eligibility: {str(e)}"
        )

@app.post("/api/loans/apply")
async def apply_for_micro_loan(
    loan_application: dict,
    current_user: dict = Depends(get_current_user)
):
    """Apply for micro loan"""
    try:
        account_id = loan_application.get("account_id")
        loan_amount = loan_application.get("loan_amount")
        selected_bank = loan_application.get("selected_bank")
        loan_term = loan_application.get("loan_term", 12)  # months
        customer_id = loan_application.get("customer_id", "IND_CUST_015")
        
        if not all([account_id, loan_amount, selected_bank]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required loan application parameters"
            )
        
        # Verify eligibility
        credit_info = await jof_service.calculate_credit_score(account_id, customer_id)
        
        if loan_amount > credit_info["max_loan_amount"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Loan amount exceeds maximum eligible amount of {credit_info['max_loan_amount']} JOD"
            )
        
        # Create loan application
        loan_application_doc = {
            "_id": str(uuid.uuid4()),
            "user_id": current_user["_id"],
            "account_id": account_id,
            "customer_id": customer_id,
            "loan_amount": loan_amount,
            "selected_bank": selected_bank,
            "loan_term": loan_term,
            "credit_score": credit_info["credit_score"],
            "eligibility": credit_info["eligibility"],
            "status": "pending",
            "applied_at": datetime.utcnow(),
            "interest_rate": 8.5,  # Fixed rate for now
            "monthly_payment": loan_amount * (1 + 0.085) / loan_term
        }
        
        # Store in database (assuming we have a micro_loans collection)
        await db.micro_loans.insert_one(loan_application_doc)
        
        return {
            "application_id": loan_application_doc["_id"],
            "status": "pending",
            "loan_amount": loan_amount,
            "selected_bank": selected_bank,
            "loan_term": loan_term,
            "estimated_monthly_payment": loan_application_doc["monthly_payment"],
            "interest_rate": loan_application_doc["interest_rate"],
            "applied_at": loan_application_doc["applied_at"],
            "message": "Loan application submitted successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing loan application: {str(e)}"
        )

# User-to-User Transfer API Endpoints

@app.post("/api/transfers/user-to-user")
async def create_user_transfer(
    transfer_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a transfer between platform users"""
    try:
        recipient_identifier = transfer_data.get("recipient_identifier")  # email or phone
        amount = transfer_data.get("amount", 0)
        currency = transfer_data.get("currency", "JOD")
        description = transfer_data.get("description", "")
        
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer amount must be greater than 0"
            )
        
        # Find recipient by email or phone
        recipient = await users_collection.find_one({
            "$or": [
                {"email": recipient_identifier},
                {"phone": recipient_identifier}
            ]
        })
        
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
        
        if recipient["_id"] == current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer to yourself"
            )
        
        # Check sender's balance
        sender_wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
        if not sender_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sender wallet not found"
            )
        
        # Check if sender has sufficient balance
        sender_balance = sender_wallet.get("jd_balance", 0) if currency == "JOD" else sender_wallet.get("dinarx_balance", sender_wallet.get("stablecoin_balance", 0))
        if sender_balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Available: {sender_balance} {currency}"
            )
        
        # Get or create recipient wallet
        recipient_wallet = await wallets_collection.find_one({"user_id": recipient["_id"]})
        if not recipient_wallet:
            # Create wallet for recipient
            recipient_wallet = {
                "_id": str(uuid.uuid4()),
                "user_id": recipient["_id"],
                "jd_balance": 0.0,
                "dinarx_balance": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await wallets_collection.insert_one(recipient_wallet)
        
        # Create transfer transaction
        transfer_id = str(uuid.uuid4())
        
        # Update sender balance
        sender_balance_field = "jd_balance" if currency == "JOD" else "dinarx_balance"
        new_sender_balance = sender_balance - amount
        await wallets_collection.update_one(
            {"user_id": current_user["_id"]},
            {"$set": {sender_balance_field: new_sender_balance, "updated_at": datetime.utcnow()}}
        )
        
        # Update recipient balance
        recipient_balance_field = "jd_balance" if currency == "JOD" else "dinarx_balance"
        recipient_current_balance = recipient_wallet.get(recipient_balance_field, 0)
        new_recipient_balance = recipient_current_balance + amount
        await wallets_collection.update_one(
            {"user_id": recipient["_id"]},
            {"$set": {recipient_balance_field: new_recipient_balance, "updated_at": datetime.utcnow()}}
        )
        
        # Create transaction records for both users
        sender_transaction = {
            "_id": f"{transfer_id}_sender",
            "transaction_id": f"{transfer_id}_sender",
            "user_id": current_user["_id"],
            "transaction_type": "transfer_out",
            "amount": -amount,  # Negative for sender
            "currency": currency,
            "status": "completed",
            "description": f"Transfer to {recipient['full_name']} - {description}",
            "recipient_id": recipient["_id"],
            "recipient_name": recipient["full_name"],
            "timestamp": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "account_id": current_user["_id"],
            "account_age_days": (datetime.utcnow() - current_user.get("created_at", datetime.utcnow())).days
        }
        
        recipient_transaction = {
            "_id": f"{transfer_id}_recipient",
            "transaction_id": f"{transfer_id}_recipient",
            "user_id": recipient["_id"],
            "transaction_type": "transfer_in",
            "amount": amount,  # Positive for recipient
            "currency": currency,
            "status": "completed",
            "description": f"Transfer from {current_user['full_name']} - {description}",
            "sender_id": current_user["_id"],
            "sender_name": current_user["full_name"],
            "timestamp": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "account_id": recipient["_id"],
            "account_age_days": (datetime.utcnow() - recipient.get("created_at", datetime.utcnow())).days
        }
        
        # Insert both transactions
        await transactions_collection.insert_one(sender_transaction)
        await transactions_collection.insert_one(recipient_transaction)
        
        # Run AML monitoring on both transactions
        try:
            sender_aml_alert = await aml_monitor.monitor_transaction(sender_transaction)
            recipient_aml_alert = await aml_monitor.monitor_transaction(recipient_transaction)
            
            if sender_aml_alert:
                logging.info(f"AML Alert for sender transfer {transfer_id}: {sender_aml_alert.alert_type.value}")
            if recipient_aml_alert:
                logging.info(f"AML Alert for recipient transfer {transfer_id}: {recipient_aml_alert.alert_type.value}")
        except Exception as e:
            logging.error(f"AML monitoring error for transfer {transfer_id}: {e}")
        
        return {
            "transfer_id": transfer_id,
            "status": "completed",
            "sender": {
                "name": current_user["full_name"],
                "new_balance": new_sender_balance
            },
            "recipient": {
                "name": recipient["full_name"],
                "identifier": recipient_identifier
            },
            "amount": amount,
            "currency": currency,
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_ids": {
                "sender": f"{transfer_id}_sender",
                "recipient": f"{transfer_id}_recipient"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer failed: {str(e)}"
        )

@app.get("/api/transfers/history")
async def get_transfer_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get user's transfer history"""
    try:
        # Get transfers both sent and received
        cursor = transactions_collection.find({
            "user_id": current_user["_id"],
            "transaction_type": {"$in": ["transfer_out", "transfer_in"]}
        }).sort("timestamp", -1).limit(limit)
        
        transfers = []
        async for transaction in cursor:
            transfer_data = {
                "transaction_id": transaction["transaction_id"],
                "type": transaction["transaction_type"],
                "amount": transaction["amount"],
                "currency": transaction["currency"],
                "status": transaction["status"],
                "description": transaction["description"],
                "timestamp": transaction["timestamp"],
                "created_at": transaction["created_at"]
            }
            
            # Add counterparty information
            if transaction["transaction_type"] == "transfer_out":
                transfer_data["counterparty"] = {
                    "id": transaction.get("recipient_id"),
                    "name": transaction.get("recipient_name"),
                    "type": "recipient"
                }
            else:  # transfer_in
                transfer_data["counterparty"] = {
                    "id": transaction.get("sender_id"),
                    "name": transaction.get("sender_name"),
                    "type": "sender"
                }
            
            transfers.append(transfer_data)
        
        return {
            "transfers": transfers,
            "total": len(transfers)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transfer history: {str(e)}"
        )

@app.get("/api/users/search")
async def search_users(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """Search for users by email or phone for transfers"""
    try:
        if len(query) < 3:
            return {"users": []}
        
        # Search by email or phone (partial match)
        cursor = users_collection.find({
            "$and": [
                {"_id": {"$ne": current_user["_id"]}},  # Exclude current user
                {
                    "$or": [
                        {"email": {"$regex": query, "$options": "i"}},
                        {"phone": {"$regex": query, "$options": "i"}},
                        {"full_name": {"$regex": query, "$options": "i"}}
                    ]
                }
            ]
        }).limit(10)
        
        users = []
        async for user in cursor:
            users.append({
                "id": user["_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "phone": user.get("phone", ""),
                "created_at": user["created_at"]
            })
        
        return {"users": users}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching users: {str(e)}"
        )

# Security System Initialization

@app.post("/api/security/initialize")
async def initialize_security_systems(current_user: dict = Depends(get_current_user)):
    """Initialize all security systems"""
    try:
        # Initialize AML system
        await aml_monitor.initialize_system()
        
        # Initialize biometric system - DISABLED
        # await biometric_service.initialize_biometric_system()
        
        return {
            "message": "Security systems initialized successfully (biometric disabled)",
            "systems": ["AML Monitor", "Risk Scoring"],
            "disabled_systems": ["Biometric Authentication"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security system initialization error: {str(e)}"
        )

@app.get("/api/security/status")
async def get_security_status(current_user: dict = Depends(get_current_user)):
    """Get security systems status"""
    try:
        # Check AML system
        aml_dashboard = await aml_monitor.get_aml_dashboard()
        
        # Check biometric system - DISABLED
        biometric_stats = 0  # Disabled
        
        # Check risk system
        risk_assessments = await risk_service.risk_assessments_collection.count_documents({})
        
        return {
            "aml_system": {
                "status": "active",
                "total_alerts": aml_dashboard.get("total_alerts_7d", 0),
                "model_version": aml_dashboard.get("model_version", "1.0")
            },
            "biometric_system": {
                "status": "disabled",
                "total_templates": 0,
                "message": "Biometric authentication is currently disabled"
            },
            "risk_system": {
                "status": "active",
                "total_assessments": risk_assessments
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking security status: {str(e)}"
        )

# Enhanced Authentication with Risk Scoring

@app.post("/api/auth/login-enhanced")
async def enhanced_login(
    login_data: UserLogin,
    request: Request
):
    """Enhanced login with risk scoring and biometric support"""
    try:
        # First, perform standard authentication
        user = await users_collection.find_one({"email": login_data.email})
        if not user or not pwd_context.verify(login_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get risk assessment
        risk_assessment = await risk_service.assess_comprehensive_risk(user["_id"])
        
        # Get user's biometrics
        biometrics = await biometric_service.get_user_biometrics(user["_id"])
        
        # Generate token
        access_token = create_access_token(data={"sub": user["_id"]})
        
        # Determine if additional verification is needed
        requires_additional_verification = (
            risk_assessment.risk_level.value in ["high", "very_high"] or
            risk_assessment.fraud_score > 0.7
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["_id"],
                "email": user["email"],
                "full_name": user["full_name"]
            },
            "risk_assessment": {
                "risk_level": risk_assessment.risk_level.value,
                "risk_score": float(risk_assessment.risk_score),
                "requires_additional_verification": bool(requires_additional_verification)
            },
            "biometric_options": [str(b["biometric_type"]) for b in biometrics.get("biometrics", [])],
            "security_recommendations": [str(rec) for rec in risk_assessment.recommendations] if risk_assessment.recommendations else []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced login error: {str(e)}"
        )

@app.post("/api/aml/initialize")
async def initialize_aml_system(current_user: dict = Depends(get_current_user)):
    """Initialize AML monitoring system"""
    try:
        await aml_monitor.initialize_system()
        return {"message": "AML system initialized successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing AML system: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)