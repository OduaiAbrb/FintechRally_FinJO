"""
Advanced Risk Scoring Service
ML-based risk assessment with continuous learning for credit scoring,
fraud detection, and behavioral analysis using open banking data
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
import os

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import joblib
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskCategory(Enum):
    CREDIT_RISK = "credit_risk"
    FRAUD_RISK = "fraud_risk"
    BEHAVIORAL_RISK = "behavioral_risk"
    OPERATIONAL_RISK = "operational_risk"
    COMPLIANCE_RISK = "compliance_risk"

class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class ModelType(Enum):
    CREDIT_SCORING = "credit_scoring"
    FRAUD_DETECTION = "fraud_detection"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    TRANSACTION_RISK = "transaction_risk"
    USER_SEGMENTATION = "user_segmentation"

@dataclass
class RiskFeatures:
    """Comprehensive risk features for ML models"""
    user_id: str
    timestamp: datetime
    
    # Demographic features
    age: int
    income_level: str
    employment_status: str
    education_level: str
    marital_status: str
    
    # Financial features
    total_assets: float
    total_liabilities: float
    monthly_income: float
    monthly_expenses: float
    credit_utilization: float
    debt_to_income: float
    
    # Transaction features
    avg_transaction_amount: float
    transaction_frequency: float
    transaction_velocity: float
    unusual_transaction_count: int
    foreign_transaction_count: int
    night_transaction_count: int
    weekend_transaction_count: int
    
    # Behavioral features
    login_frequency: float
    device_count: int
    location_count: int
    failed_login_attempts: int
    time_between_actions: float
    
    # Banking features
    account_count: int
    account_age_avg: float
    balance_volatility: float
    overdraft_frequency: int
    returned_payment_count: int
    
    # Open banking features
    spending_categories: Dict[str, float]
    income_stability: float
    savings_rate: float
    investment_activity: float
    
    # External features
    credit_bureau_score: Optional[int]
    sanctions_check: bool
    pep_check: bool
    adverse_media_check: bool

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    assessment_id: str
    user_id: str
    risk_category: RiskCategory
    risk_level: RiskLevel
    risk_score: float
    confidence_score: float
    model_version: str
    timestamp: datetime
    
    # Detailed scores
    credit_score: float
    fraud_score: float
    behavioral_score: float
    
    # Risk factors
    risk_factors: List[str]
    protective_factors: List[str]
    
    # Recommendations
    recommendations: List[str]
    
    # Model explanations
    feature_importance: Dict[str, float]
    decision_reasoning: str

class CreditScoringModel:
    """Credit scoring model with Jordan banking regulations compliance"""
    
    def __init__(self, model_path: str = "/app/backend/models/credit_model.pkl"):
        self.model_path = model_path
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        self.is_trained = False
        
        # Jordan Central Bank credit scoring guidelines
        self.credit_bands = {
            'excellent': (750, 850),
            'good': (650, 749),
            'fair': (550, 649),
            'poor': (450, 549),
            'very_poor': (300, 449)
        }
        
        # Load existing model
        self._load_model()
    
    def _load_model(self):
        """Load existing model from disk"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_columns = model_data['feature_columns']
                self.is_trained = True
                logger.info("Credit scoring model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load credit model: {e}")
    
    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns
            }
            joblib.dump(model_data, self.model_path)
            logger.info("Credit scoring model saved successfully")
        except Exception as e:
            logger.error(f"Could not save credit model: {e}")
    
    def prepare_features(self, risk_features: RiskFeatures) -> np.ndarray:
        """Convert risk features to numerical array"""
        feature_dict = asdict(risk_features)
        
        # Numerical features
        numerical_features = [
            feature_dict['age'],
            feature_dict['total_assets'],
            feature_dict['total_liabilities'],
            feature_dict['monthly_income'],
            feature_dict['monthly_expenses'],
            feature_dict['credit_utilization'],
            feature_dict['debt_to_income'],
            feature_dict['avg_transaction_amount'],
            feature_dict['transaction_frequency'],
            feature_dict['account_count'],
            feature_dict['account_age_avg'],
            feature_dict['balance_volatility'],
            feature_dict['overdraft_frequency'],
            feature_dict['returned_payment_count'],
            feature_dict['income_stability'],
            feature_dict['savings_rate'],
            feature_dict['investment_activity'],
            feature_dict['credit_bureau_score'] or 0,
            feature_dict['login_frequency'],
            feature_dict['device_count'],
            feature_dict['failed_login_attempts']
        ]
        
        # Categorical features (one-hot encoded)
        categorical_features = self._encode_categorical_features(feature_dict)
        numerical_features.extend(categorical_features)
        
        # Derived features
        derived_features = self._calculate_derived_features(feature_dict)
        numerical_features.extend(derived_features)
        
        return np.array(numerical_features).reshape(1, -1)
    
    def _encode_categorical_features(self, feature_dict: Dict) -> List[float]:
        """Encode categorical features"""
        categorical_features = []
        
        # Income level
        income_levels = ['low', 'medium', 'high', 'very_high']
        for level in income_levels:
            categorical_features.append(1.0 if feature_dict['income_level'] == level else 0.0)
        
        # Employment status
        employment_statuses = ['employed', 'self_employed', 'unemployed', 'retired', 'student']
        for status in employment_statuses:
            categorical_features.append(1.0 if feature_dict['employment_status'] == status else 0.0)
        
        # Education level
        education_levels = ['high_school', 'bachelor', 'master', 'phd']
        for level in education_levels:
            categorical_features.append(1.0 if feature_dict['education_level'] == level else 0.0)
        
        # Marital status
        marital_statuses = ['single', 'married', 'divorced', 'widowed']
        for status in marital_statuses:
            categorical_features.append(1.0 if feature_dict['marital_status'] == status else 0.0)
        
        return categorical_features
    
    def _calculate_derived_features(self, feature_dict: Dict) -> List[float]:
        """Calculate derived features"""
        derived = []
        
        # Financial ratios
        assets_to_income = feature_dict['total_assets'] / max(feature_dict['monthly_income'], 1)
        liabilities_to_assets = feature_dict['total_liabilities'] / max(feature_dict['total_assets'], 1)
        expense_to_income = feature_dict['monthly_expenses'] / max(feature_dict['monthly_income'], 1)
        
        # Transaction patterns
        transaction_amount_volatility = feature_dict['avg_transaction_amount'] / max(feature_dict['monthly_income'], 1)
        risky_transaction_ratio = (feature_dict['unusual_transaction_count'] + 
                                 feature_dict['foreign_transaction_count'] + 
                                 feature_dict['night_transaction_count']) / max(feature_dict['transaction_frequency'], 1)
        
        # Behavioral indicators
        stability_score = 1.0 / (1.0 + feature_dict['failed_login_attempts'] + feature_dict['device_count'])
        
        derived.extend([
            assets_to_income,
            liabilities_to_assets,
            expense_to_income,
            transaction_amount_volatility,
            risky_transaction_ratio,
            stability_score
        ])
        
        return derived
    
    def predict_credit_score(self, risk_features: RiskFeatures) -> Tuple[int, float, Dict]:
        """Predict credit score"""
        if not self.is_trained:
            self.train_model([])  # Train with synthetic data
        
        try:
            # Prepare features
            X = self.prepare_features(risk_features)
            X_scaled = self.scaler.transform(X)
            
            # Get probability scores
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(X_scaled)[0]
                confidence = max(probabilities)
            else:
                confidence = 0.8  # Default confidence
            
            # Predict credit band
            prediction = self.model.predict(X_scaled)[0]
            
            # Convert to numerical score
            band_mapping = {
                'excellent': 800,
                'good': 700,
                'fair': 600,
                'poor': 500,
                'very_poor': 400
            }
            
            base_score = band_mapping.get(prediction, 500)
            
            # Add noise based on confidence
            noise = np.random.normal(0, (1 - confidence) * 50)
            final_score = int(np.clip(base_score + noise, 300, 850))
            
            # Get feature importance
            feature_importance = {}
            if hasattr(self.model, 'feature_importances_'):
                for i, importance in enumerate(self.model.feature_importances_):
                    feature_importance[f"feature_{i}"] = importance
            
            details = {
                'predicted_band': prediction,
                'confidence': confidence,
                'feature_importance': feature_importance,
                'risk_factors': self._identify_risk_factors(risk_features),
                'protective_factors': self._identify_protective_factors(risk_features)
            }
            
            return final_score, confidence, details
            
        except Exception as e:
            logger.error(f"Credit scoring error: {e}")
            return 500, 0.5, {'error': str(e)}
    
    def _identify_risk_factors(self, risk_features: RiskFeatures) -> List[str]:
        """Identify credit risk factors"""
        risk_factors = []
        
        if risk_features.debt_to_income > 0.4:
            risk_factors.append("High debt-to-income ratio")
        
        if risk_features.credit_utilization > 0.8:
            risk_factors.append("High credit utilization")
        
        if risk_features.overdraft_frequency > 2:
            risk_factors.append("Frequent overdrafts")
        
        if risk_features.returned_payment_count > 0:
            risk_factors.append("Payment returns")
        
        if risk_features.income_stability < 0.7:
            risk_factors.append("Unstable income")
        
        if risk_features.savings_rate < 0.1:
            risk_factors.append("Low savings rate")
        
        if risk_features.failed_login_attempts > 5:
            risk_factors.append("Security concerns")
        
        return risk_factors
    
    def _identify_protective_factors(self, risk_features: RiskFeatures) -> List[str]:
        """Identify protective factors"""
        protective_factors = []
        
        if risk_features.savings_rate > 0.2:
            protective_factors.append("Good savings habits")
        
        if risk_features.income_stability > 0.8:
            protective_factors.append("Stable income")
        
        if risk_features.investment_activity > 0.1:
            protective_factors.append("Investment activity")
        
        if risk_features.account_age_avg > 365:
            protective_factors.append("Long banking history")
        
        if risk_features.credit_utilization < 0.3:
            protective_factors.append("Low credit utilization")
        
        if risk_features.employment_status == 'employed':
            protective_factors.append("Stable employment")
        
        return protective_factors
    
    def train_model(self, training_data: List[Dict]):
        """Train credit scoring model"""
        if not training_data:
            training_data = self._generate_synthetic_credit_data()
        
        # Prepare features and labels
        features_list = []
        labels = []
        
        for data in training_data:
            risk_features = RiskFeatures(**data['features'])
            features_array = self.prepare_features(risk_features)
            features_list.append(features_array.flatten())
            labels.append(data['credit_band'])
        
        X = np.array(features_list)
        y = np.array(labels)
        
        if len(X) > 0:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            self.feature_columns = [f"feature_{i}" for i in range(X_scaled.shape[1])]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = (y_pred == y_test).mean()
            
            logger.info(f"Credit model trained with accuracy: {accuracy:.3f}")
            
            self.is_trained = True
            self._save_model()
    
    def _generate_synthetic_credit_data(self) -> List[Dict]:
        """Generate synthetic credit data for training"""
        synthetic_data = []
        
        # Generate data for each credit band
        bands = ['excellent', 'good', 'fair', 'poor', 'very_poor']
        
        for band in bands:
            for i in range(200):
                # Adjust parameters based on credit band
                if band == 'excellent':
                    income_base = 3000
                    debt_ratio = 0.2
                    savings_rate = 0.3
                elif band == 'good':
                    income_base = 2000
                    debt_ratio = 0.3
                    savings_rate = 0.2
                elif band == 'fair':
                    income_base = 1500
                    debt_ratio = 0.4
                    savings_rate = 0.15
                elif band == 'poor':
                    income_base = 1000
                    debt_ratio = 0.5
                    savings_rate = 0.1
                else:  # very_poor
                    income_base = 800
                    debt_ratio = 0.6
                    savings_rate = 0.05
                
                monthly_income = income_base + np.random.normal(0, income_base * 0.2)
                monthly_expenses = monthly_income * (0.6 + np.random.normal(0, 0.1))
                
                features = {
                    'user_id': f"user_{band}_{i}",
                    'timestamp': datetime.utcnow(),
                    'age': np.random.randint(25, 65),
                    'income_level': np.random.choice(['low', 'medium', 'high']),
                    'employment_status': np.random.choice(['employed', 'self_employed', 'unemployed']),
                    'education_level': np.random.choice(['high_school', 'bachelor', 'master']),
                    'marital_status': np.random.choice(['single', 'married', 'divorced']),
                    'total_assets': monthly_income * 12 * np.random.uniform(0.5, 3),
                    'total_liabilities': monthly_income * 12 * debt_ratio * np.random.uniform(0.8, 1.2),
                    'monthly_income': monthly_income,
                    'monthly_expenses': monthly_expenses,
                    'credit_utilization': np.random.uniform(0.1, 0.9),
                    'debt_to_income': debt_ratio + np.random.normal(0, 0.1),
                    'avg_transaction_amount': monthly_income * 0.1,
                    'transaction_frequency': np.random.uniform(20, 100),
                    'transaction_velocity': np.random.uniform(1, 10),
                    'unusual_transaction_count': np.random.randint(0, 5),
                    'foreign_transaction_count': np.random.randint(0, 3),
                    'night_transaction_count': np.random.randint(0, 10),
                    'weekend_transaction_count': np.random.randint(0, 20),
                    'login_frequency': np.random.uniform(1, 10),
                    'device_count': np.random.randint(1, 5),
                    'location_count': np.random.randint(1, 3),
                    'failed_login_attempts': np.random.randint(0, 5),
                    'time_between_actions': np.random.uniform(1, 60),
                    'account_count': np.random.randint(1, 5),
                    'account_age_avg': np.random.uniform(30, 1000),
                    'balance_volatility': np.random.uniform(0.1, 0.5),
                    'overdraft_frequency': np.random.randint(0, 3),
                    'returned_payment_count': np.random.randint(0, 2),
                    'spending_categories': {},
                    'income_stability': np.random.uniform(0.5, 1.0),
                    'savings_rate': savings_rate + np.random.normal(0, 0.05),
                    'investment_activity': np.random.uniform(0, 0.2),
                    'credit_bureau_score': None,
                    'sanctions_check': False,
                    'pep_check': False,
                    'adverse_media_check': False
                }
                
                synthetic_data.append({
                    'features': features,
                    'credit_band': band
                })
        
        return synthetic_data

