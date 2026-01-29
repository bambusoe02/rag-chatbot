"""Cache Management Dashboard Page."""

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

st.set_page_config(page_title="Cache", page_icon="💾", layout="wide")
st.title("💾 Cache Management")

st.info("""
Redis cache stores frequently accessed data to improve response times.
Cached items include queries, user sessions, and computed results.
""")

# Get cache stats
try:
    response = requests.get(f"{API_URL}/api/cache/stats", headers=get_headers())
    
    if response.status_code == 200:
        stats = response.json()
        
        if not stats.get("enabled"):
            st.warning("⚠️ Redis cache is not enabled")
            st.info("Enable Redis by starting the Redis service in docker-compose")
        else:
            # Display stats
            st.subheader("📊 Cache Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(
                "Hit Rate",
                f"{stats.get('hit_rate', 0)}%",
                help="Percentage of requests served from cache"
            )
            
            col2.metric(
                "Total Keys",
                stats.get('total_keys', 0),
                help="Number of cached items"
            )
            
            col3.metric(
                "Memory Used",
                stats.get('used_memory_human', '0'),
                help="Redis memory usage"
            )
            
            col4.metric(
                "Connected Clients",
                stats.get('connected_clients', 0),
                help="Active Redis connections"
            )
            
            # Hit/Miss stats
            st.markdown("---")
            st.subheader("🎯 Hit/Miss Statistics")
            
            hits = stats.get('keyspace_hits', 0)
            misses = stats.get('keyspace_misses', 0)
            total = hits + misses
            
            if total > 0:
                col1, col2 = st.columns(2)
                
                col1.metric("Cache Hits", f"{hits:,}")
                col2.metric("Cache Misses", f"{misses:,}")
                
                # Progress bar
                if total > 0:
                    hit_ratio = hits / total
                    st.progress(hit_ratio)
                    st.caption(f"Hit ratio: {hit_ratio:.2%}")
            else:
                st.info("No cache statistics yet. Use the application to populate cache.")
            
            # Cache management
            st.markdown("---")
            st.subheader("🛠️ Cache Management")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Clear My Cache", use_container_width=True):
                    response = requests.post(
                        f"{API_URL}/api/cache/clear",
                        headers=get_headers()
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data['message']}")
                        st.rerun()
                    else:
                        st.error("Failed to clear cache")
                
                st.caption("Clears your cached queries and results")
            
            with col2:
                # Admin only
                user_role = st.session_state.get("user_role", "user")
                if user_role == "admin":
                    if st.button("💣 Flush All Cache", type="secondary", use_container_width=True):
                        st.warning("⚠️ This will clear ALL cached data for ALL users!")
                        if st.button("Confirm Flush", type="primary"):
                            response = requests.post(
                                f"{API_URL}/api/cache/flush",
                                headers=get_headers()
                            )
                            if response.status_code == 200:
                                st.success("✅ Cache flushed")
                                st.rerun()
                            else:
                                st.error("Failed to flush cache")
                    st.caption("⚠️ Admin only - clears entire cache")
            
            # Cache configuration
            st.markdown("---")
            st.subheader("⚙️ Cache Configuration")
            
            st.markdown("""
            **What gets cached:**
            - 🔍 Query results (1 hour TTL)
            - 👤 User sessions (5 minutes TTL)
            - 📊 Analytics data (10 minutes TTL)
            - 🔑 API key validations (1 minute TTL)
            
            **Cache invalidation:**
            - Automatic when documents are added/removed
            - Manual via "Clear My Cache" button
            - TTL expiration
            """)
            
            # Performance tips
            with st.expander("💡 Performance Tips"):
                st.markdown("""
                **To maximize cache effectiveness:**
                
                1. **Ask similar questions** - Exact matches are cached
                2. **Use consistent phrasing** - "What is X?" vs "Tell me about X" are different keys
                3. **Wait for cache** - First query is slow, repeats are fast
                4. **Clear cache after uploads** - Done automatically, but good to know
                
                **Cache hit rate interpretation:**
                - **>50%** - Excellent, queries are being reused
                - **30-50%** - Good, moderate query reuse
                - **<30%** - Low, mostly unique queries
                """)

except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info("Make sure Redis is running: `docker-compose up -d redis`")

# Refresh button
if st.button("🔄 Refresh Stats", use_container_width=True):
    st.rerun()

