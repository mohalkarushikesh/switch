"""
Advisory Engine - Test Version
Simplified version for testing with SQLite and mock data
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
from pathlib import Path
import os
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="Advisory Engine (Test Mode)",
    description="Portfolio analysis and investment recommendations - Test Version",
    version="1.0.0-test"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data path
MOCK_DATA_DIR = Path(__file__).parent.parent.parent.parent / "mock_data"

# Simple models
class PortfolioAnalysis(BaseModel):
    portfolio_value: float
    total_return: float
    risk_score: float
    recommendations: List[str]

class StockRecommendation(BaseModel):
    symbol: str
    name: str
    price: float
    recommendation: str
    score: float

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Advisory Engine (Test Mode)",
        "version": "1.0.0-test",
        "status": "running",
        "database": "SQLite",
        "mock_data": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "test",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/portfolio/analysis")
async def analyze_portfolio(user_id: int = 1):
    """Analyze user portfolio using mock data"""
    # Load mock user profile
    user_profiles_path = MOCK_DATA_DIR / "user_profiles.json"
    
    if user_profiles_path.exists():
        with open(user_profiles_path) as f:
            profiles = json.load(f)
            
        user_profile = profiles.get(str(user_id), profiles.get("1"))
        
        # Simple mock analysis
        analysis = PortfolioAnalysis(
            portfolio_value=user_profile["portfolio_value"],
            total_return=12.5,  # Mock return
            risk_score=5.2,  # Mock risk score
            recommendations=[
                "Consider diversifying into international markets",
                "Your tech allocation is high, consider rebalancing",
                "Add some defensive stocks for stability"
            ]
        )
        
        return analysis
    else:
        raise HTTPException(status_code=500, detail="Mock data not found")

@app.get("/recommendations", response_model=List[StockRecommendation])
async def get_recommendations(limit: int = 5):
    """Get stock recommendations using mock data"""
    # Load mock stock data
    stock_prices_path = MOCK_DATA_DIR / "stock_prices.json"
    
    if stock_prices_path.exists():
        with open(stock_prices_path) as f:
            stocks = json.load(f)
            
        recommendations = []
        
        # Create simple recommendations
        for symbol, data in list(stocks.items())[:limit]:
            # Simple scoring based on recent performance
            score = 7.5 + (data["change"] / 10)  # Mock score
            
            recommendation = StockRecommendation(
                symbol=symbol,
                name=data["name"],
                price=data["price"],
                recommendation="BUY" if score > 7 else "HOLD",
                score=min(10, max(0, score))
            )
            recommendations.append(recommendation)
            
        return recommendations
    else:
        raise HTTPException(status_code=500, detail="Mock data not found")

@app.get("/market/overview")
async def market_overview():
    """Get market overview using mock data"""
    market_data_path = MOCK_DATA_DIR / "market_data.json"
    
    if market_data_path.exists():
        with open(market_data_path) as f:
            market_data = json.load(f)
            
        return {
            "indices": market_data["indices"],
            "sectors": market_data["sectors"],
            "market_status": market_data["market_status"],
            "last_update": market_data["last_update"]
        }
    else:
        raise HTTPException(status_code=500, detail="Mock data not found")

@app.get("/news/sentiment")
async def news_sentiment():
    """Get news sentiment using mock data"""
    news_path = MOCK_DATA_DIR / "news_feed.json"
    
    if news_path.exists():
        with open(news_path) as f:
            news_items = json.load(f)
            
        # Calculate overall sentiment
        positive_count = sum(1 for item in news_items if item["sentiment"] == "positive")
        negative_count = sum(1 for item in news_items if item["sentiment"] == "negative")
        
        return {
            "overall_sentiment": "positive" if positive_count > negative_count else "neutral",
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total_articles": len(news_items),
            "latest_news": news_items[:3]
        }
    else:
        raise HTTPException(status_code=500, detail="Mock data not found")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Advisory Engine in TEST MODE")
    print(f"📁 Mock data directory: {MOCK_DATA_DIR}")
    print("🗄️ Using SQLite database")
    print("🔧 External APIs disabled")
    
    uvicorn.run(
        "main_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 