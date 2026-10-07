"""
Data models for Advisory Engine Service
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class GoalType(str, Enum):
    RETIREMENT = "retirement"
    WEALTH_BUILDING = "wealth_building"
    EDUCATION = "education"
    HOME_PURCHASE = "home_purchase"
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    CUSTOM = "custom"


class RecommendationType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REBALANCE = "rebalance"
    NEW_OPPORTUNITY = "new_opportunity"
    RISK_MITIGATION = "risk_mitigation"


class ActionPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AdvisoryRequest(BaseModel):
    """Request for comprehensive advisory"""
    portfolio_id: str
    goals: List[GoalType] = []
    time_horizon: int = Field(5, ge=1, le=50)  # years
    review_frequency: str = "quarterly"  # monthly, quarterly, annually
    include_tax_optimization: bool = True
    include_esg_analysis: bool = True


class PortfolioMetrics(BaseModel):
    """Portfolio performance and risk metrics"""
    total_value: float
    total_return: float
    total_return_percentage: float
    daily_return: float
    daily_return_percentage: float
    monthly_return: float
    yearly_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    beta: float
    alpha: float
    tracking_error: Optional[float] = None


class AssetAllocation(BaseModel):
    """Asset allocation breakdown"""
    asset_class: str
    current_percentage: float
    target_percentage: float
    deviation: float
    assets: List[Dict[str, Any]]


class PortfolioAnalysis(BaseModel):
    """Comprehensive portfolio analysis"""
    portfolio_id: str
    analysis_date: datetime
    metrics: PortfolioMetrics
    asset_allocation: List[AssetAllocation]
    diversification_score: float = Field(ge=0, le=100)
    cost_efficiency_score: float = Field(ge=0, le=100)
    tax_efficiency_score: float = Field(ge=0, le=100)
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]


class Recommendation(BaseModel):
    """Investment recommendation"""
    id: str
    type: RecommendationType
    symbol: str
    asset_name: str
    asset_class: str
    action: str  # Specific action to take
    quantity: Optional[float] = None
    target_price: Optional[float] = None
    current_price: float
    rationale: str
    confidence_score: float = Field(ge=0, le=100)
    expected_impact: Dict[str, Any]
    time_horizon: str
    risks: List[str]
    created_at: datetime = Field(default_factory=datetime.now)


class RiskMetric(BaseModel):
    """Individual risk metric"""
    metric_name: str
    current_value: float
    benchmark_value: float
    status: str  # good, warning, critical
    description: str


class RiskAssessment(BaseModel):
    """Portfolio risk assessment"""
    overall_risk_level: RiskLevel
    risk_score: float = Field(ge=0, le=100)
    risk_metrics: List[RiskMetric]
    concentration_risks: List[Dict[str, Any]]
    market_risks: List[Dict[str, Any]]
    specific_risks: List[Dict[str, Any]]
    risk_mitigation_suggestions: List[str]
    stress_test_results: Optional[Dict[str, Any]] = None


class ActionItem(BaseModel):
    """Actionable advisory item"""
    id: str
    title: str
    description: str
    priority: ActionPriority
    category: str  # rebalancing, tax, risk, opportunity
    deadline: Optional[datetime] = None
    impact: str
    steps: List[str]
    automated_available: bool = False


class AdvisoryResponse(BaseModel):
    """Comprehensive advisory response"""
    portfolio_id: str
    generated_at: datetime
    portfolio_analysis: PortfolioAnalysis
    recommendations: List[Recommendation]
    risk_assessment: RiskAssessment
    action_items: List[ActionItem]
    next_review_date: datetime
    summary: Optional[str] = None


class PortfolioAnalysisRequest(BaseModel):
    """Request for portfolio analysis"""
    portfolio_id: str
    include_projections: bool = True
    projection_years: int = Field(5, ge=1, le=30)
    benchmark: Optional[str] = "SP500"
    include_stress_test: bool = False


class PortfolioProjection(BaseModel):
    """Future portfolio projection"""
    year: int
    expected_value: float
    best_case_value: float
    worst_case_value: float
    probability_of_success: float


class PortfolioAnalysisResponse(BaseModel):
    """Response for portfolio analysis"""
    analysis: PortfolioAnalysis
    projections: Optional[List[PortfolioProjection]] = None
    benchmark_comparison: Optional[Dict[str, Any]] = None
    peer_comparison: Optional[Dict[str, Any]] = None


class RecommendationRequest(BaseModel):
    """Request for recommendations"""
    type: Optional[RecommendationType] = None
    asset_classes: Optional[List[str]] = None
    risk_level: Optional[RiskLevel] = None
    min_investment: Optional[float] = None
    max_investment: Optional[float] = None
    exclude_symbols: List[str] = []
    filters: Dict[str, Any] = {}
    limit: int = Field(10, ge=1, le=50)


class RecommendationResponse(BaseModel):
    """Response with recommendations"""
    recommendations: List[Recommendation]
    generated_at: datetime
    validity_period: str
    disclaimer: str = "These recommendations are for informational purposes only."


class MarketCondition(BaseModel):
    """Current market condition"""
    index: str
    value: float
    change: float
    change_percentage: float
    trend: str  # bullish, bearish, neutral
    volatility: str  # low, medium, high


class MarketInsight(BaseModel):
    """Market insight or trend"""
    title: str
    description: str
    impact: str  # positive, negative, neutral
    affected_sectors: List[str]
    recommended_actions: List[str]
    confidence: float = Field(ge=0, le=100)


class MarketOverview(BaseModel):
    """Market overview and insights"""
    timestamp: datetime
    conditions: List[MarketCondition]
    insights: List[MarketInsight]
    sentiment: str  # bullish, bearish, neutral
    volatility_index: float
    fear_greed_index: Optional[float] = None
    sector_performance: Dict[str, float]
    global_factors: List[str]


class GoalProgress(BaseModel):
    """Progress towards a financial goal"""
    goal_id: str
    goal_type: GoalType
    goal_name: str
    target_amount: float
    current_amount: float
    progress_percentage: float
    projected_completion_date: datetime
    on_track: bool
    monthly_contribution_needed: float
    recommendations: List[str]


class EducationalContent(BaseModel):
    """Educational content item"""
    id: str
    title: str
    category: str
    level: str  # beginner, intermediate, advanced
    content_type: str  # article, video, interactive
    summary: str
    url: Optional[str] = None
    duration_minutes: Optional[int] = None
    topics: List[str]
    personalized_relevance: float = Field(ge=0, le=1)
