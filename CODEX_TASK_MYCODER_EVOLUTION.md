# CODEX TASK: MyCoder v2.2.0 Evolution

**Datum:** 2026-01-15
**Autor:** Claude Code (analýza a specifikace)
**Cíl:** Implementovat opravy slabin + doplnit funkce z Claude Code CLI

---

## Executive Summary

Na základě důkladné analýzy MyCoder v2.1.1 a porovnání s Claude Code CLI je třeba:
1. Opravit bezpečnostní a architektonické slabiny v Self-Evolve modulu
2. Vylepšit API Provider systém o chybějící patterns
3. Doplnit funkce, které má Claude Code CLI ale MyCoder ne

**Očekávaný výstup:** MyCoder v2.2.0 s robustnější architekturou a rozšířenými schopnostmi.

---

## ČÁST 1: Opravy slabin (PRIORITA: VYSOKÁ)

### 1.1 Self-Evolve: User Approval před aplikací patche

**Problém:** Patche se mohou aplikovat bez explicitního souhlasu uživatele.

**Řešení:**
```python
# src/mycoder/self_evolve/manager.py

async def apply(self, proposal_id: str, require_approval: bool = True) -> EvolveProposal:
    """Apply proposal with optional user approval."""
    proposal = self.store.get(proposal_id)
    if not proposal:
        raise ValueError(f"Proposal not found: {proposal_id}")

    if require_approval:
        # Zobrazit diff a čekat na potvrzení
        approval = await self._request_user_approval(proposal)
        if not approval:
            proposal.status = "rejected"
            self.store.upsert(proposal)
            return proposal

    # ... zbytek apply logiky
```

**Soubory k úpravě:**
- `src/mycoder/self_evolve/manager.py` - přidat approval flow
- `src/mycoder/cli_interactive.py` - UI pro zobrazení diffu a approval prompt

---

### 1.2 Self-Evolve: Dry-Run Mode

**Problém:** Nelze otestovat patch bez skutečné aplikace.

**Řešení:**
```python
# src/mycoder/self_evolve/manager.py

async def dry_run(self, proposal_id: str) -> Dict[str, Any]:
    """Test patch application without modifying files."""
    proposal = self.store.get(proposal_id)
    if not proposal:
        raise ValueError(f"Proposal not found: {proposal_id}")

    # Vytvořit temporary git worktree
    worktree_path = self._create_temp_worktree()
    try:
        # Aplikovat patch v worktree
        apply_result = self._apply_patch_to_worktree(proposal.diff, worktree_path)
        if apply_result:
            return {"success": False, "error": apply_result}

        # Spustit testy v worktree
        test_result = await self._run_tests_in_worktree(worktree_path)

        return {
            "success": not test_result.failures(),
            "test_results": test_result.to_dict(),
            "affected_files": self._extract_paths(proposal.diff),
        }
    finally:
        self._cleanup_worktree(worktree_path)
```

**Nové soubory:**
- `src/mycoder/self_evolve/sandbox.py` - worktree management

---

### 1.3 Self-Evolve: Race Condition v ProposalStore

**Problém:** Souběžný přístup k `proposals.json` může způsobit data corruption.

**Řešení:**
```python
# src/mycoder/self_evolve/storage.py

import filelock  # Přidat do dependencies

class ProposalStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_file = self.base_dir / "proposals.json"
        self.lock_file = self.base_dir / "proposals.lock"
        self.lock = filelock.FileLock(self.lock_file, timeout=10)

    def upsert(self, proposal: EvolveProposal) -> None:
        with self.lock:
            proposals = self._load_all_unsafe()
            # ... update logic
            self._save_all_unsafe(proposals)

    def _load_all_unsafe(self) -> List[EvolveProposal]:
        """Load without lock - caller must hold lock."""
        # ... existing load logic

    def _save_all_unsafe(self, proposals: List[EvolveProposal]) -> None:
        """Save without lock - caller must hold lock."""
        # ... existing save logic with atomic write
        temp_file = self.proposals_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        temp_file.replace(self.proposals_file)  # Atomic on POSIX
```

**Dependencies:**
```toml
# pyproject.toml
filelock = "^3.13.0"
```

---

### 1.4 Self-Evolve: Limit počtu návrhů

**Problém:** Neomezený počet návrhů může zaplnit disk.

**Řešení:**
```python
# src/mycoder/self_evolve/manager.py

def _load_config(self) -> Dict[str, object]:
    defaults = {
        # ... existing defaults
        "max_proposals": 100,
        "auto_cleanup_days": 30,
    }
    # ...

def _cleanup_old_proposals(self) -> int:
    """Remove proposals older than auto_cleanup_days."""
    proposals = self.store.load_all()
    cutoff = datetime.now(timezone.utc) - timedelta(days=self.config["auto_cleanup_days"])

    to_keep = []
    removed = 0
    for p in proposals:
        created = datetime.fromisoformat(p.created_at)
        if created > cutoff or p.status == "applied":
            to_keep.append(p)
        else:
            removed += 1
            # Smazat patch soubor
            patch_file = self.store.patch_dir / f"{p.proposal_id}.patch"
            patch_file.unlink(missing_ok=True)

    if removed > 0:
        self.store.save_all(to_keep)
    return removed
```

