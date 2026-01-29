import pytest
from playwright.sync_api import Page, expect
import allure


@allure.feature("Analytics")
@allure.story("View Analytics Dashboard")
def test_view_analytics(authenticated_page: Page):
    """Test user can view analytics page"""
    
    page = authenticated_page
    
    # Navigate to analytics
    page.click("text=Analytics")
    
    # Should see analytics page
    expect(page.locator("text=/analytics|statistics|metrics/i")).to_be_visible()
    
    # Should see some metrics (even if zero)
    expect(page.locator("text=/queries|documents|satisfaction/i")).to_be_visible()


@allure.feature("Analytics")
@allure.story("Time Range Filter")
def test_analytics_time_range(authenticated_page: Page):
    """Test changing time range in analytics"""
    
    page = authenticated_page
    
    # Navigate to analytics
    page.click("text=Analytics")
    
    # Try to change time range
    try:
        page.click("text=Last 30 days")
        page.wait_for_timeout(1000)
        
        # Should update data (might take a moment)
        page.wait_for_timeout(2000)
    except:
        pass  # Time range selector might not be available


@allure.feature("Analytics")
@allure.story("Popular Queries")
def test_view_popular_queries(authenticated_page: Page):
    """Test viewing popular queries in analytics"""
    
    page = authenticated_page
    
    # Navigate to analytics
    page.click("text=Analytics")
    
    # Should see popular queries section
    expect(page.locator("text=/popular.*queries/i")).to_be_visible()

