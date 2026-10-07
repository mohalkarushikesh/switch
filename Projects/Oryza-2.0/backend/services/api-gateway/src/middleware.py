"""
API Gateway Middleware
"""
import os
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"

# Security
security = HTTPBearer()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        now = time.time()
        if client_ip in self.clients:
            calls, last_reset = self.clients[client_ip]
            if now - last_reset > self.period:
                # Reset counter
                self.clients[client_ip] = (1, now)
            elif calls >= self.calls:
                # Rate limit exceeded
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": str(self.period)}
                )
            else:
                # Increment counter
                self.clients[client_ip] = (calls + 1, last_reset)
        else:
            # New client
            self.clients[client_ip] = (1, now)
        
        # Process request
        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/Response logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Duration: {duration:.3f}s"
        )
        
        return response


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user_from_token(token: str) -> Optional[dict]:
    """Extract user information from JWT token"""
    payload = decode_token(token)
    
    if not payload:
        return None
    
    # Check if it's an access token
    if payload.get("type") != "access":
        return None
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role")
    }


async def verify_token(request: Request) -> Optional[dict]:
    """Verify JWT token from request"""
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    return get_current_user_from_token(token)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected routes"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next):
        # Check if path is excluded
        path = request.url.path
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)
        
        # Verify authentication for protected routes
        if path.startswith("/api/v1/") and not path.startswith("/api/v1/auth/"):
            user = await verify_token(request)
            if not user:
                return Response(
                    content='{"detail": "Not authenticated"}',
                    status_code=401,
                    headers={"Content-Type": "application/json"}
                )
            
            # Add user info to request state
            request.state.user = user
        
        return await call_next(request)
