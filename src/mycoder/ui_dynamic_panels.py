"""
Dynamic UI Panels for MyCoder v2.1.1

Enhanced execution monitor with AI-aware features.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class DynamicExecutionMonitor:
    """
    Enhanced execution monitor with:
    - Progress bars for active operations
    - Provider health dashboard
    - Thermal warnings
    - Cost estimates
    """

    def __init__(self) -> None:
        self.logs: List[Tuple[str, str, str]] = []
        self.max_logs: int = 15

        self.current_operation: Optional[str] = None
        self.progress_percent: int = 0
        self.provider_health: Dict[str, str] = {}
        self.cost_estimate: float = 0.0
        self.thermal_warning: bool = False

    def add_log(self, action: str, resource: str = "") -> None:
        """Add a timestamped entry and trim logs to the configured cap."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logs.append((timestamp, action, resource))
        self.logs = self.logs[-self.max_logs :]

    def set_operation(self, operation: str, progress: int = 0) -> None:
        """Set current operation with progress."""
        self.current_operation = operation
        self.progress_percent = progress

    def update_progress(self, percent: int) -> None:
        """Update progress percentage."""
        self.progress_percent = min(100, max(0, percent))

    def clear_operation(self) -> None:
        """Clear current operation."""
        self.current_operation = None
        self.progress_percent = 0

    def update_provider_health(self, provider: str, status: str) -> None:
        """Update provider health status."""
        self.provider_health[provider] = status

    def set_thermal_warning(self, warning: bool) -> None:
        """Set thermal warning state."""
        self.thermal_warning = warning

    def render(self, console) -> Panel:
        """
        Smart rendering based on current context.

        Priority:
        1. Thermal alert (if warning)
        2. Progress bar (if operation active)
        3. Standard monitoring
        """
        if self.thermal_warning:
            return self._render_thermal_alert()
        if self.current_operation:
            return self._render_with_progress()
        return self._render_standard(console)

    def _render_with_progress(self) -> Panel:
        """Render with progress bar."""
        table = Table.grid(padding=(0, 1))
        table.add_row(Text("OPERATION", style="bold cyan"))
        table.add_row(Text(self.current_operation or "Processing..."))
        table.add_row("")

        progress_bar = self._render_progress_bar(self.progress_percent)
        table.add_row(Text(f"Progress: {progress_bar} {self.progress_percent}%"))
        table.add_row("")

        if self.provider_health:
            table.add_row(Text("PROVIDER HEALTH", style="bold cyan"))
            for provider, status in self.provider_health.items():
                icon = self._get_status_icon(status)
                table.add_row(Text(f"{icon} {provider}: {status}"))
            table.add_row("")

        metrics = self._get_system_metrics()
        table.add_row(Text("SYSTEM", style="bold cyan"))
        table.add_row(
            Text(f"CPU: {self._render_bar(metrics['cpu'])} {metrics['cpu']:.0f}%")
        )
        table.add_row(
            Text(f"RAM: {self._render_bar(metrics['ram'])} {metrics['ram']:.0f}%")
        )
        if metrics["thermal"] != "N/A":
            table.add_row(Text(f"THERMAL: {metrics['thermal']}"))

        return Panel(table, title="EXECUTION MONITOR", border_style="cyan")

    def _render_standard(self, console) -> Panel:
        """Standard rendering (adapted from ExecutionMonitor)."""
        term_height = console.size.height
        term_width = console.size.width

        panel_overhead = 9
        available_rows = max(2, term_height - panel_overhead)
        safe_available_rows = int(available_rows * 0.9)
        max_visible_logs = max(1, safe_available_rows // 2)
        max_visible_logs = min(max_visible_logs, 25)

        visible_logs = self.logs[-max_visible_logs:] if self.logs else []

        table = Table(
            title="OPERATION LOG",
            box=box.ASCII,
            show_header=True,
            show_lines=True,
            expand=False,
            width=max(40, term_width - 6),
            padding=(0, 1),
        )

        time_width = 12
        remaining_width = max(40, term_width - 22)
        action_width = max(18, int(remaining_width * 0.55))
        resource_width = max(12, int(remaining_width * 0.35))

        table.add_column("TIME", width=time_width, style="bold yellow", no_wrap=True)
        table.add_column(
            "ACTION FLOW", width=action_width, style="cyan", overflow="ellipsis"
        )
        table.add_column(
            "RESOURCE", width=resource_width, style="dim white", overflow="ellipsis"
        )

        if not visible_logs:
            table.add_row("-", "No operations yet", "-")
        else:
            for timestamp, action, resource in visible_logs:
                table.add_row(timestamp, action, resource or "-")

        metrics = self._get_system_metrics()
        cpu_bar = self._render_bar(metrics["cpu"])
        ram_bar = self._render_bar(metrics["ram"])

        subtitle = (
            f"SYS | CPU: {cpu_bar} {metrics['cpu']:.0f}% | "
            f"RAM: {ram_bar} {metrics['ram']:.0f}% | "
            f"THERMAL: {metrics['thermal']}"
        )

        return Panel(
            table,
            title="EXECUTION MONITOR",
            border_style="cyan",
            box=box.DOUBLE,
            subtitle=subtitle,
            expand=True,
        )

    def _render_thermal_alert(self) -> Panel:
        """Render thermal warning."""
        table = Table.grid(padding=(0, 1))
        table.add_row(Text("THERMAL WARNING", style="bold red"))
        table.add_row(Text("CPU temperature critical!", style="red"))
        table.add_row(Text("Throttling to local inference...", style="yellow"))

        return Panel(table, title="THERMAL ALERT", border_style="red")

    def _render_progress_bar(self, percent: int) -> str:
        """Render ASCII progress bar."""
        filled = int(percent / 10)
        empty = 10 - filled
        return "=" * filled + "." * empty

    def _render_bar(self, percent: float) -> str:
        """Render metric bar."""
        normalized = max(0.0, min(100.0, percent or 0.0))
        filled = int(round(normalized / 10))
        filled = max(0, min(10, filled))
        empty = 10 - filled
        return "#" * filled + "." * empty

    def _get_status_icon(self, status: str) -> str:
        """Get status icon."""
        icons = {
            "healthy": "OK",
            "degraded": "WARN",
            "unavailable": "DOWN",
        }
        return icons.get(status, "UNK")

    def _get_system_metrics(self) -> dict:
        """Get system metrics."""
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
                        metrics["thermal"] = f"{temp.current:.1f}C"
                    else:
                        metrics["thermal"] = str(temp)
                    break
        except (AttributeError, Exception):
            pass
        return metrics
