import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency during runtime
    psutil = None


class ActivityType(Enum):
    FILE_CREATE = "file_create"
    FILE_EDIT = "file_edit"
    FILE_READ = "file_read"
    BASH_EXEC = "bash_exec"
    THINKING = "thinking"
    API_CALL = "api_call"
    TOOL_CALL = "tool_call"


@dataclass
class Activity:
    type: ActivityType
    description: str
    target: str = ""
    status: str = "pending"
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0


class ActivityPanel:
    """Real-time activity tracking panel for MyCoder UI."""

    def __init__(self, max_activities: int = 10) -> None:
        self.activities: List[Activity] = []
        self.max_activities = max_activities
        self.current_operation: Optional[str] = None
        self.current_progress: int = 0
        self.thinking_text: str = ""
        self.files_modified: List[str] = []
        self.files_created: List[str] = []

        # Bolt Optimization: Cache system metrics to reduce IO in render loop
        self._last_metrics_time = 0.0
        self._cached_metrics_str = "[dim]SYS | CPU: 0% | RAM: 0% | TEMP: N/A[/]"

    def add_activity(self, activity: Activity) -> None:
        """Add new activity and trim old ones."""
        self.activities.append(activity)
        self.activities = self.activities[-self.max_activities :]

        if activity.type == ActivityType.FILE_CREATE:
            if activity.target and activity.target not in self.files_created:
                self.files_created.append(activity.target)
        elif activity.type == ActivityType.FILE_EDIT:
            if activity.target and activity.target not in self.files_modified:
                self.files_modified.append(activity.target)

    def add_log(self, action: str, resource: str = "") -> None:
        """Compatibility helper for older log-style calls."""
        self.add_activity(
            Activity(
                type=ActivityType.TOOL_CALL,
                description=action.replace("_", " ").title(),
                target=resource,
                status="done",
            )
        )

    def set_thinking(self, text: str) -> None:
        """Update thinking/reasoning display."""
        self.thinking_text = text[-200:]

    def clear_thinking(self) -> None:
        self.thinking_text = ""

    def set_operation(self, operation: str, progress: int = 0) -> None:
        self.current_operation = operation
        self.current_progress = progress

    def update_progress(self, progress: int) -> None:
        self.current_progress = min(100, max(0, progress))

    def clear_operation(self) -> None:
        self.current_operation = None
        self.current_progress = 0

    def render(self, console: Console) -> Panel:
        """Render the activity panel."""
        renderables: List[str] = []

        if self.current_operation:
            progress_bar = self._render_progress_bar(self.current_progress)
            renderables.append(
                f"[bold cyan]>>> {self.current_operation}[/]\n"
                f"{progress_bar} {self.current_progress}%"
            )
            renderables.append("")

        if self.thinking_text:
            renderables.append("[bold magenta]Thinking:[/]")
            renderables.append(f"[dim italic]{self.thinking_text}...[/]")
            renderables.append("")

        if self.files_created or self.files_modified:
            renderables.append("[bold green]Files Changed:[/]")
            for path in self.files_created[-5:]:
                renderables.append(f"  [green]+ {path}[/]")
            for path in self.files_modified[-5:]:
                renderables.append(f"  [yellow]~ {path}[/]")
            renderables.append("")

        renderables.append("[bold cyan]Recent Activity:[/]")
        if not self.activities:
            renderables.append("[dim]No activity yet[/]")
        else:
            for act in self.activities[-6:]:
                icon = self._get_activity_icon(act.type)
                status_color = self._get_status_color(act.status)
                time_str = act.timestamp.strftime("%H:%M:%S")
                target_short = act.target[-30:] if len(act.target) > 30 else act.target
                renderables.append(
                    f"[dim]{time_str}[/] {icon} "
                    f"[{status_color}]{act.description}[/] {target_short}"
                )

        renderables.append("")
        renderables.append(self._render_system_metrics())

        content = "\n".join(renderables)

        return Panel(
            content,
            title="[bold cyan]ACTIVITY[/]",
            border_style="cyan",
            box=box.ROUNDED,
            expand=True,
        )

    def _render_progress_bar(self, percent: int) -> str:
        filled = int(percent / 5)
        empty = 20 - filled
        return f"[green]{'=' * filled}[/][dim]{'.' * empty}[/]"

    def _render_system_metrics(self) -> str:
        # Bolt Optimization: Return cached metrics if within TTL (2s)
        current_time = time.time()
        if current_time - self._last_metrics_time < 2.0:
            return self._cached_metrics_str

        if not psutil:
            return "[dim]SYS | CPU: N/A | RAM: N/A | TEMP: N/A[/]"
        try:
            cpu = psutil.cpu_percent(interval=None)
        except Exception:
            cpu = 0.0
        try:
            ram = psutil.virtual_memory().percent
        except Exception:
            ram = 0.0

        self._cached_metrics_str = (
            f"[dim]SYS | CPU: {cpu:.0f}% | RAM: {ram:.0f}% | TEMP: N/A[/]"
        )
        self._last_metrics_time = current_time
        return self._cached_metrics_str

    def _get_activity_icon(self, activity_type: ActivityType) -> str:
        icons = {
            ActivityType.FILE_CREATE: "[green]+[/]",
            ActivityType.FILE_EDIT: "[yellow]~[/]",
            ActivityType.FILE_READ: "[blue]>[/]",
            ActivityType.BASH_EXEC: "[magenta]$[/]",
            ActivityType.THINKING: "[cyan]?[/]",
            ActivityType.API_CALL: "[white]@[/]",
            ActivityType.TOOL_CALL: "[cyan]#[/]",
        }
        return icons.get(activity_type, "[dim].[/]")

    def _get_status_color(self, status: str) -> str:
        colors = {
            "pending": "dim",
            "running": "yellow",
            "done": "green",
            "error": "red",
        }
        return colors.get(status, "white")
