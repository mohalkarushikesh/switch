"""
Data models for ESG Advisor Service
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class AssetType(str, Enum):
    EQUITY = "equity"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    REIT = "reit"


class ESGCategory(str, Enum):
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"


class ImpactTheme(str, Enum):
    RENEWABLE_ENERGY = "renewable_energy"
    CLEAN_WATER = "clean_water"
    SUSTAINABLE_AGRICULTURE = "sustainable_agriculture"
    AFFORDABLE_HOUSING = "affordable_housing"
    HEALTHCARE_ACCESS = "healthcare_access"
    EDUCATION = "education"
    GENDER_EQUALITY = "gender_equality"
    CIRCULAR_ECONOMY = "circular_economy"


class GreenwashingRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ESGScore(BaseModel):
    """Individual ESG score component"""
    score: float = Field(ge=0, le=100)
    category: ESGCategory
    subcategories: Dict[str, float] = {}
    data_quality: float = Field(ge=0, le=1)
    last_updated: datetime


class ESGAnalysisRequest(BaseModel):
    """Request for ESG analysis of a single asset"""
    symbol: str
    asset_type: AssetType
    sector: Optional[str] = None
    include_controversies: bool = True
    include_peer_comparison: bool = True


class ESGAnalysisResponse(BaseModel):
    """Response with ESG analysis results"""
    symbol: str
    company_name: Optional[str] = None
    
    # ESG Scores
    esg_scores: Dict[str, ESGScore]
    overall_score: float = Field(ge=0, le=100)
    
    # Greenwashing assessment
    greenwashing_risk: GreenwashingRisk
    greenwashing_factors: List[str] = []
    
    # Peer comparison
    peer_comparison: Optional[Dict[str, Any]] = None
    percentile_rank: Optional[float] = None
    
    # Controversies
    controversies: List[Dict[str, Any]] = []
    controversy_score: float = Field(ge=0, le=100)
    
    # Recommendations
    recommendations: List[str] = []
    
    # Metadata
    data_sources: List[str] = []
    analysis_date: datetime = Field(default_factory=datetime.now)


class PortfolioESGRequest(BaseModel):
    """Request for portfolio-level ESG analysis"""
    portfolio_id: str
    include_carbon_footprint: bool = True
    include_sdg_alignment: bool = True
    preferences: Optional[Dict[str, Any]] = {}


class PortfolioESGResponse(BaseModel):
    """Response with portfolio ESG analysis"""
    portfolio_id: str
    
    # Overall scores
    overall_esg_score: float = Field(ge=0, le=100)
    environmental_score: float = Field(ge=0, le=100)
    social_score: float = Field(ge=0, le=100)
    governance_score: float = Field(ge=0, le=100)
    
    # Carbon footprint
    carbon_footprint: Optional[Dict[str, float]] = None
    carbon_intensity: Optional[float] = None
    
    # SDG alignment
    sdg_alignment: Optional[Dict[int, float]] = None
    primary_sdgs: Optional[List[int]] = None
    
    # Asset breakdown
    asset_breakdown: List[Dict[str, Any]] = []
    
    # Improvement suggestions
    improvement_suggestions: List[Dict[str, Any]] = []
    
    # Benchmarking
    benchmark_comparison: Optional[Dict[str, Any]] = None


class ESGCriteria(BaseModel):
    """ESG screening criteria"""
    min_overall_score: Optional[float] = Field(None, ge=0, le=100)
    min_environmental_score: Optional[float] = Field(None, ge=0, le=100)
    min_social_score: Optional[float] = Field(None, ge=0, le=100)
    min_governance_score: Optional[float] = Field(None, ge=0, le=100)
    max_controversy_score: Optional[float] = Field(None, ge=0, le=100)
    required_certifications: List[str] = []


class ESGScreeningRequest(BaseModel):
    """Request for ESG-based investment screening"""
    criteria: ESGCriteria
    asset_classes: List[AssetType] = [AssetType.EQUITY]
    regions: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    
    # Exclusions
    exclusions: List[str] = []  # e.g., ["tobacco", "weapons", "fossil_fuels"]
    
    # Positive screening
    positive_themes: Optional[List[ImpactTheme]] = None
    
    # Results
    max_results: int = Field(50, ge=1, le=500)
    sort_by: str = "overall_score"  # or specific score


class ESGScreeningResponse(BaseModel):
    """Response with ESG screening results"""
    total_screened: int
    total_passed: int
    
    # Screened assets
    assets: List[Dict[str, Any]]
    
    # Summary statistics
    screening_summary: Dict[str, Any]
    
    # Filters applied
    applied_criteria: ESGCriteria
    applied_exclusions: List[str]


class ImpactReportRequest(BaseModel):
    """Request for impact calculation"""
    portfolio_id: str
    time_period: str = "1Y"  # 1M, 3M, 6M, 1Y, 3Y, 5Y
    include_projections: bool = False
    report_format: str = "summary"  # summary, detailed, visual


class ImpactMetric(BaseModel):
    """Individual impact metric"""
    metric_name: str
    value: float
    unit: str
    description: str
    calculation_method: str
    confidence_level: float = Field(ge=0, le=1)


class ImpactStory(BaseModel):
    """Real-world impact story"""
    title: str
    description: str
    metrics: List[ImpactMetric]
    beneficiaries: str
    location: Optional[str] = None
    images: List[str] = []


class ImpactReportResponse(BaseModel):
    """Response with impact calculation results"""
    portfolio_id: str
    time_period: str
    report_date: datetime = Field(default_factory=datetime.now)
    
    # Environmental impact
    carbon_avoided_tons: float
    renewable_energy_mwh: float
    water_saved_gallons: Optional[float] = None
    waste_diverted_tons: Optional[float] = None
    
    # Social impact
    jobs_supported: int
    communities_impacted: int
    people_with_improved_access: Optional[Dict[str, int]] = None
    
    # SDG contributions
    sdg_contributions: Dict[int, Dict[str, Any]]
    
    # Impact stories
    impact_stories: List[ImpactStory]
    
    # Visualizations
    visualizations: Dict[str, Any]
    
    # Report
    report_url: Optional[str] = None
    
    # Projections (if requested)
    future_impact: Optional[Dict[str, Any]] = None


class GreenwashingAlert(BaseModel):
    """Alert for potential greenwashing"""
    asset_symbol: str
    risk_level: GreenwashingRisk
    factors: List[str]
    evidence: List[Dict[str, Any]]
    recommendations: List[str]
    alert_date: datetime = Field(default_factory=datetime.now)


class ESGTrend(BaseModel):
    """ESG market trend"""
    trend_name: str
    description: str
    affected_sectors: List[str]
    impact_level: str  # low, medium, high
    opportunities: List[str]
    risks: List[str]
    relevant_assets: List[str] = []


class ESGCertification(BaseModel):
    """ESG certification or rating"""
    name: str
    issuer: str
    rating: str
    score: Optional[float] = None
    valid_until: Optional[datetime] = None
    methodology_url: Optional[str] = None 