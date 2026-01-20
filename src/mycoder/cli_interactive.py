"""
MyCoder v2.2.0 Interactive CLI
Architecture: Split-screen UI using rich.Live.
Left: Chat History (Auto-scrolling Markdown). Right: Activity Panel (Live Activity).
"""

import asyncio
import json
import os
import re
import shutil
import sys
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

# Rich library is now required via poetry
try:
    from rich import box
    from rich.align import Align
    from rich.console import Console, Group
    from rich.layout import Layout
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("CRITICAL: 'rich' library not found. Please run: poetry add rich")
    sys.exit(1)

# Optional prompt_toolkit for Tab-based selection.
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.key_binding import KeyBindings
except ImportError:
    pt_prompt = None
    KeyBindings = None
    PromptSession = None

# Import Core
try:
    from .agents import AgentOrchestrator, AgentType
    from .api_providers import APIProviderType
    from .auto_executor import ActionType, AutoExecutor
    from .command_parser import Command, CommandParser
    from .context_manager import ContextManager
    from .enhanced_mycoder_v2 import EnhancedMyCoderV2
    from .mcp_bridge import MCPBridge
    from .project_init import (
        DEFAULT_INIT_FILENAME,
        INIT_FILE_ALIASES,
        generate_project_guide,
    )
    from .self_evolve import SelfEvolveManager
    from .todo_tracker import TodoTracker
    from .tool_registry import ToolExecutionContext
    from .ui_activity_panel import Activity, ActivityPanel, ActivityType
    from .web_tools import WebFetcher, WebSearcher
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from mycoder.agents import AgentOrchestrator, AgentType
    from mycoder.api_providers import APIProviderType
    from mycoder.auto_executor import ActionType, AutoExecutor
    from mycoder.command_parser import Command, CommandParser
    from mycoder.enhanced_mycoder_v2 import EnhancedMyCoderV2
    from mycoder.mcp_bridge import MCPBridge
    from mycoder.project_init import (
        DEFAULT_INIT_FILENAME,
        INIT_FILE_ALIASES,
        generate_project_guide,
    )
    from mycoder.self_evolve import SelfEvolveManager
    from mycoder.todo_tracker import TodoTracker
    from mycoder.tool_registry import ToolExecutionContext
    from mycoder.ui_activity_panel import Activity, ActivityPanel, ActivityType
    from mycoder.web_tools import WebFetcher, WebSearcher

try:
    from .tts_engine import TTSEngine
except ImportError:
    TTSEngine = None

# CYBERPUNK PALETTE
COLOR_SYSTEM = "bold cyan"
COLOR_USER = "bold green"
COLOR_SUCCESS = "bold magenta"
COLOR_INFO = "italic yellow"
COLOR_BORDER = "blue"

# Pre-compiled Regex Patterns for Performance
THINKING_REGEX = re.compile(r"(<thinking>.*?</thinking>)", flags=re.DOTALL)
MD_CODE_BLOCK_REGEX = re.compile(r"```[\s\S]*?```")
MD_INLINE_CODE_REGEX = re.compile(r"`[^`]*`")
MD_STYLE_REGEX = re.compile(r"[*_~`]")
MD_HEADER_REGEX = re.compile(r"^#+\s+", flags=re.MULTILINE)


class ConfigWrapper:
    """Helper to access dict via dot notation for backward compatibility."""

    def __init__(self, data):
        object.__setattr__(self, "_data", data)

    def __getattr__(self, name):
        if name in self._data:
            val = self._data[name]
            if isinstance(val, dict):
                return ConfigWrapper(val)
            return val
        return None

    def __setattr__(self, name, value):
        self._data[name] = value


