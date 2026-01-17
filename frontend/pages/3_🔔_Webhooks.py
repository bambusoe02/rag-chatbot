"""Webhooks Management Page."""

import streamlit as st
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.auth import require_auth, get_headers, get_user_info

st.set_page_config(
    page_title="Webhooks",
    page_icon="🔔",
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

st.title("🔔 Webhooks Management")
st.caption("Configure webhooks to receive event notifications from your RAG Chatbot")

user_info = get_user_info()
if user_info:
    st.info(f"👤 Logged in as: **{user_info['username']}** | Role: {user_info['role']}")

st.markdown("---")

# Create webhook
with st.expander("➕ Create New Webhook", expanded=False):
    with st.form("create_webhook_form"):
        webhook_url = st.text_input(
            "Webhook URL",
            placeholder="https://your-app.com/webhook",
            help="The URL where webhook events will be sent"
        )
        
        st.markdown("**Events to Listen For:**")
        events = st.multiselect(
            "Select events",
            [
                "document.uploaded",
                "document.deleted",
                "query.completed",
                "user.feedback"
            ],
            default=["document.uploaded", "query.completed"],
            help="Choose which events should trigger this webhook"
        )
        
        create_button = st.form_submit_button("Create Webhook", type="primary", use_container_width=True)
        
        if create_button:
            if not webhook_url:
                st.error("⚠️ Please enter a webhook URL")
            elif not events:
                st.error("⚠️ Please select at least one event")
            elif not webhook_url.startswith(("http://", "https://")):
                st.error("⚠️ URL must start with http:// or https://")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/api/webhooks",
                        params={"url": webhook_url},
                        json=events,
                        headers=get_headers()
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Webhook created successfully!")
                        st.code(f"Secret: {data['secret']}", language="text")
                        st.warning("⚠️ **Save this secret now - it's used to verify webhook authenticity!**")
                        st.info("💡 Use this secret to verify webhook signatures in your endpoint handler.")
                        
                        # Add download button
                        st.download_button(
                            label="📥 Download Secret",
                            data=data['secret'],
                            file_name=f"webhook_secret_{data['id']}.txt",
                            mime="text/plain"
                        )
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create webhook: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

st.markdown("---")

# List webhooks
st.subheader("📋 Your Webhooks")

try:
    response = requests.get(f"{API_URL}/api/webhooks", headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        webhooks = data.get("webhooks", [])
        
        if not webhooks:
            st.info("📝 No webhooks configured. Create one above to receive event notifications.")
        else:
            for wh in webhooks:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    col1.markdown(f"**{wh['url']}**")
                    col2.write(f"📅 Created: {wh['created_at'][:10] if wh['created_at'] else 'N/A'}")
                    status = "🟢 Active" if wh['is_active'] else "🔴 Inactive"
                    col2.write(status)
                    
                    # Show events
                    with col1:
                        events_str = ", ".join(wh.get('events', []))
                        st.caption(f"Events: {events_str}")
                    
                    if col3.button("Delete", key=f"del_{wh['id']}", type="secondary"):
                        try:
                            delete_response = requests.delete(
                                f"{API_URL}/api/webhooks/{wh['id']}",
                                headers=get_headers()
                            )
                            if delete_response.status_code == 200:
                                st.success("✅ Webhook deleted")
                                st.rerun()
                            else:
                                st.error("Failed to delete webhook")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    st.markdown("---")
    else:
        st.error(f"❌ Failed to load webhooks: {response.text}")
except Exception as e:
    st.error(f"❌ Error loading webhooks: {str(e)}")

st.markdown("---")

# Webhook signature verification example
with st.expander("🔒 Verify Webhook Signatures", expanded=False):
    st.markdown("""
    ### Python Example - Verify Webhook Signature:
    
    All webhooks include an `X-Webhook-Signature` header with an HMAC SHA256 signature.
    Verify it to ensure the webhook is authentic.
    """)
    
    st.code("""
import hmac
import hashlib
import json
from flask import Flask, request

app = Flask(__name__)

# Your webhook secret (from webhook creation)
WEBHOOK_SECRET = "your_webhook_secret_here"

def verify_webhook_signature(payload, signature, secret):
    \"\"\"Verify webhook HMAC signature.\"\"\"
    # Sort keys for consistent JSON encoding
    message = json.dumps(payload, sort_keys=True)
    
    # Calculate expected signature
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(signature, expected)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    # Get signature from header
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_json()
    
    # Verify signature
    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return {'error': 'Invalid signature'}, 401
    
    # Process webhook
    event_type = payload.get('event')
    event_data = payload.get('data')
    
    if event_type == 'document.uploaded':
        print(f"Document uploaded: {event_data.get('filename')}")
    elif event_type == 'query.completed':
        print(f"Query completed: {event_data.get('question')}")
    
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(port=5000)
    """, language="python")
    
    st.markdown("### Webhook Payload Format:")
    st.json({
        "event": "document.uploaded",
        "timestamp": "2024-01-17T12:00:00",
        "data": {
            "filename": "example.pdf",
            "chunks": 10,
            "file_size": 1024000
        }
    })
    
    st.info("💡 Always verify webhook signatures in production to ensure data integrity and security!")

