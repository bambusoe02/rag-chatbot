"""Login and Registration Page."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.auth import login, register, is_authenticated, logout, get_user_info

st.set_page_config(
    page_title="Login",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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

if is_authenticated():
    st.title("🔐 Already Logged In")
    user_info = get_user_info()
    if user_info:
        st.success(f"✅ Logged in as: **{user_info['username']}**")
        st.info(f"Role: {user_info['role']}")
    
    if st.button("Logout", type="primary", use_container_width=True):
        logout()
    
    st.markdown("---")
    st.markdown("Navigate to other pages using the sidebar 👈")
else:
    st.title("🔐 RAG Chatbot - Login")
    st.caption("Enterprise Edition with Multi-User Support")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_button = st.form_submit_button("Login", type="primary", use_container_width=True)
            with col2:
                forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True)
            
            if login_button:
                if username and password:
                    if login(username, password):
                        st.success("✅ Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
            
            if forgot_password:
                st.info("💡 Contact administrator to reset your password")
    
    with tab2:
        st.subheader("Create New Account")
        
        with st.form("register_form"):
            reg_username = st.text_input("Username", placeholder="Choose a username")
            reg_email = st.text_input("Email", placeholder="your.email@example.com")
            reg_full_name = st.text_input("Full Name (optional)", placeholder="Your full name")
            reg_password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 characters)")
            reg_password2 = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            register_button = st.form_submit_button("Register", type="primary", use_container_width=True)
            
            if register_button:
                if reg_password != reg_password2:
                    st.error("❌ Passwords don't match")
                elif len(reg_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif not reg_username or not reg_email:
                    st.warning("⚠️ Please fill in username and email")
                elif register(reg_username, reg_email, reg_password, reg_full_name):
                    st.success("✅ Registration successful! Please login.")
                    st.balloons()
                else:
                    st.error("❌ Registration failed. Username or email may already be in use.")

