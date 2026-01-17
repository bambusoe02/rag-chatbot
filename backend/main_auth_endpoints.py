"""Additional auth-protected endpoints for enterprise features.

This file contains endpoints that need to be added to backend/main.py
after the existing endpoints.
"""

from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os
import secrets

from backend.database import get_db
from backend.db_models import User, Document, APIKey, Webhook, ChatSession, ChatMessage
from backend.auth import get_current_user, get_api_key_user
from backend.user_rag_engine import UserRAGEngine
from backend.webhooks import WebhookManager


# ==========================================
# MULTI-USER DOCUMENT ENDPOINTS
# ==========================================

@app.post("/api/documents/upload")
async def upload_document_multi_user(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and index a document (multi-user)."""
    try:
        # Create user-specific upload directory
        upload_dir = f"./data/uploads/user_{current_user.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = f"{upload_dir}/{file.filename}"
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Uploaded file for user {current_user.id}: {file.filename}")
        
        # Process with user-specific RAG engine
        rag_engine = UserRAGEngine(user_id=current_user.id)
        chunks, metadata = rag_engine.add_document(file_path, {"filename": file.filename})
        
        # Save to database
        doc = Document(
            user_id=current_user.id,
            filename=file.filename,
            original_name=file.filename,
            file_path=file_path,
            file_size=len(content),
            file_type=file.content_type,
            chunks_count=chunks
        )
        db.add(doc)
        db.commit()
        
        # Trigger webhook
        try:
            await WebhookManager.trigger_webhook(
                db=db,
                user_id=current_user.id,
                event_type="document.uploaded",
                payload={
                    "filename": file.filename,
                    "chunks": chunks,
                    "file_size": len(content)
                }
            )
        except Exception as e:
            logger.warning(f"Webhook trigger failed: {e}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks": chunks,
            "message": f"Document indexed successfully with {chunks} chunks"
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        # Clean up file on error
        file_path = f"./data/uploads/user_{current_user.id}/{file.filename}"
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents_multi_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents for current user."""
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_size": doc.file_size,
                "chunks_count": doc.chunks_count,
                "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            }
            for doc in docs
        ]
    }


@app.delete("/api/documents/{filename}")
async def delete_document_multi_user(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document (multi-user)."""
    # Get document from database
    doc = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.filename == filename
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from vector store
    rag_engine = UserRAGEngine(user_id=current_user.id)
    rag_engine.delete_document(filename)
    
    # Delete file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    # Delete from database
    db.delete(doc)
    db.commit()
    
    # Trigger webhook
    try:
        await WebhookManager.trigger_webhook(
            db=db,
            user_id=current_user.id,
            event_type="document.deleted",
            payload={"filename": filename}
        )
    except Exception as e:
        logger.warning(f"Webhook trigger failed: {e}")
    
    return {"status": "success", "message": f"Deleted {filename}"}


@app.post("/api/chat")
async def chat_multi_user(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query the RAG system (multi-user)."""
    try:
        question = request.get("question")
        search_mode = request.get("search_mode", "hybrid")
        temperature = request.get("temperature")
        top_k = request.get("top_k", 5)
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Use user-specific RAG engine
        rag_engine = UserRAGEngine(user_id=current_user.id)
        response = rag_engine.query(
            question=question,
            search_mode=search_mode,
            k=top_k,
            temperature=temperature,
        )
        
        # Save to chat history
        session_id = request.get("session_id", f"session_{datetime.now().timestamp()}")
        
        # Ensure session exists
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(user_id=current_user.id, session_id=session_id)
            db.add(session)
            db.commit()
        
        # Save messages
        user_msg = ChatMessage(session_id=session_id, role="user", content=question)
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response["answer"],
            sources=response.get("sources", [])
        )
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()
        
        # Trigger webhook
        try:
            await WebhookManager.trigger_webhook(
                db=db,
                user_id=current_user.id,
                event_type="query.completed",
                payload={
                    "question": question,
                    "answer_length": len(response["answer"]),
                    "sources_count": len(response.get("sources", [])),
                    "query_time": response.get("query_time", 0)
                }
            )
        except Exception as e:
            logger.warning(f"Webhook trigger failed: {e}")
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# API KEY ENDPOINTS
# ==========================================

@app.post("/api/api-keys")
async def create_api_key(
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
async def list_api_keys(
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
async def revoke_api_key(
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
async def create_webhook(
    url: str,
    events: list[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new webhook."""
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
async def list_webhooks(
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
async def delete_webhook(
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
async def api_v1_chat(
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

