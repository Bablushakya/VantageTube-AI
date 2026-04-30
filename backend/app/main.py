"""
VantageTube AI - Main FastAPI Application
Entry point for the backend API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, users, youtube, seo, content, trending, generator
from app.utils.monitoring import request_logger, performance_metrics
import time


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered YouTube Creator Optimization Platform",
    debug=settings.DEBUG
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Add request/response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log requests and responses"""
    start_time = time.time()
    
    # Get user ID from request (if available)
    user_id = "anonymous"
    if hasattr(request.state, "user_id"):
        user_id = request.state.user_id
    
    # Log request
    request_logger.log_request(
        user_id=user_id,
        endpoint=request.url.path,
        method=request.method,
        parameters=dict(request.query_params)
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    response_time_ms = process_time * 1000
    
    # Log response
    request_logger.log_response(
        user_id=user_id,
        endpoint=request.url.path,
        status_code=response.status_code,
        response_time_ms=response_time_ms,
        response_size_bytes=len(response.body) if hasattr(response, 'body') else 0
    )
    
    # Add response time header
    response.headers["X-Process-Time"] = str(response_time_ms)
    
    return response


# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(youtube.router, prefix="/api")
app.include_router(seo.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(trending.router, prefix="/api")
app.include_router(generator.router)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
