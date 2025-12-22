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

# Import Core
try:
    from src.enhanced_mycoder_v2 import EnhancedMyCoderV2
    from src.config_manager import ConfigManager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.enhanced_mycoder_v2 import EnhancedMyCoderV2
    from src.config_manager import ConfigManager

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
        self.coder = EnhancedMyCoderV2()
        self.diffusing_mode = True
        self.realtime_mode = False
        self.active_provider = "inception_mercury"

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
        self.console.print(Panel(Text(banner, justify="center", style="bold magenta"), border_style=COLOR_BORDER, box=box.HEAVY))

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
        elif cmd == "/clear":
            self.console.clear()
            self.print_banner()
        else:
            self.console.print(f"[bold red]Unknown command: {cmd}[/]")

    def show_help(self):
        table = Table(title="Commands", box=box.ROUNDED, border_style=COLOR_BORDER)
        table.add_column("Command", style="green"); table.add_column("Action", style="white")
        table.add_row("/status", "Show system flags")
        table.add_row("/diffon | /diffoff", "Toggle Mercury Diffusion")
        table.add_row("/realtime", "Toggle Realtime")
        table.add_row("/tools", "List tools")
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
        self.console.print(Panel(status.strip(), title="System Status", border_style="blue"))

    def list_tools(self):
        # Placeholder for visual feedback until tool registry is fully linked
        tools = self.coder.tool_registry.list_tools() if hasattr(self.coder, 'tool_registry') else {}
        self.console.print(f"[italic]Registered Tools: {len(tools)}[/italic]")

    async def process_chat(self, user_input: str):
        with self.console.status("[bold magenta]Processing...[/]", spinner="dots12"):
            try:
                response = await self.coder.process_request(
                    user_input, diffusing=self.diffusing_mode, realtime=self.realtime_mode
                )
                content = response.get("content", str(response)) if isinstance(response, dict) else str(response)
                self.console.print(Panel(Markdown(content), title="MyCoder", border_style="green", box=box.ROUNDED))
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")

    async def run(self):
        self.print_banner()
        while True:
            try:
                user_input = Prompt.ask(f"[{COLOR_USER}]You[/]")
                if not user_input: continue
                if user_input.startswith("/"): await self.handle_slash_command(user_input)
                else: await self.process_chat(user_input)
            except (KeyboardInterrupt, EOFError): break

if __name__ == "__main__":
    try:
        asyncio.run(InteractiveCLI().run())
    except KeyboardInterrupt:
        pass
