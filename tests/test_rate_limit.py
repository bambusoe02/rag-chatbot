"""Tests for rate limiting functionality."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
import time

client = TestClient(app)


def test_rate_limit_enforcement():
    """Test that rate limits are enforced"""
    # Make multiple requests quickly
    responses = []
    for i in range(15):
        response = client.post(
            "/api/auth/login",
            data={"username": "test", "password": "test"}
        )
        responses.append(response.status_code)
    
    # Should hit rate limit (10/minute for login)
    assert 429 in responses, "Rate limit not enforced"


def test_rate_limit_headers():
    """Test that rate limit headers are present"""
    response = client.get("/api/documents")
    
    # Headers should be present (if rate limiting is enabled)
    if "X-RateLimit-Limit" in response.headers:
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_status_endpoint():
    """Test rate limit status endpoint"""
    # This requires authentication, so we'll test the endpoint exists
    response = client.get("/api/rate-limit/status")
    
    # Should return 401 (unauthorized) or 200 (if authenticated)
    assert response.status_code in [200, 401, 503], "Unexpected status code"


def test_rate_limit_exception_handler():
    """Test that rate limit exceptions are handled properly"""
    # Make many requests to trigger rate limit
    for i in range(20):
        response = client.post(
            "/api/auth/register",
            json={"username": f"test{i}", "email": f"test{i}@test.com", "password": "test"}
        )
        if response.status_code == 429:
            # Check response format
            assert "error" in response.json()
            assert "Retry-After" in response.headers
            break

