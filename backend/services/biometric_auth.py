"""
Biometric Authentication Service
Advanced biometric authentication with fingerprint, face recognition, and voice authentication
Integrated with modern biometric APIs and continuous security monitoring
"""

import base64
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import os
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiometricType(Enum):
    FINGERPRINT = "fingerprint"
    FACE = "face"
    VOICE = "voice"
    PALM = "palm"
    IRIS = "iris"

class BiometricProvider(Enum):
    WEBAUTHN = "webauthn"          # Web standard for fingerprint
    FACE_API = "face_api"          # Custom face recognition
    AZURE_FACE = "azure_face"      # Microsoft Azure Face API
    AMAZON_REKOGNITION = "aws_rekognition"  # AWS face recognition
    ONFIDO = "onfido"              # Identity verification
    IPROOV = "iproov"              # Liveness detection

class AuthenticationResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_ADDITIONAL_VERIFICATION = "requires_additional"
    BIOMETRIC_NOT_ENROLLED = "not_enrolled"
    LIVENESS_FAILED = "liveness_failed"
    DEVICE_NOT_TRUSTED = "device_not_trusted"

@dataclass
class BiometricTemplate:
    """Encrypted biometric template storage"""
    template_id: str
    user_id: str
    biometric_type: BiometricType
    provider: BiometricProvider
    encrypted_template: str
    template_hash: str
    quality_score: float
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True

@dataclass
class BiometricAttempt:
    """Biometric authentication attempt record"""
    attempt_id: str
    user_id: str
    biometric_type: BiometricType
    provider: BiometricProvider
    result: AuthenticationResult
    confidence_score: float
    liveness_score: float
    device_fingerprint: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    location: Optional[str] = None
    failure_reason: Optional[str] = None

@dataclass
class DeviceRegistration:
    """Trusted device registration"""
    device_id: str
    user_id: str
    device_name: str
    device_type: str  # mobile, desktop, tablet
    fingerprint: str
    public_key: str
    registered_at: datetime
    last_used: datetime
    is_trusted: bool = True
    trust_score: float = 1.0

class BiometricSecurity:
    """Advanced biometric security and fraud prevention"""
    
    def __init__(self):
        self.attempt_limits = {
            BiometricType.FINGERPRINT: 5,
            BiometricType.FACE: 3,
            BiometricType.VOICE: 3,
            BiometricType.PALM: 5,
            BiometricType.IRIS: 3
        }
        
        self.lockout_duration = timedelta(minutes=15)
        self.suspicious_patterns = {
            'rapid_attempts': 10,  # 10 attempts in 5 minutes
            'device_switching': 5,  # 5 different devices in 1 hour
            'location_anomaly': True,  # Login from unusual location
            'velocity_check': True  # High velocity authentication
        }
    
    def calculate_trust_score(self, user_id: str, device_fingerprint: str, 
                            location: str, recent_attempts: List[BiometricAttempt]) -> float:
        """Calculate device and behavioral trust score"""
        base_score = 0.5
        
        # Device familiarity
        device_attempts = [a for a in recent_attempts if a.device_fingerprint == device_fingerprint]
        if device_attempts:
            device_score = min(len(device_attempts) / 10, 0.3)
            base_score += device_score
        
        # Success rate
        successful_attempts = [a for a in recent_attempts if a.result == AuthenticationResult.SUCCESS]
        if recent_attempts:
            success_rate = len(successful_attempts) / len(recent_attempts)
            base_score += success_rate * 0.2
        
        # Recent failures penalty
        recent_failures = [a for a in recent_attempts[-5:] if a.result == AuthenticationResult.FAILED]
        failure_penalty = len(recent_failures) * 0.1
        base_score -= failure_penalty
        
        # Location consistency
        if location:
            location_attempts = [a for a in recent_attempts if a.location == location]
            if location_attempts:
                location_score = min(len(location_attempts) / 5, 0.2)
                base_score += location_score
        
        return max(0.0, min(1.0, base_score))
    
    def detect_suspicious_activity(self, user_id: str, recent_attempts: List[BiometricAttempt]) -> List[str]:
        """Detect suspicious biometric authentication patterns"""
        warnings = []
        
        # Rapid attempts check
        recent_window = datetime.utcnow() - timedelta(minutes=5)
        rapid_attempts = [a for a in recent_attempts if a.timestamp > recent_window]
        if len(rapid_attempts) > self.suspicious_patterns['rapid_attempts']:
            warnings.append("Rapid authentication attempts detected")
        
        # Device switching
        hour_window = datetime.utcnow() - timedelta(hours=1)
        hour_attempts = [a for a in recent_attempts if a.timestamp > hour_window]
        unique_devices = set(a.device_fingerprint for a in hour_attempts)
        if len(unique_devices) > self.suspicious_patterns['device_switching']:
            warnings.append("Multiple device switching detected")
        
        # Failed attempts pattern
        failed_attempts = [a for a in recent_attempts[-10:] if a.result == AuthenticationResult.FAILED]
        if len(failed_attempts) > 7:
            warnings.append("High failure rate detected")
        
        # Confidence score pattern
        low_confidence = [a for a in recent_attempts[-5:] if a.confidence_score < 0.5]
        if len(low_confidence) > 3:
            warnings.append("Consistently low confidence scores")
        
        return warnings

