"""SQLAlchemy ORM models for database."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")  # user, admin, enterprise
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    """Document model for user uploads."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(50))
    upload_date = Column(DateTime, default=datetime.utcnow)
    chunks_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    
    owner = relationship("User", back_populates="documents")


class APIKey(Base):
    """API Key model for external access."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(255))
    api_key = Column(String(255), unique=True, index=True, nullable=False)
    permissions = Column(JSON)  # {"read": true, "write": true, "delete": false}
    rate_limit = Column(Integer, default=100)  # per hour
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="api_keys")


class Webhook(Base):
    """Webhook model for event notifications."""
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSON)  # ["document.uploaded", "query.completed"]
    secret = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="webhooks")


class WebhookDelivery(Base):
    """Webhook delivery logs."""
    __tablename__ = "webhook_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"))
    event_type = Column(String(100))
    payload = Column(JSON)
    status_code = Column(Integer)
    response = Column(Text)
    delivered_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    """Chat session model."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id"))
    role = Column(String(50))  # user, assistant
    content = Column(Text)
    sources = Column(JSON)
    rating = Column(Integer)  # -1, 0, 1 for thumbs down, none, thumbs up
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")


class TrainingData(Base):
    """Training data model for fine-tuning."""
    __tablename__ = "training_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text)
    context = Column(Text)
    answer = Column(Text)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_for_training = Column(Boolean, default=False)


class APIUsage(Base):
    """API usage tracking."""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    endpoint = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    status_code = Column(Integer)

