#!/bin/bash

set -e

echo "🧪 RAG Chatbot Load Testing Suite"
echo "=================================="
echo ""

# Configuration
API_URL=${API_URL:-http://localhost:8000}
SCENARIO=${1:-smoke}
REPORT_DIR="tests/load/reports"

# Create reports directory
mkdir -p "$REPORT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to run a test scenario
run_scenario() {
    local scenario=$1
    
    echo -e "${YELLOW}Running $scenario test...${NC}"
    
    case $scenario in
        smoke)
            echo "💨 Smoke Test - Quick validation"
            locust -f tests/load/locustfile.py \
                --host=$API_URL \
                --users 5 \
                --spawn-rate 1 \
                --run-time 2m \
                --headless \
                --html "$REPORT_DIR/smoke_report.html" \
                --csv "$REPORT_DIR/smoke"
            ;;
        
        load)
            echo "📊 Load Test - Normal traffic simulation"
            locust -f tests/load/locustfile.py \
                --host=$API_URL \
                --users 50 \
                --spawn-rate 5 \
                --run-time 10m \
                --headless \
                --html "$REPORT_DIR/load_report.html" \
                --csv "$REPORT_DIR/load"
            ;;
        
        stress)
            echo "💪 Stress Test - High load"
            locust -f tests/load/locustfile.py \
                --host=$API_URL \
                --users 200 \
                --spawn-rate 20 \
                --run-time 15m \
                --headless \
                --html "$REPORT_DIR/stress_report.html" \
                --csv "$REPORT_DIR/stress"
            ;;
        
        spike)
            echo "⚡ Spike Test - Sudden traffic increase"
            locust -f tests/load/spike_test.py \
                --host=$API_URL \
                --users 500 \
                --spawn-rate 100 \
                --run-time 5m \
                --headless \
                --html "$REPORT_DIR/spike_report.html" \
                --csv "$REPORT_DIR/spike"
            ;;
        
        endurance)
            echo "🏃 Endurance Test - Long duration (4 hours)"
            echo "⚠️  This will take 4 hours. Continue? (yes/no)"
            read -r confirm
            if [ "$confirm" != "yes" ]; then
                echo "Test cancelled"
                return
            fi
            
            locust -f tests/load/endurance_test.py \
                --host=$API_URL \
                --users 100 \
                --spawn-rate 10 \
                --run-time 4h \
                --headless \
                --html "$REPORT_DIR/endurance_report.html" \
                --csv "$REPORT_DIR/endurance"
            ;;
        
        all)
            echo "🚀 Running all tests sequentially"
            run_scenario smoke
            sleep 60
            run_scenario load
            sleep 120
            run_scenario stress
            ;;
        
        *)
            echo -e "${RED}Unknown scenario: $scenario${NC}"
            echo "Available scenarios: smoke, load, stress, spike, endurance, all"
            exit 1
            ;;
    esac
}

# Check if backend is running
echo "🔍 Checking if backend is available..."
if ! curl -s "$API_URL/health/status" > /dev/null; then
    echo -e "${RED}❌ Backend not accessible at $API_URL${NC}"
    echo "Please start the backend first:"
    echo "  docker-compose up -d backend"
    exit 1
fi

echo -e "${GREEN}✅ Backend is running${NC}"
echo ""

# Run the test
run_scenario "$SCENARIO"

# Display results
echo ""
echo "=================================="
echo -e "${GREEN}✅ Test completed!${NC}"
echo ""
echo "📊 Reports generated in: $REPORT_DIR"
echo "   HTML Report: $REPORT_DIR/${SCENARIO}_report.html"
echo "   CSV Data: $REPORT_DIR/${SCENARIO}_*.csv"
echo ""
echo "View HTML report:"
echo "  open $REPORT_DIR/${SCENARIO}_report.html"

