"""
MyCoder Adaptive Modes System

This module implements intelligent mode switching based on network conditions,
resource availability, and service health for optimal user experience.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

try:
    from claude_cli_auth import (  # type: ignore
        AuthConfig,
        AuthManager,
        ClaudeAuthError,
        ClaudeAuthManager,
    )
except Exception:
    # Temporary local definitions for Docker development
    class ClaudeAuthError(Exception):
        """Base auth error for temporary use."""

    class AuthConfig:
        """Temporary auth config class."""

        def __init__(self, **kwargs):
            self.settings = kwargs

    class AuthManager:
        """Temporary auth manager for missing claude_cli_auth."""

        def is_authenticated(self) -> bool:
            return False

        def _find_claude_cli(self) -> Optional[str]:
            return None

        async def _run_claude_command(self, args: List[str]):
            raise ClaudeAuthError("Claude CLI not available")

    class ClaudeAuthManager:
        """Temporary auth manager class."""

        def __init__(self, *args, **kwargs):
            self.config = kwargs.get("config")

        async def authenticate(self) -> bool:
            return True

        async def shutdown(self) -> None:
            return None

        async def query(self, *args, **kwargs):
            raise ClaudeAuthError("Claude auth not available")


# Define ClaudeNetworkError locally since it's MyCoder-specific
class ClaudeNetworkError(ClaudeAuthError):
    """Network-related error for adaptive mode operations."""

    pass


logger = logging.getLogger(__name__)


class OperationalMode(Enum):
    """Available operational modes for MyCoder system."""

    FULL = "FULL"  # Complete functionality - orchestrator + Claude + all MCP
    DEGRADED = "DEGRADED"  # Limited connectivity - local MCP + Claude with fallbacks
    AUTONOMOUS = "AUTONOMOUS"  # No external AI - local LLM only + basic MCP
    RECOVERY = "RECOVERY"  # Emergency mode - file operations only


@dataclass
class ModeCapabilities:
    """Defines what capabilities are available in each mode."""

    claude_auth: bool = True
    mcp_orchestrator: Optional[str] = None
    memory_system: str = "sqlite"
    available_tools: List[str] = field(default_factory=list)
    local_llm: Optional[str] = None
    max_timeout: int = 30
    enable_streaming: bool = True
    use_sdk: bool = True


@dataclass
class HealthStatus:
    """System health indicators."""

    internet_stable: bool = False
    orchestrator_available: bool = False
    claude_auth_working: bool = False
    local_resources_ok: bool = True
    last_check: float = 0.0
    check_duration: float = 0.0


class NetworkDetective:
    """Detects network conditions and service availability."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_internet_stability(self) -> bool:
        """Test internet connectivity and stability."""
        if not self.session:
            return False

        test_urls = [
            "https://api.anthropic.com/health",
            "https://www.google.com",
            "https://github.com",
        ]

        successful_tests = 0
        start_time = time.time()

        for url in test_urls:
            try:
                async with self.session.get(url) as response:
                    if response.status < 500:  # Accept 4xx as "reachable"
                        successful_tests += 1
            except Exception as e:
                logger.debug(f"Internet test failed for {url}: {e}")

        test_duration = time.time() - start_time
        stability = successful_tests >= 2 and test_duration < 8.0

        logger.debug(
            f"Internet stability: {successful_tests}/{len(test_urls)} "
            f"tests passed in {test_duration:.1f}s -> {stability}"
        )
        return stability

    async def test_orchestrator_connection(
        self, orchestrator_url: str = "http://192.168.0.58:8020"
    ) -> bool:
        """Test MCP orchestrator availability and response time."""
        if not self.session:
            return False

        try:
            start_time = time.time()
            async with self.session.get(f"{orchestrator_url}/health") as response:
                response_time = time.time() - start_time

                if response.status == 200 and response_time < 5.0:
                    logger.debug(f"Orchestrator healthy: {response_time:.1f}s")
                    return True
                else:
                    logger.debug(
                        f"Orchestrator unhealthy: status={response.status}, "
                        f"time={response_time:.1f}s"
                    )
                    return False

        except Exception as e:
            logger.debug(f"Orchestrator connection failed: {e}")
            return False

    async def test_claude_authentication(self) -> bool:
        """Test Claude CLI authentication status."""
        try:
            auth_manager = AuthManager()

            # Quick authentication check without full initialization
            if not auth_manager.is_authenticated():
                logger.debug("Claude CLI not authenticated")
                return False

            # Try a minimal command to verify working auth
            claude_cli = auth_manager._find_claude_cli()
            if not claude_cli:
                logger.debug("Claude CLI executable not found")
                return False

            # Test command execution with timeout
            result = await asyncio.wait_for(
                auth_manager._run_claude_command([claude_cli, "auth", "whoami"]),
                timeout=10.0,
            )

            success = result.returncode == 0 and "@" in result.stdout
            logger.debug(f"Claude auth test: {'✅' if success else '❌'}")
            return success

        except asyncio.TimeoutError:
            logger.debug("Claude auth test timed out")
            return False
        except Exception as e:
            logger.debug(f"Claude auth test failed: {e}")
            return False


