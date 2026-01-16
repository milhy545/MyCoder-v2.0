"""
System Limits and Edge Case Stress Tests for Enhanced MyCoder v2.1.0

These tests verify system behavior at operational boundaries:
- Configuration edge cases
- Provider switching limits
- Session management boundaries
- Tool registry stress scenarios
- Error recovery cascades
- System shutdown/restart stress

Run with: pytest tests/stress/test_system_limits.py -v -s --tb=short
"""

import asyncio
import json
import os
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mycoder import EnhancedMyCoderV2
from mycoder.api_providers import (
    APIProviderConfig,
    APIProviderStatus,
    APIProviderType,
    APIResponse,
)
from mycoder.config_manager import ConfigManager
from mycoder.tool_registry import ToolExecutionContext


class TestConfigurationLimits:
    """Test configuration edge cases and limits"""

    def test_malformed_configuration_stress(self):
        """Test handling of various malformed configurations"""
        malformed_configs = [
            # Missing required fields
            {"claude_anthropic": {}},
            # Invalid timeout values
            {"ollama_local": {"timeout_seconds": -1}},
            {"claude_oauth": {"timeout_seconds": 0}},
            {"gemini": {"timeout_seconds": 99999}},
            # Invalid URLs
            {"ollama_local": {"base_url": "not-a-url"}},
            {"ollama_remote_urls": ["invalid-url", "also-not-url"]},
            # Invalid thermal settings
            {"thermal": {"max_temp": -10}},
            {"thermal": {"max_temp": 150}},
            {"thermal": {"check_interval": 0}},
            # Circular dependencies
            {"preferred_provider": "nonexistent_provider"},
            # Type mismatches
            {"debug_mode": "yes"},  # Should be boolean
            {"ollama_remote_urls": "single_string"},  # Should be list
            # Extremely large values
            {"ollama_remote_urls": ["http://server:11434"] * 1000},
        ]

        print(f"\n🔧 Testing {len(malformed_configs)} malformed configurations...")

        handled_gracefully = 0

        for i, malformed_config in enumerate(malformed_configs):
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as f:
                    json.dump(malformed_config, f)
                    config_file = Path(f.name)

                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Should handle malformed config gracefully
                        mycoder = EnhancedMyCoderV2(
                            working_directory=Path(temp_dir), config=malformed_config
                        )

                        # If initialization succeeds, config was normalized
                        handled_gracefully += 1
                        print(f"   ✅ Config {i:2d}: Handled gracefully")

                except Exception as e:
                    # Should provide meaningful error messages
                    if "config" in str(e).lower() or "invalid" in str(e).lower():
                        handled_gracefully += 1
                        print(f"   ✅ Config {i:2d}: Proper validation error")
                    else:
                        print(
                            f"   ❌ Config {i:2d}: Unexpected error - {type(e).__name__}"
                        )

                finally:
                    config_file.unlink()

            except Exception as e:
                print(f"   🚨 Config {i:2d}: Test setup failed - {type(e).__name__}")

        print(f"📊 Configuration stress results:")
        print(f"   Handled gracefully: {handled_gracefully}/{len(malformed_configs)}")

        # Should handle most malformed configs gracefully
        assert handled_gracefully >= len(malformed_configs) * 0.8

    @pytest.mark.asyncio
    async def test_configuration_change_stress(self):
        """Test rapid configuration changes"""
        base_config = {"ollama_local": {"enabled": True}}

        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir), config=base_config
            )

            await mycoder.initialize()

            # Test rapid configuration updates
            print(f"\n⚙️  Testing rapid configuration changes...")

            config_changes = [
                {"thermal": {"enabled": True, "max_temp": 75}},
                {"thermal": {"enabled": True, "max_temp": 80}},
                {"thermal": {"enabled": False}},
                {"claude_oauth": {"enabled": True}},
                {"claude_oauth": {"enabled": False}},
                {"debug_mode": True},
                {"debug_mode": False},
            ]

            successful_changes = 0

            for i, config_change in enumerate(config_changes):
                try:
                    # Update configuration
                    new_config = {**mycoder.config, **config_change}
                    mycoder.config.update(config_change)

                    # Verify system still functions
                    with patch.object(mycoder.provider_router, "query") as mock_query:
                        mock_query.return_value = APIResponse(
                            success=True,
                            content=f"Config change {i} successful",
                            provider=APIProviderType.OLLAMA_LOCAL,
                        )

                        response = await mycoder.process_request(
                            f"Test after config change {i}"
                        )

                        if response.get("success"):
                            successful_changes += 1
                            print(
                                f"   ✅ Change {i}: {list(config_change.keys())[0]} updated successfully"
                            )
                        else:
                            print(
                                f"   ❌ Change {i}: System not responding after change"
                            )

                except Exception as e:
                    print(f"   🚨 Change {i}: Exception - {type(e).__name__}")

            print(
                f"📊 Configuration change results: {successful_changes}/{len(config_changes)}"
            )

            # Should handle most config changes
            assert successful_changes >= len(config_changes) * 0.8

            await mycoder.shutdown()


