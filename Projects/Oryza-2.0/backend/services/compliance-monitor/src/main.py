"""
Compliance Monitor - Regulatory compliance and risk monitoring
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.settings import get_settings
from shared.database.connection import init_databases, close_databases, get_db, get_redis
from shared.database.models import User, Transaction
from shared.utils.logger import ServiceLogger
from shared.utils.auth import get_current_verified_user, get_current_admin_user

# Import compliance modules
from .compliance_engine import ComplianceEngine
from .kyc_manager import KYCManager
from .aml_monitor import AMLMonitor
from .regulatory_reporter import RegulatoryReporter
from .models import (
    ComplianceCheck, ComplianceStatus, ComplianceType,
    KYCRequest, KYCStatus, KYCResult,
    AMLAlert, AlertSeverity, SuspiciousActivity,
    RegulatoryReport, ReportType, Jurisdiction,
    ComplianceRule, RuleViolation, RiskScore,
    AuditLog, ComplianceMetrics
)

settings = get_settings()
compliance_logger = ServiceLogger("compliance-monitor")
logger = compliance_logger.get_logger()

# Global instances
compliance_engine = None
kyc_manager = None
aml_monitor = None
regulatory_reporter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global compliance_engine, kyc_manager, aml_monitor, regulatory_reporter
    
    # Startup
    logger.info("Starting Compliance Monitor Service")
    await init_databases()
    
    # Initialize components
    compliance_engine = ComplianceEngine()
    kyc_manager = KYCManager()
    aml_monitor = AMLMonitor()
    regulatory_reporter = RegulatoryReporter()
    
    await asyncio.gather(
        compliance_engine.initialize(),
        kyc_manager.initialize(),
        aml_monitor.initialize(),
        regulatory_reporter.initialize()
    )
    
    # Start background monitoring
    asyncio.create_task(aml_monitor.continuous_monitoring())
    asyncio.create_task(compliance_engine.rule_monitoring())
    
    logger.info("Compliance Monitor Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Compliance Monitor Service")
    await aml_monitor.shutdown()
    await compliance_engine.shutdown()
    await close_databases()


# Create FastAPI app
app = FastAPI(
    title="Compliance Monitor Service",
    description="Regulatory compliance, KYC/AML, and risk monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Compliance Monitor",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "KYC verification",
            "AML monitoring",
            "Transaction screening",
            "Regulatory reporting",
            "Risk scoring",
            "Audit logging"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "compliance_engine": "ready" if compliance_engine else "not initialized",
            "kyc_manager": "ready" if kyc_manager else "not initialized",
            "aml_monitor": "ready" if aml_monitor else "not initialized",
            "regulatory_reporter": "ready" if regulatory_reporter else "not initialized"
        },
        "monitoring_active": {
            "aml": aml_monitor.is_monitoring if aml_monitor else False,
            "rules": compliance_engine.is_monitoring if compliance_engine else False
        }
    }


@app.post("/kyc/verify")
async def verify_kyc(
    request: KYCRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user)
) -> KYCResult:
    """
    Initiate KYC verification
    
    Performs identity verification and compliance checks
    """
    try:
        # Check if already verified
        existing = await kyc_manager.get_kyc_status(str(current_user.id))
        if existing and existing.status == KYCStatus.VERIFIED:
            return existing
            
        # Initiate verification
        result = await kyc_manager.verify_identity(
            user_id=str(current_user.id),
            request=request
        )
        
        # If additional verification needed, process in background
        if result.status == KYCStatus.PENDING:
            background_tasks.add_task(
                kyc_manager.complete_verification,
                str(current_user.id),
                result.verification_id
            )
            
        return result
        
    except Exception as e:
        logger.error(f"KYC verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KYC verification failed: {str(e)}"
        )


@app.get("/kyc/status")
async def get_kyc_status(
    current_user: User = Depends(get_current_verified_user)
) -> KYCResult:
    """Get current KYC status"""
    try:
        result = await kyc_manager.get_kyc_status(str(current_user.id))
        
        if not result:
            return KYCResult(
                user_id=str(current_user.id),
                status=KYCStatus.NOT_STARTED,
                verification_id="",
                checks_passed=[],
                checks_failed=[],
                risk_score=0.0,
                verified_at=None
            )
            
        return result
        
    except Exception as e:
        logger.error(f"Error fetching KYC status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch KYC status: {str(e)}"
        )


@app.post("/compliance/check")
async def run_compliance_check(
    check_type: ComplianceType,
    transaction_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_verified_user)
) -> ComplianceCheck:
    """
    Run compliance check
    
    Performs various compliance checks based on type
    """
    try:
        check = await compliance_engine.run_check(
            user_id=str(current_user.id),
            check_type=check_type,
            data=transaction_data
        )
        
        return check
        
    except Exception as e:
        logger.error(f"Compliance check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check failed: {str(e)}"
        )


@app.get("/compliance/history")
async def get_compliance_history(
    check_type: Optional[ComplianceType] = None,
    days: int = 30,
    current_user: User = Depends(get_current_verified_user)
) -> List[ComplianceCheck]:
    """Get compliance check history"""
    try:
        since = datetime.now() - timedelta(days=days)
        
        history = await compliance_engine.get_user_compliance_history(
            user_id=str(current_user.id),
            check_type=check_type,
            since=since
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error fetching compliance history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch compliance history: {str(e)}"
        )


@app.get("/aml/alerts")
async def get_aml_alerts(
    severity: Optional[AlertSeverity] = None,
    days: int = 7,
    current_user: User = Depends(get_current_admin_user)
) -> List[AMLAlert]:
    """
    Get AML alerts (admin only)
    
    Returns suspicious activity alerts
    """
    try:
        since = datetime.now() - timedelta(days=days)
        
        alerts = await aml_monitor.get_alerts(
            severity=severity,
            since=since
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error fetching AML alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch AML alerts: {str(e)}"
        )


@app.post("/aml/report-suspicious")
async def report_suspicious_activity(
    activity: SuspiciousActivity,
    current_user: User = Depends(get_current_verified_user)
):
    """Report suspicious activity"""
    try:
        # Create alert
        alert = await aml_monitor.create_alert(
            activity=activity,
            reporter_id=str(current_user.id)
        )
        
        # Investigate in background
        asyncio.create_task(
            aml_monitor.investigate_activity(alert)
        )
        
        return {
            "status": "reported",
            "alert_id": alert.alert_id,
            "message": "Suspicious activity reported and under investigation"
        }
        
    except Exception as e:
        logger.error(f"Error reporting suspicious activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report activity: {str(e)}"
        )


@app.post("/transaction/screen")
async def screen_transaction(
    transaction: Dict[str, Any],
    current_user: User = Depends(get_current_verified_user)
) -> ComplianceCheck:
    """
    Screen transaction for compliance
    
    Pre-transaction compliance screening
    """
    try:
        # Run transaction screening
        check = await compliance_engine.screen_transaction(
            user_id=str(current_user.id),
            transaction=transaction
        )
        
        # If failed, create alert
        if check.status == ComplianceStatus.FAILED:
            await aml_monitor.create_transaction_alert(
                user_id=str(current_user.id),
                transaction=transaction,
                violations=check.violations
            )
            
        return check
        
    except Exception as e:
        logger.error(f"Transaction screening error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction screening failed: {str(e)}"
        )


@app.get("/risk-score")
async def get_risk_score(
    current_user: User = Depends(get_current_verified_user)
) -> RiskScore:
    """Get user's compliance risk score"""
    try:
        score = await compliance_engine.calculate_risk_score(
            user_id=str(current_user.id)
        )
        
        return score
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate risk score: {str(e)}"
        )


