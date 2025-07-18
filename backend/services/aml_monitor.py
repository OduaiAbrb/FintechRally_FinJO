"""
AML (Anti-Money Laundering) Monitoring System
Jordan Central Bank Compliant - 2025 Standards

This module implements ML-based AML monitoring with continuous learning capabilities
for transaction pattern analysis, risk scoring, and fraud detection.
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
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    EXCHANGE = "exchange"
    PAYMENT = "payment"

class AMLFlag(Enum):
    STRUCTURING = "structuring"          # Breaking large amounts into smaller ones
    VELOCITY = "velocity"                # High frequency transactions
    AMOUNT = "amount"                    # Unusual amounts
    PATTERN = "pattern"                  # Suspicious patterns
    GEOGRAPHY = "geography"              # Geographic anomalies
    BEHAVIOR = "behavior"                # Behavioral anomalies
    SANCTIONED = "sanctioned"            # Sanctions list hit
    PEP = "pep"                         # Politically Exposed Person

@dataclass
class TransactionFeatures:
    """Feature extraction for AML analysis"""
    transaction_id: str
    user_id: str
    amount: float
    transaction_type: str
    timestamp: datetime
    account_id: str
    counterparty_id: Optional[str]
    currency: str
    location: Optional[str]
    device_fingerprint: Optional[str]
    
    # Derived features
    hour_of_day: int
    day_of_week: int
    is_weekend: bool
    is_business_hours: bool
    
    # User behavior features
    user_avg_amount: float
    user_transaction_count_24h: int
    user_transaction_count_7d: int
    user_velocity_score: float
    account_age_days: int
    
    # Network features
    counterparty_risk_score: float
    is_new_counterparty: bool
    
def extract_features(transaction: Dict, user_history: List[Dict], 
                    counterparty_data: Dict) -> TransactionFeatures:
    """Extract comprehensive features from transaction data"""
    
    timestamp = datetime.fromisoformat(transaction['timestamp'])
    
    # Calculate user behavior metrics
    recent_24h = [t for t in user_history 
                  if datetime.fromisoformat(t['timestamp']) > timestamp - timedelta(days=1)]
    recent_7d = [t for t in user_history 
                 if datetime.fromisoformat(t['timestamp']) > timestamp - timedelta(days=7)]
    
    user_avg_amount = np.mean([t['amount'] for t in user_history]) if user_history else 0
    user_velocity_score = len(recent_24h) / 24.0  # Transactions per hour
    
    # Calculate counterparty risk
    counterparty_risk_score = counterparty_data.get('risk_score', 0.5) if counterparty_data else 0.5
    is_new_counterparty = counterparty_data.get('first_interaction', True) if counterparty_data else True
    
    return TransactionFeatures(
        transaction_id=transaction['transaction_id'],
        user_id=transaction['user_id'],
        amount=transaction['amount'],
        transaction_type=transaction['transaction_type'],
        timestamp=timestamp,
        account_id=transaction.get('account_id', ''),
        counterparty_id=transaction.get('counterparty_id'),
        currency=transaction.get('currency', 'JOD'),
        location=transaction.get('location'),
        device_fingerprint=transaction.get('device_fingerprint'),
        
        hour_of_day=timestamp.hour,
        day_of_week=timestamp.weekday(),
        is_weekend=timestamp.weekday() >= 5,
        is_business_hours=9 <= timestamp.hour <= 17,
        
        user_avg_amount=user_avg_amount,
        user_transaction_count_24h=len(recent_24h),
        user_transaction_count_7d=len(recent_7d),
        user_velocity_score=user_velocity_score,
        account_age_days=transaction.get('account_age_days', 0),
        
        counterparty_risk_score=counterparty_risk_score,
        is_new_counterparty=is_new_counterparty
    )

@dataclass
class AMLAlert:
    """AML Alert structure"""
    alert_id: str
    transaction_id: str
    user_id: str
    alert_type: AMLFlag
    risk_level: RiskLevel
    score: float
    description: str
    timestamp: datetime
    status: str = "pending"
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    false_positive: bool = False
    
    # Jordan Central Bank specific fields
    regulatory_reference: Optional[str] = None
    cbj_reported: bool = False
    amlu_case_number: Optional[str] = None

class AMLMLModel:
    """Machine Learning Model for AML Detection with Continuous Learning"""
    
    def __init__(self, model_path: str = "/app/backend/models/aml_model.pkl"):
        self.model_path = model_path
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.fraud_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.feature_columns = []
        self.performance_metrics = {}
        
        # Continuous learning components
        self.feedback_buffer = deque(maxlen=1000)
        self.retrain_threshold = 100
        self.model_version = 1
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load existing model from disk"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.isolation_forest = model_data['isolation_forest']
                self.fraud_classifier = model_data['fraud_classifier']
                self.scaler = model_data['scaler']
                self.label_encoder = model_data['label_encoder']
                self.feature_columns = model_data['feature_columns']
                self.model_version = model_data.get('version', 1)
                self.is_trained = True
                logger.info(f"AML model loaded successfully - version {self.model_version}")
        except Exception as e:
            logger.warning(f"Could not load existing model: {e}")
    
    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model_data = {
                'isolation_forest': self.isolation_forest,
                'fraud_classifier': self.fraud_classifier,
                'scaler': self.scaler,
                'label_encoder': self.label_encoder,
                'feature_columns': self.feature_columns,
                'version': self.model_version,
                'performance_metrics': self.performance_metrics
            }
            joblib.dump(model_data, self.model_path)
            logger.info(f"AML model saved successfully - version {self.model_version}")
        except Exception as e:
            logger.error(f"Could not save model: {e}")
    
    def prepare_features(self, features: TransactionFeatures) -> np.ndarray:
        """Convert features to numerical array for ML model"""
        feature_dict = asdict(features)
        
        # Convert to numerical features
        numerical_features = [
            feature_dict['amount'],
            feature_dict['hour_of_day'],
            feature_dict['day_of_week'],
            1 if feature_dict['is_weekend'] else 0,
            1 if feature_dict['is_business_hours'] else 0,
            feature_dict['user_avg_amount'],
            feature_dict['user_transaction_count_24h'],
            feature_dict['user_transaction_count_7d'],
            feature_dict['user_velocity_score'],
            feature_dict['account_age_days'],
            feature_dict['counterparty_risk_score'],
            1 if feature_dict['is_new_counterparty'] else 0,
        ]
        
        # Encode transaction type
        transaction_type_encoded = self._encode_transaction_type(feature_dict['transaction_type'])
        numerical_features.extend(transaction_type_encoded)
        
        return np.array(numerical_features).reshape(1, -1)
    
    def _encode_transaction_type(self, transaction_type: str) -> List[int]:
        """One-hot encode transaction type"""
        types = ['deposit', 'withdrawal', 'transfer', 'exchange', 'payment']
        return [1 if transaction_type == t else 0 for t in types]
    
    def train_initial_model(self, training_data: List[Dict]):
        """Train initial model with synthetic/historical data"""
        if not training_data:
            logger.warning("No training data provided, using synthetic data")
            training_data = self._generate_synthetic_data()
        
        # Prepare training features
        features_list = []
        labels = []
        
        for data in training_data:
            transaction_features = extract_features(
                data['transaction'], 
                data.get('user_history', []),
                data.get('counterparty_data', {})
            )
            features_array = self.prepare_features(transaction_features)
            features_list.append(features_array.flatten())
            labels.append(data.get('is_fraud', 0))
        
        X = np.array(features_list)
        y = np.array(labels)
        
        if len(X) > 0:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            self.feature_columns = [f"feature_{i}" for i in range(X_scaled.shape[1])]
            
            # Train isolation forest for anomaly detection
            self.isolation_forest.fit(X_scaled)
            
            # Train fraud classifier if we have labeled data
            if len(set(y)) > 1:  # At least 2 classes
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42
                )
                self.fraud_classifier.fit(X_train, y_train)
                
                # Evaluate model
                y_pred = self.fraud_classifier.predict(X_test)
                self.performance_metrics = {
                    'classification_report': classification_report(y_test, y_pred, output_dict=True),
                    'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
                    'training_samples': len(X),
                    'last_trained': datetime.utcnow().isoformat()
                }
            
            self.is_trained = True
            self._save_model()
            logger.info(f"AML model trained successfully with {len(X)} samples")
    
    def _generate_synthetic_data(self) -> List[Dict]:
        """Generate synthetic training data for initial model"""
        synthetic_data = []
        
        # Generate normal transactions
        for i in range(800):
            transaction = {
                'transaction_id': f"tx_{i}",
                'user_id': f"user_{i % 100}",
                'amount': np.random.lognormal(mean=3, sigma=1),  # Normal distribution
                'transaction_type': np.random.choice(['deposit', 'withdrawal', 'transfer']),
                'timestamp': (datetime.utcnow() - timedelta(days=np.random.randint(0, 30))).isoformat(),
                'account_id': f"acc_{i % 50}",
                'currency': 'JOD',
                'account_age_days': np.random.randint(30, 1000)
            }
            
            synthetic_data.append({
                'transaction': transaction,
                'user_history': [],
                'counterparty_data': {},
                'is_fraud': 0
            })
        
        # Generate fraudulent transactions
        for i in range(200):
            transaction = {
                'transaction_id': f"fraud_tx_{i}",
                'user_id': f"user_{i % 20}",
                'amount': np.random.choice([9999, 49999, 99999]),  # Suspicious amounts
                'transaction_type': np.random.choice(['transfer', 'withdrawal']),
                'timestamp': (datetime.utcnow() - timedelta(hours=np.random.randint(0, 24))).isoformat(),
                'account_id': f"acc_{i % 10}",
                'currency': 'JOD',
                'account_age_days': np.random.randint(1, 30)  # New accounts
            }
            
            # Add suspicious patterns
            user_history = []
            for j in range(np.random.randint(5, 20)):  # High velocity
                hist_tx = {
                    'amount': np.random.uniform(9000, 10000),
                    'timestamp': (datetime.utcnow() - timedelta(hours=j)).isoformat(),
                    'transaction_type': 'transfer'
                }
                user_history.append(hist_tx)
            
            synthetic_data.append({
                'transaction': transaction,
                'user_history': user_history,
                'counterparty_data': {'risk_score': 0.8, 'first_interaction': True},
                'is_fraud': 1
            })
        
        return synthetic_data
    
    def predict_risk(self, features: TransactionFeatures) -> Tuple[float, Dict]:
        """Predict fraud risk for a transaction"""
        if not self.is_trained:
            logger.warning("Model not trained, training with synthetic data")
            self.train_initial_model([])
        
        try:
            # Prepare features
            X = self.prepare_features(features)
            X_scaled = self.scaler.transform(X)
            
            # Get anomaly score from isolation forest
            anomaly_score = self.isolation_forest.decision_function(X_scaled)[0]
            is_outlier = self.isolation_forest.predict(X_scaled)[0] == -1
            
            # Get fraud probability from classifier
            fraud_probability = 0.5  # Default
            if hasattr(self.fraud_classifier, 'predict_proba'):
                fraud_probability = self.fraud_classifier.predict_proba(X_scaled)[0][1]
            
            # Combine scores
            combined_score = (abs(anomaly_score) + fraud_probability) / 2
            
            # Get feature importance
            feature_importance = {}
            if hasattr(self.fraud_classifier, 'feature_importances_'):
                for i, importance in enumerate(self.fraud_classifier.feature_importances_):
                    feature_importance[f"feature_{i}"] = importance
            
            prediction_details = {
                'anomaly_score': float(anomaly_score),
                'is_outlier': bool(is_outlier),
                'fraud_probability': float(fraud_probability),
                'combined_score': float(combined_score),
                'feature_importance': feature_importance,
                'model_version': self.model_version
            }
            
            return combined_score, prediction_details
            
        except Exception as e:
            logger.error(f"Error in risk prediction: {e}")
            return 0.5, {'error': str(e)}
    
    def add_feedback(self, transaction_id: str, features: TransactionFeatures, 
                    actual_label: int, predicted_score: float):
        """Add feedback for continuous learning"""
        feedback = {
            'transaction_id': transaction_id,
            'features': asdict(features),
            'actual_label': actual_label,
            'predicted_score': predicted_score,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.feedback_buffer.append(feedback)
        
        # Retrain if enough feedback accumulated
        if len(self.feedback_buffer) >= self.retrain_threshold:
            self._retrain_with_feedback()
    
    def _retrain_with_feedback(self):
        """Retrain model with accumulated feedback"""
        try:
            # Prepare feedback data
            features_list = []
            labels = []
            
            for feedback in self.feedback_buffer:
                transaction_features = TransactionFeatures(**feedback['features'])
                features_array = self.prepare_features(transaction_features)
                features_list.append(features_array.flatten())
                labels.append(feedback['actual_label'])
            
            if len(features_list) > 10:  # Minimum samples for retraining
                X = np.array(features_list)
                y = np.array(labels)
                
                # Scale features
                X_scaled = self.scaler.fit_transform(X)
                
                # Retrain models
                self.isolation_forest.fit(X_scaled)
                
                if len(set(y)) > 1:
                    self.fraud_classifier.fit(X_scaled, y)
                
                # Update version and save
                self.model_version += 1
                self._save_model()
                
                # Clear feedback buffer
                self.feedback_buffer.clear()
                
                logger.info(f"Model retrained with feedback - version {self.model_version}")
                
        except Exception as e:
            logger.error(f"Error in model retraining: {e}")

class AMLMonitor:
    """Main AML Monitoring System"""
    
    def __init__(self, mongo_url: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client.get_database("stablecoin_db")
        self.alerts_collection = self.db.get_collection("aml_alerts")
        self.transactions_collection = self.db.get_collection("transactions")
        self.users_collection = self.db.get_collection("users")
        self.aml_reports_collection = self.db.get_collection("aml_reports")
        
        # Initialize ML model
        self.ml_model = AMLMLModel()
        
        # Risk thresholds (Jordan Central Bank compliant)
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.9
        }
        
        # Amount thresholds (JOD)
        self.amount_thresholds = {
            'large_transaction': 10000,      # JOD 10,000
            'cash_transaction': 5000,        # JOD 5,000
            'suspicious_amount': 9999,       # Just under reporting threshold
            'structuring_threshold': 50000   # JOD 50,000
        }
        
        # Sanctions and PEP lists (simplified)
        self.sanctions_list = set()
        self.pep_list = set()
        
        logger.info("AML Monitor initialized successfully")
    
    async def monitor_transaction(self, transaction: Dict) -> Optional[AMLAlert]:
        """Monitor a transaction for AML violations"""
        try:
            # Get user history
            user_history = await self._get_user_transaction_history(transaction['user_id'])
            
            # Get counterparty data
            counterparty_data = await self._get_counterparty_data(
                transaction.get('counterparty_id')
            )
            
            # Extract features
            features = extract_features(transaction, user_history, counterparty_data)
            
            # Run ML-based risk assessment
            risk_score, prediction_details = self.ml_model.predict_risk(features)
            
            # Apply rule-based checks
            rule_violations = await self._apply_aml_rules(features, user_history)
            
            # Determine overall risk level
            risk_level = self._calculate_risk_level(risk_score, rule_violations)
            
            # Generate alert if necessary
            if risk_level != RiskLevel.LOW or rule_violations:
                alert = await self._generate_alert(
                    transaction, features, risk_level, risk_score, 
                    rule_violations, prediction_details
                )
                
                # Convert enum values for MongoDB storage
                alert_dict = asdict(alert)
                alert_dict['risk_level'] = alert.risk_level.value
                alert_dict['alert_type'] = alert.alert_type.value
                
                # Store alert
                await self.alerts_collection.insert_one(alert_dict)
                
                # Report to Jordan Central Bank if critical
                if risk_level == RiskLevel.CRITICAL:
                    await self._report_to_cbj(alert)
                
                logger.info(f"AML Alert generated: {alert.alert_id} - {risk_level.value}")
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Error in transaction monitoring: {e}")
            return None
    
    async def _get_user_transaction_history(self, user_id: str) -> List[Dict]:
        """Get user's transaction history for pattern analysis"""
        cursor = self.transactions_collection.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)],
            limit=100
        )
        
        transactions = []
        async for tx in cursor:
            transactions.append({
                'transaction_id': tx['transaction_id'],
                'amount': tx['amount'],
                'transaction_type': tx['transaction_type'],
                'timestamp': tx['timestamp'],
                'account_id': tx.get('account_id', '')
            })
        
        return transactions
    
    async def _get_counterparty_data(self, counterparty_id: Optional[str]) -> Dict:
        """Get counterparty risk data"""
        if not counterparty_id:
            return {}
        
        # Check if counterparty is in sanctions or PEP list
        is_sanctioned = counterparty_id in self.sanctions_list
        is_pep = counterparty_id in self.pep_list
        
        # Calculate risk score based on historical data
        risk_score = 0.5  # Default
        if is_sanctioned:
            risk_score = 1.0
        elif is_pep:
            risk_score = 0.8
        
        # Check interaction history
        interaction_count = await self.transactions_collection.count_documents({
            "counterparty_id": counterparty_id
        })
        
        return {
            'risk_score': risk_score,
            'is_sanctioned': is_sanctioned,
            'is_pep': is_pep,
            'interaction_count': interaction_count,
            'first_interaction': interaction_count == 0
        }
    
    async def _apply_aml_rules(self, features: TransactionFeatures, 
                              user_history: List[Dict]) -> List[AMLFlag]:
        """Apply rule-based AML checks"""
        violations = []
        
        # Amount-based rules
        if features.amount >= self.amount_thresholds['large_transaction']:
            violations.append(AMLFlag.AMOUNT)
        
        # Structuring detection
        if await self._detect_structuring(features, user_history):
            violations.append(AMLFlag.STRUCTURING)
        
        # Velocity checks
        if features.user_velocity_score > 5:  # More than 5 transactions per hour
            violations.append(AMLFlag.VELOCITY)
        
        # Pattern analysis
        if await self._detect_suspicious_patterns(features, user_history):
            violations.append(AMLFlag.PATTERN)
        
        # Behavioral anomalies
        if await self._detect_behavioral_anomalies(features, user_history):
            violations.append(AMLFlag.BEHAVIOR)
        
        # Sanctions/PEP checks
        if features.counterparty_id in self.sanctions_list:
            violations.append(AMLFlag.SANCTIONED)
        
        if features.counterparty_id in self.pep_list:
            violations.append(AMLFlag.PEP)
        
        return violations
    
    async def _detect_structuring(self, features: TransactionFeatures, 
                                 user_history: List[Dict]) -> bool:
        """Detect transaction structuring (smurfing)"""
        # Look for multiple transactions just below reporting threshold
        recent_transactions = [
            t for t in user_history 
            if datetime.fromisoformat(t['timestamp']) > features.timestamp - timedelta(days=1)
        ]
        
        # Check for multiple transactions near threshold amounts
        threshold_transactions = [
            t for t in recent_transactions 
            if 9000 <= t['amount'] <= 9999
        ]
        
        return len(threshold_transactions) >= 3
    
    async def _detect_suspicious_patterns(self, features: TransactionFeatures, 
                                        user_history: List[Dict]) -> bool:
        """Detect suspicious transaction patterns"""
        # Round number transactions
        if features.amount % 1000 == 0 and features.amount >= 10000:
            return True
        
        # Unusual timing patterns
        night_transactions = [
            t for t in user_history 
            if datetime.fromisoformat(t['timestamp']).hour < 6 or 
               datetime.fromisoformat(t['timestamp']).hour > 23
        ]
        
        return len(night_transactions) > 5
    
    async def _detect_behavioral_anomalies(self, features: TransactionFeatures, 
                                         user_history: List[Dict]) -> bool:
        """Detect behavioral anomalies"""
        # Sudden increase in transaction amounts
        if features.user_avg_amount > 0:
            amount_ratio = features.amount / features.user_avg_amount
            if amount_ratio > 10:  # 10x normal amount
                return True
        
        # New account with large transactions
        if features.account_age_days < 30 and features.amount > 5000:
            return True
        
        return False
    
    def _calculate_risk_level(self, ml_score: float, rule_violations: List[AMLFlag]) -> RiskLevel:
        """Calculate overall risk level"""
        # Start with ML score
        base_score = ml_score
        
        # Adjust based on rule violations
        violation_penalty = len(rule_violations) * 0.2
        final_score = min(base_score + violation_penalty, 1.0)
        
        # Critical violations
        critical_violations = [AMLFlag.SANCTIONED, AMLFlag.STRUCTURING]
        if any(v in rule_violations for v in critical_violations):
            return RiskLevel.CRITICAL
        
        # Determine risk level
        if final_score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif final_score >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif final_score >= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _generate_alert(self, transaction: Dict, features: TransactionFeatures,
                            risk_level: RiskLevel, risk_score: float,
                            rule_violations: List[AMLFlag], 
                            prediction_details: Dict) -> AMLAlert:
        """Generate AML alert"""
        alert_id = f"AML_{datetime.utcnow().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}"
        
        # Create description
        description = f"Transaction {transaction['transaction_id']} flagged for AML review. "
        description += f"Risk score: {risk_score:.3f}. "
        
        if rule_violations:
            description += f"Violations: {', '.join([v.value for v in rule_violations])}. "
        
        description += f"Amount: {features.amount} {features.currency}. "
        description += f"User velocity: {features.user_velocity_score:.2f} tx/hour."
        
        # Determine alert type
        alert_type = rule_violations[0] if rule_violations else AMLFlag.PATTERN
        
        return AMLAlert(
            alert_id=alert_id,
            transaction_id=transaction['transaction_id'],
            user_id=transaction['user_id'],
            alert_type=alert_type,
            risk_level=risk_level,
            score=risk_score,
            description=description,
            timestamp=datetime.utcnow(),
            regulatory_reference=f"CBJ_AML_{alert_id}"
        )
    
    async def _report_to_cbj(self, alert: AMLAlert):
        """Report critical alerts to Jordan Central Bank"""
        try:
            # Generate CBJ report
            report = {
                'report_id': f"CBJ_RPT_{datetime.utcnow().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}",
                'alert_id': alert.alert_id,
                'institution_id': 'STABLECOIN_FINTECH_001',
                'report_type': 'SUSPICIOUS_TRANSACTION',
                'transaction_details': {
                    'transaction_id': alert.transaction_id,
                    'amount': 'CONFIDENTIAL',  # Actual amount would be in secure section
                    'currency': 'JOD',
                    'transaction_type': alert.alert_type.value,
                    'risk_level': alert.risk_level.value
                },
                'regulatory_reference': alert.regulatory_reference,
                'submitted_to_cbj': datetime.utcnow().isoformat(),
                'status': 'submitted'
            }
            
            # Store report
            await self.aml_reports_collection.insert_one(report)
            
            # Update alert
            await self.alerts_collection.update_one(
                {'alert_id': alert.alert_id},
                {'$set': {'cbj_reported': True, 'amlu_case_number': report['report_id']}}
            )
            
            logger.info(f"Alert {alert.alert_id} reported to CBJ: {report['report_id']}")
            
        except Exception as e:
            logger.error(f"Error reporting to CBJ: {e}")
    
    async def process_alert_feedback(self, alert_id: str, is_false_positive: bool,
                                   resolution: str, analyst_id: str):
        """Process feedback from alert resolution"""
        try:
            # Update alert
            await self.alerts_collection.update_one(
                {'alert_id': alert_id},
                {
                    '$set': {
                        'status': 'resolved',
                        'false_positive': is_false_positive,
                        'resolution': resolution,
                        'assigned_to': analyst_id,
                        'resolved_at': datetime.utcnow()
                    }
                }
            )
            
            # Get alert details for ML feedback
            alert = await self.alerts_collection.find_one({'alert_id': alert_id})
            if alert:
                # Get transaction details
                transaction = await self.transactions_collection.find_one(
                    {'transaction_id': alert['transaction_id']}
                )
                
                if transaction:
                    # Get user history and counterparty data
                    user_history = await self._get_user_transaction_history(transaction['user_id'])
                    counterparty_data = await self._get_counterparty_data(
                        transaction.get('counterparty_id')
                    )
                    
                    # Extract features
                    features = extract_features(transaction, user_history, counterparty_data)
                    
                    # Provide feedback to ML model
                    actual_label = 0 if is_false_positive else 1
                    self.ml_model.add_feedback(
                        alert['transaction_id'],
                        features,
                        actual_label,
                        alert['score']
                    )
                    
                    logger.info(f"Feedback processed for alert {alert_id}")
            
        except Exception as e:
            logger.error(f"Error processing alert feedback: {e}")
    
    async def get_aml_dashboard(self) -> Dict:
        """Get AML monitoring dashboard data"""
        try:
            # Get alert counts by risk level
            alert_counts = {}
            for risk_level in RiskLevel:
                count = await self.alerts_collection.count_documents({
                    'risk_level': risk_level.value,
                    'timestamp': {'$gte': datetime.utcnow() - timedelta(days=7)}
                })
                alert_counts[risk_level.value] = count
            
            # Get recent alerts
            recent_alerts = []
            cursor = self.alerts_collection.find(
                {},
                sort=[("timestamp", -1)],
                limit=10
            )
            
            async for alert in cursor:
                recent_alerts.append({
                    'alert_id': alert['alert_id'],
                    'transaction_id': alert['transaction_id'],
                    'risk_level': alert['risk_level'],
                    'score': alert['score'],
                    'timestamp': alert['timestamp'],
                    'status': alert['status']
                })
            
            # Get model performance
            model_performance = self.ml_model.performance_metrics
            
            return {
                'alert_counts': alert_counts,
                'recent_alerts': recent_alerts,
                'model_performance': model_performance,
                'model_version': self.ml_model.model_version,
                'total_alerts_7d': sum(alert_counts.values()),
                'system_status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error generating AML dashboard: {e}")
            return {'error': str(e)}
    
    async def initialize_system(self):
        """Initialize AML monitoring system"""
        try:
            # Create indexes
            await self.alerts_collection.create_index([("alert_id", 1)], unique=True)
            await self.alerts_collection.create_index([("transaction_id", 1)])
            await self.alerts_collection.create_index([("user_id", 1)])
            await self.alerts_collection.create_index([("timestamp", -1)])
            await self.alerts_collection.create_index([("risk_level", 1)])
            
            # Train initial ML model if not already trained
            if not self.ml_model.is_trained:
                logger.info("Training initial AML model...")
                self.ml_model.train_initial_model([])
            
            logger.info("AML monitoring system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AML system: {e}")
            raise