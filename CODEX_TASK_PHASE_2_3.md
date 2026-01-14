# TASK: MyCoder v2.1.1 - Implementace Fází 2 a 3

## CONTEXT

Právě byla dokončena **Fáze 1: Action-Performing CLI Foundation** projektu MyCoder v2.1.1.

**Co je hotovo:**
- ✅ `src/mycoder/command_parser.py` (200 řádků) - Parsování CLI příkazů
- ✅ `src/mycoder/mcp_bridge.py` (280 řádků) - MCP bridge
- ✅ `src/mycoder/tool_orchestrator.py` (350 řádků) - Tool orchestrator
- ✅ Modifikace `enhanced_mycoder_v2.py` a `cli_interactive.py`
- ✅ 57 unit testů passed

**Struktura projektu:**
```
MyCoder-v2.0/
├── src/
│   ├── mycoder/                      # Core package
│   │   ├── enhanced_mycoder_v2.py        # Main class (897 lines)
│   │   ├── api_providers.py              # 5-tier API system (1271 lines)
│   │   ├── tool_registry.py              # Tool registry (707 lines)
│   │   ├── command_parser.py             # ✅ NEW (200 lines)
│   │   ├── mcp_bridge.py                 # ✅ NEW (280 lines)
│   │   ├── tool_orchestrator.py          # ✅ NEW (350 lines)
│   │   ├── cli_interactive.py            # CLI UI (modified)
│   │   └── config_manager.py             # Config (602 lines)
│   └── speech_recognition/           # Existing speech module
│       ├── cli.py
│       ├── dictation_app.py
│       ├── whisper_transcriber.py
│       ├── gemini_transcriber.py
│       └── (další soubory...)
├── tests/
│   ├── unit/
│   │   ├── test_command_parser.py        # ✅ 25 tests
│   │   ├── test_mcp_bridge.py            # ✅ 17 tests
│   │   └── test_tool_orchestrator.py     # ✅ 16 tests
│   └── integration/
│       └── test_cli_tool_execution.py    # ✅ Integration tests
├── CLAUDE.md                         # Project docs
├── AGENTS.md                         # Shared AI context
└── pyproject.toml                    # Poetry project
```

**Tech Stack:**
- Python 3.13, Poetry package manager
- Rich library pro terminal UI
- Async/await s asyncio
- pytest pro testing
- Existující speech recognition moduly (PyQt5, sounddevice, openai-whisper)

## ÚKOL

Implementuj **Fázi 2 (Speech + TTS)** a **Fázi 3 (Mercury/Termux + Smart UI)** podle detailního plánu níže.

---

## FÁZE 2: Speech Recognition + TTS (v2.1.1-beta)

### CÍL
Integrovat existující dictation modul jako MyCoder tool + přidat Text-to-Speech pro čtení AI odpovědí nahlas.

### IMPLEMENTATION TODO

#### TODO 2.1: Vytvořit `src/mycoder/speech_tool.py` (~450 řádků)

**Požadavky:**
- Implementovat `SpeechTool` jako `BaseTool` subclass
- Podporovat 2 režimy: GUI overlay mode + CLI inline mode
- Integrace s existujícím `GlobalDictationApp` z `src/speech_recognition/dictation_app.py`

**Kód template:**