class TestProviderSwitchingLimits:
    """Test provider switching under extreme conditions"""

    @pytest.mark.asyncio
    async def test_rapid_provider_switching_stress(self):
        """Test rapid switching between providers"""
        config = {
            "claude_anthropic": {"enabled": True},
            "claude_oauth": {"enabled": True},
            "gemini": {"enabled": True},
            "ollama_local": {"enabled": True},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(working_directory=Path(temp_dir), config=config)

            await mycoder.initialize()

            providers = [
                APIProviderType.CLAUDE_ANTHROPIC,
                APIProviderType.CLAUDE_OAUTH,
                APIProviderType.GEMINI,
                APIProviderType.OLLAMA_LOCAL,
            ]

            switch_count = 0

            def mock_switching_query(prompt, **kwargs):
                nonlocal switch_count
                switch_count += 1

                # Switch provider every call
                current_provider = providers[switch_count % len(providers)]

                return APIResponse(
                    success=True,
                    content=f"Response from {current_provider.value} (switch #{switch_count})",
                    provider=current_provider,
                )

            with patch.object(mycoder.provider_router, "query") as mock_query:
                mock_query.side_effect = mock_switching_query

                print(f"\n🔄 Testing rapid provider switching...")

                successful_switches = 0
                session_id = "rapid_switch_session"

                # Perform 100 rapid requests with provider switches
                for i in range(100):
                    response = await mycoder.process_request(
                        f"Rapid switch test {i}",
                        session_id=session_id,
                        continue_session=i > 0,
                    )

                    if response.get("success"):
                        successful_switches += 1
                        if i % 20 == 0:
                            print(
                                f"   ✅ Switch {i:3d}: {response.get('content', '')[:40]}..."
                            )
                    else:
                        print(f"   ❌ Switch {i:3d}: Failed")

                print(f"📊 Rapid switching results:")
                print(f"   Successful switches: {successful_switches}/100")
                print(f"   Total provider calls: {switch_count}")

                # Should handle rapid switching well
                assert successful_switches >= 90
                assert switch_count >= 100

                # Session should track all switches
                assert session_id in mycoder.session_store
                session_data = mycoder.session_store[session_id]
                assert session_data["total_interactions"] == 100

            await mycoder.shutdown()

    @pytest.mark.asyncio
    async def test_provider_health_oscillation_stress(self):
        """Test handling of rapidly changing provider health states"""
        config = {"claude_oauth": {"enabled": True}, "ollama_local": {"enabled": True}}

        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(working_directory=Path(temp_dir), config=config)

            await mycoder.initialize()

            health_check_count = 0

            def mock_oscillating_query(prompt, **kwargs):
                nonlocal health_check_count
                health_check_count += 1

                # Simulate providers oscillating between healthy/unhealthy
                if health_check_count % 3 == 0:
                    # Primary provider fails
                    return APIResponse(
                        success=False,
                        content="",
                        provider=APIProviderType.CLAUDE_OAUTH,
                        error="Provider temporarily unavailable",
                    )
                elif health_check_count % 3 == 1:
                    # Fallback to local
                    return APIResponse(
                        success=True,
                        content="Fallback provider response",
                        provider=APIProviderType.OLLAMA_LOCAL,
                    )
                else:
                    # Primary provider recovers
                    return APIResponse(
                        success=True,
                        content="Primary provider recovered",
                        provider=APIProviderType.CLAUDE_OAUTH,
                    )

            with patch.object(mycoder.provider_router, "query") as mock_query:
                mock_query.side_effect = mock_oscillating_query

                print(f"\n💓 Testing provider health oscillation...")

                successful = 0
                provider_switches = {"claude_oauth": 0, "ollama_local": 0}

                for i in range(60):  # Test over 60 requests
                    response = await mycoder.process_request(f"Oscillation test {i}")

                    if response.get("success"):
                        successful += 1
                        provider = response.get("provider", "unknown")
                        if provider in provider_switches:
                            provider_switches[provider] += 1

                    if i % 15 == 0:
                        print(
                            f"   Status at {i:2d}: Success rate {successful/(i+1)*100:.1f}%"
                        )

                print(f"📊 Health oscillation results:")
                print(f"   Success rate: {successful/60*100:.1f}%")
                print(f"   Provider usage: {provider_switches}")
                print(f"   Total health checks: {health_check_count}")

                # Should maintain high success rate despite oscillations
                assert successful >= 45  # At least 75% success

                # Should use both providers
                assert provider_switches["claude_oauth"] > 0
                assert provider_switches["ollama_local"] > 0

            await mycoder.shutdown()


class TestSessionManagementLimits:
    """Test session management edge cases"""

    @pytest.mark.asyncio
    async def test_session_explosion_stress(self):
        """Test handling of session explosion scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}},
            )

            await mycoder.initialize()

            with patch.object(mycoder.provider_router, "query") as mock_query:
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Session explosion test response",
                    provider=APIProviderType.OLLAMA_LOCAL,
                )

                print(f"\n💥 Testing session explosion scenarios...")

                # Create sessions rapidly with unique IDs
                explosion_tasks = []

                for i in range(500):  # Create 500 concurrent sessions
                    task = mycoder.process_request(
                        f"Explosion test {i}", session_id=f"explosion_session_{i}"
                    )
                    explosion_tasks.append(task)

                # Execute all tasks concurrently
                start_time = time.time()
                responses = await asyncio.gather(
                    *explosion_tasks, return_exceptions=True
                )
                execution_time = time.time() - start_time

                # Analyze results
                successful = sum(
                    1
                    for r in responses
                    if not isinstance(r, Exception) and r.get("success")
                )
                exceptions = sum(1 for r in responses if isinstance(r, Exception))

                print(f"📊 Session explosion results:")
                print(f"   Execution time: {execution_time:.2f}s")
                print(f"   Successful requests: {successful}/500")
                print(f"   Exceptions: {exceptions}")
                print(f"   Final session count: {len(mycoder.session_store)}")

                # Should handle explosion gracefully
                assert successful >= 450  # At least 90% success
                assert exceptions <= 25  # Less than 5% exceptions
                assert len(mycoder.session_store) <= 100  # Should cleanup to limit
                assert execution_time < 30  # Should complete within 30s

            await mycoder.shutdown()

    @pytest.mark.asyncio
    async def test_session_corruption_recovery(self):
        """Test recovery from session corruption scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}},
            )

            await mycoder.initialize()

            # Create normal sessions first
            with patch.object(mycoder.provider_router, "query") as mock_query:
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Normal session response",
                    provider=APIProviderType.OLLAMA_LOCAL,
                )

                # Create some normal sessions
                for i in range(10):
                    await mycoder.process_request(
                        f"Normal session {i}", session_id=f"normal_{i}"
                    )

                print(f"\n🔧 Testing session corruption recovery...")
                print(f"   Created {len(mycoder.session_store)} normal sessions")

                # Corrupt some sessions manually
                corruption_scenarios = [
                    (
                        "missing_keys",
                        lambda s: {k: v for k, v in s.items() if k != "last_context"},
                    ),
                    ("invalid_data", lambda s: {**s, "last_context": "not_a_dict"}),
                    ("circular_ref", lambda s: {**s, "circular": s}),
                    (
                        "invalid_timestamp",
                        lambda s: {**s, "updated_at": "not_a_number"},
                    ),
                    ("none_values", lambda s: {**s, "total_interactions": None}),
                ]

                # Apply corruptions
                session_ids = list(mycoder.session_store.keys())
                for i, (corruption_name, corruption_func) in enumerate(
                    corruption_scenarios
                ):
                    if i < len(session_ids):
                        session_id = session_ids[i]
                        try:
                            original_session = mycoder.session_store[session_id]
                            corrupted_session = corruption_func(original_session)
                            mycoder.session_store[session_id] = corrupted_session
                            print(
                                f"   Applied {corruption_name} to session {session_id}"
                            )
                        except Exception as e:
                            print(f"   Failed to apply {corruption_name}: {e}")

                # Test system behavior with corrupted sessions
                recovery_successful = 0

                for i, session_id in enumerate(session_ids[:5]):
                    try:
                        response = await mycoder.process_request(
                            f"Recovery test {i}",
                            session_id=session_id,
                            continue_session=True,
                        )

                        if response.get("success"):
                            recovery_successful += 1
                            print(f"   ✅ Recovered from corruption in {session_id}")
                        else:
                            print(f"   ⚠️  Failed recovery for {session_id}")

                    except Exception as e:
                        print(
                            f"   🚨 Exception during recovery for {session_id}: {type(e).__name__}"
                        )

                # Test creation of new sessions after corruption
                new_session_response = await mycoder.process_request(
                    "New session after corruption", session_id="post_corruption_session"
                )

                print(f"📊 Session corruption recovery results:")
                print(f"   Recovered sessions: {recovery_successful}/5")
                print(
                    f"   New session creation: {'✅' if new_session_response.get('success') else '❌'}"
                )
                print(f"   Final session count: {len(mycoder.session_store)}")

                # Should recover from most corruptions
                assert recovery_successful >= 3
                assert new_session_response.get("success") is True

            await mycoder.shutdown()


