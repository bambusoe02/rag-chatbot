"""Email service for sending notifications via SMTP."""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from premailer import transform
import os
from typing import Optional, List
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailConfig:
    """Email configuration from environment"""
    
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@ragchatbot.com")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "RAG Chatbot")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # Email features
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if email is properly configured"""
        return bool(cls.SMTP_USERNAME and cls.SMTP_PASSWORD and cls.EMAIL_ENABLED)


class EmailService:
    """Email service for sending notifications"""
    
    def __init__(self):
        self.config = EmailConfig()
        
        # Setup template environment
        template_dir = Path(__file__).parent / "email_templates"
        if template_dir.exists():
            self.template_env = Environment(
                loader=FileSystemLoader(str(template_dir))
            )
        else:
            logger.warning(f"Email templates directory not found: {template_dir}")
            self.template_env = None
        
        if not self.config.is_configured():
            logger.warning("⚠️  Email not configured, notifications will be disabled")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using SMTP
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.config.is_configured():
            logger.warning("Email not sent - service not configured")
            return False
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.config.SMTP_FROM_NAME} <{self.config.SMTP_FROM_EMAIL}>"
            message['To'] = to_email
            
            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)
            
            # Add text part
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                message.attach(text_part)
            
            # Add HTML part (inline CSS)
            html_with_inline_css = transform(html_body)
            html_part = MIMEText(html_with_inline_css, 'html')
            message.attach(html_part)
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.config.SMTP_HOST,
                port=self.config.SMTP_PORT,
                use_tls=self.config.SMTP_USE_TLS
            ) as smtp:
                await smtp.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                await smtp.send_message(message)
            
            logger.info(f"✅ Email sent to {to_email}: {subject}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def render_template(self, template_name: str, **context) -> str:
        """Render email template with context"""
        if not self.template_env:
            logger.error("Template environment not initialized")
            return ""
        
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return ""
    
    async def send_welcome_email(self, user_email: str, username: str):
        """Send welcome email to new user"""
        html = self.render_template(
            'welcome.html',
            username=username,
            login_url=os.getenv("APP_URL", "http://localhost:8501")
        )
        
        await self.send_email(
            to_email=user_email,
            subject="Welcome to RAG Chatbot!",
            html_body=html,
            text_body=f"Welcome {username}! Your account has been created successfully."
        )
    
    async def send_document_processed_email(
        self,
        user_email: str,
        username: str,
        filename: str,
        chunks_count: int
    ):
        """Notify user when document processing is complete"""
        html = self.render_template(
            'document_processed.html',
            username=username,
            filename=filename,
            chunks_count=chunks_count,
            app_url=os.getenv("APP_URL", "http://localhost:8501")
        )
        
        await self.send_email(
            to_email=user_email,
            subject=f"Document '{filename}' processed successfully",
            html_body=html,
            text_body=f"Hi {username}, your document '{filename}' has been processed into {chunks_count} chunks."
        )
    
    async def send_password_reset_email(
        self,
        user_email: str,
        username: str,
        reset_token: str
    ):
        """Send password reset email"""
        reset_url = f"{os.getenv('APP_URL', 'http://localhost:8501')}/reset-password?token={reset_token}"
        
        html = self.render_template(
            'password_reset.html',
            username=username,
            reset_url=reset_url,
            expiry_hours=24
        )
        
        await self.send_email(
            to_email=user_email,
            subject="Password Reset Request",
            html_body=html,
            text_body=f"Hi {username}, click this link to reset your password: {reset_url}"
        )
    
    async def send_api_key_created_email(
        self,
        user_email: str,
        username: str,
        key_name: str
    ):
        """Notify user when API key is created"""
        html = self.render_template(
            'api_key_created.html',
            username=username,
            key_name=key_name
        )
        
        await self.send_email(
            to_email=user_email,
            subject=f"New API Key Created: {key_name}",
            html_body=html,
            text_body=f"Hi {username}, a new API key '{key_name}' was created for your account."
        )
    
    async def send_quota_warning_email(
        self,
        user_email: str,
        username: str,
        usage_percent: float,
        limit: int
    ):
        """Send warning when user approaches rate limit"""
        html = self.render_template(
            'quota_warning.html',
            username=username,
            usage_percent=usage_percent,
            limit=limit
        )
        
        await self.send_email(
            to_email=user_email,
            subject="Rate Limit Warning - 80% Quota Used",
            html_body=html,
            text_body=f"Hi {username}, you've used {usage_percent}% of your rate limit ({limit} requests/hour)."
        )
    
    async def send_admin_alert(
        self,
        subject: str,
        message: str,
        severity: str = "info"
    ):
        """Send alert to admin"""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        
        html = self.render_template(
            'admin_alert.html',
            subject=subject,
            message=message,
            severity=severity,
            timestamp=datetime.utcnow().isoformat()
        )
        
        await self.send_email(
            to_email=admin_email,
            subject=f"[{severity.upper()}] {subject}",
            html_body=html,
            text_body=message
        )


# Global email service instance
email_service = EmailService()

