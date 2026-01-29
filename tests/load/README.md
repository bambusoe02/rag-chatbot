# Load Testing Guide

Test RAG Chatbot performance under various load conditions.

## Quick Start
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Start backend
docker-compose up -d

# Run smoke test (quick validation)
./tests/load/run_tests.sh smoke

# View report
open tests/load/reports/smoke_report.html
```

## Test Scenarios

### 1. Smoke Test (2 min)
**Purpose:** Quick validation that system works under minimal load
```bash
./tests/load/run_tests.sh smoke
```

**Expected:** <100ms avg response, 0% failures

### 2. Load Test (10 min)
**Purpose:** Simulate normal production traffic
```bash
./tests/load/run_tests.sh load
```

**Expected:** <1000ms avg response, <1% failures, 100+ RPS

### 3. Stress Test (15 min)
**Purpose:** Push system to limits
```bash
./tests/load/run_tests.sh stress
```

**Expected:** <2000ms avg response, <5% failures

### 4. Spike Test (5 min)
**Purpose:** Test sudden traffic spikes
```bash
./tests/load/run_tests.sh spike
```

**Expected:** System recovers, no crashes

### 5. Endurance Test (4 hours)
**Purpose:** Find memory leaks, resource exhaustion
```bash
./tests/load/run_tests.sh endurance
```

**Expected:** Stable performance over time

## Manual Testing
```bash
# Web UI (interactive)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# Set users and spawn rate
# Start swarming
```

## Analyze Results
```bash
python tests/load/analyze_results.py
```

Shows:
- Overall statistics
- Response time breakdown
- Endpoint performance
- Recommendations

## Interpreting Results

**Good Performance:**
- ✅ Avg response < 1s
- ✅ 95th percentile < 2s
- ✅ Failure rate < 1%
- ✅ Consistent performance over time

**Warning Signs:**
- ⚠️  Avg response 1-3s
- ⚠️  Failure rate 1-5%
- ⚠️  Increasing response times

**Poor Performance:**
- ❌ Avg response > 3s
- ❌ Failure rate > 5%
- ❌ Crashes or timeouts
- ❌ Memory leaks

## Optimization Tips

If tests show poor performance:

1. **Enable caching** (Redis)
2. **Scale horizontally** (add replicas)
3. **Optimize queries** (check slow queries)
4. **Add rate limiting**
5. **Increase resources** (CPU, memory)
6. **Use CDN** for static assets