```python
"""
Speech Tool for MyCoder v2.1.1

Provides voice dictation capabilities as a MyCoder tool.
Modes: GUI overlay (background app) or CLI inline (record → transcribe → return).
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .tool_registry import (
    BaseTool,
    ToolCategory,
    ToolAvailability,
    ToolPriority,
    ToolCapabilities,
    ToolExecutionContext,
    ToolResult,
)

logger = logging.getLogger(__name__)


class SpeechTool(BaseTool):
    """
    Hybrid voice dictation tool.

    Modes:
    - GUI: Launches GlobalDictationApp with overlay button (background)
    - CLI: Inline recording → transcription → text return (foreground)
    """

    def __init__(self):
        super().__init__(
            name="voice_dictation",
            category=ToolCategory.COMMUNICATION,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=ToolCapabilities(
                requires_filesystem=False,
                requires_network=True,  # For Whisper API
                max_execution_time=300,  # 5 minutes max
                resource_intensive=True,
            ),
        )
        self.dictation_app = None  # Lazy load
        self.is_running = False

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """
        Execute voice dictation.

        Args:
            mode (str): "gui" (overlay) or "cli" (inline). Default: "gui"
            action (str): "start", "stop", "status". Default: "start"
            duration (int): Recording duration in seconds (CLI mode). Default: 10
            language (str): Language code. Default: "cs"

        Returns:
            ToolResult with transcribed text (CLI mode) or status (GUI mode)
        """
        mode = kwargs.get("mode", "gui")
        action = kwargs.get("action", "start")

        if mode == "gui":
            return await self._execute_gui_mode(action, **kwargs)
        elif mode == "cli":
            return await self._execute_cli_mode(**kwargs)
        else:
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=0,
                error=f"Invalid mode: {mode}. Use 'gui' or 'cli'",
            )

    async def _execute_gui_mode(self, action: str, **kwargs) -> ToolResult:
        """Launch GUI overlay mode (background app)"""
        # TODO: Implementovat spuštění GlobalDictationApp
        # - Import: from speech_recognition.dictation_app import GlobalDictationApp
        # - Lazy load self.dictation_app
        # - Start app in background thread
        # - Return immediately with status
        pass

    async def _execute_cli_mode(self, **kwargs) -> ToolResult:
        """Inline dictation: record → transcribe → return text"""
        # TODO: Implementovat inline recording
        # - Duration from kwargs
        # - Record audio using sounddevice
        # - Transcribe using WhisperTranscriber or GeminiTranscriber
        # - Return transcribed text
        pass

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Validate speech tool can run"""
        # Check if speech dependencies are available
        try:
            import sounddevice  # noqa
            return True
        except ImportError:
            logger.warning("Speech tool dependencies not installed")
            return False


# TODO: Register in tool_registry.py:
# from .speech_tool import SpeechTool
# self.register_tool(SpeechTool())
```

**Testovací strategie:**
- Mock `GlobalDictationApp` import
- Mock audio recording (sounddevice)
- Mock transcription APIs
- Test GUI mode start/stop/status
- Test CLI mode recording + transcription

---

#### TODO 2.2: Vytvořit `src/mycoder/tts_engine.py` (~300 řádků)

**Požadavky:**
- Multi-backend TTS: pyttsx3 (primary), espeak (Linux), gtts (Google), gemini (fallback)
- Async non-blocking speech
- Czech voice support
- Konfigurovatelná rychlost a hlas

**Kód template:**

```python
"""
Text-to-Speech Engine for MyCoder v2.1.1

Multi-backend TTS with Czech language support.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Multi-backend Text-to-Speech engine.

    Supported providers:
    - pyttsx3: Offline, cross-platform (PRIMARY)
    - espeak: Linux native, Czech support
    - gtts: Google TTS (requires network)
    - gemini: Gemini TTS API (fallback)
    """

    def __init__(self, provider: str = "pyttsx3", voice: str = "cs", rate: int = 150):
        """
        Initialize TTS engine.

        Args:
            provider: TTS provider ("pyttsx3", "espeak", "gtts", "gemini")
            voice: Voice language code ("cs", "en", etc.)
            rate: Speech rate (words per minute)
        """
        self.provider = provider
        self.voice = voice
        self.rate = rate
        self.engine = None
        self._init_provider()

    def _init_provider(self):
        """Initialize TTS provider"""
        if self.provider == "pyttsx3":
            try:
                import pyttsx3
                self.engine = pyttsx3.init()
                self._configure_pyttsx3()
            except Exception as e:
                logger.error(f"Failed to init pyttsx3: {e}")
                self.engine = None
        # TODO: Implementovat další providery (espeak, gtts, gemini)

    def _configure_pyttsx3(self):
        """Configure pyttsx3 engine for Czech"""
        if not self.engine:
            return

        # Set rate
        self.engine.setProperty('rate', self.rate)

        # Find Czech voice
        voices = self.engine.getProperty('voices')
        for v in voices:
            # TODO: Detekovat český hlas podle v.languages nebo v.name
            pass

    async def speak_async(self, text: str) -> None:
        """
        Speak text asynchronously (non-blocking).

        Args:
            text: Text to speak
        """
        await asyncio.to_thread(self._speak_sync, text)

    def _speak_sync(self, text: str):
        """Synchronous speech (blocking)"""
        if self.provider == "pyttsx3" and self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        elif self.provider == "espeak":
            # TODO: Implementovat espeak via subprocess
            pass
        elif self.provider == "gtts":
            # TODO: Implementovat Google TTS
            pass
        elif self.provider == "gemini":
            # TODO: Implementovat Gemini TTS
            pass

    def stop(self):
        """Stop current speech"""
        if self.provider == "pyttsx3" and self.engine:
            self.engine.stop()


# TODO: Add to config_manager.py DEFAULT_CONFIG:
# "text_to_speech": {
#     "enabled": False,
#     "provider": "pyttsx3",
#     "voice": "cs",
#     "rate": 150,
#     "auto_read_responses": False
# }
```

