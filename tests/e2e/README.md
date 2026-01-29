# End-to-End Testing Guide

Automated browser testing with Playwright.

## Quick Start
```bash
# Install dependencies
pip install -r requirements-dev.txt
python -m playwright install chromium

# Start services
docker-compose up -d

# Run all tests
./tests/e2e/run_tests.sh

# View report
open tests/e2e/reports/report.html
```

## Test Categories

### Authentication Tests
```bash
pytest tests/e2e/test_auth.py -v
```

Tests:
- ✅ User registration
- ✅ Login/logout
- ✅ Invalid credentials
- ✅ Password validation

### Document Tests
```bash
pytest tests/e2e/test_documents.py -v
```

Tests:
- ✅ Upload document
- ✅ View documents
- ✅ Delete document
- ✅ Invalid file types
- ✅ Large file rejection

### Chat Tests
```bash
pytest tests/e2e/test_chat.py -v
```

Tests:
- ✅ Ask questions
- ✅ Multiple questions
- ✅ No documents handling
- ✅ Search modes
- ✅ Feedback system

### Analytics Tests
```bash
pytest tests/e2e/test_analytics.py -v
```

Tests:
- ✅ View dashboard
- ✅ Time range filters
- ✅ Popular queries

### API Key Tests
```bash
pytest tests/e2e/test_api_keys.py -v
```

Tests:
- ✅ Create API key
- ✅ View keys
- ✅ Revoke key

### Admin Tests
```bash
pytest tests/e2e/test_admin.py -v -m admin
```

Tests:
- ✅ Admin dashboard
- ✅ View users
- ✅ System status

## Running Options

### Headed Mode (see browser)
```bash
HEADLESS=false ./tests/e2e/run_tests.sh
```

### Slow Motion (debug)
```bash
E2E_SLOW_MO=1000 ./tests/e2e/run_tests.sh
```

### Specific Test
```bash
pytest tests/e2e/test_chat.py::test_ask_question -v
```

### Parallel Execution
```bash
pytest tests/e2e -n 4 -v  # 4 workers
```

### By Marker
```bash
pytest tests/e2e -m admin -v  # Only admin tests
pytest tests/e2e -m "not admin" -v  # Skip admin tests
```

## Debugging

### Interactive Debugging
```bash
# Add to test:
page.pause()  # Opens Playwright Inspector

# Run test
pytest tests/e2e/test_chat.py::test_ask_question -v
```

### Screenshots
Screenshots automatically saved on failure:
```
tests/e2e/screenshots/
```

### Video Recording
```python
# In conftest.py
context = browser.new_context(
    record_video_dir="tests/e2e/videos/"
)
```

### Console Logs
```python
# Capture browser console
page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run E2E Tests
  run: |
    docker-compose up -d
    ./tests/e2e/run_tests.sh
    
- name: Upload Test Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: e2e-reports
    path: tests/e2e/reports/
```

## Troubleshooting

**Tests fail immediately:**
- Check services: `docker-compose ps`
- Check logs: `docker-compose logs -f`

**Browser not launching:**
- Install browsers: `python -m playwright install`
- Check display: `xhost +` (Linux)

**Timeouts:**
- Increase timeout in conftest.py
- Check server performance
- Use `--headed` to see what's happening

**Flaky tests:**
- Add explicit waits: `page.wait_for_timeout(1000)`
- Use `expect().to_be_visible(timeout=10000)`
- Check for race conditions

## Best Practices

1. **Use data-testid attributes** in UI
2. **Wait for elements** before interacting
3. **Take screenshots** on important steps
4. **Isolate tests** (each test independent)
5. **Clean up** (delete test data after)
6. **Use fixtures** for common setup
7. **Page Object Model** for complex pages

## Coverage

Current coverage:
- ✅ Authentication flows
- ✅ Document management
- ✅ Chat interactions
- ✅ Analytics viewing
- ✅ API key management
- ✅ Admin functions

Missing:
- ⏳ Multi-language UI
- ⏳ Webhook configuration
- ⏳ Email settings

