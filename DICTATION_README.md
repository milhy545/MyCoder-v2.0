# 🎤 Global Dictation - Nativní linuxová aplikace pro diktování

> Diktujte do **jakékoliv** aplikace - prohlížeč, terminál, textový editor. Jednoduše klikněte na tlačítko nebo stiskněte klávesovou zkratku a začněte mluvit!

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Hlavní vlastnosti

- 🌍 **Globální funkčnost** - Funguje ve všech aplikacích (Firefox, Chrome, VS Code, terminál, ...)
- 🎨 **Floating GUI** - Stylové přetahovatelné tlačítko pro rychlý přístup
- ⌨️ **Globální klávesové zkratky** - Spusťte diktování odkudkoliv (výchozí: Ctrl+Shift+Space)
- 🤖 **OpenAI Whisper** - Nejlepší speech-to-text technologie (API + lokální modely)
- 🔇 **Automatická detekce ticha** - Ukončí nahrávání automaticky po ~1.5s ticha
- 📋 **Vícenásobné metody vkládání** - xdotool type/paste, clipboard
- ⚙️ **Plně konfigurovatelné** - JSON config + environment proměnné
- 🇨🇿 **Podpora češtiny** - Výchozí jazyk čeština, ale funguje pro všechny jazyky
- 🔌 **Offline režim** - Lokální Whisper modely pro práci bez internetu

## 🎬 Jak to vypadá

```
┌─────────────────────────────────────┐
│                                     │
│        🎤                           │  ← Kliknutelné tlačítko
│      Ready                          │     (přetahovatelné)
│                                     │
└─────────────────────────────────────┘

1. Klikněte na 🎤 nebo stiskněte Ctrl+Shift+Space
2. Tlačítko zčervená 🔴 - mluvte
3. Přestaňte mluvit a počkejte ~1.5s ticha
4. Text se automaticky vloží do aktivního okna ✨
```

## 🚀 Rychlá instalace

### 1. Systémové závislosti

```bash
# Ubuntu/Debian
sudo apt-get install xdotool portaudio19-dev python3-pyqt5

# Fedora
sudo dnf install xdotool portaudio-devel python3-qt5

# Arch Linux
sudo pacman -S xdotool portaudio python-pyqt5
```

### 2. Python balíčky

```bash
# Instalace všech závislostí
poetry install --extras speech

# Nebo manuálně
pip install sounddevice numpy PyQt5 openai-whisper openai pynput python-xlib pyperclip
```

### 3. První spuštění

```bash
# S lokálním Whisper modelem (offline, žádné API)
poetry run dictation run --provider local --model base

# Nebo s OpenAI API (rychlejší, vyžaduje API klíč)
export OPENAI_API_KEY="sk-your-key-here"
poetry run dictation run
```

**Hotovo!** Objeví se floating tlačítko 🎤

## 📖 Použití

### Základní ovládání

1. **Klikněte na tlačítko** nebo **stiskněte Ctrl+Shift+Space**
2. **Mluvte** (tlačítko zčervená 🔴)
3. **Přestaňte mluvit** a počkejte ~1.5 sekundy ticha
4. **Text se automaticky vloží** do aktivního okna

### CLI příkazy

```bash
# Spustit aplikaci
dictation run

# Spustit bez GUI (jen klávesové zkratky)
dictation run --no-gui

# Spustit s lokálním modelem
dictation run --provider local --model base

# Změnit jazyk
dictation run --language en  # Angličtina
dictation run --language de  # Němčina
dictation run --language cs  # Čeština (výchozí)

# Debug režim
dictation run --debug

# Zobrazit dostupná audio zařízení
dictation devices

# Otestovat komponenty
dictation test

# Vytvořit konfigurační soubor
dictation config-create

# Zobrazit aktuální konfiguraci
dictation config-show

# Otestovat vkládání textu
dictation inject "Test zpráva"
```

## ⚙️ Konfigurace

### Environment proměnné

```bash
# OpenAI API klíč (pro API provider)
export OPENAI_API_KEY="sk-..."

# Whisper provider (api nebo local)
export DICTATION_WHISPER_PROVIDER="local"

# Jazyk
export DICTATION_LANGUAGE="cs"

# Log level
export DICTATION_LOG_LEVEL="DEBUG"

# Vypnout GUI
export DICTATION_GUI_ENABLED="false"
```

### Konfigurační soubor

Vytvoření: `dictation config-create`

Umístění: `~/.config/mycoder/dictation_config.json`

```json
{
  "whisper": {
    "provider": "local",
    "local_model": "base",
    "language": "cs"
  },
  "hotkey": {
    "enabled": true,
    "combination": ["ctrl", "shift", "space"]
  },
  "gui": {
    "enabled": true,
    "button_size": 80
  }
}
```

## 🎙️ Whisper modely

### OpenAI API (`--provider api`)

**Výhody:**
- ✅ Nejrychlejší (1-2 sekundy)
- ✅ Nejpřesnější
- ✅ Nízká zátěž CPU

**Nevýhody:**
- ❌ Vyžaduje internet
- ❌ Vyžaduje API klíč ($$$)

### Lokální modely (`--provider local`)

| Model | Velikost | Rychlost | Přesnost | RAM | Doporučeno pro |
|-------|----------|----------|----------|-----|----------------|
| `tiny` | 39 MB | ⚡⚡⚡ | ⭐⭐ | 1 GB | Testování |
| `base` | 74 MB | ⚡⚡ | ⭐⭐⭐ | 1 GB | **Běžné použití** |
| `small` | 244 MB | ⚡ | ⭐⭐⭐⭐ | 2 GB | **Lepší přesnost** |
| `medium` | 769 MB | 🐌 | ⭐⭐⭐⭐⭐ | 5 GB | Maximální přesnost |
| `large` | 1550 MB | 🐌🐌 | ⭐⭐⭐⭐⭐⭐ | 10 GB | Server/vysoký výkon |

**Doporučení pro Q9550:**
```bash
# Pro běžné použití - rychlé a dostatečně přesné
dictation run --provider local --model base

# Pro lepší přesnost (pomalejší)
dictation run --provider local --model small
```

## 🔧 Metody vkládání textu

### `auto` (výchozí, doporučeno)
Automaticky vybere nejlepší metodu podle dostupných nástrojů.

### `xdotool_paste`
Vloží text pomocí Ctrl+V (rychlé, vyžaduje xdotool).

### `xdotool_type`
Simuluje psaní jednotlivých znaků (spolehlivé, pomalejší).

### `clipboard_only`
Pouze zkopíruje do schránky, uživatel musí ručně vložit.

## 🎯 Praktické příklady použití

### 1. Diktování do prohlížeče
1. Otevřete Google Docs / Gmail / jakýkoliv web
2. Klikněte do textového pole
3. Stiskněte Ctrl+Shift+Space
4. Mluvte: "Ahoj, jak se máš?"
5. Text se vloží automaticky ✨

### 2. Diktování do terminálu
1. Otevřete terminál
2. Stiskněte Ctrl+Shift+Space
3. Mluvte: "sudo apt update"
4. Příkaz se vloží do terminálu

### 3. Diktování do VS Code
1. Otevřete VS Code
2. Klikněte do editoru
3. Klikněte na 🎤 tlačítko
4. Mluvte kód: "function calculate total amount"
5. Kód se vloží

## 🐛 Řešení problémů

### Audio zařízení nenalezeno
```bash
# Zobrazit dostupná zařízení
dictation devices

# Nebo
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### xdotool nefunguje
```bash
# Instalace
sudo apt-get install xdotool

# Test
xdotool type "test"
```

### Text se nevkládá
```bash
# Zkuste jinou metodu
dictation run --injection-method clipboard_only

# Nebo otestujte
dictation inject "Test text"
```

### PyQt5 import error
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5

# Nebo
pip install PyQt5
```

### Whisper API chyba
```bash
# Zkontrolujte API klíč
echo $OPENAI_API_KEY

# Použijte lokální model
dictation run --provider local --model base
```

## 📊 Performance

Testováno na **Intel Q9550 @ 2.83GHz, 8GB RAM**:

| Operace | Whisper API | Whisper Base | Whisper Small |
|---------|-------------|--------------|---------------|
| Nahrávání 10s audio | 10s | 10s | 10s |
| Přepis | 1-2s | 3-5s | 8-12s |
| Vložení textu | <0.1s | <0.1s | <0.1s |
| **Celková doba** | **~12s** | **~15s** | **~22s** |

## 🏗️ Architektura

```
src/speech_recognition/
├── audio_recorder.py        # 🎤 Audio capture (sounddevice)
├── whisper_transcriber.py   # 🤖 Speech-to-text (Whisper)
├── text_injector.py         # ⌨️ Text injection (xdotool)
├── overlay_button.py        # 🎨 GUI overlay (PyQt5)
├── hotkey_manager.py        # ⌨️ Global hotkeys (pynput)
├── dictation_app.py         # 🎯 Main orchestrator
├── config.py                # ⚙️ Configuration
└── cli.py                   # 💻 CLI interface
```

## 📚 Dokumentace

- **[Kompletní dokumentace](docs/DICTATION_APP.md)** - Detailní návody a API reference
- **[Demo script](examples/dictation_demo.py)** - Ukázkové příklady použití

## 🤝 Příklady kódu

### Programmatické použití

```python
from speech_recognition import GlobalDictationApp, WhisperProvider

# Vytvořit aplikaci
app = GlobalDictationApp(
    whisper_provider=WhisperProvider.LOCAL,
    whisper_model="base",
    language="cs",
    enable_gui=True,
    enable_hotkeys=True,
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

## 🧪 Testování

```bash
# Spustit všechny testy
poetry run pytest tests/unit/test_speech_recognition.py -v

# Otestovat komponenty
poetry run dictation test

# Otestovat audio zařízení
poetry run dictation devices

# Otestovat vkládání textu
poetry run dictation inject "Test zpráva"
```

## 📄 Licence

MIT License - viz [LICENSE](LICENSE)

## 🙏 Poděkování

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition AI
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio I/O
- [pynput](https://pynput.readthedocs.io/) - Global keyboard hooks
- [xdotool](https://github.com/jordansissel/xdotool) - X11 automation

## 💡 Tip

**Pro nejlepší výsledky:**
- Mluvte jasně a ne příliš rychle
- Minimalizujte hluk v pozadí
- Použijte kvalitní mikrofon
- Pro češtinu doporučujeme model `small` nebo větší

**Enjoy diktování! 🎤✨**