@app.get("/rules")
async def get_compliance_rules(
    jurisdiction: Optional[Jurisdiction] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_admin_user)
) -> List[ComplianceRule]:
    """Get compliance rules (admin only)"""
    try:
        rules = await compliance_engine.get_rules(
            jurisdiction=jurisdiction,
            active_only=active_only
        )
        
        return rules
        
    except Exception as e:
        logger.error(f"Error fetching compliance rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rules: {str(e)}"
        )


@app.post("/rules")
async def create_compliance_rule(
    rule: ComplianceRule,
    current_user: User = Depends(get_current_admin_user)
):
    """Create new compliance rule (admin only)"""
    try:
        created_rule = await compliance_engine.create_rule(rule)
        
        return {
            "status": "created",
            "rule_id": created_rule.rule_id,
            "message": "Compliance rule created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating compliance rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}"
        )


@app.get("/reports/regulatory")
async def get_regulatory_reports(
    report_type: Optional[ReportType] = None,
    jurisdiction: Optional[Jurisdiction] = None,
    days: int = 90,
    current_user: User = Depends(get_current_admin_user)
) -> List[RegulatoryReport]:
    """Get regulatory reports (admin only)"""
    try:
        since = datetime.now() - timedelta(days=days)
        
        reports = await regulatory_reporter.get_reports(
            report_type=report_type,
            jurisdiction=jurisdiction,
            since=since
        )
        
        return reports
        
    except Exception as e:
        logger.error(f"Error fetching regulatory reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports: {str(e)}"
        )


