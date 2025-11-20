"""
Text injection module for inserting transcribed text into active windows.

Uses multiple methods to ensure compatibility across different Linux applications.
"""

import logging
import subprocess
import time
from enum import Enum
from typing import Optional

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    pyperclip = None

logger = logging.getLogger(__name__)


class InjectionMethod(Enum):
    """Available text injection methods."""
    XDOTOOL_TYPE = "xdotool_type"  # Direct typing simulation
    XDOTOOL_PASTE = "xdotool_paste"  # Paste via clipboard
    CLIPBOARD_ONLY = "clipboard_only"  # Only copy to clipboard
    AUTO = "auto"  # Automatic selection


class TextInjector:
    """
    Injects text into the currently active window.

    Supports multiple injection methods for compatibility with different applications.
    """

    def __init__(
        self,
        method: InjectionMethod = InjectionMethod.AUTO,
        typing_delay: int = 12,
        use_clipboard_backup: bool = True,
    ):
        """
        Initialize the text injector.

        Args:
            method: Injection method to use
            typing_delay: Delay between keystrokes in milliseconds (for XDOTOOL_TYPE)
            use_clipboard_backup: Whether to backup and restore clipboard
        """
        self.method = method
        self.typing_delay = typing_delay
        self.use_clipboard_backup = use_clipboard_backup

        # Check xdotool availability
        self.xdotool_available = self._check_xdotool()

        if not self.xdotool_available:
            logger.warning(
                "xdotool not found. Install with: sudo apt-get install xdotool"
            )

        if not CLIPBOARD_AVAILABLE:
            logger.warning(
                "pyperclip not available. Install with: poetry install --extras speech"
            )

    def _check_xdotool(self) -> bool:
        """Check if xdotool is available."""
        try:
            result = subprocess.run(
                ["which", "xdotool"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to check xdotool: {e}")
            return False

    def inject_text(self, text: str) -> bool:
        """
        Inject text into the active window.

        Args:
            text: Text to inject

        Returns:
            True if injection was successful, False otherwise
        """
        if not text:
            logger.warning("No text to inject")
            return False

        # Determine injection method
        method = self._select_method()

        logger.info(f"Injecting text using method: {method.value}")

        try:
            if method == InjectionMethod.XDOTOOL_TYPE:
                return self._inject_xdotool_type(text)
            elif method == InjectionMethod.XDOTOOL_PASTE:
                return self._inject_xdotool_paste(text)
            elif method == InjectionMethod.CLIPBOARD_ONLY:
                return self._inject_clipboard_only(text)
            else:
                logger.error(f"Unknown injection method: {method}")
                return False

        except Exception as e:
            logger.error(f"Text injection failed: {e}")
            return False

    def _select_method(self) -> InjectionMethod:
        """Select appropriate injection method based on availability."""
        if self.method != InjectionMethod.AUTO:
            return self.method

        # Automatic selection based on available tools
        if self.xdotool_available:
            # Prefer paste method for better performance with long texts
            return InjectionMethod.XDOTOOL_PASTE
        elif CLIPBOARD_AVAILABLE:
            return InjectionMethod.CLIPBOARD_ONLY
        else:
            logger.error("No injection method available")
            return InjectionMethod.CLIPBOARD_ONLY

    def _inject_xdotool_type(self, text: str) -> bool:
        """Inject text by simulating typing with xdotool."""
        if not self.xdotool_available:
            logger.error("xdotool not available")
            return False

        try:
            # Small delay to ensure focus is ready
            time.sleep(0.1)

            # Use xdotool to type the text
            result = subprocess.run(
                [
                    "xdotool",
                    "type",
                    "--delay", str(self.typing_delay),
                    "--",
                    text,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"xdotool type failed: {result.stderr}")
                return False

            logger.info(f"Successfully typed {len(text)} characters")
            return True

        except subprocess.TimeoutExpired:
            logger.error("xdotool type timed out")
            return False
        except Exception as e:
            logger.error(f"xdotool type failed: {e}")
            return False

    def _inject_xdotool_paste(self, text: str) -> bool:
        """Inject text by pasting via clipboard using xdotool."""
        if not self.xdotool_available:
            logger.error("xdotool not available")
            return False

        if not CLIPBOARD_AVAILABLE:
            logger.error("pyperclip not available")
            return False

        try:
            # Backup clipboard if requested
            old_clipboard = None
            if self.use_clipboard_backup:
                try:
                    old_clipboard = pyperclip.paste()
                except Exception as e:
                    logger.warning(f"Failed to backup clipboard: {e}")

            # Copy text to clipboard
            pyperclip.copy(text)
            time.sleep(0.05)  # Small delay for clipboard to sync

            # Paste using Ctrl+V
            result = subprocess.run(
                ["xdotool", "key", "ctrl+v"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                logger.error(f"xdotool paste failed: {result.stderr}")
                return False

            # Restore clipboard if requested
            if self.use_clipboard_backup and old_clipboard is not None:
                time.sleep(0.1)  # Wait for paste to complete
                try:
                    pyperclip.copy(old_clipboard)
                except Exception as e:
                    logger.warning(f"Failed to restore clipboard: {e}")

            logger.info(f"Successfully pasted {len(text)} characters")
            return True

        except subprocess.TimeoutExpired:
            logger.error("xdotool paste timed out")
            return False
        except Exception as e:
            logger.error(f"xdotool paste failed: {e}")
            return False

    def _inject_clipboard_only(self, text: str) -> bool:
        """Copy text to clipboard only (user must paste manually)."""
        if not CLIPBOARD_AVAILABLE:
            logger.error("pyperclip not available")
            return False

        try:
            pyperclip.copy(text)
            logger.info(f"Copied {len(text)} characters to clipboard")
            logger.info("Text is in clipboard - paste with Ctrl+V")
            return True

        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False

    def get_active_window_info(self) -> Optional[dict]:
        """
        Get information about the currently active window.

        Returns:
            Dictionary with window info, or None if unavailable
        """
        if not self.xdotool_available:
            return None

        try:
            # Get active window ID
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True,
                text=True,
                timeout=1,
            )

            if result.returncode != 0:
                return None

            window_id = result.stdout.strip()

            # Get window name
            result = subprocess.run(
                ["xdotool", "getwindowname", window_id],
                capture_output=True,
                text=True,
                timeout=1,
            )

            window_name = result.stdout.strip() if result.returncode == 0 else "Unknown"

            # Get window class
            result = subprocess.run(
                ["xdotool", "getwindowclassname", window_id],
                capture_output=True,
                text=True,
                timeout=1,
            )

            window_class = result.stdout.strip() if result.returncode == 0 else "Unknown"

            return {
                "id": window_id,
                "name": window_name,
                "class": window_class,
            }

        except Exception as e:
            logger.error(f"Failed to get window info: {e}")
            return None

    def test_injection(self) -> bool:
        """
        Test text injection with a sample message.

        Returns:
            True if test was successful
        """
        test_text = "Test injection - MyCoder Speech Recognition"
        logger.info("Testing text injection...")

        window_info = self.get_active_window_info()
        if window_info:
            logger.info(
                f"Active window: {window_info['name']} "
                f"(class: {window_info['class']})"
            )

        return self.inject_text(test_text)