---

### 1.5 API Providers: Circuit Breaker Pattern

**Problém:** Cascade failures když provider padá.

**Řešení:**
```python
# src/mycoder/api_providers.py - nová třída

from enum import Enum
from dataclasses import dataclass
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normální provoz
    OPEN = "open"          # Provider blokován
    HALF_OPEN = "half_open"  # Testovací režim

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_max_calls: int = 3

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    half_open_calls: int = 0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        # HALF_OPEN
        return self.half_open_calls < self.half_open_max_calls

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Integrace do BaseAPIProvider
class BaseAPIProvider(ABC):
    def __init__(self, config: APIProviderConfig):
        # ... existing init
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.config.get("circuit_breaker_threshold", 5),
            recovery_timeout=config.config.get("circuit_breaker_timeout", 60),
        )

    async def can_handle_request(self, context: Dict[str, Any] = None) -> bool:
        if not self.circuit_breaker.can_execute():
            logger.info(f"Circuit breaker OPEN for {self.config.provider_type.value}")
            return False
        # ... rest of existing logic
```

---

### 1.6 API Providers: Rate Limiting

**Problém:** Může dojít k překročení rate limitů API.

**Řešení:**
```python
# src/mycoder/api_providers.py - nová třída

import asyncio
from collections import deque

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()
        self.request_times: deque = deque(maxlen=requests_per_minute)

    async def acquire(self) -> None:
        """Wait until a request can be made."""
        self._refill()

        while self.tokens <= 0:
            await asyncio.sleep(0.1)
            self._refill()

        self.tokens -= 1
        self.request_times.append(time.time())

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = int(elapsed * (self.rpm / 60))

        if refill_amount > 0:
            self.tokens = min(self.rpm, self.tokens + refill_amount)
            self.last_refill = now

# Integrace - každý provider má vlastní rate limiter
class ClaudeAnthropicProvider(BaseAPIProvider):
    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.config.get("rate_limit_rpm", 60)
        )

    async def query(self, prompt: str, context: Dict[str, Any] = None, **kwargs) -> APIResponse:
        await self.rate_limiter.acquire()
        # ... rest of query logic
```

---

### 1.7 API Providers: Lightweight Health Check

**Problém:** Health check používá plné API volání, plýtvá kredity.

**Řešení:**
```python
# src/mycoder/api_providers.py

class ClaudeAnthropicProvider(BaseAPIProvider):
    async def health_check(self) -> APIProviderStatus:
        """Lightweight health check without full API call."""
        try:
            if not self.api_key:
                return APIProviderStatus.UNAVAILABLE

            # Pouze ověřit že API endpoint odpovídá
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                # HEAD request nebo minimální endpoint
                async with session.get(
                    f"{self.base_url}/v1/models",
                    headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
                ) as response:
                    if response.status == 200:
                        return APIProviderStatus.HEALTHY
                    elif response.status == 401:
                        return APIProviderStatus.UNAVAILABLE  # Invalid key
                    else:
                        return APIProviderStatus.DEGRADED
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE
```

---

## ČÁST 2: Nové funkce z Claude Code CLI (PRIORITA: STŘEDNÍ-VYSOKÁ)

### 2.1 Agent Orchestration System

**Popis:** Claude Code používá specializované agenty pro různé úkoly (Explore, Plan, Bash, general-purpose).

**Implementace:**

```python
# src/mycoder/agents/__init__.py
"""Agent orchestration system inspired by Claude Code CLI."""

from .base import BaseAgent, AgentResult
from .explore import ExploreAgent
from .plan import PlanAgent
from .bash import BashAgent
from .general import GeneralPurposeAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    "BaseAgent", "AgentResult",
    "ExploreAgent", "PlanAgent", "BashAgent", "GeneralPurposeAgent",
    "AgentOrchestrator"
]
```

```python
# src/mycoder/agents/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

class AgentType(Enum):
    EXPLORE = "explore"
    PLAN = "plan"
    BASH = "bash"
    GENERAL = "general"

@dataclass
class AgentResult:
    success: bool
    content: str
    agent_type: AgentType
    metadata: Dict[str, Any] = None
    error: Optional[str] = None

class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, coder, working_directory: Path):
        self.coder = coder
        self.working_dir = working_directory
        self.context: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of agent capabilities."""
        pass

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """Execute the agent's task."""
        pass

    def add_context(self, item: Dict[str, Any]) -> None:
        self.context.append(item)
```