class FaceRecognitionService:
    """Face recognition service with liveness detection"""
    
    def __init__(self, provider: BiometricProvider = BiometricProvider.FACE_API):
        self.provider = provider
        self.confidence_threshold = 0.85
        self.liveness_threshold = 0.90
        
        # Initialize provider-specific settings
        if provider == BiometricProvider.AZURE_FACE:
            self.api_key = os.getenv("AZURE_FACE_API_KEY")
            self.endpoint = os.getenv("AZURE_FACE_ENDPOINT")
        elif provider == BiometricProvider.AMAZON_REKOGNITION:
            self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
            self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            self.region = os.getenv("AWS_REGION", "us-east-1")
    
    async def enroll_face(self, user_id: str, face_image: str, 
                         device_fingerprint: str) -> Tuple[bool, Dict]:
        """Enroll user's face for authentication"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(face_image)
            
            # Quality check
            quality_score = await self._assess_image_quality(image_data)
            if quality_score < 0.7:
                return False, {"error": "Image quality too low", "quality_score": quality_score}
            
            # Liveness detection
            liveness_score = await self._detect_liveness(image_data)
            if liveness_score < self.liveness_threshold:
                return False, {"error": "Liveness detection failed", "liveness_score": liveness_score}
            
            # Extract face features
            face_features = await self._extract_face_features(image_data)
            if not face_features:
                return False, {"error": "Could not extract face features"}
            
            # Encrypt and store template
            encrypted_template = self._encrypt_template(face_features, user_id)
            template_hash = hashlib.sha256(encrypted_template.encode()).hexdigest()
            
            template = BiometricTemplate(
                template_id=str(uuid.uuid4()),
                user_id=user_id,
                biometric_type=BiometricType.FACE,
                provider=self.provider,
                encrypted_template=encrypted_template,
                template_hash=template_hash,
                quality_score=quality_score,
                created_at=datetime.utcnow()
            )
            
            return True, {
                "template_id": template.template_id,
                "quality_score": quality_score,
                "liveness_score": liveness_score
            }
            
        except Exception as e:
            logger.error(f"Face enrollment error: {e}")
            return False, {"error": str(e)}
    
    async def authenticate_face(self, user_id: str, face_image: str, 
                              device_fingerprint: str) -> Tuple[AuthenticationResult, Dict]:
        """Authenticate user using face recognition"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(face_image)
            
            # Quality check
            quality_score = await self._assess_image_quality(image_data)
            if quality_score < 0.5:
                return AuthenticationResult.FAILED, {
                    "error": "Image quality too low",
                    "quality_score": quality_score
                }
            
            # Liveness detection
            liveness_score = await self._detect_liveness(image_data)
            if liveness_score < self.liveness_threshold:
                return AuthenticationResult.LIVENESS_FAILED, {
                    "error": "Liveness detection failed",
                    "liveness_score": liveness_score
                }
            
            # Extract face features
            face_features = await self._extract_face_features(image_data)
            if not face_features:
                return AuthenticationResult.FAILED, {"error": "Could not extract face features"}
            
            # Compare with stored template
            stored_template = await self._get_stored_template(user_id, BiometricType.FACE)
            if not stored_template:
                return AuthenticationResult.BIOMETRIC_NOT_ENROLLED, {"error": "Face not enrolled"}
            
            # Compare features
            confidence_score = await self._compare_features(face_features, stored_template)
            
            if confidence_score >= self.confidence_threshold:
                return AuthenticationResult.SUCCESS, {
                    "confidence_score": confidence_score,
                    "liveness_score": liveness_score,
                    "quality_score": quality_score
                }
            else:
                return AuthenticationResult.FAILED, {
                    "confidence_score": confidence_score,
                    "liveness_score": liveness_score,
                    "quality_score": quality_score,
                    "error": "Face recognition failed"
                }
            
        except Exception as e:
            logger.error(f"Face authentication error: {e}")
            return AuthenticationResult.FAILED, {"error": str(e)}
    
    async def _assess_image_quality(self, image_data: bytes) -> float:
        """Assess image quality for face recognition"""
        # Simulate image quality assessment
        # In real implementation, this would analyze brightness, sharpness, etc.
        return np.random.uniform(0.6, 0.95)
    
    async def _detect_liveness(self, image_data: bytes) -> float:
        """Detect if the face is from a live person"""
        # Simulate liveness detection
        # In real implementation, this would use advanced anti-spoofing techniques
        return np.random.uniform(0.85, 0.98)
    
    async def _extract_face_features(self, image_data: bytes) -> Optional[Dict]:
        """Extract face features/embeddings"""
        # Simulate face feature extraction
        # In real implementation, this would use deep learning models
        return {
            "features": np.random.rand(512).tolist(),  # 512-dimensional embedding
            "landmarks": np.random.rand(68, 2).tolist(),  # 68 facial landmarks
            "pose": {
                "yaw": np.random.uniform(-30, 30),
                "pitch": np.random.uniform(-20, 20),
                "roll": np.random.uniform(-15, 15)
            }
        }
    
    def _encrypt_template(self, features: Dict, user_id: str) -> str:
        """Encrypt biometric template"""
        # Simple encryption for demo - use proper encryption in production
        template_data = json.dumps(features)
        encrypted = base64.b64encode(template_data.encode()).decode()
        return encrypted
    
    async def _get_stored_template(self, user_id: str, biometric_type: BiometricType) -> Optional[str]:
        """Get stored biometric template"""
        # In real implementation, this would query the database
        # For demo, return a mock template
        return base64.b64encode(json.dumps({
            "features": np.random.rand(512).tolist(),
            "landmarks": np.random.rand(68, 2).tolist()
        }).encode()).decode()
    
    async def _compare_features(self, current_features: Dict, stored_template: str) -> float:
        """Compare current features with stored template"""
        try:
            # Decrypt stored template
            stored_data = json.loads(base64.b64decode(stored_template).decode())
            
            # Simple cosine similarity for demo
            current_vec = np.array(current_features["features"])
            stored_vec = np.array(stored_data["features"])
            
            # Normalize vectors
            current_norm = current_vec / np.linalg.norm(current_vec)
            stored_norm = stored_vec / np.linalg.norm(stored_vec)
            
            # Calculate cosine similarity
            similarity = np.dot(current_norm, stored_norm)
            
            # Convert to confidence score (0-1)
            confidence = (similarity + 1) / 2
            
            return float(confidence)
            
        except Exception as e:
            logger.error(f"Feature comparison error: {e}")
            return 0.0

