"""
Persistent Rate Limiter for API Providers.
Ensures rate limits are respected across application restarts.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    """State of rate limits for a specific provider."""

    last_request_time: float = 0.0
    minute_request_count: int = 0
    minute_window_start: float = 0.0
    daily_request_count: int = 0
    day_window_start: float = 0.0


class PersistentRateLimiter:
    """
    Rate limiter that persists state to disk.
    Supports RPM (Requests Per Minute) and RPD (Requests Per Day) limits.
    """

    DEFAULT_STATE_PATH = Path.home() / ".config" / "mycoder" / "rate_limits.json"

    def __init__(
        self,
        provider_id: str,
        rpm: int = 60,
        rpd: int = 1500,
        state_path: Optional[Path] = None,
    ):
        """
        Initialize persistent rate limiter.

        Args:
            provider_id: Unique identifier for the provider (e.g., "gemini")
            rpm: Requests per minute limit
            rpd: Requests per day limit
            state_path: Path to state file (default: ~/.config/mycoder/rate_limits.json)
        """
        self.provider_id = provider_id
        self.rpm = rpm
        self.rpd = rpd
        self.state_path = state_path or self.DEFAULT_STATE_PATH
        self.state = RateLimitState()
        self._lock = asyncio.Lock()

        # Load initial state
        self._load_state()

    async def acquire(self) -> None:
        """
        Acquire a token to make a request.
        Waits if limits are exceeded.
        """
        async with self._lock:
            while True:
                now = time.time()
                self._update_windows(now)

                # Check Daily Limit
                if self.rpd > 0 and self.state.daily_request_count >= self.rpd:
                    wait_time = (self.state.day_window_start + 86400) - now
                    if wait_time > 0:
                        logger.warning(
                            f"Daily rate limit reached for {self.provider_id}. "
                            f"Waiting {wait_time:.0f}s"
                        )
                        # We don't want to actually sleep for hours in the loop,
                        # but for safety we raise or return error?
                        # For now, let's just log and raise an exception or sleep if it's short.
                        # Given strict requirements, we should probably fail hard or wait.
                        # However, blocking for hours is bad UX.
                        # Let's throw an exception if wait is > 60s
                        if wait_time > 60:
                             raise Exception(f"Daily rate limit exceeded for {self.provider_id}. Resets in {wait_time/3600:.1f} hours.")

                        await asyncio.sleep(wait_time)
                        continue

                # Check Minute Limit
                if self.rpm > 0 and self.state.minute_request_count >= self.rpm:
                    wait_time = (self.state.minute_window_start + 60) - now
                    if wait_time > 0:
                        logger.debug(
                            f"Minute rate limit reached for {self.provider_id}. "
                            f"Waiting {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                # All good, increment counts and save
                self.state.minute_request_count += 1
                self.state.daily_request_count += 1
                self.state.last_request_time = now
                self._save_state()
                return

    def _update_windows(self, now: float) -> None:
        """Reset windows if time has passed."""
        # Check minute window
        if now - self.state.minute_window_start >= 60:
            self.state.minute_window_start = now
            self.state.minute_request_count = 0

        # Check day window
        if now - self.state.day_window_start >= 86400:
            self.state.day_window_start = now
            self.state.daily_request_count = 0

    def _load_state(self) -> None:
        """Load state from JSON file."""
        if not self.state_path.exists():
            return

        try:
            with open(self.state_path, "r") as f:
                data = json.load(f)

            provider_data = data.get(self.provider_id, {})
            if provider_data:
                self.state.last_request_time = provider_data.get("last_request", 0.0)
                self.state.minute_request_count = provider_data.get("minute_count", 0)
                self.state.minute_window_start = provider_data.get("minute_start", 0.0)
                self.state.daily_request_count = provider_data.get("daily_count", 0)
                self.state.day_window_start = provider_data.get("day_start", 0.0)

        except Exception as e:
            logger.warning(f"Failed to load rate limit state: {e}")

    def _save_state(self) -> None:
        """Save state to JSON file."""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing data first to preserve other providers
            current_data = {}
            if self.state_path.exists():
                try:
                    with open(self.state_path, "r") as f:
                        current_data = json.load(f)
                except Exception:
                    pass # Overwrite corrupt file

            current_data[self.provider_id] = {
                "last_request": self.state.last_request_time,
                "minute_count": self.state.minute_request_count,
                "minute_start": self.state.minute_window_start,
                "daily_count": self.state.daily_request_count,
                "day_start": self.state.day_window_start,
            }

            with open(self.state_path, "w") as f:
                json.dump(current_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save rate limit state: {e}")