```python
# src/mycoder/agents/explore.py
"""Fast agent for exploring codebases."""

import asyncio
from pathlib import Path
from typing import Dict, Any, List
import fnmatch

from .base import BaseAgent, AgentResult, AgentType

class ExploreAgent(BaseAgent):
    """
    Agent pro rychlé prozkoumávání codebase.

    Schopnosti:
    - Hledání souborů podle patternu (glob)
    - Vyhledávání v kódu (grep)
    - Odpovídání na otázky o struktuře projektu
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.EXPLORE

    @property
    def description(self) -> str:
        return "Fast codebase exploration: find files, search code, understand structure"

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        thoroughness = context.get("thoroughness", "medium") if context else "medium"

        # Analyzovat úkol
        if self._is_file_search(task):
            result = await self._search_files(task, thoroughness)
        elif self._is_code_search(task):
            result = await self._search_code(task, thoroughness)
        else:
            result = await self._explore_structure(task, thoroughness)

        return AgentResult(
            success=True,
            content=result,
            agent_type=self.agent_type,
            metadata={"thoroughness": thoroughness}
        )

    def _is_file_search(self, task: str) -> bool:
        keywords = ["find file", "where is", "locate", "*.py", "*.js", "*.ts"]
        return any(kw in task.lower() for kw in keywords)

    def _is_code_search(self, task: str) -> bool:
        keywords = ["search for", "find code", "grep", "where is function", "class"]
        return any(kw in task.lower() for kw in keywords)

    async def _search_files(self, task: str, thoroughness: str) -> str:
        # Implementace glob search
        patterns = self._extract_patterns(task)
        results = []

        for pattern in patterns:
            matches = list(self.working_dir.rglob(pattern))
            results.extend(matches[:50])  # Limit

        if not results:
            return "No files found matching the pattern."

        return "\n".join(str(p.relative_to(self.working_dir)) for p in results)

    async def _search_code(self, task: str, thoroughness: str) -> str:
        # Implementace grep-like search
        import subprocess

        search_term = self._extract_search_term(task)
        if not search_term:
            return "Could not determine search term."

        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", search_term, str(self.working_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout[:5000] if result.stdout else "No matches found."
        except Exception as e:
            return f"Search error: {e}"

    async def _explore_structure(self, task: str, thoroughness: str) -> str:
        # Vrátit strukturu projektu
        structure = []
        for item in sorted(self.working_dir.iterdir()):
            if item.name.startswith('.'):
                continue
            prefix = "📁" if item.is_dir() else "📄"
            structure.append(f"{prefix} {item.name}")

        return "\n".join(structure)

    def _extract_patterns(self, task: str) -> List[str]:
        import re
        patterns = re.findall(r'\*\.\w+|\*\*/\*\.\w+', task)
        return patterns if patterns else ["*.py"]

    def _extract_search_term(self, task: str) -> str:
        import re
        # Hledat text v uvozovkách nebo po "for"
        quoted = re.search(r'["\']([^"\']+)["\']', task)
        if quoted:
            return quoted.group(1)

        for_match = re.search(r'(?:search|find|grep)\s+(?:for\s+)?(\w+)', task.lower())
        if for_match:
            return for_match.group(1)

        return ""
```

```python
# src/mycoder/agents/plan.py
"""Software architect agent for designing implementation plans."""

from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

from .base import BaseAgent, AgentResult, AgentType

@dataclass
class PlanStep:
    step_number: int
    description: str
    files_affected: List[str]
    estimated_complexity: str  # low, medium, high

@dataclass
class ImplementationPlan:
    summary: str
    steps: List[PlanStep]
    critical_files: List[str]
    risks: List[str]
    dependencies: List[str]

class PlanAgent(BaseAgent):
    """
    Agent pro plánování implementace.

    Schopnosti:
    - Analyzovat požadavky
    - Navrhnout kroky implementace
    - Identifikovat kritické soubory
    - Zvážit architektonické trade-offs
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.PLAN

    @property
    def description(self) -> str:
        return "Design implementation plans, identify critical files, consider trade-offs"

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        # Použít AI k vygenerování plánu
        plan_prompt = self._build_plan_prompt(task, context)

        response = await self.coder.process_request(
            plan_prompt,
            use_tools=False
        )

        content = response.get("content") if isinstance(response, dict) else str(response)

        return AgentResult(
            success=True,
            content=content,
            agent_type=self.agent_type,
            metadata={"task": task}
        )

    def _build_plan_prompt(self, task: str, context: Dict[str, Any] = None) -> str:
        return f"""You are a software architect. Create an implementation plan for:

Task: {task}

Project context:
- Working directory: {self.working_dir}
- Language: Python 3.10+
- Framework: MyCoder AI assistant

Provide:
1. Summary of approach
2. Step-by-step implementation (no time estimates)
3. Critical files to modify
4. Potential risks
5. Dependencies to add (if any)

Format as structured markdown."""
```