@app.post("/reports/generate")
async def generate_regulatory_report(
    report_type: ReportType,
    jurisdiction: Jurisdiction,
    period_start: datetime,
    period_end: datetime,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """Generate regulatory report (admin only)"""
    try:
        # Generate report in background
        report_id = await regulatory_reporter.initiate_report(
            report_type=report_type,
            jurisdiction=jurisdiction,
            period_start=period_start,
            period_end=period_end
        )
        
        background_tasks.add_task(
            regulatory_reporter.generate_report,
            report_id
        )
        
        return {
            "status": "generating",
            "report_id": report_id,
            "message": "Report generation initiated"
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@app.get("/audit-log")
async def get_audit_log(
    event_type: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
) -> List[AuditLog]:
    """Get audit log (admin only)"""
    try:
        since = datetime.now() - timedelta(days=days)
        
        logs = await compliance_engine.get_audit_logs(
            event_type=event_type,
            since=since,
            limit=limit
        )
        
        return logs
        
    except Exception as e:
        logger.error(f"Error fetching audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit logs: {str(e)}"
        )


@app.get("/metrics")
async def get_compliance_metrics(
    days: int = 30,
    current_user: User = Depends(get_current_admin_user)
) -> ComplianceMetrics:
    """Get compliance metrics (admin only)"""
    try:
        metrics = await compliance_engine.calculate_metrics(days=days)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate metrics: {str(e)}"
        )


@app.post("/sanctions/screen")
async def screen_sanctions(
    name: str,
    country: Optional[str] = None,
    current_user: User = Depends(get_current_verified_user)
):
    """Screen against sanctions lists"""
    try:
        result = await aml_monitor.screen_sanctions(
            name=name,
            country=country
        )
        
        # Log the screening
        await compliance_engine.log_audit_event(
            event_type="sanctions_screening",
            user_id=str(current_user.id),
            details={
                "name": name,
                "country": country,
                "result": result
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Sanctions screening error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sanctions screening failed: {str(e)}"
        )


@app.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution: str,
    action_taken: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Resolve an AML alert (admin only)"""
    try:
        success = await aml_monitor.resolve_alert(
            alert_id=alert_id,
            resolved_by=str(current_user.id),
            resolution=resolution,
            action_taken=action_taken
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
            
        return {
            "status": "resolved",
            "alert_id": alert_id,
            "message": "Alert resolved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}"
        )


@app.post("/training/complete")
async def complete_compliance_training(
    training_module: str,
    score: float,
    current_user: User = Depends(get_current_verified_user)
):
    """Record compliance training completion"""
    try:
        await compliance_engine.record_training(
            user_id=str(current_user.id),
            module=training_module,
            score=score,
            completed_at=datetime.now()
        )
        
        return {
            "status": "recorded",
            "module": training_module,
            "score": score,
            "message": "Training completion recorded"
        }
        
    except Exception as e:
        logger.error(f"Error recording training: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record training: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8009,
        reload=True
    )
