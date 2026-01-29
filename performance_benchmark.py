#!/usr/bin/env python3
"""
Performance benchmark script
Measures key metrics for production readiness
"""

import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor
import sys

API_URL = "http://localhost:8000"


class PerformanceBenchmark:
    """Benchmark system performance"""
    
    def __init__(self):
        self.results = {}
    
    def test_health_endpoint(self, iterations=100):
        """Test health endpoint response time"""
        print("📊 Testing health endpoint...")
        
        times = []
        for i in range(iterations):
            start = time.time()
            try:
                response = requests.get(f"{API_URL}/health/status", timeout=5)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                
                if response.status_code != 200:
                    print(f"❌ Health check failed: {response.status_code}")
                    return
            except Exception as e:
                print(f"❌ Health check error: {e}")
                return
        
        self.results['health_endpoint'] = {
            'avg': statistics.mean(times),
            'median': statistics.median(times),
            'p95': statistics.quantiles(times, n=20)[18] if len(times) >= 20 else times[-1],
            'p99': statistics.quantiles(times, n=100)[98] if len(times) >= 100 else times[-1],
            'min': min(times),
            'max': max(times)
        }
        
        print(f"  Average: {self.results['health_endpoint']['avg']:.2f}ms")
        print(f"  95th percentile: {self.results['health_endpoint']['p95']:.2f}ms")
        
        # Pass criteria: < 100ms average
        if self.results['health_endpoint']['avg'] < 100:
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL (should be < 100ms)")
    
    def test_concurrent_requests(self, workers=10, requests_per_worker=10):
        """Test concurrent request handling"""
        print(f"\n📊 Testing concurrent requests ({workers} workers, {requests_per_worker} req each)...")
        
        def make_request():
            start = time.time()
            try:
                response = requests.get(f"{API_URL}/health/status", timeout=5)
                elapsed = (time.time() - start) * 1000
                return elapsed, response.status_code
            except Exception as e:
                return 0, 500
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(make_request) for _ in range(workers * requests_per_worker)]
            results = [f.result() for f in futures]
        
        total_time = time.time() - start_time
        times = [r[0] for r in results if r[0] > 0]
        errors = sum(1 for r in results if r[1] != 200)
        
        if times:
            self.results['concurrent'] = {
                'total_requests': len(results),
                'total_time': total_time,
                'requests_per_second': len(results) / total_time if total_time > 0 else 0,
                'avg_response_time': statistics.mean(times),
                'errors': errors
            }
            
            print(f"  Total requests: {self.results['concurrent']['total_requests']}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Throughput: {self.results['concurrent']['requests_per_second']:.2f} req/s")
            print(f"  Avg response: {self.results['concurrent']['avg_response_time']:.2f}ms")
            print(f"  Errors: {errors}")
            
            # Pass criteria: > 50 RPS, 0 errors
            if self.results['concurrent']['requests_per_second'] > 50 and errors == 0:
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL (should be > 50 RPS with 0 errors)")
        else:
            print(f"  ❌ All requests failed")
    
    def test_memory_baseline(self):
        """Check baseline memory usage"""
        print(f"\n📊 Testing memory usage...")
        
        try:
            import docker
            
            client = docker.from_env()
            containers = client.containers.list(filters={"name": "rag"})
            
            if not containers:
                # Try without filter
                containers = [c for c in client.containers.list() if 'rag' in c.name.lower() or 'backend' in c.name.lower()]
            
            for container in containers:
                stats = container.stats(stream=False)
                if 'memory_stats' in stats and 'usage' in stats['memory_stats']:
                    memory_usage = stats['memory_stats']['usage'] / (1024 * 1024)  # MB
                    memory_limit = stats['memory_stats'].get('limit', memory_usage * 2) / (1024 * 1024)
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                    
                    print(f"  {container.name}:")
                    print(f"    Memory: {memory_usage:.1f}MB / {memory_limit:.1f}MB ({memory_percent:.1f}%)")
                    
                    # Warn if > 80%
                    if memory_percent > 80:
                        print(f"    ⚠️  High memory usage!")
        
        except ImportError:
            print(f"  ⚠️  Install docker for memory testing: pip install docker")
        except Exception as e:
            print(f"  ⚠️  Could not check memory: {e}")
    
    def generate_report(self):
        """Generate performance report"""
        print(f"\n{'='*60}")
        print(f"PERFORMANCE BENCHMARK REPORT")
        print(f"{'='*60}\n")
        
        # Health endpoint
        if 'health_endpoint' in self.results:
            print("Health Endpoint:")
            print(f"  Average: {self.results['health_endpoint']['avg']:.2f}ms")
            print(f"  Median: {self.results['health_endpoint']['median']:.2f}ms")
            print(f"  95th percentile: {self.results['health_endpoint']['p95']:.2f}ms")
            print(f"  99th percentile: {self.results['health_endpoint']['p99']:.2f}ms")
            print()
        
        # Concurrent
        if 'concurrent' in self.results:
            print("Concurrent Requests:")
            print(f"  Throughput: {self.results['concurrent']['requests_per_second']:.2f} req/s")
            print(f"  Avg response: {self.results['concurrent']['avg_response_time']:.2f}ms")
            print(f"  Errors: {self.results['concurrent']['errors']}")
            print()
        
        # Overall verdict
        print("="*60)
        
        health_pass = self.results.get('health_endpoint', {}).get('avg', 1000) < 100
        concurrent_pass = self.results.get('concurrent', {}).get('requests_per_second', 0) > 50
        
        if health_pass and concurrent_pass:
            print("✅ PERFORMANCE: PASS")
            print("System ready for production load")
        else:
            print("❌ PERFORMANCE: FAIL")
            print("Optimization needed before production")
        
        print("="*60)
    
    def run(self):
        """Run all benchmarks"""
        print("🚀 Starting Performance Benchmark\n")
        
        # Check if backend is running
        try:
            requests.get(f"{API_URL}/health/status", timeout=2)
        except:
            print(f"❌ Backend not running at {API_URL}")
            print("Start with: docker-compose up -d")
            sys.exit(1)
        
        self.test_health_endpoint()
        self.test_concurrent_requests()
        self.test_memory_baseline()
        self.generate_report()


if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    benchmark.run()