```python
# src/mycoder/agents/orchestrator.py
"""Agent orchestrator for managing multiple agents."""

from typing import Dict, Any, List, Optional
from pathlib import Path

from .base import BaseAgent, AgentResult, AgentType
from .explore import ExploreAgent
from .plan import PlanAgent
from .bash import BashAgent
from .general import GeneralPurposeAgent

class AgentOrchestrator:
    """
    Orchestrátor agentů - vybírá a spouští vhodného agenta.
    """

    def __init__(self, coder, working_directory: Path):
        self.coder = coder
        self.working_dir = working_directory

        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.EXPLORE: ExploreAgent(coder, working_directory),
            AgentType.PLAN: PlanAgent(coder, working_directory),
            AgentType.BASH: BashAgent(coder, working_directory),
            AgentType.GENERAL: GeneralPurposeAgent(coder, working_directory),
        }

        self.running_agents: Dict[str, BaseAgent] = {}
        self.agent_history: List[AgentResult] = []

    async def spawn_agent(
        self,
        agent_type: AgentType,
        task: str,
        context: Dict[str, Any] = None,
        run_in_background: bool = False
    ) -> AgentResult:
        """Spawn an agent to handle a task."""
        agent = self.agents.get(agent_type)
        if not agent:
            return AgentResult(
                success=False,
                content="",
                agent_type=agent_type,
                error=f"Unknown agent type: {agent_type}"
            )

        if run_in_background:
            import asyncio
            import uuid

            agent_id = str(uuid.uuid4())[:8]
            task_coro = agent.execute(task, context)
            asyncio.create_task(self._run_background_agent(agent_id, task_coro))

            return AgentResult(
                success=True,
                content=f"Agent {agent_id} started in background",
                agent_type=agent_type,
                metadata={"agent_id": agent_id, "background": True}
            )

        result = await agent.execute(task, context)
        self.agent_history.append(result)
        return result

    async def _run_background_agent(self, agent_id: str, coro) -> None:
        try:
            result = await coro
            self.agent_history.append(result)
        except Exception as e:
            # Log error
            pass

    def select_agent(self, task: str) -> AgentType:
        """Automatically select best agent for task."""
        task_lower = task.lower()

        # Explore patterns
        explore_keywords = ["find", "search", "where", "locate", "structure", "list files"]
        if any(kw in task_lower for kw in explore_keywords):
            return AgentType.EXPLORE

        # Plan patterns
        plan_keywords = ["plan", "design", "architect", "how to implement", "strategy"]
        if any(kw in task_lower for kw in plan_keywords):
            return AgentType.PLAN

        # Bash patterns
        bash_keywords = ["run", "execute", "command", "git", "npm", "poetry", "make"]
        if any(kw in task_lower for kw in bash_keywords):
            return AgentType.BASH

        # Default to general
        return AgentType.GENERAL

    async def auto_execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """Automatically select and execute appropriate agent."""
        agent_type = self.select_agent(task)
        return await self.spawn_agent(agent_type, task, context)
```

**Soubory k vytvoření:**
- `src/mycoder/agents/__init__.py`
- `src/mycoder/agents/base.py`
- `src/mycoder/agents/explore.py`
- `src/mycoder/agents/plan.py`
- `src/mycoder/agents/bash.py`
- `src/mycoder/agents/general.py`
- `src/mycoder/agents/orchestrator.py`

---

### 2.2 Plan Mode Workflow

**Popis:** Claude Code má EnterPlanMode/ExitPlanMode pro plánování s user approval.

**Implementace:**

```python
# src/mycoder/plan_mode.py
"""Plan mode workflow for user-approved implementations."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum

class PlanModeState(Enum):
    INACTIVE = "inactive"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"

@dataclass
class PlanItem:
    step: int
    description: str
    status: str  # pending, in_progress, completed, skipped
    files: List[str]

@dataclass
class Plan:
    plan_id: str
    title: str
    items: List[PlanItem]
    created_at: str
    approved_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", ""]
        for item in self.items:
            status_icon = {
                "pending": "⬜",
                "in_progress": "🔄",
                "completed": "✅",
                "skipped": "⏭️"
            }.get(item.status, "⬜")

            lines.append(f"{status_icon} **Step {item.step}:** {item.description}")
            if item.files:
                lines.append(f"   Files: {', '.join(item.files)}")

        return "\n".join(lines)

class PlanModeManager:
    """Manage plan mode workflow."""

    def __init__(self, coder, working_directory: Path):
        self.coder = coder
        self.working_dir = working_directory
        self.state = PlanModeState.INACTIVE
        self.current_plan: Optional[Plan] = None
        self.plan_file: Optional[Path] = None

    async def enter_plan_mode(self, task: str) -> Dict[str, Any]:
        """Enter plan mode for a task."""
        if self.state != PlanModeState.INACTIVE:
            return {"error": "Already in plan mode"}

        self.state = PlanModeState.PLANNING
        self.plan_file = self.working_dir / ".mycoder" / "current_plan.md"
        self.plan_file.parent.mkdir(parents=True, exist_ok=True)

        return {
            "status": "planning",
            "message": f"Entered plan mode for: {task}",
            "plan_file": str(self.plan_file)
        }

    async def create_plan(self, task: str) -> Plan:
        """Use AI to create implementation plan."""
        from datetime import datetime, timezone
        import uuid

        # Generovat plán pomocí AI
        plan_response = await self.coder.process_request(
            f"Create a step-by-step implementation plan for: {task}\n"
            "Return JSON with: title, steps (each with: step, description, files)",
            use_tools=False
        )

        # Parse response
        content = plan_response.get("content") if isinstance(plan_response, dict) else str(plan_response)
        plan_data = self._parse_plan_json(content)

        items = [
            PlanItem(
                step=s.get("step", i+1),
                description=s.get("description", ""),
                status="pending",
                files=s.get("files", [])
            )
            for i, s in enumerate(plan_data.get("steps", []))
        ]

        self.current_plan = Plan(
            plan_id=str(uuid.uuid4())[:8],
            title=plan_data.get("title", task),
            items=items,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Uložit do souboru
        self.plan_file.write_text(self.current_plan.to_markdown())
        self.state = PlanModeState.AWAITING_APPROVAL

        return self.current_plan

    async def exit_plan_mode(self, approved: bool = False) -> Dict[str, Any]:
        """Exit plan mode, optionally with approval."""
        if self.state == PlanModeState.INACTIVE:
            return {"error": "Not in plan mode"}

        if approved and self.current_plan:
            from datetime import datetime, timezone
            self.current_plan.approved_at = datetime.now(timezone.utc).isoformat()
            self.state = PlanModeState.EXECUTING
            return {
                "status": "approved",
                "plan": self.current_plan.to_markdown()
            }

        self.state = PlanModeState.INACTIVE
        self.current_plan = None
        return {"status": "cancelled"}

    async def execute_plan(self) -> Dict[str, Any]:
        """Execute approved plan step by step."""
        if self.state != PlanModeState.EXECUTING or not self.current_plan:
            return {"error": "No approved plan to execute"}

        results = []
        for item in self.current_plan.items:
            if item.status == "completed":
                continue

            item.status = "in_progress"
            self.plan_file.write_text(self.current_plan.to_markdown())

            # Execute step
            result = await self.coder.process_request(
                f"Execute step {item.step}: {item.description}",
                use_tools=True
            )

            item.status = "completed"
            results.append({
                "step": item.step,
                "result": result
            })

        from datetime import datetime, timezone
        self.current_plan.completed_at = datetime.now(timezone.utc).isoformat()
        self.plan_file.write_text(self.current_plan.to_markdown())
        self.state = PlanModeState.INACTIVE

        return {"status": "completed", "results": results}

    def _parse_plan_json(self, content: str) -> Dict[str, Any]:
        import json
        import re

        # Zkusit extrahovat JSON
        json_match = re.search(r'```json\s*([\s\S]*?)```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Fallback - vrátit základní strukturu
        return {
            "title": "Implementation Plan",
            "steps": [{"step": 1, "description": content, "files": []}]
        }
```

