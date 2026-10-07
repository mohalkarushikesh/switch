"""
Advisory Engine Service - Core investment advisory and recommendations
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.settings import get_settings
from shared.database.connection import init_databases, close_databases, get_db
from shared.database.models import User, Portfolio, Asset, Transaction
from shared.utils.logger import advisory_logger
from shared.utils.auth import get_current_verified_user

# Import advisory modules
from .advisory_core import AdvisoryCore
from .recommendation_engine import RecommendationEngine
from .portfolio_analyzer import PortfolioAnalyzer
from .models import (
    AdvisoryRequest, AdvisoryResponse,
    PortfolioAnalysisRequest, PortfolioAnalysisResponse,
    RecommendationRequest, RecommendationResponse,
    MarketOverview, RiskAssessment
)

settings = get_settings()
logger = advisory_logger.get_logger()

# Global instances
advisory_core = None
recommendation_engine = None
portfolio_analyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global advisory_core, recommendation_engine, portfolio_analyzer
    
    # Startup
    logger.info("Starting Advisory Engine Service")
    await init_databases()
    
    # Initialize components
    advisory_core = AdvisoryCore()
    recommendation_engine = RecommendationEngine()
    portfolio_analyzer = PortfolioAnalyzer()
    
    await asyncio.gather(
        advisory_core.initialize(),
        recommendation_engine.initialize(),
        portfolio_analyzer.initialize()
    )
    
    logger.info("Advisory Engine Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Advisory Engine Service")
    await close_databases()


# Create FastAPI app
app = FastAPI(
    title="Advisory Engine Service",
    description="Core investment advisory, analysis, and personalized recommendations",
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
        "service": "Advisory Engine",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "Portfolio analysis",
            "Investment recommendations",
            "Risk assessment",
            "Market insights",
            "Personalized advice"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "advisory_core": "ready" if advisory_core else "not initialized",
            "recommendation_engine": "ready" if recommendation_engine else "not initialized",
            "portfolio_analyzer": "ready" if portfolio_analyzer else "not initialized"
        }
    }


@app.post("/advise", response_model=AdvisoryResponse)
async def get_advisory(
    request: AdvisoryRequest,
    current_user: User = Depends(get_current_verified_user),
    db = Depends(get_db)
):
    """
    Get comprehensive investment advisory
    
    Provides:
    - Portfolio analysis
    - Personalized recommendations
    - Risk assessment
    - Market insights
    - Action items
    """
    try:
        logger.info(f"Generating advisory for user {current_user.id}")
        
        # Fetch user's portfolio
        portfolio = await db.get(Portfolio, request.portfolio_id)
        if not portfolio or portfolio.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Analyze portfolio
        portfolio_analysis = await portfolio_analyzer.analyze(
            portfolio=portfolio,
            user_preferences={
                "risk_tolerance": current_user.risk_tolerance,
                "investment_goals": request.goals,
                "time_horizon": request.time_horizon
            }
        )
        
        # Generate recommendations
        recommendations = await recommendation_engine.generate_recommendations(
            portfolio_analysis=portfolio_analysis,
            market_conditions=await advisory_core.get_market_conditions(),
            user_profile=current_user
        )
        
        # Assess risks
        risk_assessment = await advisory_core.assess_risks(
            portfolio=portfolio,
            market_conditions=await advisory_core.get_market_conditions()
        )
        
        # Generate action items
        action_items = await advisory_core.generate_action_items(
            portfolio_analysis=portfolio_analysis,
            recommendations=recommendations,
            risk_assessment=risk_assessment
        )
        
        return AdvisoryResponse(
            portfolio_id=request.portfolio_id,
            generated_at=datetime.now(),
            portfolio_analysis=portfolio_analysis,
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            action_items=action_items,
            next_review_date=advisory_core.calculate_next_review_date(
                portfolio_analysis, request.review_frequency
            )
        )
        
    except Exception as e:
        logger.error(f"Error generating advisory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advisory generation failed: {str(e)}"
        )


@app.post("/analyze/portfolio", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(
    request: PortfolioAnalysisRequest,
    current_user: User = Depends(get_current_verified_user),
    db = Depends(get_db)
):
    """
    Perform detailed portfolio analysis
    
    Analyzes:
    - Asset allocation
    - Performance metrics
    - Risk metrics
    - Diversification
    - Cost efficiency
    """
    try:
        portfolio = await db.get(Portfolio, request.portfolio_id)
        if not portfolio or portfolio.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        analysis = await portfolio_analyzer.deep_analyze(
            portfolio=portfolio,
            include_projections=request.include_projections,
            benchmark=request.benchmark
        )
        
        return PortfolioAnalysisResponse(**analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio analysis failed: {str(e)}"
        )


@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get investment recommendations
    
    Types:
    - Buy/Sell/Hold recommendations
    - Asset allocation adjustments
    - New investment opportunities
    - Risk mitigation strategies
    """
    try:
        recommendations = await recommendation_engine.get_recommendations(
            user_id=str(current_user.id),
            recommendation_type=request.type,
            filters=request.filters,
            limit=request.limit
        )
        
        return RecommendationResponse(
            recommendations=recommendations,
            generated_at=datetime.now(),
            validity_period="7 days"
        )
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation generation failed: {str(e)}"
        )


