# MyCoder Adaptive Modes Design Document

## 🎯 Overview

Integration of `claude-cli-auth` module into MyCoder orchestration system with intelligent adaptive modes for different network and resource conditions.

## 🏗️ Adaptive Modes Architecture

### Mode Definitions

#### **FULL Mode** (Optimální prostředí)
- **Network**: Plné připojení, stabilní internet
- **Resources**: Všechny MCP servery dostupné (192.168.0.58:8020)
- **Claude Access**: CLI authentication working
- **Capabilities**:
  - Full MCP orchestration (7+ services)
  - Claude CLI Auth via claude-cli-auth module
  - Advanced memory system (PostgreSQL + Qdrant)
  - Research & web browsing capabilities
  - Complete tool suite access

```python
FULL_MODE = {
    "claude_auth": "claude-cli-auth",  # Náš nový modul
    "mcp_orchestrator": "192.168.0.58:8020",
    "memory_system": "postgresql+qdrant", 
    "tools": ["filesystem", "git", "terminal", "database", "memory", "transcriber", "research"],
    "fallback": "DEGRADED"
}
```

#### **DEGRADED Mode** (Slabá síť)
- **Network**: Omezené připojení, nestabilní
- **Resources**: Pouze lokální MCP servery
- **Claude Access**: CLI auth s fallback
- **Capabilities**:
  - Local MCP services only
  - Claude CLI Auth with timeout handling
  - Basic memory (SQLite)
  - Essential tools only

```python
DEGRADED_MODE = {
    "claude_auth": "claude-cli-auth",  # S fallback mechanikou
    "mcp_orchestrator": "localhost:8020",  # Lokální instance
    "memory_system": "sqlite",
    "tools": ["filesystem", "git", "terminal"],  # Essential only
    "fallback": "AUTONOMOUS"
}
```

#### **AUTONOMOUS Mode** (Bez externí AI)
- **Network**: Pouze lokální přístup
- **Resources**: Local LLM (Ollama/CodeLlama)
- **Claude Access**: None (offline)
- **Capabilities**:
  - Local LLM integration (Ollama)
  - Basic MCP tools
  - File operations
  - Local memory

```python
AUTONOMOUS_MODE = {
    "claude_auth": None,  # Offline
    "local_llm": "ollama://codellama",
    "mcp_orchestrator": "localhost:8020",
    "memory_system": "sqlite",
    "tools": ["filesystem", "terminal"],  # Minimal set
    "fallback": "RECOVERY"
}
```

#### **RECOVERY Mode** (Emergency)
- **Network**: Žádné nebo velmi omezené
- **Resources**: Minimální funkce
- **Claude Access**: None
- **Capabilities**:
  - File operations only
  - Basic shell commands
  - Local logging
  - Emergency procedures

```python
RECOVERY_MODE = {
    "claude_auth": None,
    "local_llm": None,
    "mcp_orchestrator": None,
    "memory_system": "file",  # JSON files
    "tools": ["filesystem"],  # File ops only
    "fallback": None  # Terminal mode
}
```

## 🔄 Mode Detection Logic

### Network Detection Algorithm

```python
async def detect_network_condition():
    """Detect current network condition and available resources."""
    conditions = {
        "internet_stable": await test_internet_stability(),
        "orchestrator_available": await test_orchestrator_connection(),
        "claude_auth_working": await test_claude_authentication(),
        "local_resources": await assess_local_resources()
    }
    
    if all([
        conditions["internet_stable"],
        conditions["orchestrator_available"], 
        conditions["claude_auth_working"]
    ]):
        return "FULL"
    
    elif conditions["orchestrator_available"] and conditions["claude_auth_working"]:
        return "DEGRADED"
        
    elif conditions["local_resources"]["ollama_available"]:
        return "AUTONOMOUS"
        
    else:
        return "RECOVERY"
```

### Health Monitoring

```python
async def monitor_system_health():
    """Continuous monitoring and adaptive mode switching."""
    while True:
        current_mode = await detect_network_condition()
        
        if current_mode != active_mode:
            logger.info(f"Mode transition: {active_mode} → {current_mode}")
            await transition_to_mode(current_mode)
            
        await asyncio.sleep(30)  # Check every 30 seconds
```

## 🧩 Claude-CLI-Auth Integration

### Integration Points

1. **Primary Mode Handler**: `claude-cli-auth` as main AI interface
2. **Fallback Detection**: Automatic degradation when auth fails
3. **Session Management**: Persistent sessions across mode transitions
4. **Error Recovery**: Intelligent retry and mode switching

### Implementation

