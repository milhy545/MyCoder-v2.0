# Global Dictation App - Nativní linuxová aplikace pro diktování

Nativní aplikace pro globální rozpoznávání řeči v Linuxu, která umožňuje diktovat do libovolného okna včetně terminálu.

## 🎯 Vlastnosti

- **Globální funkčnost** - Funguje ve všech aplikacích (prohlížeč, terminál, textový editor, atd.)
- **Floating GUI** - Přetahovatelné tlačítko pro rychlý přístup
- **Globální klávesové zkratky** - Spuštění diktování odkudkoliv
- **Whisper AI** - Podpora OpenAI API i lokálních modelů
- **Automatická detekce ticha** - Ukončí nahrávání po tichu
- **Vícenásobné metody vkládání textu** - xdotool, clipboard
- **Konfigurovatelné** - JSON konfigurace + environment proměnné

## 📦 Instalace

### 1. Instalace systémových závislostí

```bash
# Ubuntu/Debian
sudo apt-get install xdotool portaudio19-dev python3-pyqt5

# Fedora
sudo dnf install xdotool portaudio-devel python3-qt5

# Arch
sudo pacman -S xdotool portaudio python-pyqt5
```

### 2. Instalace Python balíčků

```bash
# Instalace všech závislostí pro speech recognition
poetry install --extras speech

# Nebo jen základní závislosti
pip install sounddevice numpy PyQt5 openai-whisper openai pynput python-xlib pyperclip
```

## 🚀 Rychlý start

### Spuštění s výchozím nastavením

```bash
# S OpenAI API (vyžaduje OPENAI_API_KEY)
export OPENAI_API_KEY="your-api-key"
poetry run dictation run

# S lokálním Whisper modelem (žádné API, běží offline)
poetry run dictation run --provider local --model base
```

### Spuštění s vlastním nastavením

```bash
# Vytvořit výchozí konfiguraci
poetry run dictation config-create

# Upravit konfiguraci
nano ~/.config/mycoder/dictation_config.json

# Spustit s konfigurací
poetry run dictation run --config ~/.config/mycoder/dictation_config.json
```

## 🎮 Použití

### GUI režim (výchozí)

1. Spusťte aplikaci: `poetry run dictation run`
2. Objeví se floating tlačítko s mikrofonem 🎤
3. Klikněte na tlačítko nebo stiskněte **Ctrl+Shift+Space**
4. Mluvte (tlačítko se změní na červené)
5. Přestaňte mluvit a počkejte ~1.5s ticha
6. Text se automaticky vloží do aktivního okna

### Klávesové zkratky

- **Ctrl+Shift+Space** - Zapnout/vypnout nahrávání (výchozí)
- Lze změnit v konfiguraci: `hotkey.combination`

### CLI příkazy

```bash
# Spustit aplikaci
dictation run

# Spustit bez GUI (jen klávesové zkratky)
dictation run --no-gui

# Spustit s lokálním modelem
dictation run --provider local --model base

# Spustit s českou lokalizací (výchozí)
dictation run --language cs

# Spustit s anglickou lokalizací
dictation run --language en

# Zobrazit konfiguraci
dictation config-show

# Vytvořit výchozí konfiguraci
dictation config-create

# Otestovat komponenty
dictation test

# Zobrazit dostupná audio zařízení
dictation devices

# Otestovat vkládání textu
dictation inject "Test text"
```

## ⚙️ Konfigurace

### Konfigurační soubor

Výchozí umístění: `~/.config/mycoder/dictation_config.json`

```json
{
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "silence_threshold": 0.01,
    "silence_duration": 1.5,
    "max_duration": 60.0
  },
  "whisper": {
    "provider": "api",
    "model": "whisper-1",
    "local_model": "base",
    "language": "cs",
    "temperature": 0.0
  },
  "injection": {
    "method": "auto",
    "typing_delay": 12,
    "use_clipboard_backup": true
  },
  "gui": {
    "enabled": true,
    "button_size": 80,
    "position_x": null,
    "position_y": null
  },
  "hotkey": {
    "enabled": true,
    "combination": ["ctrl", "shift", "space"]
  },
  "log_level": "INFO",
  "log_file": null
}
```

### Environment proměnné

```bash
# OpenAI API klíč
export OPENAI_API_KEY="sk-..."

# Whisper provider (api nebo local)
export DICTATION_WHISPER_PROVIDER="local"

# Jazyk
export DICTATION_LANGUAGE="cs"

# Log úroveň
export DICTATION_LOG_LEVEL="DEBUG"

# Vypnout GUI
export DICTATION_GUI_ENABLED="false"

# Vypnout hotkeys
export DICTATION_HOTKEY_ENABLED="false"
```

## 🔧 Metody vkládání textu

### `auto` (doporučeno)
Automatický výběr nejlepší metody podle dostupných nástrojů.

### `xdotool_paste`
Rychlé vložení pomocí Ctrl+V (vyžaduje xdotool).

### `xdotool_type`
Simulace psaní jednotlivých znaků (vyžaduje xdotool).

### `clipboard_only`
Pouze zkopíruje do schránky, uživatel musí ručně vložit (Ctrl+V).

## 🎙️ Whisper modely

