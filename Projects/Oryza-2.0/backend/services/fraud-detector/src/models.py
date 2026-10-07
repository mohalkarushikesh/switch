"""
Data models for Fraud Detector Service
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid


class TransactionType(str, Enum):
    PAYMENT = "payment"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    PURCHASE = "purchase"
    REFUND = "refund"
    FEE = "fee"
    INTEREST = "interest"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    UNDER_REVIEW = "under_review"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class RuleType(str, Enum):
    AMOUNT_LIMIT = "amount_limit"
    VELOCITY = "velocity"
    LOCATION = "location"
    MERCHANT = "merchant"
    BEHAVIOR = "behavior"
    DEVICE = "device"
    TIME_BASED = "time_based"
    CUSTOM = "custom"


class RuleAction(str, Enum):
    FLAG = "flag"
    BLOCK = "block"
    REVIEW = "review"
    NOTIFY = "notify"
    CHALLENGE = "challenge"  # Request additional verification


class InvestigationStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    RESOLVED = "resolved"
    CLOSED = "closed"


class BlockType(str, Enum):
    USER = "user"
    CARD = "card"
    MERCHANT = "merchant"
    IP_ADDRESS = "ip_address"
    DEVICE = "device"
    EMAIL = "email"
    PHONE = "phone"


class Transaction(BaseModel):
    """Transaction to be checked for fraud"""
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Transaction details
    type: TransactionType
    amount: Decimal
    currency: str = "USD"
    
    # Parties involved
    sender_account: Optional[str] = None
    recipient_account: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    
    # Location data
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Device information
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    device_os: Optional[str] = None
    browser: Optional[str] = None
    
    # Card details (if applicable)
    card_number_masked: Optional[str] = None  # Last 4 digits only
    card_type: Optional[str] = None
    
    # Additional context
    description: Optional[str] = None
    reference_number: Optional[str] = None
    
    # Status
    status: TransactionStatus = TransactionStatus.PENDING
    
    # Timestamps
    initiated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


class FraudScore(BaseModel):
    """Detailed fraud score breakdown"""
    transaction_id: str
    
    # Overall score (0-100, higher = more likely fraud)
    overall_score: float = Field(ge=0, le=100)
    risk_level: RiskLevel
    
    # Component scores
    ml_score: float = Field(ge=0, le=100)
    rule_score: float = Field(ge=0, le=100)
    behavior_score: float = Field(ge=0, le=100)
    velocity_score: float = Field(ge=0, le=100)
    location_score: float = Field(ge=0, le=100)
    
    # Confidence
    confidence: float = Field(ge=0, le=1)
    
    # Contributing factors
    risk_factors: List[str]
    triggered_rules: List[str]
    anomalies: List[str]
    
    # Model details
    model_version: str
    scoring_timestamp: datetime = Field(default_factory=datetime.now)


class FraudCheck(BaseModel):
    """Result of fraud check"""
    check_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str
    
    # Decision
    is_fraudulent: bool
    risk_level: RiskLevel
    action_taken: str  # "approved", "blocked", "flagged_for_review"
    
    # Scoring
    fraud_score: FraudScore
    
    # Reasons
    reasons: List[str]
    triggered_rules: List[Dict[str, Any]]
    
    # Review requirements
    requires_manual_review: bool
    review_priority: str  # "low", "medium", "high", "urgent"
    
    # Additional checks performed
    checks_performed: List[str]
    
    # Response time
    check_duration_ms: int
    checked_at: datetime = Field(default_factory=datetime.now)


class FraudAlert(BaseModel):
    """Fraud alert notification"""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Alert details
    type: str  # "suspicious_activity", "rule_violation", "anomaly", etc.
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.NEW
    
    # Related entities
    user_id: Optional[str] = None
    transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None
    
    # Content
    title: str
    description: str
    details: Dict[str, Any]
    
    # Actions
    recommended_actions: List[str]
    automated_actions_taken: List[str] = []
    
    # Assignment
    assigned_to: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    # Resolution
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserBehavior(BaseModel):
    """User behavior profile"""
    user_id: str
    
    # Transaction patterns
    typical_transaction_amount: Decimal
    max_transaction_amount: Decimal
    typical_transaction_frequency: float  # Transactions per day
    
    # Common patterns
    common_merchants: List[str]
    common_transaction_types: List[TransactionType]
    common_locations: List[str]
    common_time_of_day: List[int]  # Hours 0-23
    
    # Device patterns
    known_devices: List[str]
    device_fingerprints: List[str]
    typical_ip_locations: List[str]
    
    # Velocity metrics
    max_daily_transactions: int
    max_daily_amount: Decimal
    max_hourly_transactions: int
    
    # Risk indicators
    failed_transaction_rate: float
    dispute_rate: float
    account_age_days: int
    
    # Scoring
    risk_score: float = Field(ge=0, le=100)
    trust_score: float = Field(ge=0, le=100)
    
    # Last update
    last_transaction_date: datetime
    profile_updated_at: datetime = Field(default_factory=datetime.now)


class BehaviorPattern(BaseModel):
    """Detected behavior pattern"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Pattern details
    pattern_type: str  # "spending", "location", "time", "merchant"
    description: str
    
    # Pattern data
    pattern_data: Dict[str, Any]
    confidence: float = Field(ge=0, le=1)
    
    # Anomaly detection
    is_anomaly: bool
    anomaly_score: float = Field(ge=0, le=100)
    
    # Time range
    observed_from: datetime
    observed_to: datetime
    occurrence_count: int
    
    # Status
    is_suspicious: bool
    requires_investigation: bool


