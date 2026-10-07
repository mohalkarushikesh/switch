"""
AML Monitor - Anti-Money Laundering monitoring and detection
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import numpy as np

from .models import (
    AMLAlert, AlertSeverity, SuspiciousActivity,
    SanctionsScreeningResult
)


class AMLMonitor:
    """
    Monitors transactions and activities for AML compliance
    """
    
    def __init__(self):
        self.logger = logging.getLogger("aml_monitor")
        self.alerts = {}  # alert_id -> AMLAlert
        self.activity_patterns = {}  # user_id -> pattern_data
        self.is_monitoring = False
        self.monitoring_interval = 60  # seconds
        
    async def initialize(self):
        """Initialize AML monitor"""
        self.logger.info("Initializing AML Monitor")
        
        # In production:
        # - Load ML models for pattern detection
        # - Connect to transaction monitoring systems
        # - Initialize rule engine
        
    async def continuous_monitoring(self):
        """Continuously monitor for suspicious activities"""
        self.is_monitoring = True
        self.logger.info("Started AML continuous monitoring")
        
        while self.is_monitoring:
            try:
                # Monitor various aspects
                await self._monitor_transaction_patterns()
                await self._monitor_velocity_rules()
                await self._monitor_behavioral_changes()
                
                # Wait before next cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in AML monitoring: {str(e)}")
                await asyncio.sleep(30)
                
    async def _monitor_transaction_patterns(self):
        """Monitor for suspicious transaction patterns"""
        # In production, analyze real transaction data
        # Mock pattern detection
        
        # Structuring pattern
        structuring_detected = np.random.random() < 0.05  # 5% chance
        if structuring_detected:
            alert = AMLAlert(
                alert_type="structuring",
                severity=AlertSeverity.HIGH,
                title="Potential Structuring Detected",
                description="Multiple transactions just below reporting threshold",
                trigger_rules=["structuring_detection"],
                suspicious_factors=[
                    "5 transactions of $9,900 within 24 hours",
                    "Total amount: $49,500",
                    "All cash deposits"
                ],
                transaction_ids=["tx_001", "tx_002", "tx_003", "tx_004", "tx_005"],
                total_amount=Decimal("49500")
            )
            
            self.alerts[alert.alert_id] = alert
            self.logger.warning(f"Structuring alert created: {alert.alert_id}")
            
    async def _monitor_velocity_rules(self):
        """Monitor transaction velocity"""
        # Rapid movement of funds
        rapid_movement = np.random.random() < 0.03  # 3% chance
        if rapid_movement:
            alert = AMLAlert(
                alert_type="rapid_movement",
                severity=AlertSeverity.MEDIUM,
                title="Rapid Fund Movement Detected",
                description="Funds moved through account unusually quickly",
                trigger_rules=["velocity_rule"],
                suspicious_factors=[
                    "Deposit and withdrawal within 1 hour",
                    "90% of deposit amount withdrawn",
                    "Different withdrawal method"
                ],
                total_amount=Decimal("25000")
            )
            
            self.alerts[alert.alert_id] = alert
            
    async def _monitor_behavioral_changes(self):
        """Monitor for behavioral changes"""
        # Sudden change in transaction behavior
        behavior_change = np.random.random() < 0.02  # 2% chance
        if behavior_change:
            alert = AMLAlert(
                user_id="user_123",  # Mock user
                alert_type="behavior_change",
                severity=AlertSeverity.MEDIUM,
                title="Significant Behavioral Change",
                description="User's transaction pattern changed significantly",
                trigger_rules=["behavior_analysis"],
                suspicious_factors=[
                    "Transaction volume increased 500%",
                    "New geographic locations",
                    "Different transaction types"
                ]
            )
            
            self.alerts[alert.alert_id] = alert
            
    async def create_alert(
        self,
        activity: SuspiciousActivity,
        reporter_id: Optional[str] = None
    ) -> AMLAlert:
        """Create alert from suspicious activity report"""
        # Determine severity based on activity
        severity = self._determine_severity(activity)
        
        alert = AMLAlert(
            user_id=activity.user_ids[0] if activity.user_ids else None,
            alert_type="suspicious_activity_report",
            severity=severity,
            title=f"Suspicious Activity: {activity.activity_type}",
            description=activity.description,
            trigger_rules=["manual_report"],
            suspicious_factors=activity.red_flags,
            transaction_ids=activity.transaction_ids,
            total_amount=activity.amount,
            investigation_notes=[
                f"Reported by: {reporter_id or 'system'}",
                f"Pattern: {activity.pattern_detected}"
            ] if activity.pattern_detected else []
        )
        
        self.alerts[alert.alert_id] = alert
        
        self.logger.info(f"Created alert {alert.alert_id} from suspicious activity report")
        
        return alert
        
    def _determine_severity(self, activity: SuspiciousActivity) -> AlertSeverity:
        """Determine alert severity from suspicious activity"""
        # High severity indicators
        high_severity_indicators = [
            "terrorism", "sanctions", "large_amount", "multiple_accounts"
        ]
        
        # Check red flags
        for flag in activity.red_flags:
            if any(indicator in flag.lower() for indicator in high_severity_indicators):
                return AlertSeverity.HIGH
                
        # Check amount
        if activity.amount and activity.amount > Decimal("100000"):
            return AlertSeverity.HIGH
        elif activity.amount and activity.amount > Decimal("50000"):
            return AlertSeverity.MEDIUM
            
        return AlertSeverity.LOW
        
    async def investigate_activity(self, alert: AMLAlert):
        """Investigate suspicious activity"""
        self.logger.info(f"Investigating alert {alert.alert_id}")
        
        alert.status = "investigating"
        alert.updated_at = datetime.now()
        
        # In production, this would:
        # - Gather additional transaction data
        # - Run advanced analytics
        # - Check against known patterns
        # - Generate investigation report
        
        # Mock investigation
        await asyncio.sleep(10)
        
        # Add investigation notes
        alert.investigation_notes.append(
            f"Investigation completed at {datetime.now().isoformat()}"
        )
        alert.investigation_notes.append(
            "Pattern analysis: Confirmed suspicious pattern"
        )
        
        # Escalate high severity alerts
        if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            alert.status = "escalated"
            alert.investigation_notes.append(
                "Escalated to compliance team for review"
            )
            
    async def create_transaction_alert(
        self,
        user_id: str,
        transaction: Dict[str, Any],
        violations: List[Any]
    ) -> AMLAlert:
        """Create alert from transaction screening"""
        alert = AMLAlert(
            user_id=user_id,
            alert_type="transaction_violation",
            severity=AlertSeverity.HIGH,
            title="Transaction Compliance Violation",
            description=f"Transaction failed compliance checks",
            trigger_rules=[v.rule_id for v in violations],
            suspicious_factors=[v.description for v in violations],
            transaction_ids=[transaction.get("id", "unknown")],
            total_amount=Decimal(str(transaction.get("amount", 0)))
        )
        
        self.alerts[alert.alert_id] = alert
        
        return alert
        
    async def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        since: Optional[datetime] = None
    ) -> List[AMLAlert]:
        """Get AML alerts"""
        alerts = list(self.alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
            
        if since:
            alerts = [a for a in alerts if a.created_at >= since]
            
        # Sort by created date descending
        alerts.sort(key=lambda a: a.created_at, reverse=True)
        
        return alerts
        
    async def screen_sanctions(
        self,
        name: str,
        country: Optional[str] = None
    ) -> SanctionsScreeningResult:
        """Screen against sanctions lists"""
        self.logger.info(f"Screening sanctions for: {name}")
        
        # In production, check against:
        # - OFAC SDN List
        # - UN Sanctions List
        # - EU Consolidated List
        # - UK HM Treasury List
        # - Local sanctions lists
        
        # Mock screening
        sanctioned_names = ["osama", "kim jong", "putin"]
        sanctioned_countries = ["IR", "KP", "SY", "CU", "VE"]
        
        matches = []
        risk_level = "none"
        
        # Name matching (simplified)
        name_lower = name.lower()
        for sanctioned in sanctioned_names:
            if sanctioned in name_lower:
                matches.append({
                    "list": "OFAC SDN",
                    "name": sanctioned,
                    "match_score": 0.9,
                    "details": "Name match found"
                })
                risk_level = "critical"
                
        # Country check
        if country and country in sanctioned_countries:
            matches.append({
                "list": "Country Sanctions",
                "country": country,
                "match_score": 1.0,
                "details": "Sanctioned country"
            })
            risk_level = "critical"
            
        # Determine action
        if risk_level == "critical":
            recommended_action = "Block transaction and report"
        elif risk_level == "high":
            recommended_action = "Enhanced due diligence required"
        else:
            recommended_action = "Proceed with standard checks"
            
        result = SanctionsScreeningResult(
            search_name=name,
            search_country=country,
            matches_found=len(matches) > 0,
            match_count=len(matches),
            matches=matches,
            risk_level=risk_level,
            recommended_action=recommended_action,
            lists_checked=[
                "OFAC SDN",
                "UN Sanctions",
                "EU Consolidated",
                "UK HM Treasury"
            ]
        )
        
        return result
        
    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution: str,
        action_taken: str
    ) -> bool:
        """Resolve an AML alert"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
            
        alert.status = "resolved"
        alert.resolution = resolution
        alert.action_taken = action_taken
        alert.resolved_at = datetime.now()
        alert.updated_at = datetime.now()
        
        # Determine if false positive
        alert.false_positive = "false positive" in resolution.lower()
        
        # Add resolution note
        alert.investigation_notes.append(
            f"Resolved by {resolved_by}: {resolution}"
        )
        
        self.logger.info(f"Alert {alert_id} resolved: {resolution}")
        
        return True
        
    async def generate_sar(self, alert_id: str) -> Dict[str, Any]:
        """Generate Suspicious Activity Report"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return {"error": "Alert not found"}
            
        # In production, generate actual SAR form
        # Following FinCEN requirements
        
        sar = {
            "report_type": "Suspicious Activity Report",
            "filing_institution": "Oryza Financial",
            "alert_id": alert_id,
            "alert_details": {
                "type": alert.alert_type,
                "severity": alert.severity.value,
                "description": alert.description,
                "total_amount": str(alert.total_amount) if alert.total_amount else None
            },
            "suspicious_activity": {
                "date_range": {
                    "start": (alert.created_at - timedelta(days=30)).isoformat(),
                    "end": alert.created_at.isoformat()
                },
                "suspicious_factors": alert.suspicious_factors,
                "transaction_count": len(alert.transaction_ids)
            },
            "subject_information": {
                "user_id": alert.user_id,
                "account_numbers": alert.transaction_ids[:5]  # Mock
            },
            "narrative": self._generate_sar_narrative(alert),
            "filing_date": datetime.now().isoformat()
        }
        
        return sar
        
    def _generate_sar_narrative(self, alert: AMLAlert) -> str:
        """Generate SAR narrative"""
        narrative = f"""
        Suspicious Activity Report
        
        Alert Type: {alert.alert_type}
        Date: {alert.created_at.strftime('%Y-%m-%d')}
        
        Description:
        {alert.description}
        
        Suspicious Factors:
        {chr(10).join(f'- {factor}' for factor in alert.suspicious_factors)}
        
        Investigation Notes:
        {chr(10).join(f'- {note}' for note in alert.investigation_notes)}
        
        Action Taken:
        {alert.action_taken or 'Pending review'}
        """
        
        return narrative.strip()
        
    async def get_alert_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get AML alert statistics"""
        since = datetime.now() - timedelta(days=days)
        recent_alerts = [
            a for a in self.alerts.values()
            if a.created_at >= since
        ]
        
        # Calculate statistics
        total_alerts = len(recent_alerts)
        by_severity = {}
        by_type = {}
        by_status = {}
        
        for alert in recent_alerts:
            # By severity
            severity = alert.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # By type
            alert_type = alert.alert_type
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
            
            # By status
            status = alert.status
            by_status[status] = by_status.get(status, 0) + 1
            
        # False positive rate
        resolved_alerts = [a for a in recent_alerts if a.status == "resolved"]
        false_positives = [a for a in resolved_alerts if a.false_positive]
        false_positive_rate = (
            len(false_positives) / len(resolved_alerts)
            if resolved_alerts else 0
        )
        
        return {
            "period_days": days,
            "total_alerts": total_alerts,
            "by_severity": by_severity,
            "by_type": by_type,
            "by_status": by_status,
            "false_positive_rate": false_positive_rate,
            "avg_resolution_time_hours": 24.5,  # Mock
            "alerts_per_day": total_alerts / days if days > 0 else 0
        }
        
    async def shutdown(self):
        """Shutdown AML monitor"""
        self.is_monitoring = False
        self.logger.info("AML Monitor shutdown complete") 