```python
from claude_cli_auth import ClaudeAuthManager, AuthConfig

class MyCoder:
    def __init__(self):
        self.mode = "FULL"  # Start optimistic
        self.claude_auth = None
        self.initialize_claude_auth()
    
    async def initialize_claude_auth(self):
        """Initialize Claude authentication with adaptive config."""
        config = AuthConfig(
            timeout_seconds=30 if self.mode == "FULL" else 60,
            use_sdk=self.mode == "FULL",
            enable_streaming=self.mode in ["FULL", "DEGRADED"],
            session_timeout_hours=24 if self.mode == "FULL" else 6
        )
        
        try:
            self.claude_auth = ClaudeAuthManager(config=config)
            logger.info(f"Claude auth initialized in {self.mode} mode")
        except Exception as e:
            logger.warning(f"Claude auth failed: {e}")
            await self.degrade_mode()
    
    async def query_claude(self, prompt, **kwargs):
        """Adaptive Claude querying with mode-aware handling."""
        if not self.claude_auth:
            return await self.handle_no_claude(prompt)
            
        try:
            response = await self.claude_auth.query(
                prompt,
                timeout=self.get_timeout_for_mode(),
                **kwargs
            )
            return response
            
        except Exception as e:
            logger.error(f"Claude query failed: {e}")
            return await self.handle_claude_failure(prompt, e)
```

## 📊 Mode Transition Matrix

```
┌─────────────┬──────────────────────────────────────────────────┐
│ From → To   │ Trigger Conditions                               │
├─────────────┼──────────────────────────────────────────────────┤
│ FULL → DEG  │ • Orchestrator slow/unreliable (>5s response)   │
│             │ • Network instability detected                  │
├─────────────┼──────────────────────────────────────────────────┤
│ DEG → AUTO  │ • Claude auth consistently failing              │
│             │ • Orchestrator completely unreachable           │
├─────────────┼──────────────────────────────────────────────────┤
│ AUTO → REC  │ • Local LLM unavailable                         │
│             │ • System resources critical                     │
├─────────────┼──────────────────────────────────────────────────┤
│ Any → FULL  │ • All services healthy for >2 minutes          │
│             │ • Successful Claude auth test                   │
└─────────────┴──────────────────────────────────────────────────┘
```

## 🛠️ Implementation Components

### 1. Mode Manager

```python
class AdaptiveModeManager:
    def __init__(self):
        self.current_mode = "FULL"
        self.mode_history = []
        self.health_checks = {}
        
    async def evaluate_conditions(self):
        """Evaluate all conditions and determine appropriate mode."""
        
    async def transition_mode(self, new_mode):
        """Safely transition between modes."""
        
    def get_capabilities_for_mode(self, mode):
        """Return available capabilities for given mode."""
```

### 2. Network Detective

```python
class NetworkDetective:
    async def test_internet_stability(self):
        """Test internet connection stability."""
        
    async def test_orchestrator_connection(self):
        """Test MCP orchestrator availability."""
        
    async def test_claude_authentication(self):
        """Test Claude CLI authentication status."""
```

### 3. Resource Monitor

```python
class ResourceMonitor:
    async def check_system_resources(self):
        """Monitor CPU, memory, disk usage."""
        
    async def assess_local_llm_availability(self):
        """Check if Ollama/local LLM is available."""
        
    async def evaluate_mcp_service_health(self):
        """Test MCP services availability."""
```

## 🎮 Usage Scenarios

### Scenario 1: Domácí Práce (FULL Mode)
```python
# Uživatel má plné připojení, všechny služby fungují
mycoder = MyCoder()
await mycoder.process_request(
    "Analyzuj tento kód a navrhni vylepšení",
    files=["app.py", "models.py"],
    use_memory=True,
    research_context=True
)
```

### Scenario 2: Cestování (DEGRADED Mode)
```python
# Slabé WiFi, pouze základní funkce
mycoder = MyCoder()  # Automaticky detekuje DEGRADED
await mycoder.process_request(
    "Opravu tento bug",
    files=["bug.py"],
    timeout=90,  # Vyšší timeout
    use_memory=False  # Rychlejší bez memory
)
```

### Scenario 3: Offline Práce (AUTONOMOUS Mode)  
```python
# Žádný internet, local LLM
mycoder = MyCoder()  # Detekuje AUTONOMOUS
await mycoder.process_request(
    "Zkontroluj syntax tohoto kódu",
    files=["script.py"],
    llm="codellama",  # Local model
    simple_output=True
)
```

## 🧪 Testing Strategy

### 1. Mode Detection Testing
- Simulace různých síťových podmínek
- Test přechodu mezi modes
- Ověření fallback mechanizmů

### 2. Integration Testing
- Test claude-cli-auth v každém mode
- Ověření session persistence
- Test error recovery

### 3. Performance Testing
- Měření response times v různých modes
- Load testing MCP orchestrator
- Memory usage profiling

## 📈 Success Metrics

- **Reliability**: 99.9% uptime v FULL mode
- **Adaptability**: Mode transition < 5 seconds
- **Performance**: Response time < 10s v FULL, < 30s v DEGRADED
- **Resilience**: Automatický recovery ve 100% případů

---

**Próximos Pasos**: Implementace `AdaptiveModeManager` s integrací claude-cli-auth modulu.