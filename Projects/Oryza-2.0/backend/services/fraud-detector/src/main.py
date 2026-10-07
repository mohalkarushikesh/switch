"""
Fraud Detector - AI-powered fraud detection and prevention
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
from shared.database.models import User
from shared.utils.logger import ServiceLogger
from shared.utils.auth import get_current_verified_user

# Import fraud detector modules
from .fraud_detector import FraudDetector
from .pattern_analyzer import PatternAnalyzer
from .ml_scorer import MLScorer
from .rule_engine import RuleEngine
from .models import (
    Transaction, TransactionType, TransactionStatus,
    FraudCheck, FraudScore, RiskLevel,
    FraudAlert, AlertSeverity, AlertStatus,
    UserBehavior, BehaviorPattern,
    FraudRule, RuleType, RuleAction,
    Investigation, InvestigationStatus,
    BlockList, BlockType,
    FraudStats, DetectionMetrics
)

settings = get_settings()
fraud_logger = ServiceLogger("fraud-detector")
logger = fraud_logger.get_logger()

# Global instances
fraud_detector = None
pattern_analyzer = None
ml_scorer = None
rule_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global fraud_detector, pattern_analyzer, ml_scorer, rule_engine
    
    # Startup
    logger.info("Starting Fraud Detector Service")
    await init_databases()
    
    # Initialize components
    rule_engine = RuleEngine()
    ml_scorer = MLScorer()
    pattern_analyzer = PatternAnalyzer()
    fraud_detector = FraudDetector(rule_engine, ml_scorer, pattern_analyzer)
    
    await asyncio.gather(
        rule_engine.initialize(),
        ml_scorer.initialize(),
        pattern_analyzer.initialize(),
        fraud_detector.initialize()
    )
    
    # Start real-time monitoring
    asyncio.create_task(fraud_detector.start_monitoring())
    
    logger.info("Fraud Detector Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fraud Detector Service")
    await fraud_detector.shutdown()
    await close_databases()


# Create FastAPI app
app = FastAPI(
    title="Fraud Detector Service",
    description="AI-powered fraud detection and prevention",
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
        "service": "Fraud Detector",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "Real-time transaction monitoring",
            "ML-based fraud scoring",
            "Pattern recognition",
            "Rule-based detection",
            "Behavioral analysis",
            "Alert generation",
            "Investigation management",
            "Block list management"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "fraud_detector": "ready" if fraud_detector else "not initialized",
            "pattern_analyzer": "ready" if pattern_analyzer else "not initialized",
            "ml_scorer": "ready" if ml_scorer else "not initialized",
            "rule_engine": "ready" if rule_engine else "not initialized"
        },
        "monitoring_active": fraud_detector.is_monitoring if fraud_detector else False
    }


@app.post("/transactions/check", response_model=FraudCheck)
async def check_transaction(
    transaction: Transaction,
    background_tasks: BackgroundTasks
):
    """Check a transaction for fraud"""
    try:
        # Perform fraud check
        fraud_check = await fraud_detector.check_transaction(transaction)
        
        # If high risk, create investigation in background
        if fraud_check.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            background_tasks.add_task(
                fraud_detector.create_investigation,
                transaction,
                fraud_check
            )
            
        return fraud_check
        
    except Exception as e:
        logger.error(f"Error checking transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check transaction: {str(e)}"
        )


@app.post("/transactions/batch-check")
async def batch_check_transactions(
    transactions: List[Transaction],
    background_tasks: BackgroundTasks
) -> List[FraudCheck]:
    """Check multiple transactions for fraud"""
    try:
        # Process in batches for efficiency
        fraud_checks = await fraud_detector.batch_check_transactions(transactions)
        
        # Create investigations for high-risk transactions
        high_risk_checks = [
            (t, fc) for t, fc in zip(transactions, fraud_checks)
            if fc.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
        
        for transaction, fraud_check in high_risk_checks:
            background_tasks.add_task(
                fraud_detector.create_investigation,
                transaction,
                fraud_check
            )
            
        return fraud_checks
        
    except Exception as e:
        logger.error(f"Error batch checking transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch check: {str(e)}"
        )


@app.get("/score/{transaction_id}", response_model=FraudScore)
async def get_fraud_score(transaction_id: str):
    """Get detailed fraud score for a transaction"""
    try:
        score = await fraud_detector.get_fraud_score(transaction_id)
        
        if not score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
            
        return score
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fraud score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch score: {str(e)}"
        )


@app.post("/transactions/{transaction_id}/review")
async def review_transaction(
    transaction_id: str,
    decision: str,  # "approve", "reject", "investigate"
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_verified_user)
):
    """Manually review a flagged transaction"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        result = await fraud_detector.review_transaction(
            transaction_id=transaction_id,
            reviewer_id=str(current_user.id),
            decision=decision,
            notes=notes
        )
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "decision": decision,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review transaction: {str(e)}"
        )


