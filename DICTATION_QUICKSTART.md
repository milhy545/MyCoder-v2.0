# 🎤 Quick Start - Diktování BEZ OpenAI API

> Pro uživatele, kteří nemají OpenAI API klíč. Používá lokální Whisper modely - **zcela zdarma a offline!**

## ⚡ Rychlá instalace (5 minut)

### Nejjednodušší cesta - Instalační skript:

```bash
./install_dictation.sh
```

Skript automaticky:
- ✅ Detekuje vaši Linux distribuci
- ✅ Nainstaluje systémové závislosti (xdotool, portaudio, PyQt5, ffmpeg)
- ✅ Nainstaluje Poetry a Python balíčky
- ✅ Nabídne spuštění průvodce nastavením

### Nebo manuálně:

#### 1. Systémové závislosti

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y xdotool portaudio19-dev python3-pyqt5 ffmpeg

# Fedora
sudo dnf install -y xdotool portaudio-devel python3-qt5 ffmpeg

# Arch
sudo pacman -S xdotool portaudio python-pyqt5 ffmpeg
```

#### 2. Python závislosti

```bash
# V MyCoder-v2.0 adresáři
poetry install --extras speech

# Nebo pokud nemáte Poetry
pip install sounddevice numpy PyQt5 openai-whisper pynput python-xlib pyperclip
```

#### 3. Průvodce nastavením (🆕 DOPORUČENO!)

```bash
poetry run dictation setup
```

Interaktivní wizard vás provede:
1. **🎙️ Test mikrofonu** - Detekce audio zařízení
2. **📊 Test hlasitosti** - Živý VU metr + optimální práh ticha
3. **🗣️ Test rozpoznávání** - Zkouška Whisper s češtinou
4. **⌨️ Test vkládání** - Ověření text injection
5. **⚙️ Konfigurace** - Výběr modelu a klávesové zkratky
6. **💾 Automatické uložení** - Optimální config

#### 4. Nebo spustit bez wizardu:

```bash
# Použít předpřipravenou konfiguraci
poetry run dictation run --config dictation_config_tuned.json

# Nebo jednoduše
poetry run dictation run --provider local --model base
```

**Hotovo!** Objeví se zelené tlačítko 🎤

## 🎯 První použití

1. **Klikněte na 🎤** nebo stiskněte **Ctrl+Alt+Space** (nebo vaši zvolenou zkratku)
2. Tlačítko zčervená 🔴 - **mluvte česky**
3. Po ~2s ticha se **text automaticky vloží**

> **💡 Tip**: Pokud jste použili průvodce nastavením, optimální parametry už jsou nastaveny!

### Test ve 3 krocích:

```bash
# 1. Otevřete textový editor (gedit, mousepad, atd.)
gedit &

# 2. Spusťte dictation
poetry run dictation run --provider local --model base

# 3. Klikněte na 🎤 a řekněte: "Toto je test diktování"
```

## 📊 Whisper modely - Jaký vybrat?

Pro **Intel Q9550 @ 2.83GHz**:

| Model | Velikost | Čas na 10s audio | Přesnost | Doporučení |
|-------|----------|------------------|----------|------------|
| `tiny` | 39 MB | ~1-2s | ⭐⭐ | Jen na testování |
| **`base`** | 74 MB | **~3-5s** | ⭐⭐⭐ | **✅ ZAČNĚTE TADY** |
| `small` | 244 MB | ~8-12s | ⭐⭐⭐⭐ | Pokud vám nevadí čekat |
| `medium` | 769 MB | ~20-30s | ⭐⭐⭐⭐⭐ | Jen pokud máte trpělivost |

### Můj osobní tip:

```bash
# Pro běžné používání - rychlé a spolehlivé
poetry run dictation run --provider local --model base

# Pro delší texty kde chcete lepší přesnost
poetry run dictation run --provider local --model small
```

## 🔧 Časté problémy

### "No module named sounddevice"

```bash
sudo apt-get install portaudio19-dev
poetry install --extras speech
```

### "No audio devices found"

```bash
# Zjistit dostupná zařízení
poetry run dictation devices

# Nebo
arecord -l
```

### "xdotool not found"

```bash
sudo apt-get install xdotool
```

### Text se nevkládá

```bash
# Zkuste metodu clipboard (pak ručně Ctrl+V)
poetry run dictation run --provider local --model base --injection-method clipboard_only
```

### Model se dlouho stahuje

První spuštění každého modelu ho stáhne (~74MB pro base). Pak je uložen v `~/.cache/whisper/`.

### Vysoká zátěž CPU

```bash
# Použijte menší model
poetry run dictation run --provider local --model tiny

