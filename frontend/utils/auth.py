"""Authentication utilities for Streamlit frontend."""

import os
import streamlit as st
import requests
from typing import Optional, Dict, Any

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return "access_token" in st.session_state and st.session_state.access_token is not None


def get_headers() -> dict:
    """Get headers with authentication token."""
    if not is_authenticated():
        return {}
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


def login(username: str, password: str) -> bool:
    """Login user and store token."""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            
            # Get user info
            user_response = requests.get(
                f"{API_URL}/api/auth/me",
                headers=get_headers()
            )
            if user_response.status_code == 200:
                user_data = user_response.json()
                st.session_state.user = user_data
                st.session_state.username = user_data["username"]
                st.session_state.user_role = user_data["role"]
                st.session_state.user_id = user_data["id"]
            
            return True
    except Exception as e:
        st.error(f"Login failed: {e}")
    return False


def register(username: str, email: str, password: str, full_name: str = "") -> bool:
    """Register a new user."""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Registration failed: {e}")
    return False


def logout():
    """Logout user and clear session."""
    st.session_state.clear()
    st.rerun()


def require_auth():
    """Decorator to require authentication. Shows warning if not authenticated."""
    if not is_authenticated():
        st.warning("⚠️ Please login to access this page")
        st.info("👉 Go to Login page from the sidebar")
        st.stop()


def get_user_info() -> Optional[Dict[str, Any]]:
    """Get current user information."""
    if is_authenticated():
        return st.session_state.get("user")
    return None