@app.get("/alerts", response_model=List[FraudAlert])
async def get_fraud_alerts(
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_verified_user)
):
    """Get fraud alerts"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            # Regular users can only see their own alerts
            user_id = str(current_user.id)
            
        alerts = await fraud_detector.get_alerts(
            status=status,
            severity=severity,
            user_id=user_id,
            limit=limit
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {str(e)}"
        )


@app.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Acknowledge a fraud alert"""
    try:
        success = await fraud_detector.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
            
        return {"status": "success", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@app.get("/behavior/{user_id}", response_model=UserBehavior)
async def get_user_behavior(
    user_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get user behavior profile"""
    try:
        # Check permissions
        if str(current_user.id) != user_id:
            if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access other users' behavior"
                )
                
        behavior = await pattern_analyzer.get_user_behavior(user_id)
        
        if not behavior:
            # Return default behavior if none exists
            behavior = UserBehavior(
                user_id=user_id,
                typical_transaction_amount=Decimal("100"),
                typical_transaction_frequency=5,
                common_merchants=[],
                common_locations=[],
                device_fingerprints=[],
                risk_score=0
            )
            
        return behavior
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching behavior: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch behavior: {str(e)}"
        )


@app.get("/patterns/anomalies")
async def get_anomalies(
    time_window_hours: int = 24,
    min_severity: float = 0.7,
    current_user: User = Depends(get_current_verified_user)
):
    """Get detected anomalies"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        anomalies = await pattern_analyzer.get_anomalies(
            time_window_hours=time_window_hours,
            min_severity=min_severity
        )
        
        return anomalies
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching anomalies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch anomalies: {str(e)}"
        )


@app.get("/rules", response_model=List[FraudRule])
async def get_fraud_rules(
    rule_type: Optional[RuleType] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_verified_user)
):
    """Get fraud detection rules"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        rules = await rule_engine.get_rules(
            rule_type=rule_type,
            active_only=active_only
        )
        
        return rules
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rules: {str(e)}"
        )


@app.post("/rules", response_model=FraudRule)
async def create_fraud_rule(
    rule: FraudRule,
    current_user: User = Depends(get_current_verified_user)
):
    """Create a new fraud detection rule"""
    try:
        # Check permissions
        if "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )
            
        # Set creator
        rule.created_by = str(current_user.id)
        
        created_rule = await rule_engine.create_rule(rule)
        
        return created_rule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}"
        )


@app.put("/rules/{rule_id}")
async def update_fraud_rule(
    rule_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_verified_user)
):
    """Update a fraud detection rule"""
    try:
        # Check permissions
        if "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )
            
        success = await rule_engine.update_rule(rule_id, updates)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
            
        return {"status": "success", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rule: {str(e)}"
        )


@app.delete("/rules/{rule_id}")
async def delete_fraud_rule(
    rule_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Delete a fraud detection rule"""
    try:
        # Check permissions
        if "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )
            
        success = await rule_engine.delete_rule(rule_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
            
        return {"status": "success", "message": "Rule deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rule: {str(e)}"
        )


@app.get("/investigations", response_model=List[Investigation])
async def get_investigations(
    status: Optional[InvestigationStatus] = None,
    assigned_to: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_verified_user)
):
    """Get fraud investigations"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        investigations = await fraud_detector.get_investigations(
            status=status,
            assigned_to=assigned_to,
            limit=limit
        )
        
        return investigations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching investigations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch investigations: {str(e)}"
        )


@app.post("/investigations/{investigation_id}/update")
async def update_investigation(
    investigation_id: str,
    status: InvestigationStatus,
    findings: Optional[str] = None,
    action_taken: Optional[str] = None,
    current_user: User = Depends(get_current_verified_user)
):
    """Update investigation status"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        success = await fraud_detector.update_investigation(
            investigation_id=investigation_id,
            investigator_id=str(current_user.id),
            status=status,
            findings=findings,
            action_taken=action_taken
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investigation not found"
            )
            
        return {
            "status": "success",
            "investigation_id": investigation_id,
            "new_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating investigation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update investigation: {str(e)}"
        )


