"""Background Tasks Management Page."""

import streamlit as st
import requests
from utils.auth import require_auth, get_headers
import time

require_auth()

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Background Tasks", page_icon="⚙️", layout="wide")
st.title("⚙️ Background Tasks")

st.info("""
Long-running operations are processed in background to keep the UI responsive.
Track your async tasks here.
""")

# Flower monitoring link
st.markdown("""
### 🌸 Celery Flower Dashboard
Monitor all background workers and tasks:
[Open Flower →](http://localhost:5555)
""")

st.markdown("---")

# Task status checker
st.subheader("🔍 Check Task Status")

task_id = st.text_input("Task ID", placeholder="Enter task ID from upload response")

if st.button("Check Status") and task_id:
    try:
        response = requests.get(
            f"{API_URL}/api/tasks/{task_id}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            
            status = data["status"]
            
            # Status indicator
            status_emoji = {
                "PENDING": "⏳",
                "PROGRESS": "🔄",
                "SUCCESS": "✅",
                "FAILURE": "❌",
                "RETRY": "🔁"
            }
            
            st.markdown(f"## {status_emoji.get(status, '❓')} Status: **{status}**")
            
            # Progress bar
            if status == "PROGRESS" and "progress" in data:
                progress_info = data["progress"]
                progress_value = progress_info.get("progress", 0) / 100 if isinstance(progress_info.get("progress"), (int, float)) else 0
                st.progress(progress_value)
                st.caption(progress_info.get("status", "Processing..."))
            
            # Result
            if data.get("result"):
                st.json(data["result"])
        
        else:
            st.error("Failed to fetch task status")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("---")

# Async upload
st.subheader("📤 Async Document Upload")

uploaded_files = st.file_uploader(
    "Upload documents (processed in background)",
    accept_multiple_files=True,
    type=["pdf", "docx", "txt", "md"]
)

if st.button("Upload & Process Async") and uploaded_files:
    with st.spinner("Uploading..."):
        task_ids = []
        for file in uploaded_files:
            try:
                files = {"file": (file.name, file.getvalue(), file.type)}
                response = requests.post(
                    f"{API_URL}/api/documents/upload/async",
                    files=files,
                    headers=get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ {file.name} queued")
                    st.code(f"Task ID: {data['task_id']}")
                    task_ids.append(data['task_id'])
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    st.error(f"❌ {file.name} failed: {error_msg}")
            except Exception as e:
                st.error(f"❌ {file.name} error: {str(e)}")
        
        if task_ids:
            st.session_state.active_tasks = task_ids

# Auto-refresh for active tasks
if "active_tasks" not in st.session_state:
    st.session_state.active_tasks = []

if st.session_state.active_tasks:
    st.markdown("---")
    st.subheader("🔄 Active Tasks")
    
    for task_id in st.session_state.active_tasks:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.text(f"Task: {task_id}")
        
        with col2:
            if st.button("Check", key=f"check_{task_id}"):
                st.rerun()
    
    if st.button("Auto-refresh (5s)"):
        time.sleep(5)
        st.rerun()

