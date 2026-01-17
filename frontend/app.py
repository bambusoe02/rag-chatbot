"""Enhanced Streamlit frontend for RAG Chatbot with advanced features."""

import os
import sys
import time
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import utilities
try:
    from frontend.utils.file_handler import chat_history, user_preferences
    from frontend.utils.api_client import api_client
except ImportError:
    # Fallback if utils not available
    api_client = None
    chat_history = None
    user_preferences = None

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
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
    .source-card {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def save_chat_history():
    """Save current chat history to file."""
    if chat_history and "session_id" in st.session_state and st.session_state.messages:
        try:
            chat_history.save_chat(
                st.session_state.session_id,
                st.session_state.messages
            )
        except Exception as e:
            st.error(f"Error saving chat history: {e}")


def load_chat_history(session_id: str):
    """Load chat history from file."""
    if chat_history:
        try:
            messages = chat_history.load_chat(session_id)
            if messages:
                st.session_state.messages = messages
        except Exception as e:
            st.warning(f"Could not load chat history: {e}")


def export_chat_to_text() -> str:
    """Export chat to plain text."""
    lines = []
    for msg in st.session_state.messages:
        role = msg["role"].upper()
        content = msg["content"]
        timestamp = msg.get("timestamp", "")
        lines.append(f"[{timestamp}] {role}: {content}")
        if "sources" in msg and msg["sources"]:
            lines.append("Sources:")
            for source in msg["sources"]:
                lines.append(f"  - {source.get('filename', 'unknown')}")
    return "\n".join(lines)


def export_chat_to_json() -> str:
    """Export chat to JSON."""
    export_data = {
        "session_id": st.session_state.get("session_id", "unknown"),
        "exported_at": datetime.now().isoformat(),
        "messages": st.session_state.messages,
    }
    return json.dumps(export_data, indent=2)


def export_chat_to_pdf_content() -> bytes:
    """Export chat to PDF content (simple text-based PDF).
    
    Returns:
        PDF content as bytes
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.units import inch
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
        )
        
        elements.append(Paragraph("RAG Chatbot - Chat Export", title_style))
        elements.append(Paragraph(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(f"Session ID: {st.session_state.get('session_id', 'unknown')}", styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Add messages
        for msg in st.session_state.messages:
            role = msg["role"].upper()
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            # Role header
            role_style = ParagraphStyle(
                'Role',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#ff7f0e' if role == 'USER' else '#2ca02c'),
                spaceAfter=6,
            )
            elements.append(Paragraph(f"{role} {timestamp if timestamp else ''}", role_style))
            
            # Content
            # Escape HTML in content
            content_escaped = content.replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(content_escaped, styles['Normal']))
            
            # Sources if available
            if "sources" in msg and msg["sources"]:
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph("Sources:", styles['Heading3']))
                for source in msg["sources"]:
                    filename = source.get('filename', 'unknown')
                    page = source.get('page', '')
                    page_info = f" (page {page})" if page else ""
                    elements.append(Paragraph(f"• {filename}{page_info}", styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback: create simple PDF using markdown text
        # For production, install: pip install reportlab
        raise ImportError("PDF export requires 'reportlab' library. Install with: pip install reportlab")


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "temperature" not in st.session_state:
    if user_preferences:
        prefs = user_preferences.load_preferences()
        st.session_state.temperature = prefs.get("temperature", 0.1)
        st.session_state.top_k = prefs.get("top_k", 5)
        st.session_state.model = prefs.get("model", "qwen2.5:14b-instruct")
    else:
        st.session_state.temperature = 0.1
        st.session_state.top_k = 5
        st.session_state.model = "qwen2.5:14b-instruct"

# Check API health
api_healthy = check_api_health()

# Main title
st.title("🤖 RAG Chatbot")
st.caption("Retrieval-Augmented Generation Chatbot with local Qwen LLM")

if not api_healthy:
    st.error("""
    ⚠️ **Backend API is not available**
    
    Please start the backend server:
    
    ```bash
    ./run_backend.sh
    ```
    
    Or use: `./start.sh`
    """)
    st.stop()

# Sidebar
with st.sidebar:
    
    # Settings Panel
    with st.expander("⚙️ Settings", expanded=False):
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1,
            help="Controls randomness (0=deterministic, 1=creative)",
        )
        st.session_state.top_k = st.slider(
            "Top K Results",
            min_value=1,
            max_value=10,
            value=st.session_state.top_k,
            step=1,
            help="Number of documents to retrieve",
        )
        model_options = ["qwen2.5:7b-instruct", "qwen2.5:14b-instruct", "qwen2.5:32b-instruct"]
        st.session_state.model = st.selectbox(
            "Model",
            model_options,
            index=1 if st.session_state.model in model_options else 0,
            help="Select Ollama model",
        )
        
        if st.button("💾 Save Settings"):
            if user_preferences:
                prefs = {
                    "temperature": st.session_state.temperature,
                    "top_k": st.session_state.top_k,
                    "model": st.session_state.model,
                }
                user_preferences.save_preferences(prefs)
                st.success("Settings saved!")
    
    st.divider()
    
    # Document Management
    st.header("📚 Documents")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "docx", "txt", "md"],
        help="Upload PDF, DOCX, TXT, or MD files (max 50MB)",
    )
    
    if uploaded_file is not None:
        # Check file size (50MB limit)
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > 50:
            st.error(f"File too large: {file_size_mb:.1f}MB. Maximum size is 50MB.")
        elif st.button("📤 Upload", type="primary"):
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(
                        f"{API_BASE_URL}/api/documents/upload",
                        files=files,
                        timeout=120,
                    )
                    response.raise_for_status()
                    result = response.json()
                    st.success(f"✅ {result.get('filename')} uploaded! ({result.get('chunks', 0)} chunks)")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Upload failed: {str(e)}")
    
    st.divider()
    
    # Document list with preview
    st.subheader("📋 Indexed Documents")
    try:
        response = requests.get(f"{API_BASE_URL}/api/documents", timeout=5)
        documents = response.json().get("documents", []) if response.status_code == 200 else []
    except:
        documents = []
    
    if documents:
        for doc in documents:
            with st.container():
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"**📄 {doc['filename']}**")
                    st.caption(f"Chunks: {doc.get('chunks', 0)}")
                    if doc.get('file_size'):
                        st.caption(f"Size: {format_file_size(doc['file_size'])}")
                with col2:
                    if st.button("👁️", key=f"preview_{doc['filename']}", help="Preview"):
                        try:
                            preview_response = requests.get(
                                f"{API_BASE_URL}/api/documents/{doc['filename']}/preview",
                                params={"max_chars": 500},
                                timeout=5,
                            )
                            if preview_response.status_code == 200:
                                preview_data = preview_response.json()
                                st.info(f"**Preview:**\n\n{preview_data.get('preview', '')}")
                        except:
                            st.error("Could not load preview")
                    
                    if st.button("🗑️", key=f"delete_{doc['filename']}", help="Delete"):
                        try:
                            delete_response = requests.delete(
                                f"{API_BASE_URL}/api/documents/{doc['filename']}",
                                timeout=5,
                            )
                            if delete_response.status_code == 200:
                                st.success(f"Deleted {doc['filename']}")
                                time.sleep(1)
                                st.rerun()
                        except:
                            st.error("Delete failed")
    else:
        st.info("No documents indexed yet. Upload a document to get started.")
    
    st.divider()
    
    # Statistics
    try:
        stats_response = requests.get(f"{API_BASE_URL}/api/stats", timeout=5)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            st.metric("📊 Documents", stats.get("document_count", 0))
            st.metric("📝 Total Chunks", stats.get("chunk_count", 0))
    except:
        pass
    
    st.divider()
    
    # Chat history management
    st.subheader("💬 Chat History")
    if st.button("📥 Load Previous Chat"):
        if chat_history:
            sessions = chat_history.list_sessions()
            if sessions:
                session_ids = [s["session_id"] for s in sessions]
                selected_session = st.selectbox("Select session", session_ids)
                if st.button("Load"):
                    load_chat_history(selected_session)
                    st.rerun()
            else:
                st.info("No saved chats found")
    
    if st.session_state.messages and st.button("💾 Save Current Chat"):
        save_chat_history()
        st.success("Chat saved!")
    
    st.divider()
    
    # Query suggestions
    try:
        suggestions_response = requests.get(f"{API_BASE_URL}/api/chat/suggestions", timeout=5)
        if suggestions_response.status_code == 200:
            suggestions_data = suggestions_response.json()
            suggestions = suggestions_data.get("suggestions", [])
            if suggestions:
                st.subheader("💡 Suggested Questions")
                for suggestion in suggestions[:5]:
                    if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                        # This will be handled by chat input below
                        st.session_state.suggestion_clicked = suggestion
                        st.rerun()
    except:
        pass
    
    st.divider()
    
    # Clear all button
    if st.button("🗑️ Clear All Documents", type="secondary"):
        if st.checkbox("⚠️ Confirm deletion", key="confirm_clear"):
            try:
                clear_response = requests.delete(f"{API_BASE_URL}/api/clear", timeout=10)
                if clear_response.status_code == 200:
                    st.success("All documents cleared!")
                    st.session_state.messages = []
                    time.sleep(1)
                    st.rerun()
            except:
                st.error("Clear failed")

# Main chat interface
st.subheader("💬 Chat")

# Handle suggestion click
if "suggestion_clicked" in st.session_state:
    prompt = st.session_state.suggestion_clicked
    del st.session_state.suggestion_clicked
else:
    prompt = None

# Display chat history
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Timestamp
        timestamp = message.get("timestamp", "")
        if timestamp:
            st.caption(f"🕐 {timestamp}")
        
        # Enhanced source citations for assistant messages
        if message["role"] == "assistant" and "sources" in message:
            sources = message["sources"]
            if sources:
                with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
                    for i, source in enumerate(sources, 1):
                        with st.container():
                            filename = source.get('filename', 'unknown')
                            page = source.get('page')
                            score = source.get('score', 0)
                            content = source.get('content', '')
                            
                            st.markdown(f"**Source {i}:** {filename}")
                            if page:
                                st.caption(f"📍 Page {page}")
                            st.caption(f"📊 Confidence: {score*100:.1f}%")
                            
                            # Show relevant snippet
                            snippet = content[:300] + "..." if len(content) > 300 else content
                            st.markdown(f"*{snippet}*")
                        
                        if i < len(sources):
                            st.divider()
        
        # Feedback buttons for assistant messages
        if message["role"] == "assistant":
            col_fb1, col_fb2 = st.columns(2)
            with col_fb1:
                if st.button("👍", key=f"thumb_up_{idx}", help="Helpful"):
                    try:
                        requests.post(
                            f"{API_BASE_URL}/api/chat/feedback",
                            json={
                                "question": st.session_state.messages[idx-1]["content"] if idx > 0 else "",
                                "answer": message["content"],
                                "is_positive": True,
                            },
                            timeout=5,
                        )
                        st.success("Thanks for your feedback!")
                    except:
                        pass
            with col_fb2:
                if st.button("👎", key=f"thumb_down_{idx}", help="Not helpful"):
                    try:
                        requests.post(
                            f"{API_BASE_URL}/api/chat/feedback",
                            json={
                                "question": st.session_state.messages[idx-1]["content"] if idx > 0 else "",
                                "answer": message["content"],
                                "is_positive": False,
                            },
                            timeout=5,
                        )
                        st.success("Thanks for your feedback!")
                    except:
                        pass

# Chat input
user_input = prompt or st.chat_input("Ask a question about your documents...")

if user_input:
    # Add user message with timestamp
    user_msg = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        st.markdown(user_input)
        st.caption(f"🕐 {user_msg['timestamp']}")
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/chat",
                    json={
                        "question": user_input,
                        "temperature": st.session_state.temperature,
                        "top_k": st.session_state.top_k,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()
                
                answer = data.get("answer", "No answer generated.")
                sources = data.get("sources", [])
                query_time = data.get("query_time", 0)
                
                st.markdown(answer)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.caption(f"⏱️ Response time: {query_time:.2f}s | 🕐 {timestamp}")
                
                # Enhanced source citations
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)})", expanded=True):
                        for i, source in enumerate(sources, 1):
                            with st.container():
                                filename = source.get('filename', 'unknown')
                                page = source.get('page')
                                score = source.get('score', 0)
                                content = source.get('content', '')
                                
                                st.markdown(f"**Source {i}:** `{filename}`")
                                if page:
                                    st.caption(f"📍 Page {page}")
                                st.caption(f"📊 Confidence: {score*100:.1f}%")
                                
                                # Show relevant snippet with better formatting
                                snippet = content[:400] + "..." if len(content) > 400 else content
                                st.markdown(f"```\n{snippet}\n```")
                            
                            if i < len(sources):
                                st.divider()
                
                # Add assistant message to history
                assistant_msg = {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "timestamp": timestamp,
                    "query_time": query_time,
                }
                st.session_state.messages.append(assistant_msg)
                
                # Auto-save chat history
                save_chat_history()
                
            except requests.exceptions.RequestException as e:
                st.error(f"❌ **Connection Error:** Could not connect to backend API. Please check if the server is running.")
            except Exception as e:
                st.error(f"❌ **Error:** {str(e)}")
                st.session_state.messages.pop()  # Remove user message if error

# Footer with actions
if st.session_state.messages:
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        # Export to TXT
        chat_text = export_chat_to_text()
        st.download_button(
            "💾 Export TXT",
            data=chat_text,
            file_name=f"chat_export_{int(time.time())}.txt",
            mime="text/plain",
        )
    
    with col3:
        # Export to JSON
        chat_json = export_chat_to_json()
        st.download_button(
            "📄 Export JSON",
            data=chat_json,
            file_name=f"chat_export_{int(time.time())}.json",
            mime="application/json",
        )
    
    with col4:
        # Export to PDF
        try:
            pdf_content = export_chat_to_pdf_content()
            st.download_button(
                "📑 Export PDF",
                data=pdf_content,
                file_name=f"chat_export_{int(time.time())}.pdf",
                mime="application/pdf",
            )
        except ImportError:
            st.download_button(
                "📑 Export PDF (Install reportlab)",
                data=export_chat_to_text().encode(),
                file_name=f"chat_export_{int(time.time())}.txt",
                mime="text/plain",
                help="Install 'reportlab' for PDF export: pip install reportlab",
                disabled=True,
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

# Footer
st.divider()
st.caption("RAG Chatbot - Powered by Ollama (Qwen2.5) | ChromaDB | LangChain")
