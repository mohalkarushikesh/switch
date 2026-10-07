"""
Fraud Detector - Core fraud detection logic
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import statistics

from .models import (
    Transaction, TransactionStatus, FraudCheck, FraudScore,
    RiskLevel, FraudAlert, AlertSeverity, AlertStatus,
    Investigation, InvestigationStatus, BlockList,
    FraudStats, DetectionMetrics
)
from .rule_engine import RuleEngine
from .ml_scorer import MLScorer
from .pattern_analyzer import PatternAnalyzer


class FraudDetector:
    """
    Core fraud detection engine
    """
    
    def __init__(
        self,
        rule_engine: RuleEngine,
        ml_scorer: MLScorer,
        pattern_analyzer: PatternAnalyzer
    ):
        self.logger = logging.getLogger("fraud_detector")
        self.rule_engine = rule_engine
        self.ml_scorer = ml_scorer
        self.pattern_analyzer = pattern_analyzer
        
        # Storage
        self.transactions = {}  # transaction_id -> Transaction
        self.fraud_checks = {}  # check_id -> FraudCheck
        self.alerts = {}  # alert_id -> FraudAlert
        self.investigations = {}  # investigation_id -> Investigation
        self.blocklist = {}  # entry_id -> BlockList
        
        # Metrics
        self.metrics = {
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
            "total_checked": 0
        }
        
        self.is_monitoring = False
        
    async def initialize(self):
        """Initialize fraud detector"""
        self.logger.info("Initializing Fraud Detector")
        
        # In production:
        # - Load blocklist from database
        # - Initialize real-time monitoring
        # - Set up alert system
        
        # Create sample blocklist entries
        await self._create_sample_blocklist()
        
    async def _create_sample_blocklist(self):
        """Create sample blocklist entries"""
        from .models import BlockType
        
        sample_entries = [
            BlockList(
                block_type=BlockType.CARD,
                value="****1234",
                reason="Reported stolen",
                is_active=True
            ),
            BlockList(
                block_type=BlockType.IP_ADDRESS,
                value="192.168.1.100",
                reason="Known fraud source",
                is_active=True
            ),
            BlockList(
                block_type=BlockType.MERCHANT,
                value="FRAUD_MERCHANT_123",
                reason="Fraudulent merchant",
                is_active=True
            )
        ]
        
        for entry in sample_entries:
            self.blocklist[entry.entry_id] = entry
            
    async def start_monitoring(self):
        """Start real-time transaction monitoring"""
        self.is_monitoring = True
        self.logger.info("Started real-time fraud monitoring")
        
        while self.is_monitoring:
            try:
                # Monitor for anomalies
                await self._check_for_anomalies()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(10)
                
    async def _check_for_anomalies(self):
        """Check for system-wide anomalies"""
        # In production, implement anomaly detection
        # - Sudden spike in transactions
        # - Unusual patterns
        # - Coordinated attacks
        pass
        
    async def _cleanup_old_data(self):
        """Clean up old transaction data"""
        # Keep only recent data in memory
        cutoff_time = datetime.now() - timedelta(days=7)
        
        # Clean transactions
        old_transactions = [
            tid for tid, t in self.transactions.items()
            if t.initiated_at < cutoff_time
        ]
        
        for tid in old_transactions:
            del self.transactions[tid]
            
    async def check_transaction(self, transaction: Transaction) -> FraudCheck:
        """Check a transaction for fraud"""
        start_time = datetime.now()
        
        # Store transaction
        self.transactions[transaction.transaction_id] = transaction
        self.metrics["total_checked"] += 1
        
        # Check blocklist first
        if await self._is_blocked(transaction):
            return await self._create_blocked_check(transaction)
            
        # Get fraud score components
        ml_score = await self.ml_scorer.score_transaction(transaction)
        rule_results = await self.rule_engine.evaluate_transaction(transaction)
        behavior_analysis = await self.pattern_analyzer.analyze_transaction(transaction)
        
        # Calculate overall fraud score
        fraud_score = await self._calculate_fraud_score(
            transaction,
            ml_score,
            rule_results,
            behavior_analysis
        )
        
        # Determine risk level and action
        risk_level = self._determine_risk_level(fraud_score.overall_score)
        action = self._determine_action(risk_level, fraud_score)
        
        # Create fraud check result
        fraud_check = FraudCheck(
            transaction_id=transaction.transaction_id,
            is_fraudulent=risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            risk_level=risk_level,
            action_taken=action,
            fraud_score=fraud_score,
            reasons=self._get_reasons(fraud_score, rule_results, behavior_analysis),
            triggered_rules=[r.dict() for r in rule_results["triggered_rules"]],
            requires_manual_review=action == "flagged_for_review",
            review_priority=self._get_review_priority(risk_level),
            checks_performed=["ml_scoring", "rule_evaluation", "behavior_analysis", "blocklist_check"],
            check_duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
        )
        
        # Store check result
        self.fraud_checks[fraud_check.check_id] = fraud_check
        
        # Create alert if needed
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            await self._create_alert(transaction, fraud_check)
            
        # Update transaction status
        await self._update_transaction_status(transaction, fraud_check)
        
        # Update metrics
        await self._update_metrics(fraud_check)
        
        return fraud_check
        
    async def batch_check_transactions(
        self,
        transactions: List[Transaction]
    ) -> List[FraudCheck]:
        """Check multiple transactions efficiently"""
        # Process in parallel for efficiency
        tasks = [self.check_transaction(t) for t in transactions]
        results = await asyncio.gather(*tasks)
        
        return results
        
    async def _is_blocked(self, transaction: Transaction) -> bool:
        """Check if transaction involves blocked entities"""
        for entry in self.blocklist.values():
            if not entry.is_active:
                continue
                
            # Check based on block type
            if entry.block_type == BlockType.USER and entry.value == transaction.user_id:
                return True
            elif entry.block_type == BlockType.CARD and transaction.card_number_masked:
                if entry.value == transaction.card_number_masked:
                    return True
            elif entry.block_type == BlockType.MERCHANT and transaction.merchant_id:
                if entry.value == transaction.merchant_id:
                    return True
            elif entry.block_type == BlockType.IP_ADDRESS and transaction.ip_address:
                if entry.value == transaction.ip_address:
                    return True
                    
        return False
        
    async def _create_blocked_check(self, transaction: Transaction) -> FraudCheck:
        """Create fraud check for blocked transaction"""
        fraud_score = FraudScore(
            transaction_id=transaction.transaction_id,
            overall_score=100.0,
            risk_level=RiskLevel.CRITICAL,
            ml_score=100.0,
            rule_score=100.0,
            behavior_score=100.0,
            velocity_score=100.0,
            location_score=100.0,
            confidence=1.0,
            risk_factors=["Blocked entity"],
            triggered_rules=["Blocklist"],
            anomalies=[],
            model_version="1.0"
        )
        
        return FraudCheck(
            transaction_id=transaction.transaction_id,
            is_fraudulent=True,
            risk_level=RiskLevel.CRITICAL,
            action_taken="blocked",
            fraud_score=fraud_score,
            reasons=["Transaction involves blocked entity"],
            triggered_rules=[],
            requires_manual_review=False,
            review_priority="urgent",
            checks_performed=["blocklist_check"],
            check_duration_ms=1
        )
        
    async def _calculate_fraud_score(
        self,
        transaction: Transaction,
        ml_score: Dict[str, Any],
        rule_results: Dict[str, Any],
        behavior_analysis: Dict[str, Any]
    ) -> FraudScore:
        """Calculate comprehensive fraud score"""
        # Weight different components
        weights = {
            "ml": 0.40,
            "rules": 0.30,
            "behavior": 0.20,
            "velocity": 0.05,
            "location": 0.05
        }
        
        # Get component scores
        ml_fraud_score = ml_score.get("fraud_probability", 0) * 100
        rule_fraud_score = rule_results.get("risk_score", 0)
        behavior_fraud_score = behavior_analysis.get("anomaly_score", 0)
        
        # Calculate velocity score
        velocity_score = await self._calculate_velocity_score(transaction)
        
        # Calculate location score
        location_score = await self._calculate_location_score(transaction)
        
        # Calculate weighted overall score
        overall_score = (
            ml_fraud_score * weights["ml"] +
            rule_fraud_score * weights["rules"] +
            behavior_fraud_score * weights["behavior"] +
            velocity_score * weights["velocity"] +
            location_score * weights["location"]
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        # Compile risk factors
        risk_factors = []
        if ml_fraud_score > 70:
            risk_factors.append("High ML fraud score")
        if rule_fraud_score > 70:
            risk_factors.extend([r.name for r in rule_results["triggered_rules"]])
        if behavior_fraud_score > 70:
            risk_factors.append("Unusual behavior pattern")
        if velocity_score > 70:
            risk_factors.append("High velocity")
        if location_score > 70:
            risk_factors.append("Suspicious location")
            
        return FraudScore(
            transaction_id=transaction.transaction_id,
            overall_score=overall_score,
            risk_level=risk_level,
            ml_score=ml_fraud_score,
            rule_score=rule_fraud_score,
            behavior_score=behavior_fraud_score,
            velocity_score=velocity_score,
            location_score=location_score,
            confidence=ml_score.get("confidence", 0.8),
            risk_factors=risk_factors,
            triggered_rules=[r.name for r in rule_results["triggered_rules"]],
            anomalies=behavior_analysis.get("anomalies", []),
            model_version=ml_score.get("model_version", "1.0")
        )
        
    async def _calculate_velocity_score(self, transaction: Transaction) -> float:
        """Calculate velocity-based risk score"""
        # Get recent transactions for user
        user_transactions = [
            t for t in self.transactions.values()
            if t.user_id == transaction.user_id
            and t.initiated_at > datetime.now() - timedelta(hours=1)
        ]
        
        # Check transaction count
        if len(user_transactions) > 10:
            return 80.0  # High velocity
        elif len(user_transactions) > 5:
            return 50.0  # Medium velocity
        else:
            return 20.0  # Normal velocity
            
    async def _calculate_location_score(self, transaction: Transaction) -> float:
        """Calculate location-based risk score"""
        if not transaction.country:
            return 30.0  # Unknown location
            
        # High-risk countries (simplified)
        high_risk_countries = ["XX", "YY", "ZZ"]  # Example codes
        
        if transaction.country in high_risk_countries:
            return 80.0
            
        # Check for location changes
        # In production, compare with user's typical locations
        
        return 20.0  # Normal location
        
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score"""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
            
    def _determine_action(self, risk_level: RiskLevel, fraud_score: FraudScore) -> str:
        """Determine action based on risk level"""
        if risk_level == RiskLevel.CRITICAL:
            return "blocked"
        elif risk_level == RiskLevel.HIGH:
            return "flagged_for_review"
        elif risk_level == RiskLevel.MEDIUM and fraud_score.confidence < 0.7:
            return "flagged_for_review"
        else:
            return "approved"
            
    def _get_reasons(
        self,
        fraud_score: FraudScore,
        rule_results: Dict[str, Any],
        behavior_analysis: Dict[str, Any]
    ) -> List[str]:
        """Get human-readable reasons for decision"""
        reasons = []
        
        if fraud_score.ml_score > 70:
            reasons.append(f"ML model indicates {fraud_score.ml_score:.0f}% fraud probability")
            
        for rule in rule_results["triggered_rules"]:
            reasons.append(f"Triggered rule: {rule.description}")
            
        if behavior_analysis.get("is_anomaly"):
            reasons.append("Transaction deviates from normal behavior")
            
        if fraud_score.velocity_score > 70:
            reasons.append("High transaction velocity detected")
            
        if fraud_score.location_score > 70:
            reasons.append("Transaction from suspicious location")
            
        return reasons
        
    def _get_review_priority(self, risk_level: RiskLevel) -> str:
        """Get manual review priority"""
        priority_map = {
            RiskLevel.CRITICAL: "urgent",
            RiskLevel.HIGH: "high",
            RiskLevel.MEDIUM: "medium",
            RiskLevel.LOW: "low"
        }
        
        return priority_map.get(risk_level, "medium")
        
    async def _create_alert(self, transaction: Transaction, fraud_check: FraudCheck):
        """Create fraud alert"""
        alert = FraudAlert(
            type="suspicious_activity",
            severity=AlertSeverity.HIGH if fraud_check.risk_level == RiskLevel.HIGH else AlertSeverity.CRITICAL,
            user_id=transaction.user_id,
            transaction_id=transaction.transaction_id,
            title=f"Suspicious transaction detected - {fraud_check.risk_level} risk",
            description=f"Transaction of {transaction.amount} {transaction.currency} flagged as potentially fraudulent",
            details={
                "fraud_score": fraud_check.fraud_score.overall_score,
                "risk_factors": fraud_check.fraud_score.risk_factors,
                "merchant": transaction.merchant_name,
                "amount": str(transaction.amount)
            },
            recommended_actions=[
                "Review transaction details",
                "Contact customer if needed",
                "Consider blocking if confirmed fraud"
            ]
        )
        
        self.alerts[alert.alert_id] = alert
        
        self.logger.warning(f"Fraud alert created: {alert.title}")
        
    async def _update_transaction_status(
        self,
        transaction: Transaction,
        fraud_check: FraudCheck
    ):
        """Update transaction status based on fraud check"""
        if fraud_check.action_taken == "blocked":
            transaction.status = TransactionStatus.REJECTED
        elif fraud_check.action_taken == "flagged_for_review":
            transaction.status = TransactionStatus.FLAGGED
        else:
            transaction.status = TransactionStatus.APPROVED
            
        transaction.completed_at = datetime.now()
        
    async def _update_metrics(self, fraud_check: FraudCheck):
        """Update detection metrics"""
        # In production, this would be validated against actual fraud outcomes
        # For now, simulate based on risk level
        
        if fraud_check.is_fraudulent:
            # Assume high/critical risk are mostly true positives
            if fraud_check.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                self.metrics["true_positives"] += 1
            else:
                self.metrics["false_positives"] += 1
        else:
            # Assume low risk are mostly true negatives
            if fraud_check.risk_level == RiskLevel.LOW:
                self.metrics["true_negatives"] += 1
            else:
                # Could be false negatives
                pass
                
    async def get_fraud_score(self, transaction_id: str) -> Optional[FraudScore]:
        """Get detailed fraud score for transaction"""
        for check in self.fraud_checks.values():
            if check.transaction_id == transaction_id:
                return check.fraud_score
                
        return None
        
    async def review_transaction(
        self,
        transaction_id: str,
        reviewer_id: str,
        decision: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Review a flagged transaction"""
        transaction = self.transactions.get(transaction_id)
        
        if not transaction:
            return {"error": "Transaction not found"}
            
        # Update transaction status
        if decision == "approve":
            transaction.status = TransactionStatus.APPROVED
        elif decision == "reject":
            transaction.status = TransactionStatus.REJECTED
        elif decision == "investigate":
            transaction.status = TransactionStatus.UNDER_REVIEW
            # Create investigation
            await self.create_investigation(
                transaction,
                self.fraud_checks.get(transaction_id)
            )
            
        # Update metrics based on review
        if decision == "reject":
            # Confirmed fraud
            self.metrics["true_positives"] += 1
        elif decision == "approve":
            # False positive
            self.metrics["false_positives"] += 1
            
        return {
            "transaction_id": transaction_id,
            "new_status": transaction.status,
            "reviewed_by": reviewer_id,
            "notes": notes
        }
        
    async def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[FraudAlert]:
        """Get fraud alerts with filters"""
        alerts = list(self.alerts.values())
        
        # Apply filters
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if user_id:
            alerts = [a for a in alerts if a.user_id == user_id]
            
        # Sort by creation time (newest first)
        alerts.sort(key=lambda a: a.created_at, reverse=True)
        
        return alerts[:limit]
        
    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge an alert"""
        alert = self.alerts.get(alert_id)
        
        if not alert:
            return False
            
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        alert.updated_at = datetime.now()
        
        return True
        
    async def create_investigation(
        self,
        transaction: Transaction,
        fraud_check: Optional[FraudCheck] = None
    ):
        """Create a fraud investigation"""
        investigation = Investigation(
            case_number=f"CASE-{datetime.now().strftime('%Y%m%d')}-{len(self.investigations) + 1:04d}",
            title=f"Suspicious transaction - {transaction.merchant_name or 'Unknown'}",
            description=f"Investigation for transaction {transaction.transaction_id} of {transaction.amount} {transaction.currency}",
            priority="high" if fraud_check and fraud_check.risk_level == RiskLevel.CRITICAL else "medium",
            transaction_ids=[transaction.transaction_id],
            user_id=transaction.user_id,
            alert_ids=[a.alert_id for a in self.alerts.values() if a.transaction_id == transaction.transaction_id]
        )
        
        self.investigations[investigation.investigation_id] = investigation
        
        self.logger.info(f"Investigation created: {investigation.case_number}")
        
    async def get_investigations(
        self,
        status: Optional[InvestigationStatus] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50
    ) -> List[Investigation]:
        """Get investigations with filters"""
        investigations = list(self.investigations.values())
        
        # Apply filters
        if status:
            investigations = [i for i in investigations if i.status == status]
        if assigned_to:
            investigations = [i for i in investigations if i.assigned_to == assigned_to]
            
        # Sort by creation time (newest first)
        investigations.sort(key=lambda i: i.created_at, reverse=True)
        
        return investigations[:limit]
        
    async def update_investigation(
        self,
        investigation_id: str,
        investigator_id: str,
        status: InvestigationStatus,
        findings: Optional[str] = None,
        action_taken: Optional[str] = None
    ) -> bool:
        """Update investigation status"""
        investigation = self.investigations.get(investigation_id)
        
        if not investigation:
            return False
            
        investigation.status = status
        investigation.updated_at = datetime.now()
        
        if findings:
            investigation.findings = findings
            
        if action_taken:
            investigation.actions_taken.append(action_taken)
            
        if status == InvestigationStatus.CLOSED:
            investigation.closed_at = datetime.now()
            
        return True
        
    async def get_blocklist(
        self,
        block_type: Optional[BlockType] = None,
        active_only: bool = True
    ) -> List[BlockList]:
        """Get blocklist entries"""
        entries = list(self.blocklist.values())
        
        # Apply filters
        if block_type:
            entries = [e for e in entries if e.block_type == block_type]
        if active_only:
            entries = [e for e in entries if e.is_active]
            
        return entries
        
    async def add_to_blocklist(self, entry: BlockList) -> BlockList:
        """Add entry to blocklist"""
        self.blocklist[entry.entry_id] = entry
        
        self.logger.info(f"Added to blocklist: {entry.block_type} - {entry.value}")
        
        return entry
        
    async def remove_from_blocklist(self, entry_id: str) -> bool:
        """Remove entry from blocklist"""
        if entry_id in self.blocklist:
            del self.blocklist[entry_id]
            return True
            
        return False
        
    async def get_statistics(self, period: str) -> FraudStats:
        """Get fraud detection statistics"""
        # Calculate time range
        now = datetime.now()
        if period == "1h":
            start_time = now - timedelta(hours=1)
        elif period == "24h":
            start_time = now - timedelta(days=1)
        elif period == "7d":
            start_time = now - timedelta(days=7)
        else:  # 30d
            start_time = now - timedelta(days=30)
            
        # Filter data by time range
        period_transactions = [
            t for t in self.transactions.values()
            if t.initiated_at >= start_time
        ]
        
        period_checks = [
            c for c in self.fraud_checks.values()
            if c.checked_at >= start_time
        ]
        
        period_alerts = [
            a for a in self.alerts.values()
            if a.created_at >= start_time
        ]
        
        # Calculate statistics
        total_amount = sum(t.amount for t in period_transactions)
        flagged_transactions = [c for c in period_checks if c.action_taken in ["blocked", "flagged_for_review"]]
        flagged_amount = sum(
            self.transactions[c.transaction_id].amount
            for c in flagged_transactions
            if c.transaction_id in self.transactions
        )
        
        blocked_transactions = [c for c in period_checks if c.action_taken == "blocked"]
        blocked_amount = sum(
            self.transactions[c.transaction_id].amount
            for c in blocked_transactions
            if c.transaction_id in self.transactions
        )
        
        # Detection rates
        fraud_detection_rate = len(flagged_transactions) / len(period_checks) * 100 if period_checks else 0
        
        # Calculate false positive rate (simplified)
        total_flagged = len(flagged_transactions)
        false_positives = self.metrics["false_positives"]
        false_positive_rate = false_positives / total_flagged * 100 if total_flagged > 0 else 0
        
        # Risk distribution
        risk_distribution = {}
        for check in period_checks:
            level = check.risk_level.value
            risk_distribution[level] = risk_distribution.get(level, 0) + 1
            
        # Top fraud categories
        fraud_types = {}
        for check in flagged_transactions:
            for factor in check.fraud_score.risk_factors:
                fraud_types[factor] = fraud_types.get(factor, 0) + 1
                
        top_fraud_types = [
            {"type": k, "count": v}
            for k, v in sorted(fraud_types.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Average check time
        check_times = [c.check_duration_ms for c in period_checks]
        avg_check_time = statistics.mean(check_times) if check_times else 0
        
        return FraudStats(
            period=period,
            total_transactions=len(period_transactions),
            total_amount=total_amount,
            flagged_transactions=len(flagged_transactions),
            flagged_amount=flagged_amount,
            blocked_transactions=len(blocked_transactions),
            blocked_amount=blocked_amount,
            fraud_detection_rate=fraud_detection_rate,
            false_positive_rate=false_positive_rate,
            alerts_generated=len(period_alerts),
            alerts_resolved=len([a for a in period_alerts if a.status == AlertStatus.RESOLVED]),
            avg_resolution_time_hours=24.0,  # Mock
            investigations_opened=len([i for i in self.investigations.values() if i.created_at >= start_time]),
            investigations_closed=len([i for i in self.investigations.values() if i.closed_at and i.closed_at >= start_time]),
            fraud_confirmed_cases=5,  # Mock
            amount_recovered=Decimal("10000"),  # Mock
            most_effective_rules=[],  # Would get from rule engine
            risk_distribution=risk_distribution,
            top_fraud_types=top_fraud_types,
            top_fraud_merchants=[],  # Would analyze from transactions
            top_fraud_locations=[],  # Would analyze from transactions
            avg_check_time_ms=avg_check_time,
            ml_model_accuracy=0.92  # Mock
        )
        
    async def get_detection_metrics(self) -> DetectionMetrics:
        """Get detection performance metrics"""
        # Calculate metrics
        tp = self.metrics["true_positives"]
        fp = self.metrics["false_positives"]
        tn = self.metrics["true_negatives"]
        fn = self.metrics["false_negatives"]
        
        total = tp + fp + tn + fn
        
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Get check times
        check_times = [c.check_duration_ms for c in self.fraud_checks.values()]
        
        return DetectionMetrics(
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            ml_model_version="1.0",
            ml_model_accuracy=0.92,  # Mock
            ml_model_auc=0.95,  # Mock
            active_rules=await self.rule_engine.get_active_rule_count(),
            rules_triggered_count={},  # Would get from rule engine
            avg_rules_per_transaction=3.5,  # Mock
            avg_scoring_time_ms=statistics.mean(check_times) if check_times else 0,
            p95_scoring_time_ms=sorted(check_times)[int(len(check_times) * 0.95)] if check_times else 0,
            p99_scoring_time_ms=sorted(check_times)[int(len(check_times) * 0.99)] if check_times else 0,
            transactions_analyzed=self.metrics["total_checked"],
            users_monitored=len(set(t.user_id for t in self.transactions.values())),
            merchants_monitored=len(set(t.merchant_id for t in self.transactions.values() if t.merchant_id)),
            fraud_trend="stable",  # Would calculate from historical data
            detection_improvement=5.2  # Mock percentage
        )
        
    async def generate_report(
        self,
        report_id: str,
        report_type: str,
        time_period: str,
        requested_by: str
    ):
        """Generate fraud detection report"""
        # In production, this would:
        # - Gather comprehensive statistics
        # - Generate visualizations
        # - Create PDF/Excel report
        # - Store in document storage
        
        self.logger.info(f"Generating {report_type} fraud report {report_id} for period {time_period}")
        
        # Simulate report generation
        await asyncio.sleep(3)
        
    async def shutdown(self):
        """Shutdown fraud detector"""
        self.is_monitoring = False
        
        # Save state
        # In production, persist data to database
        
        self.logger.info("Fraud Detector shutdown complete") 