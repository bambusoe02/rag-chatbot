import pytest
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
import os
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8501")
BACKEND_URL = os.getenv("E2E_BACKEND_URL", "http://localhost:8000")
HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("E2E_SLOW_MO", "0"))  # Slow down by N ms

# Test user credentials
TEST_USER = {
    "username": "test_user_e2e",
    "email": "test@example.com",
    "password": "TestPassword123!"
}

ADMIN_USER = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin_password"
}


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Launch browser once for all tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Create new browser context for each test (isolated cookies/storage)"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="America/New_York",
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Create new page for each test"""
    page = context.new_page()
    page.set_default_timeout(30000)  # 30 seconds
    yield page
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page) -> Page:
    """Page with authenticated user"""
    # Navigate to login page
    page.goto(BASE_URL)
    
    # Register user (if doesn't exist)
    try:
        page.click("text=Register", timeout=2000)
        page.fill("input[name='username']", TEST_USER["username"])
        page.fill("input[name='email']", TEST_USER["email"])
        page.fill("input[name='password']", TEST_USER["password"])
        page.fill("input[name='confirm_password']", TEST_USER["password"])
        page.click("button:has-text('Create Account')")
        page.wait_for_timeout(1000)
    except:
        pass  # User might already exist
    
    # Login
    page.goto(BASE_URL)
    page.fill("input[name='username']", TEST_USER["username"])
    page.fill("input[name='password']", TEST_USER["password"])
    page.click("button:has-text('Login')")
    
    # Wait for redirect
    page.wait_for_url(f"{BASE_URL}/*", timeout=10000)
    
    logger.info(f"Authenticated as {TEST_USER['username']}")
    
    return page


@pytest.fixture(scope="function")
def admin_page(page: Page) -> Page:
    """Page with admin user"""
    page.goto(BASE_URL)
    
    page.fill("input[name='username']", ADMIN_USER["username"])
    page.fill("input[name='password']", ADMIN_USER["password"])
    page.click("button:has-text('Login')")
    
    page.wait_for_url(f"{BASE_URL}/*", timeout=10000)
    
    logger.info("Authenticated as admin")
    
    return page


@pytest.fixture
def test_document_path(tmp_path):
    """Create a temporary test document"""
    doc_path = tmp_path / "test_document.txt"
    doc_path.write_text("""
    Machine Learning Guide
    
    Machine learning is a subset of artificial intelligence that enables systems to learn from data.
    
    Types of Machine Learning:
    1. Supervised Learning - Learning from labeled data
    2. Unsupervised Learning - Finding patterns in unlabeled data
    3. Reinforcement Learning - Learning through trial and error
    
    Common algorithms include neural networks, decision trees, and support vector machines.
    """)
    return str(doc_path)


def take_screenshot(page: Page, name: str):
    """Helper to take screenshots"""
    screenshot_dir = "tests/e2e/screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    page.screenshot(path=f"{screenshot_dir}/{name}.png")
    logger.info(f"Screenshot saved: {name}.png")

