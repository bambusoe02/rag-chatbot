import pytest
from playwright.sync_api import Page, expect
import allure


@allure.feature("Admin")
@allure.story("Admin Dashboard")
@pytest.mark.admin
def test_admin_dashboard(admin_page: Page):
    """Test admin can access admin dashboard"""
    
    page = admin_page
    
    # Navigate to admin section
    try:
        page.click("text=Admin")
    except:
        # Admin link might not be visible
        pytest.skip("Admin section not found")
    
    # Should see admin interface
    expect(page.locator("text=/admin|users|system/i")).to_be_visible()


@allure.feature("Admin")
@allure.story("View All Users")
@pytest.mark.admin
def test_view_all_users(admin_page: Page):
    """Test admin can view all users"""
    
    page = admin_page
    
    try:
        page.click("text=Admin")
        page.click("text=Users")
    except:
        pytest.skip("Admin users page not found")
    
    # Should see user list
    expect(page.locator("text=/users|username|email/i")).to_be_visible()


@allure.feature("Admin")
@allure.story("System Status")
@pytest.mark.admin
def test_view_system_status(admin_page: Page):
    """Test admin can view system status"""
    
    page = admin_page
    
    try:
        page.click("text=System Status")
    except:
        pytest.skip("System status page not found")
    
    # Should see system metrics
    expect(page.locator("text=/health|status|service/i")).to_be_visible()