class FraudRule(BaseModel):
    """Fraud detection rule"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Rule definition
    name: str
    description: str
    rule_type: RuleType
    
    # Conditions
    conditions: Dict[str, Any]  # Rule-specific conditions
    
    # Actions
    action: RuleAction
    risk_score_impact: float = Field(ge=0, le=100)
    
    # Configuration
    is_active: bool = True
    priority: int = Field(ge=1, le=10)  # 1 = highest
    
    # Effectiveness
    true_positive_count: int = 0
    false_positive_count: int = 0
    effectiveness_score: float = 0.0
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('conditions')
    def validate_conditions(cls, v, values):
        # Ensure conditions match rule type
        rule_type = values.get('rule_type')
        
        if rule_type == RuleType.AMOUNT_LIMIT:
            assert 'max_amount' in v or 'min_amount' in v, "Amount limit rule needs amount conditions"
        elif rule_type == RuleType.VELOCITY:
            assert 'time_window' in v and 'max_count' in v, "Velocity rule needs time window and count"
            
        return v


class Investigation(BaseModel):
    """Fraud investigation case"""
    investigation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Case details
    case_number: str
    title: str
    description: str
    priority: str  # "low", "medium", "high", "critical"
    
    # Related entities
    transaction_ids: List[str]
    user_id: str
    alert_ids: List[str] = []
    
    # Status
    status: InvestigationStatus = InvestigationStatus.OPEN
    
    # Assignment
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    
    # Investigation details
    findings: Optional[str] = None
    evidence: List[Dict[str, Any]] = []
    
    # Actions taken
    actions_taken: List[str] = []
    blocked_entities: List[str] = []
    
    # Resolution
    resolution: Optional[str] = None
    is_fraud_confirmed: Optional[bool] = None
    amount_recovered: Optional[Decimal] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None


class BlockList(BaseModel):
    """Block list entry"""
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Block details
    block_type: BlockType
    value: str  # The actual value being blocked
    
    # Reason
    reason: str
    related_investigation_id: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Validity
    expires_at: Optional[datetime] = None
    
    # Metadata
    added_by: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.now)
    
    # Statistics
    hit_count: int = 0
    last_hit_at: Optional[datetime] = None


class FraudStats(BaseModel):
    """Fraud detection statistics"""
    period: str  # "1h", "24h", "7d", "30d"
    
    # Transaction stats
    total_transactions: int
    total_amount: Decimal
    flagged_transactions: int
    flagged_amount: Decimal
    blocked_transactions: int
    blocked_amount: Decimal
    
    # Detection rates
    fraud_detection_rate: float  # Percentage
    false_positive_rate: float
    
    # Alert stats
    alerts_generated: int
    alerts_resolved: int
    avg_resolution_time_hours: float
    
    # Investigation stats
    investigations_opened: int
    investigations_closed: int
    fraud_confirmed_cases: int
    amount_recovered: Decimal
    
    # Rule effectiveness
    most_effective_rules: List[Dict[str, Any]]
    
    # Risk distribution
    risk_distribution: Dict[str, int]  # risk_level -> count
    
    # Top categories
    top_fraud_types: List[Dict[str, Any]]
    top_fraud_merchants: List[Dict[str, Any]]
    top_fraud_locations: List[Dict[str, Any]]
    
    # Performance
    avg_check_time_ms: float
    ml_model_accuracy: float
    
    calculated_at: datetime = Field(default_factory=datetime.now)


class DetectionMetrics(BaseModel):
    """Fraud detection performance metrics"""
    # Accuracy metrics
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    
    # Calculated metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    
    # ML model metrics
    ml_model_version: str
    ml_model_accuracy: float
    ml_model_auc: float  # Area under curve
    
    # Rule engine metrics
    active_rules: int
    rules_triggered_count: Dict[str, int]
    avg_rules_per_transaction: float
    
    # Performance metrics
    avg_scoring_time_ms: float
    p95_scoring_time_ms: float
    p99_scoring_time_ms: float
    
    # Coverage
    transactions_analyzed: int
    users_monitored: int
    merchants_monitored: int
    
    # Trends
    fraud_trend: str  # "increasing", "stable", "decreasing"
    detection_improvement: float  # Percentage improvement
    
    as_of: datetime = Field(default_factory=datetime.now)


class MLModelInfo(BaseModel):
    """ML model information"""
    model_id: str
    model_type: str  # "gradient_boost", "neural_network", "ensemble"
    version: str
    
    # Training info
    trained_at: datetime
    training_samples: int
    features_used: List[str]
    
    # Performance
    training_accuracy: float
    validation_accuracy: float
    test_accuracy: float
    
    # Deployment
    deployed_at: Optional[datetime] = None
    is_active: bool
    
    # Monitoring
    predictions_made: int
    last_prediction_at: Optional[datetime] = None
    drift_detected: bool = False 