@app.get("/blocklist", response_model=List[BlockList])
async def get_blocklist(
    block_type: Optional[BlockType] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_verified_user)
):
    """Get block list entries"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        entries = await fraud_detector.get_blocklist(
            block_type=block_type,
            active_only=active_only
        )
        
        return entries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blocklist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch blocklist: {str(e)}"
        )


@app.post("/blocklist", response_model=BlockList)
async def add_to_blocklist(
    entry: BlockList,
    current_user: User = Depends(get_current_verified_user)
):
    """Add entry to block list"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        # Set creator
        entry.added_by = str(current_user.id)
        
        created_entry = await fraud_detector.add_to_blocklist(entry)
        
        return created_entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to blocklist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to blocklist: {str(e)}"
        )


@app.delete("/blocklist/{entry_id}")
async def remove_from_blocklist(
    entry_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Remove entry from block list"""
    try:
        # Check permissions
        if "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )
            
        success = await fraud_detector.remove_from_blocklist(entry_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry not found"
            )
            
        return {"status": "success", "message": "Entry removed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from blocklist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from blocklist: {str(e)}"
        )


@app.get("/stats", response_model=FraudStats)
async def get_fraud_stats(
    period: str = "24h",  # 1h, 24h, 7d, 30d
    current_user: User = Depends(get_current_verified_user)
):
    """Get fraud detection statistics"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        stats = await fraud_detector.get_statistics(period)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


@app.get("/metrics", response_model=DetectionMetrics)
async def get_detection_metrics(
    current_user: User = Depends(get_current_verified_user)
):
    """Get fraud detection performance metrics"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        metrics = await fraud_detector.get_detection_metrics()
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )


@app.post("/ml/retrain")
async def retrain_ml_model(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user)
):
    """Trigger ML model retraining"""
    try:
        # Check permissions
        if "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )
            
        # Queue retraining
        background_tasks.add_task(ml_scorer.retrain_model)
        
        return {
            "status": "success",
            "message": "Model retraining queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retraining: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger retraining: {str(e)}"
        )


@app.get("/ml/performance")
async def get_ml_performance(
    current_user: User = Depends(get_current_verified_user)
):
    """Get ML model performance metrics"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        performance = await ml_scorer.get_model_performance()
        
        return performance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ML performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance: {str(e)}"
        )


@app.post("/report/generate")
async def generate_fraud_report(
    report_type: str = "summary",  # summary, detailed, investigation
    time_period: str = "7d",
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user)
):
    """Generate fraud detection report"""
    try:
        # Check permissions
        if "fraud_analyst" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fraud analyst role required"
            )
            
        # Queue report generation
        report_id = f"fraud_report_{datetime.now().timestamp()}"
        
        background_tasks.add_task(
            fraud_detector.generate_report,
            report_id,
            report_type,
            time_period,
            str(current_user.id)
        )
        
        return {
            "status": "generating",
            "report_id": report_id,
            "message": "Report generation queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8017,
        reload=True
    ) 