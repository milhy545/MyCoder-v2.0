"""
Stress Tests for Enhanced MyCoder v2.0

These tests push the system to its limits to verify robustness under:
- High concurrent load
- Memory pressure scenarios
- Thermal limit conditions (Q9550)
- Provider failure cascades
- Network timeout scenarios
- Resource exhaustion

Run with: pytest tests/stress/test_mycoder_stress.py -v -s --tb=short
"""

import asyncio
import pytest
import os
import tempfile
import time
import random
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import threading

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from enhanced_mycoder_v2 import EnhancedMyCoderV2
from api_providers import APIProviderType, APIProviderConfig, APIResponse
from config_manager import ConfigManager


class TestConcurrencyStress:
    """Test system behavior under high concurrent load"""
    
    @pytest.mark.asyncio
    async def test_high_concurrent_requests(self):
        """Test system with many concurrent requests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "ollama_local": {"enabled": True},
                "claude_oauth": {"enabled": True},
                "system": {"log_level": "WARNING"}  # Reduce log noise
            }
            
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                def mock_response(prompt, **kwargs):
                    # Simulate variable response times
                    delay = random.uniform(0.1, 0.8)
                    time.sleep(delay)
                    return APIResponse(
                        success=True,
                        content=f"Response to: {prompt[:30]}... ({delay:.2f}s)",
                        provider=random.choice([APIProviderType.OLLAMA_LOCAL, APIProviderType.CLAUDE_OAUTH]),
                        duration_ms=int(delay * 1000)
                    )
                
                mock_query.side_effect = mock_response
                
                # Create 50 concurrent requests
                num_requests = 50
                print(f"\n🚀 Launching {num_requests} concurrent requests...")
                
                start_time = time.time()
                
                tasks = []
                for i in range(num_requests):
                    task = mycoder.process_request(
                        f"Concurrent stress test request #{i} - simulate heavy workload",
                        session_id=f"stress_session_{i % 10}"  # 10 different sessions
                    )
                    tasks.append(task)
                
                # Wait for all requests to complete
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                total_time = time.time() - start_time
                
                print(f"✅ Completed {num_requests} requests in {total_time:.2f}s")
                print(f"📊 Average: {total_time/num_requests:.2f}s per request")
                
                # Verify results
                successful_responses = 0
                exceptions = 0
                
                for i, response in enumerate(responses):
                    if isinstance(response, Exception):
                        print(f"❌ Request {i} failed with exception: {response}")
                        exceptions += 1
                    else:
                        if response.get("success"):
                            successful_responses += 1
                
                success_rate = successful_responses / num_requests * 100
                print(f"📈 Success rate: {success_rate:.1f}%")
                print(f"🚨 Exceptions: {exceptions}")
                
                # Should handle most requests successfully
                assert success_rate >= 90.0  # At least 90% success rate
                assert exceptions < num_requests * 0.1  # Less than 10% exceptions
                
                # Verify session management under load
                assert len(mycoder.session_store) <= 10  # Should be 10 sessions max
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_overflow_stress(self):
        """Test session management under overflow conditions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}}
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Session overflow test response",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                # Create way more sessions than the limit (should be 100)
                num_sessions = 200
                print(f"\n💾 Creating {num_sessions} sessions to test overflow...")
                
                for i in range(num_sessions):
                    await mycoder.process_request(
                        f"Session overflow test {i}",
                        session_id=f"overflow_session_{i}"
                    )
                    
                    # Print progress every 50 sessions
                    if (i + 1) % 50 == 0:
                        print(f"   Created {i + 1}/{num_sessions} sessions, store size: {len(mycoder.session_store)}")
                
                # Should maintain reasonable session count through cleanup
                final_session_count = len(mycoder.session_store)
                print(f"📊 Final session count: {final_session_count}")
                
                # Should not exceed reasonable limits (100 is default max)
                assert final_session_count <= 100
                
                # Most recent sessions should still exist
                assert "overflow_session_199" in mycoder.session_store
                assert "overflow_session_190" in mycoder.session_store
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_provider_cascade_failure_stress(self):
        """Test behavior when providers fail in cascading fashion"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "claude_anthropic": {"enabled": True},
                "claude_oauth": {"enabled": True},
                "gemini": {"enabled": True},
                "ollama_local": {"enabled": True},
                "ollama_remote_urls": ["http://remote1:11434", "http://remote2:11434"]
            }
            
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            # Simulate cascading provider failures
            call_count = 0
            def mock_failing_query(prompt, **kwargs):
                nonlocal call_count
                call_count += 1
                
                # First 80% of calls fail across providers
                if call_count <= 80:
                    failure_reasons = [
                        "Rate limit exceeded",
                        "API key invalid", 
                        "Network timeout",
                        "Service unavailable",
                        "Authentication failed"
                    ]
                    
                    return APIResponse(
                        success=False,
                        content="",
                        provider=random.choice([
                            APIProviderType.CLAUDE_ANTHROPIC,
                            APIProviderType.CLAUDE_OAUTH,
                            APIProviderType.GEMINI,
                            APIProviderType.OLLAMA_LOCAL
                        ]),
                        error=random.choice(failure_reasons)
                    )
                else:
                    # Last 20% succeed with local Ollama
                    return APIResponse(
                        success=True,
                        content="Local fallback response",
                        provider=APIProviderType.OLLAMA_LOCAL
                    )
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.side_effect = mock_failing_query
                
                # Send 100 requests with high failure rate
                print(f"\n💥 Testing provider cascade failures...")
                
                successful = 0
                failed = 0
                
                for i in range(100):
                    response = await mycoder.process_request(f"Cascade test {i}")
                    
                    if response.get("success"):
                        successful += 1
                    else:
                        failed += 1
                    
                    if (i + 1) % 20 == 0:
                        print(f"   Processed {i + 1}/100 requests, Success: {successful}, Failed: {failed}")
                
                success_rate = successful / 100 * 100
                print(f"📊 Final success rate: {success_rate:.1f}%")
                
                # Should eventually succeed with fallback
                assert success_rate >= 15.0  # At least 15% should succeed
                
                # Should have made many attempts due to failures
                assert call_count > 100  # More calls than requests due to retries
            
            await mycoder.shutdown()


class TestMemoryStress:
    """Test system behavior under memory pressure"""
    
    @pytest.mark.asyncio
    async def test_large_file_processing_stress(self):
        """Test processing of large files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            working_dir = Path(temp_dir)
            
            # Create large test files
            large_files = []
            
            # Large Python file
            large_py = working_dir / "large_module.py"
            py_content = ""
            for i in range(1000):
                py_content += f"""
def function_{i}():
    \"\"\"Function {i} documentation.
    
    This function performs operation {i} with complex logic
    and demonstrates large file handling capabilities.
    \"\"\"
    data = {list(range(i, i+10))}
    result = sum(x * {i} for x in data)
    return result + {i * 100}

class Class_{i}:
    \"\"\"Class {i} for testing large file processing.\"\"\"
    
    def __init__(self):
        self.value = {i}
        self.data = {{'key_{j}': {j * i} for j in range(10)}}
    
    def method_{i}(self, param):
        return param * self.value + sum(self.data.values())
"""
            
            large_py.write_text(py_content)
            large_files.append(large_py)
            print(f"📄 Created large Python file: {large_py.stat().st_size:,} bytes")
            
            # Large JSON file
            large_json = working_dir / "large_data.json"
            json_data = "{\n"
            for i in range(5000):
                json_data += f'  "item_{i}": {{"id": {i}, "name": "Item {i}", "data": {list(range(i, i+5))}}},\n'
            json_data = json_data.rstrip(',\n') + "\n}"
            
            large_json.write_text(json_data)
            large_files.append(large_json)
            print(f"📄 Created large JSON file: {large_json.stat().st_size:,} bytes")
            
            # Large text file
            large_txt = working_dir / "large_document.txt"
            txt_content = ""
            for i in range(2000):
                txt_content += f"Paragraph {i}: This is a large text document created for stress testing the MyCoder v2.0 system. " \
                             f"It contains {i} paragraphs of repetitive content to simulate processing large documents. " \
                             f"The system should handle this efficiently without memory issues. Line {i} of many.\n"
            
            large_txt.write_text(txt_content)
            large_files.append(large_txt)
            print(f"📄 Created large text file: {large_txt.stat().st_size:,} bytes")
            
            total_size = sum(f.stat().st_size for f in large_files)
            print(f"📊 Total file size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
            
            config = {"ollama_local": {"enabled": True}}
            
            mycoder = EnhancedMyCoderV2(
                working_directory=working_dir,
                config=config
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Successfully processed large files",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                # Process all large files at once
                print(f"\n💾 Processing {len(large_files)} large files simultaneously...")
                
                start_time = time.time()
                
                response = await mycoder.process_request(
                    "Analyze these large files for patterns and provide a summary",
                    files=large_files,
                    session_id="large_file_stress_test"
                )
                
                processing_time = time.time() - start_time
                
                print(f"⏱️  Processing completed in {processing_time:.2f}s")
                print(f"📊 Processing rate: {total_size/processing_time:,.0f} bytes/second")
                
                # Should complete successfully
                assert response.get("success") is True
                
                # Should have processed files in reasonable time (< 30s for MB of data)
                assert processing_time < 30.0
                
                # Verify files were passed to provider
                call_args = mock_query.call_args
                context = call_args[1]["context"]
                assert "files" in context
                assert len(context["files"]) == 3
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self):
        """Test that system doesn't leak memory over many operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}}
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                def mock_variable_response(prompt, **kwargs):
                    # Create responses with varying content sizes
                    base_content = "Memory leak test response "
                    content_multiplier = random.randint(1, 100)
                    content = base_content * content_multiplier
                    
                    return APIResponse(
                        success=True,
                        content=content,
                        provider=APIProviderType.OLLAMA_LOCAL
                    )
                
                mock_query.side_effect = mock_variable_response
                
                # Perform many operations to test for memory leaks
                num_operations = 500
                print(f"\n🔄 Performing {num_operations} operations to test memory stability...")
                
                for i in range(num_operations):
                    # Vary session usage to test cleanup
                    session_id = f"leak_test_{i % 20}" if i % 5 == 0 else None
                    
                    response = await mycoder.process_request(
                        f"Memory leak test operation {i} with variable content",
                        session_id=session_id
                    )
                    
                    assert response.get("success") is True
                    
                    # Print progress
                    if (i + 1) % 100 == 0:
                        session_count = len(mycoder.session_store)
                        print(f"   Completed {i + 1}/{num_operations} operations, Sessions: {session_count}")
                
                # Verify system is still stable
                final_session_count = len(mycoder.session_store)
                print(f"📊 Final session count: {final_session_count}")
                
                # Should not accumulate excessive sessions
                assert final_session_count <= 20  # Based on our 20-session rotation
                
                # System should still respond
                final_response = await mycoder.process_request("Final memory test")
                assert final_response.get("success") is True
            
            await mycoder.shutdown()


@pytest.mark.skipif(
    not Path("/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh").exists(),
    reason="Q9550 thermal system not available"
)
class TestThermalStress:
    """Test thermal management under stress (Q9550 specific)"""
    
    @pytest.mark.asyncio
    async def test_thermal_limit_stress(self):
        """Test system behavior at thermal limits"""
        config = {
            "ollama_local": {"enabled": True},
            "thermal": {
                "enabled": True,
                "max_temp": 72,  # Lower limit for stress testing
                "critical_temp": 80,
                "check_interval": 5  # More frequent checks
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            # Simulate high thermal load
            thermal_test_count = 0
            def mock_thermal_stressed_query(prompt, **kwargs):
                nonlocal thermal_test_count
                thermal_test_count += 1
                
                # Simulate CPU heating up during processing
                base_temp = 65
                temp_increase = min(thermal_test_count * 0.5, 15)  # Heat up to 80°C
                simulated_temp = base_temp + temp_increase
                
                # Mock thermal status with increasing temperature
                with patch.object(mycoder, '_get_thermal_status') as mock_thermal:
                    mock_thermal.return_value = {
                        "cpu_temp": simulated_temp,
                        "status": "critical" if simulated_temp > 78 else "high" if simulated_temp > 75 else "normal",
                        "safe_operation": simulated_temp <= 75
                    }
                    
                    if simulated_temp > 78:
                        return APIResponse(
                            success=False,
                            content="",
                            provider=APIProviderType.OLLAMA_LOCAL,
                            error=f"Operation blocked due to thermal limits (CPU: {simulated_temp:.1f}°C)"
                        )
                    else:
                        return APIResponse(
                            success=True,
                            content=f"Thermal-aware response (CPU: {simulated_temp:.1f}°C)",
                            provider=APIProviderType.OLLAMA_LOCAL
                        )
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.side_effect = mock_thermal_stressed_query
                
                print(f"\n🌡️  Testing thermal stress scenarios...")
                
                successful = 0
                thermal_blocked = 0
                
                # Send requests until thermal limits are hit
                for i in range(20):
                    response = await mycoder.process_request(
                        f"Thermal stress test {i} - intensive AI processing simulation"
                    )
                    
                    if response.get("success"):
                        successful += 1
                        print(f"   ✅ Request {i}: Success - {response.get('content', '')[:50]}...")
                    else:
                        thermal_blocked += 1
                        print(f"   🔥 Request {i}: Blocked - {response.get('error', '')}")
                    
                    # Small delay to simulate processing time
                    await asyncio.sleep(0.1)
                
                print(f"📊 Thermal stress results:")
                print(f"   Successful operations: {successful}")
                print(f"   Thermally blocked: {thermal_blocked}")
                
                # Should have some successful operations before thermal limits
                assert successful > 0
                
                # Should eventually block due to thermal limits
                assert thermal_blocked > 0
                
                # Should have attempted thermal monitoring
                assert thermal_test_count > 0
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_thermal_recovery_stress(self):
        """Test thermal recovery after cooling down"""
        config = {
            "ollama_local": {"enabled": True},
            "thermal": {
                "enabled": True,
                "max_temp": 75,
                "critical_temp": 82
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            # Simulate thermal stress and recovery cycle
            operation_count = 0
            
            def mock_thermal_recovery_query(prompt, **kwargs):
                nonlocal operation_count
                operation_count += 1
                
                # Simulate heating and cooling cycle
                if operation_count <= 10:
                    # Heating phase
                    temp = 70 + operation_count * 1.5  # Heat to 85°C
                elif operation_count <= 15:
                    # Critical phase - blocked
                    temp = 85
                else:
                    # Cooling phase
                    cooling_ops = operation_count - 15
                    temp = max(65, 85 - cooling_ops * 3)  # Cool down
                
                with patch.object(mycoder, '_get_thermal_status') as mock_thermal:
                    mock_thermal.return_value = {
                        "cpu_temp": temp,
                        "status": "critical" if temp > 82 else "high" if temp > 75 else "normal",
                        "safe_operation": temp <= 75
                    }
                    
                    if temp > 82:
                        return APIResponse(
                            success=False,
                            content="",
                            provider=APIProviderType.OLLAMA_LOCAL,
                            error=f"Critical temperature reached: {temp:.1f}°C"
                        )
                    else:
                        return APIResponse(
                            success=True,
                            content=f"Operation at {temp:.1f}°C",
                            provider=APIProviderType.OLLAMA_LOCAL
                        )
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.side_effect = mock_thermal_recovery_query
                
                print(f"\n♻️  Testing thermal recovery cycle...")
                
                results = []
                
                for i in range(25):
                    response = await mycoder.process_request(f"Recovery test {i}")
                    results.append(response.get("success", False))
                    
                    status = "✅" if response.get("success") else "🔥"
                    content = response.get("content", response.get("error", ""))[:30]
                    print(f"   {status} Request {i:2d}: {content}...")
                    
                    await asyncio.sleep(0.05)  # Simulate time between operations
                
                # Analyze results
                heating_phase = results[:10]
                critical_phase = results[10:15]
                cooling_phase = results[15:]
                
                print(f"📊 Recovery analysis:")
                print(f"   Heating phase success rate: {sum(heating_phase)/len(heating_phase)*100:.1f}%")
                print(f"   Critical phase success rate: {sum(critical_phase)/len(critical_phase)*100:.1f}%")
                print(f"   Cooling phase success rate: {sum(cooling_phase)/len(cooling_phase)*100:.1f}%")
                
                # Should work during heating phase
                assert sum(heating_phase) > 5
                
                # Should be blocked during critical phase
                assert sum(critical_phase) < 3
                
                # Should recover during cooling phase
                assert sum(cooling_phase) > 5
            
            await mycoder.shutdown()


class TestNetworkStress:
    """Test system behavior under network stress conditions"""
    
    @pytest.mark.asyncio
    async def test_timeout_cascade_stress(self):
        """Test behavior with cascading timeout failures"""
        config = {
            "claude_anthropic": {"enabled": True, "timeout_seconds": 5},
            "claude_oauth": {"enabled": True, "timeout_seconds": 10},
            "gemini": {"enabled": True, "timeout_seconds": 8},
            "ollama_local": {"enabled": True, "timeout_seconds": 15}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            timeout_count = 0
            
            def mock_timeout_query(prompt, **kwargs):
                nonlocal timeout_count
                timeout_count += 1
                
                # Simulate different timeout scenarios
                if timeout_count <= 30:
                    # First 30 calls simulate various network issues
                    failure_types = [
                        ("Connection timeout", 0.1),
                        ("Read timeout", 0.2),
                        ("Network unreachable", 0.0),
                        ("DNS resolution failed", 0.0),
                        ("SSL handshake timeout", 0.3)
                    ]
                    
                    error_type, delay = random.choice(failure_types)
                    if delay > 0:
                        time.sleep(delay)
                    
                    return APIResponse(
                        success=False,
                        content="",
                        provider=random.choice([
                            APIProviderType.CLAUDE_ANTHROPIC,
                            APIProviderType.CLAUDE_OAUTH,
                            APIProviderType.GEMINI
                        ]),
                        error=error_type
                    )
                else:
                    # Local provider works
                    return APIResponse(
                        success=True,
                        content="Local fallback after network issues",
                        provider=APIProviderType.OLLAMA_LOCAL
                    )
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.side_effect = mock_timeout_query
                
                print(f"\n🌐 Testing network timeout cascade scenarios...")
                
                successful = 0
                failed = 0
                total_time = 0
                
                for i in range(40):
                    start_time = time.time()
                    
                    response = await mycoder.process_request(
                        f"Network stress test {i}"
                    )
                    
                    request_time = time.time() - start_time
                    total_time += request_time
                    
                    if response.get("success"):
                        successful += 1
                        print(f"   ✅ Request {i:2d}: Success ({request_time:.2f}s)")
                    else:
                        failed += 1
                        error = response.get("error", "Unknown error")[:40]
                        print(f"   ❌ Request {i:2d}: {error} ({request_time:.2f}s)")
                
                avg_time = total_time / 40
                success_rate = successful / 40 * 100
                
                print(f"📊 Network stress results:")
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Average request time: {avg_time:.2f}s")
                print(f"   Total timeout attempts: {timeout_count}")
                
                # Should eventually succeed with local fallback
                assert success_rate >= 20.0
                
                # Should have made many timeout attempts
                assert timeout_count >= 40
                
                # Average time should be reasonable (including timeout handling)
                assert avg_time < 3.0
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_intermittent_network_stress(self):
        """Test handling of intermittent network connectivity"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"claude_oauth": {"enabled": True}, "ollama_local": {"enabled": True}}
            )
            
            await mycoder.initialize()
            
            request_count = 0
            
            def mock_intermittent_query(prompt, **kwargs):
                nonlocal request_count
                request_count += 1
                
                # Simulate intermittent connectivity (30% failure rate)
                if random.random() < 0.3:
                    failure_reasons = [
                        "Network temporarily unavailable",
                        "Connection reset by peer",
                        "Request timeout",
                        "DNS resolution temporarily failed"
                    ]
                    
                    return APIResponse(
                        success=False,
                        content="",
                        provider=APIProviderType.CLAUDE_OAUTH,
                        error=random.choice(failure_reasons)
                    )
                else:
                    # Success with some delay
                    delay = random.uniform(0.1, 0.5)
                    time.sleep(delay)
                    
                    return APIResponse(
                        success=True,
                        content=f"Intermittent network response #{request_count}",
                        provider=random.choice([APIProviderType.CLAUDE_OAUTH, APIProviderType.OLLAMA_LOCAL]),
                        duration_ms=int(delay * 1000)
                    )
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.side_effect = mock_intermittent_query
                
                print(f"\n📡 Testing intermittent network scenarios...")
                
                successful = 0
                network_failures = 0
                
                # Test with 50 requests over intermittent network
                for i in range(50):
                    response = await mycoder.process_request(
                        f"Intermittent network test {i}"
                    )
                    
                    if response.get("success"):
                        successful += 1
                    else:
                        network_failures += 1
                        if "network" in response.get("error", "").lower():
                            print(f"   📡 Network issue at request {i}")
                
                success_rate = successful / 50 * 100
                print(f"📊 Intermittent network results:")
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Network failures: {network_failures}")
                
                # Should handle intermittent network reasonably well
                assert success_rate >= 60.0  # Should succeed most of the time
                assert network_failures < 25  # Less than half should fail
            
            await mycoder.shutdown()


