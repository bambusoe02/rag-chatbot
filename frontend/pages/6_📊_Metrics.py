"""Metrics Dashboard Page."""

import os
import sys
from pathlib import Path
import requests
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.auth import require_auth, is_authenticated

require_auth()

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Metrics", page_icon="📊", layout="wide")
st.title("📊 System Metrics")

st.info("""
This page shows system metrics collected by Prometheus.
For advanced visualization, visit Grafana at http://localhost:3000
""")

# Prometheus metrics viewer (simplified)
st.subheader("Quick Metrics")

try:
    response = requests.get(f"{API_URL}/metrics", timeout=5)
    
    if response.status_code == 200:
        metrics_text = response.text
        
        # Parse some key metrics
        lines = metrics_text.split('\n')
        
        col1, col2, col3 = st.columns(3)
        
        # Extract specific metrics
        for line in lines:
            if line.startswith('rag_total_documents '):
                total_docs = line.split()[1]
                col1.metric("Total Documents", total_docs)
            
            elif line.startswith('rag_active_users '):
                active_users = line.split()[1]
                col2.metric("Active Users", active_users)
            
            elif line.startswith('rag_total_chunks '):
                total_chunks = line.split()[1]
                col3.metric("Total Chunks", total_chunks)
        
        # Show raw metrics in expander
        with st.expander("📋 View Raw Metrics"):
            st.code(metrics_text, language="text")
        
        # Links to Prometheus and Grafana
        st.markdown("---")
        st.subheader("🔗 External Tools")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Prometheus
            Query and explore metrics
            
            [Open Prometheus →](http://localhost:9090)
            """)
        
        with col2:
            st.markdown("""
            ### Grafana
            Visual dashboards and alerts
            
            [Open Grafana →](http://localhost:3000)
            
            Default login:
            - Username: `admin`
            - Password: `admin`
            """)
    
    else:
        st.error("Failed to fetch metrics")

except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info("Make sure Prometheus metrics are enabled in the backend")

