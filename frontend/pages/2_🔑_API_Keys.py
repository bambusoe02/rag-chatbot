"""API Keys Management Page."""

import streamlit as st
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.auth import require_auth, get_headers, get_user_info

st.set_page_config(
    page_title="API Keys",
    page_icon="🔑",
    layout="wide",
)

# Require authentication
require_auth()

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
import os

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔑 API Keys Management")
st.caption("Manage API keys for external access to your RAG Chatbot")

user_info = get_user_info()
if user_info:
    st.info(f"👤 Logged in as: **{user_info['username']}** | Role: {user_info['role']}")

st.markdown("---")

# Create new API key
with st.expander("➕ Create New API Key", expanded=False):
    with st.form("create_api_key_form"):
        key_name = st.text_input("Key Name", placeholder="e.g., My App Integration", help="A descriptive name for this API key")
        
        st.markdown("**Permissions:**")
        col1, col2, col3 = st.columns(3)
        perm_read = col1.checkbox("Read", value=True, help="Allow read access")
        perm_write = col2.checkbox("Write", value=False, help="Allow write access")
        perm_delete = col3.checkbox("Delete", value=False, help="Allow delete access")
        
        rate_limit = st.number_input(
            "Rate Limit (requests/hour)",
            min_value=1,
            max_value=10000,
            value=100,
            step=10,
            help="Maximum number of requests allowed per hour"
        )
        
        create_button = st.form_submit_button("Generate API Key", type="primary", use_container_width=True)
        
        if create_button:
            if not key_name:
                st.error("⚠️ Please enter a key name")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/api/api-keys",
                        params={
                            "key_name": key_name,
                            "rate_limit": rate_limit
                        },
                        json={
                            "read": perm_read,
                            "write": perm_write,
                            "delete": perm_delete
                        },
                        headers=get_headers()
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ API Key created successfully!")
                        st.code(data["api_key"], language="text")
                        st.warning("⚠️ **Save this key now - it won't be shown again!**")
                        st.info("💡 Copy the key and store it securely. You'll need it to authenticate API requests.")
                        
                        # Add download button
                        st.download_button(
                            label="📥 Download Key",
                            data=data["api_key"],
                            file_name=f"{key_name}_api_key.txt",
                            mime="text/plain"
                        )
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create API key: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

st.markdown("---")

# List existing API keys
st.subheader("📋 Your API Keys")

try:
    response = requests.get(f"{API_URL}/api/api-keys", headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        keys = data.get("keys", [])
        
        if not keys:
            st.info("📝 No API keys yet. Create one above to get started.")
        else:
            for key in keys:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                    
                    col1.markdown(f"**{key['key_name']}**")
                    col2.write(f"📅 Created: {key['created_at'][:10] if key['created_at'] else 'N/A'}")
                    col3.write(f"⏱️ Last Used: {key['last_used'][:10] if key['last_used'] else 'Never'}")
                    col4.write(f"🚦 Rate: {key['rate_limit']}/hr")
                    
                    status = "🟢 Active" if key['is_active'] else "🔴 Revoked"
                    col4.write(status)
                    
                    if col5.button("Revoke", key=f"revoke_{key['id']}", type="secondary"):
                        try:
                            revoke_response = requests.delete(
                                f"{API_URL}/api/api-keys/{key['id']}",
                                headers=get_headers()
                            )
                            if revoke_response.status_code == 200:
                                st.success("✅ API key revoked")
                                st.rerun()
                            else:
                                st.error("Failed to revoke API key")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    st.markdown("---")
    else:
        st.error(f"❌ Failed to load API keys: {response.text}")
except Exception as e:
    st.error(f"❌ Error loading API keys: {str(e)}")

st.markdown("---")

# Usage example
with st.expander("📖 Usage Example", expanded=False):
    st.markdown("### Python Example:")
    st.code("""
import requests

# Set your API key
headers = {
    "X-API-Key": "sk_your_api_key_here",
    "Content-Type": "application/json"
}

# Make a request
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    headers=headers,
    json={
        "question": "What is RAG?",
        "search_mode": "hybrid"  # or "semantic", "keyword"
    }
)

print(response.json())
    """, language="python")
    
    st.markdown("### cURL Example:")
    st.code("""
curl -X POST http://localhost:8000/api/v1/chat \\
  -H "X-API-Key: sk_your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "What is RAG?", "search_mode": "hybrid"}'
    """, language="bash")
    
    st.markdown("### JavaScript/Node.js Example:")
    st.code("""
const fetch = require('node-fetch');

const response = await fetch('http://localhost:8000/api/v1/chat', {
  method: 'POST',
  headers: {
    'X-API-Key': 'sk_your_api_key_here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: 'What is RAG?',
    search_mode: 'hybrid'
  })
});

const data = await response.json();
console.log(data);
    """, language="javascript")

