# CODEX TASK: MyCoder UI/UX Improvements

## Overview

MyCoder v2.1.1 má funkční CLI, ale UI/UX má kritické nedostatky oproti Claude Code CLI. Tento task opravuje tyto problémy.

## Zjištěné problémy

### 1. Scrollování v chatu
- Rich's `Live` display nepodporuje mouse wheel scrolling
- Pouze `/history prev|next` - nepohodlné
- Uživatel nevidí starší zprávy bez manuálního scrollu

### 2. Pravý panel (ExecutionMonitor) je k ničemu
- Zobrazuje: `TIME | ACTION FLOW | RESOURCE` + CPU/RAM/Thermal
- Uživatel chce vidět: **co se vytváří, edituje, thinking**
- Žádný progress bar pro dlouhé operace

### 3. AI neexekutuje akce automaticky
- Mercury/Claude vrací text "vytvořím soubor X"
- Ale soubor se nevytvoří - uživatel musí manuálně `/file write`
- Claude Code automaticky parsuje odpověď a vykonává tool calls

### 4. Chybí live streaming výstupu
- Uživatel nevidí thinking process
- Nevidí co AI právě dělá
- Jen čeká na finální odpověď

---

## TASK 1: Activity Panel (nahrazení ExecutionMonitor)

### Cíl
Nahradit pravý panel za **Activity Panel** který zobrazuje reálnou aktivitu.

### Specifikace

**Soubor:** `src/mycoder/ui_activity_panel.py` (nový)

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console, Group
from rich import box

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
    target: str = ""  # file path, command, etc.
    status: str = "pending"  # pending, running, done, error
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0

class ActivityPanel:
    """Real-time activity tracking panel for MyCoder UI."""

    def __init__(self, max_activities: int = 10):
        self.activities: List[Activity] = []
        self.max_activities = max_activities
        self.current_operation: Optional[str] = None
        self.current_progress: int = 0
        self.thinking_text: str = ""
        self.files_modified: List[str] = []
        self.files_created: List[str] = []

    def add_activity(self, activity: Activity) -> None:
        """Add new activity and trim old ones."""
        self.activities.append(activity)
        self.activities = self.activities[-self.max_activities:]

        # Track file changes
        if activity.type == ActivityType.FILE_CREATE:
            if activity.target not in self.files_created:
                self.files_created.append(activity.target)
        elif activity.type == ActivityType.FILE_EDIT:
            if activity.target not in self.files_modified:
                self.files_modified.append(activity.target)

    def set_thinking(self, text: str) -> None:
        """Update thinking/reasoning display."""
        self.thinking_text = text[-200:]  # Last 200 chars

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
        renderables = []

        # 1. Current Operation with Progress
        if self.current_operation:
            progress_bar = self._render_progress_bar(self.current_progress)
            renderables.append(
                f"[bold cyan]>>> {self.current_operation}[/]\n{progress_bar} {self.current_progress}%"
            )
            renderables.append("")

        # 2. Thinking Section (if active)
        if self.thinking_text:
            renderables.append("[bold magenta]Thinking:[/]")
            renderables.append(f"[dim italic]{self.thinking_text}...[/]")
            renderables.append("")

        # 3. Files Changed This Session
        if self.files_created or self.files_modified:
            renderables.append("[bold green]Files Changed:[/]")
            for f in self.files_created[-5:]:
                renderables.append(f"  [green]+ {f}[/]")
            for f in self.files_modified[-5:]:
                renderables.append(f"  [yellow]~ {f}[/]")
            renderables.append("")

        # 4. Recent Activity Log
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
                    f"[dim]{time_str}[/] {icon} [{status_color}]{act.description}[/] {target_short}"
                )

        content = "\n".join(str(r) for r in renderables)

        return Panel(
            content,
            title="[bold cyan]ACTIVITY[/]",
            border_style="cyan",
            box=box.ROUNDED,
            expand=True,
        )

    def _render_progress_bar(self, percent: int) -> str:
        filled = int(percent / 5)  # 20 char bar
        empty = 20 - filled
        return f"[green]{'█' * filled}[/][dim]{'░' * empty}[/]"

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
        return icons.get(activity_type, "[dim]·[/]")

    def _get_status_color(self, status: str) -> str:
        colors = {
            "pending": "dim",
            "running": "yellow",
            "done": "green",
            "error": "red",
        }
        return colors.get(status, "white")
```

### Integrace do cli_interactive.py

```python
# Nahradit import a inicializaci
from .ui_activity_panel import ActivityPanel, Activity, ActivityType

# V __init__:
self.activity_panel = ActivityPanel()

# V _create_layout():
layout["monitor"].update(self.activity_panel.render(self.console))

# V process_chat() - přidat tracking:
self.activity_panel.add_activity(Activity(
    type=ActivityType.API_CALL,
    description=f"Query {self.active_provider}",
    status="running"
))
```

---

## TASK 2: Auto-Execute Mode (Claude Code style)

### Cíl
Parsovat AI odpovědi a automaticky vykonávat navrhované akce (s potvrzením).

### Specifikace

**Soubor:** `src/mycoder/auto_executor.py` (nový)

```python
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

class ActionType(Enum):
    CREATE_FILE = "create_file"
    EDIT_FILE = "edit_file"
    RUN_COMMAND = "run_command"
    INSTALL_PACKAGE = "install_package"

@dataclass
class ProposedAction:
    type: ActionType
    target: str  # file path or command
    content: Optional[str] = None  # file content or None
    description: str = ""
    confidence: float = 0.0  # 0-1, how confident we are this is intended

class AIResponseParser:
    """Parse AI responses to extract proposed actions."""

    # Patterns for detecting file creation
    FILE_CREATE_PATTERNS = [
        r"```(?:python|javascript|typescript|bash|sh|json|yaml|toml|md)\n# (?:File: )?([^\n]+)\n([\s\S]*?)```",
        r"(?:vytvoř|create|write)(?: soubor| file)?\s+[`']?([^`'\n]+)[`']?",
        r"# ([a-zA-Z_/]+\.[a-z]+)\n```[\s\S]*?```",
    ]

    # Patterns for bash commands
    COMMAND_PATTERNS = [
        r"```(?:bash|sh|shell)\n([\s\S]*?)```",
        r"spusť[:\s]+`([^`]+)`",
        r"run[:\s]+`([^`]+)`",
    ]

    def parse(self, response: str) -> List[ProposedAction]:
        """Extract all proposed actions from AI response."""
        actions = []

        # 1. Find file creations with content
        actions.extend(self._find_file_creates(response))

        # 2. Find bash commands
        actions.extend(self._find_commands(response))

        # 3. Find package installs
        actions.extend(self._find_installs(response))

        return actions

    def _find_file_creates(self, text: str) -> List[ProposedAction]:
        actions = []

        # Pattern: ```language\n# filename.ext\ncontent```
        pattern = r"```(\w+)\n#\s*(?:File:\s*)?([^\n]+)\n([\s\S]*?)```"
        for match in re.finditer(pattern, text):
            lang, filename, content = match.groups()
            filename = filename.strip()
            if "/" in filename or filename.endswith((".py", ".js", ".ts", ".json", ".md", ".yaml", ".toml")):
                actions.append(ProposedAction(
                    type=ActionType.CREATE_FILE,
                    target=filename,
                    content=content.strip(),
                    description=f"Create {filename}",
                    confidence=0.9
                ))

        return actions

    def _find_commands(self, text: str) -> List[ProposedAction]:
        actions = []

        # Pattern: ```bash\ncommand```
        pattern = r"```(?:bash|sh|shell)\n([\s\S]*?)```"
        for match in re.finditer(pattern, text):
            commands = match.group(1).strip().split("\n")
            for cmd in commands:
                cmd = cmd.strip()
                if cmd and not cmd.startswith("#"):
                    # Skip dangerous commands
                    if self._is_safe_command(cmd):
                        actions.append(ProposedAction(
                            type=ActionType.RUN_COMMAND,
                            target=cmd,
                            description=f"Run: {cmd[:50]}",
                            confidence=0.7
                        ))

        return actions

    def _find_installs(self, text: str) -> List[ProposedAction]:
        actions = []

        patterns = [
            r"pip install\s+([^\n`]+)",
            r"poetry add\s+([^\n`]+)",
            r"npm install\s+([^\n`]+)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                pkg = match.group(1).strip()
                actions.append(ProposedAction(
                    type=ActionType.INSTALL_PACKAGE,
                    target=pkg,
                    description=f"Install: {pkg}",
                    confidence=0.8
                ))

        return actions

    def _is_safe_command(self, cmd: str) -> bool:
        """Check if command is safe to auto-execute."""
        dangerous = ["rm -rf", "sudo rm", "mkfs", "dd if=", "> /dev/", "chmod 777", "curl | bash"]
        cmd_lower = cmd.lower()
        return not any(d in cmd_lower for d in dangerous)


class AutoExecutor:
    """Execute proposed actions with user confirmation."""

    def __init__(self, activity_panel=None, require_confirmation: bool = True):
        self.parser = AIResponseParser()
        self.activity_panel = activity_panel
        self.require_confirmation = require_confirmation
        self.executed_actions: List[ProposedAction] = []

    async def process_response(
        self,
        response: str,
        confirm_callback=None,
        execute_callback=None
    ) -> List[Tuple[ProposedAction, bool]]:
        """
        Process AI response, extract actions, confirm with user, execute.

        Returns list of (action, success) tuples.
        """
        actions = self.parser.parse(response)
        results = []

        for action in actions:
            # Skip low confidence actions
            if action.confidence < 0.5:
                continue

            # Confirm with user if required
            should_execute = True
            if self.require_confirmation and confirm_callback:
                should_execute = await confirm_callback(action)

            if not should_execute:
                results.append((action, False))
                continue

            # Execute action
            success = False
            if execute_callback:
                success = await execute_callback(action)

            results.append((action, success))

            if success:
                self.executed_actions.append(action)
                if self.activity_panel:
                    from .ui_activity_panel import Activity, ActivityType
                    act_type = {
                        ActionType.CREATE_FILE: ActivityType.FILE_CREATE,
                        ActionType.EDIT_FILE: ActivityType.FILE_EDIT,
                        ActionType.RUN_COMMAND: ActivityType.BASH_EXEC,
                        ActionType.INSTALL_PACKAGE: ActivityType.BASH_EXEC,
                    }.get(action.type, ActivityType.TOOL_CALL)

                    self.activity_panel.add_activity(Activity(
                        type=act_type,
                        description=action.description,
                        target=action.target,
                        status="done"
                    ))

        return results
```

### Integrace do cli_interactive.py

```python
from .auto_executor import AutoExecutor, ActionType

# V __init__:
self.auto_executor = AutoExecutor(
    activity_panel=self.activity_panel,
    require_confirmation=True  # Default: ptej se uživatele
)

# V process_chat() po získání response:
async def _confirm_action(action):
    return Confirm.ask(
        f"[yellow]Execute: {action.description}?[/]",
        default=False
    )

async def _execute_action(action):
    if action.type == ActionType.CREATE_FILE:
        path = Path(action.target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(action.content, encoding="utf-8")
        return True
    elif action.type == ActionType.RUN_COMMAND:
        # Use existing bash execution
        result = await self.coder.tool_orchestrator.execute_command(
            Command(tool="terminal_exec", args={"command": action.target}, raw_input=""),
            self._build_execution_context()
        )
        return result.success
    return False

# Po process_chat response:
results = await self.auto_executor.process_response(
    content,
    confirm_callback=_confirm_action,
    execute_callback=_execute_action
)
```

---

## TASK 3: Live Streaming Output

### Cíl
Zobrazovat streaming output z AI v reálném čase (thinking, partial responses).

### Specifikace

**Úprava:** `src/mycoder/api_providers.py` - Mercury a Claude providers

Přidat streaming callback:

```python
# V MercuryProvider.query():
async def query(
    self,
    prompt: str,
    context: Dict[str, Any] = None,
    stream_callback: Optional[Callable[[str], None]] = None,  # NEW
    **kwargs
) -> APIResponse:
    # ... existing code ...

    if payload["stream"]:
        async for line in response.content:
            # Parse SSE
            if line.startswith(b"data: "):
                data = json.loads(line[6:])
                delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta and stream_callback:
                    stream_callback(delta)
                content_accum += delta
```

**Úprava:** `src/mycoder/cli_interactive.py`

```python
# V process_chat():
def _stream_handler(chunk: str):
    self.activity_panel.set_thinking(chunk)
    # Optionally update Live display

response = await self.coder.process_request(
    user_input,
    stream_callback=_stream_handler,  # NEW
    # ... rest
)
```

---

## TASK 4: Keyboard Scroll (lepší alternativa k mouse wheel)

### Cíl
Page Up/Down pro scrollování v chatu (Rich Live nepodporuje mouse wheel).

### Specifikace

**Úprava:** `src/mycoder/cli_interactive.py`

```python
# Přidat key bindings pro scroll
from prompt_toolkit.key_binding import KeyBindings

# V run() před Live loop:
kb = KeyBindings()

@kb.add('pageup')
def scroll_up(event):
    self._scroll_history(5)

@kb.add('pagedown')
def scroll_down(event):
    self._scroll_history(-5)

@kb.add('home')
def scroll_top(event):
    self.history_offset = max(0, len(self.chat_history) - 1)

@kb.add('end')
def scroll_bottom(event):
    self.history_offset = 0

# Použít v PromptSession
session = PromptSession(key_bindings=kb)
user_input = await session.prompt_async(f"[{COLOR_USER}]You[/] ")
```

---

## TASK 5: Auto-Execute Toggle Command

### Specifikace

```python
# Nový slash command /autoexec
elif cmd == "/autoexec":
    if not args:
        status = "ON" if not self.auto_executor.require_confirmation else "OFF (confirm)"
        self.console.print(f"[{COLOR_INFO}]Auto-execute: {status}[/]")
        return

    action = args[0].lower()
    if action == "on":
        self.auto_executor.require_confirmation = False
        self.console.print(f"[{COLOR_SUCCESS}]Auto-execute: ON (no confirmation)[/]")
    elif action == "off":
        self.auto_executor.require_confirmation = True
        self.console.print(f"[{COLOR_SUCCESS}]Auto-execute: OFF (will confirm)[/]")
    elif action == "confirm":
        self.auto_executor.require_confirmation = True
        self.console.print(f"[{COLOR_SUCCESS}]Auto-execute: CONFIRM mode[/]")
```

---

## Soubory k vytvoření/úpravě

### Nové soubory:
1. `src/mycoder/ui_activity_panel.py` - Activity Panel komponenta
2. `src/mycoder/auto_executor.py` - AI response parser + executor

### Úpravy:
1. `src/mycoder/cli_interactive.py`:
   - Import ActivityPanel místo ExecutionMonitor
   - Přidat AutoExecutor
   - Přidat keyboard bindings pro scroll
   - Přidat /autoexec command
   - Přidat stream_callback do process_chat

2. `src/mycoder/api_providers.py`:
   - Přidat stream_callback parameter do query() methods
   - Implementovat streaming pro Mercury a Claude providers

3. `src/mycoder/enhanced_mycoder_v2.py`:
   - Propagovat stream_callback přes process_request()

### Testy:
1. `tests/unit/test_activity_panel.py`
2. `tests/unit/test_auto_executor.py`
3. `tests/unit/test_ai_response_parser.py`

---

## Acceptance Criteria

1. **Activity Panel** zobrazuje:
   - [x] Current operation s progress barem
   - [x] Thinking text (live update)
   - [x] Files created/modified this session
   - [x] Recent activity log s ikonami

2. **Auto-Execute**:
   - [x] Parsuje code blocks s file paths
   - [x] Parsuje bash commands
   - [x] Ptá se na potvrzení (default)
   - [x] `/autoexec on|off|confirm` toggle

3. **Streaming**:
   - [x] Thinking text se zobrazuje live
   - [x] Partial response viditelná před dokončením

4. **Keyboard Scroll**:
   - [x] PageUp/PageDown scrolluje chat
   - [x] Home/End jde na začátek/konec

5. **Testy**:
   - [x] Unit testy pro všechny nové komponenty
   - [x] 100% pass rate

---

## Priority

1. **HIGH**: Activity Panel (Task 1) - okamžitá hodnota
2. **HIGH**: Auto-Execute (Task 2) - klíčová funkce
3. **MEDIUM**: Keyboard Scroll (Task 4) - usability
4. **MEDIUM**: Streaming (Task 3) - nice to have
5. **LOW**: AutoExec Toggle (Task 5) - convenience

---

## Notes pro Codex

- Zachovat kompatibilitu s existujícím kódem
- Použít existující Rich komponenty kde možné
- Testovat s Mercury i Ollama providery
- ActivityPanel musí fungovat i bez AutoExecutor
- Stream callback musí být optional (backward compatible)