---

#### TODO 2.3: Modifikovat `src/mycoder/tool_registry.py`

**Změny:**
- Přidat import a registraci `SpeechTool` v `_initialize_core_tools()`

**Přidej do metody `_initialize_core_tools()`:**
```python
# Speech recognition tool (v2.1.1)
try:
    from .speech_tool import SpeechTool
    self.register_tool(SpeechTool())
    logger.info("Registered SpeechTool")
except ImportError as e:
    logger.warning(f"SpeechTool not available: {e}")
```

---

#### TODO 2.4: Modifikovat `src/mycoder/cli_interactive.py`

**Změny potřebné:**

1. **Import TTSEngine:**
```python
try:
    from .tts_engine import TTSEngine
except ImportError:
    TTSEngine = None
```

2. **Přidat do `__init__()` metody:**
```python
# TTS engine (v2.1.1)
self.tts_engine = None
if TTSEngine and self.config.get("text_to_speech", {}).get("enabled", False):
    tts_config = self.config.get("text_to_speech", {})
    self.tts_engine = TTSEngine(
        provider=tts_config.get("provider", "pyttsx3"),
        voice=tts_config.get("voice", "cs"),
        rate=tts_config.get("rate", 150),
    )
```

3. **Přidat nové slash commands do `handle_slash_command()`:**

```python
elif cmd == "/speak":
    # TTS: Přečti text nahlas
    if not self.tts_engine:
        self.console.print("[bold red]TTS not enabled. Set text_to_speech.enabled=true in config[/]")
        return

    text = " ".join(args) if args else "Test českého hlasu"
    await self.tts_engine.speak_async(text)
    self.monitor.add_log("TTS", text[:30])
    self.console.print(f"[{COLOR_SUCCESS}]Speaking: {text}[/]")

elif cmd == "/voice":
    # Voice dictation control
    if not args:
        self.console.print("[bold red]Usage: /voice start|stop|status[/]")
        return

    action = args[0]

    if action == "start":
        # Execute voice_dictation tool
        from .command_parser import Command
        command = Command(
            tool="voice_dictation",
            args={"mode": "gui", "action": "start"},
            raw_input="/voice start"
        )

        if hasattr(self.coder, "tool_orchestrator") and self.coder.tool_orchestrator:
            result = await self.coder.tool_orchestrator.execute_command(
                command, self._build_execution_context()
            )
            if result.success:
                self.console.print("[{COLOR_SUCCESS}]Voice dictation started. Press Ctrl+Shift+Space to record.[/]")
            else:
                self.console.print(f"[bold red]Error: {result.error}[/]")

    elif action == "stop":
        # Stop dictation
        # TODO: Implement stop logic
        pass
```

4. **Auto-read AI responses (pokud enabled):**

```python
# V metodě _process_ai_query() nebo process_chat() - AFTER displaying response:

# Auto-read AI responses (v2.1.1)
if self.tts_engine and self.config.get("text_to_speech", {}).get("auto_read_responses", False):
    # Extract plain text from response (strip markdown)
    plain_text = self._strip_markdown(response_content)
    await self.tts_engine.speak_async(plain_text)
```

