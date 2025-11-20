#!/bin/bash
# Instalační script pro Global Dictation (lokální režim)
# Pro uživatele bez OpenAI API klíče

set -e

echo "╔════════════════════════════════════════════════╗"
echo "║   Global Dictation - Instalace (Lokální)      ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Detekce distribuce
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "⚠️  Nepodařilo se detekovat distribuci Linuxu"
    DISTRO="unknown"
fi

echo "📦 Instalace systémových závislostí..."
echo ""

# Instalace závislostí podle distribuce
case $DISTRO in
    ubuntu|debian|linuxmint|pop)
        echo "Detekována distribuce: Ubuntu/Debian"
        sudo apt-get update
        sudo apt-get install -y xdotool portaudio19-dev python3-pyqt5 ffmpeg
        ;;
    fedora|rhel|centos)
        echo "Detekována distribuce: Fedora/RHEL"
        sudo dnf install -y xdotool portaudio-devel python3-qt5 ffmpeg
        ;;
    arch|manjaro)
        echo "Detekována distribuce: Arch Linux"
        sudo pacman -S --noconfirm xdotool portaudio python-pyqt5 ffmpeg
        ;;
    *)
        echo "⚠️  Neznámá distribuce: $DISTRO"
        echo "Prosím nainstalujte manuálně: xdotool, portaudio, python3-pyqt5, ffmpeg"
        read -p "Pokračovat? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        ;;
esac

echo ""
echo "✅ Systémové závislosti nainstalovány"
echo ""

# Kontrola Poetry
if ! command -v poetry &> /dev/null; then
    echo "⚠️  Poetry není nainstalováno"
    echo "Instaluji Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "📦 Instalace Python balíčků..."
echo ""

# Instalace Python závislostí
poetry install --extras speech

echo ""
echo "✅ Python balíčky nainstalovány"
echo ""

# Test instalace
echo "🧪 Testování instalace..."
echo ""

if poetry run dictation test; then
    echo ""
    echo "✅ Všechny testy prošly!"
else
    echo ""
    echo "⚠️  Některé testy selhaly, ale aplikace může stále fungovat"
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║              ✅ INSTALACE DOKONČENA            ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "🚀 Spuštění aplikace:"
echo ""
echo "   poetry run dictation run --provider local --model base"
echo ""
echo "📖 Více informací:"
echo "   - Quick Start: cat DICTATION_QUICKSTART.md"
echo "   - Kompletní dokumentace: cat docs/DICTATION_APP.md"
echo ""
echo "🎤 První použití:"
echo "   1. Spusťte aplikaci"
echo "   2. Klikněte na 🎤 tlačítko nebo stiskněte Ctrl+Shift+Space"
echo "   3. Mluvte"
echo "   4. Po ~1.5s ticha se text vloží automaticky"
echo ""
echo "💡 Tip: První spuštění stáhne Whisper model (~74MB)"
echo ""
echo "Enjoy! 🎉"
