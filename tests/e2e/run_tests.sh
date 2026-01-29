#!/bin/bash

set -e

echo "🎭 Running E2E Tests with Playwright"
echo "====================================="

# Configuration
HEADLESS=${HEADLESS:-true}
WORKERS=${WORKERS:-1}
BROWSER=${BROWSER:-chromium}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if services are running
echo "🔍 Checking services..."

if ! curl -s http://localhost:8000/health/status > /dev/null; then
    echo -e "${RED}❌ Backend not running${NC}"
    echo "Start with: docker-compose up -d backend"
    exit 1
fi

if ! curl -s http://localhost:8501/_stcore/health > /dev/null; then
    echo -e "${RED}❌ Frontend not running${NC}"
    echo "Start with: docker-compose up -d frontend"
    exit 1
fi

echo -e "${GREEN}✅ Services running${NC}"
echo ""

# Install Playwright browsers if needed
echo "📦 Installing Playwright browsers..."
python -m playwright install chromium
echo ""

# Run tests
echo "🧪 Running tests..."

# Parse command line arguments
TEST_PATH=${1:-tests/e2e}
MARKERS=${2:-""}

if [ -n "$MARKERS" ]; then
    echo "Running tests with markers: $MARKERS"
    pytest "$TEST_PATH" \
        -v \
        --tb=short \
        -m "$MARKERS" \
        --html=tests/e2e/reports/report.html \
        --self-contained-html \
        --alluredir=tests/e2e/reports/allure-results
else
    pytest "$TEST_PATH" \
        -v \
        --tb=short \
        --html=tests/e2e/reports/report.html \
        --self-contained-html \
        --alluredir=tests/e2e/reports/allure-results
fi

# Generate Allure report
if command -v allure &> /dev/null; then
    echo ""
    echo "📊 Generating Allure report..."
    allure generate tests/e2e/reports/allure-results -o tests/e2e/reports/allure-report --clean
    echo ""
    echo "View report:"
    echo "  allure open tests/e2e/reports/allure-report"
else
    echo ""
    echo "💡 Install Allure for better reports:"
    echo "  brew install allure  # macOS"
    echo "  npm install -g allure-commandline  # npm"
fi

echo ""
echo -e "${GREEN}✅ E2E tests completed!${NC}"
echo ""
echo "📊 HTML Report: tests/e2e/reports/report.html"
echo "📸 Screenshots: tests/e2e/screenshots/"

