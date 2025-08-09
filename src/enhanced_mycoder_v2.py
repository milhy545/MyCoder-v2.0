"""
Enhanced MyCoder v2.0 with Multi-API Architecture

This module provides the enhanced MyCoder class that integrates the new multi-API
provider system with FEI-inspired architecture patterns for optimal performance
and intelligent fallbacks across different AI providers.

Features:
- 5-tier API provider system (Claude Anthropic, Claude OAuth, Gemini, Ollama Local/Remote)
- FEI-inspired tool registry and service layer architecture  
- Intelligent provider selection based on context and thermal conditions
- Advanced error recovery with provider fallbacks
- Thermal-aware operation for Q9550 systems
- Session persistence across provider transitions
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .api_providers import (
    APIProviderRouter, 
    APIProviderConfig, 
    APIProviderType, 
    APIResponse,
    ClaudeAnthropicProvider,
    ClaudeOAuthProvider, 
    GeminiProvider,
    OllamaProvider
)
from .tool_registry import (
    get_tool_registry,
    ToolExecutionContext,
    ToolCategory,
    ToolAvailability
)
from .adaptive_modes import AdaptiveModeManager, OperationalMode

logger = logging.getLogger(__name__)


class EnhancedMyCoderV2:
    """
    Enhanced MyCoder v2.0 with Multi-API Architecture
    
    Provides intelligent AI-powered development assistance with:
    - 5-tier API provider fallback system
    - FEI-inspired tool registry and service layers
    - Thermal-aware operation for Q9550 systems  
    - Advanced session management across providers
    - Intelligent context-aware provider selection
    """
    
    def __init__(self, 
                 working_directory: Optional[Path] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize Enhanced MyCoder v2.0
        
        Args:
            working_directory: Base directory for operations
            config: Configuration dictionary for API providers and settings
        """
        self.working_directory = working_directory or Path.cwd()
        self.config = config or {}
        self.session_store: Dict[str, Dict] = {}
        self.thermal_monitor = None
        self._initialized = False
        
        # Initialize API provider router
        self.provider_router = None
        
        # Initialize tool registry
        self.tool_registry = get_tool_registry()
        
        # Initialize adaptive mode manager
        self.mode_manager = AdaptiveModeManager(OperationalMode.FULL)
        
        logger.info(f"Enhanced MyCoder v2.0 initialized with working directory: {self.working_directory}")
    
    async def initialize(self):
        """Initialize Enhanced MyCoder system with multi-API providers"""
        if self._initialized:
            logger.debug("Enhanced MyCoder already initialized")
            return
            
        logger.info("Initializing Enhanced MyCoder v2.0 with multi-API system...")
        
        # Initialize API providers
        await self._initialize_api_providers()
        
        # Initialize thermal monitoring for Q9550 systems
        await self._initialize_thermal_monitoring()
        
        # Start adaptive mode monitoring  
        await self.mode_manager.start_monitoring()
        await self.mode_manager.evaluate_and_adapt()
        
        # Register additional tools
        await self._register_enhanced_tools()
        
        self._initialized = True
        logger.info("Enhanced MyCoder v2.0 initialization complete")
        
        # Log available providers
        available_providers = self.provider_router.get_available_providers()
        logger.info(f"Available API providers: {[p.value for p in available_providers]}")
    
    async def _initialize_api_providers(self):
        """Initialize the multi-API provider system"""
        provider_configs = []
        
        # Claude Anthropic API (Priority 1)
        if self.config.get("claude_anthropic_enabled", True):
            claude_config = APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                enabled=bool(os.getenv("ANTHROPIC_API_KEY")),
                timeout_seconds=30,
                config={
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "model": self.config.get("claude_model", "claude-3-5-sonnet-20241022")
                }
            )
            provider_configs.append(claude_config)
        
        # Claude OAuth (Priority 2) 
        if self.config.get("claude_oauth_enabled", True):
            oauth_config = APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_OAUTH,
                enabled=True,  # Always try OAuth as fallback
                timeout_seconds=45,
                config={}
            )
            provider_configs.append(oauth_config)
        
        # Gemini API (Priority 3)
        if self.config.get("gemini_enabled", True):
            gemini_config = APIProviderConfig(
                provider_type=APIProviderType.GEMINI,
                enabled=bool(os.getenv("GEMINI_API_KEY")),
                timeout_seconds=30,
                config={
                    "api_key": os.getenv("GEMINI_API_KEY"),
                    "model": self.config.get("gemini_model", "gemini-1.5-pro")
                }
            )
            provider_configs.append(gemini_config)
        
        # Ollama Local (Priority 4)
        if self.config.get("ollama_local_enabled", True):
            local_ollama_config = APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_LOCAL,
                enabled=True,
                timeout_seconds=60,  # Longer timeout for local processing
                config={
                    "base_url": "http://localhost:11434",
                    "model": self.config.get("ollama_local_model", "tinyllama")
                }
            )
            provider_configs.append(local_ollama_config)
        
        # Ollama Remote (Priority 5)
        remote_urls = self.config.get("ollama_remote_urls", [])
        for i, url in enumerate(remote_urls):
            remote_config = APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_REMOTE,
                enabled=True,
                timeout_seconds=45,
                config={
                    "base_url": url,
                    "model": self.config.get("ollama_remote_model", "tinyllama")
                }
            )
            provider_configs.append(remote_config)
        
        # Initialize router with all providers
        self.provider_router = APIProviderRouter(provider_configs)
        
        logger.info(f"Initialized {len(provider_configs)} API providers")
    
    async def _initialize_thermal_monitoring(self):
        """Initialize thermal monitoring for Q9550 systems"""
        try:
            # Check if PowerManagement system is available
            import subprocess
            result = subprocess.run(
                ["/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.thermal_monitor = {
                    "enabled": True,
                    "script_path": "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh"
                }
                logger.info("Thermal monitoring enabled for Q9550 system")
                
                # Configure thermal integration in providers
                thermal_config = {
                    "enabled": True,
                    "max_temp": 80,
                    "critical_temp": 85,
                    "check_interval": 30
                }
                await self.provider_router.configure_thermal_integration(thermal_config)
            else:
                logger.info("Thermal monitoring not available")
                
        except Exception as e:
            logger.warning(f"Failed to initialize thermal monitoring: {e}")
            self.thermal_monitor = {"enabled": False}
    
    async def _register_enhanced_tools(self):
        """Register enhanced tools for v2.0 functionality"""
        # Tools are already registered in tool_registry initialization
        # This method can be extended for additional v2.0 specific tools
        
        # Add event handlers for tool monitoring
        def tool_execution_handler(event_type, data):
            logger.debug(f"Tool event: {event_type} - {data.get('tool_name', 'unknown')}")
        
        self.tool_registry.add_event_handler("tool_post_execution", tool_execution_handler)
        self.tool_registry.add_event_handler("tool_execution_error", tool_execution_handler)
        
        logger.info("Enhanced tool system configured")
    
    async def process_request(self,
                            prompt: str,
                            files: Optional[List[Union[str, Path]]] = None,
                            session_id: Optional[str] = None,
                            continue_session: bool = False,
                            preferred_provider: Optional[APIProviderType] = None,
                            use_tools: bool = True,
                            **kwargs) -> Dict[str, Any]:
        """
        Process a development request with multi-API intelligence
        
        Args:
            prompt: The user's request or question
            files: Files to include in the request context
            session_id: Session ID for conversation continuity
            continue_session: Whether to continue existing session
            preferred_provider: Preferred API provider to try first
            use_tools: Whether to use tool registry for enhanced capabilities
            **kwargs: Additional parameters
            
        Returns:
            Dict containing response content, metadata, and provider info
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        current_mode = self.mode_manager.current_mode
        
        logger.info(f"Processing request in {current_mode.value} mode")
        logger.debug(f"Request: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        
        try:
            # Prepare request context
            context = await self._prepare_enhanced_context(
                prompt=prompt,
                files=files,
                session_id=session_id,
                continue_session=continue_session,
                **kwargs
            )
            
            # Get thermal status if monitoring enabled
            if self.thermal_monitor and self.thermal_monitor["enabled"]:
                context["thermal_status"] = await self._get_thermal_status()
            
            # Execute request with multi-API system
            api_response = await self.provider_router.query(
                prompt=prompt,
                context=context,
                preferred_provider=preferred_provider,
                **kwargs
            )
            
            # Enhance response with tool integration if requested
            if use_tools and api_response.success:
                enhanced_response = await self._enhance_with_tools(api_response, context)
                if enhanced_response:
                    api_response = enhanced_response
            
            # Update session store
            if session_id and api_response.success:
                await self._update_enhanced_session_store(session_id, context, api_response)
            
            # Prepare final response
            duration = time.time() - start_time
            
            response = {
                "success": api_response.success,
                "content": api_response.content,
                "provider": api_response.provider.value,
                "session_id": api_response.session_id,
                "cost": api_response.cost,
                "duration_seconds": duration,
                "duration_ms": api_response.duration_ms,
                "tokens_used": api_response.tokens_used,
                "mode": current_mode.value,
                "metadata": api_response.metadata or {}
            }
            
            if not api_response.success:
                response["error"] = api_response.error
            
            logger.info(f"Request completed in {duration:.1f}s using {api_response.provider.value}")
            return response
            
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            
            return {
                "success": False,
                "content": "",
                "provider": "none",
                "error": str(e),
                "mode": current_mode.value,
                "duration_seconds": time.time() - start_time,
                "recovery_suggestions": self._get_recovery_suggestions()
            }
    
    async def _prepare_enhanced_context(self, **kwargs) -> Dict[str, Any]:
        """Prepare enhanced request context for multi-API processing"""
        context = {
            "working_directory": self.working_directory,
            "mode": self.mode_manager.current_mode.value,
            "timestamp": time.time()
        }
        
        # Add file context
        if kwargs.get("files"):
            context["files"] = [Path(f) if isinstance(f, str) else f for f in kwargs["files"]]
        
        # Add session context
        if kwargs.get("session_id"):
            context["session_id"] = kwargs["session_id"]
            context["continue_session"] = kwargs.get("continue_session", False)
        
        # Add network status
        context["network_status"] = {
            "connected": True,  # TODO: Implement actual network check
            "quality": "good"   # TODO: Implement network quality check
        }
        
        # Add resource limits based on mode
        if self.mode_manager.current_mode == OperationalMode.AUTONOMOUS:
            context["resource_limits"] = {
                "max_tokens": 2048,
                "timeout_seconds": 30,
                "thermal_sensitive": True
            }
        elif self.mode_manager.current_mode == OperationalMode.RECOVERY:
            context["resource_limits"] = {
                "max_tokens": 512,
                "timeout_seconds": 15,
                "thermal_sensitive": True
            }
        
        return context
    
    async def _get_thermal_status(self) -> Dict[str, Any]:
        """Get current thermal status for Q9550 system"""
        try:
            import subprocess
            result = subprocess.run(
                [self.thermal_monitor["script_path"], "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse temperature from output
                output = result.stdout.lower()
                
                # Extract temperature if available
                cpu_temp = 60  # Default safe assumption
                if "temp" in output:
                    # Try to extract temperature value
                    import re
                    temp_match = re.search(r'(\d+)°?c', output)
                    if temp_match:
                        cpu_temp = int(temp_match.group(1))
                
                status = "normal"
                if cpu_temp > 85:
                    status = "critical"
                elif cpu_temp > 80:
                    status = "high"
                elif cpu_temp > 75:
                    status = "elevated"
                
                return {
                    "cpu_temp": cpu_temp,
                    "status": status,
                    "safe_operation": cpu_temp < 80,
                    "timestamp": time.time()
                }
            
            return {"status": "unknown", "safe_operation": True}
            
        except Exception as e:
            logger.warning(f"Thermal status check failed: {e}")
            return {"status": "unknown", "safe_operation": True}
    
    async def _enhance_with_tools(self, 
                                 api_response: APIResponse, 
                                 context: Dict[str, Any]) -> Optional[APIResponse]:
        """Enhance API response using tool registry"""
        try:
            # Create tool execution context
            tool_context = ToolExecutionContext(
                mode=context.get("mode", "FULL"),
                working_directory=context.get("working_directory"),
                session_id=context.get("session_id"),
                thermal_status=context.get("thermal_status"),
                network_status=context.get("network_status"),
                resource_limits=context.get("resource_limits")
            )
            
            # Example: If response mentions file operations, execute them
            content = api_response.content.lower()
            
            if "read file" in content or "show file" in content:
                # Extract file path from content (simplified)
                # In a real implementation, this would use NLP to extract file paths
                file_result = await self.tool_registry.execute_tool(
                    "file_read",
                    tool_context,
                    operation="read",
                    path="example.txt"  # This should be extracted from content
                )
                
                if file_result.success:
                    # Append file contents to response
                    enhanced_content = f"{api_response.content}\n\nFile Contents:\n{file_result.data}"
                    
                    return APIResponse(
                        success=True,
                        content=enhanced_content,
                        provider=api_response.provider,
                        cost=api_response.cost,
                        duration_ms=api_response.duration_ms + file_result.duration_ms,
                        tokens_used=api_response.tokens_used,
                        session_id=api_response.session_id,
                        metadata={
                            **api_response.metadata,
                            "tools_used": ["file_read"],
                            "tool_results": [file_result.metadata]
                        }
                    )
            
            return None  # No enhancement applied
            
        except Exception as e:
            logger.error(f"Tool enhancement failed: {e}")
            return None
    
    async def _update_enhanced_session_store(self, 
                                           session_id: str, 
                                           context: Dict[str, Any], 
                                           response: APIResponse):
        """Update session store with enhanced metadata"""
        self.session_store[session_id] = {
            "last_context": context,
            "last_response": {
                "provider": response.provider.value,
                "success": response.success,
                "cost": response.cost,
                "duration_ms": response.duration_ms,
                "tokens_used": response.tokens_used
            },
            "updated_at": time.time(),
            "mode": context.get("mode"),
            "thermal_status": context.get("thermal_status"),
            "total_interactions": self.session_store.get(session_id, {}).get("total_interactions", 0) + 1
        }
        
        # Cleanup old sessions (keep last 100)
        if len(self.session_store) > 100:
            oldest_sessions = sorted(
                self.session_store.items(), 
                key=lambda x: x[1]["updated_at"]
            )[:-100]
            for session_id, _ in oldest_sessions:
                del self.session_store[session_id]
    
    def _get_recovery_suggestions(self) -> List[str]:
        """Get recovery suggestions for failed requests"""
        return [
            "Check internet connectivity for cloud providers",
            "Verify API keys are configured (ANTHROPIC_API_KEY, GEMINI_API_KEY)",
            "Ensure Claude CLI is authenticated: claude auth login",
            "Check if Ollama is running: ollama list",
            "Monitor system temperature for Q9550 thermal limits",
            "Try with preferred_provider parameter to force specific provider",
            "Use RECOVERY mode for basic file operations only"
        ]
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        # Get provider health
        provider_health = await self.provider_router.health_check_all()
        
        # Get thermal status
        thermal_status = None
        if self.thermal_monitor and self.thermal_monitor["enabled"]:
            thermal_status = await self._get_thermal_status()
        
        # Get tool registry stats
        tool_stats = self.tool_registry.get_registry_stats()
        
        # Get mode manager status
        mode_status = self.mode_manager.get_system_status()
        
        return {
            "status": "initialized",
            "working_directory": str(self.working_directory),
            "active_sessions": len(self.session_store),
            "providers": provider_health,
            "thermal": thermal_status,
            "tools": tool_stats,
            "mode": mode_status,
            "timestamp": time.time()
        }
    
    async def force_provider(self, provider_type: APIProviderType) -> bool:
        """Force a specific provider for testing purposes"""
        try:
            provider = self.provider_router._get_provider(provider_type)
            if provider:
                # Test provider with simple query
                test_response = await provider.query("Hello", timeout_seconds=10)
                return test_response.success
            return False
        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            return False
    
    async def shutdown(self):
        """Gracefully shutdown Enhanced MyCoder system"""
        logger.info("Shutting down Enhanced MyCoder v2.0...")
        
        # Stop adaptive mode monitoring
        if hasattr(self.mode_manager, 'stop_monitoring'):
            await self.mode_manager.stop_monitoring()
        
        # Clear session store
        self.session_store.clear()
        
        self._initialized = False
        logger.info("Enhanced MyCoder v2.0 shutdown complete")