Přidej helper metodu:
```python
def _strip_markdown(self, text: str) -> str:
    """Strip markdown formatting for TTS"""
    import re
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`[^`]*`', '', text)
    # Remove markdown formatting
    text = re.sub(r'[*_~`]', '', text)
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    return text.strip()
```

---

#### TODO 2.5: Modifikovat `src/speech_recognition/dictation_app.py`

**Přidat MyCoder integration hooks:**

V třídě `GlobalDictationApp.__init__()`:
```python
def __init__(self, ..., mycoder_callback=None):
    # ... existující init ...
    self.mycoder_callback = mycoder_callback  # NEW: Callback pro MyCoder
```

V metodě `_process_audio()` (nebo kde se vrací transcribed text):
```python
async def _process_audio(self, audio_data):
    # ... existující transcription logic ...

    transcribed_text = await self.transcriber.transcribe(audio_data)

    # NEW: MyCoder callback
    if self.mycoder_callback:
        await self.mycoder_callback(transcribed_text)
    else:
        # Existující behavior: inject do active window
        self.text_injector.inject(transcribed_text)
```

---

#### TODO 2.6: Přidat dependencies do `pyproject.toml`

```toml
[tool.poetry.dependencies]
pyttsx3 = { version = "^2.90", optional = true }

[tool.poetry.extras]
speech = [
    "PyQt5",
    "sounddevice",
    "numpy",
    "openai-whisper",
    "openai",
    "torch",
    "pynput",
    "python-xlib",
    "pyperclip",
    "pyttsx3"  # NEW
]
```

Spusť:
```bash
poetry lock --no-update
poetry install --extras speech
```

---

#### TODO 2.7: Vytvořit `tests/unit/test_speech_tool.py`

**Testovací coverage:**
- ✅ SpeechTool initialization
- ✅ GUI mode (mock GlobalDictationApp)
- ✅ CLI mode (mock recording + transcription)
- ✅ Context validation (check dependencies)
- ✅ Error handling (missing dependencies)

**Template:**
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

from mycoder.speech_tool import SpeechTool
from mycoder.tool_registry import ToolExecutionContext, ToolResult


class TestSpeechTool:
    @pytest.fixture
    def speech_tool(self):
        return SpeechTool()

    def test_initialization(self, speech_tool):
        assert speech_tool.name == "voice_dictation"
        assert speech_tool.is_running == False

    @pytest.mark.asyncio
    @patch("mycoder.speech_tool.GlobalDictationApp")
    async def test_gui_mode_start(self, mock_app_class, speech_tool):
        # TODO: Implementovat test
        pass

    # TODO: Přidat další testy
```

---

#### TODO 2.8: Vytvořit `tests/unit/test_tts_engine.py`

**Testovací coverage:**
- ✅ TTSEngine initialization (všechny providery)
- ✅ pyttsx3 provider (mock engine)
- ✅ Czech voice selection
- ✅ Async speech (non-blocking)
- ✅ Rate configuration
- ✅ Error handling (missing dependencies)

---

#### TODO 2.9: Vytvořit `tests/integration/test_voice_workflow.py`

**End-to-end test scénář:**
1. Start voice dictation (`/voice start`)
2. Mock audio recording
3. Mock transcription
4. Verify text returned
5. Test TTS response reading (`/speak`)

---

### MILESTONE KRITÉRIA FÁZE 2 ✅

Před ukončením Fáze 2 ověř:
- [ ] `/voice start` spustí dictation overlay (nebo mock vrátí success)
- [ ] `/speak "Ahoj světe"` spustí TTS (nebo mock)
- [ ] Auto-read AI responses funguje (pokud enabled v config)
- [ ] `SpeechTool` je zaregistrován v `tool_registry`
- [ ] Všechny unit testy (min. 90% coverage na nových souborech)
- [ ] Integration test prošel

---

## FÁZE 3: Mercury + Termux + Smart UI (v2.1.1-final)

### CÍL
1. Dokončit 7-tier API fallback chain (přidat Mercury a Termux Ollama)
2. Vylepšit UI s dynamic panels (progress, provider health)

---

### IMPLEMENTATION TODO

#### TODO 3.1: Přidat `TermuxOllamaProvider` do `src/mycoder/api_providers.py`

**Požadavky:**
- Extend `OllamaProvider` class
- Support WiFi nebo USB tethering connection
- Typicky: `http://192.168.1.x:11434` nebo USB IP
- Health check před použitím

**Přidat novou třídu (~80 řádků):**

```python
class TermuxOllamaProvider(OllamaProvider):
    """
    Ollama running on Android via Termux.

    Connection types:
    - WiFi: http://192.168.1.x:11434
    - USB: http://192.168.42.129:11434 (typical USB tethering)
    """

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.is_termux = True
        self.connection_type = config.model_args.get("connection_type", "wifi")

        logger.info(
            f"Initialized TermuxOllamaProvider at {self.base_url} "
            f"(connection: {self.connection_type})"
        )

    async def health_check(self) -> APIProviderStatus:
        """
        Check if Termux device is reachable and Ollama is running.

        Returns:
            APIProviderStatus
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        logger.info("Termux Ollama is reachable and healthy")
                        return APIProviderStatus.HEALTHY

            logger.warning("Termux Ollama not responding")
            return APIProviderStatus.UNAVAILABLE

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Termux Ollama health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE

    async def generate(
        self, prompt: str, files: List[Path] = None, **kwargs
    ) -> APIResponse:
        """Generate response with Termux-specific optimizations"""
        # TODO: Možná použít menší context window pro Android zařízení
        return await super().generate(prompt, files, **kwargs)


# TODO: Přidat do APIProviderType enum:
# TERMUX_OLLAMA = "termux_ollama"
```

---

#### TODO 3.2: Modifikovat `src/mycoder/enhanced_mycoder_v2.py`

**Změny potřebné:**

1. **Update fallback chain (v `__init__` nebo `_initialize_api_providers`):**

```python
# Nový 7-tier fallback chain (v2.1.1)
self.fallback_chain = [
    APIProviderType.CLAUDE_ANTHROPIC,   # 1. Primary (paid, fastest)
    APIProviderType.CLAUDE_OAUTH,       # 2. Fallback #1 (subscription)
    APIProviderType.GEMINI,             # 3. Fallback #2 (Google AI)
    APIProviderType.MERCURY,            # 4. Fallback #3 (Inception Labs) - EXISTING
    APIProviderType.OLLAMA_LOCAL,       # 5. Fallback #4 (free, thermal-aware)
    APIProviderType.TERMUX_OLLAMA,      # 6. Fallback #5 (Android) - NEW
    APIProviderType.OLLAMA_REMOTE,      # 7. Fallback #6 (remote URLs)
]
```

2. **Přidat Termux Ollama config (v `_initialize_api_providers()`):**

```python
# Termux Ollama (Priority 6) - NEW
termux_config = self._get_section("termux_ollama")
termux_enabled = termux_config.get("enabled", False)

if termux_enabled:
    termux_provider_config = APIProviderConfig(
        provider_type=APIProviderType.TERMUX_OLLAMA,
        enabled=True,
        timeout_seconds=termux_config.get("timeout_seconds", 45),
        config={
            "base_url": termux_config.get(
                "base_url", "http://192.168.1.100:11434"
            ),
            "model": termux_config.get("model", "tinyllama"),
            "connection_type": termux_config.get("connection_type", "wifi"),
        },
    )
    provider_configs.append(termux_provider_config)
```

**POZNÁMKA:** Mercury provider je už implementován (řádky 255-291 v api_providers.py), jen není v fallback chain. Přidej ho!

---

#### TODO 3.3: Modifikovat `src/mycoder/config_manager.py`

**Přidat do DEFAULT_CONFIG:**

```python
"mercury": {
    "enabled": False,  # Opt-in
    "api_key": "${INCEPTION_API_KEY}",
    "base_url": "https://api.inceptionlabs.ai/v1",
    "model": "mercury",
    "timeout_seconds": 60,
    "diffusing": True,
    "realtime": False,
},

"termux_ollama": {
    "enabled": False,  # Opt-in
    "base_url": "http://192.168.1.100:11434",
    "model": "tinyllama",
    "timeout_seconds": 45,
    "connection_type": "wifi",  # or "usb"
},
```

---

#### TODO 3.4: Vytvořit `src/mycoder/ui_dynamic_panels.py` (~400 řádků)

**Požadavky:**
- Extend `ExecutionMonitor` z `cli_interactive.py`
- Dynamic rendering based on context:
  - Progress bars pro long operations
  - Provider health dashboard
  - Thermal alerts
  - Cost estimates

**Kód template:**

```python
"""
Dynamic UI Panels for MyCoder v2.1.1

Enhanced ExecutionMonitor with AI-aware features.
"""

from typing import Dict, Optional
import psutil
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn


class DynamicExecutionMonitor:
    """
    Enhanced execution monitor with:
    - Progress bars for active operations
    - Provider health dashboard
    - Thermal warnings
    - Cost estimates
    """

    def __init__(self):
        self.logs = []
        self.max_logs = 15

        # NEW: Dynamic state
        self.current_operation: Optional[str] = None
        self.progress_percent: int = 0
        self.provider_health: Dict[str, str] = {}  # provider -> status
        self.cost_estimate: float = 0.0
        self.thermal_warning: bool = False

    def set_operation(self, operation: str, progress: int = 0):
        """Set current operation with progress"""
        self.current_operation = operation
        self.progress_percent = progress

    def update_progress(self, percent: int):
        """Update progress percentage"""
        self.progress_percent = min(100, max(0, percent))

    def clear_operation(self):
        """Clear current operation"""
        self.current_operation = None
        self.progress_percent = 0

    def update_provider_health(self, provider: str, status: str):
        """
        Update provider health status.

        Args:
            provider: Provider name
            status: "healthy", "degraded", "unavailable"
        """
        self.provider_health[provider] = status

    def set_thermal_warning(self, warning: bool):
        """Set thermal warning state"""
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
        elif self.current_operation:
            return self._render_with_progress()
        else:
            return self._render_standard()

    def _render_with_progress(self) -> Panel:
        """Render with progress bar"""
        table = Table.grid(padding=(0, 1))

        # Current operation
        table.add_row(Text("OPERATION", style="bold cyan"))
        table.add_row(Text(self.current_operation or "Processing..."))
        table.add_row("")

        # Progress bar
        progress_bar = self._render_progress_bar(self.progress_percent)
        table.add_row(
            Text(f"Progress: {progress_bar} {self.progress_percent}%")
        )
        table.add_row("")

        # Provider health
        if self.provider_health:
            table.add_row(Text("PROVIDER HEALTH", style="bold cyan"))
            for provider, status in self.provider_health.items():
                icon = self._get_status_icon(status)
                table.add_row(Text(f"{icon} {provider}: {status}"))
            table.add_row("")

        # System metrics
        metrics = self._get_system_metrics()
        table.add_row(Text("SYSTEM", style="bold cyan"))
        table.add_row(
            Text(f"CPU: {self._render_bar(metrics['cpu'])} {metrics['cpu']:.0f}%")
        )
        table.add_row(
            Text(f"RAM: {self._render_bar(metrics['ram'])} {metrics['ram']:.0f}%")
        )
        if metrics['thermal'] != "N/A":
            table.add_row(Text(f"THERMAL: {metrics['thermal']}"))

        return Panel(
            table,
            title="[bold cyan]EXECUTION MONITOR",
            border_style="cyan"
        )

    def _render_standard(self) -> Panel:
        """Standard rendering (existing logic)"""
        # TODO: Copy existing render logic from ExecutionMonitor
        pass

    def _render_thermal_alert(self) -> Panel:
        """Render thermal warning"""
        table = Table.grid(padding=(0, 1))
        table.add_row(Text("⚠️  THERMAL WARNING  ⚠️", style="bold red"))
        table.add_row(Text("CPU temperature critical!", style="red"))
        table.add_row(Text("Throttling to local inference...", style="yellow"))

        return Panel(
            table,
            title="[bold red]THERMAL ALERT",
            border_style="red"
        )

    def _render_progress_bar(self, percent: int) -> str:
        """Render ASCII progress bar"""
        filled = int(percent / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty

    def _render_bar(self, percent: float) -> str:
        """Render metric bar"""
        # Copy from existing ExecutionMonitor
        pass

    def _get_status_icon(self, status: str) -> str:
        """Get status icon"""
        icons = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unavailable": "🔴",
        }
        return icons.get(status, "⚪")

    def _get_system_metrics(self) -> dict:
        """Get system metrics (copy from existing)"""
        # TODO: Copy from ExecutionMonitor.get_system_metrics()
        pass

    # TODO: Add rest of methods from ExecutionMonitor (add_log, etc.)
```

---

#### TODO 3.5: Modifikovat `src/mycoder/cli_interactive.py`

**Změny:**

1. **Import DynamicExecutionMonitor:**
```python
try:
    from .ui_dynamic_panels import DynamicExecutionMonitor
except ImportError:
    # Fallback to standard monitor
    DynamicExecutionMonitor = None
```

2. **Update `__init__()` metody:**
```python
# Use dynamic monitor if available
if DynamicExecutionMonitor:
    self.monitor = DynamicExecutionMonitor()
else:
    self.monitor = ExecutionMonitor()
```

3. **Update dlouhých operací s progress:**

V metodě `process_chat()` nebo kde voláš AI:
```python
async def process_chat(self, user_input: str) -> str:
    self.monitor.set_operation("Generating AI response...", 0)

    # Simulate progress updates (or get real progress from API)
    asyncio.create_task(self._update_progress_simulation())

    try:
        response = await self.coder.process_request(user_input)
        self.monitor.clear_operation()
        return response["content"]
    except Exception as e:
        self.monitor.clear_operation()
        raise

async def _update_progress_simulation(self):
    """Simulate progress updates"""
    for i in range(0, 101, 10):
        await asyncio.sleep(0.3)
        self.monitor.update_progress(i)
```

---

#### TODO 3.6: Vytvořit testy

**Unit testy:**
- `tests/unit/test_termux_provider.py` - TermuxOllamaProvider
- `tests/unit/test_ui_dynamic_panels.py` - DynamicExecutionMonitor

**Integration testy:**
- `tests/integration/test_7tier_fallback.py` - Kompletní 7-tier fallback chain
- `tests/integration/test_mercury_provider.py` - Mercury API calls (mock)

---

### MILESTONE KRITÉRIA FÁZE 3 ✅

Před ukončením Fáze 3 ověř:
- [ ] Mercury provider je v fallback chain a funkční
- [ ] Termux Ollama provider implementován a testován
- [ ] 7-tier fallback chain kompletní
- [ ] Dynamic UI zobrazuje progress při dlouhých operacích
- [ ] Provider health dashboard funguje
- [ ] Všechny testy prošly

---

## TESTING & DEBUGGING STRATEGIE

### Unit Testing (min. 85% coverage)

**Fáze 2:**
```bash
poetry run pytest tests/unit/test_speech_tool.py -v --cov=src/mycoder/speech_tool
poetry run pytest tests/unit/test_tts_engine.py -v --cov=src/mycoder/tts_engine
```

**Fáze 3:**
```bash
poetry run pytest tests/unit/test_termux_provider.py -v
poetry run pytest tests/unit/test_ui_dynamic_panels.py -v
```

### Integration Testing

```bash
poetry run pytest tests/integration/test_voice_workflow.py -v
poetry run pytest tests/integration/test_7tier_fallback.py -v
poetry run pytest tests/integration/test_mercury_provider.py -v
```

### Debugging Tips

1. **Speech dependencies error:**
   ```bash
   poetry install --extras speech
   ```

2. **TTS not working:**
   - Check if pyttsx3 is installed: `python -c "import pyttsx3; pyttsx3.init()"`
   - Linux: Install espeak: `sudo apt-get install espeak`

3. **Provider connection errors:**
   - Mercury: Check `INCEPTION_API_KEY` env var
   - Termux: Verify device IP and Ollama running: `curl http://192.168.1.x:11434/api/tags`

4. **Thermal warnings on non-Q9550:**
   - Set `thermal.enabled=false` v config

---

## DOKUMENTACE

### TODO: Update CLAUDE.md

**Přidej sekci:**

```markdown
## New Commands (v2.1.1)

### Voice Commands
- `/voice start` - Start voice dictation (GUI overlay)
- `/voice stop` - Stop voice dictation
- `/speak <text>` - Text-to-speech playback

### Provider Control
- `/provider <name>` - Override provider selection
  - Available: claude_anthropic, claude_oauth, gemini, mercury,
    ollama_local, termux_ollama, ollama_remote

## New Features (v2.1.1)

### Speech Recognition & TTS
- Voice dictation as MyCoder tool
- Text-to-speech AI response reading
- Czech language support
- Multi-backend TTS (pyttsx3, espeak, gtts, gemini)

### 7-Tier API Provider Fallback
1. Claude Anthropic (primary)
2. Claude OAuth (subscription)
3. Gemini (Google AI)
4. Mercury (Inception Labs diffusion LLM)
5. Ollama Local (thermal-aware)
6. Termux Ollama (Android device)
7. Ollama Remote (configured URLs)

### Smart Dynamic UI
- Progress bars for long operations
- Real-time provider health dashboard
- Thermal alerts with automatic throttling
- Token cost estimates
```

---

### TODO: Update AGENTS.md

**Přidej do "Recent Changes":**

```markdown
## 2026-01-13 - MyCoder v2.1.1 Implementation (Codex)

### Phase 2: Speech Recognition + TTS
- **NEW**: `src/mycoder/speech_tool.py` - Voice dictation as tool (450 lines)
- **NEW**: `src/mycoder/tts_engine.py` - Multi-backend TTS engine (300 lines)
- **MODIFIED**: `cli_interactive.py` - Added `/voice` and `/speak` commands
- **MODIFIED**: `speech_recognition/dictation_app.py` - MyCoder integration hooks
- **FEATURE**: Auto-read AI responses with Czech TTS
- **TESTS**: 35+ new tests for speech and TTS

### Phase 3: Mercury/Termux + Smart UI
- **NEW**: `TermuxOllamaProvider` in `api_providers.py` (~80 lines)
- **NEW**: `src/mycoder/ui_dynamic_panels.py` - Dynamic UI (400 lines)
- **MODIFIED**: `enhanced_mycoder_v2.py` - 7-tier fallback chain
- **MODIFIED**: `config_manager.py` - Mercury and Termux configs
- **FEATURE**: Mercury diffusion LLM integration
- **FEATURE**: Termux Ollama on Android support
- **FEATURE**: Dynamic progress bars and health dashboard
- **TESTS**: 25+ new integration tests

### Statistics
- **Lines added**: ~1800
- **Files created**: 4
- **Files modified**: 8
- **Tests added**: 60+
- **Test coverage**: 87% (target: 85%+)
```

---

## ACCEPTANCE CRITERIA

**Fáze 2 dokončena když:**
✅ `/voice start` spustí dictation (nebo mock)
✅ `/speak "test"` přehraje TTS (nebo mock)
✅ Auto-read AI responses funguje
✅ SpeechTool registered v tool_registry
✅ Min. 30 unit testů (>85% coverage)
✅ 1 integration test prošel

**Fáze 3 dokončena když:**
✅ 7-tier fallback chain kompletní
✅ Mercury a Termux providers testované
✅ Dynamic UI shows progress + health
✅ Min. 25 unit testů
✅ 2+ integration testy prošly

**Dokumentace dokončena když:**
✅ CLAUDE.md updated s novými commands
✅ AGENTS.md updated s changelogem
✅ README.md mentioned v2.1.1 features (optional)
✅ Docstrings ve všech nových třídách

---

## FINAL CHECKLIST

Před odevzdáním práce ověř:

```bash
# 1. Všechny testy prošly
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v

# 2. Code quality
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run mypy src/mycoder/

# 3. Coverage check
poetry run pytest --cov=src/mycoder --cov-report=html
# Open htmlcov/index.html, check >85% coverage

# 4. Manuální test
poetry run mycoder
> /voice start
> /speak "Ahoj světe"
> /provider mercury
> /bash echo test
> (exit)

# 5. Git status clean
git status
# Ověř že není uncommitted změny (kromě nových souborů)
```

---

## POZNÁMKY

- **Mercury provider**: Už existuje v `api_providers.py` (řádky 380-825), jen přidaj do fallback chain!
- **Q9550 thermal**: Pokud nemáš Q9550, nastav `thermal.enabled=false` v testech
- **Speech dependencies**: Optional - pokud nejsou nainstalované, SpeechTool se gracefully disable
- **Time estimate**: Fáze 2: 2-3 dny, Fáze 3: 2-3 dny (celkem 4-6 dnů práce)

---

## QUESTIONS?

Pokud máš otázky během implementace:
1. Čti CLAUDE.md pro context
2. Čti AGENTS.md pro recent changes
3. Prohlédni si existující kod v Fázi 1 jako referenci
4. Všechny async metody musí být `async def` s `await`
5. Používej `logger.info/warning/error` místo `print()`
6. Test fixtures používají `@pytest.fixture` decorator

Good luck! 🚀
