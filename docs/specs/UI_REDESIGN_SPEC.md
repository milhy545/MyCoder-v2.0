# MyCoder UI Redesign - Professional Layout Spec

## Problem Statement

Current UI has several issues:
- Tool execution results duplicated in chat and activity panel
- Thinking takes too much space (always expanded)
- Panel borders overlap causing rendering artifacts
- Unclear separation between conversation and system activity

## Professional UI Design

Inspired by: VS Code, Claude Desktop, GitHub Copilot Chat

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MyCoder v2.2.0                                      │
├─────────────────────────────────────┬───────────────────────────────────────┤
│           CHAT (60%)                │        ACTIVITY (40%)                 │
│                                     │                                       │
│  Clean conversation flow            │  Live operations & metrics           │
│  - User messages                    │  - Tool execution cards              │
│  - AI responses                     │  - Progress indicators               │
│  - Collapsed thinking               │  - System metrics                    │
│  - NO tool results here             │  - Recent activity log               │
│                                     │                                       │
└─────────────────────────────────────┴───────────────────────────────────────┘
```

### Left Panel: CHAT (Pure Conversation)

**What goes here:**
- User prompts with timestamp
- AI responses (markdown rendered)
- Collapsed "Thinking" sections (expandable)
- Confirmation prompts (Y/n)

**What does NOT go here:**
- Tool execution results
- File contents
- System logs
- Progress bars

**Example:**
```
[16:49:21] You:
Aktualizuj mi Python balíčky

[16:49:23] MyCoder:
Našel jsem pyproject.toml s následujícími závislostmi:
- rich ^13.7.0
- aiohttp ^3.9.0
...

▸ Thinking (2 steps)

Chceš spustit `poetry update`? [Y/n]
```

### Right Panel: ACTIVITY (Live Operations)

**Tool Execution Cards:**
```
┌─────────────────────────────┐
│ 🔄 /read pyproject.toml     │
│ ✓ Completed in 0.2s         │
│ 1,234 chars read            │
└─────────────────────────────┘

┌─────────────────────────────┐
│ ⏳ /read requirements.txt   │
│ In progress...              │
└─────────────────────────────┘
```

**System Metrics:**
```
SYS  CPU: 45% ▂▄▆█
     RAM: 52% ▂▃▄▅
     TEMP: N/A
```

**Recent Activity Log:**
```
Recent Activity:
16:49:23 ✓ Tool /read
16:49:22 @ AI response 4,936 chars
16:49:21 @ Query received
```

---

## Component Breakdown

### 1. Thinking Component

**State:** Collapsed by default
**Expandable:** Click to toggle

```python
class ThinkingComponent:
    def __init__(self, steps: List[str], collapsed: bool = True):
        self.steps = steps
        self.collapsed = collapsed

    def render(self) -> Panel:
        if self.collapsed:
            return Panel(
                Text(f"▸ Thinking ({len(self.steps)} steps)", style="dim italic"),
                border_style="dim",
                expand=False
            )
        else:
            content = "\n".join(f"• {step}" for step in self.steps)
            return Panel(
                Text(content, style="italic yellow"),
                title="▾ Thinking",
                border_style="yellow"
            )
```

**Keybinding:**
- `Space` or `Enter` on thinking line → toggle expand/collapse

### 2. Tool Card Component

**States:** pending ⏳, success ✓, error ✗

```python
@dataclass
class ToolCard:
    tool_name: str
    status: Literal["pending", "success", "error"]
    duration_ms: Optional[int] = None
    result_summary: Optional[str] = None  # "1,234 chars read"

    def render(self) -> Panel:
        icon = {"pending": "⏳", "success": "✓", "error": "✗"}[self.status]
        color = {"pending": "yellow", "success": "green", "error": "red"}[self.status]

        content = f"{icon} {self.tool_name}"
        if self.duration_ms:
            content += f"\n✓ Completed in {self.duration_ms/1000:.1f}s"
        if self.result_summary:
            content += f"\n{self.result_summary}"

        return Panel(
            Text(content),
            border_style=color,
            padding=(0, 1)
        )
```

### 3. Activity Panel Component

**Max cards shown:** 5 (auto-scroll to latest)

```python
class ActivityPanel:
    def __init__(self):
        self.tool_cards: List[ToolCard] = []
        self.max_cards = 5

    def add_tool(self, tool: ToolCard):
        self.tool_cards.append(tool)
        if len(self.tool_cards) > self.max_cards:
            self.tool_cards.pop(0)  # Remove oldest

    def render(self) -> Panel:
        # Tool cards
        cards = [card.render() for card in self.tool_cards[-5:]]

        # System metrics
        metrics = self._render_metrics()

        # Recent activity log
        activity_log = self._render_activity_log()

        return Panel(
            Group(*cards, metrics, activity_log),
            title="[bold cyan]ACTIVITY[/bold cyan]",
            border_style="cyan"
        )
