#!/usr/bin/env python3
"""
Demo script for Global Dictation application.

Shows different ways to use the dictation app.
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from speech_recognition import (
    GlobalDictationApp,
    WhisperProvider,
    InjectionMethod,
    ConfigManager,
    setup_logging,
)


def demo_basic():
    """Basic usage with default settings."""
    print("=== Demo 1: Basic Usage ===\n")

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create app with local Whisper model
    app = GlobalDictationApp(
        whisper_provider=WhisperProvider.LOCAL,
        whisper_model="base",
        language="cs",
        enable_gui=True,
        enable_hotkeys=True,
    )

    print("Application started!")
    print("- Click the microphone button to start recording")
    print("- Or press Ctrl+Shift+Space")
    print("- Speak and wait for ~1.5s of silence")
    print("- Text will be automatically inserted\n")
    print("Press Ctrl+C to exit\n")

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.shutdown()


def demo_api():
    """Usage with OpenAI Whisper API."""
    print("=== Demo 2: OpenAI Whisper API ===\n")

    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-key'")
        return

    logging.basicConfig(level=logging.INFO)

    # Create app with API provider
    app = GlobalDictationApp(
        whisper_provider=WhisperProvider.API,
        whisper_api_key=api_key,
        whisper_model="whisper-1",
        language="cs",
        enable_gui=True,
    )

    print("Application started with OpenAI API!")
    print("This provides faster and more accurate transcription.\n")
    print("Press Ctrl+C to exit\n")

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.shutdown()


def demo_no_gui():
    """Usage without GUI (hotkey only)."""
    print("=== Demo 3: No GUI (Hotkey Only) ===\n")

    logging.basicConfig(level=logging.INFO)

    # Create app without GUI
    app = GlobalDictationApp(
        whisper_provider=WhisperProvider.LOCAL,
        whisper_model="base",
        language="cs",
        enable_gui=False,
        enable_hotkeys=True,
        hotkey_combo=["ctrl", "alt", "d"],
    )

    print("Application started without GUI!")
    print("- Press Ctrl+Alt+D to start/stop recording")
    print("- No floating button will be shown\n")
    print("Press Ctrl+C to exit\n")

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.shutdown()


def demo_custom_config():
    """Usage with custom configuration."""
    print("=== Demo 4: Custom Configuration ===\n")

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load()

    # Customize settings
    config.whisper.provider = "local"
    config.whisper.local_model = "small"  # Better accuracy
    config.whisper.language = "cs"
    config.audio.silence_duration = 2.0  # Longer silence threshold
    config.gui.button_size = 100  # Larger button
    config.hotkey.combination = ["ctrl", "shift", "d"]

    # Setup logging
    setup_logging(config)

    # Create app from config
    app = GlobalDictationApp(
        whisper_provider=WhisperProvider(config.whisper.provider),
        whisper_model=config.whisper.local_model,
        language=config.whisper.language,
        silence_duration=config.audio.silence_duration,
        enable_gui=config.gui.enabled,
        enable_hotkeys=config.hotkey.enabled,
        hotkey_combo=config.hotkey.combination,
    )

    print("Application started with custom config!")
    print(f"- Model: {config.whisper.local_model}")
    print(f"- Silence duration: {config.audio.silence_duration}s")
    print(f"- Hotkey: {'+'.join(config.hotkey.combination)}\n")
    print("Press Ctrl+C to exit\n")

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.shutdown()


def demo_test_components():
    """Test all components."""
    print("=== Demo 5: Component Testing ===\n")

    logging.basicConfig(level=logging.INFO)

    # Create app
    app = GlobalDictationApp(
        whisper_provider=WhisperProvider.LOCAL,
        whisper_model="base",
        language="cs",
        enable_gui=False,
        enable_hotkeys=False,
    )

    print("Testing application components...\n")

    # Run tests
    results = app.test_components()

    # Print results
    print("\n=== Test Results ===")
    for component, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{component}: {status}")

    # Print status
    print("\n=== Application Status ===")
    status = app.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")


def demo_programmatic_control():
    """Programmatic control of recording."""
    print("=== Demo 6: Programmatic Control ===\n")

    logging.basicConfig(level=logging.INFO)

    # Create app without GUI and hotkeys
    app = GlobalDictationApp(
        whisper_provider=WhisperProvider.LOCAL,
        whisper_model="base",
        language="cs",
        enable_gui=False,
        enable_hotkeys=False,
    )

    print("Programmatically controlled recording")
    print("Recording will start in 3 seconds...\n")

    time.sleep(3)

    print("Recording started - speak now!")
    app.start_recording()

    # Wait for user to speak (simulating automatic stop via silence)
    print("Recording... (will stop after silence)\n")

    # Note: The recording will stop automatically when silence is detected
    # In a real application, you would integrate this into your own event loop

    print("Recording will stop automatically after silence")
    print("Check the logs for transcription results")


def main():
    """Main demo selector."""
    demos = {
        "1": ("Basic Usage (Local Whisper)", demo_basic),
        "2": ("OpenAI API", demo_api),
        "3": ("No GUI (Hotkey Only)", demo_no_gui),
        "4": ("Custom Configuration", demo_custom_config),
        "5": ("Component Testing", demo_test_components),
        "6": ("Programmatic Control", demo_programmatic_control),
    }

    print("╔════════════════════════════════════════════════╗")
    print("║   Global Dictation - Demo Selector            ║")
    print("╚════════════════════════════════════════════════╝\n")

    print("Select a demo to run:\n")
    for key, (name, _) in demos.items():
        print(f"  {key}. {name}")

    print("\n  0. Exit\n")

    choice = input("Enter choice (1-6): ").strip()

    if choice == "0":
        print("Goodbye!")
        return

    if choice in demos:
        _, demo_func = demos[choice]
        print("\n" + "="*50 + "\n")
        demo_func()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
