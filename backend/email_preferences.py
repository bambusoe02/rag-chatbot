"""Email preferences model for user notification settings."""

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from .database import Base


class EmailPreferences(Base):
    """User email notification preferences"""
    __tablename__ = "email_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Notification preferences
    document_processed = Column(Boolean, default=True)
    quota_warnings = Column(Boolean, default=True)
    api_key_created = Column(Boolean, default=True)
    security_alerts = Column(Boolean, default=True)
    newsletter = Column(Boolean, default=False)
    
    # Frequency
    digest_frequency = Column(String(50), default="daily")  # daily, weekly, never

