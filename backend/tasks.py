"""Celery background tasks for async processing."""

from .celery_app import celery_app
from .database import SessionLocal
from .db_models import Document, User
from .user_rag_engine import UserRAGEngine
from .webhooks import WebhookManager
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Email tasks availability flag
EMAIL_TASKS_AVAILABLE = False
try:
    from .email_service import email_service
    EMAIL_TASKS_AVAILABLE = True
except ImportError:
    pass


@celery_app.task(bind=True, name='backend.tasks.process_document_task')
def process_document_task(self, document_id: int, user_id: int):
    """
    Process uploaded document in background
    - Extract text
    - Create chunks
    - Generate embeddings
    - Index in ChromaDB
    """
    logger.info(f"Starting document processing: doc_id={document_id}, user_id={user_id}")
    
    db = SessionLocal()
    
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting...', 'progress': 0})
        
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        # Verify user ownership
        if document.user_id != user_id:
            raise Exception(f"Document {document_id} does not belong to user {user_id}")
        
        # Initialize RAG engine
        self.update_state(state='PROGRESS', meta={'status': 'Initializing RAG engine', 'progress': 10})
        rag_engine = UserRAGEngine(user_id=user_id)
        
        # Process document
        self.update_state(state='PROGRESS', meta={'status': 'Extracting text', 'progress': 30})
        
        if not document.file_path or not Path(document.file_path).exists():
            raise Exception(f"Document file not found: {document.file_path}")
        
        result = rag_engine.add_document(
            filepath=document.file_path,
            metadata={"filename": document.filename}
        )
        
        # Extract chunks count from result
        chunks_count = result[0] if isinstance(result, tuple) else result.get("chunks", 0)
        
        # Update document record
        self.update_state(state='PROGRESS', meta={'status': 'Updating database', 'progress': 80})
        document.chunks_count = chunks_count
        db.commit()
        
        # Trigger webhook (async, but we're in sync context)
        self.update_state(state='PROGRESS', meta={'status': 'Sending notifications', 'progress': 90})
        try:
            import asyncio
            asyncio.run(WebhookManager.trigger_webhook(
                db=db,
                user_id=user_id,
                event_type="document.processed",
                payload={
                    "document_id": document_id,
                    "filename": document.filename,
                    "chunks": chunks_count
                }
            ))
        except Exception as e:
            logger.warning(f"Webhook trigger failed: {e}")
        
        # Send email notification (if available)
        try:
            if EMAIL_TASKS_AVAILABLE:
                from .tasks import send_document_processed_email_task
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    send_document_processed_email_task.delay(
                        user.email,
                        user.username,
                        document.filename,
                        chunks_count
                    )
                    logger.info(f"Document processed email queued for {user.email}")
        except Exception as e:
            logger.warning(f"Failed to queue document processed email: {e}")
        
        logger.info(f"Document processing completed: {document_id}")
        
        return {
            'status': 'completed',
            'document_id': document_id,
            'chunks': chunks_count,
            'message': f'Document {document.filename} processed successfully'
        }
    
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        
        # Update document status (if we have error tracking)
        if 'document' in locals() and document:
            # Note: processing_status field would need to be added to Document model
            # For now, we just log the error
            pass
        
        raise
    
    finally:
        db.close()


@celery_app.task(name='backend.tasks.batch_process_documents')
def batch_process_documents(document_ids: list, user_id: int):
    """Process multiple documents"""
    logger.info(f"Batch processing {len(document_ids)} documents for user {user_id}")
    
    results = []
    for doc_id in document_ids:
        try:
            result = process_document_task.delay(doc_id, user_id)
            results.append({'document_id': doc_id, 'task_id': result.id})
        except Exception as e:
            logger.error(f"Failed to queue document {doc_id}: {e}")
            results.append({'document_id': doc_id, 'error': str(e)})
    
    return results


@celery_app.task(name='backend.tasks.generate_embeddings_task')
def generate_embeddings_task(text_chunks: list):
    """Generate embeddings for text chunks"""
    from sentence_transformers import SentenceTransformer
    
    logger.info(f"Generating embeddings for {len(text_chunks)} chunks")
    
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(text_chunks)
    
    return embeddings.tolist()


@celery_app.task(name='backend.tasks.cleanup_old_data')
def cleanup_old_data():
    """
    Periodic cleanup task
    - Remove old sessions
    - Clean temporary files
    - Archive old chat history
    """
    logger.info("Starting cleanup task")
    
    db = SessionLocal()
    
    try:
        from .db_models import ChatSession, ChatMessage
        
        # Remove sessions older than 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)
        old_sessions = db.query(ChatSession).filter(ChatSession.created_at < cutoff).all()
        
        deleted_count = 0
        for session in old_sessions:
            # Delete associated messages
            db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
            db.delete(session)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"Cleanup completed: deleted {deleted_count} old sessions")
        
        return {
            'status': 'completed',
            'cleaned_at': datetime.utcnow().isoformat(),
            'sessions_deleted': deleted_count
        }
    
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(name='backend.tasks.send_email_task')
def send_email_task(to_email: str, subject: str, body: str):
    """Send email notification"""
    logger.info(f"Sending email to {to_email}: {subject}")
    
    # Email sending logic here
    # import smtplib
    # ...
    
    time.sleep(2)  # Simulate sending
    
    return {'status': 'sent', 'to': to_email}


@celery_app.task(name='backend.tasks.generate_analytics_report')
def generate_analytics_report(user_id: int, report_type: str):
    """Generate analytics report"""
    logger.info(f"Generating {report_type} report for user {user_id}")
    
    db = SessionLocal()
    
    try:
        # Generate report logic
        # This would typically aggregate analytics data
        # For now, return a placeholder
        
        report_data = {
            'user_id': user_id,
            'report_type': report_type,
            'generated_at': time.time(),
            'data': {
                'total_queries': 0,
                'total_documents': 0,
                'avg_response_time': 0.0
            }
        }
        
        return report_data
    
    finally:
        db.close()


# Periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    
    # Cleanup every day at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        cleanup_old_data.s(),
        name='daily-cleanup'
    )
    
    # Note: Daily analytics would need user list
    # For now, we skip it or make it manual


# Email tasks
try:
    from .email_service import email_service
    
    @celery_app.task(name='backend.tasks.send_welcome_email')
    def send_welcome_email_task(user_email: str, username: str):
        """Send welcome email to new user"""
        import asyncio
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            email_service.send_welcome_email(user_email, username)
        )
    
    @celery_app.task(name='backend.tasks.send_document_processed_email')
    def send_document_processed_email_task(
        user_email: str,
        username: str,
        filename: str,
        chunks_count: int
    ):
        """Send email when document is processed"""
        import asyncio
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            email_service.send_document_processed_email(
                user_email, username, filename, chunks_count
            )
        )
    
    @celery_app.task(name='backend.tasks.send_quota_warning_email')
    def send_quota_warning_email_task(
        user_email: str,
        username: str,
        usage_percent: float,
        limit: int
    ):
        """Send quota warning email"""
        import asyncio
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            email_service.send_quota_warning_email(
                user_email, username, usage_percent, limit
            )
        )
    
    EMAIL_TASKS_AVAILABLE = True
except ImportError:
    EMAIL_TASKS_AVAILABLE = False
    logger.warning("Email service not available")