class ExecutionMonitor:
    """Track operation logs and surface system metrics for the execution panel."""

    def __init__(self) -> None:
        """Initialize the log queue and capacity."""
        self.logs: List[Tuple[str, str, str]] = []
        self.max_logs: int = 15

    def add_log(self, action: str, resource: str = "") -> None:
        """Add a timestamped entry and trim logs to the configured cap."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logs.append((timestamp, action, resource))
        self.logs = self.logs[-15:]

    def set_operation(self, operation: str, progress: int = 0) -> None:
        """No-op for compatibility with dynamic monitors."""
        return None

    def update_progress(self, percent: int) -> None:
        """No-op for compatibility with dynamic monitors."""
        return None

    def clear_operation(self) -> None:
        """No-op for compatibility with dynamic monitors."""
        return None

    def update_provider_health(self, provider: str, status: str) -> None:
        """No-op for compatibility with dynamic monitors."""
        return None

    def set_thermal_warning(self, warning: bool) -> None:
        """No-op for compatibility with dynamic monitors."""
        return None

    def _render_bar(self, percent: float) -> str:
        """Return a 10-character ASCII bar for the provided percentage."""
        normalized = max(0.0, min(100.0, percent or 0.0))
        filled = int(round(normalized / 10))
        filled = max(0, min(10, filled))
        empty = 10 - filled
        return "█" * filled + "░" * empty

    def get_system_metrics(self) -> dict:
        """Return the latest CPU, RAM, and thermal measurements."""
        metrics = {"cpu": 0.0, "ram": 0.0, "thermal": "N/A"}
        try:
            metrics["cpu"] = psutil.cpu_percent(interval=None)
        except Exception:
            # Best effort metrics; skip if psutil fails or is unavailable.
            pass
        try:
            metrics["ram"] = psutil.virtual_memory().percent
        except Exception:
            # Best effort memory metric; ignore unexpected failures.
            pass
        try:
            temps = psutil.sensors_temperatures()
            for entries in temps.values():
                if entries:
                    temp = entries[0]
                    if hasattr(temp, "current"):
                        metrics["thermal"] = f"{temp.current:.1f}°C"
                    else:
                        metrics["thermal"] = str(temp)
                    break
        except (AttributeError, Exception):
            # Ignore sensor errors, not critical for UI rendering.
            pass
        return metrics

    def render(self, console: Console) -> Panel:
        """
        Render the execution log table with conservative height calculation.

        Uses defensive sizing to prevent overflow even on small terminals or during resize.

        Args:
            console: Rich Console instance for terminal size detection

        Returns:
            Panel containing the operation log table and system metrics
        """
        # Get terminal dimensions
        term_height = console.size.height
        term_width = console.size.width

        # Calculate available height for table rows - CONSERVATIVE APPROACH
        # Panel decorations breakdown:
        #   - Top border: 1
        #   - Title line: 1
        #   - Title padding: 1
        #   - Table header: 1
        #   - Table header separator: 1
        #   - Bottom border: 1
        #   - Subtitle: 1
        #   - Safety buffer for terminal edge: 2
        PANEL_OVERHEAD = 9  # Increased from 7 to be more defensive
        available_rows = max(2, term_height - PANEL_OVERHEAD)

        # Determine how many log entries will fit
        # Each row has separator line (show_lines=True) = 2 terminal lines per table row
        # Apply safety factor: only use 90% of available space
        safe_available_rows = int(available_rows * 0.9)
        max_visible_logs = max(1, safe_available_rows // 2)

        # Hard cap to prevent extreme cases
        max_visible_logs = min(max_visible_logs, 25)

        # Slice logs to fit available space (newest at bottom)
        visible_logs = self.logs[-max_visible_logs:] if self.logs else []

        # Build table with dynamic sizing
        table = Table(
            title="[bold cyan]═══ OPERATION LOG ═══[/bold cyan]",
            box=box.ASCII,
            show_header=True,
            show_lines=True,
            expand=False,
            width=max(40, term_width - 6),  # Increased margin from 4 to 6
            padding=(0, 1),  # Tighter padding to save space
        )

        # Column widths proportional to terminal width - with minimums
        time_width = 12
        remaining_width = max(40, term_width - 22)  # After time column + borders
        action_width = max(18, int(remaining_width * 0.55))
        resource_width = max(12, int(remaining_width * 0.35))

        table.add_column("TIME", width=time_width, style="bold yellow", no_wrap=True)
        table.add_column(
            "ACTION FLOW", width=action_width, style="cyan", overflow="ellipsis"
        )
        table.add_column(
            "RESOURCE", width=resource_width, style="dim white", overflow="ellipsis"
        )

        # Populate table with visible logs
        if not visible_logs:
            table.add_row("-", "No operations yet", "-")
        else:
            for timestamp, action, resource in visible_logs:
                table.add_row(timestamp, action, resource or "-")

        # System metrics footer
        metrics = self.get_system_metrics()
        cpu_bar = self._render_bar(metrics["cpu"])
        ram_bar = self._render_bar(metrics["ram"])

        subtitle = (
            f"[dim cyan]SYS │ CPU: {cpu_bar} {metrics['cpu']:.0f}% │ "
            f"RAM: {ram_bar} {metrics['ram']:.0f}% │ "
            f"THERMAL: {metrics['thermal']}[/dim cyan]"
        )

        return Panel(
            table,
            title="╔═══ EXECUTION MONITOR ═══╗",
            border_style="cyan",
            box=box.DOUBLE,
            subtitle=subtitle,
            expand=True,
        )


class InteractiveCLI:
    """Interactive command-line interface for MyCoder with split-screen UI."""

    def __init__(self) -> None:
        """Set up console, coder, and state for the interactive session."""
        self.console = Console()
        # Force Silent Thermal Mode for clean UI
        os.environ["MYCODER_THERMAL_ENABLED"] = "false"
        self.working_directory = self._resolve_working_directory()

        self.context_manager = ContextManager(self.working_directory)
        context_data = self.context_manager.get_context()
        self.config_dict = context_data.config
        self.config = ConfigWrapper(self.config_dict)

        self.coder = EnhancedMyCoderV2(
            working_directory=self.working_directory, config=self.config_dict
        )
        self.diffusing_mode = True
        self.realtime_mode = False
        self.active_provider = self.config.preferred_provider or "ollama_local"
        self.preferred_provider = self._map_provider(self.active_provider)
        self.chat_history: List[Dict[str, str]] = []
        self.show_thinking = False  # Toggle for displaying <thinking> blocks
        self.activity_panel = ActivityPanel()
        self.auto_executor = AutoExecutor(
            activity_panel=self.activity_panel, require_confirmation=True
        )
        self._live = None
        self._warned_small_terminal = False
        self.history_offset = 0
        self.history_step = 5
        history_env = os.getenv("MYCODER_HISTORY_PATH")
        self.history_path = (
            Path(history_env)
            if history_env
            else Path.home() / ".mycoder" / "history.json"
        )
        self._load_history()

        # NEW (v2.2.0): Command parser for tool execution
        self.command_parser = CommandParser()

        # TTS engine (v2.2.0)
        self.tts_engine = None
        tts_config = getattr(self.config, "text_to_speech", {}) or {}
        if TTSEngine and tts_config.get("enabled", False):
            self.tts_engine = TTSEngine(
                provider=tts_config.get("provider", "pyttsx3"),
                voice=tts_config.get("voice", "cs"),
                rate=tts_config.get("rate", 150),
            )

        self.self_evolve_manager = SelfEvolveManager(self.coder, self.working_directory)
        self.todo_tracker = TodoTracker(
            self.working_directory / ".mycoder" / "todo.json"
        )
        self.plan_task: Optional[str] = None
        self.plan_content: Optional[str] = None
        self.plan_status: str = "idle"
        self.agent_orchestrator = AgentOrchestrator(self.coder, self.working_directory)
        cache_dir = self.working_directory / ".mycoder" / "web_cache"
        self.web_fetcher = WebFetcher(cache_dir=cache_dir)
        self.web_searcher = WebSearcher(api_key=os.getenv("MYCODER_WEB_SEARCH_KEY"))
        self.mcp_bridge: Optional[MCPBridge] = None

    def _resolve_working_directory(self) -> Path:
        return Path.cwd()

    def _default_context_files(self) -> List[Path]:
        """Collect default context files (AGENTS + guides) from workspace."""
        candidates = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "MYCODER.md")
        files: List[Path] = []
        for name in candidates:
            path = self.working_directory / name
            if path.exists():
                files.append(path)
        return files

    def _prompt_confirm(self, message: str, default: bool = False) -> bool:
        """Ask for confirmation while safely suspending Live layout."""
        live = self._live
        if live:
            with suppress(Exception):
                live.stop()
        try:
            return Confirm.ask(message, default=default)
        finally:
            if live:
                with suppress(Exception):
                    live.start()
                self._refresh_live()

    def _handle_init_command(self, args: List[str]) -> None:
        """Create a project guide file similar to Claude/Gemini /init."""
        force = False
        target_value: Optional[str] = None

        for arg in args:
            if arg in ("-f", "--force"):
                force = True
            elif arg in ("--claude", "--gemini", "--mycoder"):
                target_value = INIT_FILE_ALIASES[arg.lstrip("-")]
            elif arg.startswith("-"):
                self.console.print(
                    "[bold red]Usage: /init [--force|-f] [--claude|--gemini|--mycoder] [path][/]"
                )
                return
            else:
                target_value = arg

        if target_value is None:
            target_value = DEFAULT_INIT_FILENAME
        if target_value in INIT_FILE_ALIASES:
            target_value = INIT_FILE_ALIASES[target_value]

        target_path = Path(target_value).expanduser()
        if not target_path.is_absolute():
            target_path = self.working_directory / target_path
        if target_path.exists() and target_path.is_dir():
            target_path = target_path / DEFAULT_INIT_FILENAME

        existed = target_path.exists()
        if existed and not force:
            if not self._prompt_confirm(
                f"[yellow]{target_path} exists. Overwrite?[/]", default=False
            ):
                self.console.print(f"[{COLOR_INFO}]Init canceled.[/]")
                return

        content = generate_project_guide(self.working_directory)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

        activity_type = ActivityType.FILE_EDIT if existed else ActivityType.FILE_CREATE
        try:
            display_path = str(target_path.relative_to(self.working_directory))
        except ValueError:
            display_path = str(target_path)

        self.activity_panel.add_activity(
            Activity(
                type=activity_type,
                description="Init guide",
                target=display_path,
                status="done",
            )
        )
        self.console.print(f"[{COLOR_SUCCESS}]Init wrote {display_path}[/]")

    async def _self_evolve_approval(self, proposal) -> bool:
        """Show proposal diff and request user approval."""
        self.console.print(Markdown(f"```diff\n{proposal.diff}\n```"))
        if proposal.summary:
            self.console.print(f"[{COLOR_INFO}]Summary:[/] {proposal.summary}")
        if proposal.rationale:
            self.console.print(f"[{COLOR_INFO}]Rationale:[/] {proposal.rationale}")
        if proposal.risk_notes:
            risk_pct = proposal.risk_score * 100
            self.console.print(
                f"[{COLOR_INFO}]Risk:[/] {risk_pct:.0f}% ({', '.join(proposal.risk_notes)})"
            )
        return self._prompt_confirm(
            f"Apply proposal {proposal.proposal_id} and run tests?", default=False
        )

    def _build_plan_prompt(self, task: str) -> str:
        return (
            "You are a software architect. Create an implementation plan for:\n\n"
            f"Task: {task}\n\n"
            "Provide:\n"
            "1. Summary of approach\n"
            "2. Step-by-step implementation (no time estimates)\n"
            "3. Critical files to modify\n"
            "4. Potential risks\n"
            "5. Dependencies to add (if any)\n\n"
            "Format as structured markdown."
        )

    def print_banner(self) -> None:
        """Render the stylized MyCoder banner at startup."""
        banner = r"""
    __  ___        ______          __
   /  |/  /_  __  / ____/___  ____/ /__  _____
  / /|_/ / / / / / /   / __ \/ __  / _ \/ ___/
 / /  / / /_/ / / /___/ /_/ / /_/ /  __/ /
/_/  /_/\__, /  \____/\____/\__,_/\___/_/
       /____/
      [ v2.2.0 - AI Powered ]
