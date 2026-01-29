"""Email Notification Settings Page."""

import streamlit as st
import requests
from utils.auth import require_auth, get_headers

require_auth()

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Email Settings", page_icon="📧", layout="wide")
st.title("📧 Email Notification Settings")

st.info("""
Configure which email notifications you want to receive.
""")

# Email preferences
st.subheader("📬 Notification Preferences")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Activity Notifications")
    
    doc_processed = st.checkbox(
        "Document Processed",
        value=True,
        help="Notify when document processing completes"
    )
    
    api_key = st.checkbox(
        "API Key Created",
        value=True,
        help="Notify when new API key is created"
    )
    
    security = st.checkbox(
        "Security Alerts",
        value=True,
        help="Important security notifications"
    )

with col2:
    st.markdown("### Usage Notifications")
    
    quota = st.checkbox(
        "Quota Warnings",
        value=True,
        help="Notify when approaching rate limits"
    )
    
    newsletter = st.checkbox(
        "Newsletter",
        value=False,
        help="Product updates and tips"
    )

# Digest frequency
st.markdown("---")
st.subheader("📅 Digest Frequency")

frequency = st.radio(
    "How often do you want to receive summary emails?",
    ["Daily", "Weekly", "Never"],
    index=0
)

# Save button
if st.button("💾 Save Preferences", type="primary", use_container_width=True):
    # Save preferences via API (would need endpoint)
    st.success("✅ Preferences saved!")
    st.info("💡 Note: Email preferences API endpoint needs to be implemented")

# Test email
st.markdown("---")
st.subheader("✉️ Test Email")

if st.button("Send Test Email", use_container_width=True):
    with st.spinner("Sending test email..."):
        # Send test email (would need endpoint)
        st.success("✅ Test email sent! Check your inbox.")
        st.info("💡 Note: Test email endpoint needs to be implemented")

# Email status
st.markdown("---")
st.subheader("📊 Email Status")

col1, col2, col3 = st.columns(3)

col1.metric("Emails Sent (This Month)", "23")
col2.metric("Emails Opened", "18")
col3.metric("Last Email", "2 hours ago")

st.caption("💡 Email statistics would be tracked when email service is fully integrated")

