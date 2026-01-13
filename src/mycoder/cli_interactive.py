"""
MyCoder v2.1.0 Interactive CLI
Architecture: Split-screen UI using rich.Live.
Left: Chat History (Auto-scrolling Markdown). Right: Execution Monitor (Logs + Sys Metrics).
"""

import asyncio
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import psutil

# Rich library is now required via poetry
try:
    from rich.align import Align
    from rich.console import Console, Group
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.text import Text
    from rich import box
except ImportError:
    print("CRITICAL: 'rich' library not found. Please run: poetry add rich")
    sys.exit(1)

# Optional prompt_toolkit for Tab-based selection.
try:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit import PromptSession
except ImportError:
    pt_prompt = None
    KeyBindings = None
    PromptSession = None

# Import Core
try:
    from .enhanced_mycoder_v2 import EnhancedMyCoderV2
    from .config_manager import ConfigManager
    from .api_providers import APIProviderType
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from mycoder.enhanced_mycoder_v2 import EnhancedMyCoderV2
    from mycoder.config_manager import ConfigManager
    from mycoder.api_providers import APIProviderType

# CYBERPUNK PALETTE
COLOR_SYSTEM = "bold cyan"
COLOR_USER = "bold green"
COLOR_SUCCESS = "bold magenta"
COLOR_INFO = "italic yellow"
COLOR_BORDER = "blue"


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
            pass
        try:
            metrics["ram"] = psutil.virtual_memory().percent
        except Exception:
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
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.coder = EnhancedMyCoderV2(config=self.config)
        self.diffusing_mode = True
        self.realtime_mode = False
        self.active_provider = self.config.preferred_provider or "ollama_local"
        self.preferred_provider = self._map_provider(self.active_provider)
        self.chat_history: List[Dict[str, str]] = []
        self.monitor = ExecutionMonitor()
        self._warned_small_terminal = False

    def print_banner(self) -> None:
        """Render the stylized MyCoder banner at startup."""
        banner = r"""
    __  ___        ______          __
   /  |/  /_  __  / ____/___  ____/ /__  _____
  / /|_/ / / / / / /   / __ \/ __  / _ \/ ___/
 / /  / / /_/ / / /___/ /_/ / /_/ /  __/ /
/_/  /_/\__, /  \____/\____/\__,_/\___/_/
       /____/
      [ v2.1.0 - AI Powered ]
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
            "ollama_remote": APIProviderType.OLLAMA_REMOTE,
            "inception_mercury": APIProviderType.MERCURY,
        }
        return mapping.get(provider_key)

    def _current_timestamp(self) -> str:
        """Return the current time formatted for chat records."""
        return datetime.now().strftime("%H:%M:%S")

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
        if selected != "claude_oauth":
            self.config_manager.update_provider_config(
                "claude_oauth", {"enabled": False}
            )

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
            base_url = Prompt.ask(
                "Zadej Ollama local URL (Enter=nechat)",
                default=self.config.ollama_local.base_url or "",
            )
            if base_url.strip():
                self.config_manager.update_provider_config(
                    "ollama_local", {"base_url": base_url.strip()}
                )

        for option in self._provider_options():
            if option["key"] != selected:
                continue
            if option["api_key"]:
                current = self.config_manager.get_provider_config(option["key"])
                if current and current.api_key:
                    self.console.print(
                        f"[{COLOR_INFO}]API klic uz je ulozen, ponechavam.[/]"
                    )
                    continue
                prompt_label = (
                    "API klic (Enter=nechat, '-'=smazat)"
                    if current and current.api_key
                    else "API klic (Enter=preskocit)"
                )
                api_key = Prompt.ask(prompt_label, password=True, default="")
                if api_key.strip() == "-":
                    self.config_manager.update_provider_config(
                        option["key"], {"api_key": None, "enabled": True}
                    )
                elif api_key.strip():
                    self.config_manager.update_provider_config(
                        option["key"], {"api_key": api_key.strip(), "enabled": True}
                    )
            else:
                if option["key"] in {"claude_oauth", "ollama_local"}:
                    self.config_manager.update_provider_config(
                        option["key"], {"enabled": True}
                    )

        self.config_manager.save_config()
        self.coder = EnhancedMyCoderV2(config=self.config_manager.config)
        self.monitor.add_log("PROVIDER_SWITCH", self.active_provider)

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
        self.monitor.add_log("CMD_EXEC", cmd)

        if cmd in ["/exit", "/quit", "/q"]:
            sys.exit(0)
        elif cmd == "/help":
            self.show_help()
        elif cmd == "/status":
            self.chat_history.append(
                {
                    "role": "system",
                    "content": "System status displayed",
                    "timestamp": self._current_timestamp(),
                }
            )
            self.show_status()
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
        self.monitor.add_log("QUERY_INIT", "User Request")
        with self.console.status(
            "[bold magenta]Přemýšlím a generuji kód...[/]", spinner="dots"
        ):
            try:
                response = await self.coder.process_request(
                    user_input,
                    diffusing=self.diffusing_mode,
                    realtime=self.realtime_mode,
                    preferred_provider=self.preferred_provider,
                )
                content = (
                    response.get("content", str(response))
                    if isinstance(response, dict)
                    else str(response)
                )
                self.chat_history.append(
                    {
                        "role": "ai",
                        "content": content,
                        "timestamp": self._current_timestamp(),
                    }
                )
                self.monitor.add_log("RESPONSE_OK", f"{len(content)} chars")
                return content
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                return None

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
                    self.monitor.render(self.console),
                )
            )
            return compact_layout

        layout = Layout()
        layout.split_row(
            Layout(name="chat", ratio=60),
            Layout(name="monitor", ratio=40),
        )
        layout["chat"].update(self._render_chat_panel())
        layout["monitor"].update(self.monitor.render(self.console))
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

        # Iterate backwards through history
        for entry in reversed(self.chat_history):
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
        if not visible_history and self.chat_history:
            visible_history = [self.chat_history[-1]]

        # Calculate overflow indicator
        overflow = len(self.chat_history) - len(visible_history)

        # Build renderable content
        renderables: List = []

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
                try:
                    body_renderable = Markdown(content)
                except Exception:
                    # Fallback if markdown fails
                    body_renderable = Text(content, style="cyan")
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
        try:
            with Live(
                self._create_layout(),
                console=self.console,
                refresh_per_second=4,
                screen=False,
            ) as live:
                while True:
                    live.update(self._create_layout())
                    live.stop()
                    user_input = Prompt.ask(f"[{COLOR_USER}]You[/]")
                    live.start()
                    if not user_input:
                        continue
                    if user_input.startswith("/"):
                        await self.handle_slash_command(user_input)
                        live.update(self._create_layout())
                        live.refresh()
                        continue
                    self.chat_history.append(
                        {
                            "role": "user",
                            "content": user_input,
                            "timestamp": self._current_timestamp(),
                        }
                    )
                    live.update(self._create_layout())
                    live.refresh()
                    response_content = await self.process_chat(user_input)
                    live.update(self._create_layout())
                    live.refresh()
        except (KeyboardInterrupt, EOFError):
            self.console.print(
                "\n[bold yellow]⛔ Shutting down MyCoder... Goodbye![/bold yellow]"
            )


def main():
    try:
        asyncio.run(InteractiveCLI().run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
