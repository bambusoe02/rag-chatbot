from locust import HttpUser, task, constant_pacing, events
import logging

logger = logging.getLogger(__name__)


class SpikeTestUser(HttpUser):
    """
    Spike test: Sudden increase in load
    Tests how system handles traffic spikes
    """
    
    wait_time = constant_pacing(1)  # 1 request per second per user
    
    def on_start(self):
        # Quick login
        response = self.client.post("/api/auth/login", data={
            "username": "test_user",
            "password": "test_password"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task
    def rapid_fire_queries(self):
        """Send queries as fast as possible"""
        self.client.post(
            "/api/chat",
            json={"question": "What is AI?", "search_mode": "hybrid"},
            headers=self.headers,
            name="Spike: Query"
        )


class StressTestUser(HttpUser):
    """
    Stress test: Push system beyond normal limits
    Find breaking point
    """
    
    wait_time = constant_pacing(0.5)  # 2 requests per second per user
    
    @task
    def heavy_query(self):
        """Large, complex query"""
        long_question = "Explain " + " and ".join([
            "machine learning",
            "deep learning",
            "neural networks",
            "reinforcement learning",
            "natural language processing"
        ]) + " in detail with examples?"
        
        self.client.post(
            "/api/chat",
            json={
                "question": long_question,
                "search_mode": "hybrid",
                "top_k": 20  # Request many results
            },
            name="Stress: Heavy query"
        )

