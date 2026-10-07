"""
Oryza API Gateway - Routes requests to microservices
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv

from .middleware import AuthMiddleware, RateLimitMiddleware, LoggingMiddleware

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
SERVICE_URLS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
    "websocket": os.getenv("WEBSOCKET_SERVICE_URL", "http://localhost:8002"),
    "portfolio": os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003"),
    "trading": os.getenv("TRADING_SERVICE_URL", "http://localhost:8004"),
    "market": os.getenv("MARKET_SERVICE_URL", "http://localhost:8005"),
    "news": os.getenv("NEWS_SERVICE_URL", "http://localhost:8006"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8007"),
}

# HTTP client for proxying requests
http_client = httpx.AsyncClient(timeout=30.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    logger.info("Starting API Gateway...")
    yield
    logger.info("Shutting down API Gateway...")
    await http_client.aclose()


# Create FastAPI app
app = FastAPI(
    title="Oryza API Gateway",
    description="Central API Gateway for Oryza platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)
app.add_middleware(
    AuthMiddleware,
    exclude_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email"
    ]
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check connectivity to services
    services_status = {}
    
    for service_name, service_url in SERVICE_URLS.items():
        try:
            response = await http_client.get(f"{service_url}/health", timeout=2.0)
            services_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            services_status[service_name] = {
                "status": "unreachable",
                "error": str(e)
            }
    
    # Overall health
    all_healthy = all(
        s.get("status") == "healthy" 
        for s in services_status.values()
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "api-gateway",
        "version": "1.0.0",
        "services": services_status
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Oryza API Gateway",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "auth": "/api/v1/auth",
            "portfolio": "/api/v1/portfolio",
            "trading": "/api/v1/trading",
            "market": "/api/v1/market",
            "news": "/api/v1/news",
            "notifications": "/api/v1/notifications"
        }
    }


async def proxy_request(
    service_name: str,
    path: str,
    request: Request,
    **kwargs
) -> Any:
    """Proxy request to a microservice"""
    if service_name not in SERVICE_URLS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    service_url = SERVICE_URLS[service_name]
    url = f"{service_url}{path}"
    
    # Forward headers
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    # Add user info if authenticated
    if hasattr(request.state, "user"):
        headers["X-User-Id"] = request.state.user["user_id"]
        headers["X-User-Email"] = request.state.user["email"]
        headers["X-User-Role"] = request.state.user["role"]
    
    try:
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=await request.body() if request.method in ["POST", "PUT", "PATCH"] else None,
            **kwargs
        )
        
        # Return response
        return JSONResponse(
            content=response.json() if response.content else None,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Service '{service_name}' timeout"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service '{service_name}' is unavailable"
        )
    except Exception as e:
        logger.error(f"Error proxying to {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with service '{service_name}'"
        )


# Auth service routes
@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(path: str, request: Request):
    """Proxy auth service requests"""
    return await proxy_request("auth", f"/api/v1/auth/{path}", request)


# Portfolio service routes
@app.api_route("/api/v1/portfolio/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def portfolio_proxy(path: str, request: Request):
    """Proxy portfolio service requests"""
    return await proxy_request("portfolio", f"/api/v1/portfolio/{path}", request)


# Trading service routes
@app.api_route("/api/v1/trading/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def trading_proxy(path: str, request: Request):
    """Proxy trading service requests"""
    return await proxy_request("trading", f"/api/v1/trading/{path}", request)


# Market data service routes
@app.api_route("/api/v1/market/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def market_proxy(path: str, request: Request):
    """Proxy market data service requests"""
    return await proxy_request("market", f"/api/v1/market/{path}", request)


# News service routes
@app.api_route("/api/v1/news/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def news_proxy(path: str, request: Request):
    """Proxy news service requests"""
    return await proxy_request("news", f"/api/v1/news/{path}", request)


# Notification service routes
@app.api_route("/api/v1/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def notification_proxy(path: str, request: Request):
    """Proxy notification service requests"""
    return await proxy_request("notification", f"/api/v1/notifications/{path}", request)


# WebSocket info endpoint (WebSocket connections go directly to ws service)
@app.get("/api/v1/ws/info")
async def websocket_info():
    """Get WebSocket connection information"""
    return {
        "websocket_url": f"ws://localhost:8002/ws",
        "message": "Connect directly to WebSocket service",
        "authentication": "Pass JWT token as query parameter: ws://localhost:8002/ws?token=YOUR_TOKEN"
    }


# Catch-all for undefined routes
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str):
    """Catch all undefined routes"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "Route not found",
            "available_endpoints": [
                "/api/v1/auth",
                "/api/v1/portfolio",
                "/api/v1/trading",
                "/api/v1/market",
                "/api/v1/news",
                "/api/v1/notifications"
            ]
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main_gateway:app",
        host=host,
        port=port,
        reload=os.getenv("ENV", "development") == "development",
        log_level="info"
    ) 