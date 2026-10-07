"""
API Gateway routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import httpx
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
import uuid

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.database.connection import get_db, DatabaseHealthCheck
from shared.database.models import User, UserRole
from shared.utils.auth import (
    AuthService, get_current_user, get_current_active_user,
    get_current_verified_user, Token
)
from shared.utils.logger import api_logger
from shared.config.settings import get_settings

settings = get_settings()
logger = api_logger.get_logger()

# Health router
health_router = APIRouter()

@health_router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@health_router.get("/detailed")
async def detailed_health_check():
    """Detailed health check including database connections"""
    db_health = await DatabaseHealthCheck.check_all()
    
    all_healthy = all(db_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "databases": db_health,
        "version": settings.app_version,
        "environment": settings.app_env
    }


# Auth router
auth_router = APIRouter()

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_verified: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


@auth_router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        username=user_data.username,
        hashed_password=AuthService.get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        role=UserRole.USER
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})
    
    # Log registration
    logger.log_audit(
        user_id=str(user.id),
        action="user_registered",
        resource="user",
        email=user.email
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    # Find user by email (username field in OAuth2 form)
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not AuthService.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})
    
    # Log login
    logger.log_audit(
        user_id=str(user.id),
        action="user_login",
        resource="auth",
        ip_address=form_data.client_id  # Can be used to pass IP
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )


@auth_router.post("/refresh")
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        payload = AuthService.decode_token(refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Generate new access token
        access_token = AuthService.create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@auth_router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout current user"""
    # In a real implementation, you might want to:
    # - Invalidate the token (store in Redis blacklist)
    # - Clear refresh token from database
    # - Log the logout event
    
    logger.log_audit(
        user_id=str(current_user.id),
        action="user_logout",
        resource="auth"
    )
    
    return {"message": "Successfully logged out"}


# Proxy router
proxy_router = APIRouter()

class ProxyService:
    """Service for proxying requests to internal services"""
    
    @staticmethod
    async def forward_request(
        service_name: str,
        path: str,
        request: Request,
        current_user: Optional[User] = None
    ) -> Response:
        """Forward request to internal service"""
        
        # Get service details
        service = settings.service_registry.get(service_name)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_name}' not found"
            )
        
        # Build target URL
        target_url = f"http://{service['host']}:{service['port']}{path}"
        
        # Prepare headers
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Add user context if authenticated
        if current_user:
            headers["X-User-ID"] = str(current_user.id)
            headers["X-User-Role"] = current_user.role.value
        
        # Add request ID
        headers["X-Request-ID"] = request.state.request_id
        
        # Forward the request
        async with httpx.AsyncClient() as client:
            try:
                # Get request body
                body = await request.body()
                
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    params=request.query_params,
                    content=body,
                    timeout=30.0
                )
                
                # Return response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
            except httpx.ConnectError:
                logger.error(f"Failed to connect to service: {service_name}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service '{service_name}' is unavailable"
                )
            except httpx.TimeoutException:
                logger.error(f"Request to service timed out: {service_name}")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Request to service '{service_name}' timed out"
                )


@proxy_router.api_route(
    "/{service_name}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_request(
    service_name: str,
    path: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Proxy authenticated requests to internal services"""
    return await ProxyService.forward_request(
        service_name=service_name,
        path=f"/{path}",
        request=request,
        current_user=current_user
    )


@proxy_router.api_route(
    "/public/{service_name}/{path:path}",
    methods=["GET", "POST"]
)
async def proxy_public_request(
    service_name: str,
    path: str,
    request: Request
):
    """Proxy public requests to internal services"""
    # Only allow specific public endpoints
    allowed_public_endpoints = [
        "screening-engine/search",
        "news-sentiment/latest",
        "advisory-engine/market-overview",
        "esg-advisor/trends"
    ]
    
    endpoint = f"{service_name}/{path}"
    if not any(endpoint.startswith(allowed) for allowed in allowed_public_endpoints):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires authentication"
        )
    
    return await ProxyService.forward_request(
        service_name=service_name,
        path=f"/{path}",
        request=request
    )
