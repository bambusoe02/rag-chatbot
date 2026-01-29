"""
RAG Chatbot Python Client Example

Usage:
    client = RagChatbotClient(base_url="http://localhost:8000")
    client.login("username", "password")
    client.upload_document("document.pdf")
    answer = client.ask("What is machine learning?")
"""

import requests
from typing import Optional, Dict, Any, List
import os


class RagChatbotClient:
    """Python client for RAG Chatbot API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def register(self, username: str, email: str, password: str, full_name: str = None) -> Dict:
        """Register new user"""
        response = self.session.post(
            f"{self.base_url}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        response.raise_for_status()
        return response.json()
    
    def login(self, username: str, password: str) -> str:
        """Login and get access token"""
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data["access_token"]
        return self.token
    
    def upload_document(self, file_path: str) -> Dict:
        """Upload a document for processing"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = self.session.post(
                f"{self.base_url}/api/documents/upload",
                files=files,
                headers={"Authorization": f"Bearer {self.token}"}
            )
        
        response.raise_for_status()
        return response.json()
    
    def list_documents(self) -> List[Dict]:
        """Get list of uploaded documents"""
        response = self.session.get(
            f"{self.base_url}/api/documents",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()["documents"]
    
    def delete_document(self, filename: str) -> Dict:
        """Delete a document"""
        response = self.session.delete(
            f"{self.base_url}/api/documents/{filename}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def ask(
        self,
        question: str,
        search_mode: str = "hybrid",
        top_k: int = 5
    ) -> Dict:
        """Ask a question and get answer"""
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "question": question,
                "search_mode": search_mode,
                "top_k": top_k
            },
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def create_api_key(
        self,
        name: str,
        permissions: List[str] = None,
        rate_limit: int = 100
    ) -> Dict:
        """Create a new API key"""
        response = self.session.post(
            f"{self.base_url}/api/keys",
            json={
                "name": name,
                "permissions": permissions or ["read", "write"],
                "rate_limit": rate_limit
            },
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_analytics(self, days: int = 7) -> Dict:
        """Get analytics data"""
        response = self.session.get(
            f"{self.base_url}/api/analytics/performance?days={days}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = RagChatbotClient()
    
    # Login
    print("🔐 Logging in...")
    client.login("test_user", "test_password")
    print("✅ Logged in successfully")
    
    # Upload document
    print("\n📄 Uploading document...")
    result = client.upload_document("example.pdf")
    print(f"✅ Uploaded: {result['filename']}")
    
    # List documents
    print("\n📚 Your documents:")
    docs = client.list_documents()
    for doc in docs:
        print(f"  - {doc['filename']} ({doc['file_size']} bytes)")
    
    # Ask question
    print("\n💬 Asking question...")
    response = client.ask("What is machine learning?")
    print(f"Answer: {response['answer']}")
    print(f"Sources: {len(response['sources'])} documents")
    
    # Get analytics
    print("\n📊 Analytics:")
    analytics = client.get_analytics(days=7)
    print(f"  Total queries: {analytics['total_queries']}")
    print(f"  Avg response time: {analytics['avg_response_time_ms']:.0f}ms")

