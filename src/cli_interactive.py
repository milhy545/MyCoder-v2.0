import asyncio
import os
import sys

# Rich library is now required via poetry
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
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
    from src.enhanced_mycoder_v2 import EnhancedMyCoderV2
    from src.config_manager import ConfigManager
    from src.api_providers import APIProviderType
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.enhanced_mycoder_v2 import EnhancedMyCoderV2
    from src.config_manager import ConfigManager
    from src.api_providers import APIProviderType

# CYBERPUNK PALETTE
COLOR_SYSTEM = "bold cyan"
COLOR_USER = "bold green"
COLOR_SUCCESS = "bold magenta"
COLOR_INFO = "italic yellow"
COLOR_BORDER = "blue"


class InteractiveCLI:
    def __init__(self):
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

    def print_banner(self):
        banner = """
███╗   ███╗██╗   ██╗ ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
████╗ ████║╚██╗ ██╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
██╔████╔██║ ╚████╔╝ ██║     ██║   ██║██║  ██║█████╗  ██████╔╝
██║╚██╔╝██║  ╚██╔╝  ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║   ██║   ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
╚═╝     ╚═╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
        v2.0 :: SYSTEM READY :: MERCURY ENGINE LINKED
        """
        self.console.print(
            Panel(
                Text(banner, justify="center", style="bold magenta"),
                border_style=COLOR_BORDER,
                box=box.HEAVY,
            )
        )

    def _provider_options(self):
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

    def _show_providers(self):
        table = Table(title="Supported AI Providers", box=box.ROUNDED)
        table.add_column("Key", style="cyan")
        table.add_column("Provider", style="white")
        table.add_column("API Key", style="yellow")
        for option in self._provider_options():
            api_required = "yes" if option["api_key"] else "no"
            table.add_row(option["key"], option["label"], api_required)
        self.console.print(table)

    def _map_provider(self, provider_key: str):
        mapping = {
            "claude_anthropic": APIProviderType.CLAUDE_ANTHROPIC,
            "claude_oauth": APIProviderType.CLAUDE_OAUTH,
            "gemini": APIProviderType.GEMINI,
            "ollama_local": APIProviderType.OLLAMA_LOCAL,
            "ollama_remote": APIProviderType.OLLAMA_REMOTE,
            "inception_mercury": APIProviderType.MERCURY,
        }
        return mapping.get(provider_key)

    async def _configure_provider(self):
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

    async def _select_provider(self, choices, default_choice):
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

    async def handle_slash_command(self, command: str):
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ["/exit", "/quit", "/q"]:
            sys.exit(0)
        elif cmd == "/help":
            self.show_help()
        elif cmd == "/status":
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

    def show_help(self):
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

    def show_status(self):
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

    def list_tools(self):
        # Placeholder for visual feedback until tool registry is fully linked
        tools = (
            self.coder.tool_registry.list_tools()
            if hasattr(self.coder, "tool_registry")
            else {}
        )
        self.console.print(f"[italic]Registered Tools: {len(tools)}[/italic]")

    async def process_chat(self, user_input: str):
        with self.console.status("[bold magenta]Processing...[/]", spinner="dots12"):
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
                self.console.print(
                    Panel(
                        Markdown(content),
                        title="MyCoder",
                        border_style="green",
                        box=box.ROUNDED,
                    )
                )
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")

    async def run(self):
        self.print_banner()
        await self._configure_provider()
        while True:
            try:
                user_input = Prompt.ask(f"[{COLOR_USER}]You[/]")
                if not user_input:
                    continue
                if user_input.startswith("/"):
                    await self.handle_slash_command(user_input)
                else:
                    await self.process_chat(user_input)
            except (KeyboardInterrupt, EOFError):
                break


def main():
    try:
        asyncio.run(InteractiveCLI().run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
