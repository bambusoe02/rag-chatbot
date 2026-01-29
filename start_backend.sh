#!/bin/bash

cd /home/bambusoe/rag-chatbot

# Activate venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Stop existing
echo "🛑 Stopping existing backend..."
pkill -f "uvicorn.*backend.main:app" 2>/dev/null || true
pkill -f "uvicorn.*main:app" 2>/dev/null || true
sleep 1

# Initialize DB if needed
if [ ! -f "data/app.db" ]; then
    echo "📊 Initializing database..."
    python init_db.py
fi

# Create logs directory
mkdir -p logs

# Start backend
echo "🚀 Starting backend..."
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload





