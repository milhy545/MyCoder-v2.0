"""
Interactive terminal interface for MyCoder v2.0 styled after Gemini CLI vibes.
"""

import asyncio
import os
import sys
from typing import List, Optional

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich import box
except ImportError:
    print("Chyba: Knihovna 'rich' není nainstalována.")
    print("Nainstaluj ji pomocí: poetry add rich (nebo pip install rich)")
    sys.exit(1)

try:
    from src.enhanced_mycoder_v2 import EnhancedMyCoderV2
    from src.config_manager import ConfigManager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.enhanced_mycoder_v2 import EnhancedMyCoderV2  # noqa: F401
    from src.config_manager import ConfigManager  # noqa: F401

COLOR_SYSTEM = "bold cyan"
COLOR_USER = "bold green"
COLOR_AI = "white"
COLOR_ERROR = "bold red"
COLOR_SUCCESS = "bold magenta"
COLOR_INFO = "italic yellow"
COLOR_BORDER = "blue"


class InteractiveCLI:
    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()
        os.environ["MYCODER_THERMAL_ENABLED"] = "false"
        self.coder = EnhancedMyCoderV2()
        self.diffusing_mode = True
        self.realtime_mode = False
        self.active_provider = "inception_mercury"

    def print_banner(self):
        banner_text = """
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
                Text(banner_text, justify="center", style="bold magenta"),
                border_style=COLOR_BORDER,
                box=box.HEAVY,
            )
        )

    async def handle_slash_command(self, command: str):
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ["/exit", "/quit", "/q"]:
            self.console.print("[bold red]Odpojování systému...[/bold red]")
            sys.exit(0)
        elif cmd == "/help":
            self.show_help()
        elif cmd == "/setup":
            self.interactive_setup()
        elif cmd == "/status":
            self.show_status()
        elif cmd == "/diffon":
            self.diffusing_mode = True
            self.console.print(
                f"[{COLOR_SUCCESS}]Diffusing Mode: ACTIVATED (Mercury)[/{COLOR_SUCCESS}]"
            )
        elif cmd == "/diffoff":
            self.diffusing_mode = False
            self.console.print(
                f"[{COLOR_INFO}]Diffusing Mode: DEACTIVATED[/{COLOR_INFO}]"
            )
        elif cmd == "/realtime":
            self.realtime_mode = not self.realtime_mode
            status = "ACTIVATED" if self.realtime_mode else "DEACTIVATED"
            color = COLOR_SUCCESS if self.realtime_mode else COLOR_INFO
            self.console.print(
                f"[{color}]Realtime Mode: {status}[/{color}]"
            )
        elif cmd == "/provider":
            if args:
                self.active_provider = args[0]
                self.console.print(
                    f"[{COLOR_SUCCESS}]Provider switched to: {self.active_provider}[/{COLOR_SUCCESS}]"
                )
            else:
                self.console.print(
                    f"[{COLOR_INFO}]Current provider: {self.active_provider}. Use /provider <name> to change.[/{COLOR_INFO}]"
                )
        elif cmd == "/tools":
            self.list_tools()
        elif cmd == "/clear":
            self.console.clear()
            self.print_banner()
        else:
            self.console.print(f"[{COLOR_ERROR}]Neznámý příkaz: {cmd}[/{COLOR_ERROR}]")

    def show_help(self):
        table = Table(title="Dostupné Příkazy", box=box.ROUNDED, border_style=COLOR_BORDER)
        table.add_column("Příkaz", style="bold green")
        table.add_column("Popis", style="white")
        table.add_row("/setup", "Interaktivní konfigurace systému")
        table.add_row("/status", "Zobrazit aktuální stav a nastavení")
        table.add_row("/diffon / /diffoff", "Přepnout Mercury Diffusion mód")
        table.add_row("/realtime", "Přepnout Realtime mód")
        table.add_row("/tools", "Seznam dostupných nástrojů")
        table.add_row("/provider <name>", "Přepnout AI providera")
        table.add_row("/clear", "Vyčistit terminál")
        table.add_row("/exit", "Ukončit MyCoder")
        self.console.print(table)

    def list_tools(self):
        try:
            tools = self.coder.tool_registry.list_tools()
        except AttributeError:
            tools = [
                {"name": "system_check", "description": "Checks system health"},
                {"name": "run_script", "description": "Executes scripts"},
            ]
        table = Table(
            title="System Tools Registry",
            box=box.SIMPLE_HEAD,
            border_style="magenta",
        )
        table.add_column("Tool Name", style="cyan")
        table.add_column("Description", style="dim white")
        if isinstance(tools, dict):
            for name, tool in tools.items():
                desc = tool.description if hasattr(tool, "description") else str(tool)
                table.add_row(name, desc)
        elif isinstance(tools, list):
            for tool in tools:
                if isinstance(tool, dict):
                    table.add_row(tool.get("name", "N/A"), tool.get("description", ""))
                else:
                    table.add_row(str(tool), "")
        self.console.print(table)

    def show_status(self):
        status_text = Text()
        status_text.append("System: ", style="bold cyan")
        status_text.append("ONLINE\n", style="bold green")
        status_text.append(f"Active Provider: {self.active_provider}\n", style="white")
        status_text.append(
            f"Diffusing Mode: {'ON' if self.diffusing_mode else 'OFF'}\n", style="magenta"
        )
        status_text.append(
            f"Realtime Mode: {'ON' if self.realtime_mode else 'OFF'}\n", style="magenta"
        )
        thermal_status = (
            "DISABLED (Silent)"
            if os.environ.get("MYCODER_THERMAL_ENABLED") == "false"
            else "ACTIVE"
        )
        status_text.append(f"Thermal Monitor: {thermal_status}", style="yellow")
        self.console.print(
            Panel(status_text, title="System Status", border_style="blue")
        )

    def interactive_setup(self):
        self.console.print(Panel("[bold]System Configuration[/bold]", style="cyan"))
        current_thermal = os.environ.get("MYCODER_THERMAL_ENABLED", "true")
        self.console.print(f"Current Thermal Monitor: {current_thermal}")
        choice = Prompt.ask("Enable Thermal Monitor? (y/n)", choices=["y", "n"], default="n")
        if choice == "y":
            os.environ["MYCODER_THERMAL_ENABLED"] = "true"
            self.console.print("[green]Thermal Monitor ENABLED[/green]")
        else:
            os.environ["MYCODER_THERMAL_ENABLED"] = "false"
            self.console.print("[yellow]Thermal Monitor DISABLED[/yellow]")

    async def process_chat(self, user_input: str):
        with self.console.status(
            "[bold magenta]MyCoder is processing...[/bold magenta]", spinner="dots12"
        ):
            try:
                response = await self.coder.process_request(
                    user_input,
                    diffusing=self.diffusing_mode,
                    realtime=self.realtime_mode,
                )
                content = response
                if isinstance(response, dict):
                    content = response.get("content", str(response))
                self.console.print()
                self.console.print(
                    Panel(
                        Markdown(str(content)),
                        title="MyCoder v2.0",
                        border_style="green",
                        box=box.ROUNDED,
                    )
                )
                self.console.print()
            except Exception as e:
                self.console.print(f"[{COLOR_ERROR}]System Error: {str(e)}[/{COLOR_ERROR}]")

    async def run(self):
        self.print_banner()
        self.console.print(
            f"[{COLOR_INFO}]Type /help for commands. Start typing to chat.[/{COLOR_INFO}]"
        )
        while True:
            try:
                user_input = Prompt.ask(f"[{COLOR_USER}]You[/{COLOR_USER}]")
                if not user_input:
                    continue
                if user_input.startswith("/"):
                    await self.handle_slash_command(user_input)
                else:
                    await self.process_chat(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                self.console.print("\n[bold red]Ukončování...[/bold red]")
                break


if __name__ == "__main__":
    cli = InteractiveCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass
