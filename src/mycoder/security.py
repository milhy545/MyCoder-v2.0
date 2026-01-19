"""
Security Manager for Next-Gen MyCoder.

Responsibility:
1. Application Layer "Soft-Sandboxing"
2. Path Validation & Whitelisting
3. Prevention of Path Traversal Attacks
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


class SecurityError(PermissionError):
    """Raised when an operation violates security policies."""

    pass


class FileSecurityManager:
    """
    Enforces file access policies.
    """

    def __init__(
        self,
        working_directory: Optional[Path] = None,
        additional_allowed_paths: Optional[List[Path]] = None,
    ):
        self.allowed_paths: List[Path] = []

        # Primary Allowed Path: Working Directory
        cwd = (working_directory or Path.cwd()).resolve()
        self.allowed_paths.append(cwd)

        # Secondary Allowed Path: /tmp for temporary operations
        self.allowed_paths.append(Path("/tmp").resolve())

        # Additional user-defined paths
        if additional_allowed_paths:
            for p in additional_allowed_paths:
                try:
                    self.allowed_paths.append(p.resolve())
                except OSError:
                    logger.warning(f"Could not resolve allowed path: {p}")

        # Deduplicate
        self.allowed_paths = list(set(self.allowed_paths))
        logger.info(
            f"Security Sandbox initialized. Allowed paths: {self.allowed_paths}"
        )

    def validate_path(
        self,
        path: Union[str, Path],
        mode: str = "r",
        extra_allowed_paths: Optional[List[Path]] = None,
    ) -> Path:
        """
        Validates if the path is within allowed directories.
        Returns the resolved absolute path.
        Raises SecurityError if violation.
        """
        try:
            # Resolve absolute path, resolving symlinks and '..'
            # strict=False allows resolving paths that don't exist yet (for write)
            target = Path(path).resolve()
        except Exception as e:
            raise SecurityError(f"Invalid path structure: {path}") from e

        # Check against whitelist
        allowed = False
        allowed_paths = list(self.allowed_paths)
        if extra_allowed_paths:
            for extra in extra_allowed_paths:
                try:
                    allowed_paths.append(extra.resolve())
                except Exception:
                    logger.warning(f"Unable to resolve extra allowed path: {extra}")
        for parent in allowed_paths:
            if self._is_subpath(target, parent):
                allowed = True
                break

        if not allowed:
            logger.warning(f"Security Violation: Attempted access to {target}")
            raise SecurityError(
                f"Security Violation: Access to '{target}' is denied. "
                f"Allowed scopes: {[str(p) for p in self.allowed_paths]}"
            )

        return target

    def _is_subpath(self, child: Path, parent: Path) -> bool:
        """Checks if child is inside parent directory."""
        if child == parent:
            return True
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    def guard_tool(self, tool_func):
        """Decorator/Middleware for tool functions."""

        def wrapper(*args, **kwargs):
            # Inspect args for 'path' or 'file_path'
            # This is a heuristic; robust implementation depends on tool signature
            for key, value in kwargs.items():
                if key in ("path", "file_path", "filepath", "cwd"):
                    if isinstance(value, (str, Path)):
                        self.validate_path(value)
            return tool_func(*args, **kwargs)

        return wrapper
