"""Security validation utilities for RAG Chatbot."""

import re
import html
from typing import Optional
from fastapi import HTTPException, UploadFile
from pathlib import Path
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

# Try to import magic (optional)
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, MIME type checking disabled")


class SecurityValidator:
    """Security validation utilities"""
    
    # Allowed MIME types for file uploads
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # docx
        'text/plain',
        'text/markdown',
    }
    
    # Max file sizes (in bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.rpm', '.dmg', '.pkg', '.sh', '.ps1'
    }
    
    @staticmethod
    def validate_file_upload(file: UploadFile) -> dict:
        """
        Comprehensive file upload validation
        Returns: dict with validation results
        Raises: HTTPException if validation fails
        """
        filename = file.filename
        
        # 1. Check filename
        if not filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # 2. Check file extension
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in SecurityValidator.DANGEROUS_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} is not allowed for security reasons"
            )
        
        allowed_exts = {'.pdf', '.docx', '.txt', '.md'}
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_exts)}"
            )
        
        # 3. Read file content (for size and MIME validation)
        content = file.file.read()
        file_size = len(content)
        
        # Reset file pointer
        file.file.seek(0)
        
        # 4. Check file size
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if file_size > SecurityValidator.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = SecurityValidator.MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {size_mb:.1f}MB (max: {max_mb}MB)"
            )
        
        # 5. Validate MIME type (magic number check)
        mime_type = "unknown"
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_buffer(content, mime=True)
                
                if mime_type not in SecurityValidator.ALLOWED_MIME_TYPES:
                    logger.warning(f"Suspicious file upload attempt: {filename} (MIME: {mime_type})")
                    raise HTTPException(
                        status_code=400,
                        detail=f"File content does not match allowed types. Detected: {mime_type}"
                    )
            except Exception as e:
                logger.error(f"MIME type detection failed: {e}")
                # Continue anyway - mime detection is best-effort
        
        # 6. Sanitize filename (remove dangerous characters)
        safe_filename = SecurityValidator.sanitize_filename(filename)
        
        # 7. Generate secure hash for storage
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        
        return {
            "original_filename": filename,
            "safe_filename": safe_filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "valid": True
        }
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks
        """
        # Remove path components
        filename = Path(filename).name
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Remove multiple dots (except file extension)
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            name = name.replace('.', '_')
            filename = f"{name}.{ext}"
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1)
            name = name[:250]
            filename = f"{name}.{ext}"
        
        return filename
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """
        Sanitize user input to prevent XSS and injection attacks
        """
        if not text:
            return ""
        
        # Truncate
        text = text[:max_length]
        
        # HTML escape
        text = html.escape(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        return text
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username
        - 3-30 characters
        - Alphanumeric, underscore, hyphen only
        - Must start with letter
        """
        if not username or len(username) < 3 or len(username) > 30:
            return False
        
        pattern = r'^[a-zA-Z][a-zA-Z0-9_-]*$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        Validate password strength
        Returns: dict with validation results and score
        """
        issues = []
        score = 0
        
        # Length check
        if len(password) < 8:
            issues.append("Password must be at least 8 characters")
        else:
            score += 20
        
        if len(password) >= 12:
            score += 10
        
        # Uppercase
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        else:
            score += 20
        
        # Lowercase
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        else:
            score += 20
        
        # Digits
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        else:
            score += 20
        
        # Special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        else:
            score += 10
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "score": score,
            "strength": "weak" if score < 40 else "medium" if score < 70 else "strong"
        }
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)


class SQLInjectionProtection:
    """SQL Injection protection utilities"""
    
    # Dangerous SQL keywords
    DANGEROUS_PATTERNS = [
        r'\b(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE)\b',
        r'(--|;|\/\*|\*\/)',
        r'(\bOR\b|\bAND\b).*=.*',
        r'UNION.*SELECT',
        r'exec\s*\(',
        r'script\s*>',
    ]
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """
        Check if text contains potential SQL injection
        Returns: True if suspicious, False if safe
        """
        if not text:
            return False
        
        text_upper = text.upper()
        
        for pattern in SQLInjectionProtection.DANGEROUS_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {text[:100]}")
                return True
        
        return False


class RateLimitBypass:
    """Detect rate limit bypass attempts"""
    
    SUSPICIOUS_USER_AGENTS = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 
        'python-requests', 'go-http-client'
    ]
    
    @staticmethod
    def is_suspicious_request(user_agent: Optional[str], ip: str) -> bool:
        """Detect suspicious requests that might try to bypass rate limits"""
        
        if not user_agent:
            logger.warning(f"Request with no user agent from {ip}")
            return True
        
        ua_lower = user_agent.lower()
        for suspicious in RateLimitBypass.SUSPICIOUS_USER_AGENTS:
            if suspicious in ua_lower:
                logger.warning(f"Suspicious user agent from {ip}: {user_agent}")
                return True
        
        return False


# Export singleton instances
security_validator = SecurityValidator()
sql_protection = SQLInjectionProtection()
rate_limit_bypass = RateLimitBypass()

