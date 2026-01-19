"""
Unified Context Manager for Next-Gen MyCoder.

Responsibility:
1. Load & Merge Configuration (Global -> Project -> Local)
2. Load & Assemble Context (AGENTS.md, etc.)
3. Provide Single Source of Truth for Agent Logic
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Try importing toml support
try:
    import tomllib as toml  # Python 3.11+
except ImportError:
    try:
        import toml
    except ImportError:
        toml = None

logger = logging.getLogger(__name__)

@dataclass
class ContextData:
    """Holds the assembled context and configuration."""
    config: Dict[str, Any] = field(default_factory=dict)
    system_prompt: str = ""
    project_root: Path = field(default_factory=Path.cwd)
    loaded_files: List[str] = field(default_factory=list)

class ContextManager:
    """
    Manages hierarchal configuration and context loading.
    """

    CONFIG_FILENAMES = ["config.json", "mycoder_config.json", "config.toml"]
    CONTEXT_FILENAMES = ["AGENTS.md", "PROJECT_CONTEXT.md", "CLAUDE.md", "GEMINI.md"]

    def __init__(self, start_path: Optional[Path] = None):
        self.start_path = start_path or Path.cwd()
        self.global_config_path = Path.home() / ".config" / "mycoder"
        self._cache: Dict[str, ContextData] = {}

    def get_context(self, force_reload: bool = False) -> ContextData:
        """
        Retrieves the full context (config + prompt).
        Uses caching to ensure speed on mobile devices.
        """
        cache_key = str(self.start_path)
        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]

        logger.info(f"Loading context for {self.start_path}...")

        # 1. Determine Hierarchy
        hierarchy = self._discover_hierarchy()

        # 2. Merge Configuration
        merged_config = self._load_defaults()

        loaded_files = []

        for path in hierarchy:
            local_conf, loaded_file = self._load_config_from_dir(path)
            if local_conf:
                merged_config = self._deep_merge(merged_config, local_conf)
                if loaded_file:
                    loaded_files.append(str(loaded_file))

        # 3. Assemble System Prompt (Context)
        project_root = self._find_project_root(self.start_path)
        system_prompt, context_file = self._load_project_context(project_root)
        if context_file:
            loaded_files.append(str(context_file))

        # 4. Environment Variables Override
        merged_config = self._apply_env_overrides(merged_config)

        context_data = ContextData(
            config=merged_config,
            system_prompt=system_prompt,
            project_root=project_root,
            loaded_files=loaded_files
        )

        self._cache[cache_key] = context_data
        return context_data

    def _discover_hierarchy(self) -> List[Path]:
        """
        Returns list of paths to check for config, from Global -> Root -> Local.
        """
        paths = []

        # Global
        paths.append(self.global_config_path)

        # Project Root to Current Dir
        project_root = self._find_project_root(self.start_path)

        # Traverse from root to current
        if project_root in self.start_path.parents or project_root == self.start_path:
            try:
                rel = self.start_path.relative_to(project_root)
                parts = rel.parts
                current = project_root
                paths.append(current)
                for part in parts:
                    current = current / part
                    paths.append(current)
            except ValueError:
                paths.append(self.start_path)
        else:
            paths.append(self.start_path)

        return paths

    def _find_project_root(self, current_path: Path) -> Path:
        """
        Finds project root by looking for markers.
        """
        markers = {".git", "pyproject.toml", "AGENTS.md", "CLAUDE.md", "GEMINI.md"}

        path = current_path.resolve()
        # Traverse upwards
        for parent in [path] + list(path.parents):
            if any((parent / marker).exists() for marker in markers):
                return parent
        return current_path

    def _load_config_from_dir(self, directory: Path) -> tuple[Dict[str, Any], Optional[Path]]:
        """Loads config from a directory, checking supported filenames."""
        # Check for TOML first if supported
        if toml:
            toml_path = directory / "config.toml"
            if toml_path.exists():
                try:
                    with open(toml_path, "rb") as f:
                        return toml.load(f), toml_path
                except Exception as e:
                    logger.warning(f"Failed to load TOML config from {toml_path}: {e}")

        # Check for JSON
        for name in self.CONFIG_FILENAMES:
            if name.endswith(".toml"): continue

            p = directory / name
            if p.exists():
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                        return data, p
                except Exception as e:
                    logger.warning(f"Failed to load JSON config from {p}: {e}")

        return {}, None

    def _load_project_context(self, root: Path) -> tuple[str, Optional[Path]]:
        """Loads AGENTS.md or equivalent from project root."""
        content = ""
        loaded_path = None
        for name in self.CONTEXT_FILENAMES:
            p = root / name
            if p.exists():
                try:
                    text = p.read_text(encoding="utf-8")
                    content = f"\n\n--- Project Context ({name}) ---\n{text}"
                    loaded_path = p
                    break
                except Exception as e:
                    logger.error(f"Failed to read context file {p}: {e}")
        return content, loaded_path

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merges two dictionaries."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _load_defaults(self) -> Dict[str, Any]:
        """Hardcoded defaults."""
        return {
            "claude_anthropic": {
                "enabled": True,
                "model": "claude-3-5-sonnet-20241022",
                "timeout_seconds": 30
            },
            "ollama_local": {
                "enabled": True,
                "base_url": "http://localhost:11434",
                "timeout_seconds": 60
            },
            "thermal": {
                "enabled": True,
                "max_temp": 80,
                "critical_temp": 85,
                "check_interval": 30
            },
            "security": {
                "sandbox_enabled": True,
                "allowed_paths": []
            },
            "system": {
                "working_directory": str(self.start_path)
            }
        }

    def save_config(self, config: Dict[str, Any], path: Optional[Path] = None):
        """Saves configuration to file (default: global config)."""
        target = path or (self.global_config_path / "config.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(target, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Config saved to {target}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Applies MYCODER_* environment variables."""
        if os.environ.get("MYCODER_PREFERRED_PROVIDER"):
            config["preferred_provider"] = os.environ["MYCODER_PREFERRED_PROVIDER"]

        if os.environ.get("ANTHROPIC_API_KEY"):
             config.setdefault("claude_anthropic", {})["api_key"] = os.environ["ANTHROPIC_API_KEY"]

        if os.environ.get("GEMINI_API_KEY"):
             config.setdefault("gemini", {})["api_key"] = os.environ["GEMINI_API_KEY"]

        return config
