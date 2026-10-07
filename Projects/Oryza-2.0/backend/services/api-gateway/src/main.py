"""
API Gateway for Oryza - Main entry point for all API requests
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from prometheus_client import Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.settings import get_settings
from shared.database.connection import init_databases, close_databases
from shared.utils.logger import api_logger

# Import routers
from .routes import auth_router, health_router, proxy_router

settings = get_settings()
logger = api_logger.get_logger()

# Metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)
request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Oryza API Gateway")
    await init_databases()
    logger.info("Database connections initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Oryza API Gateway")
    await close_databases()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="Oryza API Gateway",
    description="Secure gateway for Oryza investment advisory platform",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=f"{settings.api_v1_prefix}/docs" if settings.debug else None,
    redoc_url=f"{settings.api_v1_prefix}/redoc" if settings.debug else None,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

if settings.app_env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.oryza.ai", "oryza.ai"]
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    start_time = time.time()
    logger.log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else "unknown"
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    
    # Log response
    logger.log_response(
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    # Update metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration_ms / 1000)
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.log_error(
        exc,
        context={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Don't expose internal errors in production
    if settings.app_env == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "request_id": request_id
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "request_id": request_id
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Oryza API Gateway",
        "version": settings.app_version,
        "status": "operational"
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


# Include routers
app.include_router(
    health_router,
    prefix=f"{settings.api_v1_prefix}/health",
    tags=["health"]
)

app.include_router(
    auth_router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["authentication"]
)

app.include_router(
    proxy_router,
    prefix=settings.api_v1_prefix,
    tags=["proxy"]
)


# Service discovery endpoint
@app.get(f"{settings.api_v1_prefix}/services")
async def list_services():
    """List available services"""
    return {
        "services": settings.service_registry,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_gateway_host,
        port=settings.api_gateway_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
