#!/usr/bin/env python3
"""
Post-installation setup wizard for Global Dictation.

Interactive wizard that tests and configures the dictation application.
"""

import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

try:
    import numpy as np
    import sounddevice as sd

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

from .config import ConfigManager, DictationConfig

logger = logging.getLogger(__name__)


class SetupWizard:
    """Interactive setup wizard for Global Dictation."""

    def __init__(self):
        """Initialize setup wizard."""
        self.config = DictationConfig()
        self.config_manager = ConfigManager()
        self.selected_device = None
        self.selected_device_name = None
        self.optimal_threshold = 0.01

    def _get_pulseaudio_source_name(self) -> Optional[str]:
        """Get PulseAudio/PipeWire source name for selected device."""
        try:
            # List all sources
            result = subprocess.run(
                ["pactl", "list", "sources", "short"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Try to match device name (alsa_input usually)
            for line in result.stdout.splitlines():
                if "alsa_input" in line and "analog-stereo" in line:
                    return line.split()[1]  # Source name

            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _get_mic_volume(self) -> Optional[int]:
        """Get current microphone volume (0-100%)."""
        source = self._get_pulseaudio_source_name()
        if not source:
            return None

        try:
            result = subprocess.run(
                ["pactl", "get-source-volume", source],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse: "Volume: front-left: 78643 / 120% / 4.75 dB"
            match = re.search(r"(\d+)%", result.stdout)
            if match:
                return int(match.group(1))

            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _set_mic_volume(self, percent: int) -> bool:
        """Set microphone volume (0-150%)."""
        source = self._get_pulseaudio_source_name()
        if not source:
            return False

        try:
            subprocess.run(
                ["pactl", "set-source-volume", source, f"{percent}%"],
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def print_header(self, text: str, char: str = "═") -> None:
        """Print formatted header."""
        width = 60
        print(f"\n╔{char * width}╗")
        padding = (width - len(text)) // 2
        print(f"║{' ' * padding}{text}{' ' * (width - padding - len(text))}║")
        print(f"╚{char * width}╝\n")

    def print_step(self, number: int, title: str) -> None:
        """Print step header."""
        print(f"\n{'─' * 60}")
        print(f"  KROK {number}: {title}")
        print(f"{'─' * 60}\n")

    def welcome(self) -> None:
        """Display welcome message."""
        self.print_header("🎤 GLOBAL DICTATION - Průvodce nastavením")

        print("Vítejte! Tento průvodce vám pomůže:")
        print("")
        print("  1. 🎙️  Otestovat váš mikrofon")
        print("  2. 📊 Nastavit optimální hlasitost")
        print("  3. 🗣️  Vyzkoušet rozpoznávání řeči")
        print("  4. ⌨️  Otestovat vkládání textu")
        print("  5. ⚙️  Vytvořit optimální konfiguraci")
        print("")
        print("Celý proces zabere asi 2-3 minuty.")
        print("")

        input("Stiskněte Enter pro pokračování...")

    def test_audio_devices(self) -> bool:
        """Test and select audio device."""
        self.print_step(1, "Detekce audio zařízení")

        if not AUDIO_AVAILABLE:
            print("❌ Chyba: sounddevice není nainstalováno!")
            return False

        try:
            devices = sd.query_devices()

            # Filter only real hardware devices (hw:X,Y) and system default
            input_devices = []
            for idx, dev in enumerate(devices):
                if dev["max_input_channels"] > 0:
                    name = dev["name"]
                    # Include: hardware devices (hw:), pulse, pipewire, or default
                    # Exclude: virtual ALSA plugins (sysdefault, lavrate, samplerate, etc.)
                    if any(
                        [
                            "hw:" in name,
                            name == "default",
                            name == "pulse",
                            name == "pipewire",
                        ]
                    ):
                        input_devices.append((idx, dev))

            if not input_devices:
                print("❌ Nebylo nalezeno žádné vstupní audio zařízení!")
                return False

            print(f"✅ Nalezeno {len(input_devices)} vstupních zařízení:\n")

            for i, (idx, dev) in enumerate(input_devices, 1):
                default_marker = " (VÝCHOZÍ)" if idx == sd.default.device[0] else ""
                print(f"  [{i}] {dev['name']}{default_marker}")
                print(
                    f"      Kanály: {dev['max_input_channels']}, "
                    f"Vzorkovací frekvence: {dev['default_samplerate']} Hz"
                )
                print()

            # Auto-select default or first device
            if sd.default.device[0] is not None:
                default_idx = next(
                    (
                        i
                        for i, (idx, _) in enumerate(input_devices)
                        if idx == sd.default.device[0]
                    ),
                    0,
                )
            else:
                default_idx = 0

            print(f"Doporučené zařízení: [{default_idx + 1}]")
            choice = input(
                f"Vyberte zařízení (1-{len(input_devices)}) nebo Enter pro výchozí: "
            ).strip()

            if not choice:
                selected_idx = default_idx
            else:
                try:
                    selected_idx = int(choice) - 1
                    if selected_idx < 0 or selected_idx >= len(input_devices):
                        selected_idx = default_idx
                except ValueError:
                    selected_idx = default_idx

            self.selected_device = input_devices[selected_idx][0]
            print(f"\n✅ Vybráno: {devices[self.selected_device]['name']}")

            return True

        except Exception as e:
            print(f"❌ Chyba při detekci zařízení: {e}")
            return False

    def test_microphone_level(self) -> Tuple[bool, float]:
        """Test microphone recording level with automatic calibration."""
        self.print_step(2, "Automatická kalibrace mikrofonu")

        # Check if we can control mic volume
        current_volume = self._get_mic_volume()
        can_auto_adjust = current_volume is not None

        if can_auto_adjust:
            print(f"📊 Aktuální hlasitost mikrofonu: {current_volume}%")
            print("")

        print("🎯 CÍL: Najít optimální hlasitost pro rozpoznávání řeči")
        print("")
        print("📝 Proces:")
        print("  1. Nahraji 5 sekund vašeho hlasu")
        print("  2. Analyzuji úroveň zvuku")
        print("  3. Automaticky upravím hlasitost pokud je potřeba")
        print("  4. Opakuji dokud není optimální (30-70%)")
        print("")

        input("Připravte se mluvit a stiskněte Enter...")

        attempt = 0
        max_attempts = 5  # Prevent infinite loop

        while attempt < max_attempts:
            attempt += 1

            if attempt > 1:
                print(f"\n🔄 Pokus {attempt}/{max_attempts}")

            print("\n🎤 NAHRÁVÁM 5 SEKUND - MLUVTE NYNÍ!\n")

            # Recording parameters
            duration = 5
            sample_rate = 16000
            max_level = 0.0
            avg_level = 0.0
            samples_count = 0

            def callback(indata, frames, time_info, status):
                nonlocal max_level, avg_level, samples_count

                # Calculate RMS level (0.0 to 1.0)
                rms = np.sqrt(np.mean(indata**2))
                max_level = max(max_level, rms)
                avg_level += rms
                samples_count += 1

                # VU meter - convert to percentage (0-100%)
                # Typical speaking voice is around 0.01-0.5 RMS
                # We'll scale so 0.5 RMS = 100%
                bar_length = 50
                level_percent = min(100, (rms / 0.5) * 100)
                filled = int(bar_length * level_percent / 100)
                bar = "█" * filled + "░" * (bar_length - filled)

                # Color coding based on level
                if level_percent < 20:
                    status_icon = "🔴"  # Too quiet
                elif level_percent < 30:
                    status_icon = "🟡"  # Acceptable but low
                elif level_percent <= 70:
                    status_icon = "🟢"  # Optimal
                else:
                    status_icon = "🟠"  # Too loud

                print(
                    f"\r{status_icon} [{bar}] {level_percent:5.1f}%", end="", flush=True
                )

            try:
                with sd.InputStream(
                    device=self.selected_device,
                    channels=1,
                    samplerate=sample_rate,
                    callback=callback,
                ):
                    time.sleep(duration)

                print("\n")  # New line after VU meter

                avg_level = avg_level / samples_count if samples_count > 0 else 0

                # Convert to percentage (0-100%)
                max_percent = min(100, (max_level / 0.5) * 100)
                avg_percent = min(100, (avg_level / 0.5) * 100)

                # Show analysis
                print(f"\n📊 Analýza:")
                print(f"  Maximální úroveň: {max_percent:.1f}%")
                print(f"  Průměrná úroveň:  {avg_percent:.1f}%")

                # Calculate optimal threshold (as percentage for user)
                threshold_percent = (avg_level * 1.5 / 0.5) * 100
                print(f"  Práh ticha: {threshold_percent:.1f}%")
                print("")

                # Determine if in optimal range (30-70%)
                if 30 <= max_percent <= 70:
                    # OPTIMAL!
                    print("🎉 ✅ PERFEKTNÍ! Hlasitost je v optimální zóně!")
                    print("")
                    self.optimal_threshold = avg_level * 1.5

                    if can_auto_adjust:
                        final_volume = self._get_mic_volume()
                        print(f"💾 Optimální hlasitost mikrofonu: {final_volume}%")

                    print("")
                    return True, self.optimal_threshold

                elif max_percent < 30:
                    # TOO QUIET
                    print(f"🔴 Příliš tiché ({max_percent:.1f}% < 30%)")

                    if can_auto_adjust:
                        current_vol = self._get_mic_volume()
                        # Calculate needed increase (aim for 50%)
                        needed_vol = (
                            int(current_vol * (50 / max_percent))
                            if max_percent > 0
                            else current_vol + 20
                        )
                        needed_vol = min(150, needed_vol)  # Cap at 150%

                        print(
                            f"🔧 Automaticky zvyšuji z {current_vol}% na {needed_vol}%..."
                        )
                        if self._set_mic_volume(needed_vol):
                            print("✅ Hlasitost upravena, zkusím znovu...")
                            time.sleep(1)
                            continue
                        else:
                            print("⚠️  Nepodařilo se upravit automaticky")

                    print("   → Zvyšte hlasitost mikrofonu v systému")
                    print("   → Nebo mluvte blíž k mikrofonu")
                    print("")

                    if input("Zkusit znovu? (a/n): ").strip().lower() == "a":
                        continue
                    else:
                        self.optimal_threshold = 0.005
                        return False, self.optimal_threshold

                else:
                    # TOO LOUD (>70%)
                    print(f"🟠 Příliš hlasité ({max_percent:.1f}% > 70%)")

                    if can_auto_adjust:
                        current_vol = self._get_mic_volume()
                        # Calculate needed decrease (aim for 50%)
                        needed_vol = int(current_vol * (50 / max_percent))
                        needed_vol = max(20, needed_vol)  # Min 20%

                        print(
                            f"🔧 Automaticky snižuji z {current_vol}% na {needed_vol}%..."
                        )
                        if self._set_mic_volume(needed_vol):
                            print("✅ Hlasitost upravena, zkusím znovu...")
                            time.sleep(1)
                            continue
                        else:
                            print("⚠️  Nepodařilo se upravit automaticky")

                    print("   → Snižte hlasitost mikrofonu na 50-70%")
                    print("")

                    if input("Zkusit znovu? (a/n): ").strip().lower() == "a":
                        continue
                    else:
                        self.optimal_threshold = max_level * 0.1
                        return True, self.optimal_threshold

            except Exception as e:
                print(f"\n❌ Chyba při testu nahrávání: {e}")
                return False, 0.01

        # Max attempts reached
        print(f"\n⚠️  Dosaženo maximálního počtu pokusů ({max_attempts})")
        print("Pokračuji s aktuálním nastavením...")
        self.optimal_threshold = avg_level * 1.5 if avg_level > 0 else 0.01
        return True, self.optimal_threshold

    def test_speech_recognition(self) -> bool:
        """Test speech recognition with tiny model."""
        self.print_step(3, "Test rozpoznávání řeči")

        print("Nyní otestujeme rozpoznávání řeči pomocí Whisper AI.")
        print("")
        print("📝 Co udělat:")
        print("  1. Za chvíli začne nahrávání")
        print("  2. Řekněte česky nějakou větu (např: 'Ahoj, toto je test')")
        print("  3. Po 2 sekundách ticha se nahrávání automaticky zastaví")
        print("  4. Uvidíte přepsaný text")
        print("")

        response = input("Spustit test rozpoznávání? (a/n): ").strip().lower()
        if response != "a":
            print("⏭️  Test přeskočen")
            return True

        try:
            from .audio_recorder import AudioRecorder
            from .whisper_transcriber import WhisperProvider, WhisperTranscriber

            print("\n🔄 Načítám Whisper model (tiny)...")
            recorder = AudioRecorder(
                silence_threshold=self.optimal_threshold,
                silence_duration=2.0,
            )
            transcriber = WhisperTranscriber(
                provider=WhisperProvider.LOCAL,
                local_model="tiny",
                language="cs",
            )

            print("✅ Model načten!")
            print("\n🎤 NAHRÁVÁM - MLUVTE ČESKY!\n")

            recorder.start_recording()

            # Wait for recording to finish
            while recorder.is_active():
                duration = recorder.get_duration()
                print(f"\r⏺️  Nahrávám... {duration:.1f}s", end="", flush=True)
                time.sleep(0.1)

            print("\n\n⏹️  Nahrávání zastaveno")

            audio_data = recorder.stop_recording()

            if not audio_data:
                print("❌ Nebylo zachyceno žádné audio")
                return False

            print("🔄 Přepisuji řeč na text...")
            text = transcriber.transcribe(audio_data)

            if text:
                print(f"\n✅ ROZPOZNANÝ TEXT:")
                print(f'\n  📝 "{text}"\n')

                correct = input("Je text správně rozpoznán? (a/n): ").strip().lower()
                if correct == "a":
                    print("✅ Skvělé! Tiny model funguje dobře!")
                    return True
                else:
                    print("⚠️  Text nebyl rozpoznán správně.")
                    print("")
                    print("🔄 Zkusím automaticky s lepším modelem 'base'...")
                    print("   (Je větší, ale přesnější)")
                    print("")

                    # Try with base model
                    try:
                        print("🔄 Načítám Whisper model (base)...")
                        transcriber_base = WhisperTranscriber(
                            provider=WhisperProvider.LOCAL,
                            local_model="base",
                            language="cs",
                        )

                        print("✅ Model načten!")
                        print("🔄 Přepisuji znovu s base modelem...")

                        text_base = transcriber_base.transcribe(audio_data)

                        if text_base:
                            print(f"\n✅ NOVÝ ROZPOZNANÝ TEXT (base model):")
                            print(f'\n  📝 "{text_base}"\n')

                            correct_base = (
                                input("Je tento text správně? (a/n): ").strip().lower()
                            )
                            if correct_base == "a":
                                print("✅ Skvělé! Base model funguje lépe!")
                                print("💡 Doporučuji použít model 'base' místo 'tiny'")
                                return True
                            else:
                                print("⚠️  Ani base model není dokonalý.")
                                print(
                                    "💡 Tip: Můžete zkusit model 'small', ale je pomalejší"
                                )
                                return True
                        else:
                            print("❌ Ani base model nerozpoznal text")
                            return True

                    except Exception as e:
                        print(f"⚠️  Nepodařilo se načíst base model: {e}")
                        print(
                            "💡 Tip: Zkuste model 'base' nebo 'small' při spuštění aplikace"
                        )
                        return True

            else:
                print("❌ Nepodařilo se rozpoznat žádný text")
                return False

        except Exception as e:
            print(f"❌ Chyba při testu rozpoznávání: {e}")
            logger.exception("Speech recognition test failed")
            return False

    def test_text_injection(self) -> bool:
        """Test text injection."""
        self.print_step(4, "Test vkládání textu")

        print("Nyní otestujeme vkládání textu do aplikací.")
        print("")
        print("📝 Co udělat:")
        print("  1. Otevřete textový editor nebo poznámkový blok")
        print("  2. Klikněte tam, kde chcete vložit text")
        print("  3. Počkejte 3 sekundy")
        print("  4. Testovací text se automaticky vloží")
        print("")

        response = input("Jste připraveni? (a/n): ").strip().lower()
        if response != "a":
            print("⏭️  Test přeskočen")
            return True

        try:
            from .text_injector import TextInjector

            injector = TextInjector()

            print("\n⏳ Máte 3 sekundy na přepnutí do textového editoru...")
            for i in range(3, 0, -1):
                print(f"   {i}...", flush=True)
                time.sleep(1)

            test_text = "Test vkládání textu - Global Dictation funguje!"
            success = injector.inject_text(test_text)

            print("")
            if success:
                response = input("Byl text úspěšně vložen? (a/n): ").strip().lower()
                if response == "a":
                    print("✅ Vkládání textu funguje!")
                    return True
                else:
                    print("⚠️  Text nebyl vložen správně")
                    print("💡 Zkuste jinou metodu vkládání (clipboard_only)")
                    self.config.injection.method = "clipboard_only"
                    return True
            else:
                print("❌ Vkládání textu selhalo")
                return False

        except Exception as e:
            print(f"❌ Chyba při testu vkládání: {e}")
            return False

    def configure_settings(self) -> None:
        """Configure optimal settings based on tests."""
        self.print_step(5, "Konfigurace nastavení")

        print("Na základě testů doporučuji tato nastavení:\n")

        # Audio settings
        self.config.audio.silence_threshold = self.optimal_threshold
        self.config.audio.silence_duration = 2.0

        print(f"📊 Audio:")
        print(f"  Práh ticha: {self.config.audio.silence_threshold:.3f}")
        print(f"  Doba ticha: {self.config.audio.silence_duration}s")
        print()

        # Whisper settings
        print("🤖 Whisper model:")
        print("  [1] tiny   - Nejrychlejší, nižší přesnost")
        print("  [2] base   - Dobrý kompromis (DOPORUČENO)")
        print("  [3] small  - Lepší přesnost, pomalejší")
        print()

        model_choice = input("Vyberte model (1-3) [2]: ").strip()
        if model_choice == "" or model_choice not in ["1", "2", "3"]:
            model_choice = "2"  # Default to base

        model_map = {"1": "tiny", "2": "base", "3": "small"}
        self.config.whisper.local_model = model_map[model_choice]

        print(f"  ✅ Vybrán model: {self.config.whisper.local_model}")
        print()

        # Hotkey
        print("⌨️  Klávesová zkratka:")
        print("  [1] Ctrl+Alt+Space (DOPORUČENO)")
        print("  [2] Ctrl+Shift+D")
        print("  [3] Ctrl+Alt+D")
        print("  [4] Vlastní zkratka")
        print()

        hotkey_choice = input("Vyberte zkratku (1-4) [1]: ").strip()
        if hotkey_choice == "" or hotkey_choice not in ["1", "2", "3", "4"]:
            hotkey_choice = "1"  # Default

        hotkey_map = {
            "1": ["ctrl", "alt", "space"],
            "2": ["ctrl", "shift", "d"],
            "3": ["ctrl", "alt", "d"],
        }

        if hotkey_choice == "4":
            # Custom hotkey
            print("")
            print("📝 Zadejte vlastní klávesovou zkratku:")
            print("   Format: ctrl+alt+key nebo ctrl+shift+key")
            print("   Příklad: ctrl+alt+h")
            print("")
            custom_hotkey = input("Vlastní zkratka: ").strip().lower()

            if custom_hotkey:
                # Parse custom hotkey
                keys = custom_hotkey.replace(" ", "").split("+")
                if len(keys) >= 2:
                    self.config.hotkey.combination = keys
                    print(f"  ✅ Vybrána vlastní zkratka: {'+'.join(keys)}")
                else:
                    print("  ⚠️  Neplatný formát, použiji výchozí (ctrl+alt+space)")
                    self.config.hotkey.combination = ["ctrl", "alt", "space"]
            else:
                print("  ⚠️  Prázdný vstup, použiji výchozí (ctrl+alt+space)")
                self.config.hotkey.combination = ["ctrl", "alt", "space"]
        else:
            self.config.hotkey.combination = hotkey_map[hotkey_choice]
            print(f"  ✅ Vybrána zkratka: {'+'.join(self.config.hotkey.combination)}")

        print()

    def save_configuration(self) -> bool:
        """Save configuration to file."""
        self.print_step(6, "Uložení konfigurace")

        config_path = Path.home() / ".config" / "mycoder" / "dictation_config.json"

        print(f"💾 Ukládám konfiguraci do:")
        print(f"   {config_path}")
        print()

        self.config_manager.config = self.config

        if self.config_manager.save():
            print("✅ Konfigurace úspěšně uložena!")
            return True
        else:
            print("❌ Chyba při ukládání konfigurace")
            return False

    def finish(self) -> None:
        """Display finish message."""
        self.print_header("✅ NASTAVENÍ DOKONČENO", "═")

        print("🎉 Gratulujeme! Global Dictation je připraveno k použití.\n")
        print("🚀 Spuštění aplikace:")
        print(f"   poetry run dictation run")
        print()
        print("📖 Jak používat:")
        print(f"  1. Stiskněte {'+'.join(self.config.hotkey.combination)}")
        print("  2. Mluvte česky")
        print("  3. Počkejte 2s ticha")
        print("  4. Text se automaticky vloží!")
        print()
        print("💡 Tipy:")
        print("  • Mluvte jasně a přirozeně")
        print("  • Minimalizujte hluk v pozadí")
        print("  • Pro delší texty použijte model 'small' nebo 'base'")
        print()

        launch = input("Chcete spustit aplikaci nyní? (a/n): ").strip().lower()
        if launch == "a":
            print("\n🚀 Spouštím Global Dictation...")
            print("   Měli byste vidět zelené tlačítko 🎤")
            print(
                f"   Stiskněte {'+'.join(self.config.hotkey.combination)} pro diktování"
            )
            print()
            return True
        else:
            print("\n👋 Můžete spustit později příkazem: poetry run dictation run")
            return False

    def run(self) -> bool:
        """Run the complete setup wizard."""
        try:
            self.welcome()

            # Step 1: Audio devices
            if not self.test_audio_devices():
                print("\n❌ Nepodařilo se detekovat audio zařízení.")
                print("   Zkontrolujte že máte mikrofon připojený a funkční.")
                return False

            # Step 2: Microphone level
            success, threshold = self.test_microphone_level()
            if not success:
                print("\n⚠️  Problém s hlasitostí mikrofonu.")
                response = input("Pokračovat i přesto? (a/n): ").strip().lower()
                if response != "a":
                    return False

            # Step 3: Speech recognition
            if not self.test_speech_recognition():
                print("\n⚠️  Problém s rozpoznáváním řeči.")
                response = input("Pokračovat i přesto? (a/n): ").strip().lower()
                if response != "a":
                    return False

            # Step 4: Text injection
            self.test_text_injection()

            # Step 5: Configure
            self.configure_settings()

            # Step 6: Save
            if not self.save_configuration():
                print("\n❌ Nepodařilo se uložit konfiguraci")
                return False

            # Finish
            should_launch = self.finish()

            return should_launch

        except KeyboardInterrupt:
            print("\n\n⚠️  Průvodce přerušen uživatelem")
            return False
        except Exception as e:
            print(f"\n❌ Neočekávaná chyba: {e}")
            logger.exception("Setup wizard failed")
            return False


def main() -> int:
    """Main entry point for setup wizard."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    wizard = SetupWizard()
    should_launch = wizard.run()

    if should_launch:
        # Launch the application
        from .cli import run as run_dictation

        try:
            run_dictation.callback(
                config=None,
                provider="local",
                model=wizard.config.whisper.local_model,
                language="cs",
                no_gui=False,
                no_hotkeys=False,
                hotkey=None,
                api_key=None,
                injection_method=None,
                debug=False,
            )
        except Exception as e:
            print(f"❌ Chyba při spouštění aplikace: {e}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
