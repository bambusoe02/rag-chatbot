"""Health check endpoints for monitoring system status."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import psutil
import requests
from datetime import datetime
import os
from sqlalchemy import text
from .database import engine

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    checks: Dict[str, Any]


class LivenessResponse(BaseModel):
    status: str
    timestamp: str


class ReadinessResponse(BaseModel):
    status: str
    timestamp: str
    ready: bool


def check_ollama() -> Dict[str, Any]:
    """Check Ollama service health"""
    try:
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "message": "Ollama is responding",
                "models": len(response.json().get("models", []))
            }
        return {
            "status": "unhealthy",
            "message": f"Ollama returned status {response.status_code}"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Ollama unreachable: {str(e)}"
        }


def check_database() -> Dict[str, Any]:
    """Check database connection"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Get database size
        db_path = "./data/app.db"
        size_mb = 0
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
        
        return {
            "status": "healthy",
            "message": "Database is accessible",
            "size_mb": round(size_mb, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }


def check_chromadb() -> Dict[str, Any]:
    """Check ChromaDB status"""
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./data/chroma_db")
        collections = client.list_collections()
        
        total_docs = sum([len(c.get()['ids']) for c in collections])
        
        return {
            "status": "healthy",
            "message": "ChromaDB is accessible",
            "collections": len(collections),
            "total_documents": total_docs
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"ChromaDB error: {str(e)}"
        }


def check_disk_space() -> Dict[str, Any]:
    """Check available disk space"""
    try:
        usage = psutil.disk_usage('/')
        percent_used = usage.percent
        
        status = "healthy"
        if percent_used > 90:
            status = "unhealthy"
        elif percent_used > 80:
            status = "degraded"
        
        return {
            "status": status,
            "message": f"Disk usage: {percent_used}%",
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "percent_used": percent_used
        }
    except Exception as e:
        return {
            "status": "unknown",
            "message": f"Cannot check disk space: {str(e)}"
        }


def check_memory() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        status = "healthy"
        if percent_used > 90:
            status = "unhealthy"
        elif percent_used > 80:
            status = "degraded"
        
        return {
            "status": status,
            "message": f"Memory usage: {percent_used}%",
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": percent_used
        }
    except Exception as e:
        return {
            "status": "unknown",
            "message": f"Cannot check memory: {str(e)}"
        }


@router.get("/live", response_model=LivenessResponse)
async def liveness():
    """
    Kubernetes liveness probe
    Returns 200 if service is running (even if degraded)
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready", response_model=ReadinessResponse)
async def readiness():
    """
    Kubernetes readiness probe
    Returns 200 only if all critical services are healthy
    """
    ollama = check_ollama()
    db = check_database()
    
    ready = (
        ollama["status"] == "healthy" and
        db["status"] == "healthy"
    )
    
    return {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "ready": ready
    }


@router.get("/status", response_model=HealthStatus)
async def health_status():
    """
    Detailed health status of all system components
    """
    checks = {
        "ollama": check_ollama(),
        "database": check_database(),
        "chromadb": check_chromadb(),
        "disk": check_disk_space(),
        "memory": check_memory()
    }
    
    # Determine overall status
    unhealthy_count = sum(1 for c in checks.values() if c["status"] == "unhealthy")
    degraded_count = sum(1 for c in checks.values() if c["status"] == "degraded")
    
    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "checks": checks
    }