### OpenAI API (`provider: api`)
- **Model**: `whisper-1`
- **Výhody**: Vysoká přesnost, rychlá odezva
- **Nevýhody**: Vyžaduje internet a API klíč, náklady
- **Použití**: `dictation run --provider api`

### Lokální modely (`provider: local`)

| Model | Velikost | Rychlost | Přesnost | RAM |
|-------|----------|----------|----------|-----|
| tiny | 39 MB | Velmi rychlá | Nízká | ~1 GB |
| base | 74 MB | Rychlá | Dobrá | ~1 GB |
| small | 244 MB | Střední | Velmi dobrá | ~2 GB |
| medium | 769 MB | Pomalá | Výborná | ~5 GB |
| large | 1550 MB | Velmi pomalá | Nejlepší | ~10 GB |

**Doporučení pro Q9550**:
- Pro rychlou odezvu: `base` nebo `small`
- Pro přesnost: `medium` (vyšší zátěž CPU)

```bash
# Použití lokálního modelu
dictation run --provider local --model base
```

## 🐛 Řešení problémů

### Audio zařízení nenalezeno

```bash
# Zobrazit dostupná zařízení
dictation devices

# Otestovat nahrávání
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### xdotool nefunguje

```bash
# Instalace xdotool
sudo apt-get install xdotool

# Test
xdotool type "test"
```

### Text se nevkládá

```bash
# Otestovat vkládání
dictation inject "Test text"

# Zkusit jinou metodu
dictation run --injection-method clipboard_only
```

### Whisper API chyba

```bash
# Zkontrolovat API klíč
echo $OPENAI_API_KEY

# Použít lokální model
dictation run --provider local --model base
```

### PyQt5 import error

```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5

# Nebo instalace přes pip
pip install PyQt5
```

## 🏗️ Architektura

```
┌─────────────────────────────────────────┐
│       GlobalDictationApp                │
│         (Orchestrator)                  │
└─────────────────────────────────────────┘
           │
           ├─── AudioRecorder
           │      ├─ sounddevice
           │      └─ Silence detection
           │
           ├─── WhisperTranscriber
           │      ├─ OpenAI API
           │      └─ Local Whisper
           │
           ├─── TextInjector
           │      ├─ xdotool
           │      └─ pyperclip
           │
           ├─── OverlayButton (PyQt5)
           │      └─ Floating GUI
           │
           ├─── HotkeyManager (pynput)
           │      └─ Global hotkeys
           │
           └─── ConfigManager
                  └─ JSON config
```

## 📝 Příklady použití

### Základní použití

```python
from speech_recognition import GlobalDictationApp, WhisperProvider

# Vytvořit aplikaci
app = GlobalDictationApp(
    whisper_provider=WhisperProvider.LOCAL,
    whisper_model="base",
    language="cs",
)

# Spustit
app.run()
```

### Bez GUI (jen hotkeys)

```python
app = GlobalDictationApp(
    enable_gui=False,
    enable_hotkeys=True,
    hotkey_combo=["ctrl", "alt", "d"],
)
app.run()
```

### Vlastní callback

```python
def on_recording_toggle():
    print("Recording toggled!")

app = GlobalDictationApp(enable_gui=False)
# Přidat vlastní hotkey
app.hotkey_manager.register_hotkey(
    ["ctrl", "shift", "r"],
    on_recording_toggle
)
app.run()
```

## 🧪 Testování

```bash
# Otestovat všechny komponenty
poetry run dictation test

# Otestovat audio zařízení
poetry run dictation devices

# Otestovat vkládání textu
poetry run dictation inject "Test message"

# Debug režim
poetry run dictation run --debug
```

## 📊 Performance (Q9550 @ 2.83GHz)

| Operace | Whisper API | Whisper Base | Whisper Medium |
|---------|-------------|--------------|----------------|
| Nahrávání | Real-time | Real-time | Real-time |
| Přepis (10s audio) | ~1-2s | ~3-5s | ~10-15s |
| Vložení textu | <0.1s | <0.1s | <0.1s |
| **Celkem** | **~2-3s** | **~4-6s** | **~11-16s** |

## 🔐 Bezpečnost

- API klíče nejsou ukládány do konfiguračního souboru
- Používejte environment proměnné pro citlivé údaje
- Audio data jsou zpracována lokálně (kromě API přepisů)
- Žádná telemetrie ani logování audio obsahu

## 🛠️ Vývoj

### Struktura modulů

```
src/speech_recognition/
├── __init__.py
├── audio_recorder.py        # Audio capture
├── whisper_transcriber.py   # Speech-to-text
├── text_injector.py         # Text injection
├── overlay_button.py        # GUI overlay
├── hotkey_manager.py        # Global hotkeys
├── dictation_app.py         # Main app
├── config.py                # Configuration
└── cli.py                   # CLI interface
```

### Přidání vlastního poskytovatele

```python
from speech_recognition import WhisperTranscriber

class CustomTranscriber:
    def transcribe(self, audio_data: bytes) -> str:
        # Vlastní implementace
        return "transcribed text"
```

## 📄 Licence

MIT License - viz hlavní README projektu

## 🙏 Poděkování

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio I/O
- [pynput](https://pynput.readthedocs.io/) - Global hotkeys
- [xdotool](https://github.com/jordansissel/xdotool) - X11 automation
