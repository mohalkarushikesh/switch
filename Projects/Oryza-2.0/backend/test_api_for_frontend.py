"""
Test API for Frontend Development
This provides mock endpoints for the frontend to work with
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Depends, status, Body, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from jose import jwt
import uuid
from pathlib import Path
from fastapi.responses import StreamingResponse
import io
import httpx
import os

# Import our database module
from backend.database import UserDB, get_db, init_database

# Ensure SQLite demo DB is initialized
init_database()

# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    firstName: str
    lastName: str

class OrderRequest(BaseModel):
    symbol: str
    type: str
    orderType: str
    quantity: int
    price: float

class User(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str

# Import our AI models
import sys
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "services" / "advisory-engine" / "src"))
sys.path.append(str(Path(__file__).parent / "services" / "esg-advisor" / "src"))
sys.path.append(str(Path(__file__).parent / "services" / "news-sentiment" / "src"))
sys.path.append(str(Path(__file__).parent / "services" / "goal-planner" / "src"))
sys.path.append(str(Path(__file__).parent / "services" / "backtesting-engine" / "src"))
sys.path.append(str(Path(__file__).parent / "services" / "autonomous-trading"))

# Import AI modules
try:
    from ai_models import SentimentAnalyzer, RiskScorer, PortfolioOptimizer
    from esg_scorer import ESGScorer
    from sentiment_engine import SentimentEngine
    from goal_engine import GoalEngine
    from backtesting_engine import BacktestingEngine
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"Warning: AI modules not available, using mock data. Error: {e}")

# Initialize AI models if available
if AI_AVAILABLE:
    risk_scorer = RiskScorer()
    portfolio_optimizer = PortfolioOptimizer()
    esg_scorer = ESGScorer()
    sentiment_engine = SentimentEngine()
    goal_engine = GoalEngine()
    backtesting_engine = BacktestingEngine()

# Get the directory of this script
BACKEND_DIR = Path(__file__).parent
MOCK_DATA_DIR = BACKEND_DIR / "mock_data"

# Initialize service variables
paper_trading_engine = None
marketplace_engine = None
social_engine = None
learning_platform = None
voice_chatbot = None
tax_optimizer = None
autonomous_trader = None

MARKET_SERVICE_URL = os.getenv("MARKET_SERVICE_URL", "http://localhost:8005")

def initialize_services():
    """Initialize all new services"""
    global paper_trading_engine, marketplace_engine, social_engine
    global learning_platform, voice_chatbot, tax_optimizer, autonomous_trader
    
    try:
        # Try to import from the services directory using relative paths
        import sys
        sys.path.insert(0, str(BACKEND_DIR))
        
        # Add each service directory to the path
        sys.path.insert(0, str(BACKEND_DIR / "services" / "paper-trading" / "src"))
        sys.path.insert(0, str(BACKEND_DIR / "services" / "agent-marketplace" / "src"))
        sys.path.insert(0, str(BACKEND_DIR / "services" / "social-trading" / "src"))
        sys.path.insert(0, str(BACKEND_DIR / "services" / "education-hub" / "src"))
        sys.path.insert(0, str(BACKEND_DIR / "services" / "ai-assistant" / "src"))
        sys.path.insert(0, str(BACKEND_DIR / "services" / "tax-optimizer" / "src"))
        sys.path.insert(0, str(BACKEND_DIR / "services" / "autonomous-trading"))
        
        from paper_trading_engine import PaperTradingEngine
        from marketplace_engine import MarketplaceEngine
        from social_engine import SocialTradingEngine
        from learning_platform import LearningPlatform
        from voice_chatbot import VoiceChatbot
        from tax_optimizer import TaxOptimizer
        from autonomous_trading import AutonomousTradingEngine
        
        paper_trading_engine = PaperTradingEngine()
        marketplace_engine = MarketplaceEngine()
        social_engine = SocialTradingEngine()
        learning_platform = LearningPlatform()
        voice_chatbot = VoiceChatbot()
        tax_optimizer = TaxOptimizer()
        autonomous_trader = AutonomousTradingEngine()
        
        # Add some mock fund positions for demo
        autonomous_trader.add_fund_position("1", "HDFC_TOP_100", 150, 650.00)
        autonomous_trader.add_fund_position("1", "NIFTY_BEES", 100, 240.00)
        autonomous_trader.add_fund_position("1", "ICICI_LIQUID", 50, 300.00)
        autonomous_trader.add_fund_position("1", "KOTAK_EMERGING", 75, 85.00)
        
        # Add some mock bond positions for demo
        autonomous_trader.add_bond_position("1", "GOI_5Y", 10, 97.80)
        autonomous_trader.add_bond_position("1", "HDFC_3Y", 5, 98.80)
        autonomous_trader.add_bond_position("1", "ICICI_5Y", 8, 97.60)
        autonomous_trader.add_bond_position("1", "NHAI_15Y", 15, 97.00)
        
        # Add some mock commodity positions for demo
        autonomous_trader.add_commodity_position("1", "GOLD", 100, 1950.50)
        autonomous_trader.add_commodity_position("1", "SILVER", 500, 23.45)
        autonomous_trader.add_commodity_position("1", "GOLDBEES", 200, 4850.50)
        autonomous_trader.add_commodity_position("1", "COPPER", 1000, 3.85)
        
        # Add some mock alternative positions for demo
        autonomous_trader.add_alternative_position("1", "EMBASSY_REIT", 100, 320.50)
        autonomous_trader.add_alternative_position("1", "BITCOIN", 0.1, 42850.00)
        autonomous_trader.add_alternative_position("1", "ETHEREUM", 1, 2280.00)
        autonomous_trader.add_alternative_position("1", "DIGITAL_ART_FUND", 10, 1250.00)
        
        # Add some mock global positions for demo
        autonomous_trader.add_global_position("1", "SPY", 50, 445.50)
        autonomous_trader.add_global_position("1", "VEUR", 100, 65.80)
        autonomous_trader.add_global_position("1", "VWO", 150, 42.15)
        autonomous_trader.add_global_position("1", "EWJ", 80, 58.90)
        autonomous_trader.add_global_position("1", "INDA", 100, 45.75)
        
        # Add some mock ESG positions for demo
        autonomous_trader.add_esg_position("1", "ICLN", 100, 18.75)
        autonomous_trader.add_esg_position("1", "ESGU", 50, 98.75)
        autonomous_trader.add_esg_position("1", "DSI", 30, 132.50)
        autonomous_trader.add_esg_position("1", "TAN", 40, 65.40)
        autonomous_trader.add_esg_position("1", "SHE", 25, 112.30)
        
        print("✅ All new services initialized successfully")
    except ImportError as e:
        print(f"⚠️  Some services could not be imported: {e}")
        # Initialize with mock versions if imports fail
        class MockService:
            def __init__(self):
                pass
                
            def __getattr__(self, name):
                async def mock_method(*args, **kwargs):
                    return {"message": f"Service method '{name}' not available", "mock": True}
                return mock_method
        
        paper_trading_engine = paper_trading_engine or MockService()
        marketplace_engine = marketplace_engine or MockService()
        social_engine = social_engine or MockService()
        learning_platform = learning_platform or MockService()
        voice_chatbot = voice_chatbot or MockService()
        tax_optimizer = tax_optimizer or MockService()
        autonomous_trader = autonomous_trader or MockService()

# Use lifespan handler instead of deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_services()
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="Oryza Test API", 
    description="Test API for Oryza frontend development with AI features",
    version="2.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Remove mock_users - we'll use database instead

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return email
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    # Verify user from database
    user = UserDB.verify_user(user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/v1/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    try:
        # Create user in database
        new_user = UserDB.create_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.firstName,
            last_name=user_data.lastName,
            phone=getattr(user_data, 'phone', None)
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": new_user["email"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": new_user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Get current user from token
async def get_current_user(email: str = Depends(verify_token)):
    user = UserDB.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return User(**user)

# Routes
@app.get("/")
async def root():
    return {"message": "Oryza Test API", "status": "running"}

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_available": AI_AVAILABLE
    }

# API Endpoints
@app.get("/api/v1/portfolio")
async def get_portfolio(user: User = Depends(get_current_user)):
    # Get portfolio from database
    portfolio = UserDB.get_user_portfolio(user.id)
    
    return {
        "portfolios": [{
            "id": portfolio.get("id", "1"),
            "name": portfolio.get("name", "Main Portfolio"),
            "totalValue": portfolio["totalValue"],
            "dayChange": portfolio["performance"]["dayChange"],
            "totalReturn": portfolio["performance"]["totalReturn"],
            "holdings": portfolio["holdings"]
        }],
        "metrics": {
            "totalValue": portfolio["totalValue"],
            "dayChange": portfolio["performance"]["dayChange"],
            "totalReturn": portfolio["performance"]["totalReturn"],
            "riskScore": 42.5
        }
    }

@app.get("/api/v1/market/overview")
async def get_market_overview():
    """Proxy to real market-service overview instead of mock"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MARKET_SERVICE_URL}/api/v1/market/overview")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Market overview unavailable: {e}")

@app.post("/api/v1/auth/refresh")
async def refresh_token(email: str = Depends(verify_token)):
    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/goals")
async def get_goals(email: str = Depends(verify_token)):
    return {
        "goals": [
            {
                "id": "1",
                "name": "Retirement Fund",
                "type": "retirement",
                "targetAmount": 10000000,
                "currentAmount": 2500000,
                "targetDate": "2045-12-31",
                "monthlyContribution": 50000,
                "priority": "high",
                "status": "on-track",
                "progress": 25,
                "milestones": []
            },
            {
                "id": "2",
                "name": "Children's Education",
                "type": "education",
                "targetAmount": 5000000,
                "currentAmount": 1000000,
                "targetDate": "2035-06-30",
                "monthlyContribution": 25000,
                "priority": "high",
                "status": "on-track",
                "progress": 20,
                "milestones": []
            }
        ]
    }

@app.post("/api/goals")
async def create_goal(
    request: dict,
    email: str = Depends(verify_token)
):
    # In a real app, save to database
    new_goal = {
        "id": str(datetime.now(timezone.utc).timestamp()),
        "name": request.get("name"),
        "type": request.get("type", "other"),
        "targetAmount": request.get("targetAmount", 0),
        "currentAmount": 0,
        "targetDate": request.get("targetDate"),
        "monthlyContribution": request.get("monthlyContribution", 0),
        "priority": request.get("priority", "medium"),
        "status": "on-track",
        "progress": 0,
        "milestones": []
    }
    
    return {
        "message": "Goal created successfully",
        "goal": new_goal
    }

@app.put("/api/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    request: dict,
    email: str = Depends(verify_token)
):
    # In a real app, update in database
    updated_goal = {
        "id": goal_id,
        "name": request.get("name"),
        "type": request.get("type", "other"),
        "targetAmount": request.get("targetAmount", 0),
        "targetDate": request.get("targetDate"),
        "monthlyContribution": request.get("monthlyContribution", 0),
        "priority": request.get("priority", "medium"),
        "status": "on-track"
    }
    
    return {
        "message": "Goal updated successfully",
        "goal": updated_goal
    }

@app.delete("/api/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
    email: str = Depends(verify_token)
):
    # In a real app, delete from database
    return {
        "message": "Goal deleted successfully"
    }

@app.get("/api/analytics/performance")
async def get_performance_analytics(email: str = Depends(verify_token)):
    return {
        "returns": {
            "daily": 0.45,
            "weekly": 2.3,
            "monthly": 5.8,
            "yearly": 18.5
        },
        "metrics": {
            "sharpeRatio": 1.42,
            "beta": 0.85,
            "alpha": 0.12,
            "standardDeviation": 14.2
        }
    }

@app.get("/api/analytics/allocation")
async def get_allocation_analytics(email: str = Depends(verify_token)):
    return {
        "byAssetClass": {
            "equity": 60,
            "debt": 25,
            "commodities": 10,
            "cash": 5
        },
        "bySector": {
            "technology": 25,
            "finance": 20,
            "healthcare": 15,
            "consumer": 15,
            "energy": 10,
            "others": 15
        }
    }

@app.get("/api/v1/market/quote/{symbol}")
async def proxy_market_quote(symbol: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MARKET_SERVICE_URL}/api/v1/market/quote/{symbol}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Quote unavailable: {e}")

@app.get("/api/v1/market/news")
async def proxy_market_news(limit: int = 20):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MARKET_SERVICE_URL}/api/v1/market/news", params={"limit": limit})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News unavailable: {e}")

@app.post("/api/v1/orders")
async def place_order(order: OrderRequest, user: User = Depends(get_current_user)):
    """Place a trading order"""
    # Save transaction to database
    transaction = {
        "type": order.type,
        "symbol": order.symbol,
        "quantity": order.quantity,
        "price": order.price
    }
    
    UserDB.add_transaction(user.id, transaction)
    
    # Return mock order confirmation
    return {
        "message": f"{order.type.upper()} order placed successfully",
        "order": {
            "id": str(uuid.uuid4()),
            "symbol": order.symbol,
            "type": order.type,
            "orderType": order.orderType,
            "quantity": order.quantity,
            "price": order.price,
            "status": "filled",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/orders")
async def get_orders(email: str = Depends(verify_token)):
    return {
        "orders": [
            {
                "id": "ORD123456",
                "symbol": "RELIANCE",
                "type": "buy",
                "orderType": "market",
                "quantity": 10,
                "price": 2450.00,
                "status": "executed",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }

# Profile Endpoints
@app.get("/api/v1/profile")
async def get_profile(user: User = Depends(get_current_user)):
    """Get user profile"""
    return {
        "personalInfo": {
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "phone": "+91 98765 43210",
            "dateOfBirth": "1990-01-01",
            "address": "123, Main Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001"
        },
        "preferences": {
            "language": "English",
            "currency": "INR",
            "theme": "light",
            "notifications": {
                "email": True,
                "sms": False,
                "push": True,
                "marketAlerts": True,
                "priceAlerts": True,
                "newsAlerts": False
            }
        },
        "security": {
            "twoFactorEnabled": False,
            "lastPasswordChange": "2024-01-01",
            "activeSessions": 2
        },
        "riskProfile": {
            "score": 65,
            "category": "moderate",
            "lastAssessment": "2024-01-15"
        }
    }

@app.put("/api/v1/profile")
async def update_profile(profile_data: dict, user: User = Depends(get_current_user)):
    """Update user profile"""
    # Save to database
    UserDB.update_user_profile(user.id, profile_data)
    return {"message": "Profile updated successfully", "profile": profile_data}

@app.post("/api/v1/auth/change-password")
async def change_password(
    request: dict,
    user: User = Depends(get_current_user)
):
    """Change user password"""
    current_password = request.get("current_password")
    new_password = request.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current and new passwords are required")
    
    # Verify current password
    verified_user = UserDB.verify_user(user.email, current_password)
    if not verified_user:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Update password in database
    import bcrypt
    with get_db() as conn:
        cursor = conn.cursor()
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user.id))
        conn.commit()
    
    return {"message": "Password changed successfully"}

@app.post("/api/v1/auth/2fa/toggle")
async def toggle_2fa(enable: bool, user: User = Depends(get_current_user)):
    """Toggle 2FA for user account"""
    if enable:
        # Generate QR code for 2FA setup
        return {
            "message": "2FA enabled successfully",
            "qrCode": "data:image/png;base64,mock_qr_code_data",
            "secret": "MOCK2FASECRET"
        }
    else:
        return {"message": "2FA disabled successfully"}

@app.get("/api/v1/profile/download-data")
async def download_user_data(user: User = Depends(get_current_user)):
    """Download user data"""
    user_data = {
        "user": {
            "id": user.id,
            "email": user.email,
            "firstName": user.firstName,
            "lastName": user.lastName
        },
        "portfolio": mock_portfolio_data,
        "transactions": [],
        "settings": {},
        "exportedAt": datetime.now().isoformat()
    }
    
    return StreamingResponse(
        io.StringIO(json.dumps(user_data, indent=2)),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=oryza-user-data.json"}
    )

@app.delete("/api/v1/profile/delete")
async def delete_account(user: User = Depends(get_current_user)):
    """Delete user account"""
    # In production, implement proper account deletion
    return {"message": "Account deletion initiated. You will receive confirmation within 48 hours."}

# Settings Endpoints
@app.get("/api/v1/settings")
async def get_settings(user: User = Depends(get_current_user)):
    """Get user settings"""
    # Get settings from database
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT settings_data FROM users WHERE id = ?", (user.id,))
        row = cursor.fetchone()
        
        if row and row['settings_data']:
            return json.loads(row['settings_data'])
        
    # Return default settings
    return {
        "language": "en",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "dateFormat": "DD/MM/YYYY",
        "theme": "light",
        "fontSize": "medium",
        "compactMode": False,
        "showAnimations": True,
        "emailNotifications": True,
        "pushNotifications": True,
        "smsNotifications": False,
        "marketingEmails": False,
        "priceAlerts": True,
        "portfolioUpdates": True,
        "newsAlerts": True,
        "dataSharing": False,
        "analyticsTracking": True,
        "personalization": True,
        "betaFeatures": False,
        "developerMode": False,
        "performanceMode": False
    }

@app.put("/api/v1/settings")
async def update_settings(settings: dict, user: User = Depends(get_current_user)):
    """Update user settings"""
    # Save to database
    UserDB.update_user_settings(user.id, settings)
    return {"message": "Settings saved successfully", "settings": settings}

# Market Data Endpoints

# New AI-powered endpoints

@app.get("/api/v1/ai/risk-assessment")
async def get_risk_assessment(email: str = Depends(verify_token)):
    """Get AI-powered risk assessment for portfolio"""
    if AI_AVAILABLE:
        portfolio_data = {
            "holdings": [
                {"symbol": "RELIANCE", "value": 125000, "asset_type": "stock"},
                {"symbol": "TCS", "value": 87000, "asset_type": "stock"},
                {"symbol": "HDFC_BOND", "value": 50000, "asset_type": "bond"},
                {"symbol": "GOLD_ETF", "value": 38000, "asset_type": "commodity"}
            ],
            "total_value": 300000
        }
        risk_assessment = risk_scorer.calculate_portfolio_risk(portfolio_data)
        return risk_assessment
    else:
        return {
            "overall_risk_score": 42.5,
            "risk_level": "moderate",
            "risk_breakdown": {
                "concentration": 35.2,
                "volatility": 48.3,
                "correlation": 32.1,
                "liquidity": 28.7,
                "market_conditions": 45.0
            },
            "recommendations": [
                "Portfolio is moderately concentrated. Consider diversifying across more assets.",
                "Volatility is within acceptable range for moderate risk profile.",
                "Maintain current allocation strategy."
            ]
        }

@app.get("/api/v1/ai/esg-score/{symbol}")
async def get_esg_score(symbol: str):
    """Get ESG score for a specific company"""
    if AI_AVAILABLE:
        return esg_scorer.calculate_esg_score(symbol)
    else:
        return {
            "company": symbol,
            "overall_score": 73.8,
            "rating": "AA",
            "breakdown": {
                "environmental": 75.2,
                "social": 71.5,
                "governance": 74.6
            },
            "strengths": ["Strong environmental practices", "Good diversity metrics"],
            "weaknesses": ["Room for improvement in sustainability"],
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/ai/portfolio-esg")
async def get_portfolio_esg(email: str = Depends(verify_token)):
    """Get ESG analysis for entire portfolio"""
    if AI_AVAILABLE:
        holdings = [
            {"symbol": "RELIANCE", "value": 125000},
            {"symbol": "TCS", "value": 87000},
            {"symbol": "HDFC", "value": 50000},
            {"symbol": "INFY", "value": 38000}
        ]
        return esg_scorer.analyze_portfolio_esg(holdings)
    else:
        return {
            "portfolio_esg_score": 71.5,
            "portfolio_rating": "AA",
            "dimension_scores": {
                "environmental": 72.3,
                "social": 70.8,
                "governance": 71.4
            },
            "esg_leaders": ["TCS", "INFY"],
            "esg_laggards": [],
            "improvement_suggestions": [
                "Portfolio has good ESG balance. Continue monitoring for improvements."
            ]
        }

@app.post("/api/v1/ai/sentiment-analysis")
async def analyze_sentiment(news_items: List[Dict[str, Any]]):
    """Analyze sentiment from news articles"""
    if AI_AVAILABLE:
        analysis = await sentiment_engine.analyze_news(news_items)
        return analysis
    else:
        return {
            "overall_sentiment": 0.45,
            "sentiment_label": "positive",
            "confidence": 0.78,
            "volatility": 0.15,
            "market_impact": "medium",
            "impact_score": 0.62,
            "sentiment_distribution": {
                "positive": 8,
                "neutral": 3,
                "negative": 2
            },
            "entity_sentiments": {
                "RELIANCE": {"sentiment": 0.6, "mentions": 3},
                "technology_sector": {"sentiment": 0.7, "mentions": 5}
            }
        }

@app.get("/api/v1/ai/market-mood")
async def get_market_mood():
    """Get AI-analyzed market mood"""
    if AI_AVAILABLE:
        return await sentiment_engine.get_market_mood()
    else:
        return {
            "market_mood": "bullish",
            "mood_score": 0.65,
            "confidence": 0.82,
            "contributing_factors": [
                "Positive earnings reports",
                "Economic growth indicators",
                "Policy support"
            ],
            "time_window_hours": 24,
            "last_updated": datetime.now().isoformat()
        }

@app.post("/api/v1/ai/portfolio-optimization")
async def optimize_portfolio(
    risk_tolerance: str = "moderate",
    investment_goals: List[str] = ["growth"],
    email: str = Depends(verify_token)
):
    """Get AI-powered portfolio optimization recommendations"""
    if AI_AVAILABLE:
        current_portfolio = {
            "allocation": {"stocks": 0.6, "bonds": 0.3, "cash": 0.1}
        }
        optimization = portfolio_optimizer.optimize_allocation(
            current_portfolio, risk_tolerance, investment_goals
        )
        return optimization
    else:
        return {
            "target_allocation": {
                "stocks": 0.50,
                "bonds": 0.30,
                "commodities": 0.10,
                "alternatives": 0.05,
                "cash": 0.05
            },
            "expected_return": 0.085,
            "sharpe_ratio": 1.2,
            "rebalancing_needed": {
                "needed": True,
                "actions": [
                    {
                        "asset_class": "stocks",
                        "action": "decrease",
                        "amount": 0.1,
                        "current": 0.6,
                        "target": 0.5
                    }
                ]
            }
        }

@app.post("/api/v1/ai/create-goal")
async def create_goal(goal_data: Dict[str, Any], email: str = Depends(verify_token)):
    """Create a new financial goal with AI analysis"""
    if AI_AVAILABLE:
        goal = await goal_engine.create_goal(goal_data)
        return goal
    else:
        return {
            "id": "goal_123456",
            "type": goal_data.get("goal_type", "custom"),
            "name": goal_data.get("name", "Financial Goal"),
            "target_amount": goal_data.get("target_amount", 1000000),
            "current_savings": goal_data.get("current_savings", 0),
            "monthly_contribution": goal_data.get("monthly_contribution", 10000),
            "target_date": "2030-12-31",
            "months_to_goal": 84,
            "feasibility_analysis": {
                "is_achievable": True,
                "projected_value": 1050000,
                "gap": 0,
                "success_probability": 0.75,
                "required_monthly_contribution": 10000
            },
            "ai_recommendations": [
                {
                    "type": "investment_strategy",
                    "priority": "high",
                    "title": "Optimize Asset Allocation",
                    "description": "Consider 60% equity allocation for long-term growth"
                }
            ]
        }

@app.post("/api/v1/ai/backtest")
async def run_backtest(strategy: Dict[str, Any], email: str = Depends(verify_token)):
    """Run backtesting for a trading strategy"""
    if AI_AVAILABLE:
        result = await backtesting_engine.run_backtest(
            strategy,
            strategy.get("start_date", "2023-01-01"),
            strategy.get("end_date", "2024-01-01"),
            strategy.get("initial_capital", 1000000)
        )
        return result
    else:
        return {
            "strategy": strategy,
            "period": {
                "start": "2023-01-01",
                "end": "2024-01-01"
            },
            "initial_capital": 1000000,
            "final_value": 1235000,
            "performance": {
                "total_return": 23.5,
                "annualized_return": 23.5,
                "sharpe_ratio": 1.35,
                "max_drawdown": -12.3,
                "volatility": 18.5
            },
            "trade_analysis": {
                "total_trades": 142,
                "winning_trades": 82,
                "losing_trades": 60,
                "win_rate": 57.7,
                "avg_win": 15000,
                "avg_loss": 8000,
                "profit_factor": 1.8
            }
        }

@app.get("/api/v1/ai/agent-recommendations")
async def get_agent_recommendations(email: str = Depends(verify_token)):
    """Get multi-agent AI recommendations"""
    return {
        "timestamp": datetime.now().isoformat(),
        "consensus_allocation": {
            "equity": {"allocation": 60, "confidence": 0.85},
            "bonds": {"allocation": 25, "confidence": 0.78},
            "commodities": {"allocation": 10, "confidence": 0.72},
            "cash": {"allocation": 5, "confidence": 0.90}
        },
        "agent_insights": {
            "equity_agent": {
                "recommendation": "overweight",
                "key_sectors": ["technology", "healthcare"],
                "rationale": "Strong earnings growth expected"
            },
            "fixed_income_agent": {
                "recommendation": "neutral",
                "duration": "medium",
                "rationale": "Interest rate stability expected"
            },
            "commodity_agent": {
                "recommendation": "underweight",
                "focus": "gold",
                "rationale": "Dollar strength limiting upside"
            }
        },
        "risk_warnings": [
            "Market volatility elevated",
            "Geopolitical tensions present"
        ]
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    try:
        while True:
            # Send market updates every 5 seconds
            import asyncio
            import random
            
            market_update = {
                "type": "market_update",
                "timestamp": datetime.now().isoformat(),
                "indices": {
                    "NIFTY": {
                        "value": 19845.50 + random.uniform(-50, 50),
                        "change": random.uniform(-0.5, 0.5)
                    },
                    "SENSEX": {
                        "value": 65782.30 + random.uniform(-100, 100),
                        "change": random.uniform(-0.5, 0.5)
                    }
                },
                "stocks": [
                    {
                        "symbol": "RELIANCE",
                        "price": 2456.50 + random.uniform(-20, 20),
                        "change": random.uniform(-2, 2)
                    },
                    {
                        "symbol": "TCS",
                        "price": 3567.80 + random.uniform(-30, 30),
                        "change": random.uniform(-2, 2)
                    }
                ]
            }
            
            await websocket.send_json(market_update)
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Paper Trading Endpoints
@app.post("/api/v1/paper-trading/create-account")
async def create_paper_account(user: User = Depends(get_current_user)):
    """Create a paper trading account"""
    if not paper_trading_engine:
        return {"error": "Paper trading not available"}
    
    result = await paper_trading_engine.create_paper_account(user.id, "Demo Account")
    return result

@app.post("/api/v1/paper-trading/place-order")
async def place_paper_order(
    account_id: str,
    symbol: str,
    order_type: str,
    side: str,
    quantity: int,
    price: Optional[float] = None,
    user: User = Depends(get_current_user)
):
    """Place a paper trading order"""
    if not paper_trading_engine:
        return {"error": "Paper trading not available"}
    
    result = await paper_trading_engine.place_order(
        account_id, symbol, order_type, side, quantity, price
    )
    return result

@app.get("/api/v1/paper-trading/account/{account_id}")
async def get_paper_account(account_id: str, user: User = Depends(get_current_user)):
    """Get paper trading account details"""
    if not paper_trading_engine:
        return {"error": "Paper trading not available"}
    
    result = await paper_trading_engine.get_account_summary(account_id)
    return result

@app.get("/api/v1/paper-trading/leaderboard")
async def get_paper_trading_leaderboard():
    """Get paper trading leaderboard"""
    if not paper_trading_engine:
        return {"error": "Paper trading not available"}
    
    result = await paper_trading_engine.get_leaderboard()
    return result

# AI Agent Marketplace Endpoints
@app.post("/api/v1/marketplace/create-strategy")
async def create_strategy(strategy_data: dict, user: User = Depends(get_current_user)):
    """Create a new trading strategy for marketplace"""
    if not marketplace_engine:
        return {"error": "Marketplace not available"}
    
    result = await marketplace_engine.create_strategy(user.id, strategy_data)
    return result

@app.get("/api/v1/marketplace/browse")
async def browse_strategies(
    category: Optional[str] = None,
    sort_by: str = "popularity",
    page: int = 1
):
    """Browse marketplace strategies"""
    if not marketplace_engine:
        return {"error": "Marketplace not available"}
    
    filters = {"category": category} if category else {}
    result = await marketplace_engine.browse_strategies(filters, sort_by, page)
    return result

@app.post("/api/v1/marketplace/subscribe/{strategy_id}")
async def subscribe_to_strategy(
    strategy_id: str,
    payment_method: dict,
    user: User = Depends(get_current_user)
):
    """Subscribe to a marketplace strategy"""
    if not marketplace_engine:
        return {"error": "Marketplace not available"}
    
    result = await marketplace_engine.subscribe_to_strategy(
        user.id, strategy_id, payment_method
    )
    return result

@app.get("/api/v1/marketplace/creator-dashboard")
async def get_creator_dashboard(user: User = Depends(get_current_user)):
    """Get strategy creator dashboard"""
    if not marketplace_engine:
        return {"error": "Marketplace not available"}
    
    result = await marketplace_engine.get_creator_dashboard(user.id)
    return result

# Social Trading Endpoints
@app.post("/api/v1/social/register-trader")
async def register_as_trader(profile: dict, user: User = Depends(get_current_user)):
    """Register as a social trader"""
    if not social_engine:
        return {"error": "Social trading not available"}
    
    result = await social_engine.register_as_trader(user.id, profile)
    return result

@app.post("/api/v1/social/follow/{trader_id}")
async def follow_trader(
    trader_id: str,
    copy_settings: Optional[dict] = None,
    user: User = Depends(get_current_user)
):
    """Follow a trader with optional copy trading"""
    if not social_engine:
        return {"error": "Social trading not available"}
    
    result = await social_engine.follow_trader(user.id, trader_id, copy_settings)
    return result

@app.get("/api/v1/social/leaderboard")
async def get_social_leaderboard(
    category: str = "returns",
    timeframe: str = "monthly"
):
    """Get trader leaderboard"""
    if not social_engine:
        return {"error": "Social trading not available"}
    
    result = await social_engine.get_leaderboard(category, timeframe)
    return result

@app.get("/api/v1/social/trader/{trader_id}")
async def get_trader_profile(trader_id: str, user: User = Depends(get_current_user)):
    """Get detailed trader profile"""
    if not social_engine:
        return {"error": "Social trading not available"}
    
    result = await social_engine.get_trader_profile(trader_id, user.id)
    return result

@app.get("/api/v1/social/feed")
async def get_social_feed(
    filter_type: str = "all",
    page: int = 1,
    user: User = Depends(get_current_user)
):
    """Get personalized social feed"""
    if not social_engine:
        return {"error": "Social trading not available"}
    
    result = await social_engine.get_social_feed(user.id, filter_type, page)
    return result

# Educational Hub Endpoints
@app.get("/api/v1/education/courses")
async def get_courses():
    """Get available courses"""
    if not learning_platform:
        return {"error": "Education hub not available"}
    
    return {"courses": learning_platform.courses}

@app.post("/api/v1/education/enroll/{course_id}")
async def enroll_in_course(
    course_id: str,
    payment_info: Optional[dict] = None,
    user: User = Depends(get_current_user)
):
    """Enroll in a course"""
    if not learning_platform:
        return {"error": "Education hub not available"}
    
    result = await learning_platform.enroll_in_course(user.id, course_id, payment_info)
    return result

@app.get("/api/v1/education/lesson")
async def get_lesson(
    course_id: str,
    module_id: str,
    lesson_index: int,
    user: User = Depends(get_current_user)
):
    """Get lesson content"""
    if not learning_platform:
        return {"error": "Education hub not available"}
    
    result = await learning_platform.get_lesson_content(
        user.id, course_id, module_id, lesson_index
    )
    return result

@app.post("/api/v1/education/quiz/submit")
async def submit_quiz(
    course_id: str,
    module_id: str,
    answers: List[int],
    user: User = Depends(get_current_user)
):
    """Submit quiz answers"""
    if not learning_platform:
        return {"error": "Education hub not available"}
    
    result = await learning_platform.submit_quiz(
        user.id, course_id, module_id, answers
    )
    return result

@app.get("/api/v1/education/dashboard")
async def get_learning_dashboard(user: User = Depends(get_current_user)):
    """Get learning dashboard"""
    if not learning_platform:
        return {"error": "Education hub not available"}
    
    result = await learning_platform.get_learning_dashboard(user.id)
    return result

# Voice Assistant & Chatbot Endpoints
@app.post("/api/v1/assistant/start-session")
async def start_chat_session(
    voice_enabled: bool = True,
    user: User = Depends(get_current_user)
):
    """Start a new chat session"""
    if not voice_chatbot:
        return {"error": "Assistant not available"}
    
    result = await voice_chatbot.start_session(user.id, voice_enabled)
    return result

@app.post("/api/v1/assistant/message")
async def send_chat_message(
    session_id: str,
    message: str,
    voice_input: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Send message to assistant"""
    if not voice_chatbot:
        return {"error": "Assistant not available"}
    
    result = await voice_chatbot.process_message(session_id, message, voice_input)
    return result

@app.post("/api/v1/assistant/confirm")
async def confirm_action(
    session_id: str,
    confirmed: bool,
    user: User = Depends(get_current_user)
):
    """Confirm pending action"""
    if not voice_chatbot:
        return {"error": "Assistant not available"}
    
    result = await voice_chatbot.process_confirmation(session_id, confirmed)
    return result

# Tax Optimizer Endpoints
@app.post("/api/v1/tax/optimize")
async def optimize_taxes(request: dict):
    """Get tax optimization recommendations"""
    if tax_optimizer:
        return await tax_optimizer.optimize_taxes(request)
    else:
        return {"message": "Tax optimizer not available", "mock": True}

# Autonomous Trading Endpoints

@app.get("/api/v1/autonomous/analyze/{symbol}")
async def analyze_stock_autonomous(symbol: str, user: User = Depends(get_current_user)):
    """Get detailed multi-agent analysis for autonomous trading"""
    if autonomous_trader:
        # Get real-time market data from simulator
        market_data = autonomous_trader.market_simulator.get_market_data(symbol)
        if not market_data:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
            
        # Get real analysis from autonomous trader
        analysis = await autonomous_trader.analyze_stock(symbol, market_data)
        
        # Add execution parameters
        analysis["autonomous_ready"] = True
        analysis["execution_parameters"] = {
            "entry_range": [
                round(analysis["current_price"] * 0.995, 2),
                round(analysis["current_price"] * 1.005, 2)
            ],
            "stop_loss": analysis["agents"]["risk"]["stop_loss"],
            "take_profit_levels": [
                round(analysis["current_price"] * 1.05, 2),
                round(analysis["current_price"] * 1.10, 2),
                round(analysis["current_price"] * 1.15, 2)
            ],
            "position_sizing": {
                "conservative": "3%",
                "moderate": "5%",
                "aggressive": "7%"
            }
        }
        
        return analysis
    else:
        # Fallback to static data if engine not available
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": 2456.50,
            "agents": {
                "equity": {"signal": "Buy", "technical_score": 7.5},
                "sentiment": {"market_mood": "Bullish"},
                "risk": {"risk_level": "Moderate"},
                "timing": {"entry_signal": "Good"}
            },
            "consensus": {
                "action": "BUY",
                "confidence": "87%",
                "recommendation": "Mock data - engine not available"
            }
        }

@app.post("/api/v1/autonomous/enable")
async def enable_autonomous_trading(
    parameters: dict,
    user: User = Depends(get_current_user)
):
    """Enable autonomous trading for user"""
    if autonomous_trader:
        # Enable in the real engine
        autonomous_trader.enable_for_user(user.id, parameters)
        
        return {
            "status": "enabled",
            "message": "Autonomous trading activated with live monitoring",
            "user_id": user.id,
            "parameters": {
                "max_position_size": parameters.get("max_position_size", 0.1),
                "risk_tolerance": parameters.get("risk_tolerance", "moderate"),
                "investment_amount": parameters.get("investment_amount", 100000),
                "stop_loss_percent": parameters.get("stop_loss_percent", 0.05),
                "take_profit_percent": parameters.get("take_profit_percent", 0.15),
                "bank_account_linked": True,
                "auto_debit_enabled": True
            },
            "next_steps": [
                "AI agents are now monitoring markets in real-time",
                "Trades will be executed automatically when opportunities arise",
                "You'll see positions appear as they're created",
                "Monitor performance in the dashboard"
            ],
            "engine_status": "Live and monitoring"
        }
    else:
        return {
            "status": "demo",
            "message": "Autonomous trading in demo mode",
            "user_id": user.id,
            "parameters": parameters
        }

@app.post("/api/v1/autonomous/disable")
async def disable_autonomous_trading(user: User = Depends(get_current_user)):
    """Disable autonomous trading for user"""
    if autonomous_trader:
        autonomous_trader.disable_for_user(user.id)
    
    return {
        "status": "disabled",
        "message": "Autonomous trading has been disabled"
    }

@app.post("/api/v1/autonomous/execute")
async def execute_autonomous_trade(
    trade_request: dict,
    user: User = Depends(get_current_user)
):
    """Execute autonomous trade based on AI analysis"""
    symbol = trade_request.get("symbol", "RELIANCE")
    
    if autonomous_trader:
        # Get current analysis
        market_data = autonomous_trader.market_simulator.get_market_data(symbol)
        if market_data:
            analysis = await autonomous_trader.analyze_stock(symbol, market_data)
            
            # Create order through the engine
            await autonomous_trader.create_autonomous_order(user.id, symbol, analysis)
            
            # Get the latest order
            user_orders = autonomous_trader.pending_orders.get(user.id, [])
            latest_order = user_orders[-1] if user_orders else None
            
            if latest_order:
                return {
                    "status": "executed",
                    "trade": {
                        "trade_id": latest_order["order_id"],
                        "user_id": user.id,
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": latest_order["quantity"],
                        "price": latest_order["price"],
                        "amount": latest_order["quantity"] * latest_order["price"],
                        "timestamp": latest_order["timestamp"].isoformat(),
                        "autonomous": True,
                        "consensus_confidence": latest_order["confidence"],
                        "stop_loss": latest_order["stop_loss"],
                        "take_profit": latest_order["take_profit"],
                        "execution_type": "AI-Driven"
                    },
                    "message": "Trade queued for execution in real-time engine"
                }
    
    # Fallback to mock execution
    return {
        "status": "demo",
        "message": "Demo trade execution"
    }

@app.get("/api/v1/autonomous/positions")
async def get_autonomous_positions(user: User = Depends(get_current_user)):
    """Get all autonomous trading positions"""
    if autonomous_trader:
        # Get real positions from the engine
        positions = autonomous_trader.get_user_positions(user.id)
        
        # Format positions for display
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                "trade_id": pos["position_id"],
                "symbol": pos["symbol"],
                "entry_price": pos["entry_price"],
                "current_price": pos["current_price"],
                "quantity": pos["quantity"],
                "pnl": round(pos["pnl"], 2),
                "pnl_percent": round(pos["pnl_percent"], 2),
                "status": pos["status"],
                "days_held": (datetime.now() - pos["entry_time"]).days,
                "stop_loss": pos["stop_loss"],
                "take_profit": pos["take_profit"],
                "ai_recommendation": "Hold" if pos["status"] == "ACTIVE" else pos.get("close_reason", "Closed"),
                "last_ai_review": "Real-time monitoring"
            })
        
        # Calculate summary
        total_invested = sum(p["entry_price"] * p["quantity"] for p in positions)
        total_value = sum(p["current_price"] * p["quantity"] for p in positions if p["status"] == "ACTIVE")
        total_pnl = sum(p["pnl"] for p in positions)
        
        # Get performance metrics
        performance = autonomous_trader.get_performance_metrics()
        
        return {
            "positions": formatted_positions,
            "summary": {
                "total_positions": len([p for p in positions if p["status"] == "ACTIVE"]),
                "total_invested": round(total_invested, 2),
                "current_value": round(total_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0,
                "ai_performance": {
                    "win_rate": performance.get("win_rate", "0%"),
                    "average_return": f"+{performance.get('average_trade', 0):.2f}",
                    "total_trades": performance.get("total_trades", 0),
                    "status": "Live Trading" if user.id in autonomous_trader.enabled_users else "Monitoring Only"
                }
            },
            "next_actions": [
                {
                    "symbol": symbol,
                    "action": "Monitoring",
                    "confidence": f"{analysis['consensus']['confidence']}" if 'analysis' in locals() else "Active",
                    "expected_time": "Continuous"
                } for symbol in autonomous_trader.market_simulator.stocks.keys()
            ][:3]  # Show top 3
        }
    else:
        # Return mock data
        return {
            "positions": [],
            "summary": {
                "total_positions": 0,
                "ai_performance": {"status": "Demo Mode"}
            }
        }

# Fund Management Endpoints

@app.get("/api/v1/funds/list")
async def get_fund_list(user: User = Depends(get_current_user)):
    """Get list of available mutual funds and ETFs"""
    if autonomous_trader:
        funds = []
        for fund_id, fund_data in autonomous_trader.fund_analyzer.funds.items():
            performance = autonomous_trader.fund_analyzer.fund_performance.get(fund_id, {})
            funds.append({
                "fund_id": fund_id,
                "name": fund_data["name"],
                "type": fund_data["type"],
                "category": fund_data["category"],
                "expense_ratio": fund_data["expense_ratio"],
                "nav": performance.get("current_nav", fund_data["nav"]),
                "returns": fund_data["returns"],
                "risk_rating": fund_data["risk_rating"],
                "sharpe_ratio": fund_data["sharpe_ratio"],
                "day_change": performance.get("day_change", 0),
                "aum": fund_data["aum"]
            })
        return {"funds": funds}
    else:
        return {"funds": []}

@app.get("/api/v1/funds/analyze/{fund_id}")
async def analyze_fund(fund_id: str, user: User = Depends(get_current_user)):
    """Get multi-agent analysis for a fund"""
    if autonomous_trader:
        analysis = await autonomous_trader.analyze_fund(fund_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Fund {fund_id} not found")
        return analysis
    else:
        return {
            "fund_id": fund_id,
            "fund_name": "Demo Fund",
            "agents": {
                "performance": {"returns": {"1Y": "25%"}, "recommendation": "Hold"},
                "risk": {"risk_rating": "Moderate", "volatility": "15%"},
                "tax": {"tax_status": "LTCG Eligible", "harvest_opportunity": False},
                "category": {"category_rank": "5/100", "expense_ratio": "1.5%"}
            },
            "consensus": {
                "action": "HOLD",
                "confidence": "75%",
                "recommendation": "Continue holding"
            }
        }

@app.get("/api/v1/funds/positions")
async def get_fund_positions(user: User = Depends(get_current_user)):
    """Get user's fund positions"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_fund_positions(user.id)
        
        # Calculate summary
        total_invested = sum(p["invested_value"] for p in positions)
        current_value = sum(p["current_value"] for p in positions)
        total_pnl = current_value - total_invested
        
        return {
            "positions": positions,
            "summary": {
                "total_funds": len(positions),
                "total_invested": round(total_invested, 2),
                "current_value": round(current_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0
            }
        }
    else:
        return {"positions": [], "summary": {}}

@app.post("/api/v1/funds/invest")
async def invest_in_fund(investment_data: dict, user: User = Depends(get_current_user)):
    """Invest in a mutual fund or ETF"""
    fund_id = investment_data.get("fund_id")
    amount = investment_data.get("amount", 10000)
    
    if autonomous_trader:
        fund = autonomous_trader.fund_analyzer.funds.get(fund_id)
        if not fund:
            raise HTTPException(status_code=404, detail=f"Fund {fund_id} not found")
            
        nav = autonomous_trader.fund_analyzer.fund_performance[fund_id]["current_nav"]
        units = amount / nav
        
        # Add position
        autonomous_trader.add_fund_position(user.id, fund_id, units, nav)
        
        return {
            "status": "success",
            "investment": {
                "fund_id": fund_id,
                "fund_name": fund["name"],
                "amount_invested": amount,
                "nav": nav,
                "units_allotted": round(units, 4),
                "timestamp": datetime.now().isoformat()
            },
            "message": f"Successfully invested ₹{amount:,.2f} in {fund['name']}"
        }
    else:
        return {"status": "demo", "message": "Demo investment"}

@app.get("/api/v1/funds/opportunities")
async def get_fund_opportunities(user: User = Depends(get_current_user)):
    """Get current fund switching opportunities"""
    if autonomous_trader:
        opportunities = await autonomous_trader.fund_analyzer.monitor_all_funds()
        
        # Filter for user's holdings
        user_positions = autonomous_trader.get_user_fund_positions(user.id)
        user_fund_ids = {p["fund_id"] for p in user_positions}
        
        relevant_opportunities = [
            opp for opp in opportunities 
            if opp["fund_id"] in user_fund_ids
        ]
        
        return {
            "opportunities": relevant_opportunities,
            "total_opportunities": len(relevant_opportunities),
            "potential_tax_savings": sum(
                10000 for opp in relevant_opportunities 
                if opp["action"] == "TAX_HARVEST"
            )
        }
    else:
        return {"opportunities": [], "total_opportunities": 0}

@app.get("/api/v1/funds/switches")
async def get_fund_switches(user: User = Depends(get_current_user)):
    """Get fund switch history"""
    if autonomous_trader:
        switches = autonomous_trader.get_fund_switch_history(user.id)
        return {
            "switches": switches,
            "total_switches": len(switches),
            "tax_harvested": sum(1 for s in switches if s.get("reason") == "tax_harvest")
        }
    else:
        return {"switches": [], "total_switches": 0}

@app.post("/api/v1/funds/enable-auto-switch")
async def enable_auto_switching(params: dict, user: User = Depends(get_current_user)):
    """Enable automatic fund switching"""
    if autonomous_trader:
        # Update user params to include fund management
        if user.id in autonomous_trader.enabled_users:
            autonomous_trader.enabled_users[user.id]["include_funds"] = True
            autonomous_trader.enabled_users[user.id]["tax_harvest_enabled"] = params.get("tax_harvest", True)
            autonomous_trader.enabled_users[user.id]["switch_threshold"] = params.get("switch_threshold", 0.6)
        
        return {
            "status": "enabled",
            "message": "Automatic fund switching activated",
            "features": [
                "Multi-agent fund analysis",
                "Automatic tax-loss harvesting",
                "Performance-based switching",
                "Category optimization"
            ]
        }
    else:
        return {"status": "demo", "message": "Demo mode"}

# Fixed Income Endpoints

@app.get("/api/v1/bonds/list")
async def get_bond_list(user: User = Depends(get_current_user)):
    """Get list of available bonds"""
    if autonomous_trader:
        bonds = []
        for bond_id, bond_data in autonomous_trader.fixed_income_analyzer.bonds.items():
            performance = autonomous_trader.fixed_income_analyzer.bond_performance.get(bond_id, {})
            bonds.append({
                "bond_id": bond_id,
                "name": bond_data["name"],
                "type": bond_data["type"],
                "rating": bond_data["rating"],
                "maturity": bond_data["maturity"].isoformat() if bond_data.get("maturity") else None,
                "coupon": bond_data["coupon"],
                "yield": performance.get("current_yield", bond_data["yield"]),
                "price": performance.get("current_price", bond_data["price"]),
                "duration": bond_data["duration"],
                "liquidity": bond_data["liquidity"],
                "min_investment": bond_data["min_investment"],
                "accrued_interest": performance.get("accrued_interest", 0),
                "days_to_maturity": performance.get("days_to_maturity", 0)
            })
        return {"bonds": bonds}
    else:
        return {"bonds": []}

@app.get("/api/v1/bonds/analyze/{bond_id}")
async def analyze_bond(bond_id: str, user: User = Depends(get_current_user)):
    """Get multi-agent analysis for a bond"""
    if autonomous_trader:
        analysis = await autonomous_trader.analyze_bond(bond_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Bond {bond_id} not found")
        return analysis
    else:
        return {
            "bond_id": bond_id,
            "bond_name": "Demo Bond",
            "agents": {
                "fixed_income": {"yield_to_maturity": "7.5%", "value_assessment": "Fair"},
                "credit": {"credit_rating": "AAA", "spread_trend": "Stable"},
                "duration": {"modified_duration": "4.5", "rate_environment": "Rising"},
                "yield": {"curve_position": "Belly", "total_return_potential": "8.2%"}
            },
            "consensus": {
                "action": "HOLD",
                "confidence": "75%",
                "recommendation": "Continue holding"
            }
        }

@app.get("/api/v1/bonds/positions")
async def get_bond_positions(user: User = Depends(get_current_user)):
    """Get user's bond positions"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_bond_positions(user.id)
        
        # Calculate summary
        total_invested = sum(p["purchase_value"] for p in positions)
        current_value = sum(p["current_value"] for p in positions)
        total_pnl = current_value - total_invested
        annual_income = sum(p["coupon"] * p["units"] for p in positions)
        
        return {
            "positions": positions,
            "summary": {
                "total_bonds": len(positions),
                "total_invested": round(total_invested, 2),
                "current_value": round(current_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0,
                "annual_income": round(annual_income, 2),
                "current_yield": round((annual_income / current_value) * 100, 2) if current_value > 0 else 0
            }
        }
    else:
        return {"positions": [], "summary": {}}

@app.post("/api/v1/bonds/invest")
async def invest_in_bond(investment_data: dict, user: User = Depends(get_current_user)):
    """Invest in a bond"""
    bond_id = investment_data.get("bond_id")
    units = investment_data.get("units", 1)
    
    if autonomous_trader:
        bond = autonomous_trader.fixed_income_analyzer.bonds.get(bond_id)
        if not bond:
            raise HTTPException(status_code=404, detail=f"Bond {bond_id} not found")
            
        price = autonomous_trader.fixed_income_analyzer.bond_performance[bond_id]["current_price"]
        
        # Add position
        autonomous_trader.add_bond_position(user.id, bond_id, units, price)
        
        return {
            "status": "success",
            "investment": {
                "bond_id": bond_id,
                "bond_name": bond["name"],
                "units": units,
                "price": price,
                "total_investment": units * price * bond["min_investment"] / 100,
                "timestamp": datetime.now().isoformat()
            },
            "message": f"Successfully invested in {bond['name']}"
        }
    else:
        return {"status": "demo", "message": "Demo investment"}

@app.post("/api/v1/bonds/construct-ladder")
async def construct_bond_ladder(ladder_params: dict, user: User = Depends(get_current_user)):
    """Construct a bond ladder"""
    amount = ladder_params.get("amount", 1000000)
    strategy = ladder_params.get("strategy", "moderate")
    
    if autonomous_trader:
        ladder = await autonomous_trader.construct_bond_ladder(user.id, amount, strategy)
        
        return {
            "status": "success",
            "ladder": ladder,
            "message": f"Successfully constructed {strategy} bond ladder with {ladder['rungs']} rungs"
        }
    else:
        return {"status": "demo", "message": "Demo ladder"}

@app.get("/api/v1/bonds/yield-curve")
async def get_yield_curve(user: User = Depends(get_current_user)):
    """Get current yield curve data"""
    if autonomous_trader:
        yield_curve = autonomous_trader.fixed_income_analyzer.yield_curve
        market_conditions = autonomous_trader.fixed_income_analyzer.market_conditions
        
        return {
            "yield_curve": yield_curve,
            "market_conditions": market_conditions,
            "curve_shape": autonomous_trader.fixed_income_analyzer._get_curve_shape(),
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "yield_curve": {"1Y": 6.5, "5Y": 7.5, "10Y": 8.1},
            "market_conditions": {"rate_environment": "rising"}
        }

@app.get("/api/v1/bonds/rollovers")
async def get_bond_rollovers(user: User = Depends(get_current_user)):
    """Get upcoming bond maturities and rollover recommendations"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_bond_positions(user.id)
        
        upcoming_maturities = []
        for pos in positions:
            if pos["days_to_maturity"] < 90 and pos["days_to_maturity"] > 0:
                rollover = await autonomous_trader.fixed_income_analyzer.manage_rollover(
                    pos["bond_id"],
                    pos["current_value"]
                )
                upcoming_maturities.append({
                    "position": pos,
                    "rollover_recommendation": rollover
                })
                
        return {
            "upcoming_maturities": upcoming_maturities,
            "total_maturing": len(upcoming_maturities)
        }
    else:
        return {"upcoming_maturities": [], "total_maturing": 0}

@app.get("/api/v1/bonds/trades")
async def get_bond_trades(user: User = Depends(get_current_user)):
    """Get bond trading history"""
    if autonomous_trader:
        trades = autonomous_trader.get_bond_trades_history(user.id)
        return {
            "trades": trades,
            "total_trades": len(trades),
            "duration_adjustments": sum(1 for t in trades if t.get("trade_type") == "duration_adjustment"),
            "credit_events": sum(1 for t in trades if t.get("trade_type") == "credit_event"),
            "rollovers": sum(1 for t in trades if t.get("trade_type") == "rollover")
        }
    else:
        return {"trades": [], "total_trades": 0}

@app.post("/api/v1/bonds/enable-auto-management")
async def enable_bond_auto_management(params: dict, user: User = Depends(get_current_user)):
    """Enable automatic bond management"""
    if autonomous_trader:
        # Update user params to include bond management
        if user.id in autonomous_trader.enabled_users:
            autonomous_trader.enabled_users[user.id]["include_bonds"] = True
            autonomous_trader.enabled_users[user.id]["bond_strategy"] = params.get("strategy", "moderate")
            autonomous_trader.enabled_users[user.id]["rate_hedging"] = params.get("rate_hedging", True)
        
        return {
            "status": "enabled",
            "message": "Automatic bond management activated",
            "features": [
                "Yield curve monitoring",
                "Credit event detection",
                "Duration adjustment for rate changes",
                "Automatic ladder rollover"
            ]
        }
    else:
        return {"status": "demo", "message": "Demo mode"}

# Commodity Endpoints

@app.get("/api/v1/commodities/list")
async def get_commodity_list(user: User = Depends(get_current_user)):
    """Get list of available commodities"""
    if autonomous_trader:
        commodities = []
        for commodity_id, commodity_data in autonomous_trader.commodity_analyzer.commodities.items():
            performance = autonomous_trader.commodity_analyzer.commodity_performance.get(commodity_id, {})
            commodities.append({
                "commodity_id": commodity_id,
                "name": commodity_data["name"],
                "symbol": commodity_data["symbol"],
                "type": commodity_data["type"],
                "price": performance.get("current_price", commodity_data["price"]),
                "currency": commodity_data["currency"],
                "unit": commodity_data["unit"],
                "daily_change": performance.get("daily_change_percent", 0),
                "ytd_return": performance.get("ytd_return", 0),
                "volatility": commodity_data["volatility"],
                "safe_haven_score": commodity_data["safe_haven_score"],
                "correlation_to_inflation": commodity_data["correlation_to_inflation"],
                "liquidity": commodity_data["liquidity"]
            })
        return {"commodities": commodities}
    else:
        return {"commodities": []}

@app.get("/api/v1/commodities/analyze/{commodity_id}")
async def analyze_commodity(commodity_id: str, user: User = Depends(get_current_user)):
    """Get multi-agent analysis for a commodity"""
    if autonomous_trader:
        analysis = await autonomous_trader.analyze_commodity(commodity_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Commodity {commodity_id} not found")
        return analysis
    else:
        return {
            "commodity_id": commodity_id,
            "commodity_name": "Demo Commodity",
            "agents": {
                "commodity": {"price_trend": "Uptrend", "momentum_signal": "Buy"},
                "macro": {"macro_score": "7.5/10", "dollar_impact": "Positive"},
                "hedge": {"safe_haven_score": "0.95", "hedge_effectiveness": "Excellent"},
                "inflation": {"current_inflation": "3.7%", "inflation_protection": "Good"}
            },
            "consensus": {
                "action": "BUY",
                "confidence": "85%",
                "recommendation": "Increase allocation"
            }
        }

@app.get("/api/v1/commodities/positions")
async def get_commodity_positions(user: User = Depends(get_current_user)):
    """Get user's commodity positions"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_commodity_positions(user.id)
        
        # Calculate summary
        total_invested = sum(p["purchase_value"] for p in positions)
        current_value = sum(p["current_value"] for p in positions)
        total_pnl = current_value - total_invested
        
        return {
            "positions": positions,
            "summary": {
                "total_commodities": len(positions),
                "total_invested": round(total_invested, 2),
                "current_value": round(current_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0,
                "portfolio_allocation": round((current_value / 10000000) * 100, 2)  # Assuming 10M portfolio
            }
        }
    else:
        return {"positions": [], "summary": {}}

@app.post("/api/v1/commodities/invest")
async def invest_in_commodity(investment_data: dict, user: User = Depends(get_current_user)):
    """Invest in a commodity"""
    commodity_id = investment_data.get("commodity_id")
    units = investment_data.get("units", 1)
    
    if autonomous_trader:
        commodity = autonomous_trader.commodity_analyzer.commodities.get(commodity_id)
        if not commodity:
            raise HTTPException(status_code=404, detail=f"Commodity {commodity_id} not found")
            
        price = autonomous_trader.commodity_analyzer.commodity_performance[commodity_id]["current_price"]
        
        # Add position
        autonomous_trader.add_commodity_position(user.id, commodity_id, units, price)
        
        return {
            "status": "success",
            "investment": {
                "commodity_id": commodity_id,
                "commodity_name": commodity["name"],
                "units": units,
                "price": price,
                "total_investment": units * price,
                "timestamp": datetime.now().isoformat()
            },
            "message": f"Successfully invested in {commodity['name']}"
        }
    else:
        return {"status": "demo", "message": "Demo investment"}

@app.get("/api/v1/commodities/macro-indicators")
async def get_macro_indicators(user: User = Depends(get_current_user)):
    """Get current macro indicators"""
    if autonomous_trader:
        indicators = autonomous_trader.get_macro_indicators()
        
        return {
            **indicators,
            "market_conditions": {
                "favorable_for_gold": sum([
                    1 if indicators["indicators"]["US_CPI"]["value"] > 3 else 0,
                    1 if indicators["indicators"]["US_DOLLAR_INDEX"]["trend"] == "falling" else 0,
                    1 if indicators["indicators"]["GEOPOLITICAL_RISK"]["value"] > 60 else 0,
                    1 if indicators["uncertainty_metrics"]["market_stress"] > 0.5 else 0
                ]) >= 2
            }
        }
    else:
        return {
            "indicators": {},
            "uncertainty_metrics": {},
            "market_conditions": {"favorable_for_gold": True}
        }

@app.post("/api/v1/commodities/hedge-portfolio")
async def hedge_portfolio(hedge_params: dict, user: User = Depends(get_current_user)):
    """Execute portfolio hedge with commodities"""
    if autonomous_trader:
        # Get current allocation
        portfolio_value = await autonomous_trader.get_portfolio_value(user.id)
        commodity_value = await autonomous_trader.get_commodity_value(user.id)
        current_allocation = commodity_value / portfolio_value if portfolio_value > 0 else 0
        
        # Execute hedge
        hedge_result = await autonomous_trader.commodity_analyzer.execute_hedge(
            portfolio_value,
            current_allocation
        )
        
        if hedge_result["action"] != "No adjustment needed":
            await autonomous_trader.execute_commodity_hedge(user.id, hedge_result)
            
        return {
            "status": "success",
            "hedge_result": hedge_result,
            "message": f"Portfolio hedge {hedge_result['action']} executed"
        }
    else:
        return {"status": "demo", "message": "Demo hedge"}

@app.post("/api/v1/commodities/rebalance-inflation")
async def rebalance_for_inflation(user: User = Depends(get_current_user)):
    """Rebalance commodities based on inflation"""
    if autonomous_trader:
        # Force rebalance check
        current_inflation = autonomous_trader.commodity_analyzer.macro_indicators["US_CPI"]["value"]
        portfolio = {
            "commodity_positions": autonomous_trader.commodity_positions.get(user.id, [])
        }
        
        rebalance_result = await autonomous_trader.commodity_analyzer.rebalance_for_inflation(
            portfolio,
            current_inflation
        )
        
        if rebalance_result["rebalance_needed"]:
            await autonomous_trader.execute_inflation_rebalance(user.id, rebalance_result)
            
        return {
            "status": "success",
            "rebalance_result": rebalance_result,
            "message": "Inflation-based rebalancing completed"
        }
    else:
        return {"status": "demo", "message": "Demo rebalance"}

@app.get("/api/v1/commodities/trades")
async def get_commodity_trades(user: User = Depends(get_current_user)):
    """Get commodity trading history"""
    if autonomous_trader:
        trades = autonomous_trader.get_commodity_trades_history(user.id)
        return {
            "trades": trades,
            "total_trades": len(trades),
            "hedge_trades": sum(1 for t in trades if t.get("trade_type") == "hedge"),
            "rebalance_trades": sum(1 for t in trades if t.get("trade_type") == "rebalance")
        }
    else:
        return {"trades": [], "total_trades": 0}

@app.post("/api/v1/commodities/enable-auto-management")
async def enable_commodity_auto_management(params: dict, user: User = Depends(get_current_user)):
    """Enable automatic commodity management"""
    if autonomous_trader:
        # Update user params to include commodity management
        if user.id in autonomous_trader.enabled_users:
            autonomous_trader.enabled_users[user.id]["include_commodities"] = True
            autonomous_trader.enabled_users[user.id]["hedge_strategy"] = params.get("strategy", "balanced")
            autonomous_trader.enabled_users[user.id]["inflation_protection"] = params.get("inflation_protection", True)
        
        return {
            "status": "enabled",
            "message": "Automatic commodity management activated",
            "features": [
                "Global macro indicator monitoring",
                "Uncertainty spike hedging",
                "Inflation-based rebalancing",
                "Safe haven allocation"
            ]
        }
    else:
        return {"status": "demo", "message": "Demo mode"}

# Alternative Investment Endpoints

@app.get("/api/v1/alternatives/list")
async def get_alternative_list(user: User = Depends(get_current_user)):
    """Get list of alternative investments"""
    if autonomous_trader:
        alternatives = []
        for alt_id, alt_data in autonomous_trader.alternative_analyzer.alternatives.items():
            performance = autonomous_trader.alternative_analyzer.alternative_performance.get(alt_id, {})
            alternatives.append({
                "alternative_id": alt_id,
                "name": alt_data["name"],
                "symbol": alt_data.get("symbol", alt_id),
                "type": alt_data["type"],
                "sub_type": alt_data.get("sub_type", "General"),
                "current_value": performance.get("current_price", alt_data.get("price", alt_data.get("nav", 0))),
                "currency": alt_data.get("currency", "USD"),
                "daily_change": performance.get("daily_change_percent", 0),
                "ytd_return": performance.get("ytd_return", 0),
                "liquidity": alt_data.get("liquidity", "Unknown"),
                "min_investment": alt_data.get("min_investment", 0),
                "sharpe_ratio": performance.get("sharpe_ratio", 0)
            })
        return {"alternatives": alternatives}
    else:
        return {"alternatives": []}

@app.get("/api/v1/alternatives/analyze/{alt_id}")
async def analyze_alternative(alt_id: str, user: User = Depends(get_current_user)):
    """Get multi-agent analysis for an alternative investment"""
    if autonomous_trader:
        analysis = await autonomous_trader.analyze_alternative(alt_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Alternative {alt_id} not found")
        return analysis
    else:
        return {
            "alternative_id": alt_id,
            "alternative_name": "Demo Alternative",
            "agents": {
                "alternative": {"asset_type": "REIT", "performance_ytd": "15.2%"},
                "opportunity": {"opportunity_score": "0.85/1.0", "market_timing": "Favorable"},
                "liquidity": {"liquidity_score": "6.5/10", "days_to_liquidate": "3-30 days"},
                "risk": {"overall_risk_score": "4.2/10", "volatility_percentile": "25-50%"}
            },
            "consensus": {
                "action": "INVEST",
                "confidence": "82%",
                "recommendation": "Strong opportunity"
            }
        }

@app.get("/api/v1/alternatives/positions")
async def get_alternative_positions(user: User = Depends(get_current_user)):
    """Get user's alternative investment positions"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_alternative_positions(user.id)
        
        # Calculate summary
        total_invested = sum(p["purchase_value"] for p in positions)
        current_value = sum(p["current_value"] for p in positions)
        total_pnl = current_value - total_invested
        
        # Liquidity breakdown
        liquid_value = sum(p["current_value"] for p in positions if p["liquidity"] in ["Very High", "High"])
        illiquid_value = sum(p["current_value"] for p in positions if p["liquidity"] in ["Low", "Very Low", "Illiquid"])
        
        return {
            "positions": positions,
            "summary": {
                "total_alternatives": len(positions),
                "total_invested": round(total_invested, 2),
                "current_value": round(current_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0,
                "liquid_portion": round(liquid_value, 2),
                "illiquid_portion": round(illiquid_value, 2),
                "portfolio_allocation": round((current_value / 10000000) * 100, 2)
            }
        }
    else:
        return {"positions": [], "summary": {}}

@app.post("/api/v1/alternatives/invest")
async def invest_in_alternative(investment_data: dict, user: User = Depends(get_current_user)):
    """Invest in an alternative investment"""
    alt_id = investment_data.get("alternative_id")
    units = investment_data.get("units", 1)
    
    if autonomous_trader:
        alternative = autonomous_trader.alternative_analyzer.alternatives.get(alt_id)
        if not alternative:
            raise HTTPException(status_code=404, detail=f"Alternative {alt_id} not found")
            
        price = autonomous_trader.alternative_analyzer.alternative_performance[alt_id]["current_price"]
        
        # Add position
        autonomous_trader.add_alternative_position(user.id, alt_id, units, price)
        
        return {
            "status": "success",
            "investment": {
                "alternative_id": alt_id,
                "alternative_name": alternative["name"],
                "units": units,
                "price": price,
                "total_investment": units * price,
                "timestamp": datetime.now().isoformat()
            },
            "message": f"Successfully invested in {alternative['name']}"
        }
    else:
        return {"status": "demo", "message": "Demo investment"}

@app.get("/api/v1/alternatives/opportunities")
async def get_discovered_opportunities(user: User = Depends(get_current_user)):
    """Get discovered alternative investment opportunities"""
    if autonomous_trader:
        opportunities = autonomous_trader.get_discovered_opportunities(user.id)
        
        return {
            "opportunities": opportunities,
            "total_opportunities": len(opportunities),
            "high_priority": sum(1 for o in opportunities if o.get("fit_score", 0) > 0.8),
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "opportunities": [
                {
                    "id": "CARBON_CREDITS",
                    "name": "Carbon Credit Trading Platform",
                    "type": "Environmental",
                    "expected_return": 0.15,
                    "risk_level": "Medium",
                    "fit_score": 0.85,
                    "recommendation": "High priority - allocate immediately"
                }
            ],
            "total_opportunities": 1
        }

@app.post("/api/v1/alternatives/invest-opportunity")
async def invest_in_opportunity(opportunity_data: dict, user: User = Depends(get_current_user)):
    """Invest in a discovered opportunity"""
    opportunity_id = opportunity_data.get("opportunity_id")
    amount = opportunity_data.get("amount", 100000)
    
    if autonomous_trader:
        result = await autonomous_trader.invest_in_opportunity(user.id, opportunity_id, amount)
        return result
    else:
        return {"status": "demo", "message": "Demo opportunity investment"}

@app.get("/api/v1/alternatives/liquidity-profile")
async def get_liquidity_profile(user: User = Depends(get_current_user)):
    """Get liquidity profile of alternative investments"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_alternative_positions(user.id)
        
        portfolio = {
            "alternative_positions": positions
        }
        
        liquidity_result = await autonomous_trader.alternative_analyzer.manage_liquidity(portfolio)
        
        return liquidity_result
    else:
        return {
            "current_liquidity_profile": {
                "immediate": 0.35,
                "short_term": 0.25,
                "medium_term": 0.25,
                "long_term": 0.15
            },
            "liquidity_score": 6.5
        }

@app.get("/api/v1/alternatives/trades")
async def get_alternative_trades(user: User = Depends(get_current_user)):
    """Get alternative investment trading history"""
    if autonomous_trader:
        trades = autonomous_trader.get_alternative_trades_history(user.id)
        return {
            "trades": trades,
            "total_trades": len(trades),
            "opportunity_investments": sum(1 for t in trades if t.get("trade_type") == "new_opportunity")
        }
    else:
        return {"trades": [], "total_trades": 0}

@app.post("/api/v1/alternatives/enable-auto-discovery")
async def enable_alternative_auto_discovery(params: dict, user: User = Depends(get_current_user)):
    """Enable automatic opportunity discovery"""
    if autonomous_trader:
        # Update user params to include alternative discovery
        if user.id in autonomous_trader.enabled_users:
            autonomous_trader.enabled_users[user.id]["include_alternatives"] = True
            autonomous_trader.enabled_users[user.id]["alternative_strategy"] = params.get("strategy", "balanced")
            autonomous_trader.enabled_users[user.id]["liquidity_preference"] = params.get("liquidity_preference", "medium")
        
        return {
            "status": "enabled",
            "message": "Automatic alternative investment discovery activated",
            "features": [
                "Opportunity discovery across asset classes",
                "REITs, crypto, and art allocation",
                "Liquidity management",
                "Risk-adjusted recommendations"
            ]
        }
    else:
        return {"status": "demo", "message": "Demo mode"}

# Global Asset Endpoints

@app.get("/api/v1/global/assets")
async def get_global_assets(user: User = Depends(get_current_user)):
    """Get list of global assets"""
    if autonomous_trader:
        assets = []
        for asset_id, asset_data in autonomous_trader.global_asset_analyzer.global_assets.items():
            performance = autonomous_trader.global_asset_analyzer.asset_performance.get(asset_id, {})
            assets.append({
                "asset_id": asset_id,
                "name": asset_data["name"],
                "symbol": asset_data["symbol"],
                "type": asset_data["type"],
                "region": asset_data["region"],
                "country": asset_data["country"],
                "currency": asset_data["currency"],
                "price": performance.get("current_price", asset_data["price"]),
                "daily_change": performance.get("daily_change_percent", 0),
                "ytd_return": performance.get("ytd_return", 0),
                "local_return": performance.get("local_currency_return", 0),
                "usd_return": performance.get("usd_return", 0),
                "expense_ratio": asset_data.get("expense_ratio", 0),
                "is_hedged": asset_data.get("currency_hedged", False)
            })
        return {"assets": assets}
    else:
        return {"assets": []}

@app.get("/api/v1/global/analyze/{asset_id}")
async def analyze_global_asset(asset_id: str, user: User = Depends(get_current_user)):
    """Get multi-agent analysis for a global asset"""
    if autonomous_trader:
        analysis = await autonomous_trader.analyze_global_asset(asset_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return analysis
    else:
        return {
            "asset_id": asset_id,
            "asset_name": "Demo Global Asset",
            "agents": {
                "global": {"region": "North America", "regional_score": "7.5/10"},
                "macro": {"gdp_growth": "2.5%", "macro_score": "8.0/10"},
                "currency": {"base_currency": "USD", "hedge_recommendation": "No hedging needed"},
                "growth": {"projected_growth": "3.2%", "rebalance_signal": "Hold"}
            },
            "consensus": {
                "action": "OVERWEIGHT",
                "confidence": "78%",
                "recommendation": "Increase allocation"
            }
        }

@app.get("/api/v1/global/positions")
async def get_global_positions(user: User = Depends(get_current_user)):
    """Get user's global asset positions"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_global_positions(user.id)
        
        # Calculate regional allocation
        regional_allocation = {}
        total_value = sum(p["current_value"] for p in positions)
        
        for position in positions:
            region = position["region"]
            regional_allocation[region] = regional_allocation.get(region, 0) + position["current_value"]
            
        return {
            "positions": positions,
            "summary": {
                "total_positions": len(positions),
                "total_value": round(total_value, 2),
                "regional_allocation": {k: round(v/total_value * 100, 1) for k, v in regional_allocation.items()} if total_value > 0 else {},
                "currency_exposure": autonomous_trader.get_currency_exposures(user.id)
            }
        }
    else:
        return {"positions": [], "summary": {}}

@app.post("/api/v1/global/invest")
async def invest_in_global_asset(investment_data: dict, user: User = Depends(get_current_user)):
    """Invest in a global asset"""
    asset_id = investment_data.get("asset_id")
    units = investment_data.get("units", 1)
    
    if autonomous_trader:
        asset = autonomous_trader.global_asset_analyzer.global_assets.get(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
            
        price = autonomous_trader.global_asset_analyzer.asset_performance[asset_id]["current_price"]
        
        # Add position
        autonomous_trader.add_global_position(user.id, asset_id, units, price)
        
        return {
            "status": "success",
            "investment": {
                "asset_id": asset_id,
                "asset_name": asset["name"],
                "units": units,
                "price": price,
                "total_investment": units * price,
                "currency": asset["currency"],
                "timestamp": datetime.now().isoformat()
            },
            "message": f"Successfully invested in {asset['name']}"
        }
    else:
        return {"status": "demo", "message": "Demo investment"}

@app.get("/api/v1/global/regional-growth")
async def get_regional_growth(user: User = Depends(get_current_user)):
    """Get regional growth projections"""
    if autonomous_trader:
        growth_data = autonomous_trader.get_regional_growth_data()
        
        return {
            **growth_data,
            "recommendations": {
                region: "Overweight" if data["projected_growth"] > 3 else "Neutral"
                for region, data in growth_data["regional_data"].items()
            }
        }
    else:
        return {
            "regional_data": {},
            "exchange_rates": {},
            "recommendations": {}
        }

@app.get("/api/v1/global/currency-exposure")
async def get_currency_exposure(user: User = Depends(get_current_user)):
    """Get currency exposure analysis"""
    if autonomous_trader:
        exposures = autonomous_trader.get_currency_exposures(user.id)
        
        # Get portfolio for optimization
        positions = autonomous_trader.get_user_global_positions(user.id)
        portfolio = {"global_positions": positions}
        
        optimization = await autonomous_trader.global_asset_analyzer.optimize_currency_exposure(portfolio)
        
        return {
            **exposures,
            **optimization
        }
    else:
        return {
            "exposures": {"USD": "60%", "EUR": "20%", "JPY": "10%", "Other": "10%"},
            "total_foreign_exposure": "40%"
        }

@app.post("/api/v1/global/hedge-currency")
async def hedge_currency(hedge_data: dict, user: User = Depends(get_current_user)):
    """Execute currency hedge"""
    currency = hedge_data.get("currency")
    hedge_ratio = hedge_data.get("hedge_ratio", 1.0)
    
    if autonomous_trader:
        result = await autonomous_trader.execute_currency_hedge(user.id, currency, hedge_ratio)
        return result
    else:
        return {"status": "demo", "message": "Demo hedge executed"}

@app.post("/api/v1/global/rebalance-geographic")
async def rebalance_geographic(user: User = Depends(get_current_user)):
    """Rebalance geographic allocation"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_global_positions(user.id)
        portfolio = {"global_positions": positions}
        
        rebalance_result = await autonomous_trader.global_asset_analyzer.rebalance_geographic_allocation(portfolio)
        
        # Record rebalancing
        if len(rebalance_result["rebalancing_trades"]) > 0:
            autonomous_trader.global_trades.append({
                "user_id": user.id,
                "trade_type": "geographic_rebalance",
                "trades": rebalance_result["rebalancing_trades"],
                "timestamp": datetime.now()
            })
            
        return {
            "status": "success",
            **rebalance_result
        }
    else:
        return {"status": "demo", "message": "Demo rebalancing"}

@app.get("/api/v1/global/trades")
async def get_global_trades(user: User = Depends(get_current_user)):
    """Get global asset trading history"""
    if autonomous_trader:
        trades = autonomous_trader.get_global_trades_history(user.id)
        return {
            "trades": trades,
            "total_trades": len(trades),
            "hedge_trades": sum(1 for t in trades if t.get("trade_type") == "currency_hedge"),
            "rebalance_trades": sum(1 for t in trades if t.get("trade_type") == "geographic_rebalance")
        }
    else:
        return {"trades": [], "total_trades": 0}

@app.post("/api/v1/global/enable-auto-management")
async def enable_global_auto_management(params: dict, user: User = Depends(get_current_user)):
    """Enable automatic global asset management"""
    if autonomous_trader:
        # Update user params to include global management
        if user.id in autonomous_trader.enabled_users:
            autonomous_trader.enabled_users[user.id]["include_global"] = True
            autonomous_trader.enabled_users[user.id]["hedge_strategy"] = params.get("hedge_strategy", "dynamic")
            autonomous_trader.enabled_users[user.id]["rebalance_frequency"] = params.get("rebalance_frequency", "monthly")
        
        return {
            "status": "enabled",
            "message": "Automatic global asset management activated",
            "features": [
                "Currency exposure monitoring",
                "Dynamic hedging recommendations",
                "Geographic rebalancing based on growth",
                "FX impact optimization"
            ]
        }
    else:
        return {"status": "demo", "message": "Demo mode"}

# ESG Investment Endpoints

@app.get("/api/v1/esg/investments")
async def get_esg_investments(user: User = Depends(get_current_user)):
    """Get list of ESG investments"""
    if autonomous_trader:
        investments = []
        for inv_id, inv_data in autonomous_trader.esg_analyzer.esg_investments.items():
            performance = autonomous_trader.esg_analyzer.investment_performance.get(inv_id, {})
            investments.append({
                "investment_id": inv_id,
                "name": inv_data["name"],
                "symbol": inv_data["symbol"],
                "type": inv_data["type"],
                "category": inv_data["category"],
                "price": performance.get("current_price", inv_data["price"]),
                "daily_change": performance.get("daily_change_percent", 0),
                "esg_score": inv_data["esg_score"],
                "environmental_score": inv_data["environmental_score"],
                "social_score": inv_data["social_score"],
                "governance_score": inv_data["governance_score"],
                "carbon_intensity": inv_data["carbon_intensity"],
                "controversy_score": inv_data["controversy_score"],
                "impact_score": performance.get("impact_score", 0),
                "controversy_alert": performance.get("controversy_alert", False)
            })
        return {"investments": investments}
    else:
        return {"investments": []}

@app.get("/api/v1/esg/analyze/{investment_id}")
async def analyze_esg_investment(investment_id: str, user: User = Depends(get_current_user)):
    """Get multi-agent analysis for an ESG investment"""
    if autonomous_trader:
        analysis = await autonomous_trader.analyze_esg_investment(investment_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Investment {investment_id} not found")
        return analysis
    else:
        return {
            "investment_id": investment_id,
            "investment_name": "Demo ESG Investment",
            "agents": {
                "esg": {"overall_score": "8.5/10", "rating": "Excellent"},
                "impact": {"impact_score": "85.0/100", "tangible_outcomes": ["CO2 reduction"]},
                "risk": {"controversy_score": "0.5/10", "controversy_level": "Minimal"},
                "values": {"values_match": "92%", "aligned_themes": ["Climate Action"]}
            },
            "consensus": {
                "action": "STRONG BUY",
                "confidence": "88%",
                "recommendation": "Excellent ESG profile with high impact"
            }
        }

@app.get("/api/v1/esg/positions")
async def get_esg_positions(user: User = Depends(get_current_user)):
    """Get user's ESG positions"""
    if autonomous_trader:
        positions = autonomous_trader.get_user_esg_positions(user.id)
        
        # Calculate category breakdown
        category_breakdown = {}
        total_value = sum(p["current_value"] for p in positions)
        
        for position in positions:
            category = position["category"]
            category_breakdown[category] = category_breakdown.get(category, 0) + position["current_value"]
            
        return {
            "positions": positions,
            "summary": {
                "total_positions": len(positions),
                "total_value": round(total_value, 2),
                "category_breakdown": {k: round(v/total_value * 100, 1) for k, v in category_breakdown.items()} if total_value > 0 else {},
                "avg_esg_score": round(sum(p["esg_score"] for p in positions) / len(positions), 1) if positions else 0,
                "controversy_alerts": sum(1 for p in positions if p.get("controversy_alert", False))
            }
        }
    else:
        return {"positions": [], "summary": {}}

@app.post("/api/v1/esg/invest")
async def invest_in_esg(investment_data: dict, user: User = Depends(get_current_user)):
    """Invest in an ESG investment"""
    investment_id = investment_data.get("investment_id")
    units = investment_data.get("units", 1)
    
    if autonomous_trader:
        investment = autonomous_trader.esg_analyzer.esg_investments.get(investment_id)
        if not investment:
            raise HTTPException(status_code=404, detail=f"Investment {investment_id} not found")
            
        price = autonomous_trader.esg_analyzer.investment_performance[investment_id]["current_price"]
        
        # Add position
        autonomous_trader.add_esg_position(user.id, investment_id, units, price)
        
        # Record trade
        autonomous_trader.esg_trades.append({
            "user_id": user.id,
            "investment_id": investment_id,
            "trade_type": "buy",
            "units": units,
            "price": price,
            "timestamp": datetime.now()
        })
        
        return {
            "status": "success",
            "investment": {
                "investment_id": investment_id,
                "investment_name": investment["name"],
                "units": units,
                "price": price,
                "total_investment": units * price,
                "esg_score": investment["esg_score"],
                "timestamp": datetime.now().isoformat()
            },
            "message": f"Successfully invested in {investment['name']}"
        }
    else:
        return {"status": "demo", "message": "Demo investment"}

@app.get("/api/v1/esg/themes")
async def get_esg_themes(user: User = Depends(get_current_user)):
    """Get ESG themes and focus areas"""
    if autonomous_trader:
        themes = autonomous_trader.get_esg_themes()
        
        return {
            "themes": [
                {
                    "name": theme,
                    "priority": data["priority"],
                    "impact_focus": data["impact_focus"],
                    "investment_count": len(data["investments"])
                }
                for theme, data in themes.items()
            ],
            "categories": ["Environmental", "Social", "Broad ESG"]
        }
    else:
        return {"themes": [], "categories": []}

@app.post("/api/v1/esg/screen-portfolio")
async def screen_portfolio_values(values_data: dict, user: User = Depends(get_current_user)):
    """Screen portfolio for values alignment"""
    values_profile = values_data.get("values_profile", "balanced_esg")
    
    if autonomous_trader:
        positions = autonomous_trader.get_user_esg_positions(user.id)
        
        if positions:
            screening_result = await autonomous_trader.esg_analyzer.screen_portfolio_values(
                [{"investment_id": p["investment_id"], "value": p["current_value"]} for p in positions],
                values_profile
            )
            
            return screening_result
        else:
            return {
                "values_profile": values_profile,
                "aligned_count": 0,
                "exclusion_count": 0,
                "portfolio_values_score": 0
            }
    else:
        return {"status": "demo", "message": "Demo screening"}

@app.get("/api/v1/esg/portfolio-impact")
async def get_portfolio_impact(user: User = Depends(get_current_user)):
    """Calculate portfolio-wide ESG impact"""
    if autonomous_trader:
        impact = await autonomous_trader.calculate_portfolio_impact(user.id)
        return impact
    else:
        return {
            "total_impacts": {
                "CO2 Avoided": "1,500,000 tons/year",
                "Renewable Capacity": "25,000 MW",
                "People Benefited": "500,000"
            },
            "portfolio_impact_score": "78.5/100",
            "impact_rating": "High Impact"
        }

@app.get("/api/v1/esg/controversies")
async def get_controversies(user: User = Depends(get_current_user)):
    """Get active ESG controversies"""
    if autonomous_trader:
        all_controversies = autonomous_trader.get_controversy_alerts()
        user_positions = autonomous_trader.get_user_esg_positions(user.id)
        
        # Filter to user's holdings
        user_controversies = {}
        for position in user_positions:
            inv_id = position["investment_id"]
            if inv_id in all_controversies:
                user_controversies[inv_id] = all_controversies[inv_id]
                
        return {
            "controversies": user_controversies,
            "total_alerts": sum(len(c) for c in user_controversies.values()),
            "affected_holdings": len(user_controversies)
        }
    else:
        return {"controversies": {}, "total_alerts": 0}

@app.post("/api/v1/esg/set-values-profile")
async def set_values_profile(profile_data: dict, user: User = Depends(get_current_user)):
    """Set user's values alignment profile"""
    profile = profile_data.get("profile", "balanced_esg")
    
    if autonomous_trader:
        autonomous_trader.set_values_profile(user.id, profile)
        
        return {
            "status": "success",
            "profile": profile,
            "message": f"Values profile set to {profile}"
        }
    else:
        return {"status": "demo", "message": "Demo profile set"}

@app.post("/api/v1/esg/enable-monitoring")
async def enable_esg_monitoring(params: dict, user: User = Depends(get_current_user)):
    """Enable automatic ESG monitoring"""
    if autonomous_trader:
        values_profile = params.get("values_profile", "balanced_esg")
        
        # Enable ESG management
        autonomous_trader.enable_esg_management(user.id, values_profile)
        
        return {
            "status": "enabled",
            "message": "ESG monitoring activated",
            "features": [
                "Real-time controversy monitoring",
                "Automatic divestment from violations",
                "Values-based portfolio screening",
                "Impact tracking and reporting"
            ]
        }
    else:
        return {"status": "demo", "message": "Demo mode"}

@app.get("/api/v1/esg/search")
async def search_esg_investments(
    min_esg_score: float = 7.0,
    max_carbon: float = 100.0,
    category: Optional[str] = None,
    exclude_controversies: bool = True,
    user: User = Depends(get_current_user)
):
    """Search ESG investments with filters"""
    if autonomous_trader:
        criteria = {
            "min_esg_score": min_esg_score,
            "max_carbon_intensity": max_carbon,
            "category": category,
            "exclude_controversies": exclude_controversies
        }
        
        results = autonomous_trader.search_esg_investments(criteria)
        
        return {
            "results": results[:20],  # Top 20 results
            "total_found": len(results),
            "filters_applied": criteria
        }
    else:
        return {"results": [], "total_found": 0}

@app.get("/api/v1/esg/trades")
async def get_esg_trades(user: User = Depends(get_current_user)):
    """Get ESG trading history"""
    if autonomous_trader:
        trades = autonomous_trader.get_esg_trades_history(user.id)
        
        return {
            "trades": trades,
            "total_trades": len(trades),
            "divestments": sum(1 for t in trades if t.get("trade_type") == "controversy_divestment"),
            "values_trades": sum(1 for t in trades if "values" in t.get("reason", ""))
        }
    else:
        return {"trades": [], "total_trades": 0}

@app.post("/api/v1/kyc/submit")
async def submit_kyc(
    request: Request,
    email: str = Depends(verify_token)
):
    # In a real app, this would validate and store KYC data
    # For demo, we'll simulate successful submission
    
    # Parse form data
    form = await request.form()
    
    kyc_data = {
        "panNumber": form.get("panNumber"),
        "aadhaarNumber": form.get("aadhaarNumber"),
        "dateOfBirth": form.get("dateOfBirth"),
        "address": form.get("address"),
        "email": email,
        "submittedAt": datetime.now(timezone.utc).isoformat(),
        "status": "submitted",
        "verificationStatus": "pending"
    }
    
    # Simulate processing time and verification
    # In production, this would trigger actual verification process
    verification_id = f"KYC{datetime.now(timezone.utc).timestamp():.0f}"
    
    return {
        "message": "KYC submitted successfully",
        "verificationId": verification_id,
        "status": "submitted",
        "estimatedVerificationTime": "24-48 hours",
        "kycData": {
            "panNumber": kyc_data["panNumber"][-4:] if kyc_data["panNumber"] else "",
            "aadhaarNumber": kyc_data["aadhaarNumber"][-4:] if kyc_data["aadhaarNumber"] else "",
            "submittedAt": kyc_data["submittedAt"]
        }
    }

@app.get("/api/v1/kyc/status")
async def get_kyc_status(email: str = Depends(verify_token)):
    # Mock KYC status
    return {
        "status": "verified",
        "verificationId": "KYC1234567890",
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "kycLevel": 2,
        "limits": {
            "dailyTransactionLimit": 1000000,
            "monthlyTransactionLimit": 10000000,
            "singleTransactionLimit": 500000
        }
    }

# Update the main function to show new endpoints
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🚀 Starting Oryza Test API for Frontend")
    print("=" * 50)
    print(f"📁 Mock data directory: {MOCK_DATA_DIR}")
    print(f"🌐 API will be available at: http://localhost:8889/api/v1")
    print(f"🤖 AI models available: {AI_AVAILABLE}")
    print("📊 Test endpoints:")
    print("   Core Features:")
    print("   - POST /api/v1/auth/login    - Login (use test@oryza.com / test@123)")
    print("   - GET  /api/v1/portfolio     - Get portfolio data")
    print("   - GET  /api/v1/market/overview - Get market data")
    print("   AI Features:")
    print("   - GET  /api/v1/ai/risk-assessment - AI risk analysis")
    print("   - GET  /api/v1/ai/esg-score/{symbol} - ESG scoring")
    print("   - POST /api/v1/ai/sentiment-analysis - News sentiment")
    print("   - POST /api/v1/ai/backtest   - Strategy backtesting")
    print("   New Features:")
    print("   - POST /api/v1/paper-trading/* - Paper trading")
    print("   - GET  /api/v1/marketplace/*   - AI agent marketplace")
    print("   - GET  /api/v1/social/*        - Social trading")
    print("   - GET  /api/v1/education/*     - Learning platform")
    print("   - POST /api/v1/assistant/*     - Voice/chat assistant")
    print("   - POST /api/v1/tax/*           - Tax optimization")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8889) 