**CLI integrace:**
```python
# src/mycoder/cli_interactive.py - přidat příkazy

# Nové příkazy:
# /plan <task>     - Vstoupit do plan mode
# /plan approve    - Schválit plán
# /plan cancel     - Zrušit plán
# /plan execute    - Spustit schválený plán
# /plan show       - Zobrazit aktuální plán
```

---

### 2.3 Todo Tracking System

**Popis:** Claude Code používá TodoWrite pro strukturované sledování úkolů.

**Implementace:**

```python
# src/mycoder/todo_tracker.py
"""Todo tracking system for task management."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path
import json
from datetime import datetime, timezone

class TodoStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

@dataclass
class TodoItem:
    content: str
    status: TodoStatus
    active_form: str  # "Running tests", "Fixing bug"...
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    blocked_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "status": self.status.value,
            "active_form": self.active_form,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "blocked_reason": self.blocked_reason,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TodoItem":
        return TodoItem(
            content=data["content"],
            status=TodoStatus(data["status"]),
            active_form=data["active_form"],
            created_at=data.get("created_at", ""),
            completed_at=data.get("completed_at"),
            blocked_reason=data.get("blocked_reason"),
        )

class TodoTracker:
    """Manage todo list for current session."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.todos: List[TodoItem] = []
        self.storage_path = storage_path
        if storage_path and storage_path.exists():
            self._load()

    def write(self, todos: List[Dict[str, Any]]) -> None:
        """Replace entire todo list."""
        self.todos = [
            TodoItem(
                content=t["content"],
                status=TodoStatus(t["status"]),
                active_form=t["activeForm"]
            )
            for t in todos
        ]
        self._save()

    def add(self, content: str, active_form: str) -> TodoItem:
        """Add new todo item."""
        item = TodoItem(
            content=content,
            status=TodoStatus.PENDING,
            active_form=active_form
        )
        self.todos.append(item)
        self._save()
        return item

    def update_status(self, index: int, status: TodoStatus) -> Optional[TodoItem]:
        """Update todo status by index."""
        if 0 <= index < len(self.todos):
            self.todos[index].status = status
            if status == TodoStatus.COMPLETED:
                self.todos[index].completed_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return self.todos[index]
        return None

    def mark_in_progress(self, index: int) -> Optional[TodoItem]:
        """Mark todo as in progress (only one at a time)."""
        # Nejprve zrušit jiné in_progress
        for i, todo in enumerate(self.todos):
            if todo.status == TodoStatus.IN_PROGRESS and i != index:
                todo.status = TodoStatus.PENDING

        return self.update_status(index, TodoStatus.IN_PROGRESS)

    def mark_completed(self, index: int) -> Optional[TodoItem]:
        return self.update_status(index, TodoStatus.COMPLETED)

    def get_current(self) -> Optional[TodoItem]:
        """Get currently in-progress item."""
        for todo in self.todos:
            if todo.status == TodoStatus.IN_PROGRESS:
                return todo
        return None

    def get_pending(self) -> List[TodoItem]:
        return [t for t in self.todos if t.status == TodoStatus.PENDING]

    def render(self) -> str:
        """Render todo list as formatted string."""
        if not self.todos:
            return "No todos."

        lines = []
        for i, todo in enumerate(self.todos, 1):
            status_icon = {
                TodoStatus.PENDING: "⬜",
                TodoStatus.IN_PROGRESS: "🔄",
                TodoStatus.COMPLETED: "✅",
                TodoStatus.BLOCKED: "🚫"
            }.get(todo.status, "⬜")

            if todo.status == TodoStatus.IN_PROGRESS:
                lines.append(f"{i}. {status_icon} [{todo.active_form}] {todo.content}")
            else:
                lines.append(f"{i}. {status_icon} {todo.content}")

        return "\n".join(lines)

    def _save(self) -> None:
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = [t.to_dict() for t in self.todos]
            self.storage_path.write_text(json.dumps(data, indent=2))

    def _load(self) -> None:
        try:
            data = json.loads(self.storage_path.read_text())
            self.todos = [TodoItem.from_dict(t) for t in data]
        except Exception:
            self.todos = []
```

