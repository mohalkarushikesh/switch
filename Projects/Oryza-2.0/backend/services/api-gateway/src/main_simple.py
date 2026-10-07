"""
Simplified API Gateway for Oryza - Works without PostgreSQL/Redis
"""
from fastapi import FastAPI, Request, status, Depends, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

# Simple settings
class Settings:
    app_name = "Oryza API Gateway"
    app_version = "1.0.0"
    api_v1_prefix = "/api/v1"
    secret_key = "test-secret-key-for-development-only"
    algorithm = "HS256"
    access_token_expire_minutes = 30
    cors_origins = ["*"]
    cors_allow_credentials = True
    cors_allow_methods = ["*"]
    cors_allow_headers = ["*"]

settings = Settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mock user database
MOCK_USERS = {
    "test@oryza.com": {
        "id": "1",
        "email": "test@oryza.com",
        "username": "test",
        "hashed_password": pwd_context.hash("test@123"),
        "firstName": "Test",
        "lastName": "User",
        "role": "user",
        "isVerified": True,
        "createdAt": "2024-01-01T00:00:00Z"
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("Starting Oryza API Gateway (Simplified)")
    yield
    # Shutdown
    print("Shutting down Oryza API Gateway")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Simplified gateway for Oryza investment advisory platform",
    version=settings.app_version,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Oryza API Gateway is running!",
        "version": settings.app_version
    }

@app.get(f"{settings.api_v1_prefix}/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post(f"{settings.api_v1_prefix}/auth/login")
async def login(form_data: dict = Body(...)):
    """Login endpoint"""
    email = form_data.get("username", "")  # OAuth2 sends email as username
    password = form_data.get("password", "")
    
    # Check user
    user = MOCK_USERS.get(email)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": f"refresh_{access_token[:20]}",
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "role": user["role"],
            "isVerified": user["isVerified"],
            "createdAt": user["createdAt"]
        }
    }

@app.post(f"{settings.api_v1_prefix}/auth/register")
async def register(user_data: dict = Body(...)):
    """Register endpoint"""
    email = user_data.get("email", "")
    
    # Check if user exists
    if email in MOCK_USERS:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )
    
    # Create new user
    new_user = {
        "id": str(len(MOCK_USERS) + 1),
        "email": email,
        "username": user_data.get("username", email.split("@")[0]),
        "hashed_password": pwd_context.hash(user_data.get("password", "")),
        "firstName": user_data.get("firstName", "New"),
        "lastName": user_data.get("lastName", "User"),
        "role": "user",
        "isVerified": False,
        "createdAt": datetime.utcnow().isoformat()
    }
    
    MOCK_USERS[email] = new_user
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": new_user["email"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": f"refresh_{access_token[:20]}",
        "token_type": "bearer",
        "user": {k: v for k, v in new_user.items() if k != "hashed_password"}
    }

@app.get(f"{settings.api_v1_prefix}/auth/me")
async def get_current_user(authorization: str = None):
    """Get current user endpoint"""
    # For simplicity, return the test user
    user = MOCK_USERS.get("test@oryza.com")
    return {k: v for k, v in user.items() if k != "hashed_password"}

@app.post(f"{settings.api_v1_prefix}/auth/refresh")
async def refresh_token(data: dict = Body(...)):
    """Refresh token endpoint"""
    return {
        "access_token": create_access_token(data={"sub": "test@oryza.com"}),
        "token_type": "bearer"
    }

@app.post(f"{settings.api_v1_prefix}/auth/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Successfully logged out"}

@app.get(f"{settings.api_v1_prefix}/services")
async def list_services():
    """List available services"""
    return {
        "services": ["auth", "portfolio", "market", "advisory"],
        "version": settings.app_version
    }

# Mock service endpoints
@app.get(f"{settings.api_v1_prefix}/portfolio")
async def get_portfolio():
    """Mock portfolio endpoint"""
    return {
        "totalValue": 100000,
        "totalReturn": 15.5,
        "holdings": [
            {"symbol": "AAPL", "shares": 100, "value": 17500},
            {"symbol": "GOOGL", "shares": 50, "value": 12500}
        ]
    }

@app.get(f"{settings.api_v1_prefix}/market/overview")
async def market_overview():
    """Mock market overview"""
    return {
        "indices": [
            {"symbol": "SPY", "name": "S&P 500", "value": 450.25, "change": 1.5},
            {"symbol": "DIA", "name": "Dow Jones", "value": 380.10, "change": 0.8}
        ],
        "topGainers": [
            {"symbol": "TSLA", "name": "Tesla", "price": 250.00, "change": 5.2}
        ],
        "topLosers": [
            {"symbol": "META", "name": "Meta", "price": 320.00, "change": -2.1}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print(f"\n{'='*50}")
    print(f"🚀 Starting {settings.app_name} (Simplified)")
    print(f"{'='*50}")
    print(f"🌐 API will be available at: http://localhost:8080{settings.api_v1_prefix}")
    print(f"📊 Test credentials: test@oryza.com / test@123")
    print(f"{'='*50}\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080) 