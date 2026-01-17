"""FastAPI application entry point."""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, File, HTTPException, UploadFile, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from loguru import logger

# Setup logging first
logging_enabled = False
try:
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/rag_chatbot.log", rotation="10 MB", retention="7 days", level="INFO")
    logging_enabled = True
except Exception:
    # If logging fails, continue without it
    pass

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="Production-ready RAG Chatbot with local Qwen LLM",
    version="1.0.0",
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG engine instance (legacy, for backward compatibility)
rag_engine: Optional[Any] = None

# Import database and auth
from backend.database import get_db, init_db
from backend.db_models import User, Document, APIKey, Webhook, ChatSession, ChatMessage
from backend.auth import (
    get_current_user, get_current_active_user, get_api_key_user,
    get_password_hash, verify_password, create_access_token,
    generate_api_key, ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.user_rag_engine import UserRAGEngine
from backend.webhooks import WebhookManager

# Pydantic schemas for auth
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global rag_engine
    
    logger.info("=" * 50)
    logger.info("Starting RAG Chatbot Enterprise API...")
    logger.info("=" * 50)
    
    # Create necessary directories
    os.makedirs("./data/uploads", exist_ok=True)
    os.makedirs("./data/chroma_db", exist_ok=True)
    os.makedirs("./data/chat_history", exist_ok=True)
    os.makedirs("./data/feedback", exist_ok=True)
    os.makedirs("./data/analytics", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    logger.info("✓ Data directories created")
    
    # Initialize database
    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Initialize legacy RAG engine (for backward compatibility)
    try:
        from backend.config import settings
        from backend.rag_engine import RAGEngine
        
        logger.info("Loading legacy RAG engine...")
        rag_engine = RAGEngine()
        logger.info("✓ Legacy RAG Engine initialized")
    except Exception as e:
        logger.warning(f"Legacy RAG engine not initialized: {e}")
        # Don't fail startup, user-specific engines will be created on demand


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "message": "RAG Chatbot Enterprise API is running",
        "rag_engine_loaded": rag_engine is not None
    }


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role="user"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user registered: {user.username}")
    return db_user


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.post("/api/auth/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    logger.info(f"Password changed for user: {current_user.username}")
    return {"message": "Password updated successfully"}


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        # Save file
        file_path = f"./data/uploads/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Uploaded file: {file.filename}")
        
        # Process document
        chunks, metadata = rag_engine.add_document(file_path, {"filename": file.filename})
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks": chunks,
            "message": f"Document indexed successfully with {chunks} chunks"
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        # Clean up file on error
        file_path = f"./data/uploads/{file.filename}"
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents():
    """List all indexed documents."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        docs = rag_engine.list_documents()
        return {"documents": docs}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document from the index."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        rag_engine.delete_document(filename)
        
        # Delete file
        file_path = f"./data/uploads/{filename}"
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {"status": "success", "message": f"Deleted {filename}"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: dict):
    """Query the RAG system with a question."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        from backend.analytics import analytics_tracker
        
        question = request.get("question", "")
        temperature = request.get("temperature")
        top_k = request.get("top_k")
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        answer, sources, query_time = rag_engine.query(
            question=question,
            temperature=temperature,
            top_k=top_k,
        )
        
        # Track the query for analytics
        try:
            documents_used = [s.filename if hasattr(s, 'filename') else s.get('filename', 'unknown') for s in sources]
            analytics_tracker.track_query(
                question=question,
                response_time=query_time,
                sources_count=len(sources),
                documents_used=documents_used,
            )
        except Exception as e:
            logger.warning(f"Failed to track query analytics: {e}")
        
        return {
            "answer": answer,
            "sources": [s.model_dump() if hasattr(s, 'model_dump') else s for s in sources],
            "query_time": query_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get analytics statistics."""
    try:
        from backend.analytics import analytics_tracker
        
        stats = analytics_tracker.get_stats()
        
        # Update document stats
        if rag_engine:
            doc_stats = rag_engine.get_stats()
            stats["total_documents"] = doc_stats.get("document_count", 0)
            stats["total_chunks"] = doc_stats.get("chunk_count", 0)
            analytics_tracker.update_document_stats(
                stats["total_documents"],
                stats["total_chunks"]
            )
        
        return stats
    except Exception as e:
        logger.error(f"Error getting analytics stats: {e}")
        # Fallback to document stats only
        if rag_engine:
            try:
                return rag_engine.get_stats()
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export/chat")
async def export_chat(request: dict):
    """Export chat session to TXT, JSON, or PDF.
    
    Expected: {"format": "txt|json|pdf", "session_id": str, "messages": list}
    """
    try:
        from backend.export import chat_exporter
        
        export_format = request.get("format", "txt").lower()
        session_id = request.get("session_id", "unknown")
        messages = request.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages to export")
        
        if export_format == "txt":
            content = chat_exporter.to_text(messages)
            return JSONResponse(content={"format": "txt", "content": content})
        elif export_format == "json":
            content = chat_exporter.to_json(messages, session_id)
            return JSONResponse(content={"format": "json", "content": content})
        elif export_format == "pdf":
            pdf_bytes = chat_exporter.to_pdf(messages, session_id)
            from fastapi.responses import Response
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="chat_{session_id}.pdf"'}
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {export_format}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/clear")
async def clear_all():
    """Clear all documents from the index."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        rag_engine.clear_all()
        
        # Clear uploaded files
        upload_dir = Path("./data/uploads")
        for file in upload_dir.glob("*"):
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()
        
        return {"status": "success", "message": "All documents cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{filename}/preview")
async def get_document_preview(filename: str, max_chars: int = 500):
    """Get document preview (first N characters).
    
    Args:
        filename: Name of the document
        max_chars: Maximum number of characters to return
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        from backend.document_processor import DocumentProcessor
        from backend.config import settings
        
        file_path = Path(settings.UPLOAD_DIR) / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {filename}")
        
        processor = DocumentProcessor()
        text, metadata = processor.extract_text(str(file_path))
        
        preview = text[:max_chars] + "..." if len(text) > max_chars else text
        
        return {
            "filename": filename,
            "preview": preview,
            "total_length": len(text),
            "metadata": metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/feedback")
async def save_feedback(request: dict):
    """Save user feedback on a response.
    
    Expected: {"question": str, "answer": str, "is_positive": bool, "comment": optional str}
    """
    try:
        from backend.feedback import feedback_handler
        from backend.analytics import analytics_tracker
        
        question = request.get("question", "")
        answer = request.get("answer", "")
        is_positive = request.get("is_positive", True)
        comment = request.get("comment")
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        feedback_handler.save_feedback(question, answer, is_positive, comment)
        analytics_tracker.track_feedback(question, is_positive)
        
        return {"status": "success", "message": "Feedback saved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/suggestions")
async def get_query_suggestions():
    """Get query suggestions based on uploaded documents."""
    try:
        from backend.suggestions import suggestion_generator
        
        documents = []
        if rag_engine:
            documents = rag_engine.list_documents()
        
        suggestions = suggestion_generator.generate_suggestions_from_documents(documents)
        templates = suggestion_generator.get_query_templates()
        
        return {
            "suggestions": suggestions,
            "templates": templates,
        }
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
async def get_settings():
    """Get current settings."""
    try:
        from backend.config import settings
        
        return {
            "temperature": settings.TEMPERATURE,
            "top_k": settings.TOP_K,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "ollama_model": settings.OLLAMA_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
        }
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def update_settings(new_settings: dict):
    """Update settings (note: these are session-specific, not persisted to .env).
    
    Expected: {"temperature": float, "top_k": int, "chunk_size": int, etc.}
    """
    # Note: This updates settings in memory but doesn't persist to .env
    # For production, you might want to save to user preferences file
    try:
        from backend.config import settings
        
        updated = {}
        if "temperature" in new_settings:
            settings.TEMPERATURE = float(new_settings["temperature"])
            updated["temperature"] = settings.TEMPERATURE
        
        if "top_k" in new_settings:
            settings.TOP_K = int(new_settings["top_k"])
            updated["top_k"] = settings.TOP_K
        
        if "chunk_size" in new_settings:
            settings.CHUNK_SIZE = int(new_settings["chunk_size"])
            updated["chunk_size"] = settings.CHUNK_SIZE
        
        if "chunk_overlap" in new_settings:
            settings.CHUNK_OVERLAP = int(new_settings["chunk_overlap"])
            updated["chunk_overlap"] = settings.CHUNK_OVERLAP
        
        return {"status": "success", "updated": updated}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{filename}/chunks")
async def get_document_chunks(filename: str):
    """Get all chunks for a specific document."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        # Get all chunks from vector store filtered by filename
        results = rag_engine.vector_store.collection.get(
            where={"filename": filename},
            limit=10000,
        )
        
        chunks = []
        if results and results.get("documents"):
            for idx, (doc_text, metadata) in enumerate(zip(
                results["documents"],
                results.get("metadatas", [])
            )):
                chunks.append({
                    "chunk_index": metadata.get("chunk_index", idx),
                    "content": doc_text,
                    "metadata": metadata,
                })
        
        return {
            "filename": filename,
            "chunks": sorted(chunks, key=lambda x: x["chunk_index"]),
            "total_chunks": len(chunks),
        }
    except Exception as e:
        logger.error(f"Error getting document chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/history")
async def get_chat_history(limit: int = 50):
    """Get query history.
    
    Args:
        limit: Maximum number of queries to return
    """
    try:
        from backend.analytics import analytics_tracker
        return {"queries": analytics_tracker.get_query_history(limit=limit)}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# API KEY ENDPOINTS
# ==========================================

@app.post("/api/api-keys")
async def create_api_key_endpoint(
    key_name: str,
    permissions: dict = {"read": True, "write": False, "delete": False},
    rate_limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key."""
    api_key = generate_api_key()
    
    db_key = APIKey(
        user_id=current_user.id,
        key_name=key_name,
        api_key=api_key,
        permissions=permissions,
        rate_limit=rate_limit
    )
    db.add(db_key)
    db.commit()
    
    logger.info(f"API key created for user {current_user.id}: {key_name}")
    
    return {
        "api_key": api_key,
        "key_name": key_name,
        "message": "Save this key - it won't be shown again!"
    }


@app.get("/api/api-keys")
async def list_api_keys_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys for current user."""
    keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return {
        "keys": [
            {
                "id": k.id,
                "key_name": k.key_name,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used": k.last_used.isoformat() if k.last_used else None,
                "is_active": k.is_active,
                "rate_limit": k.rate_limit
            }
            for k in keys
        ]
    }


@app.delete("/api/api-keys/{key_id}")
async def revoke_api_key_endpoint(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key."""
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.is_active = False
    db.commit()
    
    logger.info(f"API key revoked: {key.key_name}")
    return {"status": "revoked"}


# ==========================================
# WEBHOOK ENDPOINTS
# ==========================================

@app.post("/api/webhooks")
async def create_webhook_endpoint(
    url: str,
    events: list[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new webhook."""
    import secrets
    secret = secrets.token_urlsafe(32)
    
    webhook = Webhook(
        user_id=current_user.id,
        url=url,
        events=events,
        secret=secret
    )
    db.add(webhook)
    db.commit()
    
    logger.info(f"Webhook created for user {current_user.id}: {url}")
    
    return {
        "id": webhook.id,
        "url": url,
        "events": events,
        "secret": secret,
        "message": "Save the secret - it's used to verify webhook authenticity"
    }


@app.get("/api/webhooks")
async def list_webhooks_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all webhooks for current user."""
    webhooks = db.query(Webhook).filter(Webhook.user_id == current_user.id).all()
    return {
        "webhooks": [
            {
                "id": wh.id,
                "url": wh.url,
                "events": wh.events,
                "is_active": wh.is_active,
                "created_at": wh.created_at.isoformat() if wh.created_at else None,
            }
            for wh in webhooks
        ]
    }


@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook_endpoint(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a webhook."""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(webhook)
    db.commit()
    
    logger.info(f"Webhook deleted: {webhook.url}")
    return {"status": "deleted"}


# ==========================================
# EXTERNAL API ENDPOINT (API KEY AUTH)
# ==========================================

@app.post("/api/v1/chat")
async def api_v1_chat_endpoint(
    request: dict,
    user: User = Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """External API endpoint - requires API key."""
    try:
        question = request.get("question")
        search_mode = request.get("search_mode", "hybrid")
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Use user-specific RAG engine
        rag_engine = UserRAGEngine(user_id=user.id)
        response = rag_engine.query(question, search_mode=search_mode)
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API v1 chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