**CLI integrace:**
```python
# Nové příkazy:
# /todo                - Zobrazit todo list
# /todo add <task>     - Přidat úkol
# /todo done <n>       - Označit úkol jako hotový
# /todo start <n>      - Označit úkol jako rozpracovaný
# /todo clear          - Vymazat hotové úkoly
```

---

### 2.4 Web Search & Fetch

**Popis:** Claude Code má WebSearch a WebFetch pro práci s webem.

**Implementace:**

```python
# src/mycoder/web_tools.py
"""Web search and fetch tools."""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str

@dataclass
class WebContent:
    url: str
    content: str
    fetched_at: str
    content_type: str

class WebFetcher:
    """Fetch and process web content."""

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_minutes: int = 15):
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch(self, url: str, prompt: str = "") -> Dict[str, Any]:
        """Fetch URL and optionally process with prompt."""
        # Check cache
        cached = self._get_cached(url)
        if cached:
            return {"success": True, "content": cached, "cached": True}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                # Upgrade HTTP to HTTPS
                if url.startswith("http://"):
                    url = "https://" + url[7:]

                async with session.get(url) as response:
                    if response.status != 200:
                        return {"success": False, "error": f"HTTP {response.status}"}

                    content_type = response.headers.get("content-type", "")

                    if "text/html" in content_type:
                        html = await response.text()
                        content = self._html_to_markdown(html)
                    else:
                        content = await response.text()

                    # Cache result
                    self._cache(url, content)

                    # Process with prompt if provided
                    if prompt:
                        content = await self._process_with_prompt(content, prompt)

                    return {
                        "success": True,
                        "content": content,
                        "url": str(response.url),
                        "cached": False
                    }

        except aiohttp.ClientError as e:
            return {"success": False, "error": str(e)}

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to markdown (simplified)."""
        import re

        # Remove scripts and styles
        html = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.I)
        html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.I)

        # Convert common tags
        html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', html, flags=re.I)
        html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', html, flags=re.I)
        html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', html, flags=re.I)
        html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html, flags=re.I|re.S)
        html = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
        html = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html, flags=re.I)
        html = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.I)
        html = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html, flags=re.I)
        html = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```', html, flags=re.I|re.S)
        html = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html, flags=re.I)
        html = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html, flags=re.I)

        # Remove remaining tags
        html = re.sub(r'<[^>]+>', '', html)

        # Clean up whitespace
        html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
        html = html.strip()

        return html[:50000]  # Limit size

    async def _process_with_prompt(self, content: str, prompt: str) -> str:
        """Process content with AI prompt."""
        # Toto by mělo využít coder instance
        return f"Content summary for: {prompt}\n\n{content[:5000]}"

    def _cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cached(self, url: str) -> Optional[str]:
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{self._cache_key(url)}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text())
            cached_at = datetime.fromisoformat(data["fetched_at"])
            if datetime.now() - cached_at < self.cache_ttl:
                return data["content"]
        except Exception:
            pass

        return None

    def _cache(self, url: str, content: str) -> None:
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{self._cache_key(url)}.json"
        data = {
            "url": url,
            "content": content,
            "fetched_at": datetime.now().isoformat()
        }
        cache_file.write_text(json.dumps(data))


