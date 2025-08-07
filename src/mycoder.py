"""
MyCoder Integration with Claude CLI Auth and Adaptive Modes

This module provides the main MyCoder class that integrates claude-cli-auth
with the adaptive modes system for optimal performance under varying conditions.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from claude_cli_auth import (
    ClaudeAuthManager,
    ClaudeAuthError,
    AuthConfig,
    ClaudeResponse,
)

from .adaptive_modes import AdaptiveModeManager, OperationalMode
from .ollama_integration import CodeGenerationProvider, OllamaClient

# Create custom network error that inherits from ClaudeAuthError
class ClaudeNetworkError(ClaudeAuthError):
    """Network-related error for MyCoder operations."""
    pass

logger = logging.getLogger(__name__)


class MyCoder:
    """
    Main MyCoder class with adaptive Claude integration.
    
    Provides intelligent AI-powered development assistance that automatically
    adapts to network conditions, resource availability, and service health.
    
    Features:
    - Adaptive mode switching (FULL, DEGRADED, AUTONOMOUS, RECOVERY)
    - Claude CLI authentication with fallbacks
    - MCP orchestrator integration
    - Session persistence across mode transitions
    - Intelligent error recovery
    """
    
    def __init__(self, 
                 working_directory: Optional[Path] = None,
                 initial_mode: OperationalMode = OperationalMode.FULL):
        """
        Initialize MyCoder with adaptive capabilities.
        
        Args:
            working_directory: Base directory for operations
            initial_mode: Starting operational mode (optimistic by default)
        """
        self.working_directory = working_directory or Path.cwd()
        self.mode_manager = AdaptiveModeManager(initial_mode)
        self.session_store: Dict[str, Dict] = {}  # Session persistence
        self._initialized = False
        
        logger.info(f"MyCoder initialized with working directory: {self.working_directory}")
    
    async def initialize(self):
        """Initialize MyCoder system with adaptive mode detection."""
        if self._initialized:
            logger.debug("MyCoder already initialized")
            return
            
        logger.info("Initializing MyCoder with adaptive mode detection...")
        
        # Start adaptive mode monitoring
        await self.mode_manager.start_monitoring()
        
        # Perform initial health evaluation and mode setup
        await self.mode_manager.evaluate_and_adapt()
        
        self._initialized = True
        current_mode = self.mode_manager.current_mode
        logger.info(f"MyCoder initialization complete in {current_mode.value} mode")
    
    async def shutdown(self):
        """Gracefully shutdown MyCoder system."""
        logger.info("Shutting down MyCoder...")
        
        # Stop monitoring
        await self.mode_manager.stop_monitoring()
        
        # Clean up Claude auth
        if self.mode_manager.claude_auth:
            await self.mode_manager.claude_auth.shutdown()
            
        self._initialized = False
        logger.info("MyCoder shutdown complete")
    
    async def process_request(self,
                            prompt: str,
                            files: Optional[List[Union[str, Path]]] = None,
                            session_id: Optional[str] = None,
                            continue_session: bool = False,
                            **kwargs) -> Dict[str, Any]:
        """
        Process a development request with adaptive AI assistance.
        
        Args:
            prompt: The user's request or question
            files: Files to include in the request context
            session_id: Session ID for conversation continuity
            continue_session: Whether to continue existing session
            **kwargs: Additional parameters (timeout, temperature, etc.)
            
        Returns:
            Dict containing response content, metadata, and session info
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        current_mode = self.mode_manager.current_mode
        
        logger.info(f"Processing request in {current_mode.value} mode")
        logger.debug(f"Request: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        
        try:
            # Prepare request context
            request_context = await self._prepare_request_context(
                prompt=prompt,
                files=files,
                session_id=session_id,
                continue_session=continue_session,
                **kwargs
            )
            
            # Execute based on current mode capabilities
            result = await self._execute_request(request_context)
            
            # Record session for persistence
            if result.get("session_id"):
                await self._update_session_store(result["session_id"], request_context, result)
            
            # Add performance metrics
            duration = asyncio.get_event_loop().time() - start_time
            result.update({
                "mode": current_mode.value,
                "duration_seconds": duration,
                "capabilities": self.mode_manager.get_current_capabilities().__dict__
            })
            
            logger.info(f"Request completed in {duration:.1f}s using {current_mode.value} mode")
            return result
            
        except Exception as e:
            logger.error(f"Request processing failed in {current_mode.value} mode: {e}")
            
            # Attempt recovery by degrading mode
            if current_mode != OperationalMode.RECOVERY:
                logger.info("Attempting request retry with mode degradation...")
                await self._handle_request_failure(e)
                return await self.process_request(prompt, files, session_id, continue_session, **kwargs)
            else:
                # Already in recovery mode, return error
                return {
                    "success": False,
                    "error": str(e),
                    "mode": current_mode.value,
                    "recovery_suggestions": self._get_recovery_suggestions()
                }
    
    async def _prepare_request_context(self, **kwargs) -> Dict[str, Any]:
        """Prepare request context based on current mode capabilities."""
        capabilities = self.mode_manager.get_current_capabilities()
        
        context = {
            "prompt": kwargs.get("prompt", ""),
            "working_directory": self.working_directory,
            "timeout": kwargs.get("timeout", capabilities.max_timeout),
        }
        
        # Handle files based on mode
        if kwargs.get("files"):
            context["files"] = [Path(f) for f in kwargs["files"]]
        
        # Session management
        if kwargs.get("session_id"):
            context["session_id"] = kwargs["session_id"]
            context["continue_session"] = kwargs.get("continue_session", False)
        
        # Mode-specific options
        if capabilities.enable_streaming:
            context["enable_streaming"] = kwargs.get("enable_streaming", True)
            
        return context
    
    async def _execute_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request based on current mode capabilities."""
        capabilities = self.mode_manager.get_current_capabilities()
        
        if capabilities.claude_auth:
            # Use Claude via our adaptive auth manager
            return await self._execute_claude_request(context)
            
        elif capabilities.local_llm:
            # Use local LLM
            return await self._execute_local_llm_request(context)
            
        else:
            # Recovery mode - basic file operations only
            return await self._execute_recovery_request(context)
    
    async def _execute_claude_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request using Claude with our auth manager."""
        if not self.mode_manager.claude_auth:
            raise ClaudeAuthError("Claude auth manager not available")
        
        try:
            # Convert to claude-cli-auth format
            claude_kwargs = {
                "working_directory": context["working_directory"],
                "timeout": context["timeout"]
            }
            
            if context.get("files"):
                claude_kwargs["files"] = [str(f) for f in context["files"]]
            
            if context.get("session_id"):
                claude_kwargs["session_id"] = context["session_id"]
                claude_kwargs["continue_session"] = context.get("continue_session", False)
            
            # Execute query
            response = await self.mode_manager.claude_auth.query(
                context["prompt"],
                **claude_kwargs
            )
            
            return {
                "success": True,
                "content": response.content,
                "session_id": response.session_id,
                "cost": response.cost,
                "duration_ms": response.duration_ms,
                "num_turns": response.num_turns,
                "tools_used": response.tools_used,
                "source": "claude_auth"
            }
            
        except Exception as e:
            logger.error(f"Claude request execution failed: {e}")
            raise
    
    async def _execute_local_llm_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request using local LLM."""
        capabilities = self.mode_manager.get_current_capabilities()
        
        # Build context-aware prompt for local LLM
        enhanced_prompt = await self._build_local_llm_prompt(context)
        
        # Use mode manager's local LLM query
        result = await self.mode_manager._query_local_llm(
            enhanced_prompt, 
            capabilities.local_llm
        )
        
        if result["success"]:
            result.update({
                "session_id": context.get("session_id") or f"local_{int(asyncio.get_event_loop().time())}",
                "source": "local_llm"
            })
        
        return result
    
    async def _execute_recovery_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute basic file operations in recovery mode."""
        prompt = context["prompt"].lower()
        
        if "read" in prompt or "show" in prompt or "display" in prompt:
            return await self._handle_file_read_request(context)
        elif "write" in prompt or "create" in prompt or "save" in prompt:
            return await self._handle_file_write_request(context) 
        elif "list" in prompt or "ls" in prompt or "dir" in prompt:
            return await self._handle_file_list_request(context)
        else:
            return {
                "success": False,
                "content": (
                    "🚨 RECOVERY MODE ACTIVE\n\n"
                    "AI services are currently unavailable. Available commands:\n"
                    "• 'read [filename]' - Read file contents\n"
                    "• 'write [filename] [content]' - Write to file\n" 
                    "• 'list [directory]' - List directory contents\n\n"
                    "Please try again when services are restored."
                ),
                "mode": "recovery",
                "source": "recovery"
            }
    
    async def _build_local_llm_prompt(self, context: Dict[str, Any]) -> str:
        """Build enhanced prompt for local LLM with file context."""
        prompt_parts = []
        
        # Add system context for local LLM
        prompt_parts.append(
            "You are a helpful coding assistant. Provide clear, concise answers.\n"
        )
        
        # Add file contents if specified
        if context.get("files"):
            prompt_parts.append("=== FILE CONTEXT ===")
            for file_path in context["files"][:3]:  # Limit to first 3 files
                try:
                    if file_path.exists() and file_path.is_file():
                        content = file_path.read_text(encoding="utf-8")[:2000]  # Limit size
                        prompt_parts.append(f"File: {file_path.name}\n```\n{content}\n```\n")
                except Exception as e:
                    prompt_parts.append(f"File: {file_path.name} (error reading: {e})\n")
        
        # Add user prompt
        prompt_parts.append("=== USER REQUEST ===")
        prompt_parts.append(context["prompt"])
        
        return "\n\n".join(prompt_parts)
    
    async def _handle_file_read_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file reading in recovery mode."""
        try:
            files = context.get("files", [])
            if not files:
                return {
                    "success": False,
                    "content": "No files specified for reading",
                    "source": "recovery"
                }
            
            results = []
            for file_path in files[:5]:  # Limit to 5 files
                if file_path.exists() and file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        results.append(f"=== {file_path.name} ===\n{content}")
                    except Exception as e:
                        results.append(f"=== {file_path.name} ===\nError: {e}")
                else:
                    results.append(f"=== {file_path.name} ===\nFile not found")
            
            return {
                "success": True,
                "content": "\n\n".join(results),
                "source": "recovery",
                "files_read": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"File read failed: {e}",
                "source": "recovery"
            }
    
    async def _handle_file_write_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle basic file writing in recovery mode."""
        return {
            "success": False,
            "content": "File writing not implemented in recovery mode for safety",
            "source": "recovery"
        }
    
    async def _handle_file_list_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle directory listing in recovery mode."""
        try:
            directory = context.get("working_directory", self.working_directory)
            
            if not directory.exists():
                return {
                    "success": False,
                    "content": f"Directory not found: {directory}",
                    "source": "recovery"
                }
            
            files = []
            for item in directory.iterdir():
                item_type = "dir" if item.is_dir() else "file"
                size = item.stat().st_size if item.is_file() else 0
                files.append(f"{item_type:4} {size:>10} {item.name}")
            
            content = f"Directory listing for {directory}:\n" + "\n".join(sorted(files))
            
            return {
                "success": True,
                "content": content,
                "source": "recovery",
                "file_count": len(files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"Directory listing failed: {e}",
                "source": "recovery"
            }
    
    async def _handle_request_failure(self, error: Exception):
        """Handle request failure by attempting mode degradation."""
        current_mode = self.mode_manager.current_mode
        
        if isinstance(error, (ClaudeAuthError, ClaudeNetworkError)):
            reason = f"claude error: {str(error)[:50]}"
        else:
            reason = f"general error: {type(error).__name__}"
        
        # Determine appropriate fallback mode
        if current_mode == OperationalMode.FULL:
            await self.mode_manager.transition_to_mode(OperationalMode.DEGRADED, reason)
        elif current_mode == OperationalMode.DEGRADED:
            await self.mode_manager.transition_to_mode(OperationalMode.AUTONOMOUS, reason)
        elif current_mode == OperationalMode.AUTONOMOUS:
            await self.mode_manager.transition_to_mode(OperationalMode.RECOVERY, reason)
        
        logger.info(f"Mode degraded due to error: {reason}")
    
    async def _update_session_store(self, session_id: str, context: Dict[str, Any], result: Dict[str, Any]):
        """Update persistent session storage."""
        self.session_store[session_id] = {
            "last_context": context,
            "last_result": result,
            "updated_at": asyncio.get_event_loop().time(),
            "mode": self.mode_manager.current_mode.value
        }
        
        # Cleanup old sessions (keep last 50)
        if len(self.session_store) > 50:
            oldest_sessions = sorted(
                self.session_store.items(), 
                key=lambda x: x[1]["updated_at"]
            )[:-50]
            for session_id, _ in oldest_sessions:
                del self.session_store[session_id]
    
    def _get_recovery_suggestions(self) -> List[str]:
        """Get recovery suggestions for failed requests."""
        return [
            "Check internet connectivity",
            "Verify Claude CLI authentication: claude auth login",
            "Restart MCP orchestrator services",
            "Try again with simpler request",
            "Use recovery mode for basic file operations"
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive MyCoder system status."""
        status = self.mode_manager.get_system_status()
        status.update({
            "working_directory": str(self.working_directory),
            "initialized": self._initialized,
            "active_sessions": len(self.session_store)
        })
        return status
    
    async def force_mode(self, mode: OperationalMode, reason: str = "manual override"):
        """Manually force a specific operational mode."""
        await self.mode_manager.transition_to_mode(mode, reason)
        logger.info(f"Manually forced to {mode.value} mode: {reason}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        if not self._initialized:
            await self.initialize()
            
        await self.mode_manager.evaluate_and_adapt()
        return self.get_status()