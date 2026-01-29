"""Middleware for enforcing rate limiting on all requests."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .rate_limit import check_rate_limit, add_rate_limit_headers
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on all requests"""
    
    EXCLUDED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        try:
            # Check rate limit
            await check_rate_limit(request)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            headers = add_rate_limit_headers(request)
            for key, value in headers.items():
                response.headers[key] = value
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            raise

