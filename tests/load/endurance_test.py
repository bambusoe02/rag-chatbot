from locust import HttpUser, task, between
import random


class EnduranceTestUser(HttpUser):
    """
    Endurance/Soak test: Sustained load over long period
    Tests for memory leaks, resource exhaustion
    Run for 4-8 hours
    """
    
    wait_time = between(3, 8)
    
    def on_start(self):
        response = self.client.post("/api/auth/login", data={
            "username": f"endurance_user_{random.randint(1, 100)}",
            "password": "test_password"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def regular_query(self):
        """Regular queries"""
        self.client.post(
            "/api/chat",
            json={"question": "What is ML?", "search_mode": "hybrid"},
            headers=getattr(self, 'headers', {}),
            name="Endurance: Query"
        )
    
    @task(3)
    def check_health(self):
        """Health checks"""
        self.client.get("/health/status", name="Endurance: Health")
    
    @task(2)
    def view_analytics(self):
        """Analytics"""
        self.client.get(
            "/api/analytics/performance?days=1",
            headers=getattr(self, 'headers', {}),
            name="Endurance: Analytics"
        )

