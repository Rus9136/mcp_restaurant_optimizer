#!/usr/bin/env python3
"""
Production SSE Testing Script for MCP Restaurant Optimizer
Tests the SSE endpoint on production domain https://mcp.madlen.space
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List
import argparse
import sys

import httpx
import urllib3
from loguru import logger

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SSEProductionTester:
    """
    Comprehensive SSE testing for production environment
    """
    
    def __init__(self, base_url: str = "https://mcp.madlen.space", verify_ssl: bool = True):
        self.base_url = base_url
        self.verify_ssl = verify_ssl
        self.sse_url = f"{base_url}/api/v1/mcp/sse"
        self.status_url = f"{base_url}/api/v1/mcp/sse/status"
        self.health_url = f"{base_url}/health"
        self.test_results = []
        
    async def run_comprehensive_tests(self):
        """
        Запускает полный набор тестов SSE endpoint
        """
        logger.info("🧪 Starting comprehensive SSE production tests")
        logger.info(f"Testing endpoint: {self.sse_url}")
        print("=" * 60)
        
        # Test 1: Basic connectivity
        await self._test_basic_connectivity()
        
        # Test 2: SSL/TLS verification
        await self._test_ssl_security()
        
        # Test 3: SSE status endpoint
        await self._test_status_endpoint()
        
        # Test 4: SSE stream connection
        await self._test_sse_stream()
        
        # Test 5: Multiple concurrent connections
        await self._test_concurrent_connections()
        
        # Test 6: Error handling
        await self._test_error_handling()
        
        # Test 7: Performance metrics
        await self._test_performance()
        
        # Test 8: CORS headers
        await self._test_cors_headers()
        
        # Generate test report
        self._generate_test_report()
        
    async def _test_basic_connectivity(self):
        """Test 1: Basic connectivity to the domain"""
        logger.info("🔌 Test 1: Basic connectivity")
        
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=30.0) as client:
                # Test health endpoint
                response = await client.get(self.health_url)
                
                if response.status_code == 200:
                    self._add_result("✅ Basic connectivity", True, f"Health endpoint responded: {response.status_code}")
                else:
                    self._add_result("❌ Basic connectivity", False, f"Health endpoint failed: {response.status_code}")
                    
        except Exception as e:
            self._add_result("❌ Basic connectivity", False, f"Connection failed: {str(e)}")
            
    async def _test_ssl_security(self):
        """Test 2: SSL/TLS security verification"""
        logger.info("🔒 Test 2: SSL/TLS security")
        
        try:
            # Test with SSL verification enabled
            async with httpx.AsyncClient(verify=True, timeout=30.0) as client:
                response = await client.get(self.health_url)
                
                if response.status_code == 200:
                    self._add_result("✅ SSL/TLS security", True, "SSL certificate is valid")
                else:
                    self._add_result("⚠️ SSL/TLS security", False, f"SSL issue: {response.status_code}")
                    
        except httpx.SSLError as e:
            self._add_result("❌ SSL/TLS security", False, f"SSL certificate error: {str(e)}")
        except Exception as e:
            self._add_result("❌ SSL/TLS security", False, f"SSL test failed: {str(e)}")
            
    async def _test_status_endpoint(self):
        """Test 3: SSE status endpoint"""
        logger.info("📊 Test 3: SSE status endpoint")
        
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=30.0) as client:
                response = await client.get(self.status_url)
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ["status", "active_connections", "service", "version"]
                    
                    missing_fields = [field for field in expected_fields if field not in data]
                    
                    if not missing_fields:
                        self._add_result(
                            "✅ SSE status endpoint", 
                            True, 
                            f"All fields present. Active connections: {data.get('active_connections', 0)}"
                        )
                    else:
                        self._add_result(
                            "⚠️ SSE status endpoint", 
                            False, 
                            f"Missing fields: {missing_fields}"
                        )
                else:
                    self._add_result("❌ SSE status endpoint", False, f"Status: {response.status_code}")
                    
        except Exception as e:
            self._add_result("❌ SSE status endpoint", False, f"Request failed: {str(e)}")
            
    async def _test_sse_stream(self):
        """Test 4: SSE stream connection and data"""
        logger.info("🌊 Test 4: SSE stream connection")
        
        try:
            headers = {"Accept": "text/event-stream"}
            timeout = httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=30.0)
            
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=timeout) as client:
                events_received = []
                connection_established = False
                
                async with client.stream("GET", self.sse_url, headers=headers) as response:
                    if response.status_code == 200:
                        connection_established = True
                        
                        # Check content type
                        content_type = response.headers.get("content-type", "")
                        if "text/event-stream" not in content_type:
                            self._add_result(
                                "⚠️ SSE stream - content type", 
                                False, 
                                f"Wrong content type: {content_type}"
                            )
                        
                        # Read events for 30 seconds
                        start_time = time.time()
                        async for line in response.aiter_lines():
                            if time.time() - start_time > 30:  # 30 second timeout
                                break
                                
                            if line.startswith("data: "):
                                try:
                                    event_data = json.loads(line[6:])  # Remove "data: " prefix
                                    events_received.append(event_data)
                                    
                                    # Log first few events
                                    if len(events_received) <= 3:
                                        logger.info(f"📨 Received event: {event_data.get('type', 'unknown')}")
                                    
                                except json.JSONDecodeError:
                                    logger.warning(f"Invalid JSON in SSE event: {line}")
                                    
                                # Stop after receiving 5 events
                                if len(events_received) >= 5:
                                    break
                    
                    if connection_established and events_received:
                        event_types = {event.get("type") for event in events_received}
                        self._add_result(
                            "✅ SSE stream connection", 
                            True, 
                            f"Received {len(events_received)} events. Types: {event_types}"
                        )
                        
                        # Test event structure
                        await self._validate_event_structure(events_received)
                        
                    elif connection_established:
                        self._add_result("⚠️ SSE stream connection", False, "Connected but no events received")
                    else:
                        self._add_result("❌ SSE stream connection", False, f"Failed to connect: {response.status_code}")
                    
        except Exception as e:
            self._add_result("❌ SSE stream connection", False, f"Stream test failed: {str(e)}")
            
    async def _validate_event_structure(self, events: List[Dict]):
        """Validate the structure of received SSE events"""
        logger.info("🔍 Validating event structure")
        
        required_fields = ["type", "timestamp", "department_id"]
        valid_types = {"sales", "bookings", "occupancy", "shifts", "connection", "error"}
        
        structure_issues = []
        
        for i, event in enumerate(events):
            # Check required fields
            missing_fields = [field for field in required_fields if field not in event]
            if missing_fields:
                structure_issues.append(f"Event {i}: missing fields {missing_fields}")
                
            # Check event type
            event_type = event.get("type")
            if event_type not in valid_types:
                structure_issues.append(f"Event {i}: invalid type '{event_type}'")
                
            # Check data field exists for non-connection events
            if event_type not in {"connection", "error"} and "data" not in event:
                structure_issues.append(f"Event {i}: missing 'data' field")
                
        if not structure_issues:
            self._add_result("✅ Event structure validation", True, "All events have valid structure")
        else:
            self._add_result("⚠️ Event structure validation", False, f"Issues: {structure_issues[:3]}")
            
    async def _test_concurrent_connections(self):
        """Test 5: Multiple concurrent SSE connections"""
        logger.info("🔄 Test 5: Concurrent connections")
        
        async def create_connection(client_id: int):
            try:
                headers = {"Accept": "text/event-stream"}
                timeout = httpx.Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0)
                
                async with httpx.AsyncClient(verify=self.verify_ssl, timeout=timeout) as client:
                    async with client.stream("GET", self.sse_url, headers=headers) as response:
                        if response.status_code == 200:
                            # Read a few events
                            event_count = 0
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    event_count += 1
                                    if event_count >= 2:  # Read 2 events per connection
                                        break
                            return True
                        else:
                            return False
            except Exception:
                return False
                
        # Test 3 concurrent connections
        try:
            tasks = [create_connection(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_connections = sum(1 for result in results if result is True)
            
            if successful_connections >= 2:
                self._add_result(
                    "✅ Concurrent connections", 
                    True, 
                    f"{successful_connections}/3 connections successful"
                )
            else:
                self._add_result(
                    "⚠️ Concurrent connections", 
                    False, 
                    f"Only {successful_connections}/3 connections successful"
                )
                
        except Exception as e:
            self._add_result("❌ Concurrent connections", False, f"Test failed: {str(e)}")
            
    async def _test_error_handling(self):
        """Test 6: Error handling for invalid requests"""
        logger.info("🚨 Test 6: Error handling")
        
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=30.0) as client:
                # Test invalid department_id
                invalid_url = f"{self.sse_url}?department_id=invalid-uuid"
                response = await client.get(invalid_url, headers={"Accept": "text/event-stream"})
                
                if response.status_code in [400, 422]:  # Expected validation error
                    self._add_result("✅ Error handling", True, f"Invalid UUID rejected: {response.status_code}")
                else:
                    self._add_result("⚠️ Error handling", False, f"Invalid UUID not rejected: {response.status_code}")
                    
        except Exception as e:
            self._add_result("❌ Error handling", False, f"Error test failed: {str(e)}")
            
    async def _test_performance(self):
        """Test 7: Performance metrics"""
        logger.info("⚡ Test 7: Performance metrics")
        
        try:
            response_times = []
            
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=30.0) as client:
                for _ in range(3):
                    start_time = time.time()
                    response = await client.get(self.status_url)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_times.append(end_time - start_time)
                    
                    await asyncio.sleep(1)  # Wait between requests
                    
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                
                if avg_time < 1.0:  # Less than 1 second average
                    self._add_result(
                        "✅ Performance", 
                        True, 
                        f"Avg response: {avg_time:.3f}s, Max: {max_time:.3f}s"
                    )
                else:
                    self._add_result(
                        "⚠️ Performance", 
                        False, 
                        f"Slow response - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s"
                    )
            else:
                self._add_result("❌ Performance", False, "No successful responses for timing")
                
        except Exception as e:
            self._add_result("❌ Performance", False, f"Performance test failed: {str(e)}")
            
    async def _test_cors_headers(self):
        """Test 8: CORS headers for SSE endpoint"""
        logger.info("🌐 Test 8: CORS headers")
        
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=30.0) as client:
                # Test OPTIONS request
                response = await client.options(self.sse_url)
                
                cors_headers = {
                    "Access-Control-Allow-Origin": response.headers.get("access-control-allow-origin"),
                    "Access-Control-Allow-Methods": response.headers.get("access-control-allow-methods"),
                    "Access-Control-Allow-Headers": response.headers.get("access-control-allow-headers"),
                }
                
                missing_headers = [key for key, value in cors_headers.items() if not value]
                
                if not missing_headers:
                    self._add_result("✅ CORS headers", True, f"All CORS headers present")
                else:
                    self._add_result("⚠️ CORS headers", False, f"Missing CORS headers: {missing_headers}")
                    
        except Exception as e:
            self._add_result("❌ CORS headers", False, f"CORS test failed: {str(e)}")
            
    def _add_result(self, test_name: str, success: bool, details: str):
        """Add test result to results list"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        # Print result immediately
        status_icon = "✅" if success else "❌" if not success else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"📊 Test Summary:")
        print(f"   Total tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success rate: {(successful_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        print("🎯 Production Readiness Assessment:")
        if successful_tests >= total_tests * 0.8:  # 80% success rate
            print("   ✅ READY FOR PRODUCTION")
            print("   The SSE endpoint is functioning properly and ready for production use.")
        else:
            print("   ❌ NOT READY FOR PRODUCTION")
            print("   Critical issues detected. Please resolve failed tests before deployment.")
        
        print()
        print("🔗 Test Endpoint: " + self.sse_url)
        print("⏰ Test completed: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


async def main():
    """Main function to run tests"""
    parser = argparse.ArgumentParser(description="Test MCP Restaurant Optimizer SSE in production")
    parser.add_argument("--url", default="https://mcp.madlen.space", help="Base URL to test")
    parser.add_argument("--no-ssl-verify", action="store_true", help="Disable SSL verification")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stdout, level="INFO")
    
    # Create tester instance
    tester = SSEProductionTester(
        base_url=args.url,
        verify_ssl=not args.no_ssl_verify
    )
    
    # Run tests
    try:
        await tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())