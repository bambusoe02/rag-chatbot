#!/bin/bash
# Run frontend server

cd "$(dirname "$0")"

# Activate venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./start.sh first."
    exit 1
fi

source venv/bin/activate

echo "🎨 Starting frontend server..."
echo "   Frontend: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

streamlit run frontend/app.py

