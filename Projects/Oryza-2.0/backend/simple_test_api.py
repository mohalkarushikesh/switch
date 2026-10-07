"""
Simple Test API - Verifies the Oryza test setup
No complex dependencies, just FastAPI with mock data
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import uvicorn
from pydantic import BaseModel
from typing import List
from fastapi import Body, Header
from datetime import datetime

# Create app
app = FastAPI(title="Oryza Test API", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data directory
MOCK_DATA_DIR = Path(__file__).parent / "mock_data"

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

class LoginRequest(BaseModel):
    username: str  # Frontend sends email as username
    password: str

class User(BaseModel):
    id: str = "1"
    email: str
    username: str
    firstName: str = "Test"
    lastName: str = "User"
    role: str = "user"
    isVerified: bool = True
    createdAt: str = "2024-01-01T00:00:00Z"

@app.get("/")
async def root():
    """Test endpoint"""
    return {
        "message": "Oryza Test API is running!",
        "status": "success",
        "mock_data_available": MOCK_DATA_DIR.exists()
    }

@app.get("/stocks")
async def get_stocks():
    """Get mock stock data"""
    stock_file = MOCK_DATA_DIR / "stock_prices.json"
    
    if stock_file.exists():
        with open(stock_file) as f:
            stocks = json.load(f)
        
        # Return simplified stock list
        stock_list = []
        for symbol, data in stocks.items():
            stock_list.append({
                "symbol": symbol,
                "name": data["name"],
                "price": data["price"],
                "change": data["change"]
            })
        
        return {"stocks": stock_list[:10]}
    else:
        return {"error": "Mock data not found", "path": str(stock_file)}

@app.get("/news")
async def get_news():
    """Get mock news data"""
    news_file = MOCK_DATA_DIR / "news_feed.json"
    
    if news_file.exists():
        with open(news_file) as f:
            news = json.load(f)
        
        return {"news": news[:5]}
    else:
        return {"error": "Mock data not found", "path": str(news_file)}

@app.get("/market")
async def get_market():
    """Get mock market data"""
    market_file = MOCK_DATA_DIR / "market_data.json"
    
    if market_file.exists():
        with open(market_file) as f:
            market = json.load(f)
        
        return market
    else:
        return {"error": "Mock data not found", "path": str(market_file)}

@app.post("/auth/login")
async def login(form_data: dict = Body(...)):
    """Mock login endpoint"""
    # Accept any credentials for testing
    email = form_data.get("username", "test@oryza.com")  # OAuth2 sends email as username
    
    # Create mock response
    return {
        "access_token": "mock_access_token_12345",
        "refresh_token": "mock_refresh_token_67890",
        "token_type": "bearer",
        "user": {
            "id": "1",
            "email": email,
            "username": email.split("@")[0],
            "firstName": "Test",
            "lastName": "User",
            "role": "user",
            "isVerified": True,
            "createdAt": "2024-01-01T00:00:00Z"
        }
    }

@app.post("/auth/register")
async def register(user_data: dict):
    """Mock register endpoint"""
    return {
        "access_token": "mock_access_token_12345",
        "refresh_token": "mock_refresh_token_67890",
        "token_type": "bearer",
        "user": {
            "id": "2",
            "email": user_data.get("email"),
            "username": user_data.get("username"),
            "firstName": user_data.get("firstName", "New"),
            "lastName": user_data.get("lastName", "User"),
            "role": "user",
            "isVerified": False,
            "createdAt": datetime.now().isoformat()
        }
    }

@app.get("/auth/me")
async def get_current_user(authorization: str = Header(None)):
    """Mock get current user endpoint"""
    return {
        "id": "1",
        "email": "test@oryza.com",
        "username": "test",
        "firstName": "Test",
        "lastName": "User",
        "role": "user",
        "isVerified": True,
        "createdAt": "2024-01-01T00:00:00Z"
    }

@app.get("/test-db")
async def test_database():
    """Test SQLite database connection"""
    import sqlite3
    
    db_path = Path(__file__).parent / "test_oryza.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "database": "SQLite",
            "path": str(db_path),
            "tables": [t[0] for t in tables],
            "user_count": user_count
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Oryza Simple Test API")
    parser.add_argument("--port", type=int, default=8888, help="Port to run the API on")
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("🚀 Starting Oryza Test API")
    print("="*50)
    print(f"📁 Mock data directory: {MOCK_DATA_DIR}")
    print(f"🌐 API will be available at: http://localhost:{args.port}")
    print("📊 Test endpoints:")
    print("   - GET /          - Status check")
    print("   - GET /stocks    - Mock stock data")
    print("   - GET /news      - Mock news data")
    print("   - GET /market    - Mock market data")
    print("   - GET /test-db   - Database connection test")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=args.port) 