@app.get("/market-overview", response_model=MarketOverview)
async def get_market_overview():
    """Get current market overview and insights"""
    try:
        overview = await advisory_core.get_market_overview()
        return MarketOverview(**overview)
        
    except Exception as e:
        logger.error(f"Error getting market overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market overview failed: {str(e)}"
        )


@app.post("/risk-assessment", response_model=RiskAssessment)
async def assess_portfolio_risk(
    portfolio_id: str,
    current_user: User = Depends(get_current_verified_user),
    db = Depends(get_db)
):
    """Assess portfolio risk"""
    try:
        portfolio = await db.get(Portfolio, portfolio_id)
        if not portfolio or portfolio.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        risk_assessment = await advisory_core.assess_risks(
            portfolio=portfolio,
            market_conditions=await advisory_core.get_market_conditions()
        )
        
        return RiskAssessment(**risk_assessment)
        
    except Exception as e:
        logger.error(f"Error assessing risk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment failed: {str(e)}"
        )


@app.get("/insights/trending")
async def get_trending_insights(
    current_user: User = Depends(get_current_verified_user)
):
    """Get trending market insights and opportunities"""
    try:
        insights = await advisory_core.get_trending_insights()
        return {
            "insights": insights,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights: {str(e)}"
        )


@app.post("/goals/progress")
async def check_goal_progress(
    portfolio_id: str,
    current_user: User = Depends(get_current_verified_user),
    db = Depends(get_db)
):
    """Check progress towards investment goals"""
    try:
        # Fetch user's goals
        goals = await db.query(
            "SELECT * FROM goals WHERE user_id = ?",
            [current_user.id]
        )
        
        portfolio = await db.get(Portfolio, portfolio_id)
        if not portfolio or portfolio.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        progress = await advisory_core.calculate_goal_progress(
            portfolio=portfolio,
            goals=goals
        )
        
        return {
            "portfolio_id": portfolio_id,
            "goals_progress": progress,
            "evaluated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error checking goal progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Goal progress check failed: {str(e)}"
        )


@app.get("/educational/content")
async def get_educational_content(
    topic: Optional[str] = None,
    level: Optional[str] = "beginner",
    current_user: User = Depends(get_current_verified_user)
):
    """Get personalized educational content"""
    try:
        content = await advisory_core.get_educational_content(
            user_level=level,
            topic=topic,
            user_interests=current_user.interests if hasattr(current_user, 'interests') else []
        )
        
        return {
            "content": content,
            "level": level,
            "topic": topic
        }
        
    except Exception as e:
        logger.error(f"Error getting educational content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get educational content: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
