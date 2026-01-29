"""Rate Limits Dashboard Page."""

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

st.set_page_config(page_title="Rate Limits", page_icon="⏱️", layout="wide")
st.title("⏱️ Rate Limit Status")

st.info("""
Rate limits protect the system from abuse and ensure fair usage for all users.
Your limits depend on your account role.
""")

# Get rate limit status
try:
    response = requests.get(
        f"{API_URL}/api/rate-limit/status",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Display current status
        st.subheader("📊 Your Current Usage")
        
        col1, col2, col3 = st.columns(3)
        
        col1.metric(
            "Role",
            data["role"].upper(),
            help="Your account role determines your rate limits"
        )
        
        col2.metric(
            "Rate Limit",
            data["limit"],
            help="Maximum requests allowed per time window"
        )
        
        usage_pct = (data["current_usage"] / data["limit_value"]) * 100 if data["limit_value"] > 0 else 0
        col3.metric(
            "Usage",
            f"{usage_pct:.1f}%",
            delta=f"{data['remaining']} remaining"
        )
        
        # Progress bar
        st.progress(min(usage_pct / 100, 1.0))
        
        st.caption(f"Used {data['current_usage']} of {data['limit_value']} requests")
        st.caption(f"Window resets in {data['reset_in_seconds']} seconds")
        
        st.markdown("---")
        
        # Rate limit tiers
        st.subheader("💎 Rate Limit Tiers")
        
        tiers = {
            "User": {
                "limit": "100 requests/hour",
                "description": "Standard rate limit for regular users",
                "icon": "👤"
            },
            "Admin": {
                "limit": "1,000 requests/hour",
                "description": "Elevated limit for administrators",
                "icon": "👑"
            },
            "Enterprise": {
                "limit": "10,000 requests/hour",
                "description": "High-volume limit for enterprise accounts",
                "icon": "🏢"
            }
        }
        
        for tier_name, tier_info in tiers.items():
            is_current = tier_name.lower() == data["role"].lower()
            
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                col1.markdown(f"## {tier_info['icon']}")
                
                with col2:
                    if is_current:
                        st.markdown(f"### {tier_name} ⭐ (Your Tier)")
                    else:
                        st.markdown(f"### {tier_name}")
                    
                    st.markdown(f"**{tier_info['limit']}**")
                    st.caption(tier_info['description'])
                
                st.markdown("---")
        
        # Endpoint-specific limits
        st.subheader("🎯 Endpoint-Specific Limits")
        
        endpoints = {
            "/api/auth/login": "10 requests/minute",
            "/api/auth/register": "5 requests/hour",
            "/api/documents/upload": "50 requests/hour",
            "/api/chat": "200 requests/hour",
        }
        
        for endpoint, limit in endpoints.items():
            st.markdown(f"**{endpoint}**: `{limit}`")
        
        # Tips
        st.markdown("---")
        st.subheader("💡 Tips to Avoid Rate Limits")
        
        st.markdown("""
        - **Batch operations**: Upload multiple documents in one session
        - **Cache results**: Save frequently accessed data locally
        - **Use webhooks**: Instead of polling, use webhooks for notifications
        - **Upgrade tier**: Contact admin to upgrade to higher tier
        - **Use API keys**: API keys have separate rate limits
        """)
        
        # What happens when limit exceeded
        with st.expander("❓ What happens if I exceed the limit?"):
            st.markdown("""
            When you exceed your rate limit:
            
            1. **HTTP 429** response is returned
            2. **Retry-After** header indicates when you can try again
            3. **X-RateLimit-Reset** shows when the window resets
            4. Your request is **not processed**
            
            The system uses a **sliding window** algorithm, so limits reset gradually over time.
            """)
        
        # Refresh button
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
    
    else:
        st.error(f"Failed to fetch rate limit status: {response.status_code}")

except Exception as e:
    st.error(f"Error: {str(e)}")

