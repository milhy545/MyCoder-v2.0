"""
GUI overlay module for displaying a floating microphone button.

Provides a draggable, always-on-top button for starting/stopping dictation.
"""

import logging
from enum import Enum
from typing import Callable, Optional

try:
    from PyQt5.QtCore import QPoint, Qt, QTimer
    from PyQt5.QtGui import QCursor, QFont
    from PyQt5.QtWidgets import (
        QApplication,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QApplication = None
    QPushButton = None
    QWidget = None
    QLabel = None
    QVBoxLayout = None
    Qt = None
    QTimer = None
    QPoint = None
    QFont = None
    QCursor = None

logger = logging.getLogger(__name__)
BaseWidget = QWidget if PYQT_AVAILABLE else object


class ButtonState(Enum):
    """States of the overlay button."""

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


if PYQT_AVAILABLE:

    class OverlayButton(BaseWidget):
        """
        Floating overlay button for speech recognition control.

        Features:
        - Always on top
        - Draggable
        - Visual feedback for recording state
        - Click to start/stop recording
        """

        def __init__(
            self,
            on_click: Optional[Callable[[], None]] = None,
            size: int = 80,
            position: Optional[tuple[int, int]] = None,
        ):
            """
            Initialize the overlay button.

            Args:
                on_click: Callback function when button is clicked
                size: Button diameter in pixels (default: 80)
                position: Initial position as (x, y) tuple, or None for bottom-right
            """
            super().__init__()

            self.on_click = on_click
            self.size = size
            self.state = ButtonState.IDLE

            # For dragging
            self.dragging = False
            self.drag_position = QPoint()

            # Setup UI
            self._setup_ui()
            self._setup_styles()

            # Set initial position
            if position:
                self.move(*position)
            else:
                self._move_to_bottom_right()

            # Animation timer for recording pulse effect
            self.pulse_timer = QTimer()
            self.pulse_timer.timeout.connect(self._animate_pulse)
            self.pulse_opacity = 1.0
            self.pulse_direction = -1

        def _setup_ui(self) -> None:
            """Setup the UI components."""
            # Window flags for floating overlay
            self.setWindowFlags(
                Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
            )
            self.setAttribute(Qt.WA_TranslucentBackground)

            # Set window size
            self.setFixedSize(self.size + 40, self.size + 60)

            # Main layout
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(5)

            # Microphone button
            self.button = QPushButton("🎤")
            self.button.setFixedSize(self.size, self.size)
            self.button.clicked.connect(self._handle_click)
            self.button.setCursor(QCursor(Qt.PointingHandCursor))

            # Status label
            self.status_label = QLabel("Ready")
            self.status_label.setAlignment(Qt.AlignCenter)
            self.status_label.setWordWrap(True)

            # Add widgets to layout
            layout.addWidget(self.button, alignment=Qt.AlignCenter)
            layout.addWidget(self.status_label)

            self.setLayout(layout)

        def _setup_styles(self) -> None:
            """Setup component styles."""
            # Button style
            self.button.setFont(QFont("Arial", 32))
            self._update_button_style()

            # Status label style
            self.status_label.setFont(QFont("Arial", 10))
            self.status_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: rgba(0, 0, 0, 150);
                    border-radius: 10px;
                    padding: 5px;
                }
            """)

        def _update_button_style(self) -> None:
            """Update button style based on current state."""
            styles = {
                ButtonState.IDLE: """
                    QPushButton {
                        background-color: #4CAF50;
                        border-radius: 40px;
                        border: 3px solid #45a049;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """,
                ButtonState.RECORDING: """
                    QPushButton {
                        background-color: #f44336;
                        border-radius: 40px;
                        border: 3px solid #da190b;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                """,
                ButtonState.PROCESSING: """
                    QPushButton {
                        background-color: #FF9800;
                        border-radius: 40px;
                        border: 3px solid #F57C00;
                    }
                """,
                ButtonState.ERROR: """
                    QPushButton {
                        background-color: #9E9E9E;
                        border-radius: 40px;
                        border: 3px solid #757575;
                    }
                """,
            }

            self.button.setStyleSheet(styles.get(self.state, styles[ButtonState.IDLE]))

        def _move_to_bottom_right(self) -> None:
            """Move button to bottom-right corner of screen."""
            screen = QApplication.primaryScreen().geometry()
            x = screen.width() - self.width() - 20
            y = screen.height() - self.height() - 20
            self.move(x, y)

        def _handle_click(self) -> None:
            """Handle button click."""
            logger.info(f"Button clicked in state: {self.state.value}")

            if self.on_click:
                self.on_click()

        def _animate_pulse(self) -> None:
            """Animate button pulsing effect during recording."""
            self.pulse_opacity += 0.05 * self.pulse_direction

            if self.pulse_opacity <= 0.5:
                self.pulse_direction = 1
            elif self.pulse_opacity >= 1.0:
                self.pulse_direction = -1

            self.setWindowOpacity(self.pulse_opacity)

        def set_state(self, state: ButtonState) -> None:
            """
            Set button state and update visuals.

            Args:
                state: New button state
            """
            logger.info(f"Button state changed: {self.state.value} -> {state.value}")
            self.state = state
            self._update_button_style()

            # Update status label
            status_texts = {
                ButtonState.IDLE: "Ready",
                ButtonState.RECORDING: "Recording...",
                ButtonState.PROCESSING: "Processing...",
                ButtonState.ERROR: "Error",
            }
            self.status_label.setText(status_texts.get(state, "Unknown"))

            # Start/stop pulse animation for recording
            if state == ButtonState.RECORDING:
                self.pulse_timer.start(50)  # 50ms interval
            else:
                self.pulse_timer.stop()
                self.setWindowOpacity(1.0)

        def set_status(self, text: str) -> None:
            """
            Set custom status text.

            Args:
                text: Status text to display
            """
            self.status_label.setText(text)

        def mousePressEvent(self, event) -> None:
            """Handle mouse press for dragging."""
            if event.button() == Qt.LeftButton:
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event) -> None:
            """Handle mouse move for dragging."""
            if self.dragging and event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.drag_position)
                event.accept()

        def mouseReleaseEvent(self, event) -> None:
            """Handle mouse release for dragging."""
            if event.button() == Qt.LeftButton:
                self.dragging = False
                event.accept()

        def show_notification(self, message: str, duration: int = 2000) -> None:
            """
            Show temporary notification message.

            Args:
                message: Message to display
                duration: Duration in milliseconds
            """
            original_text = self.status_label.text()

            self.status_label.setText(message)

            # Restore original text after duration
            QTimer.singleShot(
                duration, lambda: self.status_label.setText(original_text)
            )

        def flash_error(self) -> None:
            """Flash button to indicate error."""
            original_state = self.state

            self.set_state(ButtonState.ERROR)
            QTimer.singleShot(500, lambda: self.set_state(original_state))

    def _get_overlay_button_class() -> type[BaseWidget]:
        if not PYQT_AVAILABLE:
            raise RuntimeError("PyQt5 not available - overlay button disabled")
        if OverlayButton is None:
            raise RuntimeError("OverlayButton not available - PyQt5 not available")
        if not callable(OverlayButton):
            raise RuntimeError("OverlayButton is not callable")
        return OverlayButton

    class OverlayApp:
        """
        Application wrapper for the overlay button.

        Manages QApplication lifecycle.
        """

        def __init__(self, on_click: Optional[Callable[[], None]] = None):
            """
            Initialize the overlay application.

            Args:
                on_click: Callback function when button is clicked
            """
            if QApplication is None:
                raise RuntimeError("QApplication not initialized - PyQt5 not available")

            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication([])

            button_cls = _get_overlay_button_class()
            self.button = button_cls(on_click=on_click)

        def show(self) -> None:
            """Show the overlay button."""
            self.button.show()

        def hide(self) -> None:
            """Hide the overlay button."""
            self.button.hide()

        def run(self) -> int:
            """
            Run the application event loop.

            Returns:
                Application exit code
            """
            if self.app is None:
                raise RuntimeError("QApplication not initialized - PyQt5 not available")
            self.button.show()
            return self.app.exec_()

        def quit(self) -> None:
            """Quit the application."""
            self.app.quit()

else:

    def _raise_missing_gui() -> None:
        raise ImportError(
            "GUI overlay requires PyQt5. "
            "Install with: poetry install --extras speech"
        )

    class OverlayButton:
        """Fallback overlay button when PyQt5 is unavailable."""

        def __init__(self, *_args, **_kwargs) -> None:
            _raise_missing_gui()

    class OverlayApp:
        """Fallback overlay app when PyQt5 is unavailable."""

        def __init__(self, *_args, **_kwargs) -> None:
            _raise_missing_gui()

        def show(self) -> None:
            _raise_missing_gui()

        def hide(self) -> None:
            _raise_missing_gui()

        def run(self) -> int:
            _raise_missing_gui()

        def quit(self) -> None:
            _raise_missing_gui()
