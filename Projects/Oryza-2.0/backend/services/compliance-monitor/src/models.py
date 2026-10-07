"""
Data models for Compliance Monitor Service
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import uuid


class ComplianceType(str, Enum):
    KYC = "kyc"
    AML = "aml"
    TRANSACTION_LIMIT = "transaction_limit"
    SANCTIONS = "sanctions"
    PEP = "pep"  # Politically Exposed Person
    FATF = "fatf"  # Financial Action Task Force
    RISK_ASSESSMENT = "risk_assessment"
    REGULATORY = "regulatory"


class ComplianceStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    REVIEW_REQUIRED = "review_required"
    EXPIRED = "expired"


class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    DOCUMENTS_REQUIRED = "documents_required"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportType(str, Enum):
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    CURRENCY_TRANSACTION = "currency_transaction"
    QUARTERLY_COMPLIANCE = "quarterly_compliance"
    ANNUAL_AML = "annual_aml"
    REGULATORY_FILING = "regulatory_filing"
    AUDIT_REPORT = "audit_report"


class Jurisdiction(str, Enum):
    US = "US"
    EU = "EU"
    UK = "UK"
    INDIA = "IN"
    SINGAPORE = "SG"
    GLOBAL = "GLOBAL"


class DocumentType(str, Enum):
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    TAX_DOCUMENT = "tax_document"
    PROOF_OF_INCOME = "proof_of_income"


class KYCRequest(BaseModel):
    """KYC verification request"""
    # Personal information
    first_name: str
    last_name: str
    date_of_birth: date
    
    # Identification
    document_type: DocumentType
    document_number: str
    document_country: str
    document_expiry: Optional[date] = None
    
    # Address
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str
    
    # Additional info
    nationality: str
    occupation: str
    source_of_funds: str
    purpose_of_account: str
    
    # Risk factors
    is_pep: bool = False  # Politically Exposed Person
    pep_details: Optional[str] = None
    
    # Documents (base64 encoded)
    document_front: Optional[str] = None
    document_back: Optional[str] = None
    proof_of_address: Optional[str] = None
    selfie: Optional[str] = None


class KYCResult(BaseModel):
    """KYC verification result"""
    user_id: str
    verification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: KYCStatus
    
    # Verification checks
    checks_passed: List[str] = []
    checks_failed: List[str] = []
    
    # Risk assessment
    risk_score: float = Field(ge=0, le=100)
    risk_level: str = "low"  # low, medium, high
    
    # Details
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ComplianceCheck(BaseModel):
    """Compliance check result"""
    check_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    check_type: ComplianceType
    status: ComplianceStatus
    
    # Check details
    description: str
    details: Dict[str, Any] = {}
    
    # Violations
    violations: List[RuleViolation] = []
    
    # Risk assessment
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    
    # Actions
    required_actions: List[str] = []
    recommendations: List[str] = []
    
    # Metadata
    performed_at: datetime = Field(default_factory=datetime.now)
    performed_by: str = "system"
    expires_at: Optional[datetime] = None


class RuleViolation(BaseModel):
    """Compliance rule violation"""
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    description: str
    
    # Violation details
    expected_value: Any
    actual_value: Any
    
    # Context
    context: Dict[str, Any] = {}
    
    # Remediation
    remediation_required: bool = True
    remediation_steps: List[str] = []


class AMLAlert(BaseModel):
    """AML alert"""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    
    # Alert details
    alert_type: str  # suspicious_pattern, large_transaction, etc.
    severity: AlertSeverity
    title: str
    description: str
    
    # Triggering factors
    trigger_rules: List[str] = []
    suspicious_factors: List[str] = []
    
    # Transaction details (if applicable)
    transaction_ids: List[str] = []
    total_amount: Optional[Decimal] = None
    
    # Investigation
    status: str = "open"  # open, investigating, resolved, escalated
    assigned_to: Optional[str] = None
    investigation_notes: List[str] = []
    
    # Resolution
    resolution: Optional[str] = None
    action_taken: Optional[str] = None
    false_positive: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


class SuspiciousActivity(BaseModel):
    """Suspicious activity report"""
    activity_type: str
    description: str
    
    # Involved parties
    user_ids: List[str] = []
    account_ids: List[str] = []
    
    # Transaction details
    transaction_ids: List[str] = []
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    
    # Suspicious indicators
    red_flags: List[str] = []
    pattern_detected: Optional[str] = None
    
    # Supporting evidence
    evidence: List[Dict[str, Any]] = []
    
    # Reporter info
    reported_by: Optional[str] = None
    report_date: datetime = Field(default_factory=datetime.now)


class ComplianceRule(BaseModel):
    """Compliance rule definition"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str
    rule_type: ComplianceType
    
    # Rule definition
    description: str
    condition: str  # Expression to evaluate
    threshold: Optional[Any] = None
    
    # Applicability
    jurisdictions: List[Jurisdiction] = [Jurisdiction.GLOBAL]
    applies_to: List[str] = ["all"]  # user types
    
    # Actions
    severity: AlertSeverity
    auto_block: bool = False
    require_review: bool = True
    
    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str
    
    # References
    regulatory_reference: Optional[str] = None
    documentation_url: Optional[str] = None