class TestToolRegistryLimits:
    """Test tool registry under stress conditions"""

    @pytest.mark.asyncio
    async def test_tool_execution_overload(self):
        """Test tool registry under heavy concurrent load"""
        with tempfile.TemporaryDirectory() as temp_dir:
            working_dir = Path(temp_dir)

            # Create many test files for tool operations
            test_files = []
            for i in range(200):
                test_file = working_dir / f"tool_test_{i:03d}.txt"
                test_file.write_text(f"Tool test content {i}\n" * 50)
                test_files.append(test_file)

            mycoder = EnhancedMyCoderV2(
                working_directory=working_dir,
                config={
                    "ollama_local": {"enabled": True},
                    "system": {"enable_tool_registry": True},
                },
            )

            await mycoder.initialize()

            print(
                f"\n🛠️  Testing tool execution overload with {len(test_files)} files..."
            )

            # Create concurrent tool execution tasks
            async def tool_operation(file_path, operation_id):
                context = ToolExecutionContext(
                    mode="FULL",
                    working_directory=working_dir,
                    session_id=f"tool_stress_session_{operation_id % 10}",
                )

                try:
                    # Read operation
                    result = await mycoder.tool_registry.execute_tool(
                        "file_read", context, operation="read", path=file_path.name
                    )
                    return result.success
                except Exception as e:
                    return False

            # Execute many concurrent tool operations
            start_time = time.time()

            tool_tasks = []
            for i, test_file in enumerate(
                test_files[:100]
            ):  # Limit to 100 for stress test
                task = tool_operation(test_file, i)
                tool_tasks.append(task)

            results = await asyncio.gather(*tool_tasks, return_exceptions=True)

            execution_time = time.time() - start_time

            # Analyze results
            successful_ops = sum(1 for r in results if r is True)
            failed_ops = sum(1 for r in results if r is False)
            exceptions = sum(1 for r in results if isinstance(r, Exception))

            print(f"📊 Tool execution overload results:")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Successful operations: {successful_ops}/100")
            print(f"   Failed operations: {failed_ops}")
            print(f"   Exceptions: {exceptions}")
            print(f"   Operations per second: {100/execution_time:.1f}")

            # Should handle tool overload reasonably
            assert successful_ops >= 80  # At least 80% success
            assert exceptions <= 10  # Less than 10% exceptions
            assert execution_time < 20  # Should complete within 20s

            # Get tool registry statistics
            registry_stats = mycoder.tool_registry.get_registry_stats()
            print(f"   Total tool executions: {registry_stats['total_executions']}")

            await mycoder.shutdown()

    @pytest.mark.asyncio
    async def test_tool_registry_resource_limits(self):
        """Test tool registry behavior at resource limits"""
        with tempfile.TemporaryDirectory() as temp_dir:
            working_dir = Path(temp_dir)

            mycoder = EnhancedMyCoderV2(
                working_directory=working_dir,
                config={"ollama_local": {"enabled": True}},
            )

            await mycoder.initialize()

            print(f"\n🔧 Testing tool registry resource limits...")

            # Test extremely large file operations
            huge_content = "x" * (10 * 1024 * 1024)  # 10MB of data
            huge_file = working_dir / "huge_file.txt"

            try:
                huge_file.write_text(huge_content)
                print(f"   Created huge file: {huge_file.stat().st_size:,} bytes")

                context = ToolExecutionContext(
                    mode="FULL",
                    working_directory=working_dir,
                    session_id="resource_limit_session",
                )

                # Test reading huge file
                start_time = time.time()
                result = await mycoder.tool_registry.execute_tool(
                    "file_read", context, operation="read", path="huge_file.txt"
                )
                read_time = time.time() - start_time

                print(
                    f"   Huge file read: {'✅' if result.success else '❌'} ({read_time:.2f}s)"
                )

                # Should handle large files gracefully
                if result.success:
                    assert read_time < 5.0  # Should read within 5 seconds

                # Test writing huge file
                start_time = time.time()
                write_result = await mycoder.tool_registry.execute_tool(
                    "file_write",
                    context,
                    operation="write",
                    path="huge_file_copy.txt",
                    content=huge_content[: 1024 * 1024],  # Limit to 1MB for write test
                )
                write_time = time.time() - start_time

                print(
                    f"   Huge file write: {'✅' if write_result.success else '❌'} ({write_time:.2f}s)"
                )

                if write_result.success:
                    assert write_time < 3.0  # Should write within 3 seconds

            except Exception as e:
                print(f"   🚨 Huge file test exception: {type(e).__name__}")
                # Should not crash the system
                assert False, f"Tool registry crashed on large file: {e}"

            # Test many small operations
            small_ops_successful = 0
            for i in range(1000):
                try:
                    result = await mycoder.tool_registry.execute_tool(
                        "file_list", context, operation="list", path="."
                    )
                    if result.success:
                        small_ops_successful += 1
                except Exception:
                    break

            print(f"   Small operations completed: {small_ops_successful}/1000")
            assert small_ops_successful >= 900  # Should handle most small operations

            await mycoder.shutdown()


