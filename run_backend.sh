#!/bin/bash
# Run backend server

cd "$(dirname "$0")"

# Activate venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./start.sh first."
    exit 1
fi

source venv/bin/activate

# Create logs directory
mkdir -p logs

echo "🔧 Starting backend server..."
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop"
echo ""

cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

