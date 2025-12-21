#!/bin/bash
# Quick start script pro Global Dictation (lokální režim)

echo "🎤 Spouštím Global Dictation (lokální Whisper model)..."
echo ""

# Kontrola závislostí
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry není nainstalováno!"
    echo "Spusťte: ./install_dictation.sh"
    exit 1
fi

# Kontrola instalace
if ! poetry run python -c "import speech_recognition" 2>/dev/null; then
    echo "❌ Aplikace není nainstalována!"
    echo "Spusťte: ./install_dictation.sh"
    exit 1
fi

# Spustit aplikaci
echo "✅ Spouštím s lokálním Whisper modelem 'base'..."
echo ""
echo "💡 Tipy:"
echo "   - Klikněte na 🎤 nebo stiskněte Ctrl+Shift+Space"
echo "   - Mluvte česky a počkejte ~1.5s ticha"
echo "   - Text se vloží automaticky do aktivního okna"
echo ""
echo "   Pro ukončení: Ctrl+C nebo zavřete okno"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Spustit s lokální konfigurací
exec poetry run dictation run --config dictation_config_local.json
