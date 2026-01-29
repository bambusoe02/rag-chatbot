import pytest
from playwright.sync_api import Page, expect
import allure


@allure.feature("Authentication")
@allure.story("User Registration")
def test_user_registration(page: Page):
    """Test user can register a new account"""
    
    page.goto("http://localhost:8501")
    
    # Click register
    page.click("text=Register")
    
    # Fill registration form
    unique_username = f"newuser_{page.evaluate('Date.now()')}"
    page.fill("input[name='username']", unique_username)
    page.fill("input[name='email']", f"{unique_username}@example.com")
    page.fill("input[name='password']", "StrongPassword123!")
    page.fill("input[name='confirm_password']", "StrongPassword123!")
    
    # Submit
    page.click("button:has-text('Create Account')")
    
    # Should redirect to chat page
    page.wait_for_url("**/chat", timeout=10000)
    
    # Should see welcome message or username
    expect(page.locator(f"text={unique_username}")).to_be_visible()


@allure.feature("Authentication")
@allure.story("User Login")
def test_user_login(page: Page):
    """Test user can login"""
    
    page.goto("http://localhost:8501")
    
    # Fill login form
    page.fill("input[name='username']", "test_user_e2e")
    page.fill("input[name='password']", "TestPassword123!")
    
    # Submit
    page.click("button:has-text('Login')")
    
    # Should redirect
    page.wait_for_url("http://localhost:8501/*", timeout=10000)
    
    # Should see user interface
    expect(page.locator("text=test_user_e2e")).to_be_visible(timeout=5000)


@allure.feature("Authentication")
@allure.story("Invalid Login")
def test_invalid_login(page: Page):
    """Test login with invalid credentials fails"""
    
    page.goto("http://localhost:8501")
    
    # Fill with wrong password
    page.fill("input[name='username']", "test_user_e2e")
    page.fill("input[name='password']", "WrongPassword123!")
    
    # Submit
    page.click("button:has-text('Login')")
    
    # Should see error message
    expect(page.locator("text=/incorrect|invalid|failed/i")).to_be_visible(timeout=5000)


@allure.feature("Authentication")
@allure.story("Logout")
def test_user_logout(authenticated_page: Page):
    """Test user can logout"""
    
    # Should be on authenticated page
    expect(authenticated_page.locator("text=test_user_e2e")).to_be_visible()
    
    # Click logout
    authenticated_page.click("button:has-text('Logout')")
    
    # Should redirect to login
    authenticated_page.wait_for_url("http://localhost:8501", timeout=10000)
    
    # Should see login form
    expect(authenticated_page.locator("input[name='username']")).to_be_visible()


@allure.feature("Authentication")
@allure.story("Password Strength")
def test_weak_password_rejected(page: Page):
    """Test weak passwords are rejected"""
    
    page.goto("http://localhost:8501")
    page.click("text=Register")
    
    # Fill with weak password
    page.fill("input[name='username']", "weakuser")
    page.fill("input[name='email']", "weak@example.com")
    page.fill("input[name='password']", "weak")
    page.fill("input[name='confirm_password']", "weak")
    
    # Submit
    page.click("button:has-text('Create Account')")
    
    # Should see validation error
    expect(page.locator("text=/password.*weak|password.*short|at least 8/i")).to_be_visible()

