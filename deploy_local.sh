#!/bin/bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     🚀 AUTOMATYCZNE LOKALNE WDROŻENIE RAG CHATBOT          ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Step 1: Check prerequisites
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "KROK 1: Sprawdzanie wymagań"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker zainstalowany: $DOCKER_VERSION"
else
    print_error "Docker NIE jest zainstalowany!"
    echo "   Zainstaluj: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose zainstalowany: $COMPOSE_VERSION"
else
    print_error "Docker Compose NIE jest zainstalowany!"
    echo "   Zainstaluj: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if docker info &> /dev/null; then
    print_success "Docker daemon działa"
else
    print_error "Docker daemon NIE działa!"
    echo "   Uruchom Docker Desktop lub: sudo systemctl start docker"
    exit 1
fi

# Check ports
echo ""
print_status "Sprawdzanie portów..."

PORT_8000=$(lsof -i :8000 2>/dev/null | wc -l)
PORT_8501=$(lsof -i :8501 2>/dev/null | wc -l)

if [ "$PORT_8000" -eq 0 ]; then
    print_success "Port 8000 (Backend) - WOLNY"
else
    print_warning "Port 8000 (Backend) - ZAJĘTY"
    echo "   Zatrzymuję proces na porcie 8000..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    print_success "Port 8000 zwolniony"
fi

if [ "$PORT_8501" -eq 0 ]; then
    print_success "Port 8501 (Frontend) - WOLNY"
else
    print_warning "Port 8501 (Frontend) - ZAJĘTY przez streamlit"
    echo "   Zatrzymuję streamlit..."
    pkill -f streamlit 2>/dev/null || true
    sleep 2
    if [ "$(lsof -i :8501 2>/dev/null | wc -l)" -eq 0 ]; then
        print_success "Port 8501 zwolniony"
    else
        print_warning "Port 8501 nadal zajęty - zmienię port w docker-compose.yml"
        # Backup original
        cp docker-compose.yml docker-compose.yml.backup
        # Change port to 8502
        sed -i 's/"8501:8501"/"8502:8501"/g' docker-compose.yml
        print_success "Port frontendu zmieniony na 8502"
        FRONTEND_PORT=8502
    fi
fi

# Check system resources
echo ""
print_status "Sprawdzanie zasobów systemowych..."

if command -v free &> /dev/null; then
    RAM_AVAILABLE=$(free -g | awk '/^Mem:/{print $7}')
    if [ "$RAM_AVAILABLE" -ge 8 ]; then
        print_success "RAM: ${RAM_AVAILABLE}GB dostępne (wystarcza)"
    else
        print_warning "RAM: ${RAM_AVAILABLE}GB dostępne (minimum 8GB zalecane)"
    fi
fi

DISK_AVAILABLE=$(df -h . | tail -1 | awk '{print $4}')
print_success "Dysk: ${DISK_AVAILABLE} dostępne"

# Step 2: Check configuration files
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "KROK 2: Konfiguracja"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    print_success "docker-compose.yml istnieje"
else
    print_error "docker-compose.yml NIE istnieje!"
    exit 1
fi

# Check/create .env
if [ ! -f ".env" ]; then
    print_warning ".env does not exist - creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env created from .env.example"
    else
        print_error ".env.example does not exist!"
        exit 1
    fi
else
    print_success ".env istnieje"
fi

# Generate SECRET_KEY if not set or default
if grep -q "CHANGE_THIS\|change-this\|SECRET_KEY=$" .env 2>/dev/null; then
    print_warning "SECRET_KEY nie jest ustawiony - generuję..."
    NEW_SECRET=$(openssl rand -hex 32)
    
    # Update .env
    if grep -q "^SECRET_KEY=" .env; then
        sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
    else
        echo "SECRET_KEY=$NEW_SECRET" >> .env
    fi
    print_success "SECRET_KEY wygenerowany i zapisany"
fi

# Step 3: Stop existing containers
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "KROK 3: Zatrzymywanie istniejących kontenerów"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker-compose ps | grep -q "Up"; then
    print_status "Zatrzymuję istniejące kontenery..."
    docker-compose down
    print_success "Kontenery zatrzymane"
else
    print_success "Brak uruchomionych kontenerów"
fi

# Step 4: Build and start
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "KROK 4: Budowanie i uruchamianie"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_status "Budowanie obrazów Docker (może zająć kilka minut)..."
docker-compose build --quiet

print_status "Uruchamianie kontenerów..."
docker-compose up -d

print_success "Kontenery uruchomione"

# Step 5: Wait for services
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "KROK 5: Oczekiwanie na gotowość serwisów"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_status "Czekam na uruchomienie serwisów (30 sekund)..."
sleep 10

# Check backend health
MAX_RETRIES=12
RETRY_COUNT=0
BACKEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health/status > /dev/null 2>&1; then
        BACKEND_READY=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 5
done
echo ""

if [ "$BACKEND_READY" = true ]; then
    print_success "Backend gotowy"
else
    print_warning "Backend może jeszcze się uruchamiać..."
fi

# Step 6: Status check
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "KROK 6: Sprawdzanie statusu"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_status "Status kontenerów:"
docker-compose ps

echo ""
print_status "Health check backend:"
if curl -s http://localhost:8000/health/status | grep -q "healthy"; then
    print_success "Backend: HEALTHY"
    curl -s http://localhost:8000/health/status | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health/status
else
    print_warning "Backend: Sprawdzam logi..."
    docker-compose logs backend --tail=20
fi

# Step 7: Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ WDROŻENIE ZAKOŃCZONE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

FRONTEND_PORT=${FRONTEND_PORT:-8501}

echo -e "${GREEN}🎉 Aplikacja uruchomiona pomyślnie!${NC}"
echo ""
echo "📱 Dostęp do aplikacji:"
echo "   Frontend:  http://localhost:${FRONTEND_PORT}"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   ReDoc:     http://localhost:8000/redoc"
echo ""
echo "🔧 Przydatne komendy:"
echo "   Status:    docker-compose ps"
echo "   Logi:      docker-compose logs -f"
echo "   Restart:   docker-compose restart"
echo "   Stop:      docker-compose down"
echo ""
echo "📊 Monitoring:"
echo "   Health:    curl http://localhost:8000/health/status"
echo "   Metrics:   curl http://localhost:8000/metrics"
echo ""
echo "🆘 Jeśli coś nie działa:"
echo "   docker-compose logs"
echo "   docker-compose logs backend"
echo "   docker-compose logs frontend"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