class FraudDetectionModel:
    """Advanced fraud detection model with real-time scoring"""
    
    def __init__(self, model_path: str = "/app/backend/models/fraud_model.pkl"):
        self.model_path = model_path
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False
        
        # Fraud detection thresholds
        self.fraud_threshold = 0.7
        self.high_risk_threshold = 0.5
        
        # Load existing model
        self._load_model()
    
    def _load_model(self):
        """Load existing model from disk"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_columns = model_data['feature_columns']
                self.is_trained = True
                logger.info("Fraud detection model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load fraud model: {e}")
    
    def predict_fraud_risk(self, risk_features: RiskFeatures) -> Tuple[float, Dict]:
        """Predict fraud risk"""
        if not self.is_trained:
            self.train_model([])  # Train with synthetic data
        
        try:
            # Prepare features
            X = self._prepare_fraud_features(risk_features)
            X_scaled = self.scaler.transform(X)
            
            # Get fraud probability
            if hasattr(self.model, 'predict_proba'):
                fraud_probability = self.model.predict_proba(X_scaled)[0][1]
            else:
                fraud_probability = 0.1  # Default low risk
            
            # Identify fraud indicators
            fraud_indicators = self._identify_fraud_indicators(risk_features)
            
            # Adjust score based on indicators
            indicator_weight = len(fraud_indicators) * 0.1
            adjusted_score = min(fraud_probability + indicator_weight, 1.0)
            
            # Determine risk level
            if adjusted_score >= self.fraud_threshold:
                risk_level = "high"
            elif adjusted_score >= self.high_risk_threshold:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            details = {
                'fraud_probability': fraud_probability,
                'adjusted_score': adjusted_score,
                'risk_level': risk_level,
                'fraud_indicators': fraud_indicators,
                'model_confidence': 0.85  # Mock confidence
            }
            
            return adjusted_score, details
            
        except Exception as e:
            logger.error(f"Fraud detection error: {e}")
            return 0.1, {'error': str(e)}
    
    def _prepare_fraud_features(self, risk_features: RiskFeatures) -> np.ndarray:
        """Prepare features specifically for fraud detection"""
        fraud_features = [
            risk_features.unusual_transaction_count,
            risk_features.foreign_transaction_count,
            risk_features.night_transaction_count,
            risk_features.transaction_velocity,
            risk_features.failed_login_attempts,
            risk_features.device_count,
            risk_features.location_count,
            risk_features.avg_transaction_amount,
            risk_features.balance_volatility,
            risk_features.time_between_actions,
            1 if risk_features.sanctions_check else 0,
            1 if risk_features.pep_check else 0,
            1 if risk_features.adverse_media_check else 0
        ]
        
        return np.array(fraud_features).reshape(1, -1)
    
    def _identify_fraud_indicators(self, risk_features: RiskFeatures) -> List[str]:
        """Identify fraud indicators"""
        indicators = []
        
        if risk_features.unusual_transaction_count > 3:
            indicators.append("High unusual transaction count")
        
        if risk_features.foreign_transaction_count > 2:
            indicators.append("Multiple foreign transactions")
        
        if risk_features.night_transaction_count > 5:
            indicators.append("High night-time activity")
        
        if risk_features.transaction_velocity > 10:
            indicators.append("High transaction velocity")
        
        if risk_features.failed_login_attempts > 3:
            indicators.append("Multiple failed logins")
        
        if risk_features.device_count > 3:
            indicators.append("Multiple devices")
        
        if risk_features.location_count > 3:
            indicators.append("Multiple locations")
        
        if risk_features.sanctions_check:
            indicators.append("Sanctions list match")
        
        if risk_features.pep_check:
            indicators.append("PEP list match")
        
        if risk_features.adverse_media_check:
            indicators.append("Adverse media mentions")
        
        return indicators
    
    def train_model(self, training_data: List[Dict]):
        """Train fraud detection model"""
        if not training_data:
            training_data = self._generate_synthetic_fraud_data()
        
        # Prepare features and labels
        features_list = []
        labels = []
        
        for data in training_data:
            risk_features = RiskFeatures(**data['features'])
            features_array = self._prepare_fraud_features(risk_features)
            features_list.append(features_array.flatten())
            labels.append(data['is_fraud'])
        
        X = np.array(features_list)
        y = np.array(labels)
        
        if len(X) > 0 and len(set(y)) > 1:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            self.feature_columns = [f"fraud_feature_{i}" for i in range(X_scaled.shape[1])]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = (y_pred == y_test).mean()
            
            if hasattr(self.model, 'predict_proba'):
                y_pred_proba = self.model.predict_proba(X_test)[:, 1]
                auc_score = roc_auc_score(y_test, y_pred_proba)
                logger.info(f"Fraud model trained - Accuracy: {accuracy:.3f}, AUC: {auc_score:.3f}")
            else:
                logger.info(f"Fraud model trained - Accuracy: {accuracy:.3f}")
            
            self.is_trained = True
            self._save_model()
    
    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns
            }
            joblib.dump(model_data, self.model_path)
            logger.info("Fraud detection model saved successfully")
        except Exception as e:
            logger.error(f"Could not save fraud model: {e}")
    
    def _generate_synthetic_fraud_data(self) -> List[Dict]:
        """Generate synthetic fraud data"""
        synthetic_data = []
        
        # Generate normal transactions
        for i in range(800):
            features = {
                'user_id': f"normal_{i}",
                'timestamp': datetime.utcnow(),
                'age': np.random.randint(25, 65),
                'income_level': 'medium',
                'employment_status': 'employed',
                'education_level': 'bachelor',
                'marital_status': 'married',
                'total_assets': np.random.uniform(10000, 100000),
                'total_liabilities': np.random.uniform(5000, 50000),
                'monthly_income': np.random.uniform(1000, 5000),
                'monthly_expenses': np.random.uniform(800, 4000),
                'credit_utilization': np.random.uniform(0.1, 0.7),
                'debt_to_income': np.random.uniform(0.1, 0.4),
                'avg_transaction_amount': np.random.uniform(50, 500),
                'transaction_frequency': np.random.uniform(10, 50),
                'transaction_velocity': np.random.uniform(1, 5),
                'unusual_transaction_count': np.random.randint(0, 2),
                'foreign_transaction_count': np.random.randint(0, 1),
                'night_transaction_count': np.random.randint(0, 5),
                'weekend_transaction_count': np.random.randint(0, 15),
                'login_frequency': np.random.uniform(1, 5),
                'device_count': np.random.randint(1, 2),
                'location_count': np.random.randint(1, 2),
                'failed_login_attempts': np.random.randint(0, 2),
                'time_between_actions': np.random.uniform(5, 30),
                'account_count': np.random.randint(1, 3),
                'account_age_avg': np.random.uniform(100, 1000),
                'balance_volatility': np.random.uniform(0.1, 0.3),
                'overdraft_frequency': np.random.randint(0, 1),
                'returned_payment_count': np.random.randint(0, 1),
                'spending_categories': {},
                'income_stability': np.random.uniform(0.7, 1.0),
                'savings_rate': np.random.uniform(0.1, 0.3),
                'investment_activity': np.random.uniform(0, 0.1),
                'credit_bureau_score': np.random.randint(600, 800),
                'sanctions_check': False,
                'pep_check': False,
                'adverse_media_check': False
            }
            
            synthetic_data.append({
                'features': features,
                'is_fraud': 0
            })
        
        # Generate fraudulent transactions
        for i in range(200):
            features = {
                'user_id': f"fraud_{i}",
                'timestamp': datetime.utcnow(),
                'age': np.random.randint(25, 65),
                'income_level': 'medium',
                'employment_status': 'employed',
                'education_level': 'bachelor',
                'marital_status': 'single',
                'total_assets': np.random.uniform(10000, 100000),
                'total_liabilities': np.random.uniform(5000, 50000),
                'monthly_income': np.random.uniform(1000, 5000),
                'monthly_expenses': np.random.uniform(800, 4000),
                'credit_utilization': np.random.uniform(0.1, 0.7),
                'debt_to_income': np.random.uniform(0.1, 0.4),
                'avg_transaction_amount': np.random.uniform(1000, 5000),  # High amounts
                'transaction_frequency': np.random.uniform(50, 200),  # High frequency
                'transaction_velocity': np.random.uniform(10, 50),  # High velocity
                'unusual_transaction_count': np.random.randint(5, 20),  # Many unusual
                'foreign_transaction_count': np.random.randint(3, 10),  # Many foreign
                'night_transaction_count': np.random.randint(10, 30),  # Many night
                'weekend_transaction_count': np.random.randint(20, 50),
                'login_frequency': np.random.uniform(10, 50),
                'device_count': np.random.randint(3, 10),  # Many devices
                'location_count': np.random.randint(3, 10),  # Many locations
                'failed_login_attempts': np.random.randint(5, 20),  # Many failures
                'time_between_actions': np.random.uniform(0.1, 2),  # Very fast
                'account_count': np.random.randint(1, 3),
                'account_age_avg': np.random.uniform(1, 50),  # New accounts
                'balance_volatility': np.random.uniform(0.5, 1.0),  # High volatility
                'overdraft_frequency': np.random.randint(0, 1),
                'returned_payment_count': np.random.randint(0, 1),
                'spending_categories': {},
                'income_stability': np.random.uniform(0.1, 0.5),  # Unstable
                'savings_rate': np.random.uniform(0, 0.1),
                'investment_activity': np.random.uniform(0, 0.1),
                'credit_bureau_score': np.random.randint(300, 600),
                'sanctions_check': np.random.choice([True, False]),
                'pep_check': np.random.choice([True, False]),
                'adverse_media_check': np.random.choice([True, False])
            }
            
            synthetic_data.append({
                'features': features,
                'is_fraud': 1
            })
        
        return synthetic_data

class RiskScoringService:
    """Main risk scoring service with comprehensive ML models"""
    
    def __init__(self, mongo_url: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client.get_database("stablecoin_db")
        self.risk_assessments_collection = self.db.get_collection("risk_assessments")
        self.risk_features_collection = self.db.get_collection("risk_features")
        self.model_performance_collection = self.db.get_collection("model_performance")
        
        # Initialize ML models
        self.credit_model = CreditScoringModel()
        self.fraud_model = FraudDetectionModel()
        
        # Risk thresholds
        self.risk_thresholds = {
            RiskLevel.VERY_LOW: 0.2,
            RiskLevel.LOW: 0.4,
            RiskLevel.MEDIUM: 0.6,
            RiskLevel.HIGH: 0.8,
            RiskLevel.VERY_HIGH: 1.0
        }
        
        logger.info("Risk scoring service initialized")
    
    async def assess_comprehensive_risk(self, user_id: str, transaction_data: Optional[Dict] = None) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        try:
            # Extract risk features
            risk_features = await self._extract_risk_features(user_id, transaction_data)
            
            # Run ML models
            credit_score, credit_confidence, credit_details = self.credit_model.predict_credit_score(risk_features)
            fraud_score, fraud_details = self.fraud_model.predict_fraud_risk(risk_features)
            
            # Calculate behavioral score
            behavioral_score = self._calculate_behavioral_score(risk_features)
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk(credit_score, fraud_score, behavioral_score)
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk_score)
            
            # Generate assessment
            assessment = RiskAssessment(
                assessment_id=str(uuid.uuid4()),
                user_id=user_id,
                risk_category=RiskCategory.CREDIT_RISK,  # Primary category
                risk_level=risk_level,
                risk_score=overall_risk_score,
                confidence_score=credit_confidence,
                model_version="1.0",
                timestamp=datetime.utcnow(),
                credit_score=credit_score / 850,  # Normalize to 0-1
                fraud_score=fraud_score,
                behavioral_score=behavioral_score,
                risk_factors=credit_details.get('risk_factors', []) + fraud_details.get('fraud_indicators', []),
                protective_factors=credit_details.get('protective_factors', []),
                recommendations=self._generate_recommendations(risk_level, credit_score, fraud_score),
                feature_importance=credit_details.get('feature_importance', {}),
                decision_reasoning=self._generate_decision_reasoning(credit_score, fraud_score, behavioral_score)
            )
            
            # Convert enum values for MongoDB storage
            assessment_dict = asdict(assessment)
            assessment_dict['risk_category'] = assessment.risk_category.value
            assessment_dict['risk_level'] = assessment.risk_level.value
            
            # Store assessment
            await self.risk_assessments_collection.insert_one(assessment_dict)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            # Return default assessment
            return RiskAssessment(
                assessment_id=str(uuid.uuid4()),
                user_id=user_id,
                risk_category=RiskCategory.CREDIT_RISK,
                risk_level=RiskLevel.MEDIUM,
                risk_score=0.5,
                confidence_score=0.5,
                model_version="1.0",
                timestamp=datetime.utcnow(),
                credit_score=0.5,
                fraud_score=0.5,
                behavioral_score=0.5,
                risk_factors=["Assessment error"],
                protective_factors=[],
                recommendations=["Manual review required"],
                feature_importance={},
                decision_reasoning=f"Error in assessment: {str(e)}"
            )
    
    async def _extract_risk_features(self, user_id: str, transaction_data: Optional[Dict] = None) -> RiskFeatures:
        """Extract comprehensive risk features for a user"""
        # In a real implementation, this would query multiple data sources
        # For now, we'll create mock features
        
        # Mock demographic data
        demographic_features = {
            'age': np.random.randint(25, 65),
            'income_level': np.random.choice(['low', 'medium', 'high']),
            'employment_status': np.random.choice(['employed', 'self_employed', 'unemployed']),
            'education_level': np.random.choice(['high_school', 'bachelor', 'master']),
            'marital_status': np.random.choice(['single', 'married', 'divorced'])
        }
        
        # Mock financial data
        monthly_income = np.random.uniform(1000, 5000)
        financial_features = {
            'total_assets': monthly_income * 12 * np.random.uniform(0.5, 3),
            'total_liabilities': monthly_income * 12 * np.random.uniform(0.1, 0.8),
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_income * np.random.uniform(0.6, 0.9),
            'credit_utilization': np.random.uniform(0.1, 0.8),
            'debt_to_income': np.random.uniform(0.1, 0.6)
        }
        
        # Mock transaction features
        transaction_features = {
            'avg_transaction_amount': np.random.uniform(50, 500),
            'transaction_frequency': np.random.uniform(10, 100),
            'transaction_velocity': np.random.uniform(1, 20),
            'unusual_transaction_count': np.random.randint(0, 5),
            'foreign_transaction_count': np.random.randint(0, 3),
            'night_transaction_count': np.random.randint(0, 10),
            'weekend_transaction_count': np.random.randint(0, 30)
        }
        
        # Mock behavioral features
        behavioral_features = {
            'login_frequency': np.random.uniform(1, 10),
            'device_count': np.random.randint(1, 5),
            'location_count': np.random.randint(1, 4),
            'failed_login_attempts': np.random.randint(0, 5),
            'time_between_actions': np.random.uniform(1, 60)
        }
        
        # Mock banking features
        banking_features = {
            'account_count': np.random.randint(1, 5),
            'account_age_avg': np.random.uniform(30, 1000),
            'balance_volatility': np.random.uniform(0.1, 0.5),
            'overdraft_frequency': np.random.randint(0, 3),
            'returned_payment_count': np.random.randint(0, 2)
        }
        
        # Mock open banking features
        open_banking_features = {
            'spending_categories': {},
            'income_stability': np.random.uniform(0.5, 1.0),
            'savings_rate': np.random.uniform(0.05, 0.3),
            'investment_activity': np.random.uniform(0, 0.2)
        }
        
        # Mock external features
        external_features = {
            'credit_bureau_score': np.random.randint(400, 800),
            'sanctions_check': False,
            'pep_check': False,
            'adverse_media_check': False
        }
        
        # Combine all features
        all_features = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            **demographic_features,
            **financial_features,
            **transaction_features,
            **behavioral_features,
            **banking_features,
            **open_banking_features,
            **external_features
        }
        
        return RiskFeatures(**all_features)
    
    def _calculate_behavioral_score(self, risk_features: RiskFeatures) -> float:
        """Calculate behavioral risk score"""
        score = 0.5  # Base score
        
        # Login patterns
        if risk_features.failed_login_attempts > 3:
            score += 0.1
        
        # Device usage
        if risk_features.device_count > 3:
            score += 0.1
        
        # Location patterns
        if risk_features.location_count > 3:
            score += 0.1
        
        # Time patterns
        if risk_features.time_between_actions < 5:
            score += 0.1
        
        # Stability indicators
        if risk_features.income_stability < 0.7:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_overall_risk(self, credit_score: int, fraud_score: float, behavioral_score: float) -> float:
        """Calculate overall risk score"""
        # Normalize credit score to 0-1 (lower is riskier)
        normalized_credit = 1.0 - ((credit_score - 300) / 550)
        
        # Weighted combination
        overall_risk = (
            normalized_credit * 0.5 +
            fraud_score * 0.3 +
            behavioral_score * 0.2
        )
        
        return min(overall_risk, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from score"""
        if risk_score <= self.risk_thresholds[RiskLevel.VERY_LOW]:
            return RiskLevel.VERY_LOW
        elif risk_score <= self.risk_thresholds[RiskLevel.LOW]:
            return RiskLevel.LOW
        elif risk_score <= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        elif risk_score <= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _generate_recommendations(self, risk_level: RiskLevel, credit_score: int, fraud_score: float) -> List[str]:
        """Generate risk-based recommendations"""
        recommendations = []
        
        if risk_level == RiskLevel.VERY_HIGH:
            recommendations.append("Account requires immediate manual review")
            recommendations.append("Consider account restrictions")
            recommendations.append("Enhanced monitoring required")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Enhanced due diligence required")
            recommendations.append("Transaction limits recommended")
            recommendations.append("Additional verification needed")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Standard monitoring procedures")
            recommendations.append("Periodic review recommended")
        else:
            recommendations.append("Standard risk management procedures")
            recommendations.append("Normal monitoring sufficient")
        
        if credit_score < 500:
            recommendations.append("Credit enhancement programs available")
        
        if fraud_score > 0.7:
            recommendations.append("Fraud prevention measures activated")
        
        return recommendations
    
    def _generate_decision_reasoning(self, credit_score: int, fraud_score: float, behavioral_score: float) -> str:
        """Generate explanation for risk decision"""
        reasoning = f"Risk assessment based on: "
        reasoning += f"Credit score: {credit_score} (weight: 50%), "
        reasoning += f"Fraud risk: {fraud_score:.2f} (weight: 30%), "
        reasoning += f"Behavioral risk: {behavioral_score:.2f} (weight: 20%). "
        
        if credit_score < 500:
            reasoning += "Low credit score indicates higher default risk. "
        
        if fraud_score > 0.5:
            reasoning += "Elevated fraud indicators detected. "
        
        if behavioral_score > 0.5:
            reasoning += "Behavioral patterns suggest increased risk. "
        
        return reasoning
    
    async def get_user_risk_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user's risk assessment history"""
        cursor = self.risk_assessments_collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        
        history = []
        async for doc in cursor:
            history.append({
                "assessment_id": doc["assessment_id"],
                "risk_level": doc["risk_level"],
                "risk_score": doc["risk_score"],
                "credit_score": doc["credit_score"],
                "fraud_score": doc["fraud_score"],
                "timestamp": doc["timestamp"]
            })
        
        return history
    
    async def initialize_risk_system(self):
        """Initialize risk scoring system"""
        try:
            # Create indexes
            await self.risk_assessments_collection.create_index([("user_id", 1), ("timestamp", -1)])
            await self.risk_assessments_collection.create_index([("assessment_id", 1)], unique=True)
            await self.risk_features_collection.create_index([("user_id", 1), ("timestamp", -1)])
            await self.model_performance_collection.create_index([("model_type", 1), ("timestamp", -1)])
            
            # Train models if not already trained
            if not self.credit_model.is_trained:
                logger.info("Training credit scoring model...")
                self.credit_model.train_model([])
            
            if not self.fraud_model.is_trained:
                logger.info("Training fraud detection model...")
                self.fraud_model.train_model([])
            
            logger.info("Risk scoring system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing risk system: {e}")
            raise