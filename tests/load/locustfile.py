from locust import HttpUser, task, between, events
from faker import Faker
import random
import json
import logging

fake = Faker()
logger = logging.getLogger(__name__)


class RagChatbotUser(HttpUser):
    """
    Simulates a user interacting with RAG Chatbot
    
    Weight distribution:
    - 50% queries (most common)
    - 20% document uploads
    - 15% browsing analytics
    - 10% API key management
    - 5% admin actions
    """
    
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Register and login
        self.username = fake.user_name()
        self.password = "TestPassword123!"
        self.email = fake.email()
        
        # Register
        self.client.post("/api/auth/register", json={
            "username": self.username,
            "email": self.email,
            "password": self.password
        })
        
        # Login
        response = self.client.post("/api/auth/login", data={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            logger.info(f"User {self.username} logged in successfully")
        else:
            logger.error(f"Failed to login: {response.status_code}")
            self.headers = {}
    
    @task(50)
    def query_documents(self):
        """
        Query documents - most common action (50% of traffic)
        """
        questions = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain neural networks",
            "What are the benefits of RAG?",
            "How to implement vector search?",
            "Compare supervised and unsupervised learning",
            "What is transfer learning?",
            "Explain attention mechanism",
            "How does BERT work?",
            "What is prompt engineering?",
        ]
        
        question = random.choice(questions)
        
        with self.client.post(
            "/api/chat",
            json={
                "question": question,
                "search_mode": random.choice(["hybrid", "semantic", "keyword"]),
                "top_k": random.choice([3, 5, 10])
            },
            headers=self.headers,
            catch_response=True,
            name="Query documents"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "answer" in data:
                    response.success()
                else:
                    response.failure("No answer in response")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(20)
    def upload_document(self):
        """
        Upload document - 20% of traffic
        """
        # Create fake document content
        content = f"""
        # {fake.catch_phrase()}
        
        ## Introduction
        {fake.paragraph(nb_sentences=5)}
        
        ## Main Content
        {fake.paragraph(nb_sentences=10)}
        
        ## Technical Details
        {fake.paragraph(nb_sentences=8)}
        
        ## Conclusion
        {fake.paragraph(nb_sentences=4)}
        """
        
        filename = f"{fake.word()}_{fake.random_int(1, 1000)}.txt"
        
        files = {
            "file": (filename, content.encode(), "text/plain")
        }
        
        with self.client.post(
            "/api/documents/upload",
            files=files,
            headers=self.headers,
            catch_response=True,
            name="Upload document"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Upload failed: {response.status_code}")
    
    @task(15)
    def view_analytics(self):
        """
        View analytics - 15% of traffic
        """
        endpoints = [
            "/api/analytics/popular-queries?days=7",
            "/api/analytics/performance?days=7",
            "/api/analytics/satisfaction?days=7",
            "/api/analytics/trends?days=30",
        ]
        
        endpoint = random.choice(endpoints)
        
        with self.client.get(
            endpoint,
            headers=self.headers,
            catch_response=True,
            name="View analytics"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Analytics failed: {response.status_code}")
    
    @task(10)
    def manage_api_keys(self):
        """
        API key management - 10% of traffic
        """
        # List API keys
        self.client.get("/api/keys", headers=self.headers, name="List API keys")
        
        # Create API key (occasionally)
        if random.random() < 0.3:
            self.client.post(
                "/api/keys",
                json={
                    "name": f"test-key-{fake.random_int(1, 1000)}",
                    "permissions": ["read", "write"],
                    "rate_limit": 100
                },
                headers=self.headers,
                name="Create API key"
            )
    
    @task(5)
    def view_documents(self):
        """
        View document list - 5% of traffic
        """
        self.client.get(
            "/api/documents",
            headers=self.headers,
            name="List documents"
        )
    
    @task(3)
    def health_check(self):
        """
        Health check - 3% of traffic
        """
        self.client.get("/health/status", name="Health check")
    
    @task(2)
    def view_metrics(self):
        """
        View Prometheus metrics - 2% of traffic
        """
        self.client.get("/metrics", name="Metrics")


class AdminUser(HttpUser):
    """
    Admin user performing admin-specific tasks
    Runs less frequently (lower weight)
    """
    
    wait_time = between(10, 20)
    weight = 2  # 2% of users are admins
    
    def on_start(self):
        # Login as admin
        self.client.post("/api/auth/login", data={
            "username": "admin",
            "password": "admin_password"
        })
    
    @task
    def view_all_users(self):
        """Admin: View all users"""
        self.client.get("/api/admin/users", name="Admin: List users")
    
    @task
    def view_system_stats(self):
        """Admin: View system statistics"""
        self.client.get("/api/admin/stats", name="Admin: System stats")


class APIUser(HttpUser):
    """
    External API user (using API keys instead of JWT)
    """
    
    wait_time = between(1, 3)
    weight = 5  # 5% of users use API keys
    
    def on_start(self):
        # Simulate having an API key
        self.api_key = "test-api-key-12345"
        self.headers = {"X-API-Key": self.api_key}
    
    @task
    def api_query(self):
        """API: Query via API key"""
        self.client.post(
            "/api/chat",
            json={
                "question": "What is machine learning?",
                "search_mode": "hybrid"
            },
            headers=self.headers,
            name="API: Query"
        )


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    logger.info("🚀 Load test started")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    logger.info("✅ Load test completed")
    
    # Print summary
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Max response time: {stats.total.max_response_time:.2f}ms")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests"""
    if response_time > 5000:  # 5 seconds
        logger.warning(f"Slow request: {name} took {response_time:.2f}ms")