class ResourceMonitor:
    """Monitors system resources and local services."""

    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_available": cpu_percent < 80,
                "memory_available": memory.percent < 85,
                "disk_available": disk.percent < 90,
                "load_average": (
                    psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0
                ),
            }

        except ImportError:
            logger.debug("psutil not available, assuming resources OK")
            return {
                "cpu_available": True,
                "memory_available": True,
                "disk_available": True,
                "load_average": 0,
            }
        except Exception as e:
            logger.debug(f"Resource check failed: {e}")
            return {
                "cpu_available": True,
                "memory_available": True,
                "disk_available": True,
                "load_average": 0,
            }

    async def assess_local_llm_availability(self) -> Dict[str, Any]:
        """Check if local LLM services are available."""
        llm_status = {
            "ollama_available": False,
            "codellama_available": False,
            "models": [],
        }

        try:
            # Test Ollama availability
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:11434/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        llm_status["ollama_available"] = True
                        llm_status["models"] = [
                            model["name"] for model in data.get("models", [])
                        ]
                        llm_status["codellama_available"] = any(
                            "codellama" in model.lower()
                            for model in llm_status["models"]
                        )

        except Exception as e:
            logger.debug(f"Local LLM check failed: {e}")

        logger.debug(f"Local LLM status: {llm_status}")
        return llm_status


