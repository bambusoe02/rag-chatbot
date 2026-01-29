"""Middleware for tracking request metrics."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .metrics import request_count, errors_total, query_duration
import time
import logging

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record metrics
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            # Record duration for specific endpoints
            if "/api/chat" in request.url.path:
                duration = time.time() - start_time
                search_mode = request.query_params.get("search_mode", "hybrid")
                query_duration.labels(search_mode=search_mode).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error
            errors_total.labels(
                error_type=type(e).__name__,
                endpoint=request.url.path
            ).inc()
            
            logger.error(f"Error processing request: {e}")
            raise

