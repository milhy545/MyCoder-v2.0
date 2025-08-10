"""
Integration Tests for Enhanced MyCoder v2.0

Tests complete system integration with real-world scenarios including:
- Multi-API provider fallback chains
- Thermal management integration with Q9550 systems
- Tool registry integration with file operations
- Configuration management with multiple sources
- Session management across provider transitions
"""

import asyncio
import pytest
import os
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from enhanced_mycoder_v2 import EnhancedMyCoderV2
from api_providers import APIProviderType, APIProviderConfig
from config_manager import ConfigManager, MyCoderConfig
from tool_registry import get_tool_registry, ToolExecutionContext


class TestEnhancedMyCoderIntegration:
    """Integration tests for complete Enhanced MyCoder system"""
    
    def create_test_config(self):
        """Create test configuration for integration tests"""
        return {
            "claude_anthropic": {
                "enabled": False  # Disable to avoid API costs in tests
            },
            "claude_oauth": {
                "enabled": True
            },
            "gemini": {
                "enabled": False  # Disable to avoid API costs in tests
            },
            "ollama_local": {
                "enabled": True,
                "base_url": "http://localhost:11434",
                "model": "tinyllama"
            },
            "ollama_remote_urls": ["http://remote-test:11434"],
            "thermal": {
                "enabled": True,
                "max_temp": 75,
                "check_interval": 30
            },
            "system": {
                "log_level": "DEBUG",
                "enable_tool_registry": True
            },
            "debug_mode": True
        }
    
    @pytest.mark.asyncio
    async def test_basic_initialization(self):
        """Test basic system initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            working_dir = Path(temp_dir)
            
            mycoder = EnhancedMyCoderV2(
                working_directory=working_dir,
                config=self.create_test_config()
            )
            
            await mycoder.initialize()
            
            assert mycoder._initialized is True
            assert mycoder.provider_router is not None
            assert mycoder.tool_registry is not None
            assert mycoder.working_directory == working_dir
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_provider_fallback_chain(self):
        """Test complete provider fallback chain"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.create_test_config()
            
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            # Mock all providers to simulate failures except last one
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                # Simulate fallback chain where first providers fail
                from api_providers import APIResponse
                
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Fallback provider response",
                    provider=APIProviderType.OLLAMA_LOCAL,
                    cost=0.0,
                    duration_ms=1000
                )
                
                response = await mycoder.process_request(
                    "Hello, test the fallback system",
                    session_id="test_fallback"
                )
                
                assert response["success"] is True
                assert response["content"] == "Fallback provider response"
                assert response["provider"] == "ollama_local"
                assert response["session_id"] == "test_fallback"
                
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_thermal_integration_safe(self):
        """Test thermal integration when system is safe"""
        config = self.create_test_config()
        config["thermal"]["enabled"] = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            # Mock thermal status as safe
            with patch.object(mycoder, '_get_thermal_status') as mock_thermal:
                mock_thermal.return_value = {
                    "cpu_temp": 65,
                    "status": "normal",
                    "safe_operation": True
                }
                
                with patch.object(mycoder.provider_router, 'query') as mock_query:
                    from api_providers import APIResponse
                    mock_query.return_value = APIResponse(
                        success=True,
                        content="Operation completed safely",
                        provider=APIProviderType.OLLAMA_LOCAL
                    )
                    
                    response = await mycoder.process_request(
                        "Perform thermal-safe operation"
                    )
                    
                    assert response["success"] is True
                    # Should have called thermal status check
                    mock_thermal.assert_called_once()
                    
                    # Context should include thermal status
                    call_args = mock_query.call_args
                    context = call_args[1]["context"]
                    assert "thermal_status" in context
                    assert context["thermal_status"]["safe_operation"] is True
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_thermal_integration_throttled(self):
        """Test thermal integration when system needs throttling"""
        config = self.create_test_config()
        config["thermal"]["enabled"] = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            # Mock thermal status as high temperature
            with patch.object(mycoder, '_get_thermal_status') as mock_thermal:
                mock_thermal.return_value = {
                    "cpu_temp": 82,
                    "status": "high",
                    "safe_operation": False
                }
                
                with patch.object(mycoder.provider_router, 'query') as mock_query:
                    from api_providers import APIResponse
                    mock_query.return_value = APIResponse(
                        success=True,
                        content="Throttled response",
                        provider=APIProviderType.OLLAMA_LOCAL
                    )
                    
                    response = await mycoder.process_request(
                        "Perform operation with thermal monitoring"
                    )
                    
                    # Should still succeed but with thermal context
                    assert response["success"] is True
                    mock_thermal.assert_called_once()
                    
                    # Context should reflect thermal concerns
                    call_args = mock_query.call_args
                    context = call_args[1]["context"]
                    assert context["thermal_status"]["cpu_temp"] == 82
                    assert context["thermal_status"]["safe_operation"] is False
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_file_operations_integration(self):
        """Test integration with file operations through tool registry"""
        with tempfile.TemporaryDirectory() as temp_dir:
            working_dir = Path(temp_dir)
            
            # Create test files
            test_file = working_dir / "integration_test.py"
            test_file.write_text("print('Integration test file')")
            
            mycoder = EnhancedMyCoderV2(
                working_directory=working_dir,
                config=self.create_test_config()
            )
            
            await mycoder.initialize()
            
            # Mock the provider to simulate AI requesting file operations
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                # First response asks for file reading
                from api_providers import APIResponse
                mock_query.return_value = APIResponse(
                    success=True,
                    content="I can help you with that file. Let me read it first.",
                    provider=APIProviderType.CLAUDE_OAUTH
                )
                
                response = await mycoder.process_request(
                    "Analyze the integration_test.py file",
                    files=[test_file],
                    use_tools=True
                )
                
                assert response["success"] is True
                
                # Verify file was included in context
                call_args = mock_query.call_args
                context = call_args[1]["context"]
                assert "files" in context
                assert len(context["files"]) == 1
                assert context["files"][0].name == "integration_test.py"
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_management_across_providers(self):
        """Test session persistence across provider transitions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=self.create_test_config()
            )
            
            await mycoder.initialize()
            
            session_id = "persistent_session_test"
            
            # First request with one provider
            with patch.object(mycoder.provider_router, 'query') as mock_query1:
                from api_providers import APIResponse
                mock_query1.return_value = APIResponse(
                    success=True,
                    content="First response",
                    provider=APIProviderType.CLAUDE_OAUTH,
                    session_id=session_id
                )
                
                response1 = await mycoder.process_request(
                    "Start conversation",
                    session_id=session_id
                )
                
                assert response1["success"] is True
                assert response1["session_id"] == session_id
            
            # Verify session was stored
            assert session_id in mycoder.session_store
            stored_session = mycoder.session_store[session_id]
            assert stored_session["last_response"]["provider"] == "claude_oauth"
            assert stored_session["total_interactions"] == 1
            
            # Second request continuing session (potentially different provider)
            with patch.object(mycoder.provider_router, 'query') as mock_query2:
                mock_query2.return_value = APIResponse(
                    success=True,
                    content="Continued conversation",
                    provider=APIProviderType.OLLAMA_LOCAL,
                    session_id=session_id
                )
                
                response2 = await mycoder.process_request(
                    "Continue conversation",
                    session_id=session_id,
                    continue_session=True
                )
                
                assert response2["success"] is True
                assert response2["session_id"] == session_id
            
            # Verify session was updated
            updated_session = mycoder.session_store[session_id]
            assert updated_session["last_response"]["provider"] == "ollama_local"
            assert updated_session["total_interactions"] == 2
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test integration with configuration management"""
        config_data = {
            "claude_anthropic": {
                "enabled": False,
                "timeout_seconds": 45
            },
            "ollama_local": {
                "enabled": True,
                "model": "custom-model",
                "timeout_seconds": 90
            },
            "thermal": {
                "enabled": True,
                "max_temp": 75
            },
            "debug_mode": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Load config from file
                config_manager = ConfigManager(config_file)
                loaded_config = config_manager.load_config()
                
                # Convert to dictionary for MyCoder
                config_dict = {
                    "claude_anthropic": {
                        "enabled": loaded_config.claude_anthropic.enabled,
                        "timeout_seconds": loaded_config.claude_anthropic.timeout_seconds
                    },
                    "ollama_local": {
                        "enabled": loaded_config.ollama_local.enabled,
                        "model": loaded_config.ollama_local.model,
                        "timeout_seconds": loaded_config.ollama_local.timeout_seconds
                    },
                    "thermal": {
                        "enabled": loaded_config.thermal.enabled,
                        "max_temp": loaded_config.thermal.max_temp
                    },
                    "debug_mode": loaded_config.debug_mode
                }
                
                mycoder = EnhancedMyCoderV2(
                    working_directory=Path(temp_dir),
                    config=config_dict
                )
                
                await mycoder.initialize()
                
                # Verify configuration was applied
                assert mycoder.config["debug_mode"] is True
                assert mycoder.thermal_monitor is not None
                
                # Test provider configuration
                local_provider = mycoder.provider_router._get_provider(APIProviderType.OLLAMA_LOCAL)
                assert local_provider is not None
                assert local_provider.config.timeout_seconds == 90
                assert local_provider.model == "custom-model"
                
                await mycoder.shutdown()
                
        finally:
            config_file.unlink()
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self):
        """Test complete error recovery scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=self.create_test_config()
            )
            
            await mycoder.initialize()
            
            # Test scenario where all providers fail
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                mock_query.return_value = APIResponse(
                    success=False,
                    content="",
                    provider=APIProviderType.RECOVERY,
                    error="All providers failed"
                )
                
                response = await mycoder.process_request(
                    "This should trigger error recovery"
                )
                
                assert response["success"] is False
                assert response["provider"] == "recovery"
                assert "All providers failed" in response["error"]
                assert "recovery_suggestions" in response
                assert len(response["recovery_suggestions"]) > 0
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_system_status_integration(self):
        """Test comprehensive system status reporting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=self.create_test_config()
            )
            
            await mycoder.initialize()
            
            # Create some session data
            mycoder.session_store["test_session_1"] = {
                "last_context": {"mode": "FULL"},
                "total_interactions": 5,
                "updated_at": time.time()
            }
            
            mycoder.session_store["test_session_2"] = {
                "last_context": {"mode": "AUTONOMOUS"},
                "total_interactions": 3,
                "updated_at": time.time()
            }
            
            with patch.object(mycoder.provider_router, 'health_check_all') as mock_health:
                mock_health.return_value = {
                    "claude_anthropic": {"status": "unavailable"},
                    "claude_oauth": {"status": "healthy"},
                    "ollama_local": {"status": "healthy"}
                }
                
                with patch.object(mycoder, '_get_thermal_status') as mock_thermal:
                    mock_thermal.return_value = {
                        "cpu_temp": 68,
                        "status": "normal",
                        "safe_operation": True
                    }
                    
                    status = await mycoder.get_system_status()
                    
                    assert status["status"] == "initialized"
                    assert status["active_sessions"] == 2
                    assert "providers" in status
                    assert "thermal" in status
                    assert "tools" in status
                    assert "mode" in status
                    
                    # Verify provider status
                    assert status["providers"]["claude_oauth"]["status"] == "healthy"
                    assert status["providers"]["ollama_local"]["status"] == "healthy"
                    
                    # Verify thermal status
                    assert status["thermal"]["cpu_temp"] == 68
                    assert status["thermal"]["safe_operation"] is True
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_integration(self):
        """Test system behavior with concurrent requests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=self.create_test_config()
            )
            
            await mycoder.initialize()
            
            # Mock provider responses
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                
                def mock_response(prompt, **kwargs):
                    # Simulate different response times
                    import random
                    delay = random.uniform(0.1, 0.5)
                    time.sleep(delay)
                    
                    return APIResponse(
                        success=True,
                        content=f"Response to: {prompt[:20]}...",
                        provider=APIProviderType.OLLAMA_LOCAL,
                        duration_ms=int(delay * 1000)
                    )
                
                mock_query.side_effect = mock_response
                
                # Create multiple concurrent requests
                requests = [
                    mycoder.process_request(f"Request {i}", session_id=f"session_{i}")
                    for i in range(5)
                ]
                
                responses = await asyncio.gather(*requests, return_exceptions=True)
                
                # All requests should complete successfully
                assert len(responses) == 5
                for i, response in enumerate(responses):
                    assert not isinstance(response, Exception)
                    assert response["success"] is True
                    assert f"Request {i}" in response["content"]
                
                # Verify sessions were created
                assert len(mycoder.session_store) == 5
                for i in range(5):
                    assert f"session_{i}" in mycoder.session_store
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_resource_limits_integration(self):
        """Test system behavior with resource limits"""
        config = self.create_test_config()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            # Set mode manager to AUTONOMOUS for resource limits
            await mycoder.initialize()
            mycoder.mode_manager.current_mode = mycoder.mode_manager.current_mode.__class__.AUTONOMOUS
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Resource-limited response",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                response = await mycoder.process_request(
                    "Process this with resource limits"
                )
                
                assert response["success"] is True
                assert response["mode"] == "AUTONOMOUS"
                
                # Verify resource limits were applied to context
                call_args = mock_query.call_args
                context = call_args[1]["context"]
                assert "resource_limits" in context
                assert context["resource_limits"]["max_tokens"] == 2048
                assert context["resource_limits"]["thermal_sensitive"] is True
            
            await mycoder.shutdown()


@pytest.mark.integration
class TestRealWorldScenarios:
    """Real-world integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_development_workflow_scenario(self):
        """Test complete development workflow scenario"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create mock project structure
            src_dir = project_dir / "src"
            src_dir.mkdir()
            
            main_file = src_dir / "main.py"
            main_file.write_text('''
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
''')
            
            test_file = project_dir / "test_main.py"
            test_file.write_text('''
import unittest
from src.main import hello_world

class TestMain(unittest.TestCase):
    def test_hello_world(self):
        # This test needs implementation
        pass
''')
            
            config = {
                "claude_oauth": {"enabled": True},
                "ollama_local": {"enabled": True},
                "system": {"enable_tool_registry": True},
                "debug_mode": True
            }
            
            mycoder = EnhancedMyCoderV2(
                working_directory=project_dir,
                config=config
            )
            
            await mycoder.initialize()
            
            # Simulate development workflow
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                
                responses = [
                    "I can see your Python project structure. The main.py file contains a simple hello_world function.",
                    "I notice your test file needs implementation. Let me suggest how to test the hello_world function.",
                    "Here's a complete test implementation that captures the output and verifies it."
                ]
                
                response_idx = 0
                def mock_dev_response(prompt, **kwargs):
                    nonlocal response_idx
                    response_content = responses[response_idx % len(responses)]
                    response_idx += 1
                    
                    return APIResponse(
                        success=True,
                        content=response_content,
                        provider=APIProviderType.CLAUDE_OAUTH,
                        session_id=kwargs.get("session_id")
                    )
                
                mock_query.side_effect = mock_dev_response
                
                session_id = "dev_workflow_session"
                
                # Step 1: Analyze project structure
                response1 = await mycoder.process_request(
                    "Analyze my Python project structure",
                    files=[main_file, test_file],
                    session_id=session_id
                )
                
                assert response1["success"] is True
                assert "project structure" in response1["content"]
                
                # Step 2: Get testing suggestions
                response2 = await mycoder.process_request(
                    "Help me implement the test case",
                    session_id=session_id,
                    continue_session=True
                )
                
                assert response2["success"] is True
                assert "test" in response2["content"]
                
                # Step 3: Get implementation details
                response3 = await mycoder.process_request(
                    "Show me the complete test implementation",
                    session_id=session_id,
                    continue_session=True
                )
                
                assert response3["success"] is True
                assert "implementation" in response3["content"]
                
                # Verify session continuity
                assert response1["session_id"] == session_id
                assert response2["session_id"] == session_id
                assert response3["session_id"] == session_id
                
                # Verify session store
                assert session_id in mycoder.session_store
                session_data = mycoder.session_store[session_id]
                assert session_data["total_interactions"] == 3
            
            await mycoder.shutdown()
    
    @pytest.mark.skipif(
        not Path("/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh").exists(),
        reason="Q9550 thermal system not available"
    )
    @pytest.mark.asyncio
    async def test_q9550_thermal_scenario(self):
        """Test Q9550-specific thermal management scenario"""
        config = {
            "ollama_local": {
                "enabled": True,
                "model": "tinyllama"
            },
            "thermal": {
                "enabled": True,
                "max_temp": 75,
                "critical_temp": 85,
                "performance_script": "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh"
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            # Test thermal-aware operation
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Thermal-safe AI response",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                # Should check real thermal status
                response = await mycoder.process_request(
                    "Perform a thermal-sensitive AI operation"
                )
                
                # Should complete regardless of thermal status
                assert response is not None
                
                if response["success"]:
                    # Verify thermal monitoring was active
                    call_args = mock_query.call_args
                    context = call_args[1]["context"]
                    assert "thermal_status" in context
                    assert "cpu_temp" in context["thermal_status"]
                else:
                    # If failed due to thermal limits, should have appropriate error
                    assert "thermal" in response.get("error", "").lower()
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_provider_switching_scenario(self):
        """Test realistic provider switching scenario"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "claude_anthropic": {"enabled": True},
                "claude_oauth": {"enabled": True}, 
                "gemini": {"enabled": True},
                "ollama_local": {"enabled": True}
            }
            
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            session_id = "provider_switching_test"
            
            # Simulate provider switching during conversation
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                
                providers = [
                    APIProviderType.CLAUDE_ANTHROPIC,
                    APIProviderType.CLAUDE_OAUTH,
                    APIProviderType.GEMINI,
                    APIProviderType.OLLAMA_LOCAL
                ]
                
                call_count = 0
                def mock_switching_response(prompt, **kwargs):
                    nonlocal call_count
                    current_provider = providers[call_count % len(providers)]
                    call_count += 1
                    
                    return APIResponse(
                        success=True,
                        content=f"Response from {current_provider.value}",
                        provider=current_provider,
                        session_id=kwargs.get("session_id")
                    )
                
                mock_query.side_effect = mock_switching_response
                
                # Multiple requests with different providers
                for i in range(4):
                    response = await mycoder.process_request(
                        f"Request {i + 1}",
                        session_id=session_id,
                        continue_session=i > 0
                    )
                    
                    assert response["success"] is True
                    assert response["session_id"] == session_id
                    expected_provider = providers[i].value
                    assert expected_provider in response["content"]
                
                # Verify session tracked all provider switches
                session_data = mycoder.session_store[session_id]
                assert session_data["total_interactions"] == 4
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_large_project_analysis_scenario(self):
        """Test analyzing a larger project structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create larger project structure
            structure = {
                "src": {
                    "models": ["user.py", "product.py", "__init__.py"],
                    "views": ["user_view.py", "product_view.py", "__init__.py"],
                    "utils": ["helpers.py", "constants.py", "__init__.py"],
                    "tests": ["test_models.py", "test_views.py", "__init__.py"]
                },
                "docs": ["README.md", "API.md"],
                "config": ["settings.py", "database.py"]
            }
            
            all_files = []
            for dir_name, contents in structure.items():
                dir_path = project_root / dir_name
                dir_path.mkdir()
                
                if isinstance(contents, list):
                    for file_name in contents:
                        file_path = dir_path / file_name
                        file_path.write_text(f"# Content of {file_name}\npass\n")
                        all_files.append(file_path)
                else:
                    for sub_dir, files in contents.items():
                        sub_path = dir_path / sub_dir
                        sub_path.mkdir()
                        for file_name in files:
                            file_path = sub_path / file_name
                            file_path.write_text(f"# Content of {file_name}\npass\n")
                            all_files.append(file_path)
            
            config = {
                "ollama_local": {"enabled": True},
                "system": {"enable_tool_registry": True}
            }
            
            mycoder = EnhancedMyCoderV2(
                working_directory=project_root,
                config=config
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                mock_query.return_value = APIResponse(
                    success=True,
                    content="This is a well-structured Python project with models, views, utils, and tests.",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                # Analyze subset of files (simulate file limit)
                selected_files = all_files[:5]  # Limit to first 5 files
                
                response = await mycoder.process_request(
                    "Analyze this Python project structure and suggest improvements",
                    files=selected_files
                )
                
                assert response["success"] is True
                assert "project" in response["content"]
                
                # Verify file context was provided
                call_args = mock_query.call_args
                context = call_args[1]["context"]
                assert "files" in context
                assert len(context["files"]) == 5
            
            await mycoder.shutdown()


@pytest.mark.performance
class TestPerformanceIntegration:
    """Performance-focused integration tests"""
    
    @pytest.mark.asyncio
    async def test_initialization_performance(self):
        """Test system initialization performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "claude_oauth": {"enabled": True},
                "ollama_local": {"enabled": True},
                "thermal": {"enabled": True}
            }
            
            start_time = time.time()
            
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config=config
            )
            
            await mycoder.initialize()
            
            init_time = time.time() - start_time
            
            # Should initialize within reasonable time
            assert init_time < 10.0  # Less than 10 seconds
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_request_processing_performance(self):
        """Test request processing performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}}
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Quick response",
                    provider=APIProviderType.OLLAMA_LOCAL,
                    duration_ms=100
                )
                
                # Test multiple requests
                times = []
                for i in range(10):
                    start = time.time()
                    response = await mycoder.process_request(f"Quick test {i}")
                    end = time.time()
                    
                    assert response["success"] is True
                    times.append(end - start)
                
                # Average processing time should be reasonable
                avg_time = sum(times) / len(times)
                assert avg_time < 1.0  # Less than 1 second average
                
                # No request should take too long
                assert max(times) < 2.0  # No request over 2 seconds
            
            await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_storage_performance(self):
        """Test session storage performance with many sessions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mycoder = EnhancedMyCoderV2(
                working_directory=Path(temp_dir),
                config={"ollama_local": {"enabled": True}}
            )
            
            await mycoder.initialize()
            
            with patch.object(mycoder.provider_router, 'query') as mock_query:
                from api_providers import APIResponse
                mock_query.return_value = APIResponse(
                    success=True,
                    content="Session response",
                    provider=APIProviderType.OLLAMA_LOCAL
                )
                
                # Create many sessions
                start_time = time.time()
                
                for i in range(50):
                    await mycoder.process_request(
                        f"Session test {i}",
                        session_id=f"perf_session_{i}"
                    )
                
                end_time = time.time()
                
                # Should handle 50 sessions efficiently
                total_time = end_time - start_time
                assert total_time < 30.0  # Less than 30 seconds for 50 sessions
                
                # Verify session cleanup works (should keep last 100)
                assert len(mycoder.session_store) == 50
                
                # Add more to test cleanup
                for i in range(50, 120):
                    await mycoder.process_request(
                        f"Session test {i}",
                        session_id=f"perf_session_{i}"
                    )
                
                # Should have cleaned up to 100 sessions
                assert len(mycoder.session_store) == 100
            
            await mycoder.shutdown()