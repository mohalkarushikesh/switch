"""
ML Scorer - Machine learning-based fraud scoring
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import numpy as np
from decimal import Decimal
import random

from .models import Transaction, TransactionType, MLModelInfo


class MLScorer:
    """
    Machine learning-based fraud scoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ml_scorer")
        
        # Model information
        self.current_model = None
        self.model_version = "1.0"
        
        # Feature cache
        self.feature_cache = {}
        
        # Model performance tracking
        self.predictions = []
        self.model_metrics = {
            "accuracy": 0.92,
            "precision": 0.88,
            "recall": 0.85,
            "auc": 0.95
        }
        
    async def initialize(self):
        """Initialize ML scorer"""
        self.logger.info("Initializing ML Scorer")
        
        # In production:
        # - Load trained ML model
        # - Set up feature engineering pipeline
        # - Initialize model monitoring
        
        # Create mock model info
        self.current_model = MLModelInfo(
            model_id="fraud_model_v1",
            model_type="gradient_boost",
            version="1.0",
            trained_at=datetime.now() - timedelta(days=7),
            training_samples=1000000,
            features_used=[
                "amount", "merchant_category", "time_of_day",
                "location_risk", "velocity_score", "device_fingerprint"
            ],
            training_accuracy=0.92,
            validation_accuracy=0.90,
            test_accuracy=0.89,
            deployed_at=datetime.now() - timedelta(days=5),
            is_active=True,
            predictions_made=50000
        )
        
    async def score_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """Score a transaction using ML model"""
        try:
            # Extract features
            features = await self._extract_features(transaction)
            
            # Get model prediction
            fraud_probability = await self._predict(features)
            
            # Calculate confidence
            confidence = await self._calculate_confidence(features, fraud_probability)
            
            # Update model stats
            if self.current_model:
                self.current_model.predictions_made += 1
                self.current_model.last_prediction_at = datetime.now()
                
            # Store prediction for monitoring
            self.predictions.append({
                "transaction_id": transaction.transaction_id,
                "fraud_probability": fraud_probability,
                "confidence": confidence,
                "timestamp": datetime.now()
            })
            
            return {
                "fraud_probability": fraud_probability,
                "confidence": confidence,
                "model_version": self.model_version,
                "features_used": list(features.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error scoring transaction: {str(e)}")
            # Return default score on error
            return {
                "fraud_probability": 0.5,
                "confidence": 0.0,
                "model_version": self.model_version,
                "error": str(e)
            }
            
    async def _extract_features(self, transaction: Transaction) -> Dict[str, float]:
        """Extract features from transaction"""
        features = {}
        
        # Amount features
        features["amount"] = float(transaction.amount)
        features["amount_log"] = np.log1p(float(transaction.amount))
        features["is_round_amount"] = 1.0 if transaction.amount % 100 == 0 else 0.0
        
        # Time features
        features["hour_of_day"] = transaction.initiated_at.hour
        features["day_of_week"] = transaction.initiated_at.weekday()
        features["is_weekend"] = 1.0 if transaction.initiated_at.weekday() >= 5 else 0.0
        features["is_night"] = 1.0 if transaction.initiated_at.hour < 6 or transaction.initiated_at.hour > 22 else 0.0
        
        # Transaction type features
        features["is_withdrawal"] = 1.0 if transaction.type == TransactionType.WITHDRAWAL else 0.0
        features["is_transfer"] = 1.0 if transaction.type == TransactionType.TRANSFER else 0.0
        features["is_purchase"] = 1.0 if transaction.type == TransactionType.PURCHASE else 0.0
        
        # Merchant features
        if transaction.merchant_category:
            # High-risk categories
            risky_categories = ["gambling", "crypto", "adult", "gaming"]
            features["is_risky_merchant"] = 1.0 if any(
                cat in transaction.merchant_category.lower() for cat in risky_categories
            ) else 0.0
        else:
            features["is_risky_merchant"] = 0.0
            
        features["has_merchant"] = 1.0 if transaction.merchant_id else 0.0
        
        # Location features
        if transaction.country:
            # High-risk countries (simplified)
            high_risk_countries = ["XX", "YY", "ZZ"]
            features["is_high_risk_country"] = 1.0 if transaction.country in high_risk_countries else 0.0
        else:
            features["is_high_risk_country"] = 0.5  # Unknown is medium risk
            
        features["has_location"] = 1.0 if transaction.latitude and transaction.longitude else 0.0
        
        # Device features
        features["has_device_id"] = 1.0 if transaction.device_id else 0.0
        features["is_mobile"] = 1.0 if transaction.device_type and "mobile" in transaction.device_type.lower() else 0.0
        
        # Velocity features (would be calculated from history in production)
        features["velocity_score"] = await self._calculate_velocity_feature(transaction)
        
        # User behavior features (would be from user profile in production)
        features["user_risk_score"] = await self._get_user_risk_score(transaction.user_id)
        
        return features
        
    async def _calculate_velocity_feature(self, transaction: Transaction) -> float:
        """Calculate velocity-based feature"""
        # In production, would query transaction history
        # For now, return random value
        return random.uniform(0, 1)
        
    async def _get_user_risk_score(self, user_id: str) -> float:
        """Get user's historical risk score"""
        # In production, would look up user profile
        # For now, return random value
        return random.uniform(0.1, 0.9)
        
    async def _predict(self, features: Dict[str, float]) -> float:
        """Make fraud prediction"""
        # In production, would use actual ML model
        # For now, create a mock prediction based on features
        
        # Simple mock scoring logic
        score = 0.0
        
        # Amount contribution
        if features["amount"] > 5000:
            score += 0.2
        if features["amount"] > 10000:
            score += 0.3
            
        # Time contribution
        if features["is_night"]:
            score += 0.1
            
        # Merchant contribution
        if features["is_risky_merchant"]:
            score += 0.3
            
        # Location contribution
        if features["is_high_risk_country"]:
            score += 0.4
            
        # Velocity contribution
        score += features["velocity_score"] * 0.2
        
        # User history contribution
        score += (1 - features["user_risk_score"]) * 0.1
        
        # Add some randomness
        score += random.uniform(-0.1, 0.1)
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
        
    async def _calculate_confidence(
        self,
        features: Dict[str, float],
        prediction: float
    ) -> float:
        """Calculate prediction confidence"""
        # In production, would use model's confidence/probability
        # For now, base confidence on feature completeness and prediction extremity
        
        # Feature completeness
        total_features = len(features)
        non_zero_features = sum(1 for v in features.values() if v != 0.0)
        completeness = non_zero_features / total_features
        
        # Prediction extremity (more extreme = more confident)
        extremity = abs(prediction - 0.5) * 2
        
        # Combine factors
        confidence = (completeness * 0.7 + extremity * 0.3)
        
        return min(0.95, confidence)  # Cap at 95%
        
    async def retrain_model(self):
        """Retrain the ML model"""
        self.logger.info("Starting model retraining")
        
        # In production, this would:
        # - Fetch recent labeled data
        # - Perform feature engineering
        # - Train new model
        # - Validate performance
        # - Deploy if improved
        
        # Simulate retraining
        await asyncio.sleep(5)
        
        # Update model info
        self.model_version = "1.1"
        self.current_model = MLModelInfo(
            model_id="fraud_model_v1.1",
            model_type="gradient_boost",
            version="1.1",
            trained_at=datetime.now(),
            training_samples=1500000,
            features_used=[
                "amount", "merchant_category", "time_of_day",
                "location_risk", "velocity_score", "device_fingerprint",
                "user_behavior_score"  # New feature
            ],
            training_accuracy=0.93,
            validation_accuracy=0.91,
            test_accuracy=0.90,
            deployed_at=datetime.now(),
            is_active=True,
            predictions_made=0
        )
        
        # Update metrics
        self.model_metrics = {
            "accuracy": 0.93,
            "precision": 0.89,
            "recall": 0.87,
            "auc": 0.96
        }
        
        self.logger.info("Model retraining completed")
        
    async def get_model_performance(self) -> Dict[str, Any]:
        """Get current model performance metrics"""
        # Calculate recent performance
        recent_predictions = [
            p for p in self.predictions
            if p["timestamp"] > datetime.now() - timedelta(hours=24)
        ]
        
        # In production, would calculate actual metrics from labeled data
        performance = {
            "model_version": self.model_version,
            "model_type": self.current_model.model_type if self.current_model else "unknown",
            "deployed_at": self.current_model.deployed_at.isoformat() if self.current_model else None,
            "predictions_24h": len(recent_predictions),
            "total_predictions": self.current_model.predictions_made if self.current_model else 0,
            "metrics": self.model_metrics,
            "feature_importance": await self._get_feature_importance(),
            "drift_detected": await self._check_model_drift(),
            "last_retrained": self.current_model.trained_at.isoformat() if self.current_model else None
        }
        
        return performance
        
    async def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        # In production, would get from model
        # Mock feature importance
        return {
            "amount": 0.25,
            "velocity_score": 0.20,
            "is_high_risk_country": 0.15,
            "is_risky_merchant": 0.12,
            "user_risk_score": 0.10,
            "hour_of_day": 0.08,
            "is_night": 0.05,
            "device_features": 0.05
        }
        
    async def _check_model_drift(self) -> bool:
        """Check if model drift is detected"""
        # In production, would monitor:
        # - Feature distributions
        # - Prediction distributions
        # - Performance metrics over time
        
        # For now, simulate no drift
        return False
        
    async def explain_prediction(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """Explain a fraud prediction"""
        # In production, would use SHAP or LIME for explanations
        
        # Find prediction
        prediction = None
        for p in self.predictions:
            if p["transaction_id"] == transaction_id:
                prediction = p
                break
                
        if not prediction:
            return {"error": "Prediction not found"}
            
        # Mock explanation
        return {
            "transaction_id": transaction_id,
            "fraud_probability": prediction["fraud_probability"],
            "top_risk_factors": [
                {
                    "feature": "amount",
                    "contribution": 0.3,
                    "description": "Transaction amount is unusually high"
                },
                {
                    "feature": "location",
                    "contribution": 0.25,
                    "description": "Transaction from high-risk location"
                },
                {
                    "feature": "velocity",
                    "contribution": 0.2,
                    "description": "Rapid transaction velocity detected"
                }
            ],
            "model_confidence": prediction["confidence"]
        }
        
    async def update_model_feedback(
        self,
        transaction_id: str,
        is_fraud: bool
    ):
        """Update model with feedback on prediction"""
        # In production, would:
        # - Store feedback for retraining
        # - Update online learning model
        # - Track model performance
        
        self.logger.info(f"Received feedback for transaction {transaction_id}: fraud={is_fraud}")
        
        # Update metrics based on feedback
        # This is simplified - real implementation would track actual predictions
        if is_fraud:
            self.model_metrics["recall"] = min(1.0, self.model_metrics["recall"] + 0.001)
        else:
            self.model_metrics["precision"] = min(1.0, self.model_metrics["precision"] + 0.001) 