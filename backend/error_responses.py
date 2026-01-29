"""Standardized error response utilities."""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class ErrorResponse:
    """Standardized error response format."""
    
    @staticmethod
    def create(
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """Create a standardized error response.
        
        Args:
            status_code: HTTP status code
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., "VALIDATION_ERROR")
            details: Additional error details
            
        Returns:
            HTTPException with standardized format
        """
        error_body = {
            "error": {
                "message": message,
                "status_code": status_code
            }
        }
        
        if error_code:
            error_body["error"]["code"] = error_code
        
        if details:
            error_body["error"]["details"] = details
        
        return HTTPException(status_code=status_code, detail=error_body)
    
    @staticmethod
    def validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Create a validation error response."""
        return ErrorResponse.create(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )
    
    @staticmethod
    def not_found(resource: str = "Resource") -> HTTPException:
        """Create a not found error response."""
        return ErrorResponse.create(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"{resource} not found",
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> HTTPException:
        """Create an unauthorized error response."""
        return ErrorResponse.create(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def forbidden(message: str = "Insufficient permissions") -> HTTPException:
        """Create a forbidden error response."""
        return ErrorResponse.create(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="FORBIDDEN"
        )
    
    @staticmethod
    def internal_error(message: str = "Internal server error", details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Create an internal server error response."""
        return ErrorResponse.create(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="INTERNAL_ERROR",
            details=details
        )
    
    @staticmethod
    def service_unavailable(message: str = "Service temporarily unavailable") -> HTTPException:
        """Create a service unavailable error response."""
        return ErrorResponse.create(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            error_code="SERVICE_UNAVAILABLE"
        )

