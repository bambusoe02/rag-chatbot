"""
Predefined load test scenarios

Usage:
    locust -f tests/load/locustfile.py --users 100 --spawn-rate 10 --run-time 10m
"""

SCENARIOS = {
    "smoke": {
        "description": "Smoke test - minimal load",
        "users": 5,
        "spawn_rate": 1,
        "run_time": "2m",
        "expected_rps": 10,
        "expected_avg_response": 500  # ms
    },
    
    "load": {
        "description": "Load test - normal traffic",
        "users": 50,
        "spawn_rate": 5,
        "run_time": "10m",
        "expected_rps": 100,
        "expected_avg_response": 1000
    },
    
    "stress": {
        "description": "Stress test - high load",
        "users": 200,
        "spawn_rate": 20,
        "run_time": "15m",
        "expected_rps": 400,
        "expected_avg_response": 2000
    },
    
    "spike": {
        "description": "Spike test - sudden traffic increase",
        "users": 500,
        "spawn_rate": 100,  # Spawn 100 users per second
        "run_time": "5m",
        "expected_rps": 1000,
        "expected_avg_response": 3000
    },
    
    "endurance": {
        "description": "Endurance test - sustained load",
        "users": 100,
        "spawn_rate": 10,
        "run_time": "4h",
        "expected_rps": 200,
        "expected_avg_response": 1500
    },
    
    "capacity": {
        "description": "Capacity test - find max throughput",
        "users": 1000,
        "spawn_rate": 50,
        "run_time": "30m",
        "expected_rps": 2000,
        "expected_avg_response": 5000
    }
}


def print_scenarios():
    """Print all available scenarios"""
    print("\n📊 Available Load Test Scenarios:\n")
    
    for name, config in SCENARIOS.items():
        print(f"🎯 {name.upper()}")
        print(f"   {config['description']}")
        print(f"   Users: {config['users']}")
        print(f"   Duration: {config['run_time']}")
        print(f"   Expected RPS: {config['expected_rps']}")
        print(f"   Expected Avg Response: {config['expected_avg_response']}ms")
        print()


if __name__ == "__main__":
    print_scenarios()

