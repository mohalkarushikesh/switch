"""
ESG Advisor Service - Provides ESG analysis and sustainable investment recommendations
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.settings import get_settings
from shared.database.connection import init_databases, close_databases, get_db
from shared.database.models import User, Portfolio, Asset
from shared.utils.logger import esg_logger
from shared.utils.auth import get_current_verified_user

# Import ESG modules
from .esg_analyzer import ESGAnalyzer
from .greenwashing_detector import GreenwashingDetector
from .impact_calculator import ImpactCalculator
from .models import (
    ESGAnalysisRequest, ESGAnalysisResponse,
    PortfolioESGRequest, PortfolioESGResponse,
    ESGScreeningRequest, ESGScreeningResponse,
    ImpactReportRequest, ImpactReportResponse
)

settings = get_settings()
logger = esg_logger.get_logger()

# Global instances
esg_analyzer = None
greenwashing_detector = None
impact_calculator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global esg_analyzer, greenwashing_detector, impact_calculator
    
    # Startup
    logger.info("Starting ESG Advisor Service")
    await init_databases()
    
    # Initialize components
    esg_analyzer = ESGAnalyzer()
    greenwashing_detector = GreenwashingDetector()
    impact_calculator = ImpactCalculator()
    
    await asyncio.gather(
        esg_analyzer.initialize(),
        greenwashing_detector.initialize(),
        impact_calculator.initialize()
    )
    
    logger.info("ESG Advisor Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ESG Advisor Service")
    await close_databases()


# Create FastAPI app
app = FastAPI(
    title="ESG Advisor Service",
    description="Provides ESG analysis, sustainable investment screening, and impact measurement",
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
        "service": "ESG Advisor",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "ESG scoring",
            "Greenwashing detection",
            "Impact calculation",
            "Sustainable screening",
            "Carbon footprint analysis"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "esg_analyzer": "ready" if esg_analyzer else "not initialized",
            "greenwashing_detector": "ready" if greenwashing_detector else "not initialized",
            "impact_calculator": "ready" if impact_calculator else "not initialized"
        }
    }


@app.post("/analyze", response_model=ESGAnalysisResponse)
async def analyze_asset(
    request: ESGAnalysisRequest,
    current_user: User = Depends(get_current_verified_user)
):
    """
    Analyze ESG characteristics of a specific asset
    
    Provides:
    - ESG scores (Environmental, Social, Governance)
    - Sustainability metrics
    - Greenwashing risk assessment
    - Peer comparison
    """
    try:
        logger.info(f"Analyzing ESG for asset: {request.symbol}")
        
        # Get ESG scores
        esg_scores = await esg_analyzer.analyze_asset(
            symbol=request.symbol,
            asset_type=request.asset_type
        )
        
        # Check for greenwashing
        greenwashing_risk = await greenwashing_detector.assess_risk(
            symbol=request.symbol,
            claimed_scores=esg_scores
        )
        
        # Get peer comparison
        peer_comparison = await esg_analyzer.get_peer_comparison(
            symbol=request.symbol,
            sector=request.sector
        )
        
        return ESGAnalysisResponse(
            symbol=request.symbol,
            esg_scores=esg_scores,
            greenwashing_risk=greenwashing_risk,
            peer_comparison=peer_comparison,
            recommendations=await esg_analyzer.generate_recommendations(
                esg_scores, greenwashing_risk
            )
        )
        
    except Exception as e:
        logger.error(f"Error in ESG analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ESG analysis failed: {str(e)}"
        )


@app.post("/portfolio/analyze", response_model=PortfolioESGResponse)
async def analyze_portfolio_esg(
    request: PortfolioESGRequest,
    current_user: User = Depends(get_current_verified_user),
    db = Depends(get_db)
):
    """
    Analyze ESG characteristics of entire portfolio
    
    Provides:
    - Weighted ESG scores
    - Carbon footprint
    - UN SDG alignment
    - Improvement suggestions
    """
    try:
        # Fetch portfolio data
        portfolio = await db.get(Portfolio, request.portfolio_id)
        if not portfolio or portfolio.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Analyze each asset
        asset_analyses = []
        for asset in portfolio.assets:
            analysis = await esg_analyzer.analyze_asset(
                symbol=asset.symbol,
                asset_type=asset.asset_class
            )
            asset_analyses.append({
                "asset": asset,
                "analysis": analysis,
                "weight": asset.allocation
            })
        
        # Calculate portfolio-level metrics
        portfolio_scores = await esg_analyzer.calculate_portfolio_scores(
            asset_analyses
        )
        
        # Calculate carbon footprint
        carbon_footprint = await impact_calculator.calculate_carbon_footprint(
            portfolio_id=request.portfolio_id,
            asset_analyses=asset_analyses
        )
        
        # Check SDG alignment
        sdg_alignment = await impact_calculator.assess_sdg_alignment(
            asset_analyses
        )
        
        # Generate improvement suggestions
        suggestions = await esg_analyzer.generate_portfolio_improvements(
            portfolio_scores,
            carbon_footprint,
            user_preferences=request.preferences
        )
        
        return PortfolioESGResponse(
            portfolio_id=request.portfolio_id,
            overall_esg_score=portfolio_scores["overall"],
            environmental_score=portfolio_scores["environmental"],
            social_score=portfolio_scores["social"],
            governance_score=portfolio_scores["governance"],
            carbon_footprint=carbon_footprint,
            sdg_alignment=sdg_alignment,
            asset_breakdown=asset_analyses,
            improvement_suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error in portfolio ESG analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio ESG analysis failed: {str(e)}"
        )


@app.post("/screen", response_model=ESGScreeningResponse)
async def screen_investments(
    request: ESGScreeningRequest,
    current_user: User = Depends(get_current_verified_user)
):
    """
    Screen investments based on ESG criteria
    
    Filter assets by:
    - Minimum ESG scores
    - Exclusion lists (tobacco, weapons, etc.)
    - Positive screening (renewable energy, etc.)
    - Impact themes
    """
    try:
        logger.info(f"ESG screening with criteria: {request.criteria}")
        
        # Get universe of assets
        assets = await esg_analyzer.get_asset_universe(
            asset_classes=request.asset_classes,
            regions=request.regions
        )
        
        # Apply ESG filters
        filtered_assets = []
        for asset in assets:
            # Get ESG scores
            scores = await esg_analyzer.analyze_asset(
                symbol=asset["symbol"],
                asset_type=asset["type"]
            )
            
            # Check against criteria
            if await esg_analyzer.meets_criteria(scores, request.criteria):
                # Check exclusions
                if not await esg_analyzer.is_excluded(
                    asset["symbol"],
                    request.exclusions
                ):
                    filtered_assets.append({
                        "asset": asset,
                        "scores": scores
                    })
        
        # Rank by ESG scores
        ranked_assets = sorted(
            filtered_assets,
            key=lambda x: x["scores"]["overall"],
            reverse=True
        )
        
        # Apply positive screening if requested
        if request.positive_themes:
            ranked_assets = await esg_analyzer.apply_positive_screening(
                ranked_assets,
                request.positive_themes
            )
        
        return ESGScreeningResponse(
            total_screened=len(assets),
            total_passed=len(ranked_assets),
            assets=ranked_assets[:request.max_results],
            screening_summary=await esg_analyzer.generate_screening_summary(
                request.criteria,
                ranked_assets
            )
        )
        
    except Exception as e:
        logger.error(f"Error in ESG screening: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ESG screening failed: {str(e)}"
        )


@app.post("/impact/calculate", response_model=ImpactReportResponse)
async def calculate_impact(
    request: ImpactReportRequest,
    current_user: User = Depends(get_current_verified_user)
):
    """
    Calculate real-world impact of investments
    
    Measures:
    - Carbon emissions avoided
    - Jobs created
    - Communities impacted
    - SDG contributions
    """
    try:
        logger.info(f"Calculating impact for portfolio: {request.portfolio_id}")
        
        # Calculate various impact metrics
        impact_metrics = await impact_calculator.calculate_impact(
            portfolio_id=request.portfolio_id,
            time_period=request.time_period
        )
        
        # Generate impact stories
        impact_stories = await impact_calculator.generate_impact_stories(
            impact_metrics
        )
        
        # Create visualizations data
        visualizations = await impact_calculator.create_visualizations(
            impact_metrics
        )
        
        return ImpactReportResponse(
            portfolio_id=request.portfolio_id,
            time_period=request.time_period,
            carbon_avoided_tons=impact_metrics["carbon_avoided"],
            renewable_energy_mwh=impact_metrics["renewable_energy"],
            jobs_supported=impact_metrics["jobs_supported"],
            communities_impacted=impact_metrics["communities"],
            sdg_contributions=impact_metrics["sdg_contributions"],
            impact_stories=impact_stories,
            visualizations=visualizations,
            report_url=await impact_calculator.generate_report_pdf(
                impact_metrics,
                impact_stories
            )
        )
        
    except Exception as e:
        logger.error(f"Error calculating impact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impact calculation failed: {str(e)}"
        )


@app.get("/trends")
async def get_esg_trends(
    current_user: User = Depends(get_current_verified_user)
):
    """Get latest ESG trends and insights"""
    try:
        trends = await esg_analyzer.get_market_trends()
        return {
            "trends": trends,
            "last_updated": await esg_analyzer.get_last_update()
        }
    except Exception as e:
        logger.error(f"Error fetching ESG trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ESG trends: {str(e)}"
        )


@app.get("/certifications/{symbol}")
async def get_certifications(
    symbol: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get ESG certifications and ratings for an asset"""
    try:
        certifications = await esg_analyzer.get_certifications(symbol)
        return {
            "symbol": symbol,
            "certifications": certifications,
            "ratings_agencies": await esg_analyzer.get_ratings_agencies(symbol)
        }
    except Exception as e:
        logger.error(f"Error fetching certifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch certifications: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    ) 