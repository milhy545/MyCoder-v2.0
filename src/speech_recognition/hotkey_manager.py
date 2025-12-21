"""
Global hotkey management module.

Provides system-wide keyboard shortcuts for triggering speech recognition.
"""

import logging
import threading
from typing import Optional, Callable, Dict, Set

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None

logger = logging.getLogger(__name__)


class HotkeyManager:
    """
    Manages global keyboard shortcuts.

    Supports registering multiple hotkeys and callbacks.
    """

    def __init__(self):
        """Initialize the hotkey manager."""
        if not PYNPUT_AVAILABLE:
            raise ImportError(
                "Hotkey support requires pynput. "
                "Install with: poetry install --extras speech"
            )

        self.hotkeys: Dict[frozenset, Callable[[], None]] = {}
        self.current_keys: Set[keyboard.Key] = set()
        self.listener: Optional[keyboard.Listener] = None
        self.running = False

        # Lock for thread-safe operations
        self.lock = threading.Lock()

    def register_hotkey(
        self,
        keys: list[str],
        callback: Callable[[], None],
    ) -> bool:
        """
        Register a global hotkey.

        Args:
            keys: List of key names (e.g., ["ctrl", "shift", "r"])
            callback: Function to call when hotkey is pressed

        Returns:
            True if registration was successful
        """
        try:
            # Convert key names to Key objects
            key_set = self._parse_keys(keys)

            if not key_set:
                logger.error(f"Invalid hotkey combination: {keys}")
                return False

            with self.lock:
                self.hotkeys[frozenset(key_set)] = callback

            logger.info(f"Registered hotkey: {'+'.join(keys)}")
            return True

        except Exception as e:
            logger.error(f"Failed to register hotkey {keys}: {e}")
            return False

    def unregister_hotkey(self, keys: list[str]) -> bool:
        """
        Unregister a global hotkey.

        Args:
            keys: List of key names to unregister

        Returns:
            True if unregistration was successful
        """
        try:
            key_set = self._parse_keys(keys)

            if not key_set:
                return False

            with self.lock:
                key_frozen = frozenset(key_set)
                if key_frozen in self.hotkeys:
                    del self.hotkeys[key_frozen]
                    logger.info(f"Unregistered hotkey: {'+'.join(keys)}")
                    return True
                else:
                    logger.warning(f"Hotkey not found: {'+'.join(keys)}")
                    return False

        except Exception as e:
            logger.error(f"Failed to unregister hotkey {keys}: {e}")
            return False

    def _parse_keys(self, keys: list[str]) -> Set[keyboard.Key]:
        """
        Parse key names into Key objects.

        Args:
            keys: List of key name strings

        Returns:
            Set of Key objects
        """
        key_set = set()

        for key_name in keys:
            key_name = key_name.lower().strip()

            # Map common key names
            key_map = {
                "ctrl": keyboard.Key.ctrl,
                "control": keyboard.Key.ctrl,
                "ctrl_l": keyboard.Key.ctrl_l,
                "ctrl_r": keyboard.Key.ctrl_r,
                "shift": keyboard.Key.shift,
                "shift_l": keyboard.Key.shift_l,
                "shift_r": keyboard.Key.shift_r,
                "alt": keyboard.Key.alt,
                "alt_l": keyboard.Key.alt_l,
                "alt_r": keyboard.Key.alt_r,
                "cmd": keyboard.Key.cmd,
                "super": keyboard.Key.cmd,
                "win": keyboard.Key.cmd,
                "tab": keyboard.Key.tab,
                "space": keyboard.Key.space,
                "enter": keyboard.Key.enter,
                "return": keyboard.Key.enter,
                "backspace": keyboard.Key.backspace,
                "delete": keyboard.Key.delete,
                "esc": keyboard.Key.esc,
                "escape": keyboard.Key.esc,
                "home": keyboard.Key.home,
                "end": keyboard.Key.end,
                "pageup": keyboard.Key.page_up,
                "pagedown": keyboard.Key.page_down,
                "up": keyboard.Key.up,
                "down": keyboard.Key.down,
                "left": keyboard.Key.left,
                "right": keyboard.Key.right,
                "f1": keyboard.Key.f1,
                "f2": keyboard.Key.f2,
                "f3": keyboard.Key.f3,
                "f4": keyboard.Key.f4,
                "f5": keyboard.Key.f5,
                "f6": keyboard.Key.f6,
                "f7": keyboard.Key.f7,
                "f8": keyboard.Key.f8,
                "f9": keyboard.Key.f9,
                "f10": keyboard.Key.f10,
                "f11": keyboard.Key.f11,
                "f12": keyboard.Key.f12,
            }

            if key_name in key_map:
                key_set.add(key_map[key_name])
            elif len(key_name) == 1:
                # Single character key
                try:
                    key_set.add(keyboard.KeyCode.from_char(key_name))
                except Exception:
                    logger.warning(f"Invalid key: {key_name}")
            else:
                logger.warning(f"Unknown key name: {key_name}")

        return key_set

    def _normalize_key(self, key) -> keyboard.Key:
        """
        Normalize key to handle left/right variants.

        Args:
            key: Key to normalize

        Returns:
            Normalized key
        """
        # Map specific left/right keys to generic versions
        key_mappings = {
            keyboard.Key.ctrl_l: keyboard.Key.ctrl,
            keyboard.Key.ctrl_r: keyboard.Key.ctrl,
            keyboard.Key.shift_l: keyboard.Key.shift,
            keyboard.Key.shift_r: keyboard.Key.shift,
            keyboard.Key.alt_l: keyboard.Key.alt,
            keyboard.Key.alt_r: keyboard.Key.alt,
        }

        return key_mappings.get(key, key)

    def _on_press(self, key) -> None:
        """Handle key press events."""
        try:
            # Normalize key
            normalized_key = self._normalize_key(key)

            with self.lock:
                self.current_keys.add(normalized_key)

                # Check if current keys match any registered hotkey
                current_frozen = frozenset(self.current_keys)

                for hotkey_keys, callback in self.hotkeys.items():
                    if current_frozen == hotkey_keys:
                        logger.info(f"Hotkey triggered: {hotkey_keys}")
                        # Execute callback in separate thread to avoid blocking
                        threading.Thread(target=callback, daemon=True).start()

        except Exception as e:
            logger.error(f"Error in key press handler: {e}")

    def _on_release(self, key) -> None:
        """Handle key release events."""
        try:
            # Normalize key
            normalized_key = self._normalize_key(key)

            with self.lock:
                self.current_keys.discard(normalized_key)

        except Exception as e:
            logger.error(f"Error in key release handler: {e}")

    def start(self) -> bool:
        """
        Start listening for hotkeys.

        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Hotkey listener already running")
            return False

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )

            self.listener.start()
            self.running = True

            logger.info("Hotkey listener started")
            return True

        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")
            return False

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if not self.running:
            return

        if self.listener:
            self.listener.stop()
            self.listener = None

        self.running = False
        logger.info("Hotkey listener stopped")

    def is_running(self) -> bool:
        """Check if hotkey listener is running."""
        return self.running

    def get_registered_hotkeys(self) -> list[str]:
        """
        Get list of registered hotkey combinations.

        Returns:
            List of hotkey strings
        """
        with self.lock:
            hotkeys = []

            for key_set in self.hotkeys.keys():
                # Convert keys back to string representation
                key_names = []
                for key in key_set:
                    if hasattr(key, 'name'):
                        key_names.append(key.name)
                    elif hasattr(key, 'char'):
                        key_names.append(key.char)
                    else:
                        key_names.append(str(key))

                hotkeys.append('+'.join(sorted(key_names)))

            return hotkeys

    def clear_all_hotkeys(self) -> None:
        """Clear all registered hotkeys."""
        with self.lock:
            self.hotkeys.clear()
            logger.info("Cleared all hotkeys")
