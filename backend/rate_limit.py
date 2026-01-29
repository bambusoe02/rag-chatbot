"""Rate limiting implementation for API protection."""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Optional
import redis
from datetime import datetime, timedelta
import json
import logging
from .models import User, APIKey
from .database import SessionLocal

logger = logging.getLogger(__name__)

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],
    storage_uri="memory://",  # Use memory by default, Redis optional
    headers_enabled=True,
)

# Optional Redis connection for distributed rate limiting
try:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(os.getenv("REDIS_DB", 0))
    
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()
    logger.info("✅ Connected to Redis for rate limiting")
    USE_REDIS = True
except Exception as e:
    redis_client = None
    logger.warning(f"⚠️  Redis not available, using in-memory rate limiting: {e}")
    USE_REDIS = False


class RateLimitConfig:
    """Rate limit configurations for different user types and endpoints"""
    
    # Per IP limits (for unauthenticated requests)
    IP_LIMITS = {
        "default": "100/hour",
        "strict": "10/minute",
    }
    
    # Per user limits (authenticated users)
    USER_LIMITS = {
        "user": "100/hour",
        "admin": "1000/hour",
        "enterprise": "10000/hour",
    }
    
    # Per API key limits
    API_KEY_LIMITS = {
        "default": "100/hour",
        "custom": None,  # Uses APIKey.rate_limit from database
    }
    
    # Endpoint-specific limits
    ENDPOINT_LIMITS = {
        "/api/auth/login": "10/minute",
        "/api/auth/register": "5/hour",
        "/api/documents/upload": "50/hour",
        "/api/chat": "200/hour",
    }


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting
    Priority: API Key > User ID > IP Address
    """
    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    
    # Check for authenticated user
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


def get_rate_limit_for_user(user: Optional[User]) -> str:
    """Get rate limit string based on user role"""
    if not user:
        return RateLimitConfig.IP_LIMITS["default"]
    
    role = user.role
    return RateLimitConfig.USER_LIMITS.get(role, RateLimitConfig.USER_LIMITS["user"])


def get_rate_limit_for_endpoint(endpoint: str) -> Optional[str]:
    """Get specific rate limit for endpoint if configured"""
    return RateLimitConfig.ENDPOINT_LIMITS.get(endpoint)


class RateLimitTracker:
    """Track rate limit usage with Redis or in-memory storage"""
    
    def __init__(self):
        self.memory_store = {}  # Fallback if Redis unavailable
    
    def _get_key(self, identifier: str, window: str) -> str:
        """Generate Redis/memory key for rate limit tracking"""
        return f"ratelimit:{identifier}:{window}"
    
    def check_limit(self, identifier: str, limit: int, window_seconds: int):
        """
        Check if request is within rate limit
        Returns: (is_allowed, info_dict)
        """
        key = self._get_key(identifier, f"{window_seconds}s")
        now = datetime.utcnow()
        
        if USE_REDIS and redis_client:
            return self._check_redis(key, limit, window_seconds, now)
        else:
            return self._check_memory(key, limit, window_seconds, now)
    
    def _check_redis(self, key: str, limit: int, window_seconds: int, now: datetime):
        """Check rate limit using Redis"""
        try:
            # Use Redis sliding window
            pipe = redis_client.pipeline()
            
            # Remove old entries
            window_start = (now - timedelta(seconds=window_seconds)).timestamp()
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
            
            # Set expiry
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            current_count = results[1]
            
            is_allowed = current_count < limit
            
            return is_allowed, {
                "limit": limit,
                "remaining": max(0, limit - current_count - 1),
                "reset": int((now + timedelta(seconds=window_seconds)).timestamp()),
                "current": current_count
            }
        
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to allowing request if Redis fails
            return True, {"limit": limit, "remaining": limit, "error": str(e)}
    
    def _check_memory(self, key: str, limit: int, window_seconds: int, now: datetime):
        """Check rate limit using in-memory storage"""
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Remove old entries
        window_start = now - timedelta(seconds=window_seconds)
        self.memory_store[key] = [
            ts for ts in self.memory_store[key]
            if ts > window_start
        ]
        
        current_count = len(self.memory_store[key])
        is_allowed = current_count < limit
        
        if is_allowed:
            self.memory_store[key].append(now)
        
        return is_allowed, {
            "limit": limit,
            "remaining": max(0, limit - current_count - 1),
            "reset": int((now + timedelta(seconds=window_seconds)).timestamp()),
            "current": current_count
        }
    
    def get_usage(self, identifier: str, window_seconds: int) -> dict:
        """Get current usage statistics"""
        key = self._get_key(identifier, f"{window_seconds}s")
        now = datetime.utcnow()
        
        if USE_REDIS and redis_client:
            try:
                window_start = (now - timedelta(seconds=window_seconds)).timestamp()
                count = redis_client.zcount(key, window_start, now.timestamp())
                return {"count": count, "window_seconds": window_seconds}
            except:
                return {"count": 0, "window_seconds": window_seconds, "error": "Redis unavailable"}
        else:
            if key in self.memory_store:
                window_start = now - timedelta(seconds=window_seconds)
                count = len([ts for ts in self.memory_store[key] if ts > window_start])
                return {"count": count, "window_seconds": window_seconds}
            return {"count": 0, "window_seconds": window_seconds}


# Global tracker instance
rate_tracker = RateLimitTracker()


def parse_rate_limit(limit_string: str):
    """
    Parse rate limit string like "100/hour" into (limit, seconds)
    Returns: (requests, window_seconds)
    """
    try:
        count, period = limit_string.split("/")
        count = int(count)
        
        period_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }
        
        seconds = period_map.get(period, 3600)
        return count, seconds
    except:
        # Default to 100/hour
        return 100, 3600


async def check_rate_limit(
    request: Request,
    limit_string: Optional[str] = None
) -> None:
    """
    Check rate limit for current request
    Raises HTTPException if limit exceeded
    """
    identifier = get_user_identifier(request)
    
    # Get rate limit
    if not limit_string:
        # Try endpoint-specific limit first
        limit_string = get_rate_limit_for_endpoint(request.url.path)
        
        # Fall back to user-based limit
        if not limit_string:
            user = getattr(request.state, "user", None)
            limit_string = get_rate_limit_for_user(user)
    
    limit, window_seconds = parse_rate_limit(limit_string)
    
    # Check limit
    is_allowed, info = rate_tracker.check_limit(identifier, limit, window_seconds)
    
    # Add headers
    request.state.rate_limit_info = info
    
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": info["limit"],
                "reset": info["reset"],
                "message": f"Too many requests. Please try again after {info['reset']}"
            },
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(info["reset"]),
                "Retry-After": str(window_seconds)
            }
        )


def add_rate_limit_headers(request: Request) -> dict:
    """Add rate limit headers to response"""
    if hasattr(request.state, "rate_limit_info"):
        info = request.state.rate_limit_info
        return {
            "X-RateLimit-Limit": str(info.get("limit", 0)),
            "X-RateLimit-Remaining": str(info.get("remaining", 0)),
            "X-RateLimit-Reset": str(info.get("reset", 0)),
        }
    return {}

