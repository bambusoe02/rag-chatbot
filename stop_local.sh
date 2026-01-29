#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "🛑 Zatrzymywanie RAG Chatbot..."
echo ""

# Stop backend
if pgrep -f "uvicorn.*backend.main:app" > /dev/null || pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo -e "${BLUE}[INFO]${NC} Zatrzymuję backend..."
    pkill -f "uvicorn.*backend.main:app" 2>/dev/null || true
    pkill -f "uvicorn.*main:app" 2>/dev/null || true
    sleep 2
    echo -e "${GREEN}[✓]${NC} Backend zatrzymany"
else
    echo -e "${YELLOW}[⚠]${NC} Backend nie działa"
fi

# Stop containers
if docker-compose ps | grep -q "Up"; then
    echo -e "${BLUE}[INFO]${NC} Zatrzymuję kontenery..."
    docker-compose down
    echo -e "${GREEN}[✓]${NC} Kontenery zatrzymane"
else
    echo -e "${YELLOW}[⚠]${NC} Brak uruchomionych kontenerów"
fi

# Stop streamlit if running
if pgrep -f streamlit > /dev/null; then
    echo -e "${BLUE}[INFO]${NC} Zatrzymuję streamlit..."
    pkill -f streamlit
    echo -e "${GREEN}[✓]${NC} Streamlit zatrzymany"
fi

echo ""
echo -e "${GREEN}✅ Wszystko zatrzymane${NC}"
echo ""

