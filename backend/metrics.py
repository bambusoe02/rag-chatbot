"""Prometheus metrics for RAG Chatbot."""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
import psutil
import os
from datetime import datetime

# Info metrics
app_info = Info('rag_chatbot_app', 'Application information')
app_info.info({
    'version': os.getenv('APP_VERSION', '1.0.0'),
    'environment': os.getenv('ENVIRONMENT', 'development')
})

# Counter metrics
request_count = Counter(
    'rag_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

document_uploads = Counter(
    'rag_documents_uploaded_total',
    'Total number of documents uploaded',
    ['user_id', 'file_type']
)

queries_total = Counter(
    'rag_queries_total',
    'Total number of chat queries',
    ['user_id', 'search_mode']
)

queries_with_results = Counter(
    'rag_queries_with_results_total',
    'Queries that returned results',
    ['user_id']
)

queries_without_results = Counter(
    'rag_queries_without_results_total',
    'Queries that returned no results',
    ['user_id']
)

api_key_usage = Counter(
    'rag_api_key_requests_total',
    'API key usage',
    ['api_key_id', 'endpoint']
)

webhook_deliveries = Counter(
    'rag_webhook_deliveries_total',
    'Webhook deliveries',
    ['webhook_id', 'event_type', 'status']
)

errors_total = Counter(
    'rag_errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

# Histogram metrics (for timing)
query_duration = Histogram(
    'rag_query_duration_seconds',
    'Time spent processing queries',
    ['search_mode'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

document_processing_duration = Histogram(
    'rag_document_processing_duration_seconds',
    'Time spent processing documents',
    ['file_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

ollama_response_time = Histogram(
    'rag_ollama_response_duration_seconds',
    'Ollama LLM response time',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0]
)

vector_search_duration = Histogram(
    'rag_vector_search_duration_seconds',
    'ChromaDB vector search time',
    ['collection'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Gauge metrics (current state)
active_users = Gauge(
    'rag_active_users',
    'Number of currently active users'
)

total_documents = Gauge(
    'rag_total_documents',
    'Total number of documents in system'
)

total_chunks = Gauge(
    'rag_total_chunks',
    'Total number of document chunks'
)

chromadb_collections = Gauge(
    'rag_chromadb_collections',
    'Number of ChromaDB collections'
)

database_size_mb = Gauge(
    'rag_database_size_megabytes',
    'Database file size in MB'
)

vector_db_size_mb = Gauge(
    'rag_vector_db_size_megabytes',
    'Vector database size in MB'
)

disk_usage_percent = Gauge(
    'rag_disk_usage_percent',
    'Disk usage percentage'
)

memory_usage_percent = Gauge(
    'rag_memory_usage_percent',
    'Memory usage percentage'
)

cpu_usage_percent = Gauge(
    'rag_cpu_usage_percent',
    'CPU usage percentage'
)

# User-specific metrics
user_document_count = Gauge(
    'rag_user_documents',
    'Number of documents per user',
    ['user_id']
)

user_query_count = Gauge(
    'rag_user_queries',
    'Number of queries per user',
    ['user_id']
)


def update_system_metrics():
    """Update system resource metrics"""
    try:
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent.set(disk.percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage_percent.set(memory.percent)
        
        # CPU usage
        cpu = psutil.cpu_percent(interval=1)
        cpu_usage_percent.set(cpu)
        
        # Database size
        db_path = "./data/app.db"
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            database_size_mb.set(size_mb)
        
        # Vector DB size
        vdb_path = "./data/chroma_db"
        if os.path.exists(vdb_path):
            total_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(vdb_path)
                for filename in filenames
            )
            vector_db_size_mb.set(total_size / (1024 * 1024))
    
    except Exception as e:
        print(f"Error updating system metrics: {e}")


def update_database_metrics(db):
    """Update database-related metrics"""
    try:
        from .db_models import User, Document, ChatMessage
        
        # Total documents
        doc_count = db.query(Document).count()
        total_documents.set(doc_count)
        
        # Active users (users with activity in last 24h)
        # This is a simplified version - you might want to track sessions
        active_count = db.query(User).filter(User.is_active == True).count()
        active_users.set(active_count)
        
    except Exception as e:
        print(f"Error updating database metrics: {e}")


def setup_metrics(app: FastAPI):
    """Setup Prometheus metrics for FastAPI app"""
    
    # Instrumentator for automatic HTTP metrics
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="rag_http_requests_inprogress",
        inprogress_labels=True,
    )
    
    instrumentator.instrument(app)
    
    # Expose metrics endpoint
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
    
    print("✅ Prometheus metrics initialized at /metrics")