```

---

## Implementation Plan

### Phase 1: Separate Chat from Activity (30 min)

**Goal:** Stop showing tool results in chat panel

1. **Modify `_render_chat_panel()`**
   - Filter out tool execution entries
   - Only show user/ai role messages
   - Add thinking component (collapsed)

2. **Modify `ActivityPanel`**
   - Add tool card rendering
   - Track active tool executions
   - Show only last 5 tools

**Files:**
- `src/mycoder/cli_interactive.py` (chat rendering)
- `src/mycoder/ui_activity_panel.py` (activity rendering)

### Phase 2: Thinking Component (20 min)

**Goal:** Make thinking collapsible

1. **Add ThinkingComponent class**
   - Collapsed by default
   - Store thinking steps
   - Toggle on keyboard input

2. **Parse thinking from AI response**
   - Detect thinking markers in response
   - Extract steps
   - Render as collapsible component

**Files:**
- `src/mycoder/ui_components.py` (NEW file)
- `src/mycoder/cli_interactive.py` (integrate component)

### Phase 3: Tool Cards (30 min)

**Goal:** Show tool execution as cards

1. **Create ToolCard dataclass**
   - States: pending/success/error
   - Duration tracking
   - Result summary

2. **Update ActivityPanel to use cards**
   - Add tool card on tool start
   - Update card on tool complete
   - Auto-scroll to latest

3. **Add tool start/complete events**
   - Listen to tool_registry events
   - Create/update cards accordingly

**Files:**
- `src/mycoder/ui_components.py` (ToolCard class)
- `src/mycoder/ui_activity_panel.py` (integrate cards)
- `src/mycoder/cli_interactive.py` (event handling)

### Phase 4: Clean Borders (15 min)

**Goal:** Fix overlapping panel borders

1. **Use consistent box styles**
   - Chat: `box.ROUNDED`
   - Activity: `box.ROUNDED`
   - No nested panels

2. **Fix layout split ratios**
   - Chat: 60%
   - Activity: 40%

**Files:**
- `src/mycoder/cli_interactive.py` (layout configuration)

### Phase 5: Polish (15 min)

**Goal:** Professional touches

1. **Add icons**
   - 💬 Chat
   - 🔧 Activity
   - 🔄 Thinking
   - ⏳/✓/✗ Tool states

2. **Improve colors**
   - Chat: green/cyan theme
   - Activity: cyan theme
   - Thinking: yellow (when expanded)

3. **Add keyboard shortcuts**
   - `t` - toggle thinking
   - `a` - toggle activity panel visibility

**Files:**
- `src/mycoder/cli_interactive.py` (keybindings)

---

## Example: Before vs After

### BEFORE (current):
```
╭─────────────── 💬 CHAT ──────────────╮╭───── ACTIVITY ─────╮
│ [16:49] You: Update packages        ││ Recent Activity:   │
│ [16:49] AI: /read pyproject.toml    ││ 16:49 @ Query      │
│                                     ││                    │
│    Tool Execution Results:          ││                    │
│    File: pyproject.toml             ││                    │
│    [entire file content shown]      ││                    │
│                                     ││                    │
│ /read requirements.txt              ││                    │
│    Tool Execution Results:          ││                    │
│    [entire file content]            ││                    │
╰─────────────────────────────────────╯╰────────────────────╯
```
❌ Tool results clutter chat
❌ Can't see conversation flow
❌ Activity panel empty/useless

### AFTER (proposed):
```
╭─────────────── 💬 CHAT ──────────────╮╭───── 🔧 ACTIVITY ──╮
│ [16:49:21] You:                     ││ ┌─────────────────┐│
│ Aktualizuj mi balíčky               ││ │✓ /read proj...  ││
│                                     ││ │  0.2s 1.2K char ││
│ [16:49:23] MyCoder:                 ││ └─────────────────┘│
│ Našel jsem pyproject.toml.          ││ ┌─────────────────┐│
│                                     ││ │✓ /read req...   ││
│ ▸ Thinking (2 steps)                ││ │  0.1s Not found ││
│                                     ││ └─────────────────┘│
│ Závislosti:                         ││                    │
│ • rich ^13.7.0                      ││ SYS CPU: 45% ▂▄█  │
│ • aiohttp ^3.9.0                    ││     RAM: 52%      │
│                                     ││                    │
│ Spustit `poetry update`? [Y/n]      ││ Recent:           │
│                                     ││ 16:49:23 AI resp  │
╰─────────────────────────────────────╯╰────────────────────╯
```
✅ Clean chat conversation
✅ Tool activity in right panel
✅ Collapsed thinking
✅ Professional appearance

---

## Testing Checklist

- [ ] Tool results NOT shown in chat panel
- [ ] Tool cards appear in activity panel
- [ ] Thinking is collapsed by default
- [ ] Thinking expands on click
- [ ] Activity panel shows last 5 tools max
- [ ] No overlapping panel borders
- [ ] System metrics visible
- [ ] Icons render correctly
- [ ] Keyboard shortcuts work

---

## Notes for Implementation

1. **Rich Layout tips:**
   - Use `Layout.split_row()` with explicit ratios
   - Avoid nested Panels (causes border overlap)
   - Use `Group()` for stacking components
   - Use `padding=(0,1)` for compact cards

2. **Event handling:**
   - Listen to tool_registry events: `tool_pre_execution`, `tool_post_execution`
   - Update activity panel in real-time
   - Don't block main render loop

3. **Performance:**
   - Limit tool cards to 5
   - Limit activity log to 10 entries
   - Use `live.update()` sparingly (only on state changes)

---

## Success Criteria

✅ Chat panel shows ONLY conversation
✅ Activity panel shows ONLY operations/metrics
✅ Thinking is collapsed by default
✅ Tool execution visible as cards
✅ No rendering artifacts
✅ Professional appearance (like VS Code)