class TestEdgeCaseStress:
    """Test various edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_malformed_input_stress(self):
        """Test system resilience to malformed inputs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}}
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Handled malformed input gracefully",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                # Test various malformed inputs
                malformed_inputs = [
                    "",  # Empty string
                    " ",  # Whitespace only
                    "\n\n\n",  # Newlines only
                    "a" * 100000,  # Extremely long string
                    "🚀" * 1000,  # Unicode stress
                    "SELECT * FROM users; DROP TABLE users;",  # SQL injection attempt
                    "<script>alert('xss')</script>",  # XSS attempt
                    "../../../etc/passwd",  # Path traversal attempt
                    None,  # None type (should be handled by validation)
                    {"malformed": "dict"},  # Wrong type
                    ["list", "instead", "of", "string"],  # Wrong type
                    "\x00\x01\x02\x03",  # Binary data
                    "Ω≈ç√∫˜µ≤≥÷",  # Special characters
                    "𝔘𝔫𝔦𝔠𝔬𝔡𝔢",  # Unicode mathematical symbols
                ]
                
                print(f"\n🔍 Testing {len(malformed_inputs)} malformed inputs...")
                
                handled_gracefully = 0
                exceptions = 0
                
                for i, malformed_input in enumerate(malformed_inputs):
                    try:
                        if isinstance(malformed_input, str) or malformed_input is None:
                            response = await mycoder.process_request(malformed_input)
                            
                            if response.get("success") is not None:  # Got some response
                                handled_gracefully += 1
                                print(f"   ✅ Input {i:2d}: Handled gracefully")
                            else:
                                print(f"   ⚠️  Input {i:2d}: Unexpected response format")
                        else:
                            # Should handle type errors gracefully
                            response = await mycoder.process_request(malformed_input)
                            print(f"   ⚠️  Input {i:2d}: Should have caught type error")
                    
                    except Exception as e:
                        exceptions += 1
                        print(f"   🚨 Input {i:2d}: Exception - {type(e).__name__}: {str(e)[:50]}...")
                
                print(f"📊 Malformed input results:")
                print(f"   Handled gracefully: {handled_gracefully}")
                print(f"   Exceptions raised: {exceptions}")
                
                # Should handle most malformed inputs gracefully
                assert handled_gracefully >= len([i for i in malformed_inputs if isinstance(i, str) or i is None]) * 0.8
                
                # Should have minimal unhandled exceptions
                assert exceptions <= 3
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_stress(self):
        """Test behavior when approaching resource limits"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many files to test file handle limits
            many_files = []
            for i in range(100):
                test_file = Path(temp_dir) / f"stress_file_{i:03d}.txt"
                test_file.write_text(f"Stress test file {i}\n" * 100)
                many_files.append(test_file)
            
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}}
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Processed under resource stress",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                print(f"\n💾 Testing resource exhaustion with {len(many_files)} files...")
                
                # Test with progressively more files
                batch_sizes = [10, 25, 50, 75, 100]
                
                for batch_size in batch_sizes:
                    try:
                        file_batch = many_files[:batch_size]
                        
                        start_time = time.time()
                        response = await mycoder.process_request(
                            f"Process {batch_size} files for resource stress test",
                            files=file_batch
                        )
                        processing_time = time.time() - start_time
                        
                        if response.get("success"):
                            print(f"   ✅ Batch {batch_size:3d}: Success ({processing_time:.2f}s)")
                        else:
                            print(f"   ❌ Batch {batch_size:3d}: Failed ({processing_time:.2f}s)")
                        
                        # Verify reasonable processing time
                        assert processing_time < 10.0  # Should complete within 10s
                        
                    except Exception as e:
                        print(f"   🚨 Batch {batch_size:3d}: Exception - {type(e).__name__}")
                        
                        # Should not crash on resource limits
                        assert batch_size >= 75  # Should handle at least 75 files
                
                print(f"✅ Resource exhaustion test completed")
            
            await mycoder.shutdown()


if __name__ == "__main__":
    """Run stress tests directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MyCoder v2.0 Stress Tests")
    parser.add_argument("--test-class", "-c", type=str,
                       help="Run specific test class")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Run quick stress tests only")
    parser.add_argument("--thermal", "-t", action="store_true",
                       help="Run thermal stress tests (Q9550 required)")
    
    args = parser.parse_args()
    
    if args.quick:
        print("🚀 Running quick stress tests...")
        pytest.main([__file__ + "::TestConcurrencyStress::test_high_concurrent_requests", "-v"])
        
    elif args.thermal:
        print("🌡️  Running thermal stress tests...")
        pytest.main([__file__ + "::TestThermalStress", "-v"])
        
    elif args.test_class:
        print(f"🧪 Running {args.test_class} stress tests...")
        pytest.main([__file__ + f"::{args.test_class}", "-v"])
        
    else:
        print("🔥 Running all stress tests...")
        print("Use --quick for fast tests or --thermal for Q9550 thermal tests")
        pytest.main([__file__, "-v", "-s", "--tb=short"])