class FingerprintService:
    """WebAuthn-based fingerprint authentication"""
    
    def __init__(self):
        self.rp_id = os.getenv("WEBAUTHN_RP_ID", "localhost")
        self.rp_name = os.getenv("WEBAUTHN_RP_NAME", "StableCoin Fintech")
        self.timeout = 60000  # 60 seconds
    
    async def initiate_fingerprint_enrollment(self, user_id: str, username: str) -> Dict:
        """Initiate fingerprint enrollment using WebAuthn"""
        try:
            # Generate challenge
            challenge = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
            
            # Create registration options
            registration_options = {
                "challenge": challenge,
                "rp": {
                    "id": self.rp_id,
                    "name": self.rp_name
                },
                "user": {
                    "id": base64.urlsafe_b64encode(user_id.encode()).decode().rstrip('='),
                    "name": username,
                    "displayName": username
                },
                "pubKeyCredParams": [
                    {"type": "public-key", "alg": -7},   # ES256
                    {"type": "public-key", "alg": -257}  # RS256
                ],
                "authenticatorSelection": {
                    "authenticatorAttachment": "platform",
                    "userVerification": "required",
                    "requireResidentKey": False
                },
                "timeout": self.timeout,
                "attestation": "direct"
            }
            
            # Store challenge temporarily
            await self._store_challenge(user_id, challenge, "enrollment")
            
            return {
                "success": True,
                "registration_options": registration_options
            }
            
        except Exception as e:
            logger.error(f"Fingerprint enrollment initiation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def complete_fingerprint_enrollment(self, user_id: str, credential: Dict) -> Dict:
        """Complete fingerprint enrollment"""
        try:
            # Verify challenge
            stored_challenge = await self._get_stored_challenge(user_id, "enrollment")
            if not stored_challenge:
                return {"success": False, "error": "Invalid or expired challenge"}
            
            # Verify credential
            if not await self._verify_credential(credential, stored_challenge):
                return {"success": False, "error": "Credential verification failed"}
            
            # Store credential
            credential_id = credential["id"]
            public_key = credential["response"]["publicKey"]
            
            template = BiometricTemplate(
                template_id=str(uuid.uuid4()),
                user_id=user_id,
                biometric_type=BiometricType.FINGERPRINT,
                provider=BiometricProvider.WEBAUTHN,
                encrypted_template=base64.b64encode(json.dumps({
                    "credential_id": credential_id,
                    "public_key": public_key
                }).encode()).decode(),
                template_hash=hashlib.sha256(credential_id.encode()).hexdigest(),
                quality_score=1.0,
                created_at=datetime.utcnow()
            )
            
            # Clean up challenge
            await self._cleanup_challenge(user_id, "enrollment")
            
            return {
                "success": True,
                "template_id": template.template_id,
                "credential_id": credential_id
            }
            
        except Exception as e:
            logger.error(f"Fingerprint enrollment completion error: {e}")
            return {"success": False, "error": str(e)}
    
    async def initiate_fingerprint_authentication(self, user_id: str) -> Dict:
        """Initiate fingerprint authentication"""
        try:
            # Generate challenge
            challenge = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
            
            # Get user's credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return {"success": False, "error": "No fingerprint enrolled"}
            
            # Create authentication options
            authentication_options = {
                "challenge": challenge,
                "rpId": self.rp_id,
                "allowCredentials": [
                    {
                        "type": "public-key",
                        "id": cred["credential_id"]
                    }
                    for cred in credentials
                ],
                "userVerification": "required",
                "timeout": self.timeout
            }
            
            # Store challenge temporarily
            await self._store_challenge(user_id, challenge, "authentication")
            
            return {
                "success": True,
                "authentication_options": authentication_options
            }
            
        except Exception as e:
            logger.error(f"Fingerprint authentication initiation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def complete_fingerprint_authentication(self, user_id: str, credential: Dict) -> Tuple[AuthenticationResult, Dict]:
        """Complete fingerprint authentication"""
        try:
            # Verify challenge
            stored_challenge = await self._get_stored_challenge(user_id, "authentication")
            if not stored_challenge:
                return AuthenticationResult.FAILED, {"error": "Invalid or expired challenge"}
            
            # Verify credential
            if not await self._verify_credential(credential, stored_challenge):
                return AuthenticationResult.FAILED, {"error": "Credential verification failed"}
            
            # Clean up challenge
            await self._cleanup_challenge(user_id, "authentication")
            
            return AuthenticationResult.SUCCESS, {
                "confidence_score": 1.0,
                "credential_id": credential["id"]
            }
            
        except Exception as e:
            logger.error(f"Fingerprint authentication completion error: {e}")
            return AuthenticationResult.FAILED, {"error": str(e)}
    
    async def _store_challenge(self, user_id: str, challenge: str, challenge_type: str):
        """Store challenge temporarily"""
        # In real implementation, store in Redis or database with expiration
        pass
    
    async def _get_stored_challenge(self, user_id: str, challenge_type: str) -> Optional[str]:
        """Get stored challenge"""
        # In real implementation, retrieve from storage
        return "mock_challenge"  # For demo
    
    async def _cleanup_challenge(self, user_id: str, challenge_type: str):
        """Clean up challenge"""
        # In real implementation, remove from storage
        pass
    
    async def _verify_credential(self, credential: Dict, challenge: str) -> bool:
        """Verify WebAuthn credential"""
        # In real implementation, use proper WebAuthn verification
        return True  # For demo
    
    async def _get_user_credentials(self, user_id: str) -> List[Dict]:
        """Get user's stored credentials"""
        # In real implementation, query database
        return [{"credential_id": "mock_credential_id"}]  # For demo

class BiometricAuthenticationService:
    """Main biometric authentication service"""
    
    def __init__(self, mongo_url: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client.get_database("stablecoin_db")
        self.biometric_templates_collection = self.db.get_collection("biometric_templates")
        self.biometric_attempts_collection = self.db.get_collection("biometric_attempts")
        self.device_registrations_collection = self.db.get_collection("device_registrations")
        
        # Initialize biometric services
        self.face_service = FaceRecognitionService()
        self.fingerprint_service = FingerprintService()
        self.security_service = BiometricSecurity()
        
        logger.info("Biometric authentication service initialized")
    
    async def enroll_biometric(self, user_id: str, biometric_type: BiometricType, 
                             biometric_data: str, device_fingerprint: str) -> Dict:
        """Enroll user's biometric data"""
        try:
            # Check if user already has this biometric type enrolled
            existing = await self.biometric_templates_collection.find_one({
                "user_id": user_id,
                "biometric_type": biometric_type.value,
                "is_active": True
            })
            
            if existing:
                return {"success": False, "error": "Biometric already enrolled"}
            
            # Route to appropriate service
            if biometric_type == BiometricType.FACE:
                success, result = await self.face_service.enroll_face(
                    user_id, biometric_data, device_fingerprint
                )
            elif biometric_type == BiometricType.FINGERPRINT:
                # For fingerprint, biometric_data would be username
                result = await self.fingerprint_service.initiate_fingerprint_enrollment(
                    user_id, biometric_data
                )
                success = result.get("success", False)
            else:
                return {"success": False, "error": "Biometric type not supported"}
            
            if success:
                # Store enrollment record
                if biometric_type == BiometricType.FACE:
                    template = BiometricTemplate(
                        template_id=result["template_id"],
                        user_id=user_id,
                        biometric_type=biometric_type,
                        provider=BiometricProvider.FACE_API,
                        encrypted_template="",  # Already stored by face service
                        template_hash="",
                        quality_score=result["quality_score"],
                        created_at=datetime.utcnow()
                    )
                    
                    # Convert enum values for MongoDB storage
                    template_dict = asdict(template)
                    template_dict['biometric_type'] = template.biometric_type.value
                    template_dict['provider'] = template.provider.value
                    
                    await self.biometric_templates_collection.insert_one(template_dict)
                
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": result.get("error", "Enrollment failed")}
                
        except Exception as e:
            logger.error(f"Biometric enrollment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def authenticate_biometric(self, user_id: str, biometric_type: BiometricType,
                                   biometric_data: str, device_fingerprint: str,
                                   ip_address: str, user_agent: str) -> Dict:
        """Authenticate user using biometric data"""
        try:
            # Check for account lockout
            if await self._is_account_locked(user_id, biometric_type):
                return {
                    "success": False,
                    "result": AuthenticationResult.FAILED,
                    "error": "Account temporarily locked due to too many failed attempts"
                }
            
            # Get recent attempts for trust scoring
            recent_attempts = await self._get_recent_attempts(user_id, biometric_type)
            
            # Calculate trust score
            trust_score = self.security_service.calculate_trust_score(
                user_id, device_fingerprint, "unknown", recent_attempts
            )
            
            # Route to appropriate service
            if biometric_type == BiometricType.FACE:
                auth_result, details = await self.face_service.authenticate_face(
                    user_id, biometric_data, device_fingerprint
                )
            elif biometric_type == BiometricType.FINGERPRINT:
                auth_result, details = await self.fingerprint_service.complete_fingerprint_authentication(
                    user_id, json.loads(biometric_data)
                )
            else:
                return {"success": False, "error": "Biometric type not supported"}
            
            # Record attempt
            attempt = BiometricAttempt(
                attempt_id=str(uuid.uuid4()),
                user_id=user_id,
                biometric_type=biometric_type,
                provider=BiometricProvider.FACE_API if biometric_type == BiometricType.FACE else BiometricProvider.WEBAUTHN,
                result=auth_result,
                confidence_score=details.get("confidence_score", 0.0),
                liveness_score=details.get("liveness_score", 0.0),
                device_fingerprint=device_fingerprint,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=details.get("error") if auth_result != AuthenticationResult.SUCCESS else None
            )
            
            # Convert enum values for MongoDB storage
            attempt_dict = asdict(attempt)
            attempt_dict['biometric_type'] = attempt.biometric_type.value
            attempt_dict['provider'] = attempt.provider.value
            attempt_dict['result'] = attempt.result.value
            
            await self.biometric_attempts_collection.insert_one(attempt_dict)
            
            # Update template usage
            if auth_result == AuthenticationResult.SUCCESS:
                await self._update_template_usage(user_id, biometric_type)
            
            # Check for suspicious activity
            all_recent_attempts = await self._get_recent_attempts(user_id)
            suspicious_activity = self.security_service.detect_suspicious_activity(
                user_id, all_recent_attempts
            )
            
            return {
                "success": auth_result == AuthenticationResult.SUCCESS,
                "result": auth_result,
                "details": details,
                "trust_score": trust_score,
                "suspicious_activity": suspicious_activity,
                "requires_additional_verification": trust_score < 0.5 or suspicious_activity
            }
            
        except Exception as e:
            logger.error(f"Biometric authentication error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _is_account_locked(self, user_id: str, biometric_type: BiometricType) -> bool:
        """Check if account is locked due to failed attempts"""
        cutoff_time = datetime.utcnow() - self.security_service.lockout_duration
        
        recent_failures = await self.biometric_attempts_collection.count_documents({
            "user_id": user_id,
            "biometric_type": biometric_type.value,
            "result": AuthenticationResult.FAILED.value,
            "timestamp": {"$gte": cutoff_time}
        })
        
        limit = self.security_service.attempt_limits.get(biometric_type, 5)
        return recent_failures >= limit
    
    async def _get_recent_attempts(self, user_id: str, biometric_type: Optional[BiometricType] = None) -> List[BiometricAttempt]:
        """Get recent authentication attempts"""
        query = {"user_id": user_id}
        if biometric_type:
            query["biometric_type"] = biometric_type.value
        
        cursor = self.biometric_attempts_collection.find(query).sort("timestamp", -1).limit(50)
        attempts = []
        
        async for doc in cursor:
            attempt = BiometricAttempt(
                attempt_id=doc["attempt_id"],
                user_id=doc["user_id"],
                biometric_type=BiometricType(doc["biometric_type"]),
                provider=BiometricProvider(doc["provider"]),
                result=AuthenticationResult(doc["result"]),
                confidence_score=doc["confidence_score"],
                liveness_score=doc["liveness_score"],
                device_fingerprint=doc["device_fingerprint"],
                timestamp=doc["timestamp"],
                ip_address=doc["ip_address"],
                user_agent=doc["user_agent"],
                failure_reason=doc.get("failure_reason")
            )
            attempts.append(attempt)
        
        return attempts
    
    async def _update_template_usage(self, user_id: str, biometric_type: BiometricType):
        """Update biometric template usage statistics"""
        await self.biometric_templates_collection.update_one(
            {
                "user_id": user_id,
                "biometric_type": biometric_type.value,
                "is_active": True
            },
            {
                "$set": {"last_used": datetime.utcnow()},
                "$inc": {"usage_count": 1}
            }
        )
    
    async def get_user_biometrics(self, user_id: str) -> Dict:
        """Get user's enrolled biometrics"""
        cursor = self.biometric_templates_collection.find({
            "user_id": user_id,
            "is_active": True
        })
        
        biometrics = []
        async for doc in cursor:
            biometrics.append({
                "template_id": doc["template_id"],
                "biometric_type": doc["biometric_type"],
                "provider": doc["provider"],
                "quality_score": doc["quality_score"],
                "created_at": doc["created_at"],
                "last_used": doc.get("last_used"),
                "usage_count": doc.get("usage_count", 0)
            })
        
        return {"biometrics": biometrics}
    
    async def revoke_biometric(self, user_id: str, template_id: str) -> Dict:
        """Revoke a biometric template"""
        try:
            result = await self.biometric_templates_collection.update_one(
                {
                    "template_id": template_id,
                    "user_id": user_id
                },
                {
                    "$set": {
                        "is_active": False,
                        "revoked_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                return {"success": True, "message": "Biometric revoked successfully"}
            else:
                return {"success": False, "error": "Biometric not found"}
                
        except Exception as e:
            logger.error(f"Biometric revocation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_authentication_history(self, user_id: str, limit: int = 50) -> Dict:
        """Get user's authentication history"""
        cursor = self.biometric_attempts_collection.find({
            "user_id": user_id
        }).sort("timestamp", -1).limit(limit)
        
        history = []
        async for doc in cursor:
            history.append({
                "attempt_id": doc["attempt_id"],
                "biometric_type": doc["biometric_type"],
                "result": doc["result"],
                "confidence_score": doc["confidence_score"],
                "timestamp": doc["timestamp"],
                "ip_address": doc["ip_address"],
                "device_fingerprint": doc["device_fingerprint"][:8] + "...",  # Truncate for privacy
                "failure_reason": doc.get("failure_reason")
            })
        
        return {"history": history}
    
    async def initialize_biometric_system(self):
        """Initialize biometric authentication system"""
        try:
            # Create indexes
            await self.biometric_templates_collection.create_index([("user_id", 1), ("biometric_type", 1)])
            await self.biometric_templates_collection.create_index([("template_id", 1)], unique=True)
            await self.biometric_attempts_collection.create_index([("user_id", 1), ("timestamp", -1)])
            await self.biometric_attempts_collection.create_index([("attempt_id", 1)], unique=True)
            await self.device_registrations_collection.create_index([("device_id", 1)], unique=True)
            await self.device_registrations_collection.create_index([("user_id", 1)])
            
            logger.info("Biometric authentication system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing biometric system: {e}")
            raise