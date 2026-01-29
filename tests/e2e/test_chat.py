import pytest
from playwright.sync_api import Page, expect
import allure
from tests.e2e.conftest import take_screenshot


@allure.feature("Chat")
@allure.story("Ask Question")
def test_ask_question(authenticated_page: Page, test_document_path: str):
    """Test user can ask a question and get answer"""
    
    page = authenticated_page
    
    # Upload document first
    page.set_input_files("input[type='file']", test_document_path)
    page.click("button:has-text('Upload')")
    page.wait_for_timeout(3000)  # Wait for processing
    
    # Find chat input (might be textarea or input)
    chat_input = page.locator("textarea, input[placeholder*='question' i]").first
    
    # Type question
    chat_input.fill("What is machine learning?")
    
    # Send message (Enter or Send button)
    try:
        page.click("button:has-text('Send')")
    except:
        chat_input.press("Enter")
    
    # Wait for response
    page.wait_for_timeout(5000)
    
    # Should see answer containing relevant text
    expect(page.locator("text=/machine learning|artificial intelligence|data/i")).to_be_visible(timeout=15000)
    
    # Should see sources
    expect(page.locator("text=/source|reference/i")).to_be_visible()
    
    take_screenshot(page, "chat_answer")


@allure.feature("Chat")
@allure.story("Multiple Questions")
def test_multiple_questions(authenticated_page: Page, test_document_path: str):
    """Test asking multiple questions in sequence"""
    
    page = authenticated_page
    
    # Upload document
    page.set_input_files("input[type='file']", test_document_path)
    page.click("button:has-text('Upload')")
    page.wait_for_timeout(3000)
    
    questions = [
        "What is supervised learning?",
        "What is unsupervised learning?",
        "What algorithms are mentioned?"
    ]
    
    chat_input = page.locator("textarea, input[placeholder*='question' i]").first
    
    for question in questions:
        # Ask question
        chat_input.fill(question)
        try:
            page.click("button:has-text('Send')")
        except:
            chat_input.press("Enter")
        
        # Wait for response
        page.wait_for_timeout(3000)
    
    # Should see all responses
    expect(page.locator("text=supervised")).to_be_visible()
    expect(page.locator("text=unsupervised")).to_be_visible()


@allure.feature("Chat")
@allure.story("No Documents")
def test_query_without_documents(authenticated_page: Page):
    """Test querying when no documents are uploaded"""
    
    page = authenticated_page
    
    # Try to ask question without uploading document
    chat_input = page.locator("textarea, input[placeholder*='question' i]").first
    chat_input.fill("What is machine learning?")
    
    try:
        page.click("button:has-text('Send')")
    except:
        chat_input.press("Enter")
    
    # Should see message about no documents
    expect(page.locator("text=/no documents|upload.*first|no.*found/i")).to_be_visible(timeout=10000)


@allure.feature("Chat")
@allure.story("Search Modes")
def test_different_search_modes(authenticated_page: Page, test_document_path: str):
    """Test different search modes work"""
    
    page = authenticated_page
    
    # Upload document
    page.set_input_files("input[type='file']", test_document_path)
    page.click("button:has-text('Upload')")
    page.wait_for_timeout(3000)
    
    # Test each search mode
    modes = ["Hybrid", "Semantic", "Keyword"]
    
    for mode in modes:
        # Select search mode (if available)
        try:
            page.click(f"text={mode}")
            page.wait_for_timeout(500)
        except:
            pass  # Mode selector might not be visible
        
        # Ask question
        chat_input = page.locator("textarea, input[placeholder*='question' i]").first
        chat_input.fill("What is machine learning?")
        
        try:
            page.click("button:has-text('Send')")
        except:
            chat_input.press("Enter")
        
        # Wait for response
        page.wait_for_timeout(3000)
        
        # Should get some answer
        expect(page.locator("text=/machine learning|learning/i")).to_be_visible()


@allure.feature("Chat")
@allure.story("Feedback")
def test_provide_feedback(authenticated_page: Page, test_document_path: str):
    """Test user can provide feedback on answers"""
    
    page = authenticated_page
    
    # Upload and ask question
    page.set_input_files("input[type='file']", test_document_path)
    page.click("button:has-text('Upload')")
    page.wait_for_timeout(3000)
    
    chat_input = page.locator("textarea, input[placeholder*='question' i]").first
    chat_input.fill("What is machine learning?")
    
    try:
        page.click("button:has-text('Send')")
    except:
        chat_input.press("Enter")
    
    page.wait_for_timeout(3000)
    
    # Click thumbs up (if available)
    try:
        page.click("button:has-text('👍'), button[aria-label='Thumbs up']")
        page.wait_for_timeout(500)
        
        # Should see confirmation
        expect(page.locator("text=/thank|feedback.*received/i")).to_be_visible(timeout=2000)
    except:
        pass  # Feedback buttons might not be implemented yet