class TestSystemRestartStress:
    """Test system restart and recovery scenarios"""

    @pytest.mark.asyncio
    async def test_rapid_initialization_shutdown_cycle(self):
        """Test rapid system initialization and shutdown cycles"""
        print(f"\n🔄 Testing rapid initialization/shutdown cycles...")

        cycle_count = 20
        successful_cycles = 0
        total_time = 0

        for cycle in range(cycle_count):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    start_time = time.time()

                    # Initialize
                    mycoder = EnhancedMyCoderV2(
                        working_directory=Path(temp_dir),
                        config={"ollama_local": {"enabled": True}},
                    )

                    await mycoder.initialize()

                    # Quick operation
                    with patch.object(mycoder.provider_router, "query") as mock_query:
                        mock_query.return_value = APIResponse(
                            success=True,
                            content=f"Cycle {cycle} response",
                            provider=APIProviderType.OLLAMA_LOCAL,
                        )

                        response = await mycoder.process_request(f"Cycle {cycle} test")

                        if response.get("success"):
                            # Shutdown
                            await mycoder.shutdown()

                            cycle_time = time.time() - start_time
                            total_time += cycle_time
                            successful_cycles += 1

                            if cycle % 5 == 0:
                                print(
                                    f"   ✅ Cycle {cycle:2d}: Success ({cycle_time:.2f}s)"
                                )
                        else:
                            print(f"   ❌ Cycle {cycle:2d}: Operation failed")

            except Exception as e:
                print(f"   🚨 Cycle {cycle:2d}: Exception - {type(e).__name__}")

        avg_cycle_time = total_time / max(successful_cycles, 1)
        success_rate = successful_cycles / cycle_count * 100

        print(f"📊 Rapid cycle results:")
        print(
            f"   Successful cycles: {successful_cycles}/{cycle_count} ({success_rate:.1f}%)"
        )
        print(f"   Average cycle time: {avg_cycle_time:.2f}s")

        # Should handle rapid cycles reliably
        assert success_rate >= 90.0
        assert avg_cycle_time < 2.0

    @pytest.mark.asyncio
    async def test_system_recovery_after_corruption(self):
        """Test system recovery after internal state corruption"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}},
            )

            await mycoder.initialize()

            print(f"\n🩹 Testing system recovery after corruption...")

            # Create initial state
            with patch.object(mycoder.provider_router, "query") as mock_query:
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Initial state response",
                    provider=APIProviderType.OLLAMA_LOCAL,
                )

                # Create some sessions
                for i in range(5):
                    await mycoder.process_request(
                        f"Initial session {i}", session_id=f"initial_{i}"
                    )

                initial_session_count = len(mycoder.session_store)
                print(f"   Initial state: {initial_session_count} sessions")

                # Simulate various corruptions
                corruptions = [
                    ("session_store", lambda: setattr(mycoder, "session_store", None)),
                    (
                        "provider_router",
                        lambda: setattr(mycoder, "provider_router", None),
                    ),
                    ("tool_registry", lambda: setattr(mycoder, "tool_registry", None)),
                    ("config", lambda: setattr(mycoder, "config", {})),
                ]

                recovery_results = {}

                for corruption_name, corruption_func in corruptions:
                    print(f"\n   Testing recovery from {corruption_name} corruption...")

                    try:
                        # Apply corruption
                        original_value = getattr(
                            mycoder,
                            (
                                corruption_name.split("_")[0]
                                if "_" in corruption_name
                                else corruption_name
                            ),
                        )
                        corruption_func()

                        # Attempt recovery through reinitialization
                        try:
                            # For some corruptions, we need to reinitialize
                            if corruption_name in ["provider_router", "tool_registry"]:
                                await mycoder.initialize()
                            elif corruption_name == "session_store":
                                mycoder.session_store = {}
                            elif corruption_name == "config":
                                mycoder.config = {"ollama_local": {"enabled": True}}

                            # Test if system still works
                            response = await mycoder.process_request(
                                f"Recovery test for {corruption_name}",
                                session_id=f"recovery_{corruption_name}",
                            )

                            if response.get("success"):
                                recovery_results[corruption_name] = "recovered"
                                print(f"   ✅ Recovered from {corruption_name}")
                            else:
                                recovery_results[corruption_name] = "failed"
                                print(f"   ❌ Failed to recover from {corruption_name}")

                        except Exception as recovery_error:
                            recovery_results[corruption_name] = "exception"
                            print(
                                f"   🚨 Recovery exception for {corruption_name}: {type(recovery_error).__name__}"
                            )

                        # Restore original value for next test
                        setattr(
                            mycoder,
                            (
                                corruption_name.split("_")[0]
                                if "_" in corruption_name
                                else corruption_name
                            ),
                            original_value,
                        )

                    except Exception as setup_error:
                        recovery_results[corruption_name] = "setup_failed"
                        print(
                            f"   🔧 Setup failed for {corruption_name}: {type(setup_error).__name__}"
                        )

                print(f"\n📊 Recovery test results:")
                recovered_count = sum(
                    1 for result in recovery_results.values() if result == "recovered"
                )

                for corruption, result in recovery_results.items():
                    status_emoji = {
                        "recovered": "✅",
                        "failed": "❌",
                        "exception": "🚨",
                        "setup_failed": "🔧",
                    }[result]
                    print(f"   {status_emoji} {corruption}: {result}")

                print(
                    f"   Recovery success rate: {recovered_count}/{len(corruptions)} ({recovered_count/len(corruptions)*100:.1f}%)"
                )

                # Should recover from most corruptions
                assert (
                    recovered_count >= len(corruptions) * 0.6
                )  # At least 60% recovery rate

            await mycoder.shutdown()


if __name__ == "__main__":
    """Run system limit tests directly"""
    import argparse

    parser = argparse.ArgumentParser(description="MyCoder v2.1.0 System Limits Tests")
    parser.add_argument("--test-class", "-c", type=str, help="Run specific test class")
    parser.add_argument(
        "--config", action="store_true", help="Run configuration limit tests"
    )
    parser.add_argument(
        "--session", action="store_true", help="Run session management limit tests"
    )
    parser.add_argument(
        "--tools", action="store_true", help="Run tool registry limit tests"
    )

    args = parser.parse_args()

    if args.config:
        print("⚙️  Running configuration limit tests...")
        pytest.main([__file__ + "::TestConfigurationLimits", "-v"])

    elif args.session:
        print("💾 Running session limit tests...")
        pytest.main([__file__ + "::TestSessionManagementLimits", "-v"])

    elif args.tools:
        print("🛠️  Running tool registry limit tests...")
        pytest.main([__file__ + "::TestToolRegistryLimits", "-v"])

    elif args.test_class:
        print(f"🧪 Running {args.test_class} tests...")
        pytest.main([__file__ + f"::{args.test_class}", "-v"])

    else:
        print("🔥 Running all system limit tests...")
        pytest.main([__file__, "-v", "-s", "--tb=short"])
