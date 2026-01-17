#!/bin/bash

# RAG Chatbot Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting RAG Chatbot..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install it first."
    exit 1
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama is not running. Please start it first:"
    echo "   ollama serve"
    echo ""
    echo "Continuing anyway..."
fi

# Check Qwen model
if ! ollama list 2>/dev/null | grep -q "qwen2.5:14b-instruct"; then
    echo "⚠️  Qwen model not found. It may be pulled automatically."
fi

# Activate venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt || echo "⚠️  Some dependencies may have issues with Python 3.14"

# Create data directories
mkdir -p data/uploads data/chroma_db logs
touch data/uploads/.gitkeep
touch data/chroma_db/.gitkeep

# Kill existing processes
echo "🛑 Stopping existing processes..."
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
sleep 1

# Start backend
echo "🔧 Starting backend on port 8000..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend did not start within 30 seconds"
        echo "Check logs: tail -f logs/backend.log"
    fi
    sleep 1
done

# Start frontend
echo "🎨 Starting frontend on port 8501..."
streamlit run frontend/app.py --server.headless=true --server.port=8501 > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend
sleep 3

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   RAG Chatbot is running!              ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📊 Frontend: http://localhost:8501"
echo "🔧 Backend:  http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap to kill both processes on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    pkill -f "uvicorn.*main:app" 2>/dev/null || true
    pkill -f "streamlit run" 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM

# Keep script running
wait
