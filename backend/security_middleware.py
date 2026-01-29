"""Security middleware for request validation and headers."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' http://localhost:* ws://localhost:*; "
        )
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"
        
        # HTTPS enforcement (if in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate all incoming requests for security threats"""
    
    async def dispatch(self, request: Request, call_next):
        # Check for suspicious patterns in URL
        url_path = str(request.url.path)
        
        # Path traversal check
        if '..' in url_path or '//' in url_path:
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"Path traversal attempt from {client_ip}: {url_path}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request path"}
            )
        
        # Check request body size (if applicable)
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > 100 * 1024 * 1024:  # 100 MB
                        return JSONResponse(
                            status_code=413,
                            content={"error": "Request body too large"}
                        )
                except ValueError:
                    pass  # Invalid content-length, let it through
        
        response = await call_next(request)
        return response

