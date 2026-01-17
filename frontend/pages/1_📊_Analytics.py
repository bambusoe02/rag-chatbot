"""Analytics Dashboard Page."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

import requests
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import plotly with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not installed. Charts will not be available. Install with: pip install plotly")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Consistent page config with main app
st.set_page_config(
    page_title="Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Consistent CSS styling
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
col_title, col_back = st.columns([4, 1])
with col_title:
    st.title("📊 Analytics Dashboard")
with col_back:
    if st.button("← Back to Chat"):
        st.switch_page("app.py")

st.caption("Real-time statistics and analytics for your RAG Chatbot")

# Check API health
try:
    health_response = requests.get(f"{API_BASE_URL}/health", timeout=2)
    if health_response.status_code != 200:
        st.error("⚠️ **Backend API is not available.** Please start the backend server.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ **Cannot connect to backend API:** {str(e)}")
    st.stop()

# Get analytics stats
try:
    response = requests.get(f"{API_BASE_URL}/api/stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
    else:
        st.error("❌ Could not load analytics data from server.")
        st.stop()
except Exception as e:
    st.error(f"❌ **Error loading analytics:** {str(e)}")
    st.stop()

# Key Metrics Section
st.markdown("### 📈 Key Metrics")
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_queries = stats.get("total_queries", 0)
    st.metric("Total Queries", total_queries, delta=None, help="Total number of queries processed")

with col2:
    avg_response_time = stats.get("average_response_time", 0.0)
    st.metric("Avg Response Time", f"{avg_response_time:.2f}s", help="Average response time in seconds")

with col3:
    total_docs = stats.get("total_documents", 0)
    st.metric("Total Documents", total_docs, help="Number of indexed documents")

with col4:
    success_rate = stats.get("success_rate", 0.0)
    st.metric("Success Rate", f"{success_rate:.1f}%", help="Percentage of positive feedback")

st.divider()

# Charts Section
st.markdown("### 📊 Charts & Visualizations")
st.divider()

if PLOTLY_AVAILABLE:
    # Charts Row 1
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### Queries Over Time")
        queries_by_date = stats.get("queries_by_date", {})
        if queries_by_date:
            dates = sorted(queries_by_date.keys())
            values = [queries_by_date[d] for d in dates]
            
            fig = px.bar(
                x=dates,
                y=values,
                labels={"x": "Date", "y": "Number of Queries"},
                color=values,
                color_continuous_scale="Blues",
            )
            fig.update_layout(
                showlegend=False,
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("📊 No query data available yet. Start chatting to see statistics!")

    with col_chart2:
        st.markdown("#### Most Queried Documents")
        top_documents = stats.get("top_documents", [])
        if top_documents:
            docs = [d[0][:30] + "..." if len(d[0]) > 30 else d[0] for d in top_documents[:10]]
            counts = [d[1] for d in top_documents[:10]]
            
            fig = px.bar(
                x=counts,
                y=docs,
                orientation='h',
                labels={"x": "Query Count", "y": "Document"},
                color=counts,
                color_continuous_scale="Greens",
            )
            fig.update_layout(
                showlegend=False,
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("📊 No document usage data available yet")

    st.divider()

    # Charts Row 2
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.markdown("#### Response Time")
        avg_response = stats.get("average_response_time", 0)
        if avg_response > 0:
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=avg_response,
                title={'text': "Avg Response Time (s)"},
                gauge={
                    'axis': {'range': [None, max(10, avg_response * 2)]},
                    'bar': {'color': "#1f77b4"},
                    'steps': [
                        {'range': [0, avg_response * 0.5], 'color': "#90EE90"},
                        {'range': [avg_response * 0.5, avg_response], 'color': "#FFD700"},
                        {'range': [avg_response, avg_response * 2], 'color': "#FF6347"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': avg_response
                    }
                }
            ))
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("📊 No response time data available yet")

    with col_chart4:
        st.markdown("#### User Feedback")
        positive = stats.get("total_feedback_positive", 0)
        negative = stats.get("total_feedback_negative", 0)
        total_feedback = positive + negative
        
        if total_feedback > 0:
            fig = px.pie(
                values=[positive, negative],
                names=["Positive 👍", "Negative 👎"],
                color_discrete_map={"Positive 👍": "#2ca02c", "Negative 👎": "#d62728"},
            )
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("📊 No feedback data available yet. Rate messages with 👍/👎 to see feedback statistics!")
else:
    # Fallback if plotly not available
    st.warning("📊 Charts require Plotly library. Install with: `pip install plotly`")
    st.info(f"**Total Queries:** {stats.get('total_queries', 0)}")
    st.info(f"**Average Response Time:** {stats.get('average_response_time', 0):.2f}s")

st.divider()

# Recent Queries Section
st.markdown("### 📋 Recent Queries")
st.divider()

try:
    history_response = requests.get(f"{API_BASE_URL}/api/chat/history", params={"limit": 10}, timeout=5)
    if history_response.status_code == 200:
        history_data = history_response.json()
        queries = history_data.get("queries", [])
        
        if queries:
            for query in queries[:10]:
                with st.container():
                    col_q1, col_q2 = st.columns([3, 1])
                    with col_q1:
                        st.markdown(f"**{query.get('question', 'N/A')}**")
                    with col_q2:
                        st.caption(f"⏱️ {query.get('response_time', 0):.2f}s")
                        st.caption(f"📚 {query.get('sources_count', 0)} sources")
                    
                    timestamp = query.get('timestamp', '')
                    if timestamp:
                        st.caption(f"🕐 {timestamp[:19] if len(timestamp) > 19 else timestamp}")
                    
                    st.divider()
        else:
            st.info("📋 No query history available yet. Start chatting to see your query history!")
    else:
        st.info("📋 Could not load query history from server")
except Exception as e:
    st.info(f"📋 Query history not available: {str(e)}")

# Footer
st.divider()
st.caption("Analytics Dashboard - Powered by RAG Chatbot | Real-time statistics and insights")
