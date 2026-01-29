import pytest
from playwright.sync_api import Page, expect
import allure
from tests.e2e.conftest import take_screenshot


@allure.feature("Documents")
@allure.story("Upload Document")
def test_upload_document(authenticated_page: Page, test_document_path: str):
    """Test user can upload a document"""
    
    page = authenticated_page
    
    # Navigate to upload section (or might be on main page)
    # Depends on UI structure
    
    # Find file input (might be hidden)
    page.set_input_files("input[type='file']", test_document_path)
    
    # Click upload button
    page.click("button:has-text('Upload')")
    
    # Wait for upload to complete
    page.wait_for_timeout(2000)
    
    # Should see success message
    expect(page.locator("text=/uploaded|success/i")).to_be_visible(timeout=10000)
    
    # Document should appear in list
    expect(page.locator("text=test_document.txt")).to_be_visible()
    
    take_screenshot(page, "document_uploaded")


@allure.feature("Documents")
@allure.story("View Documents")
def test_view_document_list(authenticated_page: Page):
    """Test user can view their documents"""
    
    page = authenticated_page
    
    # Navigate to documents section
    # Look for documents heading or list
    expect(page.locator("text=/my documents|documents/i")).to_be_visible()
    
    # Should see document list (might be empty)
    # If empty, should see "No documents" message


@allure.feature("Documents")
@allure.story("Delete Document")
def test_delete_document(authenticated_page: Page, test_document_path: str):
    """Test user can delete a document"""
    
    page = authenticated_page
    
    # First upload a document
    page.set_input_files("input[type='file']", test_document_path)
    page.click("button:has-text('Upload')")
    page.wait_for_timeout(2000)
    
    # Find delete button for the document
    # This depends on UI structure - might be trash icon
    delete_button = page.locator("button:has-text('🗑️'), button[aria-label='Delete']").first
    delete_button.click()
    
    # Confirm deletion if there's a dialog
    try:
        page.click("button:has-text('Yes'), button:has-text('Confirm')", timeout=2000)
    except:
        pass
    
    # Document should be removed
    page.wait_for_timeout(1000)
    expect(page.locator("text=test_document.txt")).to_be_hidden(timeout=5000)


@allure.feature("Documents")
@allure.story("Invalid File Type")
def test_upload_invalid_file_type(authenticated_page: Page, tmp_path):
    """Test uploading invalid file type is rejected"""
    
    page = authenticated_page
    
    # Create executable file (not allowed)
    exe_file = tmp_path / "malicious.exe"
    exe_file.write_bytes(b"MZ\x90\x00")  # PE header
    
    # Try to upload
    page.set_input_files("input[type='file']", str(exe_file))
    page.click("button:has-text('Upload')")
    
    # Should see error
    expect(page.locator("text=/not allowed|invalid file|unsupported/i")).to_be_visible(timeout=5000)


@allure.feature("Documents")
@allure.story("Large File Upload")
def test_upload_large_file(authenticated_page: Page, tmp_path):
    """Test uploading file larger than limit is rejected"""
    
    page = authenticated_page
    
    # Create large file (>50MB)
    large_file = tmp_path / "large.txt"
    large_file.write_bytes(b"x" * (51 * 1024 * 1024))  # 51 MB
    
    # Try to upload
    page.set_input_files("input[type='file']", str(large_file))
    page.click("button:has-text('Upload')")
    
    # Should see error about file size
    expect(page.locator("text=/too large|file size|exceeds/i")).to_be_visible(timeout=5000)