class RiskScore(BaseModel):
    """User risk score"""
    user_id: str
    
    # Overall score
    overall_score: float = Field(ge=0, le=100)
    risk_level: str  # low, medium, high, very_high
    
    # Component scores
    kyc_score: float = Field(ge=0, le=100)
    transaction_score: float = Field(ge=0, le=100)
    behavior_score: float = Field(ge=0, le=100)
    country_score: float = Field(ge=0, le=100)
    
    # Risk factors
    risk_factors: List[Dict[str, Any]] = []
    
    # Monitoring level
    monitoring_level: str = "standard"  # standard, enhanced, intensive
    review_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    
    # History
    previous_score: Optional[float] = None
    score_trend: str = "stable"  # increasing, decreasing, stable
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.now)
    next_review: datetime


class RegulatoryReport(BaseModel):
    """Regulatory report"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: ReportType
    
    # Report details
    title: str
    description: str
    jurisdiction: Jurisdiction
    
    # Period
    period_start: datetime
    period_end: datetime
    
    # Content
    summary: Dict[str, Any]
    detailed_data: List[Dict[str, Any]] = []
    
    # Statistics
    total_transactions: int
    flagged_transactions: int
    alerts_generated: int
    alerts_resolved: int
    
    # Filing info
    filing_deadline: datetime
    filing_status: str = "draft"  # draft, review, submitted, accepted
    filing_reference: Optional[str] = None
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: str
    approved_by: Optional[str] = None
    submitted_at: Optional[datetime] = None


class AuditLog(BaseModel):
    """Compliance audit log entry"""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Event details
    event_type: str
    event_description: str
    
    # Actor
    user_id: Optional[str] = None
    system_id: Optional[str] = None
    ip_address: Optional[str] = None
    
    # Context
    entity_type: Optional[str] = None  # user, transaction, alert, etc.
    entity_id: Optional[str] = None
    
    # Changes
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    
    # Compliance relevance
    compliance_impact: Optional[str] = None
    requires_review: bool = False
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.now)


class ComplianceMetrics(BaseModel):
    """Compliance metrics dashboard"""
    period_days: int
    
    # KYC metrics
    kyc_verifications: int
    kyc_approved: int
    kyc_rejected: int
    kyc_pending: int
    kyc_approval_rate: float
    avg_kyc_time_hours: float
    
    # AML metrics
    transactions_screened: int
    suspicious_transactions: int
    aml_alerts_generated: int
    aml_alerts_resolved: int
    false_positive_rate: float
    
    # Risk metrics
    high_risk_users: int
    medium_risk_users: int
    low_risk_users: int
    avg_risk_score: float
    
    # Compliance checks
    total_checks: int
    passed_checks: int
    failed_checks: int
    compliance_rate: float
    
    # Regulatory
    reports_generated: int
    reports_filed: int
    regulatory_breaches: int
    
    # Trends
    risk_trend: str  # improving, worsening, stable
    alert_trend: str
    compliance_trend: str
    
    # Generated at
    generated_at: datetime = Field(default_factory=datetime.now)


class TransactionScreeningRequest(BaseModel):
    """Transaction screening request"""
    transaction_id: str
    user_id: str
    
    # Transaction details
    amount: Decimal
    currency: str
    transaction_type: str  # deposit, withdrawal, transfer, trade
    
    # Parties
    sender_info: Optional[Dict[str, Any]] = None
    recipient_info: Optional[Dict[str, Any]] = None
    
    # Additional context
    purpose: Optional[str] = None
    reference: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SanctionsScreeningResult(BaseModel):
    """Sanctions screening result"""
    screening_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Search parameters
    search_name: str
    search_country: Optional[str] = None
    
    # Results
    matches_found: bool
    match_count: int
    
    # Match details
    matches: List[Dict[str, Any]] = []
    
    # Risk assessment
    risk_level: str  # none, low, medium, high, critical
    recommended_action: str
    
    # Metadata
    lists_checked: List[str] = []
    screening_date: datetime = Field(default_factory=datetime.now)
    screening_provider: str = "internal"
