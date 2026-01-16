#!/usr/bin/env python3
"""
Command-line interface for Global Dictation application.

Provides commands for running, configuring, and testing the dictation app.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import click

    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    click = None

from .config import ConfigManager, DictationConfig, setup_logging
from .dictation_app import GlobalDictationApp
from .text_injector import InjectionMethod
from .whisper_transcriber import WhisperProvider

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point."""
    if not CLICK_AVAILABLE:
        print("Error: click package required. Install with: poetry install")
        return 1

    try:
        cli()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Global Dictation - System-wide speech recognition for Linux."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--provider",
    type=click.Choice(["api", "local"], case_sensitive=False),
    help="Whisper provider (api or local)",
)
@click.option(
    "--model",
    "-m",
    help="Whisper model name",
)
@click.option(
    "--language",
    "-l",
    default="cs",
    help="Language code (default: cs for Czech)",
)
@click.option(
    "--no-gui",
    is_flag=True,
    help="Run without GUI (hotkey only mode)",
)
@click.option(
    "--no-hotkeys",
    is_flag=True,
    help="Run without global hotkeys",
)
@click.option(
    "--hotkey",
    help='Hotkey combination (e.g., "ctrl+shift+space")',
)
@click.option(
    "--api-key",
    help="OpenAI API key for Whisper API",
)
@click.option(
    "--injection-method",
    type=click.Choice(["xdotool_type", "xdotool_paste", "clipboard_only", "auto"]),
    help="Text injection method",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
)
def run(
    config: Optional[Path],
    provider: Optional[str],
    model: Optional[str],
    language: str,
    no_gui: bool,
    no_hotkeys: bool,
    hotkey: Optional[str],
    api_key: Optional[str],
    injection_method: Optional[str],
    debug: bool,
):
    """Run the global dictation application."""
    # Load configuration
    config_manager = ConfigManager(config)
    app_config = config_manager.load()

    # Override with CLI arguments
    if provider:
        app_config.whisper.provider = provider
    if model:
        if app_config.whisper.provider == "api":
            app_config.whisper.model = model
        else:
            app_config.whisper.local_model = model
    if api_key:
        app_config.whisper.api_key = api_key
    if language:
        app_config.whisper.language = language
    if no_gui:
        app_config.gui.enabled = False
    if no_hotkeys:
        app_config.hotkey.enabled = False
    if hotkey:
        app_config.hotkey.combination = hotkey.split("+")
    if injection_method:
        app_config.injection.method = injection_method
    if debug:
        app_config.log_level = "DEBUG"

    # Setup logging
    setup_logging(app_config)

    # Validate configuration
    is_valid, errors = config_manager.validate()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1

    # Show configuration summary
    logger.info("\n" + config_manager.get_summary())

    # Create and run application
    try:
        app = GlobalDictationApp(
            whisper_provider=WhisperProvider(app_config.whisper.provider),
            whisper_api_key=app_config.whisper.api_key,
            whisper_model=(
                app_config.whisper.local_model
                if app_config.whisper.provider == "local"
                else app_config.whisper.model
            ),
            language=app_config.whisper.language,
            sample_rate=app_config.audio.sample_rate,
            silence_threshold=app_config.audio.silence_threshold,
            silence_duration=app_config.audio.silence_duration,
            injection_method=InjectionMethod(app_config.injection.method),
            enable_gui=app_config.gui.enabled,
            enable_hotkeys=app_config.hotkey.enabled,
            hotkey_combo=(
                app_config.hotkey.combination if app_config.hotkey.enabled else None
            ),
        )

        return app.run()

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        return 1


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(path_type=Path),
    help="Path to configuration file",
)
def test(config: Optional[Path]):
    """Test application components."""
    # Load configuration
    config_manager = ConfigManager(config)
    app_config = config_manager.load()

    # Setup logging
    setup_logging(app_config)

    logger.info("Testing Global Dictation components...")

    try:
        # Create application
        app = GlobalDictationApp(
            whisper_provider=WhisperProvider(app_config.whisper.provider),
            whisper_api_key=app_config.whisper.api_key,
            whisper_model=app_config.whisper.local_model,
            language=app_config.whisper.language,
            enable_gui=False,
            enable_hotkeys=False,
        )

        # Run component tests
        results = app.test_components()

        # Print results
        logger.info("\n=== Component Test Results ===")
        for component, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            logger.info(f"{component}: {status}")

        # Overall result
        all_passed = all(results.values())
        if all_passed:
            logger.info("\n✓ All tests passed!")
            return 0
        else:
            logger.error("\n✗ Some tests failed")
            return 1

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(path_type=Path),
    help="Path to configuration file",
)
def config_show(config: Optional[Path]):
    """Show current configuration."""
    config_manager = ConfigManager(config)
    app_config = config_manager.load()

    print(config_manager.get_summary())


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(path_type=Path),
    help="Path to configuration file",
)
def config_create(config: Optional[Path]):
    """Create default configuration file."""
    config_manager = ConfigManager(config)

    if config_manager.config_path.exists():
        click.confirm(
            f"Configuration file already exists at {config_manager.config_path}. Overwrite?",
            abort=True,
        )

    if config_manager.create_default_config():
        click.echo(f"✓ Created configuration file: {config_manager.config_path}")
        click.echo(
            "\nEdit the file to customize settings, or use environment variables:"
        )
        click.echo("  OPENAI_API_KEY - OpenAI API key for Whisper API")
        click.echo("  DICTATION_WHISPER_PROVIDER - 'api' or 'local'")
        click.echo("  DICTATION_LANGUAGE - Language code (e.g., 'cs', 'en')")
        return 0
    else:
        click.echo("✗ Failed to create configuration file", err=True)
        return 1


@cli.command()
def devices():
    """List available audio input devices."""
    try:
        from .audio_recorder import AudioRecorder

        recorder = AudioRecorder()
        devices = recorder.get_devices()

        if not devices:
            click.echo("No audio input devices found")
            return 1

        click.echo("Available audio input devices:\n")
        for device in devices:
            click.echo(f"  [{device['index']}] {device['name']}")
            click.echo(f"      Channels: {device['channels']}")
            click.echo(f"      Sample Rate: {device['sample_rate']} Hz")
            click.echo()

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.argument("text")
def inject(text: str):
    """Test text injection with given text."""
    try:
        from .text_injector import TextInjector

        click.echo(f"Injecting text: {text}")
        click.echo("Switch to target window in 3 seconds...")

        import time

        time.sleep(3)

        injector = TextInjector()
        success = injector.inject_text(text)

        if success:
            click.echo("✓ Text injected successfully")
            return 0
        else:
            click.echo("✗ Text injection failed", err=True)
            return 1

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
def setup():
    """Run interactive setup wizard for first-time configuration."""
    try:
        from .setup_wizard import SetupWizard

        wizard = SetupWizard()
        should_launch = wizard.run()

        if should_launch:
            # User wants to launch after setup
            click.echo("\n🚀 Spouštím aplikaci...")
            import subprocess

            subprocess.Popen(
                ["poetry", "run", "dictation", "run"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            click.echo("✅ Aplikace spuštěna na pozadí")
            click.echo("   Měli byste vidět zelené tlačítko 🎤")

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
