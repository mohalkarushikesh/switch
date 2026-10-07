"""
Pattern Analyzer - Behavioral pattern analysis for fraud detection
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import statistics
import random

from .models import (
    Transaction, UserBehavior, BehaviorPattern,
    TransactionType
)


class PatternAnalyzer:
    """
    Analyzes transaction patterns and user behavior
    """
    
    def __init__(self):
        self.logger = logging.getLogger("pattern_analyzer")
        
        # User behavior profiles
        self.user_behaviors = {}  # user_id -> UserBehavior
        
        # Pattern storage
        self.behavior_patterns = {}  # pattern_id -> BehaviorPattern
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            "amount_deviation": 3.0,  # Standard deviations
            "frequency_deviation": 2.5,
            "location_distance": 500,  # km
            "time_deviation": 3  # hours
        }
        
    async def initialize(self):
        """Initialize pattern analyzer"""
        self.logger.info("Initializing Pattern Analyzer")
        
        # In production:
        # - Load historical user behaviors
        # - Initialize anomaly detection models
        # - Set up pattern recognition
        
    async def analyze_transaction(
        self,
        transaction: Transaction
    ) -> Dict[str, Any]:
        """Analyze transaction for behavioral anomalies"""
        # Get or create user behavior profile
        user_behavior = await self.get_user_behavior(transaction.user_id)
        
        # Analyze various aspects
        amount_anomaly = await self._analyze_amount_pattern(transaction, user_behavior)
        time_anomaly = await self._analyze_time_pattern(transaction, user_behavior)
        location_anomaly = await self._analyze_location_pattern(transaction, user_behavior)
        merchant_anomaly = await self._analyze_merchant_pattern(transaction, user_behavior)
        velocity_anomaly = await self._analyze_velocity_pattern(transaction, user_behavior)
        
        # Calculate overall anomaly score
        anomaly_scores = [
            amount_anomaly["score"],
            time_anomaly["score"],
            location_anomaly["score"],
            merchant_anomaly["score"],
            velocity_anomaly["score"]
        ]
        
        overall_anomaly_score = statistics.mean(anomaly_scores) * 100
        
        # Determine if transaction is anomalous
        is_anomaly = overall_anomaly_score > 50
        
        # Compile anomalies
        anomalies = []
        if amount_anomaly["is_anomaly"]:
            anomalies.append(f"Unusual amount: {amount_anomaly['reason']}")
        if time_anomaly["is_anomaly"]:
            anomalies.append(f"Unusual time: {time_anomaly['reason']}")
        if location_anomaly["is_anomaly"]:
            anomalies.append(f"Unusual location: {location_anomaly['reason']}")
        if merchant_anomaly["is_anomaly"]:
            anomalies.append(f"Unusual merchant: {merchant_anomaly['reason']}")
        if velocity_anomaly["is_anomaly"]:
            anomalies.append(f"High velocity: {velocity_anomaly['reason']}")
            
        # Update user behavior
        await self._update_user_behavior(transaction, user_behavior)
        
        # Create pattern if anomalous
        if is_anomaly:
            await self._create_behavior_pattern(transaction, anomalies, overall_anomaly_score)
            
        return {
            "anomaly_score": overall_anomaly_score,
            "is_anomaly": is_anomaly,
            "anomalies": anomalies,
            "analysis_details": {
                "amount": amount_anomaly,
                "time": time_anomaly,
                "location": location_anomaly,
                "merchant": merchant_anomaly,
                "velocity": velocity_anomaly
            }
        }
        
    async def get_user_behavior(self, user_id: str) -> UserBehavior:
        """Get or create user behavior profile"""
        if user_id not in self.user_behaviors:
            # Create default profile
            self.user_behaviors[user_id] = UserBehavior(
                user_id=user_id,
                typical_transaction_amount=Decimal("100"),
                max_transaction_amount=Decimal("1000"),
                typical_transaction_frequency=5.0,
                common_merchants=[],
                common_transaction_types=[TransactionType.PURCHASE],
                common_locations=["US"],
                common_time_of_day=list(range(9, 21)),  # 9 AM to 9 PM
                known_devices=[],
                device_fingerprints=[],
                typical_ip_locations=["US"],
                max_daily_transactions=10,
                max_daily_amount=Decimal("5000"),
                max_hourly_transactions=3,
                failed_transaction_rate=0.02,
                dispute_rate=0.001,
                account_age_days=365,
                risk_score=20.0,
                trust_score=80.0,
                last_transaction_date=datetime.now()
            )
            
        return self.user_behaviors[user_id]
        
    async def _analyze_amount_pattern(
        self,
        transaction: Transaction,
        user_behavior: UserBehavior
    ) -> Dict[str, Any]:
        """Analyze transaction amount pattern"""
        typical_amount = user_behavior.typical_transaction_amount
        
        # Calculate deviation
        if typical_amount > 0:
            deviation = abs(float(transaction.amount - typical_amount)) / float(typical_amount)
        else:
            deviation = 1.0
            
        # Check if anomalous
        is_anomaly = False
        reason = ""
        
        if transaction.amount > user_behavior.max_transaction_amount * 2:
            is_anomaly = True
            reason = f"Amount {transaction.amount} is more than double the maximum"
        elif deviation > self.anomaly_thresholds["amount_deviation"]:
            is_anomaly = True
            reason = f"Amount deviates significantly from typical {typical_amount}"
            
        # Calculate anomaly score (0-1)
        score = min(1.0, deviation / self.anomaly_thresholds["amount_deviation"])
        
        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "reason": reason,
            "typical_amount": typical_amount,
            "transaction_amount": transaction.amount,
            "deviation": deviation
        }
        
    async def _analyze_time_pattern(
        self,
        transaction: Transaction,
        user_behavior: UserBehavior
    ) -> Dict[str, Any]:
        """Analyze transaction time pattern"""
        hour = transaction.initiated_at.hour
        
        # Check if in common hours
        is_common_time = hour in user_behavior.common_time_of_day
        
        # Calculate anomaly
        is_anomaly = False
        reason = ""
        score = 0.0
        
        if not is_common_time:
            # Check how far from common times
            if user_behavior.common_time_of_day:
                min_distance = min(
                    abs(hour - common_hour)
                    for common_hour in user_behavior.common_time_of_day
                )
                
                if min_distance > self.anomaly_thresholds["time_deviation"]:
                    is_anomaly = True
                    reason = f"Transaction at {hour}:00 is unusual"
                    score = min(1.0, min_distance / 12)  # Max 12 hour difference
            else:
                # No history, moderate anomaly
                score = 0.3
                
        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "reason": reason,
            "transaction_hour": hour,
            "common_hours": user_behavior.common_time_of_day
        }
        
    async def _analyze_location_pattern(
        self,
        transaction: Transaction,
        user_behavior: UserBehavior
    ) -> Dict[str, Any]:
        """Analyze transaction location pattern"""
        if not transaction.country:
            return {
                "is_anomaly": False,
                "score": 0.2,  # Slight penalty for missing location
                "reason": "No location data"
            }
            
        # Check if in common locations
        is_common_location = transaction.country in user_behavior.common_locations
        
        is_anomaly = False
        reason = ""
        score = 0.0
        
        if not is_common_location:
            is_anomaly = True
            reason = f"Transaction from unusual location: {transaction.country}"
            score = 0.8  # High score for new location
            
        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "reason": reason,
            "transaction_location": transaction.country,
            "common_locations": user_behavior.common_locations
        }
        
    async def _analyze_merchant_pattern(
        self,
        transaction: Transaction,
        user_behavior: UserBehavior
    ) -> Dict[str, Any]:
        """Analyze merchant pattern"""
        if not transaction.merchant_id:
            return {
                "is_anomaly": False,
                "score": 0.0,
                "reason": "No merchant data"
            }
            
        # Check if known merchant
        is_known_merchant = transaction.merchant_id in user_behavior.common_merchants
        
        is_anomaly = False
        reason = ""
        score = 0.0
        
        if not is_known_merchant and transaction.amount > user_behavior.typical_transaction_amount * 3:
            is_anomaly = True
            reason = f"Large transaction with new merchant: {transaction.merchant_name}"
            score = 0.7
        elif not is_known_merchant:
            # New merchant but reasonable amount
            score = 0.3
            
        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "reason": reason,
            "merchant": transaction.merchant_name,
            "is_new_merchant": not is_known_merchant
        }
        
    async def _analyze_velocity_pattern(
        self,
        transaction: Transaction,
        user_behavior: UserBehavior
    ) -> Dict[str, Any]:
        """Analyze transaction velocity"""
        # In production, would check actual recent transactions
        # For now, simulate
        
        # Random velocity check
        recent_transaction_count = random.randint(0, 15)
        
        is_anomaly = False
        reason = ""
        score = 0.0
        
        if recent_transaction_count > user_behavior.max_hourly_transactions:
            is_anomaly = True
            reason = f"{recent_transaction_count} transactions in last hour exceeds limit"
            score = min(1.0, recent_transaction_count / user_behavior.max_hourly_transactions - 1)
            
        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "reason": reason,
            "recent_transactions": recent_transaction_count,
            "hourly_limit": user_behavior.max_hourly_transactions
        }
        
    async def _update_user_behavior(
        self,
        transaction: Transaction,
        user_behavior: UserBehavior
    ):
        """Update user behavior profile with new transaction"""
        # Update transaction amount stats
        # In production, would use proper statistical methods
        
        # Update typical amount (simple moving average)
        alpha = 0.1  # Learning rate
        user_behavior.typical_transaction_amount = Decimal(
            float(user_behavior.typical_transaction_amount) * (1 - alpha) +
            float(transaction.amount) * alpha
        )
        
        # Update max amount
        if transaction.amount > user_behavior.max_transaction_amount:
            user_behavior.max_transaction_amount = transaction.amount
            
        # Update common merchants
        if transaction.merchant_id and transaction.merchant_id not in user_behavior.common_merchants:
            user_behavior.common_merchants.append(transaction.merchant_id)
            # Keep only top 20 merchants
            if len(user_behavior.common_merchants) > 20:
                user_behavior.common_merchants = user_behavior.common_merchants[-20:]
                
        # Update common locations
        if transaction.country and transaction.country not in user_behavior.common_locations:
            user_behavior.common_locations.append(transaction.country)
            
        # Update time patterns
        hour = transaction.initiated_at.hour
        if hour not in user_behavior.common_time_of_day:
            user_behavior.common_time_of_day.append(hour)
            
        # Update device info
        if transaction.device_id and transaction.device_id not in user_behavior.known_devices:
            user_behavior.known_devices.append(transaction.device_id)
            
        # Update last transaction date
        user_behavior.last_transaction_date = transaction.initiated_at
        user_behavior.profile_updated_at = datetime.now()
        
    async def _create_behavior_pattern(
        self,
        transaction: Transaction,
        anomalies: List[str],
        anomaly_score: float
    ):
        """Create a behavior pattern record"""
        pattern = BehaviorPattern(
            user_id=transaction.user_id,
            pattern_type="anomaly",
            description=f"Anomalous transaction detected: {', '.join(anomalies[:2])}",
            pattern_data={
                "transaction_id": transaction.transaction_id,
                "anomalies": anomalies,
                "amount": str(transaction.amount),
                "merchant": transaction.merchant_name
            },
            confidence=min(0.95, anomaly_score / 100),
            is_anomaly=True,
            anomaly_score=anomaly_score,
            observed_from=transaction.initiated_at,
            observed_to=transaction.initiated_at,
            occurrence_count=1,
            is_suspicious=anomaly_score > 70,
            requires_investigation=anomaly_score > 80
        )
        
        self.behavior_patterns[pattern.pattern_id] = pattern
        
    async def get_anomalies(
        self,
        time_window_hours: int = 24,
        min_severity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        anomalies = []
        
        for pattern in self.behavior_patterns.values():
            if (pattern.is_anomaly and 
                pattern.observed_from >= cutoff_time and
                pattern.confidence >= min_severity):
                
                anomalies.append({
                    "pattern_id": pattern.pattern_id,
                    "user_id": pattern.user_id,
                    "description": pattern.description,
                    "severity": pattern.confidence,
                    "anomaly_score": pattern.anomaly_score,
                    "detected_at": pattern.observed_from,
                    "details": pattern.pattern_data
                })
                
        # Sort by severity
        anomalies.sort(key=lambda a: a["severity"], reverse=True)
        
        return anomalies
        
    async def detect_coordinated_fraud(
        self,
        time_window_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Detect potential coordinated fraud patterns"""
        # In production, would use clustering and graph analysis
        # to detect coordinated attacks
        
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        # Group patterns by similarity
        # For now, return empty list
        coordinated_patterns = []
        
        return coordinated_patterns
        
    async def get_user_risk_evolution(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user's risk score evolution over time"""
        user_behavior = await self.get_user_behavior(user_id)
        
        # In production, would track historical risk scores
        # For now, simulate
        
        risk_history = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            # Simulate risk score with some variation
            base_risk = user_behavior.risk_score
            variation = random.uniform(-10, 10)
            risk_score = max(0, min(100, base_risk + variation))
            
            risk_history.append({
                "date": date.date().isoformat(),
                "risk_score": risk_score
            })
            
        return {
            "user_id": user_id,
            "current_risk_score": user_behavior.risk_score,
            "risk_trend": "stable",  # Would calculate from history
            "risk_history": risk_history
        } 