class AdaptiveModeManager:
    """Central manager for adaptive mode switching and system health."""

    def __init__(
        self,
        initial_mode: OperationalMode = OperationalMode.FULL,
        claude_auth_enabled: bool = True,
    ):
        self.current_mode = initial_mode
        self.mode_history: List[tuple] = []  # (mode, timestamp, reason)
        self.health_status = HealthStatus()
        self.claude_auth: Optional[ClaudeAuthManager] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self._mode_transition_lock = asyncio.Lock()
        self.claude_auth_enabled = claude_auth_enabled

        # Mode configurations
        claude_auth = bool(claude_auth_enabled)
        self.mode_configs = {
            OperationalMode.FULL: ModeCapabilities(
                claude_auth=claude_auth,
                mcp_orchestrator="http://192.168.0.58:8020",
                memory_system="postgresql+qdrant",
                available_tools=[
                    "filesystem",
                    "git",
                    "terminal",
                    "database",
                    "memory",
                    "transcriber",
                    "research",
                ],
                max_timeout=30,
                enable_streaming=True,
                use_sdk=True,
            ),
            OperationalMode.DEGRADED: ModeCapabilities(
                claude_auth=claude_auth,
                mcp_orchestrator="http://localhost:8020",
                memory_system="sqlite",
                available_tools=["filesystem", "git", "terminal"],
                max_timeout=60,
                enable_streaming=True,
                use_sdk=False,  # Use CLI only for reliability
            ),
            OperationalMode.AUTONOMOUS: ModeCapabilities(
                claude_auth=False,
                local_llm="ollama://codellama",
                mcp_orchestrator="http://localhost:8020",
                memory_system="sqlite",
                available_tools=["filesystem", "terminal"],
                max_timeout=120,
                enable_streaming=False,
                use_sdk=False,
            ),
            OperationalMode.RECOVERY: ModeCapabilities(
                claude_auth=False,
                memory_system="file",
                available_tools=["filesystem"],
                max_timeout=180,
                enable_streaming=False,
                use_sdk=False,
            ),
        }

        logger.info(f"Adaptive Mode Manager initialized in {initial_mode.value} mode")

    async def start_monitoring(self):
        """Start continuous health monitoring and mode adaptation."""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Monitoring already running")
            return

        self.monitoring_task = asyncio.create_task(self._monitor_health())
        logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                logger.info("Health monitoring stop requested")
            logger.info("Health monitoring stopped")

    async def _monitor_health(self):
        """Continuous health monitoring loop."""
        while True:
            try:
                await self.evaluate_and_adapt()
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                logger.info("Health monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Longer delay on error

    async def evaluate_and_adapt(self):
        """Evaluate system health and adapt mode if necessary."""
        start_time = time.time()

        async with NetworkDetective() as detective:
            # Perform all health checks
            self.health_status.internet_stable = (
                await detective.test_internet_stability()
            )
            self.health_status.orchestrator_available = (
                await detective.test_orchestrator_connection()
            )
            if self.claude_auth_enabled:
                self.health_status.claude_auth_working = (
                    await detective.test_claude_authentication()
                )
            else:
                self.health_status.claude_auth_working = True

        resource_monitor = ResourceMonitor()
        resources = await resource_monitor.check_system_resources()
        self.health_status.local_resources_ok = all(resources.values())

        self.health_status.last_check = time.time()
        self.health_status.check_duration = time.time() - start_time

        # Determine optimal mode based on health status
        optimal_mode = self._determine_optimal_mode()

        # Transition if needed
        if optimal_mode != self.current_mode:
            reason = self._get_transition_reason(optimal_mode)
            logger.info(
                "Mode transition needed: %s -> %s (%s)",
                self.current_mode.value,
                optimal_mode.value,
                reason,
            )
            await self.transition_to_mode(optimal_mode, reason)

    def _determine_optimal_mode(self) -> OperationalMode:
        """Determine optimal mode based on current health status."""
        if (
            self.health_status.internet_stable
            and self.health_status.orchestrator_available
            and self.health_status.claude_auth_working
            and self.health_status.local_resources_ok
        ):
            return OperationalMode.FULL

        elif (
            self.health_status.claude_auth_working
            and self.health_status.local_resources_ok
        ):
            return OperationalMode.DEGRADED

        elif self.health_status.local_resources_ok:
            return OperationalMode.AUTONOMOUS

        else:
            return OperationalMode.RECOVERY

    def _get_transition_reason(self, new_mode: OperationalMode) -> str:
        """Get human-readable reason for mode transition."""
        reasons = []

        if not self.health_status.internet_stable:
            reasons.append("internet unstable")
        if not self.health_status.orchestrator_available:
            reasons.append("orchestrator unreachable")
        if not self.health_status.claude_auth_working:
            reasons.append("claude auth failed")
        if not self.health_status.local_resources_ok:
            reasons.append("low system resources")

        if not reasons:
            return "all services healthy"
        return ", ".join(reasons)

    async def transition_to_mode(
        self, new_mode: OperationalMode, reason: str = "manual"
    ):
        """Safely transition to a new operational mode."""
        async with self._mode_transition_lock:
            if new_mode == self.current_mode:
                logger.debug(f"Already in {new_mode.value} mode")
                return

            old_mode = self.current_mode
            transition_start = time.time()

            try:
                # Record transition
                self.mode_history.append((new_mode, time.time(), reason))

                # Clean up previous mode
                await self._cleanup_mode(old_mode)

                # Initialize new mode
                await self._initialize_mode(new_mode)

                self.current_mode = new_mode
                transition_time = time.time() - transition_start

                logger.info(
                    f"Mode transition completed: {old_mode.value} → {new_mode.value} "
                    f"in {transition_time:.1f}s ({reason})"
                )

            except Exception as e:
                logger.error(f"Mode transition failed: {e}")
                # Try to restore previous mode
                try:
                    await self._initialize_mode(old_mode)
                    logger.info(
                        f"Restored to {old_mode.value} mode after failed transition"
                    )
                except Exception as restore_error:
                    logger.error(f"Failed to restore mode: {restore_error}")
                    self.current_mode = OperationalMode.RECOVERY
                    logger.critical(
                        "Forced to RECOVERY mode due to transition failures"
                    )

    async def _cleanup_mode(self, mode: OperationalMode):
        """Clean up resources from previous mode."""
        if self.claude_auth:
            try:
                await self.claude_auth.shutdown()
            except Exception as e:
                logger.debug(f"Error shutting down Claude auth: {e}")
            self.claude_auth = None

        logger.debug(f"Cleaned up {mode.value} mode")

    async def _initialize_mode(self, mode: OperationalMode):
        """Initialize new operational mode."""
        config = self.mode_configs[mode]

        # Initialize Claude authentication if required
        if config.claude_auth:
            try:
                auth_config = AuthConfig(
                    timeout_seconds=config.max_timeout,
                    use_sdk=config.use_sdk,
                    enable_streaming=config.enable_streaming,
                    session_timeout_hours=24 if mode == OperationalMode.FULL else 6,
                )

                self.claude_auth = ClaudeAuthManager(
                    config=auth_config,
                    prefer_sdk=config.use_sdk,
                    enable_fallback=mode == OperationalMode.DEGRADED,
                )

                logger.debug(f"Claude auth initialized for {mode.value} mode")

            except Exception as e:
                logger.error(f"Failed to initialize Claude auth for {mode.value}: {e}")
                if mode != OperationalMode.RECOVERY:
                    # Fall back to more basic mode
                    if mode == OperationalMode.FULL:
                        await self._initialize_mode(OperationalMode.DEGRADED)
                        return
                    elif mode == OperationalMode.DEGRADED:
                        await self._initialize_mode(OperationalMode.AUTONOMOUS)
                        return
                raise

        logger.info(
            f"Initialized {mode.value} mode with capabilities: "
            f"{len(config.available_tools)} tools, "
            f"memory: {config.memory_system}"
        )

    def get_current_capabilities(self) -> ModeCapabilities:
        """Get current mode capabilities."""
        return self.mode_configs[self.current_mode]

    async def query_ai(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Query AI service based on current mode capabilities."""
        config = self.get_current_capabilities()

        if config.claude_auth and self.claude_auth:
            try:
                response = await self.claude_auth.query(
                    prompt, timeout=config.max_timeout, **kwargs
                )
                return {
                    "success": True,
                    "content": response.content,
                    "session_id": response.session_id,
                    "cost": response.cost,
                    "source": "claude",
                }

            except Exception as e:
                logger.error(
                    f"Claude query failed in {self.current_mode.value} mode: {e}"
                )
                # Try to degrade mode if possible
                if self.current_mode == OperationalMode.FULL:
                    await self.transition_to_mode(
                        OperationalMode.DEGRADED, "claude query failed"
                    )
                    return await self.query_ai(prompt, **kwargs)  # Retry

        elif config.local_llm:
            # Use local LLM
            return await self._query_local_llm(prompt, config.local_llm, **kwargs)

        else:
            # Recovery mode - return error or basic response
            return {
                "success": False,
                "content": (
                    "AI services unavailable in {} mode. "
                    "Only basic file operations available."
                ).format(self.current_mode.value),
                "source": "none",
            }

    async def _query_local_llm(
        self, prompt: str, llm_endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Query local LLM (Ollama)."""
        try:
            # Extract model from endpoint (ollama://codellama -> codellama)
            model = llm_endpoint.split("://")[-1]

            async with aiohttp.ClientSession() as session:
                payload = {"model": model, "prompt": prompt, "stream": False}

                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "content": data.get(
                                "response", "No response from local LLM"
                            ),
                            "source": "local_llm",
                            "model": model,
                        }

        except Exception as e:
            logger.error(f"Local LLM query failed: {e}")

        return {
            "success": False,
            "content": "Local LLM unavailable",
            "source": "local_llm",
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        config = self.get_current_capabilities()

        return {
            "mode": self.current_mode.value,
            "health": {
                "internet_stable": self.health_status.internet_stable,
                "orchestrator_available": self.health_status.orchestrator_available,
                "claude_auth_working": self.health_status.claude_auth_working,
                "local_resources_ok": self.health_status.local_resources_ok,
                "last_check": self.health_status.last_check,
                "check_duration": self.health_status.check_duration,
            },
            "capabilities": {
                "claude_auth": config.claude_auth,
                "mcp_orchestrator": config.mcp_orchestrator,
                "memory_system": config.memory_system,
                "available_tools": config.available_tools,
                "local_llm": config.local_llm,
            },
            "mode_history": [
                {"mode": mode.value, "timestamp": timestamp, "reason": reason}
                for mode, timestamp, reason in self.mode_history[
                    -10:
                ]  # Last 10 transitions
            ],
        }