# Nebo zvyšte silence_duration aby méně často přepisoval
# (upravte v dictation_config_local.json: "silence_duration": 2.5)
```

## ⚙️ Konfigurace

### Výchozí konfigurace

Po spuštění průvodce se uloží do: `~/.config/mycoder/dictation_config.json`

Nebo použijte připravenou: `dictation_config_tuned.json`:

```json
{
  "whisper": {
    "provider": "local",
    "local_model": "tiny",
    "language": "cs"
  },
  "hotkey": {
    "combination": ["ctrl", "alt", "space"]
  },
  "audio": {
    "silence_threshold": 0.03,
    "silence_duration": 2.0
  }
}
```

### Změna klávesové zkratky

Upravte config soubor:

```json
{
  "hotkey": {
    "combination": ["ctrl", "alt", "d"]
  }
}
```

Nebo spusťte průvodce znovu:

```bash
poetry run dictation setup
```

### Změna jazyka

```bash
# Angličtina
poetry run dictation run --provider local --model base --language en

# Slovenština
poetry run dictation run --provider local --model base --language sk

# Němčina
poetry run dictation run --provider local --model base --language de
```

## 🎨 Tipy pro lepší výsledky

### 1. Kvalitní mikrofon
- Headset je lepší než laptop mikrofon
- Kondenzátorový USB mikrofon = nejlepší

### 2. Tiché prostředí
- Zavřete okna (hluk z ulice)
- Vypněte ventilátor (pokud možno)
- Mluvte blíž k mikrofonu

### 3. Mluvte přirozeně
- ✅ Normální tempo, jasná výslovnost
- ❌ Nepřehánějte pomalost
- ✅ Přirozené pauzy jsou OK
- ❌ Nepřerušujte věty zbytečně

### 4. Delší věty = lepší přesnost
```
❌ "Ahoj." "Jak." "Se." "Máš."
✅ "Ahoj, jak se máš? Já jsem v pohodě."
```

## 📱 Příklady použití

### Diktování emailu v Gmailu

1. Otevřete Gmail v prohlížeči
2. Klikněte "Napsat"
3. Klikněte do pole "Předmět"
4. **Ctrl+Shift+Space** → Nadiktujte předmět → Pauza
5. Klikněte do pole zprávy
6. **Ctrl+Shift+Space** → Nadiktujte zprávu → Pauza
7. Hotovo!

### Diktování do terminálu

```bash
# Otevřete terminál
# Ctrl+Shift+Space
# Řekněte: "sudo apt update and upgrade dash y"
# → Vloží se: "sudo apt update && upgrade -y"
```

### Diktování kódu

```bash
# VS Code
# Ctrl+Shift+Space
# Řekněte: "funkce sečti číslo a a číslo b vrať a plus b"
# → Přepíše jako: "funkce sečti číslo a a číslo b vrať a plus b"
# (ne jako validní kod, ale jako text - kód musíte pak upravit)
```

## 🚀 Pokročilé

### Spustit na pozadí

```bash
# S nohup
nohup poetry run dictation run --provider local --model base &

# Nebo vytvořte systemd service
```

### Autostart při přihlášení

```bash
# Vytvořte desktop file
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/dictation.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Global Dictation
Exec=/path/to/MyCoder-v2.0/.venv/bin/python -m speech_recognition.cli run --provider local --model base
X-GNOME-Autostart-enabled=true
EOF
```

### Bez GUI (jen hotkeys)

```bash
poetry run dictation run --provider local --model base --no-gui
```

## 💰 Náklady

**0 Kč / měsíc**

- Lokální Whisper modely jsou zdarma
- Žádné API volání
- Žádné limity
- Žádná telemetrie

## ❓ FAQ

**Q: Proč je první přepis pomalý?**
A: První spuštění musí načíst model do paměti (~5-10s). Pak je to rychlé.

**Q: Můžu použít v práci s citlivými daty?**
A: Ano! Vše běží lokálně, žádná data neopouštějí váš počítač.

**Q: Funguje to offline?**
A: Ano! Po stažení modelu funguje bez internetu.

**Q: Kolik RAM to žere?**
A: `base` model ~1GB, `small` ~2GB, `medium` ~5GB

**Q: Můžu použít na serveru bez X11?**
A: Ne, potřebujete X11 pro GUI a xdotool. Ale můžete použít jen audio transcription bez GUI.

## 🎉 Enjoy!

Máte-li problémy, zkontrolujte:
- `poetry run dictation test` - Test komponent
- `poetry run dictation devices` - Audio zařízení
- Logy v terminálu (spusťte s `--debug`)

**Šťastné diktování! 🎤**