class WebSearcher:
    """Web search using available search APIs."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def search(
        self,
        query: str,
        allowed_domains: List[str] = None,
        blocked_domains: List[str] = None
    ) -> List[SearchResult]:
        """
        Perform web search.

        Poznámka: Vyžaduje API klíč pro search provider (Google, Bing, DuckDuckGo API).
        """
        # Placeholder - v reálné implementaci použít search API
        # Např. Google Custom Search, Bing Web Search, nebo SerpAPI

        return [
            SearchResult(
                title=f"Search result for: {query}",
                url="https://example.com",
                snippet="Web search requires API configuration."
            )
        ]
```

**CLI integrace:**
```python
# Nové příkazy:
# /web fetch <url>           - Stáhnout a zobrazit web stránku
# /web search <query>        - Vyhledat na webu
```

---

### 2.5 Enhanced Edit Tool

**Popis:** Claude Code má Edit tool s validací unique stringu.

**Implementace:**

```python
# src/mycoder/tools/edit_tool.py
"""Enhanced file editing tool with unique string validation."""

from dataclasses import dataclass
from typing import Optional, Tuple
from pathlib import Path

@dataclass
class EditResult:
    success: bool
    message: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None

class EditTool:
    """
    Edit tool s validací unique stringu.

    Pravidla:
    - old_string musí být unikátní v souboru
    - Zachovat přesnou indentaci
    - Podpora replace_all pro hromadné nahrazení
    """

    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.read_files: set = set()  # Tracking přečtených souborů

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False
    ) -> EditResult:
        """
        Perform edit with validation.

        Args:
            file_path: Absolutní cesta k souboru
            old_string: Text k nahrazení (musí být unikátní pokud ne replace_all)
            new_string: Nový text
            replace_all: Nahradit všechny výskyty
        """
        path = Path(file_path)

        # Validace - soubor musí být nejdřív přečten
        if str(path) not in self.read_files:
            return EditResult(
                success=False,
                message=f"File must be read before editing: {file_path}"
            )

        if not path.exists():
            return EditResult(
                success=False,
                message=f"File not found: {file_path}"
            )

        content = path.read_text(encoding="utf-8")

        # Počet výskytů
        count = content.count(old_string)

        if count == 0:
            return EditResult(
                success=False,
                message=f"String not found in file: {old_string[:50]}..."
            )

        if count > 1 and not replace_all:
            return EditResult(
                success=False,
                message=f"String is not unique ({count} occurrences). "
                        f"Use replace_all=True or provide more context."
            )

        # Provést nahrazení
        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        # Uložit
        path.write_text(new_content, encoding="utf-8")

        return EditResult(
            success=True,
            message=f"Replaced {count if replace_all else 1} occurrence(s)",
            old_content=content,
            new_content=new_content
        )

    def mark_as_read(self, file_path: str) -> None:
        """Mark file as read (required before editing)."""
        self.read_files.add(file_path)

    def validate_edit(
        self,
        file_path: str,
        old_string: str
    ) -> Tuple[bool, str]:
        """
        Validate edit without performing it.

        Returns:
            (is_valid, message)
        """
        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        content = path.read_text(encoding="utf-8")
        count = content.count(old_string)

        if count == 0:
            return False, "String not found"
        if count > 1:
            return False, f"String not unique ({count} occurrences)"

        return True, "Valid edit"
```

---

### 2.6 MCP Server Support (základní)

**Popis:** Model Context Protocol pro rozšiřitelnost.

**Implementace:**

```python
# src/mycoder/mcp/__init__.py
"""Basic MCP (Model Context Protocol) support."""

from .server import MCPServer
from .client import MCPClient
from .protocol import MCPMessage, MCPTool

__all__ = ["MCPServer", "MCPClient", "MCPMessage", "MCPTool"]
```

```python
# src/mycoder/mcp/protocol.py
"""MCP Protocol definitions."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

class MCPMessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"

@dataclass
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters
            }
        }

@dataclass
class MCPMessage:
    type: MCPMessageType
    method: str
    params: Dict[str, Any] = None
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
```

```python
# src/mycoder/mcp/client.py
"""MCP Client for connecting to MCP servers."""

import asyncio
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .protocol import MCPMessage, MCPMessageType, MCPTool

