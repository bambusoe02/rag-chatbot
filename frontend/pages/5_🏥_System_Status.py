"""System Status Dashboard Page."""

import os
import sys
from pathlib import Path
import requests
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.auth import require_auth, get_headers

require_auth()

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="System Status", page_icon="🏥", layout="wide")
st.title("🏥 System Status")

# Auto-refresh every 30 seconds
if st.button("🔄 Refresh"):
    st.rerun()

# Get health status
try:
    response = requests.get(f"{API_URL}/health/status", timeout=5, headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        
        # Overall status
        status = data["status"]
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }
        
        st.markdown(f"## {status_emoji.get(status, '❓')} Overall Status: **{status.upper()}**")
        st.caption(f"Last checked: {data['timestamp']}")
        st.caption(f"Version: {data['version']}")
        
        st.markdown("---")
        
        # Individual checks
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 Services")
            
            # Ollama
            ollama = data["checks"]["ollama"]
            st.metric(
                "Ollama LLM",
                ollama["status"].upper(),
                delta=f"{ollama.get('models', 'N/A')} models" if ollama.get("models") else None
            )
            st.caption(ollama["message"])
            
            # Database
            db = data["checks"]["database"]
            st.metric(
                "Database",
                db["status"].upper(),
                delta=f"{db.get('size_mb', 0)} MB" if db.get("size_mb") else None
            )
            st.caption(db["message"])
            
            # ChromaDB
            chroma = data["checks"]["chromadb"]
            st.metric(
                "Vector Database",
                chroma["status"].upper(),
                delta=f"{chroma.get('total_documents', 0)} docs" if chroma.get("total_documents") else None
            )
            st.caption(chroma["message"])
        
        with col2:
            st.subheader("💻 Resources")
            
            # Disk
            disk = data["checks"]["disk"]
            st.metric(
                "Disk Space",
                f"{disk.get('percent_used', 0)}% used",
                delta=f"{disk.get('free_gb', 0)} GB free" if disk.get("free_gb") else None
            )
            
            # Progress bar
            disk_pct = disk.get("percent_used", 0)
            color = "normal"
            if disk_pct > 90:
                color = "red"
            elif disk_pct > 80:
                color = "orange"
            
            st.progress(disk_pct / 100)
            
            # Memory
            memory = data["checks"]["memory"]
            st.metric(
                "Memory",
                f"{memory.get('percent_used', 0)}% used",
                delta=f"{memory.get('available_gb', 0)} GB free" if memory.get("available_gb") else None
            )
            
            # Progress bar
            mem_pct = memory.get("percent_used", 0)
            st.progress(mem_pct / 100)
        
        # Recommendations
        st.markdown("---")
        st.subheader("💡 Recommendations")
        
        warnings = []
        
        if disk.get("percent_used", 0) > 80:
            warnings.append("⚠️ Disk space is running low. Consider cleaning old files or expanding storage.")
        
        if memory.get("percent_used", 0) > 80:
            warnings.append("⚠️ Memory usage is high. Consider restarting services or upgrading RAM.")
        
        if ollama["status"] != "healthy":
            warnings.append("❌ Ollama is not responding. Check if the service is running.")
        
        if db["status"] != "healthy":
            warnings.append("❌ Database connection failed. Check database configuration.")
        
        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.success("✅ All systems operating normally!")
    
    else:
        st.error(f"Failed to fetch status: {response.status_code}")

except requests.exceptions.ConnectionError:
    st.error("❌ Cannot connect to backend API")
    st.info("Make sure the backend is running at http://localhost:8000")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")

# Quick actions
st.markdown("---")
st.subheader("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔧 Restart Services", use_container_width=True):
        st.info("This would restart backend services (not implemented yet)")

with col2:
    if st.button("🧹 Clean Cache", use_container_width=True):
        st.info("This would clear system cache (not implemented yet)")

with col3:
    if st.button("📊 View Logs", use_container_width=True):
        st.info("This would show system logs (not implemented yet)")