"""
        self.console.print(
            Panel(
                Align(Text(banner, style="bold cyan"), align="center"),
                border_style=COLOR_BORDER,
                box=box.HEAVY,
            )
        )

    def _provider_options(self) -> List[Dict[str, object]]:
        """Return supplier metadata for all supported AI providers."""
        return [
            {
                "key": "claude_anthropic",
                "label": "Claude Anthropic (API key)",
                "api_key": True,
            },
            {
                "key": "claude_oauth",
                "label": "Claude OAuth (claude-cli-auth)",
                "api_key": False,
            },
            {
                "key": "gemini",
                "label": "Gemini (API key)",
                "api_key": True,
            },
            {
                "key": "ollama_local",
                "label": "Ollama Local (localhost)",
                "api_key": False,
            },
            {
                "key": "termux_ollama",
                "label": "Termux Ollama (Android)",
                "api_key": False,
            },
            {
                "key": "ollama_remote",
                "label": "Ollama Remote (URLs)",
                "api_key": False,
            },
            {
                "key": "inception_mercury",
                "label": "Inception Mercury (API key)",
                "api_key": True,
            },
        ]

    def _show_providers(self) -> None:
        """Display a table of available AI providers and their API requirements."""
        table = Table(title="Supported AI Providers", box=box.ROUNDED)
        table.add_column("Key", style="cyan")
        table.add_column("Provider", style="white")
        table.add_column("API Key", style="yellow")
        for option in self._provider_options():
            api_required = "yes" if option["api_key"] else "no"
            table.add_row(option["key"], option["label"], api_required)
        self.console.print(table)

    def _map_provider(self, provider_key: str) -> Optional[APIProviderType]:
        """Map a provider key to the corresponding APIProviderType enum."""
        mapping = {
            "claude_anthropic": APIProviderType.CLAUDE_ANTHROPIC,
            "claude_oauth": APIProviderType.CLAUDE_OAUTH,
            "gemini": APIProviderType.GEMINI,
            "ollama_local": APIProviderType.OLLAMA_LOCAL,
            "termux_ollama": APIProviderType.TERMUX_OLLAMA,
            "ollama_remote": APIProviderType.OLLAMA_REMOTE,
            "inception_mercury": APIProviderType.MERCURY,
        }
        return mapping.get(provider_key)

    def _current_timestamp(self) -> str:
        """Return the current time formatted for chat records."""
        return datetime.now().strftime("%H:%M:%S")

    def _append_chat_entry(self, role: str, content: str) -> None:
        """Append a chat entry and persist history."""
        self.chat_history.append(
            {
                "role": role,
                "content": content,
                "timestamp": self._current_timestamp(),
            }
        )
        self.history_offset = 0
        self._save_history()

    def _load_history(self) -> None:
        """Load chat history from disk."""
        try:
            if not self.history_path.exists():
                return
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self.chat_history = data[-500:]
        except Exception as exc:
            self.console.print(f"[bold yellow]History load failed: {exc}[/]")

    def _save_history(self) -> None:
        """Persist chat history to disk."""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            payload = self.chat_history[-500:]
            self.history_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            self.console.print(f"[bold yellow]History save failed: {exc}[/]")

    def _export_history(self, path: Path) -> None:
        """Export chat history as Markdown."""
        lines = ["# MyCoder Chat History", ""]
        for entry in self.chat_history:
            ts = entry.get("timestamp", "")
            role = entry.get("role", "unknown").upper()
            lines.append(f"## [{ts}] {role}")
            lines.append(entry.get("content", ""))
            lines.append("")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")

    def _scroll_history(self, delta: int) -> None:
        """Scroll chat history by a delta."""
        self.history_offset = max(0, self.history_offset + delta)
        self._refresh_live()

    def _refresh_live(self) -> None:
        """Refresh the live UI if available."""
        if not self._live:
            return
        try:
            self._live.update(self._create_layout())
            self._live.refresh()
        except Exception:
            return

    def _log_activity(
        self, action: str, target: str = "", status: str = "done"
    ) -> None:
        """Map legacy action strings to activity entries."""
        action_key = action.upper()
        activity_type = ActivityType.TOOL_CALL
        description = action.replace("_", " ").title()

        if action_key in {"QUERY_INIT", "RESPONSE_OK"}:
            activity_type = ActivityType.API_CALL
            description = "AI request" if action_key == "QUERY_INIT" else "AI response"
        elif action_key in {"CMD_EXEC", "EXEC_TOOL"}:
            activity_type = ActivityType.TOOL_CALL
            description = "Command" if action_key == "CMD_EXEC" else "Tool"
        elif action_key == "PROVIDER_SWITCH":
            activity_type = ActivityType.API_CALL
            description = "Provider switch"
        elif action_key == "WEB":
            activity_type = ActivityType.TOOL_CALL
            description = "Web"
        elif action_key == "PLAN":
            activity_type = ActivityType.TOOL_CALL
            description = "Plan"
        elif action_key == "AGENT":
            activity_type = ActivityType.TOOL_CALL
            description = "Agent"
        elif action_key == "SELF_EVOLVE":
            activity_type = ActivityType.TOOL_CALL
            description = "Self-evolve"
        elif action_key == "TTS":
            activity_type = ActivityType.TOOL_CALL
            description = "TTS"

        self.activity_panel.add_activity(
            Activity(
                type=activity_type,
                description=description,
                target=target,
                status=status,
            )
        )

    def _build_execution_context(self) -> ToolExecutionContext:
        """Build execution context for tool execution (v2.2.0)."""
        from pathlib import Path

        return ToolExecutionContext(
            mode="FULL",
            working_directory=self.working_directory,
            session_id=None,
            thermal_status=None,
            network_status={"connected": True},
            metadata={"ui_mode": "interactive"},
        )

    def _display_tool_result(self, result) -> None:
        """Display tool execution result to chat history (v2.2.0)."""
        if result.success:
            # Format successful result
            output_text = f"**Tool: {result.tool_name}**\n\n"
            output_text += f"Duration: {result.duration_ms}ms\n\n"
            if result.metadata.get("verified_path"):
                output_text += f"Verified path: {result.metadata['verified_path']}\n\n"

            if result.data:
                if isinstance(result.data, dict):
                    # Format dict data nicely
                    if "stdout" in result.data:
                        output_text += f"```\n{result.data['stdout']}\n```"
                    elif "output" in result.data:
                        output_text += f"```\n{result.data['output']}\n```"
                    else:
                        output_text += (
                            f"```json\n{json.dumps(result.data, indent=2)}\n```"
                        )
                else:
                    output_text += f"```\n{result.data}\n```"

            self._append_chat_entry("system", output_text)
        else:
            # Display error
            error_text = f"**Tool Error: {result.tool_name}**\n\n"
            error_text += f"Error: {result.error}\n"
            error_text += f"Duration: {result.duration_ms}ms"

            self._append_chat_entry("system", error_text)

    async def _configure_provider(self) -> None:
        """Guide the user through selecting and configuring an AI provider."""
        self._show_providers()
        choices = [option["key"] for option in self._provider_options()]
        default_choice = (
            self.active_provider if self.active_provider in choices else choices[0]
        )
        selected = await self._select_provider(choices, default_choice)
        self.active_provider = selected
        self.preferred_provider = self._map_provider(selected)
        self.config.preferred_provider = selected
        if selected == "inception_mercury" and not self.realtime_mode:
            self.diffusing_mode = False
            self.config_dict.setdefault("inception_mercury", {})["api_key"] = None
            self.config_dict["inception_mercury"]["enabled"] = True
            self.config_dict.setdefault("claude_oauth", {})["enabled"] = False

        if selected == "ollama_remote":
            urls = Prompt.ask(
                "Zadej Ollama remote URL adresy (oddeleno carkou, Enter=skip)",
                default="",
            )
            if urls.strip():
                self.config.ollama_remote_urls = [
                    item.strip() for item in urls.split(",") if item.strip()
                ]

        if selected == "ollama_local":
            current_base = (
                self.config.ollama_local.base_url if self.config.ollama_local else ""
            )
            base_url = Prompt.ask(
                "Zadej Ollama local URL (Enter=nechat)",
                default=current_base or "",
            )
            if base_url.strip():
                self.config_dict.setdefault("ollama_local", {})[
                    "base_url"
                ] = base_url.strip()

        if selected == "termux_ollama":
            current_base = (
                self.config.termux_ollama.base_url if self.config.termux_ollama else ""
            )
            base_url = Prompt.ask(
                "Zadej Termux Ollama URL (Enter=nechat)",
                default=current_base or "",
            )
            if base_url.strip():
                self.config_dict.setdefault("termux_ollama", {})[
                    "base_url"
                ] = base_url.strip()

        for option in self._provider_options():
            if option["key"] != selected:
                continue
            if option["api_key"]:
                current = self.config_dict.get(option["key"], {})
                current_key = current.get("api_key")
                if current_key:
                    self.console.print(
                        f"[{COLOR_INFO}]API klic uz je ulozen, ponechavam.[/]"
                    )
                    continue
                prompt_label = (
                    "API klic (Enter=nechat, '-'=smazat)"
                    if current_key
                    else "API klic (Enter=preskocit)"
                )
                api_key = Prompt.ask(prompt_label, password=True, default="")
                if api_key.strip() == "-":
                    self.config_dict.setdefault(option["key"], {})["api_key"] = None
                    self.config_dict[option["key"]]["enabled"] = True
                elif api_key.strip():
                    self.config_dict.setdefault(option["key"], {})[
                        "api_key"
                    ] = api_key.strip()
                    self.config_dict[option["key"]]["enabled"] = True
            else:
                if option["key"] in {"claude_oauth", "ollama_local", "termux_ollama"}:
                    self.config_dict.setdefault(option["key"], {})["enabled"] = True

        self.context_manager.save_config(self.config_dict)
        self.coder = EnhancedMyCoderV2(
            working_directory=self.working_directory, config=self.config_dict
        )
        self._log_activity("PROVIDER_SWITCH", self.active_provider)

    async def _select_provider(self, choices: List[str], default_choice: str) -> str:
        """Prompt the user to select a provider, with optional tab cycling."""
        if not pt_prompt:
            return Prompt.ask(
                "Vyber preferovaneho providera",
                choices=choices,
                default=default_choice,
            )

        index = choices.index(default_choice)
        key_bindings = KeyBindings()
        session = PromptSession()

        @key_bindings.add("tab")
        def _next_choice(event):
            nonlocal index
            index = (index + 1) % len(choices)
            buffer = event.app.current_buffer
            buffer.text = choices[index]
            buffer.cursor_position = len(buffer.text)

        @key_bindings.add("s-tab")
        def _prev_choice(event):
            nonlocal index
            index = (index - 1) % len(choices)
            buffer = event.app.current_buffer
            buffer.text = choices[index]
            buffer.cursor_position = len(buffer.text)

        def toolbar():
            return (
                "Tab/Shift+Tab meni volbu, Enter potvrdi. "
                f"Aktualni: {choices[index]}"
            )

        value = (
            await session.prompt_async(
                "Vyber preferovaneho providera: ",
                default=choices[index],
                key_bindings=key_bindings,
                bottom_toolbar=toolbar,
            )
        ).strip()
        return value if value in choices else choices[index]

    async def handle_slash_command(self, command: str) -> None:
        """Execute slash commands such as /status, /setup, and /exit."""
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]
        self._log_activity("CMD_EXEC", cmd)

        if cmd in ["/exit", "/quit", "/q"]:
            sys.exit(0)
        elif cmd == "/help":
            self.show_help()
        elif cmd == "/status":
            self._append_chat_entry("system", "System status displayed")
            self.show_status()
        elif cmd == "/init":
            self._handle_init_command(args)
        elif cmd == "/diffon":
            if self.active_provider == "inception_mercury" and not self.realtime_mode:
                self.console.print(
                    f"[{COLOR_INFO}]Diffusing vyzaduje /realtime u Mercury.[/]"
                )
                return
            self.diffusing_mode = True
            self.console.print(f"[{COLOR_SUCCESS}]Diffusing Mode: ACTIVATED[/]")
        elif cmd == "/diffoff":
            self.diffusing_mode = False
            self.console.print(f"[{COLOR_INFO}]Diffusing Mode: DEACTIVATED[/]")
        elif cmd == "/realtime":
            self.realtime_mode = not self.realtime_mode
            status = "ACTIVATED" if self.realtime_mode else "DEACTIVATED"
            self.console.print(f"[{COLOR_SUCCESS}]Realtime Mode: {status}[/]")
        elif cmd == "/tools":
            self.list_tools()
        elif cmd == "/providers":
            self._show_providers()
        elif cmd == "/setup":
            await self._configure_provider()
        elif cmd == "/history":
            if not args:
                self.console.print(
                    "[bold red]Usage: /history save|clear|export <path>|prev|next|home|end[/]"
                )
                return
            action = args[0].lower()
            if action == "save":
                self._save_history()
                self.console.print(f"[{COLOR_SUCCESS}]History saved.[/]")
            elif action == "clear":
                self.chat_history.clear()
                self.history_offset = 0
                self._save_history()
                self.console.print(f"[{COLOR_SUCCESS}]History cleared.[/]")
            elif action == "export":
                if len(args) < 2:
                    self.console.print("[bold red]Usage: /history export <path>[/]")
                    return
                export_path = Path(args[1]).expanduser()
                self._export_history(export_path)
                self.console.print(
                    f"[{COLOR_SUCCESS}]History exported to {export_path}[/]"
                )
            elif action == "prev":
                self._scroll_history(self.history_step)
            elif action == "next":
                self._scroll_history(-self.history_step)
            elif action == "home":
                self.history_offset = max(0, len(self.chat_history) - 1)
                self._refresh_live()
            elif action == "end":
                self.history_offset = 0
                self._refresh_live()
            else:
                self.console.print(
                    "[bold red]Usage: /history save|clear|export <path>|prev|next|home|end[/]"
                )
                return
        elif cmd == "/autoexec":
            if not args:
                status = (
                    "ON"
                    if not self.auto_executor.require_confirmation
                    else "OFF (confirm)"
                )
                self.console.print(f"[{COLOR_INFO}]Auto-execute: {status}[/]")
                return
            action = args[0].lower()
            if action == "on":
                self.auto_executor.require_confirmation = False
                self.console.print(
                    f"[{COLOR_SUCCESS}]Auto-execute: ON (no confirmation)[/]"
                )
            elif action == "off":
                self.auto_executor.require_confirmation = True
                self.console.print(
                    f"[{COLOR_SUCCESS}]Auto-execute: OFF (will confirm)[/]"
                )
            elif action == "confirm":
                self.auto_executor.require_confirmation = True
                self.console.print(f"[{COLOR_SUCCESS}]Auto-execute: CONFIRM mode[/]")
            else:
                self.console.print("[bold red]Usage: /autoexec on|off|confirm[/]")
                return
        elif cmd == "/self-evolve":
            if not args:
                self.console.print(
                    "[bold red]Usage: /self-evolve propose|issue <desc>|apply <id>|dry-run <id>|status|show <id>[/]"
                )
                return
            action = args[0].lower()
            if action == "propose":
                self.console.print(
                    f"[{COLOR_INFO}]Running self-evolve diagnostics and proposal...[/]"
                )
                self._log_activity("SELF_EVOLVE", "propose")
                proposal = await self.self_evolve_manager.propose()
                if proposal is None:
                    self.console.print(
                        f"[{COLOR_SUCCESS}]No failing tests detected. No proposal generated.[/]"
                    )
                    return
                if proposal.status == "failed":
                    self.console.print(
                        f"[bold red]Proposal failed:[/] {proposal.error or 'Unknown error'}"
                    )
                    return
                self.console.print(
                    f"[{COLOR_SUCCESS}]Proposal ready:[/] {proposal.proposal_id}"
                )
                if proposal.summary:
                    self.console.print(f"[{COLOR_INFO}]Summary:[/] {proposal.summary}")
                if proposal.rationale:
                    self.console.print(
                        f"[{COLOR_INFO}]Rationale:[/] {proposal.rationale}"
                    )
                if proposal.risk_notes:
                    risk_pct = proposal.risk_score * 100
                    self.console.print(
                        f"[{COLOR_INFO}]Risk:[/] {risk_pct:.0f}% ({', '.join(proposal.risk_notes)})"
                    )
                self.console.print(
                    f"[{COLOR_INFO}]Review diff with /self-evolve show {proposal.proposal_id}[/]"
                )
            elif action == "apply":
                if len(args) < 2:
                    self.console.print(
                        "[bold red]Usage: /self-evolve apply <proposal_id>[/]"
                    )
                    return
                proposal_id = args[1]
                self.console.print(
                    f"[{COLOR_INFO}]Applying proposal {proposal_id} and running tests...[/]"
                )
                self._log_activity("SELF_EVOLVE", f"apply:{proposal_id}")
                result = await self.self_evolve_manager.apply(
                    proposal_id,
                    require_approval=True,
                    approval_callback=self._self_evolve_approval,
                )
                status = result.status.replace("_", " ")
                self.console.print(f"[{COLOR_SUCCESS}]Self-evolve result:[/] {status}")
                if result.risk_notes:
                    risk_pct = result.risk_score * 100
                    self.console.print(
                        f"[{COLOR_INFO}]Risk:[/] {risk_pct:.0f}% ({', '.join(result.risk_notes)})"
                    )
                if result.error:
                    self.console.print(f"[bold red]Error:[/] {result.error}")
            elif action == "dry-run":
                if len(args) < 2:
                    self.console.print(
                        "[bold red]Usage: /self-evolve dry-run <proposal_id>[/]"
                    )
                    return
                proposal_id = args[1]
                self.console.print(
                    f"[{COLOR_INFO}]Running dry-run for proposal {proposal_id}...[/]"
                )
                self._log_activity("SELF_EVOLVE", f"dry-run:{proposal_id}")
                try:
                    result = await self.self_evolve_manager.dry_run(proposal_id)
                except ValueError as exc:
                    self.console.print(f"[bold red]{exc}[/]")
                    return
                if not result.get("success", False):
                    error = result.get("error")
                    if error:
                        self.console.print(f"[bold red]Dry-run failed:[/] {error}")
                    else:
                        self.console.print("[bold red]Dry-run tests failed.[/]")
                else:
                    self.console.print("[bold green]Dry-run succeeded.[/]")
                test_results = result.get("test_results") or {}
                results = test_results.get("results") or []
                failures = [r for r in results if r.get("exit_code") != 0]
                if results:
                    self.console.print(
                        f"[{COLOR_INFO}]Tests:[/] {len(results)} commands, {len(failures)} failures"
                    )
                affected = result.get("affected_files") or []
                if affected:
                    self.console.print(
                        f"[{COLOR_INFO}]Affected files:[/] {', '.join(affected)}"
                    )
            elif action == "issue":
                if len(args) < 2:
                    self.console.print(
                        "[bold red]Usage: /self-evolve issue <description>[/]"
                    )
                    return
                issue_text = " ".join(args[1:]).strip()
                self.console.print(
                    f"[{COLOR_INFO}]Creating proposal from user issue...[/]"
                )
                self._log_activity("SELF_EVOLVE", "issue")
                proposal = await self.self_evolve_manager.propose_from_issue(issue_text)
                if proposal.status == "failed":
                    self.console.print(
                        f"[bold red]Proposal failed:[/] {proposal.error or 'Unknown error'}"
                    )
                    return
                self.console.print(
                    f"[{COLOR_SUCCESS}]Proposal ready:[/] {proposal.proposal_id}"
                )
                if proposal.summary:
                    self.console.print(f"[{COLOR_INFO}]Summary:[/] {proposal.summary}")
                if proposal.rationale:
                    self.console.print(
                        f"[{COLOR_INFO}]Rationale:[/] {proposal.rationale}"
                    )
                if proposal.risk_notes:
                    risk_pct = proposal.risk_score * 100
                    self.console.print(
                        f"[{COLOR_INFO}]Risk:[/] {risk_pct:.0f}% ({', '.join(proposal.risk_notes)})"
                    )
                self.console.print(
                    f"[{COLOR_INFO}]Review diff with /self-evolve show {proposal.proposal_id}[/]"
                )
            elif action == "status":
                proposals = self.self_evolve_manager.list_proposals()
                if not proposals:
                    self.console.print(
                        f"[{COLOR_INFO}]No self-evolve proposals found.[/]"
                    )
                    return
                table = Table(title="Self-Evolve Proposals", box=box.ROUNDED)
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Status", style="white")
                table.add_column("Summary", style="green")
                table.add_column("Created", style="magenta")
                for proposal in proposals[-10:]:
                    table.add_row(
                        proposal.proposal_id,
                        proposal.status,
                        proposal.summary or "-",
                        proposal.created_at,
                    )
                self.console.print(table)
            elif action == "show":
                if len(args) < 2:
                    self.console.print(
                        "[bold red]Usage: /self-evolve show <proposal_id>[/]"
                    )
                    return
                proposal_id = args[1]
                diff = self.self_evolve_manager.show_patch(proposal_id)
                if not diff:
                    self.console.print(
                        f"[bold red]Proposal not found:[/] {proposal_id}"
                    )
                    return
                self.console.print(Markdown(f"```diff\n{diff}\n```"))
            else:
                self.console.print(
                    "[bold red]Usage: /self-evolve propose|issue <desc>|apply <id>|dry-run <id>|status|show <id>[/]"
                )
                return
        elif cmd == "/plan":
            if not args:
                self.console.print(
                    "[bold red]Usage: /plan <task> | /plan approve | /plan cancel | /plan execute | /plan show[/]"
                )
                return
            action = args[0].lower()
            if action in {"approve", "cancel", "execute", "show"}:
                if action == "show":
                    if not self.plan_content:
                        self.console.print(f"[{COLOR_INFO}]No active plan.[/]")
                        return
                    self.console.print(Markdown(self.plan_content))
                    return
                if action == "cancel":
                    self.plan_task = None
                    self.plan_content = None
                    self.plan_status = "idle"
                    self.console.print(f"[{COLOR_SUCCESS}]Plan cleared.[/]")
                    return
                if action == "approve":
                    if not self.plan_content:
                        self.console.print(f"[{COLOR_INFO}]No plan to approve.[/]")
                        return
                    self.plan_status = "approved"
                    self.console.print(f"[{COLOR_SUCCESS}]Plan approved.[/]")
                    return
                if action == "execute":
                    if not self.plan_content:
                        self.console.print(f"[{COLOR_INFO}]No plan to execute.[/]")
                        return
                    if self.plan_status != "approved":
                        self.console.print(
                            "[bold red]Plan is not approved. Use /plan approve first.[/]"
                        )
                        return
                    confirm = Confirm.ask(
                        "Execute the approved plan now?", default=False
                    )
                    if not confirm:
                        self.console.print("[yellow]Cancelled.[/]")
                        return
                    execution_prompt = (
                        "Execute this plan step-by-step. Ask before any destructive action.\n\n"
                        f"{self.plan_content}"
                    )
                    self.console.print(f"[{COLOR_INFO}]Executing approved plan...[/]")
                    self._log_activity("PLAN", "execute")
                    await self.process_chat(execution_prompt)
                    return
            task = " ".join(args).strip()
            if not task:
                self.console.print("[bold red]Usage: /plan <task>[/]")
                return
            self.plan_task = task
            self.plan_status = "pending"
            plan_prompt = self._build_plan_prompt(task)
            self.console.print(f"[{COLOR_INFO}]Generating plan for: {task}[/]")
            self._log_activity("PLAN", "generate")
            with self.console.status(
                "[bold magenta]Generuji plan...[/]", spinner="dots"
            ):
                response = await self.coder.process_request(
                    plan_prompt,
                    preferred_provider=self.preferred_provider,
                    use_tools=False,
                )
            content = (
                response.get("content", str(response))
                if isinstance(response, dict)
                else str(response)
            )
            self.plan_content = content
            self._append_chat_entry("ai", content)
            self.console.print(Markdown(content))
        elif cmd == "/agent":
            if not args:
                self.console.print(
                    "[bold red]Usage: /agent explore <task> | /agent plan <task> | /agent bash <command> | /agent general <task>[/]"
                )
                return
            agent_key = args[0].lower()
            task = " ".join(args[1:]).strip()
            if not task:
                self.console.print("[bold red]Task/command is required.[/]")
                return
            context = {"agent": agent_key}
            if agent_key == "explore":
                agent_type = AgentType.EXPLORE
            elif agent_key == "plan":
                agent_type = AgentType.PLAN
            elif agent_key == "bash":
                agent_type = AgentType.BASH
            elif agent_key == "general":
                agent_type = AgentType.GENERAL
            else:
                self.console.print("[bold red]Unknown agent type.[/]")
                return
            self._log_activity("AGENT", agent_key)
            result = await self.agent_orchestrator.get_agent(agent_type).execute(
                task, context=context
            )
            if result.success:
                self.console.print(result.content)
                self._append_chat_entry("ai", result.content)
            else:
                self.console.print(f"[bold red]{result.error or 'Agent failed'}[/]")
        elif cmd == "/web":
            if not args:
                self.console.print(
                    "[bold red]Usage: /web fetch <url> [prompt] | /web search <query>[/]"
                )
                return
            action = args[0].lower()
            if action == "fetch":
                if len(args) < 2:
                    self.console.print("[bold red]Usage: /web fetch <url> [prompt][/]")
                    return
                url = args[1]
                prompt = " ".join(args[2:]).strip()
                self._log_activity("WEB", f"fetch:{url}")
                result = await self.web_fetcher.fetch(url, prompt=prompt)
                if not result.get("success"):
                    self.console.print(
                        f"[bold red]Fetch failed:[/] {result.get('error', 'Unknown error')}"
                    )
                    return
                content = result.get("content", "")
                self.console.print(content)
                self._append_chat_entry("ai", content)
            elif action == "search":
                query = " ".join(args[1:]).strip()
                if not query:
                    self.console.print("[bold red]Usage: /web search <query>[/]")
                    return
                self._log_activity("WEB", "search")
                results = await self.web_searcher.search(query)
                if not results:
                    self.console.print(f"[{COLOR_INFO}]No results.[/]")
                    return
                for item in results:
                    self.console.print(
                        f"- {item.title}\n  {item.url}\n  {item.snippet}"
                    )
            else:
                self.console.print(
                    "[bold red]Usage: /web fetch <url> [prompt] | /web search <query>[/]"
                )
                return
        elif cmd == "/mcp":
            if not args:
                self.console.print(
                    "[bold red]Usage: /mcp connect <url> | /mcp tools | /mcp call <tool> <json>[/]"
                )
                return
            action = args[0].lower()
            if action == "connect":
                if len(args) < 2:
                    self.console.print("[bold red]Usage: /mcp connect <url>[/]")
                    return
                url = args[1]
                self.mcp_bridge = MCPBridge(mcp_url=url, auto_start=False)
                self.console.print(f"[{COLOR_INFO}]Connecting to MCP at {url}...[/]")
                if await self.mcp_bridge.initialize():
                    self.console.print(f"[{COLOR_SUCCESS}]MCP connected.[/]")
                else:
                    self.console.print("[bold red]MCP connect failed.[/]")
            elif action == "tools":
                bridge = self.mcp_bridge or getattr(self.coder, "mcp_bridge", None)
                if not bridge:
                    self.console.print("[bold red]MCP bridge not initialized.[/]")
                    return
                if not bridge.is_initialized:
                    if not await bridge.initialize():
                        self.console.print("[bold red]MCP init failed.[/]")
                        return
                tools = bridge.mcp_tools or {}
                if not tools:
                    self.console.print(f"[{COLOR_INFO}]No MCP tools available.[/]")
                    return
                for name, info in tools.items():
                    desc = info.get("description") or ""
                    self.console.print(f"- {name}: {desc}")
            elif action == "call":
                if len(args) < 3:
                    self.console.print("[bold red]Usage: /mcp call <tool> <json>[/]")
                    return
                tool_name = args[1]
                payload = " ".join(args[2:]).strip()
                try:
                    arguments = json.loads(payload)
                except json.JSONDecodeError as exc:
                    self.console.print(f"[bold red]Invalid JSON:[/] {exc}")
                    return
                bridge = self.mcp_bridge or getattr(self.coder, "mcp_bridge", None)
                if not bridge:
                    self.console.print("[bold red]MCP bridge not initialized.[/]")
                    return
                if not bridge.is_initialized:
                    if not await bridge.initialize():
                        self.console.print("[bold red]MCP init failed.[/]")
                        return
                result = await bridge.call_mcp_tool(tool_name, arguments)
                self.console.print(str(result))
            else:
                self.console.print(
                    "[bold red]Usage: /mcp connect <url> | /mcp tools | /mcp call <tool> <json>[/]"
                )
                return
        elif cmd == "/todo":
            if not args:
                items = self.todo_tracker.list_items()
                if not items:
                    self.console.print(f"[{COLOR_INFO}]No todo items.[/]")
                    return
                table = Table(title="Todo List", box=box.ROUNDED)
                table.add_column("#", style="cyan", no_wrap=True)
                table.add_column("Status", style="white")
                table.add_column("Task", style="green")
                for idx, item in enumerate(items, start=1):
                    table.add_row(str(idx), item.status, item.task)
                self.console.print(table)
                return
            action = args[0].lower()
            if action == "add":
                if len(args) < 2:
                    self.console.print("[bold red]Usage: /todo add <task>[/]")
                    return
                task = " ".join(args[1:])
                try:
                    item = self.todo_tracker.add(task)
                except ValueError as exc:
                    self.console.print(f"[bold red]{exc}[/]")
                    return
                self.console.print(f"[{COLOR_SUCCESS}]Added:[/] {item.task}")
            elif action == "done":
                if len(args) < 2:
                    self.console.print("[bold red]Usage: /todo done <n>[/]")
                    return
                try:
                    item = self.todo_tracker.done(int(args[1]))
                except (ValueError, IndexError) as exc:
                    self.console.print(f"[bold red]{exc}[/]")
                    return
                self.console.print(f"[{COLOR_SUCCESS}]Done:[/] {item.task}")
            elif action == "start":
                if len(args) < 2:
                    self.console.print("[bold red]Usage: /todo start <n>[/]")
                    return
                try:
                    item = self.todo_tracker.start(int(args[1]))
                except (ValueError, IndexError) as exc:
                    self.console.print(f"[bold red]{exc}[/]")
                    return
                self.console.print(f"[{COLOR_SUCCESS}]In progress:[/] {item.task}")
            elif action == "clear":
                removed = self.todo_tracker.clear_done()
                self.console.print(
                    f"[{COLOR_SUCCESS}]Cleared {removed} done item(s).[/]"
                )
            else:
                self.console.print(
                    "[bold red]Usage: /todo | /todo add <task> | /todo start <n> | /todo done <n> | /todo clear[/]"
                )
                return
        elif cmd == "/speak":
            if not self.tts_engine:
                self.console.print(
                    "[bold red]TTS not enabled. Set text_to_speech.enabled=true in config[/]"
                )
                return
            text = " ".join(args) if args else "Test ceskeho hlasu"
            await self.tts_engine.speak_async(text)
            self._log_activity("TTS", text[:30])
            self.console.print(f"[{COLOR_SUCCESS}]Speaking: {text}[/]")
        elif cmd == "/voice":
            if not args:
                self.console.print("[bold red]Usage: /voice start|stop|status[/]")
                return

            action = args[0].lower()
            if action not in {"start", "stop", "status"}:
                self.console.print("[bold red]Usage: /voice start|stop|status[/]")
                return
            from .command_parser import Command

            command = Command(
                tool="voice_dictation",
                args={"mode": "gui", "action": action},
                raw_input=f"/voice {action}",
            )

            if (
                hasattr(self.coder, "tool_orchestrator")
                and self.coder.tool_orchestrator
            ):
                result = await self.coder.tool_orchestrator.execute_command(
                    command, self._build_execution_context()
                )
                if result.success:
                    if action == "start":
                        message = (
                            "Voice dictation started. Press Ctrl+Shift+Space to record."
                        )
                    elif action == "stop":
                        message = "Voice dictation stopped."
                    else:
                        message = f"Voice dictation status: {result.data}"
                    self.console.print(f"[{COLOR_SUCCESS}]{message}[/]")
                else:
                    self.console.print(f"[bold red]Error: {result.error}[/]")
            else:
                self.console.print("[bold yellow]Tool orchestrator not initialized.[/]")
        elif cmd == "/clear":
            self.console.clear()
            self.print_banner()
        else:
            self.console.print(f"[bold red]Unknown command: {cmd}[/]")

    def show_help(self) -> None:
        """Display available slash commands and their actions."""
        table = Table(title="Commands", box=box.ROUNDED, border_style=COLOR_BORDER)
        table.add_column("Command", style="green")
        table.add_column("Action", style="white")
        table.add_row("/status", "Show system flags")
        table.add_row("/diffon | /diffoff", "Toggle Mercury Diffusion")
        table.add_row("/realtime", "Toggle Realtime")
        table.add_row("/tools", "List tools")
        table.add_row("/providers", "List AI providers")
        table.add_row("/setup", "Configure provider & API key")
        table.add_row("/init ...", "Initialize project guide file")
        table.add_row("/history ...", "Save/export/scroll chat history")
        table.add_row("/autoexec ...", "Toggle auto-execute confirmations")
        table.add_row(
            "/self-evolve ...",
            "Self-evolve (propose|issue <desc>|apply <id>|status|show <id>)",
        )
        table.add_row("/plan ...", "Plan mode (create/approve/show/execute)")
        table.add_row("/todo ...", "Todo list tracking")
        table.add_row("/edit ...", "Edit file with unique match validation")
        table.add_row("/agent ...", "Run specialized agent (explore/plan/bash/general)")
        table.add_row("/web ...", "Web fetch/search tools")
        table.add_row("/mcp ...", "MCP connect/tools/call")
        table.add_row("/voice start|stop|status", "Voice dictation control")
        table.add_row("/speak <text>", "Text-to-speech playback")
        table.add_row("/exit", "Shutdown")
        self.console.print(table)

    def show_status(self) -> None:
        """Render the system status panel with key flags."""
        status = f"""
        [bold cyan]System:[/bold cyan] ONLINE
        [bold white]Provider:[/bold white] {self.active_provider}
        [bold magenta]Diffusing:[/bold magenta] {self.diffusing_mode}
        [bold magenta]Realtime:[/bold magenta] {self.realtime_mode}
        [yellow]Thermal:[/yellow] DISABLED (Silent)
        """
        self.console.print(
            Panel(status.strip(), title="System Status", border_style="blue")
        )

    def list_tools(self) -> None:
        """List loaded tools or a placeholder count if unavailable."""
        # Placeholder for visual feedback until tool registry is fully linked
        tools = (
            self.coder.tool_registry.list_tools()
            if hasattr(self.coder, "tool_registry")
            else {}
        )
        self.console.print(f"[italic]Registered Tools: {len(tools)}[/italic]")

    async def process_chat(self, user_input: str) -> Optional[str]:
        """Send the user's query to the coder, append the assistant response, and return it."""
        self.activity_panel.add_activity(
            Activity(
                type=ActivityType.API_CALL,
                description=f"Query {self.active_provider}",
                target="User request",
                status="running",
            )
        )
        self.activity_panel.set_operation("Generating AI response...", 0)
        progress_task = asyncio.create_task(self._update_progress_simulation())
        stream_text = ""

        def _stream_handler(chunk: str) -> None:
            nonlocal stream_text
            if not chunk:
                return
            stream_text += chunk
            if len(stream_text) > 1000:
                stream_text = stream_text[-1000:]
            self.activity_panel.set_thinking(stream_text)
            self._refresh_live()

        with self.console.status(
            "[bold magenta]Přemýšlím a generuji kód...[/]", spinner="dots"
        ):
            try:
                response = await self.coder.process_request(
                    user_input,
                    files=self._default_context_files() or None,
                    diffusing=self.diffusing_mode,
                    realtime=self.realtime_mode,
                    preferred_provider=self.preferred_provider,
                    stream_callback=_stream_handler,
                )
                content = (
                    response.get("content", str(response))
                    if isinstance(response, dict)
                    else str(response)
                )
                self._append_chat_entry("ai", content)
                self._log_activity("RESPONSE_OK", f"{len(content)} chars")
                if self.tts_engine and getattr(self.config, "text_to_speech", {}).get(
                    "auto_read_responses", False
                ):
                    plain_text = self._strip_markdown(content)
                    await self.tts_engine.speak_async(plain_text)
                if content:

                    async def _confirm_action(action):
                        return self._prompt_confirm(
                            f"[yellow]Execute: {action.description}?[/]",
                            default=False,
                        )

                    async def _execute_action(action):
                        if action.type == ActionType.CREATE_FILE:
                            if action.content is None:
                                return False
                            target_path = self.working_directory / Path(action.target)
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            if (
                                hasattr(self.coder, "tool_orchestrator")
                                and self.coder.tool_orchestrator
                            ):
                                command = Command(
                                    tool="file_write",
                                    args={
                                        "path": str(target_path),
                                        "content": action.content,
                                    },
                                    raw_input="",
                                )
                                result = (
                                    await self.coder.tool_orchestrator.execute_command(
                                        command, self._build_execution_context()
                                    )
                                )
                                self._display_tool_result(result)
                                return result.success
                            target_path.write_text(action.content, encoding="utf-8")
                            return True
                        if action.type in {
                            ActionType.RUN_COMMAND,
                            ActionType.INSTALL_PACKAGE,
                        }:
                            if (
                                not hasattr(self.coder, "tool_orchestrator")
                                or not self.coder.tool_orchestrator
                            ):
                                self.console.print(
                                    "[bold yellow]Tool orchestrator not initialized.[/]"
                                )
                                return False
                            command = Command(
                                tool="terminal_exec",
                                args={"command": action.target},
                                raw_input="",
                            )
                            result = await self.coder.tool_orchestrator.execute_command(
                                command, self._build_execution_context()
                            )
                            self._display_tool_result(result)
                            return result.success
                        return False

                    await self.auto_executor.process_response(
                        content,
                        confirm_callback=_confirm_action,
                        execute_callback=_execute_action,
                    )
                return content
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                self.activity_panel.add_activity(
                    Activity(
                        type=ActivityType.API_CALL,
                        description="AI response error",
                        target=str(e),
                        status="error",
                    )
                )
                return None
            finally:
                self.activity_panel.clear_operation()
                self.activity_panel.clear_thinking()
                progress_task.cancel()
                with suppress(asyncio.CancelledError):
                    await progress_task

    async def _update_progress_simulation(self) -> None:
        """Simulate progress updates while waiting for AI response."""
        for i in range(0, 101, 10):
            await asyncio.sleep(0.3)
            self.activity_panel.update_progress(i)

    def _strip_markdown(self, text: str) -> str:
        """Strip markdown formatting for TTS output."""
        # Bolt Optimization: Use pre-compiled regexes
        text = MD_CODE_BLOCK_REGEX.sub("", text)
        text = MD_INLINE_CODE_REGEX.sub("", text)
        text = MD_STYLE_REGEX.sub("", text)
        text = MD_HEADER_REGEX.sub("", text)
        return text.strip()

    def _create_layout(self) -> Layout:
        """Build the split-screen layout, falling back to single-column on narrow terminals."""
        terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
        if terminal_width < 80:
            if not self._warned_small_terminal:
                self.console.print(
                    "[bold yellow]Terminal width < 80 columns, using compact layout[/bold yellow]"
                )
                self._warned_small_terminal = True
            compact_layout = Layout(name="main")
            compact_layout.update(
                Group(
                    self._render_chat_panel(),
                    self.activity_panel.render(self.console),
                )
            )
            return compact_layout

        layout = Layout()
        layout.split_row(
            Layout(name="chat", ratio=60),
            Layout(name="monitor", ratio=40),
        )
        layout["chat"].update(self._render_chat_panel())
        layout["monitor"].update(self.activity_panel.render(self.console))
        return layout

    def _estimate_message_height(
        self, entry: Dict[str, str], content_width: int
    ) -> int:
        """
        Conservatively estimate how many terminal lines this message will consume.

        Uses defensive calculation that counts newlines and applies safety buffers
        to prevent overflow during rendering.

        Args:
            entry: Chat message entry with 'role' and 'content'
            content_width: Available width for content rendering

        Returns:
            Estimated line count (always rounds up for safety)
        """
        content = entry["content"]
        role = entry["role"]

        # Start with header line (timestamp + role label)
        lines = 1

        # Count explicit newlines - critical for code blocks and lists
        newline_count = content.count("\n")

        # Calculate wrapped lines based on content length
        # Use effective width (slightly less than actual to account for padding)
        effective_width = max(30, content_width - 4)
        char_based_lines = max(1, len(content) // effective_width)

        # Take the MAXIMUM of newline-based and char-based estimates
        # This handles both long single-line text and multi-line code blocks
        content_lines = max(newline_count + 1, char_based_lines)

        # Apply role-specific safety multipliers
        if role == "ai":
            # AI messages use Markdown which adds significant overhead:
            # - Code blocks add borders and syntax highlighting
            # - Lists add bullet points and indentation
            # - Headers add extra spacing
            # - Tables add grid lines
            # Use 1.5x multiplier + fixed buffer of 3 lines
            content_lines = int(content_lines * 1.5) + 3

            # Additional penalty for very long AI responses
            if len(content) > 1000:
                content_lines += 2
        else:
            # User/system messages are plain text, but still add buffer
            content_lines = int(content_lines * 1.1) + 1

        lines += content_lines

        # Separator line
        lines += 1

        # Add small buffer per message to account for Rich rendering quirks
        lines += 1

        return lines

    def _render_chat_panel(self) -> Panel:
        """
        Render chat history with conservative height calculation.

        Uses defensive sizing with newline counting and generous safety buffers
        to prevent overflow even with complex Markdown content.

        Returns:
            Panel containing formatted chat history with separators
        """
        # Get terminal dimensions
        term_height = self.console.size.height
        term_width = self.console.size.width

        # Calculate available height for chat content - CONSERVATIVE APPROACH
        # Panel decorations breakdown:
        #   - Top border: 1
        #   - Title line: 1
        #   - Top padding: 1
        #   - Bottom padding: 1
        #   - Bottom border: 1
        #   - Safety buffer for overflow indicator: 2
        #   - Extra safety margin: 2
        PANEL_OVERHEAD = 9  # Increased from 5 to be more defensive
        available_lines = max(5, term_height - PANEL_OVERHEAD)

        # Apply safety factor: only use 85% of calculated available space
        # This accounts for Rich's internal rendering overhead
        safe_available_lines = int(available_lines * 0.85)

        # Content width inside panel (accounting for borders + padding + margins)
        content_width = max(30, term_width - 10)  # Increased from 8 to 10

        # Separator configuration
        def separator_line() -> Text:
            """Return a horizontal separator line for chat messages."""
            return Text("─" * min(60, content_width), style="dim white")

        # Handle empty history
        if not self.chat_history:
            return Panel(
                Text("Waiting for input...", style=COLOR_INFO),
                title="[bold green]💬 CHAT SESSION[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
                expand=True,
            )

        # Build visible history from newest to oldest until we run out of space
        visible_history = []
        consumed_lines = 0

        # Reserve space for overflow indicator (if needed)
        OVERFLOW_INDICATOR_LINES = 3
        working_space = safe_available_lines - OVERFLOW_INDICATOR_LINES
        total_messages = len(self.chat_history)
        max_offset = max(0, total_messages - 1)
        self.history_offset = min(max(self.history_offset, 0), max_offset)
        visible_source = self.chat_history[: total_messages - self.history_offset]

        # Iterate backwards through history
        for entry in reversed(visible_source):
            estimated_lines = self._estimate_message_height(entry, content_width)

            # Strict check: stop BEFORE we exceed limit (defensive)
            if consumed_lines + estimated_lines >= working_space:
                break

            visible_history.insert(0, entry)  # Insert at front to maintain order
            consumed_lines += estimated_lines

            # Hard limit: never show more than 15 messages regardless of space
            # This prevents performance issues with rapid re-rendering
            if len(visible_history) >= 15:
                break

        # Ensure we show at least the most recent message (emergency fallback)
        if not visible_history and visible_source:
            visible_history = [visible_source[-1]]

        # Calculate overflow indicator
        overflow = len(visible_source) - len(visible_history)

        # Build renderable content
        renderables: List = []

        if self.history_offset > 0:
            renderables.append(
                Text(
                    f"[... {self.history_offset} newer messages hidden ...]",
                    style="dim italic",
                    justify="center",
                )
            )
            renderables.append(separator_line())

        # Add overflow indicator if needed
        if overflow > 0:
            renderables.append(
                Text(
                    f"[... {overflow} starších zpráv skryto ...]",
                    style="dim italic",
                    justify="center",
                )
            )
            renderables.append(separator_line())

        # Render each visible message
        for index, entry in enumerate(visible_history):
            role = entry["role"]
            content = entry["content"]
            ts = entry["timestamp"]

            # Determine styling based on role
            if role == "user":
                header_style = "bold green"
                header_label = "You"
                body_renderable = Text(content, style="white")
            elif role == "ai":
                header_style = "bold cyan"
                header_label = "MyCoder AI"

                # Split content into thinking and response blocks
                # Bolt Optimization: Use pre-compiled regex
                parts = THINKING_REGEX.split(content)

                ai_content_group = []

                for part in parts:
                    if part.startswith("<thinking>") and part.endswith("</thinking>"):
                        thought_content = part[10:-11].strip()
                        if not thought_content:
                            continue

                        if self.show_thinking:
                            # Expanded view
                            ai_content_group.append(
                                Panel(
                                    Markdown(thought_content),
                                    title="Chain of Thought",
                                    border_style="dim blue",
                                    title_align="left",
                                    expand=False,
                                )
                            )
                        else:
                            # Collapsed view
                            summary = thought_content[:60].replace("\n", " ") + "..."
                            ai_content_group.append(
                                Panel(
                                    Text(
                                        f"Thinking: {summary}", style="dim italic blue"
                                    ),
                                    border_style="dim blue",
                                    expand=False,
                                )
                            )
                    else:
                        if not part.strip():
                            continue
                        try:
                            ai_content_group.append(Markdown(part))
                        except Exception:
                            ai_content_group.append(Text(part, style="cyan"))

                body_renderable = Group(*ai_content_group)

            else:  # system
                header_style = "bold yellow"
                header_label = "System"
                body_renderable = Text(content, style="italic yellow")

            # Add message header
            renderables.append(Text(f"[{ts}] {header_label}:", style=header_style))

            # Add message body
            renderables.append(body_renderable)

            # Add separator (except after last message)
            if index != len(visible_history) - 1:
                renderables.append(separator_line())

        return Panel(
            Group(*renderables),
            title="[bold green]💬 CHAT SESSION[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=True,
        )

    async def run(self) -> None:
        """Main run loop that renders the layout and handles user input."""
        self.print_banner()
        await self._configure_provider()
        session = None
        if PromptSession and KeyBindings:
            key_bindings = KeyBindings()

            @key_bindings.add("pageup")
            def _scroll_up(event):
                self._scroll_history(self.history_step)

            @key_bindings.add("pagedown")
            def _scroll_down(event):
                self._scroll_history(-self.history_step)

            @key_bindings.add("home")
            def _scroll_top(event):
                self.history_offset = max(0, len(self.chat_history) - 1)
                self._refresh_live()

            @key_bindings.add("end")
            def _scroll_bottom(event):
                self.history_offset = 0
                self._refresh_live()

            @key_bindings.add("c-t")
            def _toggle_thinking(event):
                self.show_thinking = not self.show_thinking
                self._refresh_live()

            session = PromptSession(key_bindings=key_bindings)
        try:
            with Live(
                self._create_layout(),
                console=self.console,
                refresh_per_second=4,
                screen=False,
            ) as live:
                self._live = live
                while True:
                    live.update(self._create_layout())
                    live.stop()
                    if session:
                        user_input = (await session.prompt_async("You> ")).strip()
                    else:
                        user_input = Prompt.ask(f"[{COLOR_USER}]You[/]").strip()
                    live.start()
                    if not user_input:
                        continue

                    # NEW (v2.2.0): Parse and execute tool commands
                    if user_input.startswith("/"):
                        command = self.command_parser.parse(user_input)

                        if command:
                            # Tool command (e.g., /bash, /file, /git)
                            self._log_activity("EXEC_TOOL", command.tool)

                            # Execute tool if orchestrator is available
                            if (
                                hasattr(self.coder, "tool_orchestrator")
                                and self.coder.tool_orchestrator
                            ):
                                try:
                                    result = await self.coder.tool_orchestrator.execute_command(
                                        command, self._build_execution_context()
                                    )
                                    self._display_tool_result(result)
                                except Exception as e:
                                    self.console.print(
                                        f"[bold red]Tool execution error: {e}[/]"
                                    )
                            else:
                                self.console.print(
                                    f"[bold yellow]Tool orchestrator not initialized. Run in initialized mode.[/]"
                                )

                            live.update(self._create_layout())
                            live.refresh()
                            continue

                        # Slash command (existing logic for /exit, /help, etc.)
                        await self.handle_slash_command(user_input)
                        live.update(self._create_layout())
                        live.refresh()
                        continue
                    self._append_chat_entry("user", user_input)
                    live.update(self._create_layout())
                    live.refresh()
                    await self.process_chat(user_input)
                    live.update(self._create_layout())
                    live.refresh()
        except (KeyboardInterrupt, EOFError):
            self.console.print(
                "\n[bold yellow]⛔ Shutting down MyCoder... Goodbye![/bold yellow]"
            )
        finally:
            self._live = None


def main():
    try:
        asyncio.run(InteractiveCLI().run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
