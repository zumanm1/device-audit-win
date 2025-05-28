#!/usr/bin/env python3
"""
Performance and Load Testing for NetAuditPro
Tests application performance under various load conditions
"""

import asyncio
import aiohttp
import time
import statistics
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

class NetAuditProPerformanceTester:
    def __init__(self, base_url: str = "http://127.0.0.1:5011"):
        self.base_url = base_url
        self.results = []
        self.issues_found = []
        
    async def single_request_test(self, session: aiohttp.ClientSession, endpoint: str) -> Dict[str, Any]:
        """Test a single request and measure performance"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                content = await response.text()
                end_time = time.time()
                
                return {
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "content_length": len(content),
                    "success": response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "response_time": end_time - start_time,
                "content_length": 0,
                "success": False,
                "error": str(e)
            }
    
    async def concurrent_load_test(self, endpoint: str, concurrent_requests: int = 10, total_requests: int = 100):
        """Test endpoint with concurrent requests"""
        print(f"🧪 Load Testing {endpoint} ({concurrent_requests} concurrent, {total_requests} total)...")
        
        connector = aiohttp.TCPConnector(limit=concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for _ in range(total_requests):
                task = self.single_request_test(session, endpoint)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_requests = [r for r in results if isinstance(r, dict) and r.get("success", False)]
            failed_requests = [r for r in results if not isinstance(r, dict) or not r.get("success", False)]
            
            if successful_requests:
                response_times = [r["response_time"] for r in successful_requests]
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else response_times[0]
                
                print(f"   📊 Results for {endpoint}:")
                print(f"      • Total Requests: {total_requests}")
                print(f"      • Successful: {len(successful_requests)} ✅")
                print(f"      • Failed: {len(failed_requests)} ❌")
                print(f"      • Success Rate: {(len(successful_requests)/total_requests)*100:.1f}%")
                print(f"      • Avg Response Time: {avg_response_time:.3f}s")
                print(f"      • Min Response Time: {min_response_time:.3f}s")
                print(f"      • Max Response Time: {max_response_time:.3f}s")
                print(f"      • 95th Percentile: {p95_response_time:.3f}s")
                
                # Check for performance issues
                if avg_response_time > 2.0:
                    self.issues_found.append(f"{endpoint}: Average response time too high ({avg_response_time:.3f}s)")
                
                if len(failed_requests) > total_requests * 0.05:  # More than 5% failure rate
                    self.issues_found.append(f"{endpoint}: High failure rate ({len(failed_requests)}/{total_requests})")
                
                return {
                    "endpoint": endpoint,
                    "total_requests": total_requests,
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "success_rate": (len(successful_requests)/total_requests)*100,
                    "avg_response_time": avg_response_time,
                    "min_response_time": min_response_time,
                    "max_response_time": max_response_time,
                    "p95_response_time": p95_response_time
                }
            else:
                self.issues_found.append(f"{endpoint}: All requests failed")
                return {
                    "endpoint": endpoint,
                    "total_requests": total_requests,
                    "successful_requests": 0,
                    "failed_requests": total_requests,
                    "success_rate": 0
                }
    
    async def memory_stress_test(self):
        """Test application under memory stress"""
        print("🧪 Memory Stress Test...")
        
        # Test with large number of concurrent API calls
        endpoints = ["/api/progress", "/api/live-logs", "/api/raw-logs", "/api/timing"]
        
        connector = aiohttp.TCPConnector(limit=50)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            # Create 200 concurrent requests across different endpoints
            for i in range(200):
                endpoint = endpoints[i % len(endpoints)]
                task = self.single_request_test(session, endpoint)
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful = len([r for r in results if isinstance(r, dict) and r.get("success", False)])
            total_time = end_time - start_time
            
            print(f"   📊 Memory Stress Test Results:")
            print(f"      • Total Requests: 200")
            print(f"      • Successful: {successful}")
            print(f"      • Total Time: {total_time:.2f}s")
            print(f"      • Requests/Second: {200/total_time:.2f}")
            
            if successful < 180:  # Less than 90% success rate
                self.issues_found.append(f"Memory stress test: Low success rate ({successful}/200)")
            
            return {
                "test": "memory_stress",
                "total_requests": 200,
                "successful": successful,
                "total_time": total_time,
                "requests_per_second": 200/total_time
            }
    
    async def api_response_validation_test(self):
        """Test API responses for correct structure and data"""
        print("🧪 API Response Validation Test...")
        
        api_tests = [
            {
                "endpoint": "/api/progress",
                "required_fields": ["completed_devices", "current_device", "status", "status_counts"],
                "expected_types": {"completed_devices": int, "status": str}
            },
            {
                "endpoint": "/api/timing",
                "required_fields": ["success", "timing", "formatted"],
                "expected_types": {"success": bool, "timing": dict, "formatted": dict}
            },
            {
                "endpoint": "/api/live-logs",
                "required_fields": ["logs"],
                "expected_types": {"logs": list}
            }
        ]
        
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for test in api_tests:
                endpoint = test["endpoint"]
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                
                                # Check required fields
                                missing_fields = []
                                for field in test["required_fields"]:
                                    if field not in data:
                                        missing_fields.append(field)
                                
                                if missing_fields:
                                    self.issues_found.append(f"{endpoint}: Missing fields {missing_fields}")
                                
                                # Check data types
                                for field, expected_type in test.get("expected_types", {}).items():
                                    if field in data and not isinstance(data[field], expected_type):
                                        self.issues_found.append(f"{endpoint}: Field {field} has wrong type")
                                
                                print(f"   ✅ {endpoint}: Structure validation passed")
                                
                            except json.JSONDecodeError:
                                self.issues_found.append(f"{endpoint}: Invalid JSON response")
                        else:
                            self.issues_found.append(f"{endpoint}: HTTP {response.status}")
                            
                except Exception as e:
                    self.issues_found.append(f"{endpoint}: Request failed - {str(e)}")
    
    async def run_performance_tests(self):
        """Run all performance tests"""
        print("⚡ Starting Performance and Load Testing...")
        print("=" * 60)
        
        # Test critical endpoints
        endpoints_to_test = [
            "/",
            "/api/progress",
            "/api/live-logs",
            "/api/raw-logs",
            "/api/timing",
            "/settings",
            "/inventory"
        ]
        
        test_results = []
        
        # Light load test (5 concurrent, 25 total)
        print("\n🔥 Light Load Testing...")
        for endpoint in endpoints_to_test[:4]:  # Test main endpoints
            result = await self.concurrent_load_test(endpoint, concurrent_requests=5, total_requests=25)
            test_results.append(result)
        
        # Medium load test (10 concurrent, 50 total)
        print("\n🔥 Medium Load Testing...")
        for endpoint in ["/", "/api/progress"]:  # Test most critical endpoints
            result = await self.concurrent_load_test(endpoint, concurrent_requests=10, total_requests=50)
            test_results.append(result)
        
        # Heavy load test (20 concurrent, 100 total) - only on main page
        print("\n🔥 Heavy Load Testing...")
        result = await self.concurrent_load_test("/", concurrent_requests=20, total_requests=100)
        test_results.append(result)
        
        # Memory stress test
        print("\n🧠 Memory Stress Testing...")
        memory_result = await self.memory_stress_test()
        
        # API validation test
        print("\n🔍 API Response Validation...")
        await self.api_response_validation_test()
        
        # Generate summary
        self.generate_performance_summary(test_results, memory_result)
        
        return len(self.issues_found) == 0
    
    def generate_performance_summary(self, test_results: List[Dict], memory_result: Dict):
        """Generate performance test summary"""
        print("\n" + "=" * 60)
        print("⚡ PERFORMANCE TESTING SUMMARY")
        print("=" * 60)
        
        # Calculate overall statistics
        total_requests = sum(r.get("total_requests", 0) for r in test_results)
        total_successful = sum(r.get("successful_requests", 0) for r in test_results)
        
        if test_results:
            avg_response_times = [r.get("avg_response_time", 0) for r in test_results if "avg_response_time" in r]
            overall_avg_response = statistics.mean(avg_response_times) if avg_response_times else 0
            
            print(f"📊 Overall Performance:")
            print(f"   • Total Requests Tested: {total_requests}")
            print(f"   • Successful Requests: {total_successful}")
            print(f"   • Overall Success Rate: {(total_successful/total_requests)*100:.1f}%")
            print(f"   • Average Response Time: {overall_avg_response:.3f}s")
        
        print(f"\n🧠 Memory Stress Test:")
        print(f"   • Requests/Second: {memory_result.get('requests_per_second', 0):.2f}")
        print(f"   • Success Rate: {(memory_result.get('successful', 0)/200)*100:.1f}%")
        
        # Performance grades
        if overall_avg_response < 0.5:
            performance_grade = "A+ (Excellent)"
        elif overall_avg_response < 1.0:
            performance_grade = "A (Very Good)"
        elif overall_avg_response < 2.0:
            performance_grade = "B (Good)"
        elif overall_avg_response < 3.0:
            performance_grade = "C (Acceptable)"
        else:
            performance_grade = "D (Needs Improvement)"
        
        print(f"\n🏆 Performance Grade: {performance_grade}")
        
        if self.issues_found:
            print(f"\n⚠️ Performance Issues Found ({len(self.issues_found)}):")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"   {i}. {issue}")
        else:
            print("\n🎉 No performance issues found!")
        
        # Save detailed results
        with open("performance_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_requests": total_requests,
                    "successful_requests": total_successful,
                    "overall_avg_response_time": overall_avg_response,
                    "performance_grade": performance_grade
                },
                "test_results": test_results,
                "memory_result": memory_result,
                "issues_found": self.issues_found
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: performance_test_results.json")

async def main():
    """Main test execution"""
    tester = NetAuditProPerformanceTester()
    success = await tester.run_performance_tests()
    
    if success:
        print("\n🎉 All performance tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Found {len(tester.issues_found)} performance issues")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 