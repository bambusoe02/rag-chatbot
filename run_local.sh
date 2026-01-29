#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     🚀 URUCHOMIENIE LOKALNE (BEZ DOCKER)                    ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 nie jest zainstalowany!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓${NC} Python: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC} Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Wirtualne środowisko utworzone"
fi

# Activate virtual environment
echo -e "${BLUE}[INFO]${NC} Aktywowanie wirtualnego środowiska..."
source venv/bin/activate

# Install dependencies
if [ ! -f "venv/.installed" ]; then
    echo -e "${BLUE}[INFO]${NC} Instalowanie zależności (może zająć kilka minut)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.installed
    echo -e "${GREEN}✓${NC} Zależności zainstalowane"
else
    echo -e "${GREEN}✓${NC} Zależności już zainstalowane"
fi

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC} Creating .env from .env.example..."
    cp .env.example .env
    # Generate SECRET_KEY
    SECRET_KEY=$(openssl rand -hex 32)
    echo "SECRET_KEY=$SECRET_KEY" >> .env
    echo -e "${GREEN}✓${NC} .env created"
fi

# Create data directories
mkdir -p data/uploads data/chroma_db data/chat_history data/feedback data/analytics logs
echo -e "${GREEN}✓${NC} Katalogi danych utworzone"

# Check if Ollama is running
echo ""
echo -e "${BLUE}[INFO]${NC} Sprawdzanie Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama działa"
else
    echo -e "${YELLOW}⚠${NC} Ollama nie działa - uruchom: ollama serve"
    echo "   LUB użyj Docker: docker run -d -p 11434:11434 ollama/ollama"
fi

# Start backend
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Uruchamianie Backend (port 8000)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if port 8000 is free
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} Port 8000 zajęty - zatrzymuję proces..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start backend in background
echo -e "${BLUE}[INFO]${NC} Uruchamianie FastAPI backend..."
cd /home/bambusoe/rag-chatbot
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/rag_backend.pid

# Wait for backend
echo -e "${BLUE}[INFO]${NC} Czekam na uruchomienie backend (5 sekund)..."
sleep 5

# Check backend
if curl -s http://localhost:8000/health/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend działa na http://localhost:8000"
    curl -s http://localhost:8000/health/status | python3 -m json.tool 2>/dev/null || echo "Backend: OK"
else
    echo -e "${YELLOW}⚠${NC} Backend może jeszcze się uruchamiać..."
    echo "   Sprawdź logi: tail -f logs/backend.log"
fi

# Start frontend
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Uruchamianie Frontend (port 8501)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if port 8501 is free
if lsof -i :8501 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} Port 8501 zajęty - zatrzymuję streamlit..."
    pkill -f streamlit 2>/dev/null || true
    sleep 2
fi

# Start frontend
echo -e "${BLUE}[INFO]${NC} Uruchamianie Streamlit frontend..."
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/rag_frontend.pid

# Wait for frontend
echo -e "${BLUE}[INFO]${NC} Czekam na uruchomienie frontend (3 sekundy)..."
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ APLIKACJA URUCHOMIONA!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${GREEN}🎉 Gotowe! Aplikacja działa lokalnie${NC}"
echo ""
echo "📱 Dostęp:"
echo "   Frontend:  http://localhost:8501"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   ReDoc:     http://localhost:8000/redoc"
echo ""
echo "📊 Status:"
echo "   Backend PID:  $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "📝 Logi:"
echo "   Backend:   tail -f logs/backend.log"
echo "   Frontend:  tail -f logs/frontend.log"
echo ""
echo "🛑 Zatrzymanie:"
echo "   ./stop_local.sh"
echo "   LUB: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}[INFO]${NC} Otwieram przeglądarkę..."
sleep 2

# Try to open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501 2>/dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:8501 2>/dev/null &
fi

echo -e "${GREEN}✅ Otwórz w przeglądarce: http://localhost:8501${NC}"
echo ""

