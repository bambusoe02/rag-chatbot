"""API client utilities for frontend."""

import os
import requests
from typing import Optional, Dict, List, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class APIClient:
    """Client for API requests with retry logic and error handling."""
    
    def __init__(self, base_url: str = API_BASE_URL, max_retries: int = 3):
        """Initialize API client.
        
        Args:
            base_url: Base URL for API
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url
        self.max_retries = max_retries
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 120,
    ) -> Optional[Dict[str, Any]]:
        """Make API request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint
            data: Request data (for POST)
            files: Files to upload (for POST)
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Response JSON or None on error
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    response = requests.get(url, params=params, timeout=timeout)
                elif method == "POST":
                    if files:
                        response = requests.post(url, files=files, timeout=timeout)
                    else:
                        response = requests.post(url, json=data, timeout=timeout)
                elif method == "DELETE":
                    response = requests.delete(url, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request timeout after {self.max_retries} attempts")
                continue
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"API request failed: {str(e)}")
                continue
            except Exception as e:
                raise Exception(f"Unexpected error: {str(e)}")
        
        return None
    
    def health_check(self) -> bool:
        """Check if API is available."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat(self, question: str, temperature: Optional[float] = None, top_k: Optional[int] = None) -> Optional[Dict]:
        """Send chat query."""
        return self._request(
            "POST",
            "/api/chat",
            data={"question": question, "temperature": temperature, "top_k": top_k}
        )
    
    def upload_document(self, file_content: bytes, filename: str, content_type: str) -> Optional[Dict]:
        """Upload document."""
        files = {"file": (filename, file_content, content_type)}
        return self._request("POST", "/api/documents/upload", files=files)
    
    def list_documents(self) -> List[Dict]:
        """List all documents."""
        response = self._request("GET", "/api/documents")
        if response:
            return response.get("documents", [])
        return []
    
    def delete_document(self, filename: str) -> bool:
        """Delete document."""
        response = self._request("DELETE", f"/api/documents/{filename}")
        return response is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get analytics statistics."""
        response = self._request("GET", "/api/stats")
        return response or {}
    
    def get_document_preview(self, filename: str, max_chars: int = 500) -> Optional[Dict]:
        """Get document preview."""
        return self._request("GET", f"/api/documents/{filename}/preview", params={"max_chars": max_chars})
    
    def save_feedback(self, question: str, answer: str, is_positive: bool, comment: Optional[str] = None) -> bool:
        """Save feedback."""
        response = self._request(
            "POST",
            "/api/chat/feedback",
            data={"question": question, "answer": answer, "is_positive": is_positive, "comment": comment}
        )
        return response is not None
    
    def get_suggestions(self) -> Dict[str, Any]:
        """Get query suggestions."""
        response = self._request("GET", "/api/chat/suggestions")
        return response or {"suggestions": [], "templates": []}
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        response = self._request("GET", "/api/settings")
        return response or {}
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update settings."""
        response = self._request("POST", "/api/settings", data=settings)
        return response is not None
    
    def get_document_chunks(self, filename: str) -> Optional[Dict]:
        """Get all chunks for a document."""
        return self._request("GET", f"/api/documents/{filename}/chunks")
    
    def get_chat_history(self, limit: int = 50) -> List[Dict]:
        """Get chat history."""
        response = self._request("GET", "/api/chat/history", params={"limit": limit})
        if response:
            return response.get("queries", [])
        return []


# Global API client instance
api_client = APIClient()

