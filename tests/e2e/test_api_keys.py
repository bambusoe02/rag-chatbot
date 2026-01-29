import pytest
from playwright.sync_api import Page, expect
import allure


@allure.feature("API Keys")
@allure.story("Create API Key")
def test_create_api_key(authenticated_page: Page):
    """Test user can create API key"""
    
    page = authenticated_page
    
    # Navigate to API keys page
    page.click("text=API Keys")
    
    # Click create new key
    page.click("button:has-text('Create'), button:has-text('New')")
    
    # Fill form
    page.fill("input[name='name'], input[placeholder*='name' i]", "Test API Key")
    
    # Select permissions (if available)
    try:
        page.check("input[type='checkbox'][value='read']")
        page.check("input[type='checkbox'][value='write']")
    except:
        pass
    
    # Submit
    page.click("button:has-text('Generate'), button:has-text('Create')")
    
    # Should see success and new key
    expect(page.locator("text=/created|generated|success/i")).to_be_visible(timeout=5000)
    expect(page.locator("text=Test API Key")).to_be_visible()


@allure.feature("API Keys")
@allure.story("View API Keys")
def test_view_api_keys(authenticated_page: Page):
    """Test user can view their API keys"""
    
    page = authenticated_page
    
    # Navigate to API keys
    page.click("text=API Keys")
    
    # Should see API keys page
    expect(page.locator("text=/api.*keys/i")).to_be_visible()
    
    # Should see list or "no keys" message
    expect(page.locator("text=/your.*keys|no.*keys|create.*first/i")).to_be_visible()


@allure.feature("API Keys")
@allure.story("Revoke API Key")
def test_revoke_api_key(authenticated_page: Page):
    """Test user can revoke API key"""
    
    page = authenticated_page
    
    # Navigate to API keys
    page.click("text=API Keys")
    
    # Create a key first
    page.click("button:has-text('Create'), button:has-text('New')")
    page.fill("input[name='name'], input[placeholder*='name' i]", "Key to Revoke")
    page.click("button:has-text('Generate'), button:has-text('Create')")
    page.wait_for_timeout(1000)
    
    # Find revoke button
    revoke_button = page.locator("button:has-text('Revoke'), button:has-text('Delete')").first
    revoke_button.click()
    
    # Confirm if needed
    try:
        page.click("button:has-text('Yes'), button:has-text('Confirm')", timeout=2000)
    except:
        pass
    
    # Key should be removed
    page.wait_for_timeout(1000)
    expect(page.locator("text=Key to Revoke")).to_be_hidden(timeout=5000)

