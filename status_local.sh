#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "📊 Status RAG Chatbot"
echo "===================="
echo ""

# Container status
echo -e "${BLUE}Kontenery:${NC}"
docker-compose ps

echo ""

# Health checks
echo -e "${BLUE}Health Checks:${NC}"

# Backend
if curl -s http://localhost:8000/health/status > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health/status)
    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "${GREEN}✓ Backend: HEALTHY${NC}"
        echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
    else
        echo -e "${YELLOW}⚠ Backend: RUNNING (checking...)${NC}"
    fi
else
    echo -e "${RED}✗ Backend: NOT RESPONDING${NC}"
fi

echo ""

# Ports
echo -e "${BLUE}Porty:${NC}"
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Port 8000 (Backend): OCCUPIED${NC}"
else
    echo -e "${RED}✗ Port 8000 (Backend): FREE${NC}"
fi

if lsof -i :8501 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Port 8501 (Frontend): OCCUPIED${NC}"
elif lsof -i :8502 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Port 8502 (Frontend): OCCUPIED${NC}"
else
    echo -e "${RED}✗ Port 8501/8502 (Frontend): FREE${NC}"
fi

echo ""

# Resources
echo -e "${BLUE}Zasoby:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -10 || echo "Nie można pobrać statystyk"

echo ""
echo -e "${BLUE}URLs:${NC}"
echo "  Frontend: http://localhost:8501 (lub 8502)"
echo "  Backend:  http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo ""