class MCPClient:
    """Client for communicating with MCP servers."""

    def __init__(self):
        self.servers: Dict[str, "MCPServerConnection"] = {}
        self.available_tools: Dict[str, MCPTool] = {}

    async def connect(self, server_name: str, command: List[str]) -> bool:
        """Connect to an MCP server."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.servers[server_name] = MCPServerConnection(
                name=server_name,
                process=process
            )

            # Initialize and get tools
            tools = await self._initialize_server(server_name)
            for tool in tools:
                self.available_tools[f"{server_name}:{tool.name}"] = tool

            return True
        except Exception as e:
            return False

    async def _initialize_server(self, server_name: str) -> List[MCPTool]:
        """Initialize server and get available tools."""
        conn = self.servers.get(server_name)
        if not conn:
            return []

        # Send initialize request
        response = await self._send_request(
            server_name,
            "initialize",
            {"capabilities": {}}
        )

        # Get tools list
        tools_response = await self._send_request(
            server_name,
            "tools/list",
            {}
        )

        tools = []
        for tool_data in tools_response.get("tools", []):
            tools.append(MCPTool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                parameters=tool_data.get("inputSchema", {}).get("properties", {})
            ))

        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on connected MCP server."""
        if ":" in tool_name:
            server_name, tool = tool_name.split(":", 1)
        else:
            # Find server that has this tool
            for full_name, _ in self.available_tools.items():
                if full_name.endswith(f":{tool_name}"):
                    server_name, tool = full_name.split(":", 1)
                    break
            else:
                return {"error": f"Tool not found: {tool_name}"}

        return await self._send_request(
            server_name,
            "tools/call",
            {"name": tool, "arguments": arguments}
        )

    async def _send_request(
        self,
        server_name: str,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send request to MCP server."""
        conn = self.servers.get(server_name)
        if not conn or not conn.process.stdin:
            return {"error": "Server not connected"}

        import uuid
        request_id = str(uuid.uuid4())

        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        conn.process.stdin.write(
            (json.dumps(message) + "\n").encode()
        )
        await conn.process.stdin.drain()

        # Read response
        if conn.process.stdout:
            line = await conn.process.stdout.readline()
            response = json.loads(line.decode())
            return response.get("result", {})

        return {}

    def get_available_tools(self) -> List[MCPTool]:
        """Get all available tools from connected servers."""
        return list(self.available_tools.values())

@dataclass
class MCPServerConnection:
    name: str
    process: asyncio.subprocess.Process
```

---

## ČÁST 3: CLI Command Updates

### Nové příkazy k implementaci

```python
# src/mycoder/cli_interactive.py - rozšířit COMMANDS

NEW_COMMANDS = {
    # Agent commands
    "/agent explore <task>": "Spustit Explore agenta",
    "/agent plan <task>": "Spustit Plan agenta",
    "/agent bash <command>": "Spustit Bash agenta",

    # Plan mode
    "/plan <task>": "Vstoupit do plan mode",
    "/plan approve": "Schválit plán",
    "/plan cancel": "Zrušit plán",
    "/plan execute": "Spustit schválený plán",
    "/plan show": "Zobrazit aktuální plán",

    # Todo tracking
    "/todo": "Zobrazit todo list",
    "/todo add <task>": "Přidat úkol",
    "/todo done <n>": "Označit úkol jako hotový",
    "/todo start <n>": "Začít práci na úkolu",
    "/todo clear": "Vymazat hotové úkoly",

    # Web tools
    "/web fetch <url>": "Stáhnout web stránku",
    "/web search <query>": "Vyhledat na webu",

    # Self-evolve updates
    "/evolve propose": "Vygenerovat návrh opravy",
    "/evolve apply <id>": "Aplikovat návrh (s approval)",
    "/evolve dry-run <id>": "Otestovat návrh v sandboxu",
    "/evolve list": "Zobrazit všechny návrhy",
    "/evolve show <id>": "Zobrazit detail návrhu",

    # MCP
    "/mcp connect <server>": "Připojit MCP server",
    "/mcp tools": "Zobrazit dostupné MCP nástroje",
    "/mcp call <tool> <args>": "Zavolat MCP nástroj",
}
```

---

## ČÁST 4: Testy

### Nové test soubory k vytvoření

```
tests/unit/test_agents.py
tests/unit/test_plan_mode.py
tests/unit/test_todo_tracker.py
tests/unit/test_web_tools.py
tests/unit/test_edit_tool.py
tests/unit/test_circuit_breaker.py
tests/unit/test_rate_limiter.py
tests/unit/test_mcp_client.py

tests/integration/test_agent_orchestration.py
tests/integration/test_plan_mode_workflow.py
tests/integration/test_self_evolve_approval.py
```

---

## ČÁST 5: Dependencies Update

```toml
# pyproject.toml - přidat

[tool.poetry.dependencies]
filelock = "^3.13.0"
aiohttp = "^3.9.0"  # Již existuje, jen ověřit verzi

[tool.poetry.group.dev.dependencies]
# Beze změn
```

---

## Pořadí implementace (doporučené)

### Fáze 1: Kritické opravy (ASAP)
1. Self-Evolve user approval
2. Self-Evolve dry-run mode
3. ProposalStore filelock
4. Circuit breaker

### Fáze 2: API vylepšení
5. Rate limiter
6. Lightweight health checks
7. Proposal cleanup/limits

### Fáze 3: Nové funkce - Core
8. Todo Tracker
9. Enhanced Edit Tool
10. Plan Mode

### Fáze 4: Nové funkce - Agents
11. Agent base classes
12. Explore Agent
13. Plan Agent
14. Bash Agent
15. Agent Orchestrator

### Fáze 5: Nové funkce - Web & MCP
16. Web Fetcher
17. Web Searcher
18. MCP Protocol
19. MCP Client

### Fáze 6: CLI & Testy
20. CLI command updates
21. Unit testy
22. Integration testy

---

## Poznámky pro Codex

1. **Zachovat zpětnou kompatibilitu** - existující API nesmí být broken
2. **Dodržovat stávající coding style** - Black, isort, type hints
3. **Thermal awareness** - nové komponenty musí respektovat thermal management
4. **Dokumentace** - aktualizovat CLAUDE.md a AGENTS.md po změnách
5. **Testy** - každá nová funkce musí mít unit testy
6. **Incremental commits** - commity po každé dokončené fázi

---

## Akceptační kritéria

- [ ] Všechny unit testy procházejí
- [ ] Žádné regrese v existujících funkcích
- [ ] Self-evolve vyžaduje user approval před apply
- [ ] Dry-run mode funguje v izolovaném prostředí
- [ ] Circuit breaker správně blokuje failing providery
- [ ] Todo tracker persistuje mezi sessions
- [ ] Plan mode workflow funguje end-to-end
- [ ] Agent orchestrator správně routuje úkoly
- [ ] Web fetch stahuje a parsuje HTML
- [ ] MCP client se připojuje k serverům
- [ ] Všechny nové CLI příkazy fungují
- [ ] Dokumentace je aktualizována
