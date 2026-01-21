"""
Enhanced MyCoder with MCP Orchestrator Integration

Advanced version of MyCoder that leverages the MCP orchestrator for
enhanced capabilities including memory persistence, file operations,
git integration, and research capabilities.
"""

import logging
import os
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from .adaptive_modes import ClaudeNetworkError, OperationalMode
    from .mcp_connector import MCPConnector, MCPToolRouter
    from .mycoder import MyCoder
except ImportError:
    from adaptive_modes import (  # type: ignore
        ClaudeNetworkError,
        OperationalMode,
    )
    from mcp_connector import MCPConnector, MCPToolRouter  # type: ignore

    from mycoder import MyCoder  # type: ignore

logger = logging.getLogger(__name__)


class EnhancedMyCoder(MyCoder):
    """
    Enhanced MyCoder with full MCP orchestrator integration.

    Extends the base MyCoder with:
    - MCP tool routing and orchestration
    - Enhanced memory persistence via MCP memory service
    - File operations through MCP filesystem service
    - Git operations via MCP git service
    - Research capabilities through MCP research service
    - Intelligent tool fallbacks and mode-aware capabilities
    """

    def __init__(
        self,
        working_directory: Optional[Path] = None,
        initial_mode: OperationalMode = OperationalMode.FULL,
        orchestrator_url: str = "http://192.168.0.58:8020",
    ):
        """
        Initialize Enhanced MyCoder with MCP orchestrator integration.

        Args:
            working_directory: Base directory for operations
            initial_mode: Starting operational mode
            orchestrator_url: URL of MCP orchestrator service
        """
        super().__init__(working_directory, initial_mode)

        self.orchestrator_url = orchestrator_url
        self.mcp_connector: Optional[MCPConnector] = None
        self.tool_router: Optional[MCPToolRouter] = None
        self.enhanced_capabilities = {
            "mcp_integration": True,
            "persistent_memory": True,
            "distributed_tools": True,
            "research_capabilities": True,
        }

        logger.info(
            f"Enhanced MyCoder initialized with orchestrator: {orchestrator_url}"
        )

    async def initialize(self):
        """Initialize Enhanced MyCoder with MCP orchestrator."""
        # Initialize base MyCoder
        await super().initialize()

        # Initialize MCP connector if in appropriate mode
        current_mode = self.mode_manager.current_mode
        if current_mode in [OperationalMode.FULL, OperationalMode.DEGRADED]:
            try:
                await self._initialize_mcp_connector()
                logger.info(
                    f"MCP orchestrator integration enabled for {current_mode.value} mode"
                )
            except Exception as e:
                logger.warning(f"MCP initialization failed: {e}")
                if current_mode == OperationalMode.FULL:
                    # Degrade mode if MCP fails in FULL mode
                    await self.mode_manager.transition_to_mode(
                        OperationalMode.DEGRADED, "MCP orchestrator unavailable"
                    )

    async def _initialize_mcp_connector(self):
        """Initialize MCP connector and tool router."""
        self.mcp_connector = MCPConnector(self.orchestrator_url)
        await self.mcp_connector.__aenter__()

        # Check if orchestrator is healthy
        is_healthy = await self.mcp_connector.test_connection()
        if not is_healthy:
            await self.mcp_connector.__aexit__(None, None, None)
            self.mcp_connector = None
            raise ClaudeNetworkError("MCP orchestrator not responding")

        # Initialize tool router
        self.tool_router = MCPToolRouter(self.mcp_connector)

        # Get available tools for current mode
        available_tools = await self.mcp_connector.get_available_tools_for_mode(
            self.mode_manager.current_mode
        )
        logger.info(
            f"MCP connector initialized with {len(available_tools)} available tools"
        )

    async def shutdown(self):
        """Gracefully shutdown Enhanced MyCoder."""
        logger.info("Shutting down Enhanced MyCoder...")

        # Shutdown MCP connector
        if self.mcp_connector:
            try:
                await self.mcp_connector.__aexit__(None, None, None)
                self.mcp_connector = None
                self.tool_router = None
            except Exception as e:
                logger.error(f"Error shutting down MCP connector: {e}")

        # Shutdown base MyCoder
        await super().shutdown()

        logger.info("Enhanced MyCoder shutdown complete")

    async def process_request(
        self,
        prompt: str,
        files: Optional[List[Union[str, Path]]] = None,
        session_id: Optional[str] = None,
        continue_session: bool = False,
        use_mcp_memory: bool = True,
        research_context: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process request with enhanced MCP capabilities.

        Args:
            prompt: User's request or question
            files: Files to include in context
            session_id: Session ID for conversation continuity
            continue_session: Whether to continue existing session
            use_mcp_memory: Whether to use MCP memory service for context
            research_context: Whether to include research context
            **kwargs: Additional parameters

        Returns:
            Enhanced response with MCP tool usage and metadata
        """
        if not self._initialized:
            await self.initialize()

        current_mode = self.mode_manager.current_mode
        logger.info(f"Processing enhanced request in {current_mode.value} mode")

        # Enhance request with MCP capabilities
        enhanced_context = await self._enhance_request_context(
            prompt=prompt,
            files=files,
            session_id=session_id,
            use_mcp_memory=use_mcp_memory,
            research_context=research_context,
            **kwargs,
        )

        # Process with enhanced context
        result = await super().process_request(
            enhanced_context["enhanced_prompt"],
            files=enhanced_context.get("files"),
            session_id=session_id,
            continue_session=continue_session,
            **kwargs,
        )

        # Post-process with MCP storage
        if result.get("success") and use_mcp_memory:
            await self._store_interaction_memory(enhanced_context, result)

        # Add MCP metadata
        result.update(
            {
                "mcp_tools_used": enhanced_context.get("mcp_tools_used", []),
                "memory_context": enhanced_context.get("memory_context"),
                "research_context": enhanced_context.get("research_context"),
                "orchestrator_status": (
                    "connected" if self.mcp_connector else "disconnected"
                ),
            }
        )

        return result

    async def _enhance_request_context(self, **kwargs) -> Dict[str, Any]:
        """Enhance request context with MCP services."""
        context = {
            "enhanced_prompt": kwargs.get("prompt", ""),
            "files": kwargs.get("files", []),
            "mcp_tools_used": [],
            "memory_context": None,
            "research_context": None,
        }

        current_mode = self.mode_manager.current_mode

        # Add memory context if available
        if kwargs.get("use_mcp_memory") and self.mcp_connector:
            memory_context = await self._get_memory_context(
                kwargs.get("prompt", ""), current_mode
            )
            if memory_context:
                context["memory_context"] = memory_context
                context["enhanced_prompt"] = (
                    f"Previous context:\n{memory_context}\n\n"
                    f"Current request: {kwargs.get('prompt', '')}"
                )
                context["mcp_tools_used"].append("search_memories")

        # Add research context if requested
        if kwargs.get("research_context") and self.mcp_connector:
            research_context = await self._get_research_context(
                kwargs.get("prompt", ""), current_mode
            )
            if research_context:
                context["research_context"] = research_context
                context[
                    "enhanced_prompt"
                ] += f"\n\nResearch context:\n{research_context}"
                context["mcp_tools_used"].append("research_query")

        # Enhance with file analysis if files provided
        if kwargs.get("files") and self.mcp_connector:
            file_analysis = await self._analyze_files_via_mcp(
                kwargs["files"], current_mode
            )
            if file_analysis:
                context["enhanced_prompt"] += f"\n\nFile analysis:\n{file_analysis}"
                context["mcp_tools_used"].append("file_analyze")

        return context

    async def _get_memory_context(
        self, prompt: str, mode: OperationalMode
    ) -> Optional[str]:
        """Get relevant memory context for the prompt."""
        if not self.mcp_connector:
            return None

        try:
            # Search for relevant memories
            result = await self.mcp_connector.search_memories(
                query=prompt[:200], limit=5, mode=mode  # Limit query length
            )

            if result.get("success"):
                memories = result.get("result", {}).get("memories", [])
                if memories:
                    memory_texts = []
                    for memory in memories[:3]:  # Top 3 most relevant
                        content = memory.get("content", "")
                        importance = memory.get("importance", 0)
                        memory_texts.append(f"[{importance:.2f}] {content}")

                    return "\n".join(memory_texts)

        except Exception as e:
            logger.debug(f"Memory context retrieval failed: {e}")

        return None

    async def _get_research_context(
        self, prompt: str, mode: OperationalMode
    ) -> Optional[str]:
        """Get research context for the prompt."""
        if not self.mcp_connector or mode in [
            OperationalMode.AUTONOMOUS,
            OperationalMode.RECOVERY,
        ]:
            return None

        try:
            # Extract key terms for research
            research_query = self._extract_research_keywords(prompt)
            if not research_query:
                return None

            result = await self.mcp_connector.research_query(
                query=research_query, mode=mode
            )

            if result.get("success"):
                research_data = result.get("result", {})
                return research_data.get("summary", "")[:500]  # Limit context size

        except Exception as e:
            logger.debug(f"Research context retrieval failed: {e}")

        return None

    def _extract_research_keywords(self, prompt: str) -> Optional[str]:
        """Extract research keywords from prompt."""
        # Simple keyword extraction - can be enhanced with NLP
        research_indicators = [
            "latest",
            "current",
            "recent",
            "new",
            "update",
            "what is",
            "how to",
            "best practice",
            "example",
            "tutorial",
            "documentation",
        ]

        prompt_lower = prompt.lower()
        if any(indicator in prompt_lower for indicator in research_indicators):
            # Extract potential search terms (simple heuristic)
            words = prompt.split()
            keywords = [word for word in words if len(word) > 3 and word.isalnum()]
            return " ".join(keywords[:5])  # Top 5 keywords

        return None

    async def _analyze_files_via_mcp(
        self, files: List[Union[str, Path]], mode: OperationalMode
    ) -> Optional[str]:
        """Analyze files using MCP file service."""
        if not self.mcp_connector:
            return None

        analysis_results = []

        for file_path in files[:3]:  # Limit to 3 files
            try:
                result = await self.mcp_connector.read_file(str(file_path), mode)

                if result.get("success"):
                    file_content = result.get("result", {}).get("content", "")
                    if file_content:
                        # Simple analysis
                        analysis = {
                            "file": str(file_path),
                            "size": len(file_content),
                            "lines": file_content.count("\n") + 1,
                            "type": self._detect_file_type(str(file_path)),
                        }
                        analysis_results.append(analysis)

            except Exception as e:
                logger.debug(f"File analysis failed for {file_path}: {e}")

        if analysis_results:
            summary = "File analysis:\n"
            for analysis in analysis_results:
                summary += (
                    f"- {analysis['file']}: {analysis['type']}, "
                    f"{analysis['lines']} lines, {analysis['size']} chars\n"
                )
            return summary

        return None

    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension."""
        ext = Path(file_path).suffix.lower()
        type_mapping = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".html": "HTML",
            ".css": "CSS",
            ".json": "JSON",
            ".md": "Markdown",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".txt": "Text",
            ".log": "Log file",
        }
        return type_mapping.get(ext, "Unknown")

    async def _store_interaction_memory(
        self, context: Dict[str, Any], result: Dict[str, Any]
    ):
        """Store interaction in MCP memory service."""
        if not self.mcp_connector:
            return

        try:
            # Create memory content
            memory_content = (
                f"User request: {context.get('enhanced_prompt', '')[:200]}...\n"
                f"Response: {result.get('content', '')[:200]}...\n"
                f"Mode: {result.get('mode', 'unknown')}\n"
                f"Tools used: {', '.join(context.get('mcp_tools_used', []))}"
            )

            # Determine importance based on success and content length
            importance = 0.7 if result.get("success") else 0.3
            if result.get("cost", 0) > 0.01:  # Higher importance for expensive queries
                importance += 0.2

            await self.mcp_connector.store_memory(
                content=memory_content,
                memory_type="interaction",
                importance=min(1.0, importance),
                mode=self.mode_manager.current_mode,
            )

        except Exception as e:
            logger.debug(f"Memory storage failed: {e}")

    # Enhanced tool methods with MCP integration

    async def read_file_enhanced(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Enhanced file reading via MCP or local fallback."""
        if self.tool_router:
            result = await self.tool_router.route_tool_call(
                "read_file", {"path": str(file_path)}, self.mode_manager.current_mode
            )

            # Handle adaptive actions
            if result.get("adaptive_action") == "degrade_mode":
                await self.mode_manager.transition_to_mode(
                    OperationalMode.DEGRADED, "MCP file service unavailable"
                )
                # Retry with degraded mode
                return await self.tool_router.route_tool_call(
                    "read_file", {"path": str(file_path)}, OperationalMode.DEGRADED
                )

            return result
        else:
            # Local fallback
            return await self._local_file_read(file_path)

    async def _local_file_read(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Local file reading fallback."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            content = path.read_text(encoding="utf-8")
            return {
                "success": True,
                "result": {"content": content},
                "fallback_used": "local_pathlib",
            }

        except Exception as e:
            return {"success": False, "error": f"Local file read failed: {e}"}

    async def execute_command_enhanced(
        self, command: str, working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced command execution via MCP or local fallback."""
        if self.tool_router:
            return await self.tool_router.route_tool_call(
                "execute",
                {"command": command, "working_dir": working_dir},
                self.mode_manager.current_mode,
            )
        else:
            # Local fallback using subprocess
            return await self._local_command_execution(command, working_dir)

    async def _local_command_execution(
        self, command: str, working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Local command execution fallback."""
        try:
            import subprocess

            args = shlex.split(command, posix=os.name != "nt")
            if not args:
                return {"success": False, "error": "Command is empty"}

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=working_dir,
            )

            return {
                "success": result.returncode == 0,
                "result": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
                "fallback_used": "local_subprocess",
            }

        except Exception as e:
            return {"success": False, "error": f"Local command execution failed: {e}"}

    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive Enhanced MyCoder status."""
        status = super().get_status()

        # Add MCP-specific status
        status.update(
            {
                "mcp_orchestrator": {
                    "url": self.orchestrator_url,
                    "connected": self.mcp_connector is not None,
                    "status": (
                        self.mcp_connector.get_service_status()
                        if self.mcp_connector
                        else None
                    ),
                },
                "enhanced_capabilities": self.enhanced_capabilities,
                "tool_router": {
                    "available": self.tool_router is not None,
                    "tool_mappings": (
                        len(self.tool_router.tool_mappings) if self.tool_router else 0
                    ),
                },
            }
        )

        return status
