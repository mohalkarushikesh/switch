"""
Compliance Engine - Core compliance checking and rule enforcement
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import json

from .models import (
    ComplianceCheck, ComplianceStatus, ComplianceType,
    ComplianceRule, RuleViolation, AlertSeverity,
    RiskScore, AuditLog, ComplianceMetrics
)


class ComplianceEngine:
    """
    Core compliance checking engine
    """
    
    def __init__(self):
        self.logger = logging.getLogger("compliance_engine")
        self.rules = {}  # rule_id -> ComplianceRule
        self.checks = {}  # check_id -> ComplianceCheck
        self.risk_scores = {}  # user_id -> RiskScore
        self.audit_logs = []  # List[AuditLog]
        self.is_monitoring = False
        
    async def initialize(self):
        """Initialize compliance engine"""
        self.logger.info("Initializing Compliance Engine")
        
        # Load compliance rules
        await self._load_default_rules()
        
        # In production, connect to compliance databases
        
    async def _load_default_rules(self):
        """Load default compliance rules"""
        # Transaction limit rule
        self.rules["tx_limit_daily"] = ComplianceRule(
            rule_id="tx_limit_daily",
            rule_name="Daily Transaction Limit",
            rule_type=ComplianceType.TRANSACTION_LIMIT,
            description="Maximum daily transaction amount",
            condition="daily_total <= threshold",
            threshold=Decimal("50000"),
            jurisdictions=["GLOBAL"],
            severity=AlertSeverity.HIGH,
            auto_block=True,
            created_by="system"
        )
        
        # Large transaction rule
        self.rules["large_tx"] = ComplianceRule(
            rule_id="large_tx",
            rule_name="Large Transaction Reporting",
            rule_type=ComplianceType.AML,
            description="Report transactions over threshold",
            condition="amount >= threshold",
            threshold=Decimal("10000"),
            jurisdictions=["US"],
            severity=AlertSeverity.MEDIUM,
            require_review=True,
            created_by="system",
            regulatory_reference="31 CFR 1010.311"
        )
        
        # Suspicious pattern rule
        self.rules["suspicious_pattern"] = ComplianceRule(
            rule_id="suspicious_pattern",
            rule_name="Suspicious Transaction Pattern",
            rule_type=ComplianceType.AML,
            description="Detect structuring or unusual patterns",
            condition="pattern_score > threshold",
            threshold=0.8,
            severity=AlertSeverity.HIGH,
            auto_block=False,
            require_review=True,
            created_by="system"
        )
        
        # High-risk country rule
        self.rules["high_risk_country"] = ComplianceRule(
            rule_id="high_risk_country",
            rule_name="High-Risk Country Transaction",
            rule_type=ComplianceType.SANCTIONS,
            description="Transactions involving high-risk countries",
            condition="country in high_risk_list",
            severity=AlertSeverity.CRITICAL,
            auto_block=True,
            created_by="system"
        )
        
    async def run_check(
        self,
        user_id: str,
        check_type: ComplianceType,
        data: Optional[Dict[str, Any]] = None
    ) -> ComplianceCheck:
        """Run compliance check"""
        self.logger.info(f"Running {check_type} check for user {user_id}")
        
        check = ComplianceCheck(
            user_id=user_id,
            check_type=check_type,
            status=ComplianceStatus.PENDING,
            description=f"{check_type} compliance check",
            details=data or {}
        )
        
        try:
            # Run specific check based on type
            if check_type == ComplianceType.TRANSACTION_LIMIT:
                await self._check_transaction_limits(check, data)
            elif check_type == ComplianceType.AML:
                await self._check_aml_rules(check, data)
            elif check_type == ComplianceType.SANCTIONS:
                await self._check_sanctions(check, data)
            elif check_type == ComplianceType.KYC:
                await self._check_kyc_status(check)
            elif check_type == ComplianceType.RISK_ASSESSMENT:
                await self._assess_risk(check)
            else:
                await self._run_generic_check(check, data)
                
            # Calculate risk score
            check.risk_score = self._calculate_check_risk_score(check)
            
            # Determine final status
            if check.violations:
                critical_violations = [v for v in check.violations if v.severity == AlertSeverity.CRITICAL]
                if critical_violations:
                    check.status = ComplianceStatus.FAILED
                else:
                    check.status = ComplianceStatus.REVIEW_REQUIRED
            else:
                check.status = ComplianceStatus.PASSED
                
        except Exception as e:
            self.logger.error(f"Error running compliance check: {str(e)}")
            check.status = ComplianceStatus.FAILED
            check.details["error"] = str(e)
            
        # Store check
        self.checks[check.check_id] = check
        
        # Log audit event
        await self.log_audit_event(
            event_type="compliance_check",
            user_id=user_id,
            details={
                "check_id": check.check_id,
                "check_type": check_type.value,
                "status": check.status.value,
                "violations": len(check.violations)
            }
        )
        
        return check
        
    async def _check_transaction_limits(
        self,
        check: ComplianceCheck,
        data: Dict[str, Any]
    ):
        """Check transaction limits"""
        amount = Decimal(str(data.get("amount", 0)))
        daily_total = await self._get_daily_transaction_total(check.user_id)
        
        # Check daily limit rule
        daily_limit_rule = self.rules.get("tx_limit_daily")
        if daily_limit_rule and daily_limit_rule.is_active:
            if daily_total + amount > daily_limit_rule.threshold:
                violation = RuleViolation(
                    rule_id=daily_limit_rule.rule_id,
                    rule_name=daily_limit_rule.rule_name,
                    severity=daily_limit_rule.severity,
                    description=f"Daily transaction limit exceeded",
                    expected_value=f"<= ${daily_limit_rule.threshold}",
                    actual_value=f"${daily_total + amount}",
                    remediation_steps=[
                        "Wait until next day to transact",
                        "Request limit increase with proper justification"
                    ]
                )
                check.violations.append(violation)
                
        # Check large transaction rule
        large_tx_rule = self.rules.get("large_tx")
        if large_tx_rule and large_tx_rule.is_active:
            if amount >= large_tx_rule.threshold:
                check.details["large_transaction"] = True
                check.required_actions.append(
                    f"File Currency Transaction Report (CTR) for ${amount}"
                )
                
    async def _check_aml_rules(
        self,
        check: ComplianceCheck,
        data: Dict[str, Any]
    ):
        """Check AML rules"""
        # Pattern detection (mock)
        pattern_score = await self._calculate_pattern_score(check.user_id, data)
        
        pattern_rule = self.rules.get("suspicious_pattern")
        if pattern_rule and pattern_rule.is_active:
            if pattern_score > pattern_rule.threshold:
                violation = RuleViolation(
                    rule_id=pattern_rule.rule_id,
                    rule_name=pattern_rule.rule_name,
                    severity=pattern_rule.severity,
                    description="Suspicious transaction pattern detected",
                    expected_value=f"pattern_score <= {pattern_rule.threshold}",
                    actual_value=f"pattern_score = {pattern_score:.2f}",
                    context={
                        "pattern_type": "potential_structuring",
                        "confidence": pattern_score
                    },
                    remediation_steps=[
                        "Provide explanation for transaction pattern",
                        "Submit supporting documentation"
                    ]
                )
                check.violations.append(violation)
                check.required_actions.append("File Suspicious Activity Report (SAR)")
                
    async def _check_sanctions(
        self,
        check: ComplianceCheck,
        data: Dict[str, Any]
    ):
        """Check sanctions lists"""
        # High-risk countries (mock list)
        high_risk_countries = ["IR", "KP", "SY", "CU"]
        
        country = data.get("country")
        if country in high_risk_countries:
            violation = RuleViolation(
                rule_id="high_risk_country",
                rule_name="High-Risk Country Transaction",
                severity=AlertSeverity.CRITICAL,
                description=f"Transaction involves sanctioned country: {country}",
                expected_value="Not in sanctioned countries list",
                actual_value=country,
                remediation_required=True,
                remediation_steps=["Transaction cannot proceed"]
            )
            check.violations.append(violation)
            
    async def _check_kyc_status(self, check: ComplianceCheck):
        """Check KYC compliance"""
        # In production, check actual KYC status
        # For now, mock check
        check.details["kyc_verified"] = True
        check.details["kyc_expiry"] = (datetime.now() + timedelta(days=365)).isoformat()
        
    async def _assess_risk(self, check: ComplianceCheck):
        """Perform risk assessment"""
        risk_score = await self.calculate_risk_score(check.user_id)
        
        check.details["risk_assessment"] = {
            "overall_score": risk_score.overall_score,
            "risk_level": risk_score.risk_level,
            "monitoring_level": risk_score.monitoring_level
        }
        
        if risk_score.risk_level in ["high", "very_high"]:
            check.recommendations.append("Enhanced due diligence recommended")
            check.recommendations.append(f"Increase monitoring to {risk_score.review_frequency}")
            
    async def _run_generic_check(
        self,
        check: ComplianceCheck,
        data: Dict[str, Any]
    ):
        """Run generic compliance check"""
        # Apply all active rules of the check type
        for rule in self.rules.values():
            if rule.rule_type == check.check_type and rule.is_active:
                # Evaluate rule condition (simplified)
                # In production, use a proper rule engine
                passed = True  # Mock evaluation
                
                if not passed:
                    violation = RuleViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        severity=rule.severity,
                        description=rule.description,
                        expected_value="Rule condition met",
                        actual_value="Rule condition failed"
                    )
                    check.violations.append(violation)
                    
    async def _get_daily_transaction_total(self, user_id: str) -> Decimal:
        """Get user's daily transaction total"""
        # In production, query transaction database
        # Mock implementation
        return Decimal("15000")
        
    async def _calculate_pattern_score(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> float:
        """Calculate suspicious pattern score"""
        # In production, use ML models
        # Mock implementation
        import random
        return random.uniform(0.1, 0.9)
        
    def _calculate_check_risk_score(self, check: ComplianceCheck) -> float:
        """Calculate risk score for compliance check"""
        base_score = 0.0
        
        # Add score based on violations
        for violation in check.violations:
            if violation.severity == AlertSeverity.CRITICAL:
                base_score += 40
            elif violation.severity == AlertSeverity.HIGH:
                base_score += 25
            elif violation.severity == AlertSeverity.MEDIUM:
                base_score += 15
            else:
                base_score += 5
                
        # Cap at 100
        return min(100, base_score)
        
    async def screen_transaction(
        self,
        user_id: str,
        transaction: Dict[str, Any]
    ) -> ComplianceCheck:
        """Screen a transaction for compliance"""
        # Combine multiple checks
        checks_to_run = [
            ComplianceType.TRANSACTION_LIMIT,
            ComplianceType.AML,
            ComplianceType.SANCTIONS
        ]
        
        violations = []
        risk_scores = []
        
        for check_type in checks_to_run:
            check = await self.run_check(user_id, check_type, transaction)
            violations.extend(check.violations)
            risk_scores.append(check.risk_score)
            
        # Create combined result
        combined_check = ComplianceCheck(
            user_id=user_id,
            check_type=ComplianceType.REGULATORY,
            status=ComplianceStatus.PASSED if not violations else ComplianceStatus.FAILED,
            description="Transaction screening",
            details=transaction,
            violations=violations,
            risk_score=max(risk_scores) if risk_scores else 0
        )
        
        return combined_check
        
    async def calculate_risk_score(self, user_id: str) -> RiskScore:
        """Calculate user's risk score"""
        # Check cache
        if user_id in self.risk_scores:
            cached = self.risk_scores[user_id]
            if (datetime.now() - cached.calculated_at).days < 7:
                return cached
                
        # Calculate new score
        # In production, aggregate various risk factors
        
        # Mock calculation
        import random
        
        kyc_score = random.uniform(70, 95)
        transaction_score = random.uniform(60, 90)
        behavior_score = random.uniform(65, 95)
        country_score = 85.0  # Fixed for mock
        
        overall_score = (
            kyc_score * 0.3 +
            transaction_score * 0.3 +
            behavior_score * 0.2 +
            country_score * 0.2
        )
        
        # Determine risk level
        if overall_score >= 80:
            risk_level = "low"
            monitoring_level = "standard"
            review_frequency = "quarterly"
        elif overall_score >= 60:
            risk_level = "medium"
            monitoring_level = "enhanced"
            review_frequency = "monthly"
        elif overall_score >= 40:
            risk_level = "high"
            monitoring_level = "intensive"
            review_frequency = "weekly"
        else:
            risk_level = "very_high"
            monitoring_level = "intensive"
            review_frequency = "daily"
            
        risk_score = RiskScore(
            user_id=user_id,
            overall_score=overall_score,
            risk_level=risk_level,
            kyc_score=kyc_score,
            transaction_score=transaction_score,
            behavior_score=behavior_score,
            country_score=country_score,
            risk_factors=[
                {"factor": "transaction_volume", "impact": "medium"},
                {"factor": "account_age", "impact": "low"}
            ],
            monitoring_level=monitoring_level,
            review_frequency=review_frequency,
            next_review=datetime.now() + timedelta(days=30)
        )
        
        # Cache the score
        self.risk_scores[user_id] = risk_score
        
        return risk_score
        
    async def get_user_compliance_history(
        self,
        user_id: str,
        check_type: Optional[ComplianceType] = None,
        since: Optional[datetime] = None
    ) -> List[ComplianceCheck]:
        """Get user's compliance check history"""
        history = []
        
        for check in self.checks.values():
            if check.user_id == user_id:
                if check_type and check.check_type != check_type:
                    continue
                if since and check.performed_at < since:
                    continue
                history.append(check)
                
        # Sort by date descending
        history.sort(key=lambda c: c.performed_at, reverse=True)
        
        return history
        
    async def get_rules(
        self,
        jurisdiction: Optional[str] = None,
        active_only: bool = True
    ) -> List[ComplianceRule]:
        """Get compliance rules"""
        rules = []
        
        for rule in self.rules.values():
            if active_only and not rule.is_active:
                continue
            if jurisdiction and jurisdiction not in rule.jurisdictions:
                continue
            rules.append(rule)
            
        return rules
        
    async def create_rule(self, rule: ComplianceRule) -> ComplianceRule:
        """Create new compliance rule"""
        # Store rule
        self.rules[rule.rule_id] = rule
        
        # Log creation
        await self.log_audit_event(
            event_type="rule_created",
            details={
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "created_by": rule.created_by
            }
        )
        
        return rule
        
    async def log_audit_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log audit event"""
        audit_log = AuditLog(
            event_type=event_type,
            event_description=f"Compliance event: {event_type}",
            user_id=user_id,
            system_id="compliance_engine",
            before_state=None,
            after_state=details,
            compliance_impact="high" if "violation" in event_type else "medium"
        )
        
        self.audit_logs.append(audit_log)
        
        # In production, persist to audit database
        
    async def get_audit_logs(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs"""
        logs = self.audit_logs
        
        if event_type:
            logs = [l for l in logs if l.event_type == event_type]
        if since:
            logs = [l for l in logs if l.timestamp >= since]
            
        # Sort by timestamp descending
        logs.sort(key=lambda l: l.timestamp, reverse=True)
        
        return logs[:limit]
        
    async def calculate_metrics(self, days: int = 30) -> ComplianceMetrics:
        """Calculate compliance metrics"""
        since = datetime.now() - timedelta(days=days)
        
        # Filter recent checks
        recent_checks = [
            c for c in self.checks.values()
            if c.performed_at >= since
        ]
        
        # Calculate metrics
        total_checks = len(recent_checks)
        passed_checks = len([c for c in recent_checks if c.status == ComplianceStatus.PASSED])
        failed_checks = len([c for c in recent_checks if c.status == ComplianceStatus.FAILED])
        
        # Mock other metrics
        metrics = ComplianceMetrics(
            period_days=days,
            kyc_verifications=150,
            kyc_approved=135,
            kyc_rejected=10,
            kyc_pending=5,
            kyc_approval_rate=0.9,
            avg_kyc_time_hours=24.5,
            transactions_screened=5000,
            suspicious_transactions=25,
            aml_alerts_generated=15,
            aml_alerts_resolved=12,
            false_positive_rate=0.4,
            high_risk_users=50,
            medium_risk_users=200,
            low_risk_users=750,
            avg_risk_score=45.5,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            compliance_rate=passed_checks / total_checks if total_checks > 0 else 0,
            reports_generated=5,
            reports_filed=5,
            regulatory_breaches=0,
            risk_trend="stable",
            alert_trend="decreasing",
            compliance_trend="improving"
        )
        
        return metrics
        
    async def record_training(
        self,
        user_id: str,
        module: str,
        score: float,
        completed_at: datetime
    ):
        """Record compliance training completion"""
        await self.log_audit_event(
            event_type="training_completed",
            user_id=user_id,
            details={
                "module": module,
                "score": score,
                "completed_at": completed_at.isoformat()
            }
        )
        
        # In production, update user's training record
        
    async def rule_monitoring(self):
        """Monitor compliance rules continuously"""
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                # Check for rule updates
                # In production, sync with regulatory databases
                
                await asyncio.sleep(3600)  # Check hourly
                
            except Exception as e:
                self.logger.error(f"Error in rule monitoring: {str(e)}")
                await asyncio.sleep(60)
                
    async def shutdown(self):
        """Shutdown compliance engine"""
        self.is_monitoring = False
        self.logger.info("Compliance Engine shutdown complete") 